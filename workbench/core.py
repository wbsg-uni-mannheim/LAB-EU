"""Task discovery, manual-run persistence, and guarded Git submission."""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import secrets
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any

from scripts.baseline_prompt import render_prompt, sha256_text, strip_outer_fence
from scripts.run_opencode_taskset import safe_task_id


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
TASKS_ROOT = REPO_ROOT / "tasks"
RUNS_ROOT = REPO_ROOT / "runs" / "manual"
STUDIES_ROOT = REPO_ROOT / "runs" / "studies"
STUDY_SYSTEM_PROMPT = REPO_ROOT / "prompts" / "harness" / "study_system_prompt.txt"


class WorkbenchError(ValueError):
    """A safe, user-facing workbench error."""


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    task_dir: pathlib.Path
    task: dict[str, Any]
    deliverable: str
    language: str

    @property
    def judge_ready(self) -> bool:
        return (self.task_dir / "evals" / "rubric.json").is_file()

    def summary(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.task.get("title", self.task_id),
            "language": self.language,
            "jurisdiction": self.task.get("jurisdiction", self.language.upper()),
            "work_type": self.task.get("work_type", ""),
            "tags": self.task.get("tags", []),
            "deliverable": self.deliverable,
            "validation_status": self.task.get("validation_status", ""),
            "judge_ready": self.judge_ready,
        }


def _resolve_under(path: pathlib.Path, parent: pathlib.Path, label: str) -> pathlib.Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(parent.resolve())
    except ValueError as exc:
        raise WorkbenchError(f"{label} must remain below {parent}") from exc
    return resolved


def _deliverable(task: dict[str, Any]) -> str:
    raw = task.get("deliverables")
    if isinstance(raw, str) and raw.strip():
        value = raw.strip()
    elif isinstance(raw, list) and len(raw) == 1 and isinstance(raw[0], str):
        value = raw[0].strip()
    else:
        raise WorkbenchError("The workbench supports tasks with exactly one deliverable.")
    path = pathlib.PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise WorkbenchError("Invalid deliverable path.")
    return value


def discover_tasks(tasks_root: pathlib.Path = TASKS_ROOT) -> list[TaskRecord]:
    records: list[TaskRecord] = []
    if not tasks_root.is_dir():
        return records
    for task_json in sorted(tasks_root.rglob("task.json")):
        task_dir = task_json.parent
        if not (task_dir / "documents").is_dir():
            continue
        try:
            task = json.loads(task_json.read_text(encoding="utf-8"))
            deliverable = _deliverable(task)
        except (json.JSONDecodeError, OSError, WorkbenchError):
            continue
        task_id = task_dir.relative_to(tasks_root).as_posix()
        language = str(task.get("language") or task_id.split("/", 1)[0]).lower()
        if language not in {"de", "fr"}:
            continue
        records.append(TaskRecord(task_id, task_dir, task, deliverable, language))
    return records


def get_task(task_id: str, tasks_root: pathlib.Path = TASKS_ROOT) -> TaskRecord:
    if not task_id or "\\" in task_id:
        raise WorkbenchError("Invalid task id.")
    task_dir = _resolve_under(tasks_root / task_id, tasks_root, "Task path")
    task_json = task_dir / "task.json"
    if not task_json.is_file() or not (task_dir / "documents").is_dir():
        raise WorkbenchError("Task not found.")
    try:
        task = json.loads(task_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise WorkbenchError("The task metadata is invalid.") from exc
    language = str(task.get("language") or task_id.split("/", 1)[0]).lower()
    if language not in {"de", "fr"}:
        raise WorkbenchError("Only German and French tasks are supported.")
    return TaskRecord(task_id, task_dir, task, _deliverable(task), language)


def task_payload(record: TaskRecord, today: dt.date | None = None) -> dict[str, Any]:
    prompt, truncated = render_prompt(
        task_id=record.task_id,
        task=record.task,
        task_dir=record.task_dir,
        deliverable=record.deliverable,
        today=today,
    )
    documents = [
        {
            "path": path.relative_to(record.task_dir).as_posix(),
            "content": path.read_text(encoding="utf-8", errors="replace"),
        }
        for path in sorted((record.task_dir / "documents").rglob("*"))
        if path.is_file()
    ]
    payload = record.summary()
    payload.update(
        {
            "instructions": record.task.get("instructions", ""),
            "documents": documents,
            "prompt": prompt,
            "prompt_sha256": sha256_text(prompt),
            "documents_truncated_in_prompt": truncated,
        }
    )
    return payload


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def default_study_system_prompt() -> str:
    try:
        return STUDY_SYSTEM_PROMPT.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkbenchError("The LAB-EU study system prompt is missing.") from exc


def combine_study_prompt(system_prompt: str, case_prompt: str) -> str:
    return (
        "## SYSTEM INSTRUCTIONS\n\n"
        f"{system_prompt.rstrip()}\n\n"
        "---\n\n"
        "## CURRENT LAB-EU TASK\n\n"
        f"{case_prompt.lstrip()}"
    )


def _study_id() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)


