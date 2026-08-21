"""Shared prompt rendering for the single-call baseline and local workbench."""

from __future__ import annotations

import datetime as dt
import hashlib
import re
import pathlib
from typing import Any

from task_identity import task_format_label


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPT_TEMPLATE = REPO_ROOT / "prompts" / "harness" / "solve_task_baseline.txt"
MULTI_PROMPT_TEMPLATE = REPO_ROOT / "prompts" / "harness" / "solve_task_baseline_multi.txt"
FILE_MARKER = re.compile(r"^===\s*FILE:\s*(?P<name>.+?)\s*===\s*$", re.MULTILINE)
MAX_DOC_CHARS = 120_000
MAX_TOTAL_DOC_CHARS = 300_000


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


def render_prompt(
    task_id: str,
    task: dict[str, Any],
    task_dir: pathlib.Path,
    deliverable: str,
    today: dt.date | None = None,
) -> tuple[str, bool]:
    documents, truncated = render_documents(task_dir)
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    prompt = template.format(
        today=(today or dt.date.today()).isoformat(),
        task_id=task_id,
        title=task_format_label(task.get("title")),
        work_type=task.get("work_type", ""),
        instructions=task.get("instructions", ""),
        documents=documents,
        deliverable=deliverable,
    )
    return prompt, truncated


def strip_outer_fence(text: str) -> tuple[str, bool]:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2 and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip() + "\n", True
    return text, False


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_multi_prompt(
    task_id: str,
    task: dict[str, Any],
    task_dir: pathlib.Path,
    deliverables: list[str],
    today: dt.date | None = None,
) -> tuple[str, bool]:
    """Single-call prompt for tasks with more than one deliverable.

    The Second State Exam tasks require two or three work products; the baseline
    arm has to produce them in one response, so the model emits them separated by
    marker lines that split_multi_response turns back into files.
    """
    documents, truncated = render_documents(task_dir)
    template = MULTI_PROMPT_TEMPLATE.read_text(encoding="utf-8")
    prompt = template.format(
        today=(today or dt.date.today()).isoformat(),
        task_id=task_id,
        title=task_format_label(task.get("title")),
        work_type=task.get("work_type", ""),
        instructions=task.get("instructions", ""),
        documents=documents,
        deliverables_block="\n".join(f"- {name}" for name in deliverables),
    )
    return prompt, truncated


def split_multi_response(text: str, deliverables: list[str]) -> dict[str, str]:
    """Split a marker-separated response into {filename: content}.

    Only the declared deliverables are returned; an unknown or repeated marker is
    ignored so a stray marker inside prose cannot invent or overwrite a file. A
    deliverable the model omitted is simply absent, which the runner records as
    missing rather than silently writing an empty file.
    """
    matches = list(FILE_MARKER.finditer(text))
    if not matches:
        return {}
    wanted = {name.strip(): name for name in deliverables}
    out: dict[str, str] = {}
    for index, match in enumerate(matches):
        raw = match.group("name").strip().strip("`\"'")
        name = wanted.get(raw)
        if name is None or name in out:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        if body:
            out[name] = body + "\n"
    return out
