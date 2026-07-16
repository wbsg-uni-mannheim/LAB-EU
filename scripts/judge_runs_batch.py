#!/usr/bin/env python3
"""Judge completed runs through the OpenAI Batch API (50% price).

Collects every (submission x criterion x vote) judge request across one or
more run directories, submits them as one Batch-API job set, harvests the
verdicts, and writes the same scores.json files that `evaluation.run` /
`judge_run.py` produce synchronously (both paths share assemble_scores()).

  python scripts/judge_runs_batch.py runs/baseline-x/<id> runs/opencode-y/<id> \
      --judge-model gpt-5.6-luna

Robustness:
- tasks that already have a complete scores.json (no error verdicts) are
  skipped, so re-running after an interruption never redoes finished work;
- interrupted after submission? re-run with --resume runs/judge-batches/<ts>;
- batch lines that fail or return unusable JSON are re-judged synchronously
  during finalize, so a handful of bad lines cannot block the scores.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import time
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evaluation.run import (  # noqa: E402
    DEFAULT_API_BASE,
    aggregate_votes,
    assemble_scores,
    call_judge,
    judge_prompt,
    load_agent_output,
    load_json,
    load_rubric,
    make_client,
    parse_json_response,
)

MAX_BATCH_REQUESTS = 45_000
MAX_BATCH_BYTES = 180 * 1024 * 1024
TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Judge run directories via the OpenAI Batch API.")
    parser.add_argument("run_dirs", nargs="*", type=pathlib.Path, help="Run dirs containing manifest.json and tasks/.")
    parser.add_argument("--judge-model", default="gpt-5.6-luna")
    parser.add_argument("--votes", type=int, default=1, help="Judge votes per criterion (majority; ties fail).")
    parser.add_argument("--reasoning-effort", default="medium", help="Judge reasoning effort; 'none' omits it.")
    parser.add_argument("--batches-dir", type=pathlib.Path, default=REPO_ROOT / "runs" / "judge-batches")
    parser.add_argument("--resume", type=pathlib.Path, help="Existing judge-batch dir: skip to poll/harvest/finalize.")
    parser.add_argument("--prepare-only", action="store_true", help="Write batch input files without uploading.")
    parser.add_argument("--no-skip-existing", action="store_true", help="Also re-judge tasks with complete scores.json.")
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--max-wait-hours", type=float, default=24.0)
    parser.add_argument("--completion-window", default="24h")
    return parser.parse_args()


def already_judged(task_run_dir: pathlib.Path) -> bool:
    scores_path = task_run_dir / "submission" / "scores.json"
    if not scores_path.exists():
        return False
    try:
        scores = json.loads(scores_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    results = scores.get("criteria_results")
    return bool(results) and not any(r.get("verdict") == "error" for r in results)


def collect_jobs(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Return (batch request lines, custom_id mapping, per-task work list)."""
    lines: list[dict[str, Any]] = []
    mapping: dict[str, dict[str, Any]] = {}
    tasks: list[dict[str, Any]] = []
    effort = None if args.reasoning_effort.lower() == "none" else args.reasoning_effort
    counter = 0

    for run_dir in args.run_dirs:
        run_dir = run_dir if run_dir.is_absolute() else REPO_ROOT / run_dir
        if not (run_dir / "manifest.json").exists():
            raise SystemExit(f"Missing run manifest: {run_dir / 'manifest.json'}")
        for metadata_path in sorted((run_dir / "tasks").glob("*/metadata.json")):
            task_run_dir = metadata_path.parent
            if not args.no_skip_existing and already_judged(task_run_dir):
                print(f"skip (already judged): {task_run_dir.parent.parent.name}/{task_run_dir.name}")
                continue
            metadata = load_json(metadata_path)
            task_dir = pathlib.Path(metadata["source_task_dir"])
            submission = task_run_dir / "submission"
            if not submission.is_dir() or not any(submission.iterdir()):
                print(f"WARNING: no submission for {task_run_dir.name}, skipping", file=sys.stderr)
                continue
            task = load_json(task_dir / "task.json")
            rubric_path, criteria = load_rubric(task_dir)
            task_entry = {
                "task_run_dir": str(task_run_dir),
                "task_dir": str(task_dir),
                "rubric_path": str(rubric_path),
                "custom_ids": {},  # criterion_id -> [custom_id per vote]
            }
            for criterion in criteria:
                prompt = judge_prompt(task, task_dir, load_agent_output(submission, criterion), criterion)
                ids = []
                for vote in range(max(1, args.votes)):
                    custom_id = f"j-{counter:06d}"
                    counter += 1
                    body: dict[str, Any] = {
                        "model": args.judge_model,
                        "input": prompt,
                        "text": {"format": {"type": "json_object"}},
                    }
                    if effort:
                        body["reasoning"] = {"effort": effort}
                    lines.append({"custom_id": custom_id, "method": "POST", "url": "/v1/responses", "body": body})
                    mapping[custom_id] = {"task_run_dir": str(task_run_dir), "criterion_id": criterion["id"], "vote": vote}
                    ids.append(custom_id)
                task_entry["custom_ids"][criterion["id"]] = ids
            tasks.append(task_entry)
    return lines, mapping, tasks


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


