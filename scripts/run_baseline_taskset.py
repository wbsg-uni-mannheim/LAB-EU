#!/usr/bin/env python3
"""Run a single-LLM-call baseline against an explicit LAB-EU taskset.

One plain model call per task: task instructions plus inlined documents in,
one Markdown deliverable out. No agent loop, no tools, no workspace. This is
the reference point for the research question whether agent scaffolding helps.

The run layout mirrors run_opencode_taskset.py (manifest.json, tasks/<id>/
metadata.json with source_task_dir, submission/<deliverable>), so
scripts/judge_run.py judges baseline runs unchanged.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from run_opencode_taskset import (  # noqa: E402
    iso_now,
    load_taskset,
    make_run_id,
    relative_to_repo,
    safe_task_id,
)

PROMPT_TEMPLATE = REPO_ROOT / "prompts" / "harness" / "solve_task_baseline.txt"
DEFAULT_MODEL = "gpt-5.5"
DEFAULT_API_BASE = "https://api.openai.com/v1"
MAX_DOC_CHARS = 120_000
MAX_TOTAL_DOC_CHARS = 300_000
API_ATTEMPTS = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single-call LLM baseline on a LAB-EU taskset.")
    parser.add_argument("--taskset", type=pathlib.Path, required=True, help="JSONL taskset file.")
    parser.add_argument("--run-name", default="baseline-single-call")
    parser.add_argument("--runs-dir", type=pathlib.Path, default=REPO_ROOT / "runs")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--api-base",
        default=os.environ.get("OPENAI_API_BASE", DEFAULT_API_BASE),
        help="OpenAI-compatible endpoint. Use https://openrouter.ai/api/v1 for OpenRouter models.",
    )
    parser.add_argument(
        "--reasoning-effort",
        default="none",
        help=(
            "Optional reasoning effort passed as chat-completions reasoning_effort. "
            "Only for endpoints that support it; 'none' (default) sends a plain request."
        ),
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=0,
        help="Optional completion token cap. 0 (default) sends no cap and uses the provider default.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument(
        "--judge",
        action="store_true",
        help="After the run, judge all submissions via scripts/judge_run.py (needs OPENAI_API_KEY).",
    )
    parser.add_argument("--judge-model", default="gpt-5.5")
    parser.add_argument("--judge-votes", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and print run plan without model calls.")
    return parser.parse_args()


def api_key_env_for(api_base: str) -> str:
    """Pick the .env variable for the endpoint, so no key argument is needed."""
    host = api_base.lower()
    if "openrouter" in host:
        return "OPENROUTER_API_KEY"
    if "deepseek" in host:
        return "DEEPSEEK_API_KEY"
    return "OPENAI_API_KEY"


def render_documents(task_dir: pathlib.Path) -> tuple[str, bool]:
    docs_dir = task_dir / "documents"
    sections: list[str] = []
    truncated = False
    used = 0
    for path in sorted(p for p in docs_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(task_dir)
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > MAX_DOC_CHARS:
            text = text[:MAX_DOC_CHARS] + "\n\n[TRUNCATED]\n"
            truncated = True
        remaining = MAX_TOTAL_DOC_CHARS - used
        if remaining <= 0:
            sections.append(f"### {rel}\n\n[OMITTED: document budget reached]")
            truncated = True
            continue
        if len(text) > remaining:
            text = text[:remaining] + "\n\n[TRUNCATED_BY_TOTAL_BUDGET]\n"
            truncated = True
        used += len(text)
        sections.append(f"### {rel}\n\n{text}")
    return ("\n\n".join(sections) if sections else "(none)"), truncated


def render_prompt(row: dict[str, Any], documents: str) -> str:
    task = row["task"]
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    return template.format(
        today=dt.date.today().isoformat(),
        task_id=row["task_id"],
        title=task.get("title", row["task_id"]),
        work_type=task.get("work_type", ""),
        instructions=task.get("instructions", ""),
        documents=documents,
        deliverable=row["deliverables"][0],
    )


def strip_outer_fence(text: str) -> tuple[str, bool]:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2 and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip() + "\n", True
    return text, False


def usage_summary(response: Any) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    return {
        "input_tokens": getattr(usage, "prompt_tokens", None),
        "output_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }


def call_model(client: OpenAI, args: argparse.Namespace, prompt: str) -> tuple[str, dict[str, Any], int]:
    request: dict[str, Any] = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if args.reasoning_effort.lower() != "none":
        request["reasoning_effort"] = args.reasoning_effort
    if args.max_output_tokens > 0:
        request["max_completion_tokens"] = args.max_output_tokens

    last_error: Exception | None = None
    for attempt in range(1, API_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(**request)
        except OpenAIError as exc:
            # Older OpenAI-compatible endpoints only accept max_tokens.
            if "max_completion_tokens" in request and "max_completion_tokens" in str(exc):
                request["max_tokens"] = request.pop("max_completion_tokens")
                last_error = exc
                continue
            last_error = exc
            continue
        text = (response.choices[0].message.content or "") if response.choices else ""
        if not text.strip():
            last_error = RuntimeError("Model returned an empty response.")
            continue
        return text, usage_summary(response), attempt
    raise RuntimeError(f"Model call failed after {API_ATTEMPTS} attempts: {last_error}")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_one_task(args: argparse.Namespace, client: OpenAI, row: dict[str, Any], run_dir: pathlib.Path) -> dict[str, Any]:
    task_run_dir = run_dir / "tasks" / safe_task_id(row["task_id"])
    submission_dir = task_run_dir / "submission"
    task_run_dir.mkdir(parents=True, exist_ok=True)
    submission_dir.mkdir(parents=True, exist_ok=True)
    (task_run_dir / "input_task_dir.txt").write_text(str(row["task_dir"]) + "\n", encoding="utf-8")

    started_at = iso_now()
    started = time.monotonic()
    error: str | None = None
    usage: dict[str, Any] = {}
    attempts = 0
    fence_stripped = False
    documents_truncated = False
    deliverable_results: list[dict[str, Any]] = []

    try:
        if len(row["deliverables"]) != 1:
            raise RuntimeError(
                "Baseline harness supports exactly one deliverable per task; "
                f"got {row['deliverables']!r}."
            )
        documents, documents_truncated = render_documents(row["task_dir"])
        prompt = render_prompt(row, documents)
        (task_run_dir / "prompt.md").write_text(prompt, encoding="utf-8")

        response_text, usage, attempts = call_model(client, args, prompt)
        (task_run_dir / "response.md").write_text(response_text, encoding="utf-8")

        deliverable_text, fence_stripped = strip_outer_fence(response_text)
        deliverable_name = row["deliverables"][0]
        deliverable_path = submission_dir / deliverable_name
        deliverable_path.parent.mkdir(parents=True, exist_ok=True)
        deliverable_path.write_text(deliverable_text, encoding="utf-8")
        deliverable_results.append(
            {
                "path": deliverable_name,
                "found": True,
                "bytes": len(deliverable_text.encode("utf-8")),
                "sha256": sha256_text(deliverable_text),
            }
        )
    except Exception as exc:  # noqa: BLE001 - record the failure, keep the run going
        error = str(exc)
        deliverable_results = [
            {"path": name, "found": False} for name in row["deliverables"]
        ]

    metadata = {
        "schema_version": "0.1",
        "harness": "baseline-single-call",
        "task_id": row["task_id"],
        "source_task_dir": str(row["task_dir"]),
        "source_task_dir_relative": relative_to_repo(row["task_dir"]),
        "task_run_dir": str(task_run_dir),
        "model": args.model,
        "api_base": args.api_base,
        "reasoning_effort": None if args.reasoning_effort.lower() == "none" else args.reasoning_effort,
        "max_output_tokens": args.max_output_tokens or None,
        "expected_deliverables": row["deliverables"],
        "actual_deliverables": deliverable_results,
        "missing_deliverables": [item["path"] for item in deliverable_results if not item.get("found")],
        "documents_truncated": documents_truncated,
        "stripped_outer_fence": fence_stripped,
        "api_attempts": attempts,
        "usage": usage,
        "error": error,
        "started_at": started_at,
        "ended_at": iso_now(),
        "duration_seconds": round(time.monotonic() - started, 3),
        "exit_code": 0 if error is None else 1,
        "timed_out": False,
    }
    (task_run_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def write_manifest(args: argparse.Namespace, run_dir: pathlib.Path, run_id: str, rows: list[dict[str, Any]]) -> None:
    manifest = {
        "schema_version": "0.1",
        "harness": "baseline-single-call",
        "run_id": run_id,
        "run_name": args.run_name,
        "created_at": iso_now(),
        "taskset": relative_to_repo(args.taskset if args.taskset.is_absolute() else REPO_ROOT / args.taskset),
        "n_tasks": len(rows),
        "model": args.model,
        "api_base": args.api_base,
        "reasoning_effort": None if args.reasoning_effort.lower() == "none" else args.reasoning_effort,
        "max_output_tokens": args.max_output_tokens or None,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    load_dotenv(REPO_ROOT / ".env", override=False)
    args = parse_args()
    rows = load_taskset(args.taskset)
    if not PROMPT_TEMPLATE.exists():
        raise SystemExit(f"Missing prompt template: {PROMPT_TEMPLATE}")

    key_env = api_key_env_for(args.api_base)

    if args.dry_run:
        print(f"Validated {len(rows)} task(s).")
        print(f"Model: {args.model}")
        print(f"API base: {args.api_base}")
        print(f"API key from .env: {key_env} ({'set' if os.environ.get(key_env) else 'MISSING'})")
        print(f"Reasoning effort: {args.reasoning_effort}")
        for row in rows:
            documents, truncated = render_documents(row["task_dir"])
            prompt = render_prompt(row, documents)
            print(
                f"- {row['task_id']} -> {relative_to_repo(row['task_dir'])} "
                f"(prompt {len(prompt)} chars{', documents truncated' if truncated else ''})"
            )
        return 0

    api_key = os.environ.get(key_env)
    if not api_key:
        raise SystemExit(
            f"{key_env} is not set (selected automatically for --api-base {args.api_base}). "
            "Put it in the repo-root .env."
        )
    client = OpenAI(base_url=args.api_base, api_key=api_key, timeout=args.timeout_seconds)

    run_id = make_run_id()
    run_dir = (args.runs_dir if args.runs_dir.is_absolute() else REPO_ROOT / args.runs_dir) / args.run_name / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    write_manifest(args, run_dir, run_id, rows)

    failures = 0
    max_workers = max(1, args.parallel)
    if max_workers == 1:
        for row in rows:
            metadata = run_one_task(args, client, row, run_dir)
            failures += int(metadata["exit_code"] != 0)
            print(f"{row['task_id']}: exit={metadata['exit_code']} missing={len(metadata['missing_deliverables'])}")
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_row = {pool.submit(run_one_task, args, client, row, run_dir): row for row in rows}
            for future in as_completed(future_to_row):
                row = future_to_row[future]
                try:
                    metadata = future.result()
                except Exception as exc:  # noqa: BLE001
                    failures += 1
                    print(f"{row['task_id']}: failed before metadata: {exc}", file=sys.stderr)
                    continue
                failures += int(metadata["exit_code"] != 0)
                print(f"{row['task_id']}: exit={metadata['exit_code']} missing={len(metadata['missing_deliverables'])}")

    print(f"Wrote run: {run_dir}")

    if args.judge:
        print(f"Judging run with {args.judge_model} ({args.judge_votes} votes per criterion)...")
        judge = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "judge_run.py"),
                str(run_dir),
                "--judge-model", args.judge_model,
                "--votes", str(args.judge_votes),
            ],
            cwd=REPO_ROOT,
        )
        if judge.returncode != 0:
            print("Judging reported failures; see judge.stderr.log in the task directories.", file=sys.stderr)
            return 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
