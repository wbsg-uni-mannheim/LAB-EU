#!/usr/bin/env python3
"""Batch the first three Sol rubric-generation stages across many tasks.

The stages are dependent and therefore run as three sequential OpenAI batches:

1. atomize the gold solution;
2. generate three role-specific candidate pools;
3. prune the merged candidate pool.

Harvested responses are written to the exact step-cache keys used by
``generate_rubric.py``. After pruning, that script is run with calibration and
tagging disabled; every model call must then be a cache hit. No synchronous API
fallback is allowed by this orchestrator.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(REPO_ROOT))

import generate_rubric as gr  # noqa: E402

PHASES = ("atomize", "candidates", "prune")
TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}
MAX_BATCH_REQUESTS = 45_000
MAX_BATCH_BYTES = 180 * 1024 * 1024
SHORT_CONTEXT_LIMIT = 272_000
PRICING_AS_OF = "2026-07-28"
BATCH_PRICES_PER_MILLION = {
    "short": {"input": 2.50, "cached_input": 0.25, "cache_write": 3.125, "output": 15.00},
    "long": {"input": 5.00, "cached_input": 0.50, "cache_write": 6.25, "output": 22.50},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch atomization, candidate generation, and pruning for LAB-EU rubrics."
    )
    parser.add_argument("task_dirs", nargs="*", type=pathlib.Path)
    parser.add_argument("--taskset", type=pathlib.Path)
    parser.add_argument("--model", default=os.environ.get("OPENAI_RUBRIC_MODEL", gr.DEFAULT_MODEL))
    parser.add_argument("--reasoning-effort", default=gr.DEFAULT_REASONING_EFFORT)
    parser.add_argument("--artifact-suffix", default="broad-v1")
    parser.add_argument("--poll-seconds", type=int, default=30)
    parser.add_argument("--max-wait-hours", type=float, default=26.0)
    parser.add_argument("--completion-window", default="24h")
    parser.add_argument(
        "--runs-dir",
        type=pathlib.Path,
        default=REPO_ROOT / "runs" / "rubric-draft-batches",
    )
    parser.add_argument("--resume", type=pathlib.Path)
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Write and inspect the next batch input without uploading it.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def resolve_tasks(args: argparse.Namespace) -> list[pathlib.Path]:
    raw_tasks = list(args.task_dirs)
    if args.taskset:
        taskset = args.taskset if args.taskset.is_absolute() else REPO_ROOT / args.taskset
        for line in taskset.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            raw_tasks.append(pathlib.Path(json.loads(line)["task_dir"]))

    tasks: list[pathlib.Path] = []
    seen: set[pathlib.Path] = set()
    for raw in raw_tasks:
        task = (raw if raw.is_absolute() else REPO_ROOT / raw).resolve()
        if task in seen:
            continue
        seen.add(task)
        if not (task / "task.json").exists():
            raise SystemExit(f"Not a task directory (missing task.json): {task}")
        if not (task / "evals").exists():
            raise SystemExit(f"Task has no evals directory: {task}")
        gr.discover_solution_files(task, None)
        tasks.append(task)
    if not tasks:
        raise SystemExit("No tasks given. Pass task directories or --taskset.")
    return tasks


def normalize_step(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", label) or "call"


def task_context(task_dir: pathlib.Path) -> dict[str, Any]:
    task = gr.load_task(task_dir)
    solution_files = gr.discover_solution_files(task_dir, None)
    files, warnings = gr.collect_file_bundle(
        task_dir,
        solution_files,
        gr.MAX_FILE_CHARS,
        gr.MAX_TOTAL_CHARS,
    )
    return {
        "task": task,
        "files": files,
        "warnings": warnings,
        "bundle": json.loads(gr.task_bundle_json(task_dir, task, files)),
    }


def request_spec(
    *,
    task_dir: pathlib.Path,
    label: str,
    model: str,
    reasoning_effort: str | None,
    system: str,
    user: str,
    required_keys: set[str],
) -> dict[str, Any]:
    key, body = gr.build_api_request(
        model=model,
        system=system,
        user=user,
        reasoning_effort=reasoning_effort,
    )
    return {
        "task_dir": str(task_dir),
        "label": label,
        "step": normalize_step(label),
        "key": key,
        "required_keys": sorted(required_keys),
        "body": body,
    }


def atom_spec(task_dir: pathlib.Path, model: str, effort: str | None) -> dict[str, Any]:
    context = task_context(task_dir)
    system, user_base = gr.prompt_pair("atomize_solution")
    return request_spec(
        task_dir=task_dir,
        label="atomize_solution",
        model=model,
        reasoning_effort=effort,
        system=system,
        user=gr.build_user_payload(user_base, context["bundle"]),
        required_keys={"language", "jurisdiction", "reasoning_style", "atoms", "solution_gaps_or_warnings"},
    )


def cached_parsed(spec: dict[str, Any]) -> dict[str, Any]:
    cache_dir = pathlib.Path(spec["task_dir"]) / "evals" / ".rubric-cache"
    cached = gr.cache_read(cache_dir, spec["step"], spec["key"])
    if cached is None:
        raise RuntimeError(
            f"Missing prerequisite cache for {spec['label']} in {spec['task_dir']}"
        )
    return cached["parsed"]


def candidate_specs(task_dir: pathlib.Path, model: str, effort: str | None) -> list[dict[str, Any]]:
    context = task_context(task_dir)
    atoms = cached_parsed(atom_spec(task_dir, model, effort))
    system, user_base = gr.prompt_pair("generate_candidate_criteria")
    payload = {
        "task_json": context["task"],
        "task_files": context["files"],
        "atomization": atoms,
    }
    common_user = gr.build_user_payload(user_base, payload)
    specs: list[dict[str, Any]] = []
    for role_name, _role_code in gr.CANDIDATE_ROLES:
        role_text = gr.read_prompt_template(f"roles/{role_name}.txt")
        specs.append(
            request_spec(
                task_dir=task_dir,
                label=f"candidates/{role_name}",
                model=model,
                reasoning_effort=effort,
                system=system,
                user=common_user + "\n\n" + role_text,
                required_keys={"language", "criteria", "generation_notes"},
            )
        )
    return specs


def merged_candidates(task_dir: pathlib.Path, model: str, effort: str | None) -> dict[str, Any]:
    by_role: dict[str, dict[str, Any]] = {}
    merged: list[dict[str, Any]] = []
    specs = candidate_specs(task_dir, model, effort)
    for (role_name, role_code), spec in zip(gr.CANDIDATE_ROLES, specs, strict=True):
        parsed = copy.deepcopy(cached_parsed(spec))
        for index, criterion in enumerate(parsed.get("criteria", []), start=1):
            criterion["id"] = f"K-{role_code}-{index:03d}"
            criterion["generator_role"] = role_name
        by_role[role_name] = parsed
        merged.extend(parsed.get("criteria", []))
    return {
        "language": next(iter(by_role.values())).get("language") if by_role else None,
        "criteria": merged,
        "generation_notes_by_role": {
            role: parsed.get("generation_notes", []) for role, parsed in by_role.items()
        },
    }


def prune_spec(task_dir: pathlib.Path, model: str, effort: str | None) -> dict[str, Any]:
    context = task_context(task_dir)
    atoms = cached_parsed(atom_spec(task_dir, model, effort))
    candidates = merged_candidates(task_dir, model, effort)
    system, user_base = gr.prompt_pair("prune_rubric")
    return request_spec(
        task_dir=task_dir,
        label="prune_criteria",
        model=model,
        reasoning_effort=effort,
        system=system,
        user=gr.build_user_payload(
            user_base,
            {
                "task_json": context["task"],
                "atomization": atoms,
                "candidate_rubric": candidates,
            },
        ),
        required_keys={
            "language",
            "criteria",
            "rejected_candidates",
            "pruning_notes",
            "coverage_audit",
        },
    )


def phase_specs(
    phase: str,
    tasks: list[pathlib.Path],
    model: str,
    effort: str | None,
) -> list[dict[str, Any]]:
    if phase == "atomize":
        return [atom_spec(task, model, effort) for task in tasks]
    if phase == "candidates":
        return [spec for task in tasks for spec in candidate_specs(task, model, effort)]
    if phase == "prune":
        return [prune_spec(task, model, effort) for task in tasks]
    raise ValueError(f"Unknown phase: {phase}")


def custom_id(phase: str, spec: dict[str, Any]) -> str:
    task_hash = hashlib.sha256(spec["task_dir"].encode("utf-8")).hexdigest()[:8]
    label = normalize_step(spec["label"])[:12]
    return f"{phase[:4]}-{task_hash}-{label}-{spec['key']}"


def save_state(run_dir: pathlib.Path, state: dict[str, Any]) -> None:
    (run_dir / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def prepare_phase(run_dir: pathlib.Path, state: dict[str, Any]) -> dict[str, Any]:
    phase = state["current_phase"]
    tasks = [pathlib.Path(path) for path in state["tasks"]]
    specs = phase_specs(phase, tasks, state["model"], state["reasoning_effort"])
    mapping: dict[str, dict[str, Any]] = {}
    lines: list[str] = []
    cached_count = 0
    for spec in specs:
        cache_dir = pathlib.Path(spec["task_dir"]) / "evals" / ".rubric-cache"
        if gr.cache_read(cache_dir, spec["step"], spec["key"]) is not None:
            cached_count += 1
            continue
        cid = custom_id(phase, spec)
        if cid in mapping:
            raise RuntimeError(f"Duplicate Batch custom_id: {cid}")
        mapping[cid] = {key: value for key, value in spec.items() if key != "body"}
        lines.append(
            json.dumps(
                {
                    "custom_id": cid,
                    "method": "POST",
                    "url": "/v1/responses",
                    "body": spec["body"],
                },
                ensure_ascii=False,
            )
        )

    size_bytes = sum(len(line.encode("utf-8")) + 1 for line in lines)
    if len(lines) > MAX_BATCH_REQUESTS:
        raise RuntimeError(f"{phase} has {len(lines)} requests; limit is {MAX_BATCH_REQUESTS}.")
    if size_bytes > MAX_BATCH_BYTES:
        raise RuntimeError(f"{phase} input is {size_bytes} bytes; safety limit is {MAX_BATCH_BYTES}.")

    input_path = run_dir / f"{phase}-input.jsonl"
    input_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    phase_state = {
        "status": "prepared" if lines else "completed",
        "requests": len(lines),
        "cached": cached_count,
        "input_file": str(input_path),
        "input_bytes": size_bytes,
        "mapping": mapping,
        "batch_id": None,
        "output_file_id": None,
        "error_file_id": None,
        "harvested": 0,
        "unusable": 0,
    }
    state["phases"][phase] = phase_state
    save_state(run_dir, state)
    print(
        f"Prepared {phase}: {len(lines)} requests, {cached_count} cache hits, "
        f"{size_bytes / 1024 / 1024:.2f} MiB -> {input_path}"
    )
    return phase_state


def make_client() -> OpenAI:
    return gr.make_client(os.environ.get("OPENAI_API_BASE", gr.DEFAULT_API_BASE))


def submit_phase(
    client: OpenAI,
    run_dir: pathlib.Path,
    state: dict[str, Any],
    phase_state: dict[str, Any],
    completion_window: str,
) -> None:
    phase = state["current_phase"]
    with pathlib.Path(phase_state["input_file"]).open("rb") as handle:
        uploaded = client.files.create(file=handle, purpose="batch")
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/responses",
        completion_window=completion_window,
        metadata={"description": f"LAB-EU Sol rubric draft {phase} {run_dir.name}"},
    )
    phase_state["batch_id"] = batch.id
    phase_state["status"] = batch.status
    phase_state["uploaded_file_id"] = uploaded.id
    save_state(run_dir, state)
    print(f"Submitted {phase}: {batch.id}")


def extract_output_text(body: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in body.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if content.get("type") == "output_text":
                chunks.append(content.get("text") or "")
    return "".join(chunks)


def parse_batch_body(body: dict[str, Any], required_keys: set[str]) -> dict[str, Any] | None:
    if body.get("status") == "incomplete":
        return None
    try:
        parsed = json.loads(extract_output_text(body))
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(parsed, dict) or required_keys - set(parsed):
        return None
    return parsed


def harvest_output(
    content: str,
    mapping: dict[str, dict[str, Any]],
    usage_by_request: dict[str, dict[str, Any]],
) -> tuple[int, int]:
    harvested = 0
    unusable = 0
    for raw_line in content.splitlines():
        if not raw_line.strip():
            continue
        record = json.loads(raw_line)
        cid = record.get("custom_id", "")
        spec = mapping.get(cid)
        response = record.get("response") or {}
        if spec is None or record.get("error") or response.get("status_code") != 200:
            unusable += 1
            continue
        body = response.get("body") or {}
        parsed = parse_batch_body(body, set(spec["required_keys"]))
        if parsed is None:
            unusable += 1
            continue
        cache_dir = pathlib.Path(spec["task_dir"]) / "evals" / ".rubric-cache"
        gr.cache_write(
            cache_dir,
            spec["step"],
            spec["key"],
            {"parsed": parsed, "response": {"usage": body.get("usage")}},
        )
        usage_by_request[cid] = {
            "phase": spec["label"],
            "task_dir": spec["task_dir"],
            "usage": gr.usage_summary(body),
        }
        harvested += 1
    return harvested, unusable


def poll_and_harvest(
    client: OpenAI,
    run_dir: pathlib.Path,
    state: dict[str, Any],
    phase_state: dict[str, Any],
    poll_seconds: int,
    max_wait_hours: float,
) -> None:
    deadline = time.monotonic() + max_wait_hours * 3600
    batch_id = phase_state["batch_id"]
    while True:
        batch = client.batches.retrieve(batch_id)
        phase_state["status"] = batch.status
        counts = batch.request_counts
        print(
            f"batch {batch_id}: {batch.status}"
            + (
                f" ({counts.completed}/{counts.total} completed, {counts.failed} failed)"
                if counts
                else ""
            ),
            flush=True,
        )
        save_state(run_dir, state)
        if batch.status in TERMINAL_STATUSES:
            phase_state["output_file_id"] = getattr(batch, "output_file_id", None)
            phase_state["error_file_id"] = getattr(batch, "error_file_id", None)
            break
        if time.monotonic() > deadline:
            raise SystemExit(
                f"Batch still pending after {max_wait_hours}h. Resume with --resume {run_dir}."
            )
        time.sleep(max(1, poll_seconds))

    if phase_state["status"] != "completed":
        save_state(run_dir, state)
        raise SystemExit(f"Batch {batch_id} ended with status {phase_state['status']}.")

    if phase_state["output_file_id"]:
        content = client.files.content(phase_state["output_file_id"]).text
        (run_dir / f"{state['current_phase']}-output.jsonl").write_text(content, encoding="utf-8")
        ok, bad = harvest_output(content, phase_state["mapping"], state["usage_by_request"])
        phase_state["harvested"] = ok
        phase_state["unusable"] = bad
    if phase_state["error_file_id"]:
        errors = client.files.content(phase_state["error_file_id"]).text
        (run_dir / f"{state['current_phase']}-errors.jsonl").write_text(errors, encoding="utf-8")

    missing = []
    for cid, spec in phase_state["mapping"].items():
        cache_dir = pathlib.Path(spec["task_dir"]) / "evals" / ".rubric-cache"
        if gr.cache_read(cache_dir, spec["step"], spec["key"]) is None:
            missing.append(cid)
    if missing:
        phase_state["status"] = "incomplete_harvest"
        phase_state["missing_custom_ids"] = missing
        save_state(run_dir, state)
        raise SystemExit(
            f"{state['current_phase']} harvested {phase_state['harvested']}/"
            f"{phase_state['requests']} requests; {len(missing)} remain missing. "
            "Start a new run to submit only missing cache entries."
        )
    phase_state["status"] = "completed"
    save_state(run_dir, state)


def estimated_batch_cost(usage: dict[str, Any]) -> float:
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    details = usage.get("input_tokens_details") or {}
    cached = int(details.get("cached_tokens") or 0)
    cache_write = int(details.get("cache_write_tokens") or 0)
    uncached = max(0, input_tokens - cached - cache_write)
    tier = "long" if input_tokens > SHORT_CONTEXT_LIMIT else "short"
    prices = BATCH_PRICES_PER_MILLION[tier]
    return (
        uncached * prices["input"]
        + cached * prices["cached_input"]
        + cache_write * prices["cache_write"]
        + output_tokens * prices["output"]
    ) / 1_000_000


def write_cost_summary(run_dir: pathlib.Path, state: dict[str, Any]) -> dict[str, Any]:
    by_phase: dict[str, dict[str, Any]] = {}
    total_cost = 0.0
    totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    for item in state["usage_by_request"].values():
        usage = item["usage"]
        phase = item["phase"]
        row = by_phase.setdefault(
            phase,
            {"requests": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "estimated_batch_usd": 0.0},
        )
        row["requests"] += 1
        for key in totals:
            value = int(usage.get(key) or 0)
            row[key] += value
            totals[key] += value
        cost = estimated_batch_cost(usage)
        row["estimated_batch_usd"] += cost
        total_cost += cost

    for row in by_phase.values():
        row["estimated_batch_usd"] = round(row["estimated_batch_usd"], 6)
    task_count = len(state["tasks"])
    summary = {
        "pricing_as_of": PRICING_AS_OF,
        "model": state["model"],
        "reasoning_effort": state["reasoning_effort"],
        "task_count": task_count,
        "request_count": len(state["usage_by_request"]),
        **totals,
        "estimated_batch_usd": round(total_cost, 6),
        "estimated_standard_usd_same_tokens": round(total_cost * 2, 6),
        "projected_45_cases_batch_usd": round(total_cost / task_count * 45, 6) if task_count else None,
        "by_phase": by_phase,
        "notes": [
            "Estimate uses official OpenAI direct-US Batch prices current on the pricing date.",
            "All observed requests are priced individually as short or long context using the 272K threshold.",
            "The projection covers atomization, three candidate roles, and pruning only; calibration, negative tests, outline, and tagging are excluded.",
        ],
    }
    (run_dir / "cost-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Kostenübersicht: Sol-Draft-Batch",
        "",
        f"- Fälle: {task_count}",
        f"- Requests: {summary['request_count']}",
        f"- Input-Tokens: {summary['input_tokens']:,}",
        f"- Output-Tokens einschließlich Reasoning: {summary['output_tokens']:,}",
        f"- Geschätzte Batch-Kosten: ${summary['estimated_batch_usd']:.4f}",
        f"- Geschätzte synchrone Kosten bei identischen Tokens: ${summary['estimated_standard_usd_same_tokens']:.4f}",
        f"- Lineare Hochrechnung auf 45 Fälle: ${summary['projected_45_cases_batch_usd']:.4f}",
        "",
        "| Phase | Requests | Input | Output | Batch USD |",
        "|---|---:|---:|---:|---:|",
    ]
    for phase, row in sorted(by_phase.items()):
        lines.append(
            f"| {phase} | {row['requests']} | {row['input_tokens']:,} | "
            f"{row['output_tokens']:,} | ${row['estimated_batch_usd']:.4f} |"
        )
    lines.extend(
        [
            "",
            f"Preise: OpenAI Batch, Stand {PRICING_AS_OF}. Die Hochrechnung umfasst nur die ersten drei Generierungsstufen.",
        ]
    )
    (run_dir / "cost-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def verify_all_caches(state: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    tasks = [pathlib.Path(path) for path in state["tasks"]]
    for phase in PHASES:
        for spec in phase_specs(phase, tasks, state["model"], state["reasoning_effort"]):
            cache_dir = pathlib.Path(spec["task_dir"]) / "evals" / ".rubric-cache"
            if gr.cache_read(cache_dir, spec["step"], spec["key"]) is None:
                missing.append(f"{spec['task_dir']}::{spec['label']}")
    return missing


def finalize_drafts(run_dir: pathlib.Path, state: dict[str, Any]) -> None:
    missing = verify_all_caches(state)
    if missing:
        raise SystemExit(
            "Refusing synchronous fallback; prerequisite caches are missing:\n- "
            + "\n- ".join(missing)
        )
    results: list[dict[str, Any]] = []
    for task in [pathlib.Path(path) for path in state["tasks"]]:
        command = [
            sys.executable,
            str(SCRIPTS_DIR / "generate_rubric.py"),
            str(task),
            "--model",
            state["model"],
            "--reasoning-effort",
            state["reasoning_effort"] or "none",
            "--skip-calibration",
            "--skip-tagging",
            "--artifact-suffix",
            state["artifact_suffix"],
        ]
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        output = task / "evals" / f"rubric.generated.{state['artifact_suffix']}.json"
        results.append(
            {
                "task_dir": str(task),
                "returncode": result.returncode,
                "output": str(output),
                "stderr_tail": "\n".join(result.stderr.splitlines()[-8:]),
            }
        )
        print(f"finalize {task.name}: {'ok' if result.returncode == 0 else 'FAILED'}")
    state["finalization"] = results
    if any(item["returncode"] != 0 for item in results):
        state["status"] = "finalization_failed"
        save_state(run_dir, state)
        raise SystemExit("At least one cached draft failed local finalization; inspect state.json.")
    state["status"] = "completed"
    state["completed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    save_state(run_dir, state)


def next_phase(phase: str) -> str | None:
    index = PHASES.index(phase)
    return PHASES[index + 1] if index + 1 < len(PHASES) else None


def run_pipeline(run_dir: pathlib.Path, state: dict[str, Any], args: argparse.Namespace) -> int:
    client: OpenAI | None = None
    while state.get("current_phase"):
        phase = state["current_phase"]
        phase_state = state["phases"].get(phase)
        if phase_state is None:
            phase_state = prepare_phase(run_dir, state)
        if phase_state["status"] == "prepared":
            if args.prepare_only:
                print(f"Prepared without upload. Continue with: --resume {run_dir}")
                return 0
            client = client or make_client()
            submit_phase(client, run_dir, state, phase_state, args.completion_window)
        if phase_state["status"] != "completed":
            client = client or make_client()
            poll_and_harvest(
                client,
                run_dir,
                state,
                phase_state,
                args.poll_seconds,
                args.max_wait_hours,
            )
        following = next_phase(phase)
        state["current_phase"] = following
        save_state(run_dir, state)
        if following is None:
            break

    finalize_drafts(run_dir, state)
    summary = write_cost_summary(run_dir, state)
    print(
        f"Completed {len(state['tasks'])} draft rubrics. "
        f"Estimated Batch cost: ${summary['estimated_batch_usd']:.4f}. "
        f"Run: {run_dir}"
    )
    return 0


def main() -> int:
    load_dotenv(REPO_ROOT / ".env", override=False)
    args = parse_args()
    if args.resume:
        run_dir = (args.resume if args.resume.is_absolute() else REPO_ROOT / args.resume).resolve()
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        args.model = state["model"]
        args.reasoning_effort = state["reasoning_effort"] or "none"
        args.artifact_suffix = state["artifact_suffix"]
        if state.get("status") == "completed":
            summary = write_cost_summary(run_dir, state)
            print(f"Run already completed: {run_dir} (${summary['estimated_batch_usd']:.4f})")
            return 0
        return run_pipeline(run_dir, state, args)

    if args.model != "gpt-5.6-sol":
        raise SystemExit("This pilot is intentionally pinned to --model gpt-5.6-sol.")
    suffix = args.artifact_suffix.strip()
    if not suffix or not re.fullmatch(r"[A-Za-z0-9_-]+", suffix):
        raise SystemExit("--artifact-suffix must contain only letters, digits, '_' and '-'.")
    effort = None if args.reasoning_effort.lower() == "none" else args.reasoning_effort
    tasks = resolve_tasks(args)
    contexts = {str(task): task_context(task) for task in tasks}
    if args.dry_run:
        print(f"Tasks: {len(tasks)}")
        print(f"Model: {args.model} (effort {effort})")
        print("Sequential Batch phases: atomize (N) -> candidates (3N) -> prune (N)")
        print(f"Planned requests without cache hits: {len(tasks) * 5}")
        for task in tasks:
            warnings = contexts[str(task)]["warnings"]
            print(f"- {task.relative_to(REPO_ROOT)}" + (f" WARNINGS={warnings}" if warnings else ""))
        return 0

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set.")
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    runs_dir = args.runs_dir if args.runs_dir.is_absolute() else REPO_ROOT / args.runs_dir
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    state = {
        "schema_version": "0.1",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "running",
        "model": args.model,
        "reasoning_effort": effort,
        "artifact_suffix": suffix,
        "tasks": [str(task) for task in tasks],
        "input_warnings": {
            task: context["warnings"] for task, context in contexts.items() if context["warnings"]
        },
        "current_phase": "atomize",
        "phases": {},
        "usage_by_request": {},
    }
    save_state(run_dir, state)
    return run_pipeline(run_dir, state, args)


if __name__ == "__main__":
    raise SystemExit(main())