def save_state(batch_dir: pathlib.Path, state: dict[str, Any]) -> None:
    (batch_dir / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_results(batch_dir: pathlib.Path, results: dict[str, dict[str, Any]]) -> None:
    with (batch_dir / "results.jsonl").open("a", encoding="utf-8") as fh:
        for custom_id, result in results.items():
            fh.write(json.dumps({"custom_id": custom_id, "result": result}, ensure_ascii=False) + "\n")


def load_results(batch_dir: pathlib.Path) -> dict[str, dict[str, Any]]:
    path = batch_dir / "results.jsonl"
    results: dict[str, dict[str, Any]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                results[record["custom_id"]] = record["result"]
    return results


def harvest_content(content: str, mapping: dict[str, dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], int]:
    harvested: dict[str, dict[str, Any]] = {}
    n_bad = 0
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        custom_id = record.get("custom_id", "")
        if custom_id not in mapping:
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
        harvested[custom_id] = result
    return harvested, n_bad


def poll_and_harvest(client: OpenAI, state: dict[str, Any], batch_dir: pathlib.Path, args: argparse.Namespace) -> None:
    deadline = time.monotonic() + args.max_wait_hours * 3600
    pending = {b["batch_id"] for b in state["batches"] if b.get("status") not in TERMINAL_STATUSES}
    while pending:
        if time.monotonic() > deadline:
            save_state(batch_dir, state)
            raise SystemExit(
                f"Batches still pending after {args.max_wait_hours}h. Re-run with --resume {batch_dir} later."
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
                    harvested, n_bad = harvest_content(content, state["mapping"])
                    append_results(batch_dir, harvested)
                    print(
                        f"batch {entry['batch_id']} {file_attr}: harvested {len(harvested)}, unusable {n_bad}",
                        file=sys.stderr,
                    )
                save_state(batch_dir, state)
        if pending:
            time.sleep(args.poll_seconds)
    save_state(batch_dir, state)


def finalize(state: dict[str, Any], batch_dir: pathlib.Path, args: argparse.Namespace) -> int:
    results = load_results(batch_dir)
    effort = None if state["reasoning_effort"] is None else state["reasoning_effort"]
    sync_client = None
    n_sync = 0
    failures = 0

    for task_entry in state["tasks"]:
        task_run_dir = pathlib.Path(task_entry["task_run_dir"])
        submission = task_run_dir / "submission"
        if already_judged(task_run_dir) and not args.no_skip_existing:
            print(f"finalize skip (already judged): {task_run_dir.name}")
            continue
        task_dir = pathlib.Path(task_entry["task_dir"])
        task = load_json(task_dir / "task.json")
        rubric_path, criteria = load_rubric(task_dir)
        criteria_by_id = {c["id"]: c for c in criteria}

        aggregated: list[dict[str, Any]] = []
        for criterion_id, custom_ids in task_entry["custom_ids"].items():
            criterion = criteria_by_id.get(criterion_id)
            if criterion is None:
                # Rubric changed between submit and finalize; skip stale ids.
                print(f"WARNING: {task_run_dir.name}: criterion {criterion_id} no longer in rubric", file=sys.stderr)
                continue
            vote_results: list[dict[str, Any]] = []
            for custom_id in custom_ids:
                result = results.get(custom_id)
                if result is None:
                    # Missing or unusable batch line -> synchronous fallback.
                    if sync_client is None:
                        sync_client, _ = make_client(DEFAULT_API_BASE)
                    try:
                        prompt = judge_prompt(task, task_dir, load_agent_output(submission, criterion), criterion)
                        result = call_judge(sync_client, state["judge_model"], prompt, effort)
                        n_sync += 1
                    except Exception as exc:  # noqa: BLE001 - degrade to error verdict, never abort the run
                        result = {"verdict": "error", "reasoning": f"Judge call failed: {exc}", "evidence": [], "usage": {}}
                vote_results.append({"id": criterion_id, "title": criterion["title"], **result})
            aggregated.append(aggregate_votes(criterion, vote_results))

        missing = [c["id"] for c in criteria if c["id"] not in task_entry["custom_ids"]]
        if missing:
            print(f"WARNING: {task_run_dir.name}: no batch requests for {missing} (rubric grew?)", file=sys.stderr)

        scores = assemble_scores(
            task_dir=task_dir,
            submission=submission,
            rubric_path=rubric_path,
            task=task,
            criteria=[c for c in criteria if c["id"] in task_entry["custom_ids"]],
            results=aggregated,
            judge_model=state["judge_model"],
            api_base=DEFAULT_API_BASE + " (batch)",
            reasoning_effort=effort,
            votes=state["votes"],
            adaptive=False,
        )
        scores_path = submission / "scores.json"
        scores_path.write_text(json.dumps(scores, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (task_run_dir / "scores.json").write_text(
            json.dumps(scores, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        n_errors = scores["n_errors"]
        failures += int(n_errors > 0)
        print(
            f"{task_run_dir.parent.parent.name}/{task_run_dir.name}: "
            f"{scores['n_passed']}/{scores['n_criteria']} passed"
            + (f", {n_errors} error verdicts" if n_errors else "")
        )
    if n_sync:
        print(f"Synchronous fallback calls: {n_sync}", file=sys.stderr)
    return 1 if failures else 0


def main() -> int:
    load_dotenv(REPO_ROOT / ".env", override=False)
    args = parse_args()

    if args.resume:
        batch_dir = args.resume if args.resume.is_absolute() else REPO_ROOT / args.resume
        state = load_json(batch_dir / "state.json")
        client = OpenAI()
        poll_and_harvest(client, state, batch_dir, args)
        return finalize(state, batch_dir, args)

    if not args.run_dirs:
        raise SystemExit("Pass at least one run dir (or --resume <judge-batch-dir>).")

    lines, mapping, tasks = collect_jobs(args)
    if not tasks:
        print("Nothing to judge (all tasks already have complete scores).")
        return 0

    batch_dir = args.batches_dir / dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch_dir.mkdir(parents=True, exist_ok=True)
    chunks = write_chunks(lines, batch_dir)
    state: dict[str, Any] = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "judge_model": args.judge_model,
        "votes": max(1, args.votes),
        "reasoning_effort": None if args.reasoning_effort.lower() == "none" else args.reasoning_effort,
        "run_dirs": [str(p) for p in args.run_dirs],
        "tasks": tasks,
        "mapping": mapping,
        "batches": [],
    }
    save_state(batch_dir, state)
    print(f"{len(lines)} judge requests for {len(tasks)} task(s) in {len(chunks)} batch file(s) under {batch_dir}")

    if args.prepare_only:
        return 0

    client = OpenAI()
    for chunk in chunks:
        with chunk.open("rb") as handle:
            uploaded = client.files.create(file=handle, purpose="batch")
        batch = client.batches.create(
            input_file_id=uploaded.id,
            endpoint="/v1/responses",
            completion_window=args.completion_window,
        )
        state["batches"].append({"input_file": chunk.name, "batch_id": batch.id, "status": batch.status})
        print(f"submitted {chunk.name} as batch {batch.id}")
    save_state(batch_dir, state)

    poll_and_harvest(client, state, batch_dir, args)
    return finalize(state, batch_dir, args)


if __name__ == "__main__":
    raise SystemExit(main())
