#!/usr/bin/env python3
"""Generate lawyer-facing Markdown review bundles for LAB-EU rubrics."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate evals/rubric-review.md from task.json, case, solution, and rubric.json."
    )
    parser.add_argument(
        "task_dir",
        nargs="+",
        type=pathlib.Path,
        help="Task directory containing task.json, documents/, and evals/rubric.json.",
    )
    return parser.parse_args()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def comma_list(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def solution_path(task_dir: pathlib.Path) -> pathlib.Path:
    preferred = task_dir / "evals" / "loesung.md"
    if preferred.exists():
        return preferred

    evals_dir = task_dir / "evals"
    candidates = [
        path
        for path in sorted(evals_dir.iterdir())
        if path.is_file()
        and not path.name.startswith("rubric")
        and path.name != "scores.json"
        and path.suffix.lower() in {".md", ".txt"}
    ]
    if not candidates:
        raise SystemExit(f"No solution file found in {evals_dir}")
    return candidates[0]


def case_paths(task_dir: pathlib.Path) -> list[pathlib.Path]:
    documents_dir = task_dir / "documents"
    if not documents_dir.exists():
        raise SystemExit(f"Missing documents directory: {documents_dir}")

    preferred = documents_dir / "sachverhalt.md"
    if preferred.exists():
        return [preferred]

    paths = [
        path
        for path in sorted(documents_dir.rglob("*"))
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}
    ]
    if not paths:
        raise SystemExit(f"No case document found in {documents_dir}")
    return paths


def append_file_section(
    lines: list[str],
    heading: str,
    paths: list[pathlib.Path],
    task_dir: pathlib.Path,
) -> None:
    lines.append(f"## {heading}")
    lines.append("")
    if len(paths) == 1:
        lines.append(read_text(paths[0]))
        lines.append("")
        return

    for path in paths:
        lines.append(f"### {path.relative_to(task_dir)}")
        lines.append("")
        lines.append(read_text(path))
        lines.append("")


def build_markdown(task_dir: pathlib.Path) -> str:
    task = load_json(task_dir / "task.json")
    rubric = load_json(task_dir / "evals" / "rubric.json")
    solution = solution_path(task_dir)
    criteria = rubric.get("criteria", [])
    if not isinstance(criteria, list) or not criteria:
        raise SystemExit(f"{task_dir / 'evals' / 'rubric.json'} has no criteria list.")

    lines: list[str] = []
    lines.append(f"# Rubric Review: {task.get('title', task_dir.name)}")
    lines.append("")
    lines.append("## Task")
    lines.append("")
    lines.append(f"**Title:** {task.get('title', '')}")
    lines.append("")
    lines.append(f"**Work type:** {task.get('work_type', '')}")
    lines.append("")
    lines.append(f"**Deliverable:** {comma_list(task.get('deliverables'))}")
    lines.append("")
    lines.append(f"**Tags:** {comma_list(task.get('tags'))}")
    lines.append("")
    lines.append("**Instructions:**")
    lines.append("")
    lines.append(str(task.get("instructions", "")).strip())
    lines.append("")

    append_file_section(lines, "Case", case_paths(task_dir), task_dir)
    append_file_section(lines, "Solution", [solution], task_dir)

    lines.append("## Rubrics For Review")
    lines.append("")
    lines.append(f"**Generated at:** {rubric.get('generated_at', '')}")
    lines.append("")
    lines.append(f"**Review status:** {rubric.get('review_status', '')}")
    lines.append("")
    lines.append(f"**Language:** {rubric.get('language', '')}")
    lines.append("")
    lines.append(f"**Number of criteria:** {len(criteria)}")
    lines.append("")

    for criterion in criteria:
        lines.append(f"### {criterion.get('id', '')} - {criterion.get('title', '')}")
        lines.append("")
        lines.append("**Match criteria**")
        lines.append("")
        lines.append(str(criterion.get("match_criteria", "")).strip())
        lines.append("")
        lines.append("**Review notes**")
        lines.append("")
        notes = criterion.get("review_notes") or []
        if notes:
            for note in notes:
                lines.append(f"- {note}")
        else:
            lines.append("- (none)")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_review(task_dir: pathlib.Path) -> pathlib.Path:
    output_path = task_dir / "evals" / "rubric-review.md"
    output_path.write_text(build_markdown(task_dir), encoding="utf-8")
    return output_path


def main() -> int:
    args = parse_args()
    for raw_task_dir in args.task_dir:
        task_dir = raw_task_dir.resolve()
        output_path = write_review(task_dir)
        rubric = load_json(task_dir / "evals" / "rubric.json")
        print(f"Wrote {output_path} ({len(rubric.get('criteria', []))} criteria)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
