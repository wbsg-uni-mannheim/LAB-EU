#!/usr/bin/env python3
"""Run OpenCode against an explicit LAB-EU taskset."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO_ROOT / "prompts" / "harness"
DEFAULT_MODEL = "openrouter/deepseek/deepseek-v4-pro"
DEFAULT_VARIANT = "medium"
DEFAULT_RUN_NAME = "opencode-openrouter-deepseek-v4-pro-medium"
DEFAULT_DOCKER_IMAGE = "lab-eu-opencode-harness:latest"

OPENCODE_PERMISSION_CONFIG: dict[str, Any] = {
    "$schema": "https://opencode.ai/config.json",
    "permission": {
        "*": "deny",
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "edit": {"*": "allow"},
        "bash": {
            "*": "deny",
            "pwd": "allow",
            "ls": "allow",
            "ls *": "allow",
            "find *": "allow",
            "cat *": "allow",
            "sed *": "allow",
        },
        "webfetch": "deny",
        "websearch": "deny",
        "external_directory": "deny",
    },
}


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OpenCode on a LAB-EU taskset.")
    parser.add_argument("--taskset", type=pathlib.Path, required=True, help="JSONL taskset file.")
    parser.add_argument("--run-name", default=DEFAULT_RUN_NAME)
    parser.add_argument("--runs-dir", type=pathlib.Path, default=REPO_ROOT / "runs")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--variant", default=DEFAULT_VARIANT)
    parser.add_argument("--agent", default="", help="Optional OpenCode agent name.")
    parser.add_argument("--timeout-seconds", type=int, default=7200)
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--sandbox", choices=["docker", "local"], default="docker")
    parser.add_argument("--docker-image", default=DEFAULT_DOCKER_IMAGE)
    parser.add_argument("--docker-network", default="bridge")
    parser.add_argument("--docker-cpus", default="2")
    parser.add_argument("--docker-memory", default="4g")
    parser.add_argument("--docker-pids-limit", default="256")
    parser.add_argument(
        "--docker-auth-path",
        type=pathlib.Path,
        default=pathlib.Path.home() / ".local/share/opencode/auth.json",
        help="Host OpenCode auth file to mount read-only into Docker.",
    )
    parser.add_argument("--no-docker-auth-mount", action="store_true")
    parser.add_argument("--opencode-bin", default="opencode", help="OpenCode binary for local sandbox mode.")
    parser.add_argument("--skip-workspace-archive", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and print run plan without model calls.")
    return parser.parse_args()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_task_id(task_id: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "__", task_id).strip("_")
    return value or "task"


def safe_container_name(task_id: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_.-]+", "-", task_id).strip("-").lower()
    return f"lab-eu-{base[:40]}-{uuid.uuid4().hex[:8]}"


def normalize_deliverables(task: dict[str, Any], task_dir: pathlib.Path) -> list[str]:
    raw = task.get("deliverables")
    if isinstance(raw, str):
        deliverables = [raw]
    elif isinstance(raw, list) and all(isinstance(item, str) for item in raw):
        deliverables = list(raw)
    else:
        raise SystemExit(f"{task_dir / 'task.json'} must define deliverables as a string or list of strings.")

    for deliverable in deliverables:
        validate_relative_path(deliverable, "deliverable")
    return deliverables


def validate_relative_path(value: str, label: str) -> pathlib.Path:
    path = pathlib.PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not str(path):
        raise SystemExit(f"Invalid {label} path: {value!r}")
    return pathlib.Path(*path.parts)


def resolve_under(path: pathlib.Path, parent: pathlib.Path, label: str) -> pathlib.Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(parent.resolve())
    except ValueError as exc:
        raise SystemExit(f"{label} must be under {parent}: {path}") from exc
    return resolved


def load_taskset(taskset_path: pathlib.Path) -> list[dict[str, Any]]:
    path = taskset_path if taskset_path.is_absolute() else REPO_ROOT / taskset_path
    if not path.exists():
        raise SystemExit(f"Missing taskset: {path}")

    tasks_root = REPO_ROOT / "tasks"
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc

        task_id = row.get("task_id")
        task_dir_raw = row.get("task_dir")
        if not isinstance(task_id, str) or not task_id:
            raise SystemExit(f"{path}:{line_number}: task_id must be a non-empty string.")
        if not isinstance(task_dir_raw, str) or not task_dir_raw:
            raise SystemExit(f"{path}:{line_number}: task_dir must be a non-empty string.")
        if task_id in seen:
            raise SystemExit(f"{path}:{line_number}: duplicate task_id: {task_id}")
        seen.add(task_id)

        task_dir = pathlib.Path(task_dir_raw)
        task_dir = task_dir if task_dir.is_absolute() else REPO_ROOT / task_dir
        task_dir = resolve_under(task_dir, tasks_root, "task_dir")
        validate_task_dir(task_dir)

        task = load_json(task_dir / "task.json")
        deliverables = normalize_deliverables(task, task_dir)
        rows.append(
            {
                "task_id": task_id,
                "task_dir": task_dir,
                "task": task,
                "deliverables": deliverables,
                "allow_network": bool(row.get("allow_network", False)),
            }
        )

    if not rows:
        raise SystemExit(f"No tasks found in {path}")
    return rows


def validate_task_dir(task_dir: pathlib.Path) -> None:
    required = [
        task_dir / "task.json",
        task_dir / "documents",
        task_dir / "evals" / "rubric.json",
    ]
    for path in required:
        if not path.exists():
            raise SystemExit(f"Missing required task artifact: {path}")
    if not (task_dir / "documents").is_dir():
        raise SystemExit(f"documents must be a directory: {task_dir / 'documents'}")


def opencode_version(opencode_bin: str) -> str:
    try:
        result = subprocess.run(
            [opencode_bin, "--version"],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def make_run_id() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def relative_to_repo(path: pathlib.Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def copy_sanitized_task(task_dir: pathlib.Path, destination: pathlib.Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(task_dir / "task.json", destination / "task.json")
    shutil.copytree(task_dir / "documents", destination / "documents", dirs_exist_ok=True)


def copy_tree_contents(source: pathlib.Path, destination: pathlib.Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def document_list(task_input_dir: pathlib.Path) -> list[str]:
    docs_dir = task_input_dir / "documents"
    return [str(path.relative_to(task_input_dir)) for path in sorted(docs_dir.rglob("*")) if path.is_file()]


def render_prompt(row: dict[str, Any], task_input_dir: pathlib.Path) -> str:
    task = row["task"]
    docs = "\n".join(f"- {name}" for name in document_list(task_input_dir)) or "- (none)"
    deliverables = "\n".join(f"- {name}" for name in row["deliverables"])
    title = task.get("title", row["task_id"])
    work_type = task.get("work_type", "")
    instructions = task.get("instructions", "")
    today = dt.date.today().isoformat()

    template_path = PROMPTS_DIR / "solve_task.txt"
    if not template_path.exists():
        raise SystemExit(f"Missing prompt template: {template_path}")
    return template_path.read_text(encoding="utf-8").format(
        today=today,
        task_id=row["task_id"],
        title=title,
        work_type=work_type,
        instructions=instructions,
        docs=docs,
        deliverables=deliverables,
    )


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: pathlib.Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _line in handle)


def snapshot_workspace(work_dir: pathlib.Path) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for path in sorted(work_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(work_dir).as_posix()
        stat = path.stat()
        snapshot[relative] = {
            "bytes": stat.st_size,
            "sha256": sha256_file(path),
            "lines": count_lines(path),
        }
    return snapshot


def diff_snapshots(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> dict[str, Any]:
    before_paths = set(before)
    after_paths = set(after)
    created = sorted(after_paths - before_paths)
    deleted = sorted(before_paths - after_paths)
    modified = sorted(path for path in before_paths & after_paths if before[path]["sha256"] != after[path]["sha256"])
    unchanged = len(before_paths & after_paths) - len(modified)
    return {
        "created": [{"path": path, **after[path]} for path in created],
        "modified": [{"path": path, "before": before[path], "after": after[path]} for path in modified],
        "deleted": [{"path": path, **before[path]} for path in deleted],
        "unchanged_count": unchanged,
    }


def collect_deliverables(work_dir: pathlib.Path, task_dir: pathlib.Path, deliverables: list[str]) -> list[dict[str, Any]]:
    submission_dir = task_dir / "submission"
    submission_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for deliverable in deliverables:
        relative_path = validate_relative_path(deliverable, "deliverable")
        source = work_dir / relative_path
        target = submission_dir / relative_path

        if source.exists() and source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        if target.exists() and target.is_file():
            results.append(
                {
                    "path": deliverable,
                    "found": True,
                    "bytes": target.stat().st_size,
                    "sha256": sha256_file(target),
                }
            )
        else:
            results.append({"path": deliverable, "found": False})
    return results


def archive_workspace(work_dir: pathlib.Path, archive_path: pathlib.Path) -> None:
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(work_dir, arcname="work")


def parse_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or not stripped.startswith("{"):
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            event["_jsonl_line"] = line_number
            events.append(event)
    return events


def json_load_maybe(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped or stripped[0] not in "[{":
        return value
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return value


def iter_dicts(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    stack = [value]
    while stack:
        current = stack.pop()
        current = json_load_maybe(current)
        if isinstance(current, dict):
            found.append(current)
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return found


def first_string(data: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def pick_tool_name(event: dict[str, Any]) -> str | None:
    candidates: list[str] = []
    for data in iter_dicts(event):
        for key in ["tool", "toolName", "tool_name", "name", "function"]:
            value = data.get(key)
            if isinstance(value, str):
                candidates.append(value)
            elif isinstance(value, dict):
                nested = first_string(value, ["name", "tool", "toolName", "tool_name"])
                if nested:
                    candidates.append(nested)
    for candidate in candidates:
        lowered = candidate.lower()
        if any(token in lowered for token in ["read", "write", "edit", "bash", "grep", "glob", "list", "patch", "cat", "sed"]):
            return candidate
    return candidates[0] if candidates else None


def pick_arguments(event: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for data in iter_dicts(event):
        for key in ["input", "args", "arguments", "params", "parameters"]:
            value = json_load_maybe(data.get(key))
            if isinstance(value, dict):
                merged.update(value)
        for key, value in data.items():
            if key in {
                "path",
                "file",
                "filePath",
                "filepath",
                "pattern",
                "command",
                "cmd",
                "offset",
                "limit",
                "lineStart",
                "lineEnd",
                "line_start",
                "line_end",
            }:
                merged.setdefault(key, value)
    return merged


def extract_paths_from_text(text: str) -> list[str]:
    paths: list[str] = []
    for match in re.finditer(r"(?:(?:\.?/)?(?:documents|task\.json|[A-Za-z0-9_.-]+)[A-Za-z0-9_./-]*\.md|task\.json)", text):
        value = match.group(0).strip("'\"")
        if value not in paths:
            paths.append(value)
    return paths


def extract_paths(args: dict[str, Any], command: str | None = None) -> list[str]:
    paths: list[str] = []
    for key in ["path", "file", "filePath", "filepath", "target_file", "source_file"]:
        value = args.get(key)
        if isinstance(value, str) and value not in paths:
            paths.append(value)
    if command:
        for value in extract_paths_from_text(command):
            if value not in paths:
                paths.append(value)
    return paths


def line_range_from_args(args: dict[str, Any], command: str | None = None) -> dict[str, int] | None:
    start = args.get("lineStart") or args.get("line_start")
    end = args.get("lineEnd") or args.get("line_end")
    offset = args.get("offset")
    limit = args.get("limit")
    if isinstance(start, int) and isinstance(end, int):
        return {"start": start, "end": end}
    if isinstance(offset, int) and isinstance(limit, int):
        return {"start": offset + 1, "end": offset + limit}
    if command:
        match = re.search(r"sed\s+-n\s+['\"]?(\d+),(\d+)p['\"]?", command)
        if match:
            return {"start": int(match.group(1)), "end": int(match.group(2))}
        match = re.search(r"(?:head|tail)\s+-n\s+(\d+)", command)
        if match and command.strip().startswith("head"):
            return {"start": 1, "end": int(match.group(1))}
    return None


def classify_action(tool_name: str | None, args: dict[str, Any]) -> str:
    lowered = (tool_name or "").lower()
    command = str(args.get("command") or args.get("cmd") or "")
    command_lowered = command.lower().strip()
    if any(token in lowered for token in ["write", "edit", "patch"]):
        return "write"
    if "read" in lowered:
        return "read"
    if "grep" in lowered:
        return "search"
    if "glob" in lowered or "list" in lowered:
        return "list"
    if "bash" in lowered or command:
        if re.match(r"^(cat|sed|head|tail)\b", command_lowered):
            return "read"
        if re.match(r"^(grep|rg)\b", command_lowered):
            return "search"
        if re.match(r"^(ls|find)\b", command_lowered):
            return "list"
        if any(token in command_lowered for token in [">", "tee ", "cat <<", "python ", "node "]):
            return "shell"
        return "shell"
    return "event"


def normalize_trace_event(index: int, event: dict[str, Any]) -> dict[str, Any] | None:
    tool_name = pick_tool_name(event)
    args = pick_arguments(event)
    action = classify_action(tool_name, args)
    event_type = first_string(event, ["type", "event", "kind"])
    command = args.get("command") or args.get("cmd")
    command = command if isinstance(command, str) else None
    paths = extract_paths(args, command)
    line_range = line_range_from_args(args, command)
    pattern = args.get("pattern") if isinstance(args.get("pattern"), str) else None

    if action == "event" and not tool_name and not paths and not command:
        return None

    trace = {
        "index": index,
        "jsonl_line": event.get("_jsonl_line"),
        "action": action,
        "tool": tool_name,
        "event_type": event_type,
        "paths": paths,
    }
    if line_range:
        trace["lines"] = line_range
    if pattern:
        trace["pattern"] = pattern
    if command:
        trace["command"] = command
    return {key: value for key, value in trace.items() if value not in [None, [], ""]}


def extract_trace(stdout_path: pathlib.Path, trace_jsonl_path: pathlib.Path, trace_md_path: pathlib.Path) -> list[dict[str, Any]]:
    raw_events = parse_jsonl(stdout_path)
    trace_events: list[dict[str, Any]] = []
    for index, event in enumerate(raw_events, start=1):
        trace = normalize_trace_event(index, event)
        if trace:
            trace_events.append(trace)

    with trace_jsonl_path.open("w", encoding="utf-8") as handle:
        for trace in trace_events:
            handle.write(json.dumps(trace, ensure_ascii=False, sort_keys=True) + "\n")

    trace_md_path.write_text(render_trace_markdown(trace_events), encoding="utf-8")
    return trace_events


def render_trace_markdown(trace_events: list[dict[str, Any]]) -> str:
    lines = ["# OpenCode Trace", ""]
    if not trace_events:
        lines.extend(
            [
                "No normalized tool events were found in `stdout.jsonl`.",
                "",
                "Inspect `stdout.jsonl` and `stderr.log` for the raw OpenCode stream.",
            ]
        )
        return "\n".join(lines) + "\n"

    for event in trace_events:
        parts = [f"{event['index']}.", f"`{event['action']}`"]
        if event.get("tool"):
            parts.append(f"via `{event['tool']}`")
        if event.get("paths"):
            parts.append("paths: " + ", ".join(f"`{path}`" for path in event["paths"]))
        if event.get("lines"):
            parts.append(f"lines {event['lines']['start']}-{event['lines']['end']}")
        if event.get("pattern"):
            parts.append(f"pattern `{event['pattern']}`")
        lines.append(" ".join(parts))
        if event.get("command"):
            lines.append(f"   command: `{event['command']}`")
    return "\n".join(lines) + "\n"


def summarize_reasoning_text(text: str) -> str:
    lowered = text.lower()
    if "start by reading" in lowered or ("read" in lowered and "document" in lowered):
        return "planned to inspect task inputs and documents"
    if "analyze this legal case" in lowered or "zulässigkeit" in lowered or "begründetheit" in lowered:
        return "worked through admissibility and merits issues before drafting"
    if "write the full legal analysis" in lowered or "fallloesung-sut.md" in lowered and "write" in lowered:
        return "planned to write the final Markdown solution"
    if "verify" in lowered or "file has been written" in lowered:
        return "planned to verify the written output file"
    return "provider emitted reasoning detail"


def extract_openrouter_reasoning_details(event: dict[str, Any]) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for data in iter_dicts(event):
        openrouter = data.get("openrouter")
        if isinstance(openrouter, dict) and isinstance(openrouter.get("reasoning_details"), list):
            details.extend(item for item in openrouter["reasoning_details"] if isinstance(item, dict))
    return details


def extract_reasoning_summary(stdout_path: pathlib.Path, output_path: pathlib.Path) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for index, event in enumerate(parse_jsonl(stdout_path), start=1):
        details = extract_openrouter_reasoning_details(event)
        if not details:
            continue
        part = event.get("part") if isinstance(event.get("part"), dict) else {}
        state = part.get("state") if isinstance(part.get("state"), dict) else {}
        input_data = state.get("input") if isinstance(state.get("input"), dict) else {}
        texts = [str(detail.get("text", "")) for detail in details]
        summary_labels = list(dict.fromkeys(summarize_reasoning_text(text) for text in texts if text))
        entry = {
            "index": event.get("_jsonl_line", index),
            "event_type": event.get("type"),
            "tool": part.get("tool"),
            "path": input_data.get("filePath") or input_data.get("path"),
            "command": input_data.get("command"),
            "reasoning_detail_count": len(details),
            "reasoning_char_count": sum(len(text) for text in texts),
            "summary": "; ".join(summary_labels) if summary_labels else "provider emitted reasoning detail",
        }
        summaries.append({key: value for key, value in entry.items() if value not in [None, "", []]})
    output_path.write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summaries


def base_env() -> dict[str, str]:
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    env["OPENCODE_CONFIG_CONTENT"] = json.dumps(OPENCODE_PERMISSION_CONFIG, separators=(",", ":"))
    return env


def docker_command(args: argparse.Namespace, row: dict[str, Any], input_dir: pathlib.Path, work_dir: pathlib.Path, task_dir: pathlib.Path) -> tuple[list[str], str | None]:
    container_name = safe_container_name(row["task_id"])
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        "--network",
        args.docker_network,
        "--cpus",
        str(args.docker_cpus),
        "--memory",
        str(args.docker_memory),
        "--pids-limit",
        str(args.docker_pids_limit),
        "--security-opt",
        "no-new-privileges",
        "--cap-drop",
        "ALL",
        "-e",
        f"OPENCODE_MODEL={args.model}",
        "-e",
        f"OPENCODE_VARIANT={args.variant}",
        "-e",
        f"TASK_ID={row['task_id']}",
        "-e",
        f"OPENCODE_CONFIG_CONTENT={json.dumps(OPENCODE_PERMISSION_CONFIG, separators=(',', ':'))}",
        "-e",
        "NO_COLOR=1",
        "-v",
        f"{input_dir.resolve()}:/task:ro",
        "-v",
        f"{work_dir.resolve()}:/work:rw",
        "-v",
        f"{task_dir.resolve()}:/out:rw",
    ]

    if args.agent:
        command.extend(["-e", f"OPENCODE_AGENT={args.agent}"])

    for env_name in ["OPENROUTER_API_KEY"]:
        if os.environ.get(env_name):
            command.extend(["-e", env_name])

    if not args.no_docker_auth_mount and args.docker_auth_path.exists():
        command.extend(["-v", f"{args.docker_auth_path.resolve()}:/home/node/.local/share/opencode/auth.json:ro"])

    command.append(args.docker_image)
    return command, container_name


def local_command(args: argparse.Namespace, row: dict[str, Any], work_dir: pathlib.Path, prompt: str) -> tuple[list[str], str | None]:
    command = [
        args.opencode_bin,
        "run",
        "--dir",
        str(work_dir.resolve()),
        "--model",
        args.model,
        "--variant",
        args.variant,
        "--format",
        "json",
        "--title",
        f"LAB-EU {row['task_id']}",
        "--dangerously-skip-permissions",
    ]
    if args.agent:
        command.extend(["--agent", args.agent])
    command.append(prompt)
    return command, None


def run_command(
    command: list[str],
    stdout_path: pathlib.Path,
    stderr_path: pathlib.Path,
    timeout_seconds: int,
    env: dict[str, str],
    cleanup_container: str | None,
) -> dict[str, Any]:
    started = time.monotonic()
    started_at = iso_now()
    timed_out = False
    exit_code: int | None = None

    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(command, cwd=REPO_ROOT, env=env, stdout=stdout, stderr=stderr)
        try:
            exit_code = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
            if cleanup_container:
                subprocess.run(
                    ["docker", "rm", "-f", cleanup_container],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            exit_code = 124

    ended_at = iso_now()
    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": round(time.monotonic() - started, 3),
        "exit_code": exit_code,
        "timed_out": timed_out,
    }


def prepare_task_run(run_dir: pathlib.Path, row: dict[str, Any]) -> dict[str, pathlib.Path]:
    task_run_dir = run_dir / "tasks" / safe_task_id(row["task_id"])
    input_dir = task_run_dir / "input"
    work_dir = task_run_dir / "work"
    task_run_dir.mkdir(parents=True, exist_ok=True)

    copy_sanitized_task(row["task_dir"], input_dir)
    copy_tree_contents(input_dir, work_dir)

    prompt = render_prompt(row, input_dir)
    (task_run_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    (task_run_dir / "input_task_dir.txt").write_text(str(row["task_dir"]) + "\n", encoding="utf-8")
    return {"task_run_dir": task_run_dir, "input_dir": input_dir, "work_dir": work_dir}


def run_one_task(args: argparse.Namespace, row: dict[str, Any], run_dir: pathlib.Path) -> dict[str, Any]:
    paths = prepare_task_run(run_dir, row)
    task_run_dir = paths["task_run_dir"]
    input_dir = paths["input_dir"]
    work_dir = paths["work_dir"]
    prompt = (task_run_dir / "prompt.md").read_text(encoding="utf-8")

    stdout_path = task_run_dir / "stdout.jsonl"
    stderr_path = task_run_dir / "stderr.log"
    trace_jsonl_path = task_run_dir / "trace.jsonl"
    trace_md_path = task_run_dir / "trace.md"
    reasoning_summary_path = task_run_dir / "reasoning_trace.summary.json"
    fs_changes_path = task_run_dir / "fs_changes.json"
    before_snapshot_path = task_run_dir / "workspace.before.json"
    after_snapshot_path = task_run_dir / "workspace.after.json"

    before_snapshot = snapshot_workspace(work_dir)
    before_snapshot_path.write_text(json.dumps(before_snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.sandbox == "docker":
        command, cleanup_container = docker_command(args, row, input_dir, work_dir, task_run_dir)
    else:
        command, cleanup_container = local_command(args, row, work_dir, prompt)

    command_result = run_command(
        command=command,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_seconds=args.timeout_seconds,
        env=base_env(),
        cleanup_container=cleanup_container,
    )

    after_snapshot = snapshot_workspace(work_dir)
    after_snapshot_path.write_text(json.dumps(after_snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fs_changes = diff_snapshots(before_snapshot, after_snapshot)
    fs_changes_path.write_text(json.dumps(fs_changes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    trace_events = extract_trace(stdout_path, trace_jsonl_path, trace_md_path)
    reasoning_summaries = extract_reasoning_summary(stdout_path, reasoning_summary_path)

    deliverable_results = collect_deliverables(work_dir, task_run_dir, row["deliverables"])
    archive_path = None
    if not args.skip_workspace_archive:
        archive_path = task_run_dir / "workspace.tar.gz"
        archive_workspace(work_dir, archive_path)

    metadata = {
        "schema_version": "0.1",
        "task_id": row["task_id"],
        "source_task_dir": str(row["task_dir"]),
        "source_task_dir_relative": relative_to_repo(row["task_dir"]),
        "task_run_dir": str(task_run_dir),
        "sandbox": args.sandbox,
        "command": command,
        "model": args.model,
        "variant": args.variant,
        "agent": args.agent or None,
        "expected_deliverables": row["deliverables"],
        "actual_deliverables": deliverable_results,
        "missing_deliverables": [item["path"] for item in deliverable_results if not item.get("found")],
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "trace_jsonl": str(trace_jsonl_path),
        "trace_markdown": str(trace_md_path),
        "trace_event_count": len(trace_events),
        "reasoning_trace_summary": str(reasoning_summary_path),
        "reasoning_summary_count": len(reasoning_summaries),
        "fs_changes": str(fs_changes_path),
        "fs_change_summary": {
            "created": len(fs_changes["created"]),
            "modified": len(fs_changes["modified"]),
            "deleted": len(fs_changes["deleted"]),
            "unchanged": fs_changes["unchanged_count"],
        },
        "workspace_before_snapshot": str(before_snapshot_path),
        "workspace_after_snapshot": str(after_snapshot_path),
        "workspace_archive": str(archive_path) if archive_path else None,
        **command_result,
    }
    (task_run_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def write_manifest(args: argparse.Namespace, run_dir: pathlib.Path, run_id: str, rows: list[dict[str, Any]]) -> None:
    manifest = {
        "schema_version": "0.1",
        "harness": "opencode",
        "run_id": run_id,
        "run_name": args.run_name,
        "created_at": iso_now(),
        "taskset": relative_to_repo(args.taskset if args.taskset.is_absolute() else REPO_ROOT / args.taskset),
        "n_tasks": len(rows),
        "sandbox": args.sandbox,
        "model": args.model,
        "variant": args.variant,
        "agent": args.agent or None,
        "opencode_version": opencode_version(args.opencode_bin) if args.sandbox == "local" else "container",
        "default_model_verified_locally": DEFAULT_MODEL,
        "permission_config": OPENCODE_PERMISSION_CONFIG,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = load_taskset(args.taskset)

    if args.dry_run:
        print(f"Validated {len(rows)} task(s).")
        print(f"Sandbox: {args.sandbox}")
        print(f"Model: {args.model}")
        print(f"Variant: {args.variant}")
        for row in rows:
            print(f"- {row['task_id']} -> {relative_to_repo(row['task_dir'])}")
        return 0

    run_id = make_run_id()
    run_dir = (args.runs_dir if args.runs_dir.is_absolute() else REPO_ROOT / args.runs_dir) / args.run_name / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    write_manifest(args, run_dir, run_id, rows)

    max_workers = max(1, args.parallel)
    failures = 0
    if max_workers == 1:
        for row in rows:
            metadata = run_one_task(args, row, run_dir)
            missing = metadata["missing_deliverables"]
            if metadata["exit_code"] != 0 or missing:
                failures += 1
            print(f"{row['task_id']}: exit={metadata['exit_code']} missing={len(missing)}")
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_row = {pool.submit(run_one_task, args, row, run_dir): row for row in rows}
            for future in as_completed(future_to_row):
                row = future_to_row[future]
                try:
                    metadata = future.result()
                except Exception as exc:  # noqa: BLE001
                    failures += 1
                    print(f"{row['task_id']}: failed before metadata: {exc}", file=sys.stderr)
                    continue
                missing = metadata["missing_deliverables"]
                if metadata["exit_code"] != 0 or missing:
                    failures += 1
                print(f"{row['task_id']}: exit={metadata['exit_code']} missing={len(missing)}")

    print(f"Wrote run: {run_dir}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
