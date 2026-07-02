#!/usr/bin/env python3
"""Batch-generate calibrated rubrics for many LAB-EU tasks at once.

The calibration judge votes dominate rubric-generation cost (millions of input
tokens per task). This orchestrator routes exactly that phase through the
OpenAI Batch API (50% price, results within 24h), while the cheap steps stay
synchronous:

  Phase 1  draft:    atomize -> role candidates -> prune per task (sync,
                     step-cached, parallel across tasks)
  Phase 2  build:    all round-1 calibration votes for all tasks as Batch
                     API requests; votes already in a task's step cache are
                     skipped, so re-runs are idempotent
  Phase 3  submit:   upload chunked JSONL files, create batches, poll
  Phase 4  harvest:  write each vote result into the task's
                     evals/.rubric-cache under the same key the synchronous
                     pipeline would use
  Phase 5  finalize: full generate_rubric.py per task - round-1 votes hit the
                     cache for free; refine, re-judge, and tagging run
                     synchronously (they are small)

Interrupted after submitting? Re-run with --resume <run-dir>. Failed batch
lines simply stay uncached and are re-judged synchronously in phase 5.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(REPO_ROOT))

import generate_rubric as gr  # noqa: E402
from evaluation.run import judge_prompt as build_judge_prompt, parse_json_response  # noqa: E402

MAX_BATCH_REQUESTS = 45_000
MAX_BATCH_BYTES = 180 * 1024 * 1024
TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate calibrated rubrics for many tasks, judging via the OpenAI Batch API."
    )
    parser.add_argument("task_dirs", nargs="*", type=pathlib.Path, help="Task directories.")
    parser.add_argument("--taskset", type=pathlib.Path, help="JSONL taskset with task_dir fields.")
    parser.add_argument("--model", default=os.environ.get("OPENAI_RUBRIC_MODEL", gr.DEFAULT_MODEL))
    parser.add_argument("--reasoning-effort", default=gr.DEFAULT_REASONING_EFFORT)
    parser.add_argument("--judge-model", default=os.environ.get("OPENAI_JUDGE_MODEL", ""))
    parser.add_argument("--judge-reasoning-effort", default=gr.DEFAULT_JUDGE_REASONING_EFFORT)
    parser.add_argument("--calibration-votes", type=int, default=gr.DEFAULT_CALIBRATION_VOTES)
    parser.add_argument("--parallel-tasks", type=int, default=2, help="Concurrent tasks in phases 1 and 5.")
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--max-wait-hours", type=float, default=26.0)
    parser.add_argument("--completion-window", default="24h")
    parser.add_argument(
        "--runs-dir",
        type=pathlib.Path,
        default=REPO_ROOT / "runs" / "rubric-batches",
        help="Where batch run state is stored.",
    )
    parser.add_argument("--resume", type=pathlib.Path, help="Existing run dir: skip to poll/harvest/finalize.")
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Stop after writing the batch input files and state.json, without uploading.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate tasks and print the plan.")
    return parser.parse_args()


def resolve_tasks(args: argparse.Namespace) -> list[pathlib.Path]:
    tasks: list[pathlib.Path] = []
    for raw in args.task_dirs:
        path = (raw if raw.is_absolute() else REPO_ROOT / raw).resolve()
        tasks.append(path)
    if args.taskset:
        path = args.taskset if args.taskset.is_absolute() else REPO_ROOT / args.taskset
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            row = json.loads(line)
            task_dir = pathlib.Path(row["task_dir"])
            tasks.append((task_dir if task_dir.is_absolute() else REPO_ROOT / task_dir).resolve())
    unique: list[pathlib.Path] = []
    seen: set[pathlib.Path] = set()
    for task in tasks:
        if task in seen:
            continue
        seen.add(task)
        if not (task / "task.json").exists():
            raise SystemExit(f"Not a task directory (no task.json): {task}")
        if not (task / "evals").exists():
            raise SystemExit(f"No evals/ directory (gold solution required): {task}")
        unique.append(task)
    if not unique:
        raise SystemExit("No tasks given. Pass task directories or --taskset.")
    return unique


def run_generate_rubric(task: pathlib.Path, args: argparse.Namespace, extra: list[str]) -> tuple[pathlib.Path, int, str]:
    command = [
        sys.executable,
        str(SCRIPTS_DIR / "generate_rubric.py"),
        str(task),
        "--model", args.model,
        "--reasoning-effort", args.reasoning_effort,
        "--judge-reasoning-effort", args.judge_reasoning_effort,
        "--calibration-votes", str(args.calibration_votes),
        *extra,
    ]
    if args.judge_model:
        command += ["--judge-model", args.judge_model]
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True)
    tail = "\n".join((result.stderr or "").splitlines()[-3:])
    return task, result.returncode, tail


def run_phase_over_tasks(
    tasks: list[pathlib.Path], args: argparse.Namespace, extra: list[str], phase_name: str
) -> list[pathlib.Path]:
    succeeded: list[pathlib.Path] = []
    with ThreadPoolExecutor(max_workers=max(1, args.parallel_tasks)) as pool:
        for task, code, tail in pool.map(lambda t: run_generate_rubric(t, args, extra), tasks):
            name = task.name
            if code == 0:
                succeeded.append(task)
                print(f"{phase_name}: {name}: ok")
            else:
                print(f"{phase_name}: {name}: FAILED (exit {code})\n  {tail}", file=sys.stderr)
    return succeeded


def judge_effort_of(args: argparse.Namespace) -> str | None:
    return None if args.judge_reasoning_effort.lower() == "none" else args.judge_reasoning_effort


def build_vote_requests(
    task_dir: pathlib.Path, args: argparse.Namespace
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]], int]:
    """Return (request lines, custom_id -> {task_dir, key} mapping, n already cached)."""
    generated_path = task_dir / "evals" / "rubric.generated.json"
    if not generated_path.exists():
        raise RuntimeError(f"No rubric.generated.json (phase 1 failed?): {task_dir}")
    generated = json.loads(generated_path.read_text(encoding="utf-8"))
    criteria = generated.get("final_criteria") or []
    if not criteria:
        raise RuntimeError(f"rubric.generated.json has no final_criteria: {task_dir}")

    task = gr.load_task(task_dir)
    solution_files = gr.discover_solution_files(task_dir, None)
    solution_output = gr.solution_output_text(solution_files)
    cache_dir = task_dir / "evals" / ".rubric-cache"
    judge_model = args.judge_model or args.model
    judge_effort = judge_effort_of(args)

    lines: list[dict[str, Any]] = []
    mapping: dict[str, dict[str, str]] = {}
    n_cached = 0
    for criterion in criteria:
        prompt = build_judge_prompt(task, task_dir, solution_output, criterion)
        for vote in range(max(1, args.calibration_votes)):
            key = gr.cache_key(
                {"judge_model": judge_model, "judge_effort": judge_effort, "prompt": prompt, "vote": vote}
            )
            if gr.cache_read(cache_dir, "judge", key) is not None:
                n_cached += 1
                continue
            body: dict[str, Any] = {
                "model": judge_model,
                "input": prompt,
                "text": {"format": {"type": "json_object"}},
            }
            if judge_effort:
                body["reasoning"] = {"effort": judge_effort}
            custom_id = f"v-{key}"
            mapping[custom_id] = {"task_dir": str(task_dir), "key": key}
            lines.append({"custom_id": custom_id, "method": "POST", "url": "/v1/responses", "body": body})
    return lines, mapping, n_cached


def write_chunks(lines: list[dict[str, Any]], run_dir: pathlib.Path) -> list[pathlib.Path]:
    chunks: list[pathlib.Path] = []
    current: list[str] = []
    current_bytes = 0

    def flush() -> None:
        nonlocal current, current_bytes
        if not current:
            return
        path = run_dir / f"batch-input-{len(chunks):03d}.jsonl"
        path.write_text("\n".join(current) + "\n", encoding="utf-8")
        chunks.append(path)
        current = []
        current_bytes = 0

    for line in lines:
        encoded = json.dumps(line, ensure_ascii=False)
        if current and (len(current) >= MAX_BATCH_REQUESTS or current_bytes + len(encoded) > MAX_BATCH_BYTES):
            flush()
        current.append(encoded)
        current_bytes += len(encoded) + 1
    flush()
    return chunks


def extract_output_text(body: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in body.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if content.get("type") == "output_text":
                parts.append(content.get("text") or "")
    return "".join(parts)


def vote_result_from_body(body: dict[str, Any]) -> dict[str, Any] | None:
    if body.get("status") == "incomplete":
        return None
    try:
        parsed = parse_json_response(extract_output_text(body))
    except (ValueError, json.JSONDecodeError):
        return None
    verdict = str(parsed.get("verdict", "")).lower()
    if verdict not in {"pass", "fail"}:
        return None
    evidence = parsed.get("evidence")
    if not isinstance(evidence, list):
        evidence = [str(evidence)] if evidence else []
    usage = body.get("usage") or {}
    summary = {key: usage[key] for key in ["input_tokens", "output_tokens", "total_tokens"] if key in usage}
    details = usage.get("input_tokens_details") or {}
    if isinstance(details, dict) and "cached_tokens" in details:
        summary["cached_input_tokens"] = details["cached_tokens"]
    return {
        "verdict": verdict,
        "reasoning": str(parsed.get("reasoning", "")),
        "evidence": [str(item) for item in evidence],
        "usage": summary,
    }


def harvest_output(content: str, mapping: dict[str, dict[str, str]]) -> tuple[int, int]:
    n_ok = 0
    n_bad = 0
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        entry = mapping.get(record.get("custom_id", ""))
        if entry is None:
            n_bad += 1
            continue
        response = record.get("response") or {}
        if record.get("error") or response.get("status_code") != 200:
            n_bad += 1
            continue
        result = vote_result_from_body(response.get("body") or {})
        if result is None:
            n_bad += 1
            continue
        cache_dir = pathlib.Path(entry["task_dir"]) / "evals" / ".rubric-cache"
        gr.cache_write(cache_dir, "judge", entry["key"], result)
        n_ok += 1
    return n_ok, n_bad


def save_state(run_dir: pathlib.Path, state: dict[str, Any]) -> None:
    (run_dir / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def poll_and_harvest(client: OpenAI, state: dict[str, Any], run_dir: pathlib.Path, args: argparse.Namespace) -> None:
    deadline = time.monotonic() + args.max_wait_hours * 3600
    pending = {b["batch_id"] for b in state["batches"] if b.get("status") not in TERMINAL_STATUSES}
    while pending:
        if time.monotonic() > deadline:
            save_state(run_dir, state)
            raise SystemExit(
                f"Batches still pending after {args.max_wait_hours}h: {sorted(pending)}. "
                f"Re-run with --resume {run_dir} later."
            )
        for entry in state["batches"]:
            if entry["batch_id"] not in pending:
                continue
            batch = client.batches.retrieve(entry["batch_id"])
            entry["status"] = batch.status
            counts = batch.request_counts
            print(
                f"batch {entry['batch_id']}: {batch.status}"
                + (f" ({counts.completed}/{counts.total} done, {counts.failed} failed)" if counts else ""),
                file=sys.stderr,
            )
            if batch.status in TERMINAL_STATUSES:
                pending.discard(entry["batch_id"])
                for file_attr in ["output_file_id", "error_file_id"]:
                    file_id = getattr(batch, file_attr, None)
                    if not file_id:
                        continue
                    content = client.files.content(file_id).text
                    n_ok, n_bad = harvest_output(content, state["mapping"])
                    print(f"batch {entry['batch_id']} {file_attr}: harvested {n_ok}, unusable {n_bad}", file=sys.stderr)
                save_state(run_dir, state)
        if pending:
            time.sleep(args.poll_seconds)
    save_state(run_dir, state)


def main() -> int:
    load_dotenv(REPO_ROOT / ".env", override=False)
    args = parse_args()

    if args.resume:
        run_dir = (args.resume if args.resume.is_absolute() else REPO_ROOT / args.resume).resolve()
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        tasks = [pathlib.Path(t) for t in state["tasks"]]
        client = OpenAI()
        poll_and_harvest(client, state, run_dir, args)
        print("Phase 5: finalizing rubrics (cached votes + refine + tagging)")
        finalized = run_phase_over_tasks(tasks, args, ["--write-final"], "finalize")
        print(f"Finalized {len(finalized)}/{len(tasks)} rubrics.")
        return 0 if len(finalized) == len(tasks) else 1

    tasks = resolve_tasks(args)
    votes = max(1, args.calibration_votes)
    if args.dry_run:
        print(f"Tasks: {len(tasks)}")
        for task in tasks:
            print(f"  - {task.relative_to(REPO_ROOT) if task.is_relative_to(REPO_ROOT) else task}")
        print(f"Generator model: {args.model} (effort {args.reasoning_effort})")
        print(f"Judge model: {args.judge_model or args.model} (effort {args.judge_reasoning_effort})")
        print(f"Votes per criterion: {votes}")
        print("Phases: draft (sync) -> batch round-1 votes -> harvest -> finalize (sync)")
        return 0

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set. Put it in the environment or .env.")

    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = (args.runs_dir if args.runs_dir.is_absolute() else REPO_ROOT / args.runs_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    print(f"Phase 1: drafting rubrics for {len(tasks)} task(s) (atomize -> candidates -> prune)")
    drafted = run_phase_over_tasks(tasks, args, ["--skip-calibration", "--skip-tagging"], "draft")
    if not drafted:
        raise SystemExit("Phase 1 produced no draft rubrics.")

    print("Phase 2: building calibration vote requests")
    lines: list[dict[str, Any]] = []
    mapping: dict[str, dict[str, str]] = {}
    total_cached = 0
    for task in drafted:
        task_lines, task_mapping, n_cached = build_vote_requests(task, args)
        lines.extend(task_lines)
        mapping.update(task_mapping)
        total_cached += n_cached
        print(f"  {task.name}: {len(task_lines)} votes to judge, {n_cached} already cached")

    state: dict[str, Any] = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model": args.model,
        "judge_model": args.judge_model or args.model,
        "judge_reasoning_effort": args.judge_reasoning_effort,
        "calibration_votes": votes,
        "tasks": [str(t) for t in drafted],
        "mapping": mapping,
        "batches": [],
    }

    if not lines:
        print("All votes already cached; skipping the batch entirely.")
    else:
        chunks = write_chunks(lines, run_dir)
        print(f"Phase 3: {len(lines)} vote requests in {len(chunks)} batch file(s) under {run_dir}")
        if args.prepare_only:
            save_state(run_dir, state)
            print(
                f"--prepare-only: wrote batch input files and state to {run_dir} without uploading. "
                "Inspect them, then re-run without --prepare-only; already-cached votes are skipped, "
                "so nothing is paid twice."
            )
            return 0
        client = OpenAI()
        for chunk in chunks:
            with chunk.open("rb") as handle:
                uploaded = client.files.create(file=handle, purpose="batch")
            batch = client.batches.create(
                input_file_id=uploaded.id,
                endpoint="/v1/responses",
                completion_window=args.completion_window,
                metadata={"description": f"LAB-EU rubric calibration votes {run_id}"},
            )
            state["batches"].append({"batch_id": batch.id, "input_file": str(chunk), "status": batch.status})
            print(f"submitted {chunk.name} as batch {batch.id}")
        save_state(run_dir, state)
        poll_and_harvest(client, state, run_dir, args)

    print("Phase 5: finalizing rubrics (cached votes + refine + tagging)")
    finalized = run_phase_over_tasks(drafted, args, ["--write-final"], "finalize")
    print(f"Finalized {len(finalized)}/{len(drafted)} rubrics. State: {run_dir / 'state.json'}")
    return 0 if len(finalized) == len(drafted) else 1


if __name__ == "__main__":
    raise SystemExit(main())
