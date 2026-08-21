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
from baseline_prompt import (  # noqa: E402
    MULTI_PROMPT_TEMPLATE,
    PROMPT_TEMPLATE,
    render_documents,
    render_multi_prompt as render_baseline_multi_prompt,
    render_prompt as render_baseline_prompt,
    sha256_text,
    split_multi_response,
    strip_outer_fence,
)

import retry_util  # noqa: E402

DEFAULT_MODEL = "gpt-5.5"
DEFAULT_API_BASE = "https://api.openai.com/v1"


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
        "--max-attempts",
        type=int,
        default=retry_util.DEFAULT_MAX_ATTEMPTS,
        help=(
            "Model-call attempts per task, including the first "
            f"(default {retry_util.DEFAULT_MAX_ATTEMPTS} = 1 + 10 retries). Retried "
            "on upstream failures and empty completions; a rejected key or an "
            "unknown model fails immediately."
        ),
    )
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


def render_prompt(row: dict[str, Any], documents: str) -> str:
    # Single-deliverable tasks keep the original template byte-for-byte; the
    # multi template is only used where the task requires several work products.
    if len(row["deliverables"]) == 1:
        prompt, _truncated = render_baseline_prompt(
            task_id=row["task_id"],
            task=row["task"],
            task_dir=row["task_dir"],
            deliverable=row["deliverables"][0],
        )
        return prompt
    prompt, _truncated = render_baseline_multi_prompt(
        task_id=row["task_id"],
        task=row["task"],
        task_dir=row["task_dir"],
        deliverables=row["deliverables"],
    )
    return prompt


def usage_summary(response: Any) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    return {
        "input_tokens": getattr(usage, "prompt_tokens", None),
        "output_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }


def collect_stream(stream: Any) -> tuple[str, dict[str, Any]]:
    """Drain a streamed completion into (text, usage).

    Usage arrives in the final chunk when stream_options.include_usage is set;
    an endpoint that omits it simply yields an empty usage dict.
    """
    chunks: list[str] = []
    usage: dict[str, Any] = {}
    for event in stream:
        choices = getattr(event, "choices", None)
        if choices:
            delta = getattr(choices[0], "delta", None)
            piece = getattr(delta, "content", None) if delta else None
            if piece:
                chunks.append(piece)
        event_usage = getattr(event, "usage", None)
        if event_usage is not None:
            usage = {
                "input_tokens": getattr(event_usage, "prompt_tokens", None),
                "output_tokens": getattr(event_usage, "completion_tokens", None),
                "total_tokens": getattr(event_usage, "total_tokens", None),
            }
    return "".join(chunks), usage


def call_model(client: OpenAI, args: argparse.Namespace, prompt: str,
               task_id: str = "") -> tuple[str, dict[str, Any], int]:
    """One baseline call, retried on infrastructure failures only.

    Same policy as the OpenCode harness (scripts/retry_util.py): upstream
    failures are repeated with backoff, a rejected key or an unknown model
    fails immediately instead of burning every attempt.
    """
    # Streamed: a reasoning model can think for minutes before the first token,
    # and a non-streamed request of that length dies in the silence (verified on
    # gpt-5.6-sol with a Second-State-Exam prompt: non-streamed timed out after
    # 30 min, streamed finished in 6 min with the first token after 238 s).
    request: dict[str, Any] = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if args.reasoning_effort.lower() != "none":
        request["reasoning_effort"] = args.reasoning_effort
    if args.max_output_tokens > 0:
        request["max_completion_tokens"] = args.max_output_tokens

    max_attempts = max(1, args.max_attempts)
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = collect_stream(client.chat.completions.create(**request))
        except OpenAIError as exc:
            # Older OpenAI-compatible endpoints only accept max_tokens. A
            # request-shape fix, not an outage: repeat it straight away.
            if "max_completion_tokens" in request and "max_completion_tokens" in str(exc):
                request["max_tokens"] = request.pop("max_completion_tokens")
                last_error = exc
                continue
            last_error = exc
            outcome, reason = retry_util.classify_failure(
                exit_code=1, timed_out=False, missing_deliverables=True,
                error_text=str(exc),
            )
            if outcome == retry_util.FATAL:
                raise RuntimeError(f"Model call rejected, not retrying: {reason}: {exc}") from exc
        else:
            text, stream_usage = response
            if text.strip():
                return text, stream_usage, attempt
            # An empty completion is a truncated or dropped generation, not an
            # answer — treat it like any other upstream failure.
            last_error = RuntimeError("Model returned an empty response.")

        if attempt < max_attempts:
            delay = retry_util.sleep_before_retry(attempt)
            print(f"{task_id or args.model}: attempt {attempt}/{max_attempts} failed "
                  f"({last_error}); retried after {delay:.0f}s", file=sys.stderr)
    raise RuntimeError(f"Model call failed after {max_attempts} attempts: {last_error}")


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
        documents, documents_truncated = render_documents(row["task_dir"])
        prompt = render_prompt(row, documents)
        (task_run_dir / "prompt.md").write_text(prompt, encoding="utf-8")

        response_text, usage, attempts = call_model(client, args, prompt, row["task_id"])
        (task_run_dir / "response.md").write_text(response_text, encoding="utf-8")

        if len(row["deliverables"]) == 1:
            deliverable_text, fence_stripped = strip_outer_fence(response_text)
            texts = {row["deliverables"][0]: deliverable_text}
        else:
            texts = split_multi_response(response_text, row["deliverables"])
        for name in row["deliverables"]:
            text = texts.get(name)
            if text is None:
                deliverable_results.append({"path": name, "found": False})
                continue
            deliverable_path = submission_dir / name
            deliverable_path.parent.mkdir(parents=True, exist_ok=True)
            deliverable_path.write_text(text, encoding="utf-8")
            deliverable_results.append(
                {
                    "path": name,
                    "found": True,
                    "bytes": len(text.encode("utf-8")),
                    "sha256": sha256_text(text),
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
    if not MULTI_PROMPT_TEMPLATE.exists():
        raise SystemExit(f"Missing prompt template: {MULTI_PROMPT_TEMPLATE}")

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