def _study_dir(study_id: str, studies_root: pathlib.Path = STUDIES_ROOT) -> pathlib.Path:
    if not re.fullmatch(r"[0-9TZ-]+[a-f0-9]{6}", study_id):
        raise WorkbenchError("Invalid study id.")
    study_dir = _resolve_under(studies_root / study_id, studies_root, "Study path")
    if not (study_dir / "manifest.json").is_file():
        raise WorkbenchError("Study not found.")
    return study_dir


def _read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise WorkbenchError(f"Invalid stored data: {path.name}") from exc


def _write_json(path: pathlib.Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_study(
    name: str,
    model: str,
    language: str,
    system_prompt: str,
    reviewer: str,
    provider: str,
    capabilities: dict[str, bool],
    judge_ready_only: bool,
    studies_root: pathlib.Path = STUDIES_ROOT,
) -> dict[str, Any]:
    name = name.strip()
    model = model.strip()
    language = language.strip().lower()
    stored_system_prompt = system_prompt
    if not name:
        raise WorkbenchError("The study name is required.")
    if not model:
        raise WorkbenchError("The model name is required.")
    if language not in {"de", "fr"}:
        raise WorkbenchError("Choose German or French as the study language.")
    if not stored_system_prompt.strip():
        raise WorkbenchError("The system prompt is required.")

    records = [record for record in discover_tasks() if record.language == language]
    if judge_ready_only:
        records = [record for record in records if record.judge_ready]
    if not records:
        raise WorkbenchError("No matching tasks were found for this study.")

    normalized_capabilities = {
        key: bool(capabilities.get(key, False))
        for key in [
            "agent",
            "single_llm",
            "web_search",
            "databases",
            "other_tools",
            "system_unknown",
        ]
    }
    if normalized_capabilities["system_unknown"]:
        for key in ["agent", "single_llm", "web_search", "databases", "other_tools"]:
            normalized_capabilities[key] = False
    elif normalized_capabilities["agent"] == normalized_capabilities["single_llm"]:
        raise WorkbenchError("Choose exactly one execution type: agent or single LLM.")

    study_id = _study_id()
    study_dir = _resolve_under(studies_root / study_id, studies_root, "Study path")
    study_dir.mkdir(parents=True, exist_ok=False)
    created_at = iso_now()
    manifest = {
        "schema_version": "0.2",
        "harness": "manual-study",
        "run_id": study_id,
        "run_name": name,
        "study_name": name,
        "created_at": created_at,
        "updated_at": created_at,
        "study_date": dt.date.today().isoformat(),
        "language": language,
        "reviewer": reviewer.strip() or None,
        "provider": provider.strip() or None,
        "model": model,
        "capabilities": normalized_capabilities,
        "judge_ready_only": bool(judge_ready_only),
        "system_prompt_file": "system_prompt.md",
        "system_prompt_sha256": sha256_text(stored_system_prompt),
        "task_ids": [record.task_id for record in records],
        "n_tasks": len(records),
        "n_completed": 0,
        "status": "active",
    }
    (study_dir / "system_prompt.md").write_text(stored_system_prompt, encoding="utf-8")
    _write_json(study_dir / "manifest.json", manifest)
    return study_payload(study_id, studies_root)


def _completed_task_ids(study_dir: pathlib.Path) -> set[str]:
    completed: set[str] = set()
    tasks_dir = study_dir / "tasks"
    if not tasks_dir.is_dir():
        return completed
    for metadata_path in tasks_dir.glob("*/metadata.json"):
        metadata = _read_json(metadata_path)
        if metadata.get("exit_code") == 0 and metadata.get("task_id"):
            completed.add(str(metadata["task_id"]))
    return completed


def study_payload(study_id: str, studies_root: pathlib.Path = STUDIES_ROOT) -> dict[str, Any]:
    study_dir = _study_dir(study_id, studies_root)
    manifest = _read_json(study_dir / "manifest.json")
    completed = _completed_task_ids(study_dir)
    task_ids = [str(task_id) for task_id in manifest.get("task_ids", [])]
    status = str(manifest.get("status", "active"))
    next_task_id = next((task_id for task_id in task_ids if task_id not in completed), None)
    current_task_id = next_task_id if status == "active" else None
    complete = status in {"completed", "ended_early"} or next_task_id is None
    system_prompt = (study_dir / "system_prompt.md").read_text(encoding="utf-8")
    payload: dict[str, Any] = {
        "study_id": study_id,
        "study_name": manifest.get("study_name"),
        "language": manifest.get("language"),
        "reviewer": manifest.get("reviewer"),
        "provider": manifest.get("provider"),
        "model": manifest.get("model"),
        "capabilities": manifest.get("capabilities", {}),
        "judge_ready_only": manifest.get("judge_ready_only", False),
        "system_prompt": system_prompt,
        "system_prompt_sha256": manifest.get("system_prompt_sha256"),
        "n_tasks": len(task_ids),
        "n_completed": len(completed),
        "n_remaining": len(task_ids) - len(completed),
        "status": "completed" if status == "active" and next_task_id is None else status,
        "complete": complete,
        "ended_early": status == "ended_early",
        "ended_at": manifest.get("ended_at"),
        "run_dir": str(study_dir),
        "run_dir_relative": (
            study_dir.relative_to(REPO_ROOT).as_posix()
            if study_dir.is_relative_to(REPO_ROOT)
            else str(study_dir)
        ),
    }
    if current_task_id:
        study_date = dt.date.fromisoformat(str(manifest["study_date"]))
        current_task = task_payload(get_task(current_task_id), today=study_date)
        combined_prompt = combine_study_prompt(system_prompt, current_task["prompt"])
        current_task["combined_prompt"] = combined_prompt
        current_task["combined_prompt_sha256"] = sha256_text(combined_prompt)
        payload["current_task"] = current_task
    else:
        payload["current_task"] = None
        payload["judge_command"] = (
            f"env/bin/python scripts/judge_run.py {payload['run_dir_relative']} "
            "--judge-model gpt-5.5 --votes 3"
            if manifest.get("judge_ready_only") and completed
            else None
        )
    return payload


def list_studies(studies_root: pathlib.Path = STUDIES_ROOT) -> list[dict[str, Any]]:
    if not studies_root.is_dir():
        return []
    studies: list[dict[str, Any]] = []
    for manifest_path in sorted(studies_root.glob("*/manifest.json"), reverse=True):
        try:
            manifest = _read_json(manifest_path)
            completed = _completed_task_ids(manifest_path.parent)
        except WorkbenchError:
            continue
        studies.append(
            {
                "study_id": manifest_path.parent.name,
                "study_name": manifest.get("study_name"),
                "language": manifest.get("language"),
                "model": manifest.get("model"),
                "n_tasks": manifest.get("n_tasks", 0),
                "n_completed": len(completed),
                "status": manifest.get("status", "active"),
                "complete": manifest.get("status") in {"completed", "ended_early"}
                or len(completed) >= int(manifest.get("n_tasks", 0)),
                "ended_early": manifest.get("status") == "ended_early",
                "updated_at": manifest.get("updated_at"),
            }
        )
    return studies


def save_study_answer(
    study_id: str,
    task_id: str,
    response: str,
    confidentiality_confirmed: bool,
    studies_root: pathlib.Path = STUDIES_ROOT,
) -> dict[str, Any]:
    if not confidentiality_confirmed:
        raise WorkbenchError("Confirm that the response contains no confidential client data.")
    if not response.strip():
        raise WorkbenchError("The model response is empty.")
    study_dir = _study_dir(study_id, studies_root)
    manifest = _read_json(study_dir / "manifest.json")
    if manifest.get("status", "active") != "active":
        raise WorkbenchError("This study has already been closed.")
    current = study_payload(study_id, studies_root).get("current_task")
    if current is None:
        raise WorkbenchError("This study is already complete.")
    if task_id != current["task_id"]:
        raise WorkbenchError("The submitted task is not the current study task.")

    record = get_task(task_id)
    study_date = dt.date.fromisoformat(str(manifest["study_date"]))
    case_prompt, documents_truncated = render_prompt(
        task_id=record.task_id,
        task=record.task,
        task_dir=record.task_dir,
        deliverable=record.deliverable,
        today=study_date,
    )
    system_prompt = (study_dir / "system_prompt.md").read_text(encoding="utf-8")
    combined_prompt = combine_study_prompt(system_prompt, case_prompt)
    deliverable_text, fence_stripped = strip_outer_fence(response)
    task_run_dir = study_dir / "tasks" / safe_task_id(record.task_id)
    submission_dir = task_run_dir / "submission"
    if task_run_dir.exists():
        raise WorkbenchError("An answer for this task already exists.")
    submission_dir.mkdir(parents=True, exist_ok=False)
    (task_run_dir / "prompt.md").write_text(case_prompt, encoding="utf-8")
    (task_run_dir / "combined_prompt.md").write_text(combined_prompt, encoding="utf-8")
    (task_run_dir / "response.md").write_text(response, encoding="utf-8")
    deliverable_path = submission_dir / record.deliverable
    deliverable_path.parent.mkdir(parents=True, exist_ok=True)
    deliverable_path.write_text(deliverable_text, encoding="utf-8")
    metadata = {
        "schema_version": "0.2",
        "harness": "manual-study",
        "study_id": study_id,
        "study_name": manifest.get("study_name"),
        "task_id": record.task_id,
        "source_task_dir": str(record.task_dir.resolve()),
        "source_task_dir_relative": record.task_dir.relative_to(REPO_ROOT).as_posix(),
        "task_run_dir": str(task_run_dir.resolve()),
        "language": record.language,
        "reviewer": manifest.get("reviewer"),
        "provider": manifest.get("provider"),
        "model": manifest.get("model"),
        "capabilities": manifest.get("capabilities", {}),
        "system_prompt_file": "../../system_prompt.md",
        "system_prompt_sha256": manifest.get("system_prompt_sha256"),
        "prompt_sha256": sha256_text(case_prompt),
        "combined_prompt_file": "combined_prompt.md",
        "combined_prompt_sha256": sha256_text(combined_prompt),
        "response_sha256": sha256_text(response),
        "expected_deliverables": [record.deliverable],
        "actual_deliverables": [
            {
                "path": record.deliverable,
                "found": True,
                "bytes": len(deliverable_text.encode("utf-8")),
                "sha256": sha256_text(deliverable_text),
            }
        ],
        "missing_deliverables": [],
        "documents_truncated": documents_truncated,
        "stripped_outer_fence": fence_stripped,
        "judge_ready": record.judge_ready,
        "created_at": iso_now(),
        "exit_code": 0,
    }
    _write_json(task_run_dir / "metadata.json", metadata)
    completed = _completed_task_ids(study_dir)
    manifest["n_completed"] = len(completed)
    manifest["updated_at"] = iso_now()
    if len(completed) >= int(manifest.get("n_tasks", 0)):
        manifest["status"] = "completed"
        manifest["ended_at"] = manifest["updated_at"]
    _write_json(study_dir / "manifest.json", manifest)
    return study_payload(study_id, studies_root)


def end_study_early(
    study_id: str,
    confirmed: bool,
    studies_root: pathlib.Path = STUDIES_ROOT,
) -> dict[str, Any]:
    if not confirmed:
        raise WorkbenchError("Early submission requires explicit confirmation.")
    study_dir = _study_dir(study_id, studies_root)
    manifest = _read_json(study_dir / "manifest.json")
    if manifest.get("status", "active") != "active":
        raise WorkbenchError("This study has already been closed.")
    completed = _completed_task_ids(study_dir)
    if not completed:
        raise WorkbenchError("Save at least one case answer before submitting early.")
    ended_at = iso_now()
    task_ids = [str(task_id) for task_id in manifest.get("task_ids", [])]
    manifest["status"] = "ended_early"
    manifest["ended_at"] = ended_at
    manifest["updated_at"] = ended_at
    manifest["n_completed"] = len(completed)
    manifest["n_skipped"] = len(task_ids) - len(completed)
    manifest["skipped_task_ids"] = [task_id for task_id in task_ids if task_id not in completed]
    _write_json(study_dir / "manifest.json", manifest)
    return study_payload(study_id, studies_root)


def create_manual_run(
    record: TaskRecord,
    response: str,
    reviewer: str,
    provider: str,
    model: str,
    runs_root: pathlib.Path = RUNS_ROOT,
) -> dict[str, Any]:
    if not response.strip():
        raise WorkbenchError("The model response is empty.")
    prompt, documents_truncated = render_prompt(
        task_id=record.task_id,
        task=record.task,
        task_dir=record.task_dir,
        deliverable=record.deliverable,
    )
    deliverable_text, fence_stripped = strip_outer_fence(response)
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)
    run_dir = _resolve_under(runs_root / run_id, runs_root, "Run path")
    task_run_dir = run_dir / "tasks" / safe_task_id(record.task_id)
    submission_dir = task_run_dir / "submission"
    submission_dir.mkdir(parents=True, exist_ok=False)
    created_at = iso_now()

    (task_run_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    (task_run_dir / "response.md").write_text(response, encoding="utf-8")
    deliverable_path = submission_dir / record.deliverable
    deliverable_path.parent.mkdir(parents=True, exist_ok=True)
    deliverable_path.write_text(deliverable_text, encoding="utf-8")

    manifest = {
        "schema_version": "0.1",
        "harness": "manual-copy-paste",
        "run_id": run_id,
        "run_name": "manual",
        "created_at": created_at,
        "n_tasks": 1,
        "reviewer": reviewer.strip() or None,
        "provider": provider.strip() or None,
        "model": model.strip() or None,
    }
    metadata = {
        "schema_version": "0.1",
        "harness": "manual-copy-paste",
        "task_id": record.task_id,
        "source_task_dir": str(record.task_dir.resolve()),
        "source_task_dir_relative": record.task_dir.relative_to(REPO_ROOT).as_posix(),
        "task_run_dir": str(task_run_dir.resolve()),
        "language": record.language,
        "reviewer": reviewer.strip() or None,
        "provider": provider.strip() or None,
        "model": model.strip() or None,
        "prompt_sha256": sha256_text(prompt),
        "response_sha256": sha256_text(response),
        "expected_deliverables": [record.deliverable],
        "actual_deliverables": [
            {
                "path": record.deliverable,
                "found": True,
                "bytes": len(deliverable_text.encode("utf-8")),
                "sha256": sha256_text(deliverable_text),
            }
        ],
        "missing_deliverables": [],
        "documents_truncated": documents_truncated,
        "stripped_outer_fence": fence_stripped,
        "created_at": created_at,
        "exit_code": 0,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (task_run_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    try:
        run_reference = run_dir.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        run_reference = str(run_dir)
    judge_command = None
    if record.judge_ready:
        judge_command = (
            f"env/bin/python scripts/judge_run.py {run_reference} "
            "--judge-model gpt-5.5 --votes 3"
        )
    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "run_dir_relative": run_reference,
        "submission_dir": str(submission_dir),
        "judge_ready": record.judge_ready,
        "judge_command": judge_command,
    }


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)


def _status_entries() -> list[tuple[str, str]]:
    result = _run(["git", "status", "--porcelain", "--untracked-files=all"])
    if result.returncode != 0:
        raise WorkbenchError(result.stderr.strip() or "Could not read Git status.")
    entries: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append((status, path.strip('"')))
    return entries


def _unrelated_status_paths(entries: list[tuple[str, str]], target_prefix: str) -> list[str]:
    unrelated: list[str] = []
    for status, path in entries:
        if path == target_prefix[:-1] or path.startswith(target_prefix):
            continue
        if status == "??" and path.startswith("runs/"):
            continue
        unrelated.append(path)
    return unrelated


def git_readiness(run_dir_relative: str) -> dict[str, Any]:
    run_dir = _resolve_under(REPO_ROOT / run_dir_relative, REPO_ROOT / "runs", "Run path")
    if not (run_dir / "manifest.json").is_file():
        raise WorkbenchError("Manual run not found.")
    prefix = run_dir.relative_to(REPO_ROOT).as_posix() + "/"
    unrelated = _unrelated_status_paths(_status_entries(), prefix)
    branch_result = _run(["git", "branch", "--show-current"])
    current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else ""
    files = sorted(path.relative_to(REPO_ROOT).as_posix() for path in run_dir.rglob("*") if path.is_file())
    return {
        "ready": not unrelated and bool(current_branch),
        "current_branch": current_branch,
        "files_to_commit": files,
        "unrelated_changes": unrelated,
        "run_dir_relative": prefix[:-1],
    }


def _slug(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return (slug or fallback)[:48]


def submit_manual_run(
    run_dir_relative: str,
    task_id: str,
    reviewer: str,
    base_branch: str = "main",
    create_pull_request: bool = True,
) -> dict[str, Any]:
    readiness = git_readiness(run_dir_relative)
    run_manifest = _read_json(REPO_ROOT / readiness["run_dir_relative"] / "manifest.json")
    if run_manifest.get("harness") == "manual-study" and run_manifest.get("status") not in {
        "completed",
        "ended_early",
    }:
        raise WorkbenchError("Complete every task before submitting the study.")
    if not readiness["ready"]:
        preview = ", ".join(readiness["unrelated_changes"][:5])
        raise WorkbenchError(f"Git submission is blocked by unrelated changes: {preview}")
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", base_branch):
        raise WorkbenchError("Invalid base branch.")
    if readiness["current_branch"] != base_branch:
        raise WorkbenchError(
            f"Switch to the base branch {base_branch!r} before submitting; "
            f"the current branch is {readiness['current_branch']!r}."
        )

    date = dt.date.today().isoformat()
    branch = f"submission/{_slug(reviewer, 'reviewer')}/{date}-{_slug(task_id, 'task')}"
    if _run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"]).returncode == 0:
        branch += "-" + secrets.token_hex(2)
    switched = _run(["git", "switch", "-c", branch])
    if switched.returncode != 0:
        raise WorkbenchError(switched.stderr.strip() or "Could not create the submission branch.")

    run_path = readiness["run_dir_relative"]
    added = _run(["git", "add", "--", run_path])
    if added.returncode != 0:
        raise WorkbenchError(added.stderr.strip() or "Could not stage the manual run.")
    title = f"Add manual submission for {task_id}"
    committed = _run(["git", "commit", "-m", title])
    if committed.returncode != 0:
        raise WorkbenchError(committed.stderr.strip() or committed.stdout.strip() or "Git commit failed.")
    commit = _run(["git", "rev-parse", "HEAD"]).stdout.strip()

    pull_request_url = None
    if create_pull_request:
        if shutil.which("gh") is None:
            raise WorkbenchError(f"Commit {commit} was created, but the gh CLI is not installed.")
        pushed = _run(["git", "push", "-u", "origin", branch])
        if pushed.returncode != 0:
            raise WorkbenchError(f"Commit {commit} was created, but push failed: {pushed.stderr.strip()}")
        body = f"Manual copy/paste submission for `{task_id}`.\n\nRun: `{run_path}`"
        pr = _run(
            ["gh", "pr", "create", "--base", base_branch, "--head", branch, "--title", title, "--body", body]
        )
        if pr.returncode != 0:
            raise WorkbenchError(f"Commit {commit} was pushed, but PR creation failed: {pr.stderr.strip()}")
        pull_request_url = pr.stdout.strip().splitlines()[-1]
    return {"branch": branch, "commit": commit, "pull_request_url": pull_request_url}
