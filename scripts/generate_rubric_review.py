#!/usr/bin/env python3
"""Generate lawyer-facing Markdown review bundles for LAB-EU rubrics."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from outline_util import UE_ID, index_outline, walk  # noqa: E402
from generate_rubric import criticality_distribution_warnings  # noqa: E402


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
    parser.add_argument(
        "--rubric-name",
        default="rubric.json",
        help="Rubric filename inside evals/. Defaults to rubric.json.",
    )
    parser.add_argument(
        "--output-name",
        default="rubric-review.md",
        help="Review filename inside evals/. Defaults to rubric-review.md.",
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


def build_markdown(task_dir: pathlib.Path, rubric_name: str = "rubric.json") -> str:
    task = load_json(task_dir / "task.json")
    rubric = load_json(task_dir / "evals" / rubric_name)
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
    lines.append(f"**Number of criteria:** {len(criteria)}")
    lines.append("")

    tier_labels = {
        3: "★★★ ergebnistragend - entscheidet den Fall (Kardinalfehler, wenn verfehlt)",
        2: "★★ wichtig - in einer soliden Lösung erwartet",
        1: "★ eher unwichtig - Detail, Form, Bonuswissen",
    }
    tier_counts = {
        tier: sum(1 for c in criteria if c.get("criticality") == tier) for tier in (3, 2, 1)
    }
    if any(tier_counts.values()):
        lines.append("**Wichtigkeit (Kritikalität):**")
        lines.append("")
        for tier in (3, 2, 1):
            lines.append(f"- {tier_labels[tier]}: {tier_counts[tier]} Kriterien")
        lines.append("")
        distribution_warnings = criticality_distribution_warnings(criteria)
        if distribution_warnings:
            lines.append("**Freeze-Warnung zur Sterneverteilung:**")
            lines.append("")
            for warning in distribution_warnings:
                lines.append(f"- {warning}")
            lines.append("- Vor dem Freeze korrigieren oder die Abweichung fachlich begründen.")
            lines.append("")

    def render_criterion(criterion: dict[str, Any], heading: str) -> None:
        lines.append(f"{heading} {criterion.get('id', '')} - {criterion.get('title', '')}")
        lines.append("")
        if criterion.get("criticality") in (1, 2, 3):
            lines.append(f"**Wichtigkeit:** {tier_labels[criterion['criticality']]}")
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

    outline = rubric.get("outline") or []
    outline_ids = set(index_outline(outline)) if outline else set()
    tagged = {
        c.get("id"): (c.get("analysis_tags") or {}).get("outline_id")
        for c in criteria
    }
    if outline and any(oid in outline_ids for oid in tagged.values()):
        # Walk the Musterlösung's Gliederung; list each node's criteria under it.
        by_node: dict[str, list[dict[str, Any]]] = {}
        unmapped: list[dict[str, Any]] = []
        for criterion in criteria:
            oid = tagged.get(criterion.get("id"))
            if oid in outline_ids:
                by_node.setdefault(oid, []).append(criterion)
            else:
                unmapped.append(criterion)
        for node, depth, _path in walk(outline):
            group = by_node.get(node["id"], [])
            subtree_ids = [n["id"] for n, _d, _p in walk([node])]
            if not any(by_node.get(i) for i in subtree_ids):
                continue
            label = (
                node["label"]
                if node["id"] == UE_ID or node["id"] == node["label"]
                else f"{node['id']} {node['label']}"
            )
            lines.append(f"{'#' * min(2 + depth, 5)} {label}")
            lines.append("")
            for criterion in group:
                render_criterion(criterion, "#" * min(3 + depth, 6))
        if unmapped:
            lines.append("### Ohne Gliederungspunkt")
            lines.append("")
            for criterion in unmapped:
                render_criterion(criterion, "####")
    else:
        for criterion in criteria:
            render_criterion(criterion, "###")

    return "\n".join(lines).rstrip() + "\n"


def write_review(
    task_dir: pathlib.Path,
    rubric_name: str = "rubric.json",
    output_name: str = "rubric-review.md",
) -> pathlib.Path:
    output_path = task_dir / "evals" / output_name
    output_path.write_text(build_markdown(task_dir, rubric_name), encoding="utf-8")
    return output_path


def main() -> int:
    args = parse_args()
    for raw_task_dir in args.task_dir:
        task_dir = raw_task_dir.resolve()
        output_path = write_review(task_dir, args.rubric_name, args.output_name)
        rubric = load_json(task_dir / "evals" / args.rubric_name)
        print(f"Wrote {output_path} ({len(rubric.get('criteria', []))} criteria)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
