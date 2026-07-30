#!/usr/bin/env python3
"""Validate existing generated rubrics against their gold solutions.

OpenAI committee members are submitted through the Batch API. Committee
members on OpenAI-compatible third-party endpoints (currently Gemini through
OpenRouter) run concurrently. The run is resumable and never edits rubrics.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evaluation.run import (  # noqa: E402
    DEFAULT_API_BASE,
    JudgeSpec,
    add_judge_metadata,
    call_judge,
    judge_prompt,
    load_judge_committee,
    make_client,
    normalize_judge_result,
    parse_json_response,
)
from scripts import generate_rubric as gr  # noqa: E402


TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}
DEFAULT_COMMITTEE = REPO_ROOT / "configs" / "judge-committee-rubric-calibration.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--taskset", type=pathlib.Path, required=False)
    parser.add_argument("task_dirs", nargs="*", type=pathlib.Path)
    parser.add_argument("--artifact-suffix", default="broad-v1")
    parser.add_argument("--committee", type=pathlib.Path, default=DEFAULT_COMMITTEE)
    parser.add_argument("--runs-dir", type=pathlib.Path, default=REPO_ROOT / "runs" / "rubric-validations")
    parser.add_argument("--resume", type=pathlib.Path)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--max-wait-hours", type=float, default=26.0)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: pathlib.Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_tasks(args: argparse.Namespace) -> list[pathlib.Path]:
    raw_tasks = list(args.task_dirs)
    if args.taskset:
        taskset = args.taskset if args.taskset.is_absolute() else REPO_ROOT / args.taskset
        for line in taskset.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                raw_tasks.append(pathlib.Path(json.loads(line)["task_dir"]))
    tasks: list[pathlib.Path] = []
    seen: set[pathlib.Path] = set()
    for raw in raw_tasks:
        task = (raw if raw.is_absolute() else REPO_ROOT / raw).resolve()
        if task in seen:
            continue
        seen.add(task)
        if not (task / "task.json").exists():
            raise SystemExit(f"Missing task.json: {task}")
        tasks.append(task)
    if not tasks:
        raise SystemExit("Pass --taskset or one or more task directories.")
    return tasks


def artifact_path(task: pathlib.Path, suffix: str) -> pathlib.Path:
    suffix = suffix.strip()
    return task / "evals" / f"rubric.generated{'.' + suffix if suffix else ''}.json"


def load_criteria(path: pathlib.Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Missing generated rubric: {path}")
    data = read_json(path)
    criteria = data.get("final_criteria") or data.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise SystemExit(f"No criteria in generated rubric: {path}")
    return criteria


def result_key(task_index: int, criterion_index: int, judge_name: str) -> str:
    return f"g-{task_index:02d}-{criterion_index:03d}-{judge_name}"


def build_work(
    tasks: list[pathlib.Path], specs: list[JudgeSpec], suffix: str
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    work: list[dict[str, Any]] = []
    mapping: dict[str, dict[str, Any]] = {}
    requests_by_judge: dict[str, list[dict[str, Any]]] = {spec.name: [] for spec in specs}
    for task_index, task_dir in enumerate(tasks):
        task = read_json(task_dir / "task.json")
        rubric = artifact_path(task_dir, suffix)
        criteria = load_criteria(rubric)
        solution = gr.solution_output_text(gr.discover_solution_files(task_dir, None))
        criterion_rows: list[dict[str, Any]] = []
        for criterion_index, criterion in enumerate(criteria):
            prompt = judge_prompt(task, task_dir, solution, criterion)
            keys: dict[str, str] = {}
            for spec in specs:
                key = result_key(task_index, criterion_index, spec.name)
                keys[spec.name] = key
                mapping[key] = {
                    "task_index": task_index,
                    "criterion_index": criterion_index,
                    "task_dir": str(task_dir),
                    "rubric_path": str(rubric),
                    "criterion_id": criterion["id"],
                    "judge": spec.as_dict(),
                    "prompt": prompt,
                }
                if spec.api_base == DEFAULT_API_BASE:
                    body: dict[str, Any] = {
                        "model": spec.model,
                        "input": prompt,
                        "text": {"format": {"type": "json_object"}},
                    }
                    if spec.reasoning_effort:
                        body["reasoning"] = {"effort": spec.reasoning_effort}
                    requests_by_judge[spec.name].append(
                        {"custom_id": key, "method": "POST", "url": "/v1/responses", "body": body}
                    )
            criterion_rows.append(
                {
                    "criterion_id": criterion["id"],
                    "title": criterion.get("title", ""),
                    "judge_keys": keys,
                }
            )
        work.append(
            {
                "task_id": str(task_dir.relative_to(REPO_ROOT / "tasks")),
                "task_dir": str(task_dir),
                "rubric_path": str(rubric),
                "n_criteria": len(criteria),
                "criteria": criterion_rows,
            }
        )
    return work, mapping, requests_by_judge


def write_jsonl(path: pathlib.Path, lines: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines),
        encoding="utf-8",
    )


def load_results(run_dir: pathlib.Path) -> dict[str, dict[str, Any]]:
    path = run_dir / "results.jsonl"
    results: dict[str, dict[str, Any]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                results[record["key"]] = record
    return results


def append_results(run_dir: pathlib.Path, records: list[dict[str, Any]]) -> None:
    existing = load_results(run_dir)
    new = [record for record in records if record["key"] not in existing]
    if not new:
        return
    with (run_dir / "results.jsonl").open("a", encoding="utf-8") as handle:
        for record in new:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def extract_output_text(body: dict[str, Any]) -> str:
    parts: list[str] = []
    for output in body.get("output") or []:
        if output.get("type") == "message":
            for content in output.get("content") or []:
                if content.get("type") == "output_text":
                    parts.append(str(content.get("text") or ""))
    return "".join(parts)


def parse_batch_result(body: dict[str, Any]) -> dict[str, Any] | None:
    if body.get("status") == "incomplete":
        return None
    try:
        parsed = parse_json_response(extract_output_text(body))
    except (ValueError, json.JSONDecodeError):
        return None
    return normalize_judge_result(parsed, body.get("usage") or {})


def harvest_file(
    client: OpenAI,
    file_id: str,
    mapping: dict[str, dict[str, Any]],
    run_dir: pathlib.Path,
) -> tuple[int, int]:
    records: list[dict[str, Any]] = []
    bad = 0
    for line in client.files.content(file_id).text.splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        key = item.get("custom_id", "")
        response = item.get("response") or {}
        meta = mapping.get(key)
        result = None
        if meta and not item.get("error") and response.get("status_code") == 200:
            result = parse_batch_result(response.get("body") or {})
        if result is None:
            bad += 1
            continue
        records.append({"key": key, "meta": meta, "result": add_judge_metadata(result, JudgeSpec(**meta["judge"]))})
    append_results(run_dir, records)
    return len(records), bad


def run_external_judges(
    state: dict[str, Any], specs: list[JudgeSpec], run_dir: pathlib.Path
) -> None:
    existing = load_results(run_dir)
    external = {spec.name: spec for spec in specs if spec.api_base != DEFAULT_API_BASE}
    jobs = [
        (key, meta, external[meta["judge"]["name"]])
        for key, meta in state["mapping"].items()
        if meta["judge"]["name"] in external and key not in existing
    ]
    if not jobs:
        return
    clients = {name: make_client(spec.api_base) for name, spec in external.items()}

    def run(job: tuple[str, dict[str, Any], JudgeSpec]) -> dict[str, Any]:
        key, meta, spec = job
        client, use_chat = clients[spec.name]
        try:
            result = call_judge(client, spec.model, meta["prompt"], spec.reasoning_effort, use_chat)
        except Exception as exc:  # noqa: BLE001 - preserve the run and expose the error
            result = {"verdict": "error", "reasoning": str(exc), "evidence": [], "usage": {}}
        return {"key": key, "meta": meta, "result": add_judge_metadata(result, spec)}

    workers = max(spec.parallel or 1 for spec in external.values())
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        append_results(run_dir, list(pool.map(run, jobs)))


def poll_batches(state: dict[str, Any], run_dir: pathlib.Path, args: argparse.Namespace) -> None:
    client = OpenAI()
    deadline = time.monotonic() + args.max_wait_hours * 3600
    pending = {entry["batch_id"] for entry in state["batches"] if entry["status"] not in TERMINAL_STATUSES}
    while pending:
        if time.monotonic() > deadline:
            save_json(run_dir / "state.json", state)
            raise SystemExit(f"Batches still pending; resume with --resume {run_dir}")
        for entry in state["batches"]:
            if entry["batch_id"] not in pending:
                continue
            batch = client.batches.retrieve(entry["batch_id"])
            entry["status"] = batch.status
            counts = batch.request_counts
            entry["request_counts"] = (
                {"completed": counts.completed, "total": counts.total, "failed": counts.failed}
                if counts else None
            )
            print(
                f"{entry['judge']}: {batch.status}"
                + (f" ({counts.completed}/{counts.total}, {counts.failed} failed)" if counts else ""),
                flush=True,
            )
            if batch.status in TERMINAL_STATUSES:
                pending.remove(entry["batch_id"])
                for attr in ("output_file_id", "error_file_id"):
                    file_id = getattr(batch, attr, None)
                    if file_id:
                        ok, bad = harvest_file(client, file_id, state["mapping"], run_dir)
                        print(f"{entry['judge']}: harvested {ok}, unusable {bad}", flush=True)
        save_json(run_dir / "state.json", state)
        if pending:
            time.sleep(args.poll_seconds)


def write_summary(state: dict[str, Any], run_dir: pathlib.Path) -> dict[str, Any]:
    results = load_results(run_dir)
    cases: list[dict[str, Any]] = []
    total_unanimous = total_dissent = total_failed = total_errors = 0
    for task in state["tasks"]:
        criterion_rows: list[dict[str, Any]] = []
        for criterion in task["criteria"]:
            votes = [results.get(key) for key in criterion["judge_keys"].values()]
            verdicts = [vote["result"].get("verdict") if vote else "missing" for vote in votes]
            passes = verdicts.count("pass")
            errors = sum(verdict in {"error", "missing"} for verdict in verdicts)
            if errors:
                status = "error"
                total_errors += 1
            elif passes == len(verdicts):
                status = "unanimous_pass"
                total_unanimous += 1
            elif passes >= 2:
                status = "majority_pass"
                total_dissent += 1
            else:
                status = "failed_gold"
                total_failed += 1
            criterion_rows.append({**criterion, "verdicts": verdicts, "status": status})
        case_status = (
            "blocked" if any(row["status"] in {"failed_gold", "error"} for row in criterion_rows)
            else "review" if any(row["status"] == "majority_pass" for row in criterion_rows)
            else "ready"
        )
        cases.append({**task, "status": case_status, "criteria": criterion_rows})
    summary = {
        "schema_version": "0.1",
        "created_at": state["created_at"],
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "artifact_suffix": state["artifact_suffix"],
        "judges": state["judges"],
        "n_cases": len(cases),
        "n_criteria": sum(case["n_criteria"] for case in cases),
        "n_expected_votes": sum(case["n_criteria"] for case in cases) * len(state["judges"]),
        "n_recorded_votes": len(results),
        "criteria_outcomes": {
            "unanimous_pass": total_unanimous,
            "majority_pass": total_dissent,
            "failed_gold": total_failed,
            "error_or_missing": total_errors,
        },
        "case_outcomes": {
            status: sum(case["status"] == status for case in cases)
            for status in ("ready", "review", "blocked")
        },
        "cases": cases,
    }
    save_json(run_dir / "summary.json", summary)
    lines = [
        "# Positive Rubrikenvalidierung",
        "",
        f"- Fälle: {summary['n_cases']}",
        f"- Kriterien: {summary['n_criteria']}",
        f"- Stimmen: {summary['n_recorded_votes']} / {summary['n_expected_votes']}",
        f"- Einstimmig bestanden: {total_unanimous}",
        f"- Mit Dissens bestanden: {total_dissent}",
        f"- Gold-Fehler: {total_failed}",
        f"- Fehler/fehlend: {total_errors}",
        "",
        "| Fall | Kriterien | Status |",
        "|---|---:|---|",
        *[f"| {pathlib.Path(case['task_dir']).name} | {case['n_criteria']} | {case['status']} |" for case in cases],
        "",
    ]
    (run_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    state["status"] = "completed"
    save_json(run_dir / "state.json", state)
    return summary


def main() -> int:
    load_dotenv(REPO_ROOT / ".env", override=False)
    args = parse_args()
    specs = load_judge_committee(args.committee)

    if args.resume:
        run_dir = (args.resume if args.resume.is_absolute() else REPO_ROOT / args.resume).resolve()
        state = read_json(run_dir / "state.json")
        specs = [JudgeSpec(**spec) for spec in state["judges"]]
        run_external_judges(state, specs, run_dir)
        poll_batches(state, run_dir, args)
        summary = write_summary(state, run_dir)
        print(f"Completed: {summary['n_recorded_votes']}/{summary['n_expected_votes']} votes")
        return 0 if summary["n_recorded_votes"] == summary["n_expected_votes"] else 1

    tasks = resolve_tasks(args)
    work, mapping, requests_by_judge = build_work(tasks, specs, args.artifact_suffix)
    n_criteria = sum(task["n_criteria"] for task in work)
    print(f"Cases: {len(work)}")
    print(f"Criteria: {n_criteria}")
    print(f"Expected votes: {n_criteria * len(specs)}")
    for spec in specs:
        mode = "OpenAI Batch" if spec.api_base == DEFAULT_API_BASE else "concurrent external API"
        print(f"- {spec.name}: {n_criteria} ({mode})")
    if args.dry_run:
        return 0

    required = {"OPENAI_API_KEY"}
    if any("openrouter" in spec.api_base for spec in specs):
        required.add("OPENROUTER_API_KEY")
    missing = sorted(name for name in required if not os.environ.get(name))
    if missing:
        raise SystemExit(f"Missing API keys: {', '.join(missing)}")

    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = args.runs_dir if args.runs_dir.is_absolute() else REPO_ROOT / args.runs_dir
    run_dir = base / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    state: dict[str, Any] = {
        "schema_version": "0.1",
        "status": "prepared",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "artifact_suffix": args.artifact_suffix,
        "judges": [spec.as_dict() for spec in specs],
        "tasks": work,
        "mapping": mapping,
        "batches": [],
    }
    for spec in specs:
        lines = requests_by_judge[spec.name]
        if lines:
            write_jsonl(run_dir / f"batch-{spec.name}.jsonl", lines)
    save_json(run_dir / "state.json", state)
    print(f"Run directory: {run_dir}")
    if args.prepare_only:
        return 0

    client = OpenAI()
    for spec in specs:
        lines = requests_by_judge[spec.name]
        if not lines:
            continue
        input_path = run_dir / f"batch-{spec.name}.jsonl"
        with input_path.open("rb") as handle:
            uploaded = client.files.create(file=handle, purpose="batch")
        batch = client.batches.create(
            input_file_id=uploaded.id,
            endpoint="/v1/responses",
            completion_window="24h",
            metadata={"description": f"LAB-EU gold validation {spec.name} {run_id}"},
        )
        state["batches"].append(
            {"judge": spec.name, "batch_id": batch.id, "input_file": input_path.name, "status": batch.status}
        )
        print(f"Submitted {spec.name}: {batch.id}")
    state["status"] = "running"
    save_json(run_dir / "state.json", state)

    run_external_judges(state, specs, run_dir)
    poll_batches(state, run_dir, args)
    summary = write_summary(state, run_dir)
    print(f"Completed: {summary['n_recorded_votes']}/{summary['n_expected_votes']} votes")
    return 0 if summary["n_recorded_votes"] == summary["n_expected_votes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
