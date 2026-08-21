#!/usr/bin/env python3
"""Run Codex CLI in a fresh non-project, ephemeral session for each LAB-EU task.

The Codex process never runs inside this checkout. Each task is copied to an OS
temporary directory containing only task.json and documents/. The CLI keeps the
user's configured MCP/plugin tools and ChatGPT login, enables live web search,
disables Codex memories, and does not persist a resumable session.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
PROMPT_TEMPLATE = REPO_ROOT / "prompts" / "harness" / "solve_task_codex_web.txt"
MULTI_PROMPT_TEMPLATE = REPO_ROOT / "prompts" / "harness" / "solve_task_codex_web_multi.txt"
DEFAULT_RUN_NAME = "codex-cli-ephemeral-web-full"

sys.path.insert(0, str(SCRIPTS_DIR))

import retry_util  # noqa: E402
from task_identity import task_format_label  # noqa: E402
from codex_source_audit import (  # noqa: E402
    DEFAULT_BLOCKED_DOMAINS,
    normalize_blocked_domains,
    write_run_summary,
    write_task_report,
)
from run_opencode_taskset import (  # noqa: E402
    document_list,
    iso_now,
    load_taskset,
    make_run_id,
    relative_to_repo,
    safe_task_id,
    sha256_file,
)


def copy_anonymized_task(row: dict[str, Any], destination: pathlib.Path) -> None:
    """Expose task substance but omit benchmark identity and provenance metadata."""
    destination.mkdir(parents=True, exist_ok=True)
    task = row["task"]
    anonymized = {
        "title": task_format_label(task.get("title")),
        "work_type": task.get("work_type", ""),
        "instructions": task.get("instructions", ""),
        "deliverables": row["deliverables"],
    }
    (destination / "task.json").write_text(
        json.dumps(anonymized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.copytree(
        row["task_dir"] / "documents",
        destination / "documents",
        dirs_exist_ok=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Codex CLI on a LAB-EU taskset in ephemeral non-project sessions."
    )
    parser.add_argument(
        "--taskset", type=pathlib.Path, required=True, help="JSONL taskset file."
    )
    parser.add_argument("--run-name", default=DEFAULT_RUN_NAME)
    parser.add_argument("--runs-dir", type=pathlib.Path, default=REPO_ROOT / "runs")
    parser.add_argument(
        "--resume-run-dir",
        type=pathlib.Path,
        help=(
            "Continue an existing run directory, skipping tasks whose metadata.json "
            "already records exit_code 0."
        ),
    )
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument(
        "--model",
        default="",
        help="Optional Codex model override. Empty (default) uses the configured Codex default.",
    )
    parser.add_argument(
        "--reasoning-effort",
        choices=["minimal", "low", "medium", "high", "xhigh", "max", "ultra"],
        default=None,
        help="Optional model_reasoning_effort override.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=7200)
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Run only the first N taskset entries. 0 (default) runs all tasks.",
    )
    parser.add_argument(
        "--tool-access",
        choices=["full", "workspace"],
        default="full",
        help=(
            "'full' exposes all locally configured tools without command approvals; "
            "'workspace' confines shell writes to the temporary task workspace."
        ),
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Maximum infrastructure attempts per task (default: 3).",
    )
    parser.add_argument(
        "--retry-on-timeout",
        action="store_true",
        help="Retry a task after its full timeout. Off by default.",
    )
    parser.add_argument(
        "--with-memories",
        action="store_true",
        help="Keep Codex memories enabled. Default is disabled for an incognito-style run.",
    )
    parser.add_argument(
        "--no-web-search",
        dest="web_search_enabled",
        action="store_false",
        default=True,
        help=(
            "Disable Codex web search explicitly and prohibit all external web/network "
            "research for the comparison arm."
        ),
    )
    parser.add_argument(
        "--blocked-domain",
        action="append",
        default=[],
        help=(
            "Additional web domain to prohibit and audit. Repeat for multiple domains. "
            "zjs-online.com is always blocked."
        ),
    )
    parser.add_argument(
        "--judge", action="store_true", help="Judge submissions after the run."
    )
    parser.add_argument("--judge-model", default="gpt-5.5")
    parser.add_argument("--judge-votes", type=int, default=1)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs, auth, and command construction without starting a Codex task.",
    )
    args = parser.parse_args()
    args.blocked_domains = normalize_blocked_domains(
        [*DEFAULT_BLOCKED_DOMAINS, *args.blocked_domain]
    )
    return args


def render_prompt(
    args: argparse.Namespace, row: dict[str, Any], workspace: pathlib.Path
) -> str:
    if not row["deliverables"]:
        raise ValueError(f"No deliverables declared for {row['task_id']}.")
    docs = "\n".join(f"- {name}" for name in document_list(workspace)) or "- (none)"
    if args.web_search_enabled:
        research_policy = (
            "Live web research is enabled.\n\n"
            "Blocked research domains:\n"
            + "\n".join(f"- {domain}" for domain in args.blocked_domains)
            + "\n\nDo not search, open, fetch, cite, or use information from any blocked "
            "domain. Append every blocked domain to every web search as a negative filter "
            "in the form `-site:blocked.example`. Ignore blocked-domain results that appear "
            "despite the filter. Using or positively targeting a blocked domain invalidates "
            "the run.\n\nYou may research the facts of the case, including searches using "
            "distinctive factual details. The harness may flag searches that resemble task "
            "identifiers, solution searches, or copied task wording for later human review; "
            "those flags are informational and do not invalidate the run. No domain "
            "allowlist applies."
        )
    else:
        research_policy = (
            "External web and network research is disabled for this comparison arm. Do not "
            "use web search, cached search, browsers, connectors, MCP tools that retrieve "
            "external content, or shell network clients such as curl or wget. Work only from "
            "the supplied task files and your internal model knowledge. Any recorded search "
            "or explicit network fetch invalidates the run. Create the required source "
            "sidecar with an empty `sources` list."
        )
    # Single-file tasks keep the original template byte-for-byte (its final
    # response doubles as a file-write fallback); multi-file tasks use the
    # multi template, whose durable result is the files alone.
    if len(row["deliverables"]) == 1:
        return PROMPT_TEMPLATE.read_text(encoding="utf-8").format(
            today=time.strftime("%Y-%m-%d"),
            task_id=row["solver_case_id"],
            title=task_format_label(row["task"].get("title")),
            work_type=row["task"].get("work_type", ""),
            instructions=row["task"].get("instructions", ""),
            docs=docs,
            research_policy=research_policy,
            deliverable=row["deliverables"][0],
        )
    return MULTI_PROMPT_TEMPLATE.read_text(encoding="utf-8").format(
        today=time.strftime("%Y-%m-%d"),
        task_id=row["solver_case_id"],
        title=task_format_label(row["task"].get("title")),
        work_type=row["task"].get("work_type", ""),
        instructions=row["task"].get("instructions", ""),
        docs=docs,
        research_policy=research_policy,
        deliverables_block="\n".join(f"- {name}" for name in row["deliverables"]),
    )


def build_codex_command(
    args: argparse.Namespace,
    workspace: pathlib.Path,
    final_message: pathlib.Path,
) -> list[str]:
    sandbox = "danger-full-access" if args.tool_access == "full" else "workspace-write"
    command = [args.codex_bin]
    if args.web_search_enabled:
        command.append("--search")
    else:
        command.extend(["--config", 'web_search="disabled"'])
    command.extend(
        [
            "--sandbox",
            sandbox,
            "--ask-for-approval",
            "never",
            "--cd",
            str(workspace),
        ]
    )
    if not args.with_memories:
        command.extend(["--disable", "memories"])
    if args.model:
        command.extend(["--model", args.model])
    if args.reasoning_effort:
        command.extend(
            ["--config", f'model_reasoning_effort="{args.reasoning_effort}"']
        )
    command.extend(
        [
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--json",
            "--output-last-message",
            str(final_message),
            "-",
        ]
    )
    return command


def solver_configuration(args: argparse.Namespace) -> dict[str, Any]:
    """Describe whether the solver settings were pinned or inherited."""
    return {
        "model": args.model or "configured-default",
        "reasoning_effort": args.reasoning_effort or "configured-default",
        "model_source": "cli-override" if args.model else "codex-config",
        "reasoning_effort_source": (
            "cli-override" if args.reasoning_effort else "codex-config"
        ),
        "event_stream_verified": False,
        "note": (
            "Codex JSONL does not report the resolved model and reasoning effort. "
            "Pin both CLI options for a fully self-contained run record."
        ),
    }


def run_process(
    command: list[str],
    prompt: str,
    stdout_path: pathlib.Path,
    stderr_path: pathlib.Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    started_at = iso_now()
    started = time.monotonic()
    timed_out = False
    with (
        stdout_path.open("w", encoding="utf-8") as stdout,
        stderr_path.open("w", encoding="utf-8") as stderr,
    ):
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=stdout,
            stderr=stderr,
            text=True,
        )
        try:
            process.communicate(prompt, timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    return {
        "exit_code": process.returncode if process.returncode is not None else 1,
        "timed_out": timed_out,
        "started_at": started_at,
        "ended_at": iso_now(),
        "duration_seconds": round(time.monotonic() - started, 3),
    }


def error_text(stdout_path: pathlib.Path, stderr_path: pathlib.Path) -> str:
    """Return diagnostics only, never normal legal answer text.

    The shared retry classifier recognizes HTTP status numbers. Feeding it the
    entire JSONL stream would therefore mistake a valid answer mentioning, for
    example, section 404 BGB for an HTTP 404 configuration failure.
    """
    parts: list[str] = []
    if stderr_path.exists():
        parts.append(
            stderr_path.read_text(encoding="utf-8", errors="replace")[-100_000:]
        )
    if stdout_path.exists():
        for line in stdout_path.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            event_type = str(event.get("type", "")).lower()
            if event_type in {"error", "turn.failed", "turn_failed"} or event.get(
                "error"
            ):
                parts.append(json.dumps(event, ensure_ascii=False))
    return "\n".join(parts)


def classify_codex_attempt(
    *, exit_code: int, timed_out: bool, missing_deliverables: bool, diagnostics: str
) -> tuple[str, str]:
    """Classify a Codex turn, treating the requested file as the durable result.

    Codex can finish writing the deliverable and then lose the streaming
    connection while echoing the same document as its final message. Repeating
    that completed legal answer would be best-of-N sampling, not recovery.
    """
    if not missing_deliverables:
        return retry_util.OK, "deliverable captured"
    return retry_util.classify_failure(
        exit_code=exit_code,
        timed_out=timed_out,
        missing_deliverables=True,
        error_text=diagnostics,
    )


def find_unexpected_files(
    workspace: pathlib.Path, deliverables: list[str]
) -> list[dict[str, Any]]:
    """Report files Codex created beyond the task input and the deliverables.

    A deliverable saved under the wrong name shows up here, so a reviewer can
    trace what happened instead of only seeing a missing file. Task input
    (task.json, documents/) and dotfile sidecars are not reported.
    """
    expected = {"task.json"} | {str(name) for name in deliverables}
    unexpected: list[dict[str, Any]] = []
    for path in sorted(workspace.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(workspace)
        if rel.parts and rel.parts[0] == "documents":
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        if str(rel) in expected:
            continue
        unexpected.append({"path": str(rel), "bytes": path.stat().st_size})
    return unexpected


def copy_attempt_artifacts(
    workspace: pathlib.Path,
    task_run_dir: pathlib.Path,
    final_message: pathlib.Path,
    row: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool, list[dict[str, Any]]]:
    work_archive = task_run_dir / "work"
    shutil.rmtree(work_archive, ignore_errors=True)
    shutil.copytree(workspace, work_archive)

    response_path = task_run_dir / "response.md"
    response_text = ""
    if final_message.is_file():
        response_text = final_message.read_text(
            encoding="utf-8", errors="replace"
        ).strip()
        response_path.write_text(
            response_text + ("\n" if response_text else ""), encoding="utf-8"
        )

    submission_dir = task_run_dir / "submission"
    submission_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    used_final_fallback = False
    for name in row["deliverables"]:
        source = workspace / name
        target = submission_dir / name
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        elif len(row["deliverables"]) == 1 and response_text:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(response_text + "\n", encoding="utf-8")
            used_final_fallback = True
        if target.is_file():
            results.append(
                {
                    "path": name,
                    "found": True,
                    "bytes": target.stat().st_size,
                    "sha256": sha256_file(target),
                }
            )
        else:
            results.append({"path": name, "found": False})
    return results, used_final_fallback, find_unexpected_files(workspace, row["deliverables"])


def archive_failed_attempt(task_run_dir: pathlib.Path, attempt: int) -> None:
    destination = task_run_dir / "attempts" / f"{attempt:02d}"
    destination.mkdir(parents=True, exist_ok=True)
    for name in (
        "stdout.jsonl",
        "stderr.log",
        "response.md",
        "work",
        "submission",
        "sources.json",
        "sources.md",
    ):
        source = task_run_dir / name
        if source.exists():
            shutil.move(str(source), str(destination / name))


def run_one_task(
    args: argparse.Namespace, row: dict[str, Any], run_dir: pathlib.Path
) -> dict[str, Any]:
    task_run_dir = run_dir / "tasks" / safe_task_id(row["task_id"])
    task_run_dir.mkdir(parents=True, exist_ok=True)
    (task_run_dir / "input_task_dir.txt").write_text(
        str(row["task_dir"]) + "\n", encoding="utf-8"
    )
    attempts: list[dict[str, Any]] = []
    deliverables: list[dict[str, Any]] = []
    used_final_fallback = False
    unexpected_files: list[dict[str, Any]] = []
    command: list[str] = []
    source_report: dict[str, Any] = {}

    for attempt in range(1, max(1, args.max_attempts) + 1):
        if attempt > 1:
            shutil.rmtree(task_run_dir / "submission", ignore_errors=True)
        with tempfile.TemporaryDirectory(prefix="lab-eu-codex-") as temporary:
            workspace = pathlib.Path(temporary)
            copy_anonymized_task(row, workspace)
            prompt = render_prompt(args, row, workspace)
            (task_run_dir / "prompt.md").write_text(prompt, encoding="utf-8")
            final_message = workspace / ".codex-final-message.md"
            command = build_codex_command(args, workspace, final_message)
            stdout_path = task_run_dir / "stdout.jsonl"
            stderr_path = task_run_dir / "stderr.log"
            result = run_process(
                command, prompt, stdout_path, stderr_path, args.timeout_seconds
            )
            deliverables, used_final_fallback, unexpected_files = copy_attempt_artifacts(
                workspace, task_run_dir, final_message, row
            )

        source_report = write_task_report(
            task_run_dir,
            row["task_id"],
            args.blocked_domains,
            web_search_allowed=args.web_search_enabled,
        )
        domain_violations = source_report["blocked_domain_policy"]["violations"]
        web_violations = source_report["web_access_policy"]["violations"]
        missing = any(not item.get("found") for item in deliverables)
        if domain_violations or web_violations:
            outcome = "policy_violation"
            reasons = []
            if domain_violations:
                reasons.append(
                    "blocked-domain policy violated: "
                    + ", ".join(sorted({item["domain"] for item in domain_violations}))
                )
            if web_violations:
                reasons.append("web access occurred in no-web arm")
            reason = "; ".join(reasons)
        else:
            outcome, reason = classify_codex_attempt(
                exit_code=result["exit_code"],
                timed_out=result["timed_out"],
                missing_deliverables=missing,
                diagnostics=error_text(
                    task_run_dir / "stdout.jsonl", task_run_dir / "stderr.log"
                ),
            )
        record = {"attempt": attempt, "outcome": outcome, "reason": reason, **result}
        attempts.append(record)
        retrying = retry_util.should_retry(
            outcome, retry_on_timeout=args.retry_on_timeout
        ) and attempt < max(1, args.max_attempts)
        if not retrying:
            break
        archive_failed_attempt(task_run_dir, attempt)
        delay = retry_util.backoff_delay(attempt)
        record["retry_delay_seconds"] = round(delay, 1)
        print(
            f"{row['task_id']}: attempt {attempt} failed ({reason}); retrying in {delay:.0f}s",
            file=sys.stderr,
        )
        time.sleep(delay)

    missing_names = [item["path"] for item in deliverables if not item.get("found")]
    source_report = write_task_report(
        task_run_dir,
        row["task_id"],
        args.blocked_domains,
        web_search_allowed=args.web_search_enabled,
    )
    metadata = {
        "schema_version": "0.1",
        "harness": "codex-cli-ephemeral-web",
        "task_id": row["task_id"],
        "solver_case_id": row["solver_case_id"],
        "task_identity_anonymized": True,
        "source_task_dir": str(row["task_dir"]),
        "source_task_dir_relative": relative_to_repo(row["task_dir"]),
        "model": args.model or "configured-default",
        "reasoning_effort": args.reasoning_effort or "configured-default",
        "solver_configuration": solver_configuration(args),
        "tool_access": args.tool_access,
        "live_web_search": args.web_search_enabled,
        "web_search_mode": "live" if args.web_search_enabled else "disabled",
        "blocked_domains": args.blocked_domains,
        "blocked_domain_policy": source_report["blocked_domain_policy"],
        "web_access_policy": source_report["web_access_policy"],
        "search_leakage_audit": source_report["search_leakage_audit"],
        "memories_enabled": args.with_memories,
        "ephemeral": True,
        "project_context": False,
        "user_config_and_configured_tools_loaded": True,
        "command": command,
        "attempt_count": len(attempts),
        "attempts": attempts,
        "expected_deliverables": row["deliverables"],
        "actual_deliverables": deliverables,
        "missing_deliverables": missing_names,
        "unexpected_files": unexpected_files,
        "used_final_message_fallback": used_final_fallback,
        "source_audit": source_report["counts"],
        "source_audit_json": str(task_run_dir / "sources.json"),
        "source_audit_markdown": str(task_run_dir / "sources.md"),
        "exit_code": 0 if attempts and attempts[-1]["outcome"] == retry_util.OK else 1,
    }
    (task_run_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def codex_status(codex_bin: str) -> tuple[str, str]:
    version = subprocess.run(
        [codex_bin, "--version"],
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    if version.returncode != 0:
        raise SystemExit(version.stderr.strip() or f"Could not run {codex_bin!r}.")
    login = subprocess.run(
        [codex_bin, "login", "status"],
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    if login.returncode != 0:
        raise SystemExit(login.stderr.strip() or "Codex is not logged in.")
    return version.stdout.strip(), (login.stdout.strip() or login.stderr.strip())


def write_manifest(
    args: argparse.Namespace,
    run_dir: pathlib.Path,
    run_id: str,
    rows: list[dict[str, Any]],
    codex_version: str,
    login_status: str,
) -> None:
    manifest = {
        "schema_version": "0.1",
        "harness": "codex-cli-ephemeral-web",
        "run_id": run_id,
        "run_name": args.run_name,
        "created_at": iso_now(),
        "taskset": relative_to_repo(
            args.taskset if args.taskset.is_absolute() else REPO_ROOT / args.taskset
        ),
        "n_tasks": len(rows),
        "codex_version": codex_version,
        "login_status": login_status,
        "model": args.model or "configured-default",
        "reasoning_effort": args.reasoning_effort or "configured-default",
        "solver_configuration": solver_configuration(args),
        "tool_access": args.tool_access,
        "live_web_search": args.web_search_enabled,
        "web_search_mode": "live" if args.web_search_enabled else "disabled",
        "blocked_domains": args.blocked_domains,
        "task_identity_anonymized": True,
        "search_leakage_audit_enforcement": "informational-only",
        "ephemeral": True,
        "memories_enabled": args.with_memories,
        "project_context": False,
        "parallel": args.parallel,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    if not PROMPT_TEMPLATE.is_file():
        raise SystemExit(f"Missing prompt template: {PROMPT_TEMPLATE}")
    rows = load_taskset(args.taskset)
    if args.limit < 0:
        raise SystemExit("--limit must be 0 or greater.")
    if args.limit:
        rows = rows[: args.limit]
    for index, row in enumerate(rows, start=1):
        row["solver_case_id"] = f"case-{index:03d}"
        if not row["deliverables"]:
            raise SystemExit(f"{row['task_id']}: at least one deliverable is required.")
        duplicates = sorted(
            {name for name in row["deliverables"] if row["deliverables"].count(name) > 1}
        )
        if duplicates:
            raise SystemExit(
                f"{row['task_id']}: duplicate deliverables: {', '.join(duplicates)}"
            )
    codex_version, login_status = codex_status(args.codex_bin)

    if args.dry_run:
        with tempfile.TemporaryDirectory(prefix="lab-eu-codex-dry-") as temporary:
            workspace = pathlib.Path(temporary)
            copy_anonymized_task(rows[0], workspace)
            example = build_codex_command(
                args, workspace, workspace / ".codex-final-message.md"
            )
        print(f"Validated {len(rows)} task(s).")
        print(f"Codex: {codex_version}")
        print(f"Auth: {login_status}")
        print(
            "Sessions: ephemeral; memories disabled"
            if not args.with_memories
            else "Sessions: ephemeral"
        )
        print("Project context: none (each task runs in an OS temporary directory)")
        print("Web search: " + ("live" if args.web_search_enabled else "disabled"))
        print("Blocked domains: " + ", ".join(args.blocked_domains))
        print(
            f"Tool access: {args.tool_access}; configured MCP/plugin tools remain loaded"
        )
        print("Command shape: " + " ".join(example))
        return 0

    if args.resume_run_dir:
        run_dir = args.resume_run_dir.resolve()
        if (
            not (run_dir / "manifest.json").is_file()
            or not (run_dir / "tasks").is_dir()
        ):
            raise SystemExit(f"Not a resumable Codex run directory: {run_dir}")
        completed_task_ids: set[str] = set()
        for metadata_path in (run_dir / "tasks").glob("*/metadata.json"):
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("exit_code") == 0 and isinstance(
                metadata.get("task_id"), str
            ):
                completed_task_ids.add(metadata["task_id"])
        rows = [row for row in rows if row["task_id"] not in completed_task_ids]
        print(
            f"Resuming {run_dir}: {len(completed_task_ids)} completed, "
            f"{len(rows)} remaining."
        )
    else:
        run_id = make_run_id()
        runs_dir = (
            args.runs_dir if args.runs_dir.is_absolute() else REPO_ROOT / args.runs_dir
        )
        run_dir = runs_dir / args.run_name / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        write_manifest(args, run_dir, run_id, rows, codex_version, login_status)

    failures = 0
    workers = max(1, args.parallel)
    if workers == 1:
        for row in rows:
            metadata = run_one_task(args, row, run_dir)
            failures += int(metadata["exit_code"] != 0)
            extra = len(metadata.get("unexpected_files") or [])
            print(
                f"{row['task_id']}: exit={metadata['exit_code']} "
                f"missing={len(metadata['missing_deliverables'])}"
                + (f" unexpected={extra}" if extra else "")
            )
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(run_one_task, args, row, run_dir): row for row in rows
            }
            for future in as_completed(futures):
                row = futures[future]
                try:
                    metadata = future.result()
                except Exception as exc:  # noqa: BLE001
                    failures += 1
                    print(
                        f"{row['task_id']}: failed before metadata: {exc}",
                        file=sys.stderr,
                    )
                    continue
                failures += int(metadata["exit_code"] != 0)
                extra = len(metadata.get("unexpected_files") or [])
                print(
                    f"{row['task_id']}: exit={metadata['exit_code']} "
                    f"missing={len(metadata['missing_deliverables'])}"
                    + (f" unexpected={extra}" if extra else "")
                )

    source_summary = write_run_summary(
        run_dir,
        args.blocked_domains,
        web_search_allowed=args.web_search_enabled,
    )
    print(
        f"Sources: {source_summary['unique_source_urls']} unique URL(s), "
        f"{source_summary['unique_source_domains']} domain(s)"
    )
    print(f"Wrote run: {run_dir}")
    if args.judge:
        judge = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "judge_run.py"),
                str(run_dir),
                "--judge-model",
                args.judge_model,
                "--votes",
                str(args.judge_votes),
            ],
            cwd=REPO_ROOT,
            check=False,
        )
        if judge.returncode != 0:
            return 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
