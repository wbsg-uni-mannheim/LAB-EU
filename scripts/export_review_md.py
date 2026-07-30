#!/usr/bin/env python3
"""Export a human-readable Markdown review of one judged submission.

Renders the system's answer followed by every rubric criterion with its
True/False verdict, the criterion text, the judge's reasoning and evidence,
grouped by Pruefungsstation. Built for legal reviewers who want to see the
solution and the scoring side by side.

Usage:
  python scripts/export_review_md.py <submission-dir-or-scores.json> [more...] [--output FILE]

A submission dir is a directory containing scores.json and the deliverable(s).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from outline_util import UE_ID, index_outline  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a Markdown review of a judged submission.")
    parser.add_argument("targets", nargs="+", type=pathlib.Path, help="Submission dir(s) or scores.json path(s).")
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        help="Output file (only with a single target). Default: <submission-dir>/review.md per target.",
    )
    return parser.parse_args()


def resolve_scores_path(target: pathlib.Path) -> pathlib.Path:
    target = target if target.is_absolute() else REPO_ROOT / target
    if target.is_dir():
        path = target / "scores.json"
    else:
        path = target
    if not path.exists():
        raise SystemExit(f"No scores.json found at {path}")
    return path


def load_rubric(
    task_dir: pathlib.Path, rubric_override: pathlib.Path | None = None
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Return (criteria-by-id, outline nodes or [])."""
    rubric_path = rubric_override or (task_dir / "evals" / "rubric.json")
    if not rubric_path.exists():
        return {}, []
    rubric = json.loads(rubric_path.read_text(encoding="utf-8"))
    index = {c["id"]: c for c in rubric.get("criteria", []) if "id" in c}
    return index, rubric.get("outline") or []


def read_deliverables(submission: pathlib.Path) -> str:
    if submission.is_file():
        return submission.read_text(encoding="utf-8", errors="replace").strip()

    submission_dir = submission
    parts = []
    for path in sorted(submission_dir.glob("*.md")):
        if path.name == "review.md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if len(list(submission_dir.glob("*.md"))) > 1:
            parts.append(f"### `{path.name}`\n\n{text}")
        else:
            parts.append(text)
    return "\n\n".join(parts) if parts else "_(keine Deliverable-Datei gefunden)_"


def run_meta(submission_dir: pathlib.Path) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    # submission_dir = <run>/tasks/<task>/submission -> manifest at parents[2].
    manifest_path = submission_dir.parents[2] / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        meta["harness"] = manifest.get("harness")
    meta_path = submission_dir.parent / "metadata.json"
    if meta_path.exists():
        # Per-task metadata wins where present (e.g. baseline sets harness here).
        meta.update({k: v for k, v in json.loads(meta_path.read_text(encoding="utf-8")).items() if v is not None})
    return meta


def verdict_mark(verdict: str) -> str:
    return {"pass": "✅ TRUE", "fail": "❌ FALSE", "error": "⚠️ ERROR"}.get(verdict, verdict)


def station_of(criterion: dict[str, Any]) -> str:
    path = (criterion.get("analysis_tags") or {}).get("station_path") or []
    return path[0] if path else "Ohne Kategorie"


def criticality_stars(criterion: dict[str, Any]) -> str:
    value = criterion.get("criticality")
    return "★" * value if value in (1, 2, 3) else ""


def render_criterion(
    lines: list[str],
    r: dict[str, Any],
    crit: dict[str, Any],
    votes: int,
    *,
    heading: str | None,
) -> None:
    crit_meta = crit.get("analysis_tags") or {}
    extra = []
    stars = criticality_stars(crit)
    if stars:
        extra.append(stars)
    elif crit.get("criticality") and crit["criticality"] != "must_pass":
        extra.append(str(crit["criticality"]))
    if crit_meta.get("function"):
        extra.append(crit_meta["function"])
    tag = f" _({', '.join(extra)})_" if extra else ""
    title_line = f"{verdict_mark(r['verdict'])} — {r['id']}: {r.get('title', '')}"
    if heading:
        lines.append(f"{heading} {title_line}{tag}")
    else:
        lines.append(f"**{title_line}**{tag}")
    lines.append("")
    if crit.get("match_criteria"):
        lines.append(f"**Kriterium:** {crit['match_criteria']}")
        lines.append("")
    if votes > 1 and r.get("vote_counts"):
        vc = r["vote_counts"]
        lines.append(
            f"**Votes:** {vc.get('pass', 0)} pass / {vc.get('fail', 0)} fail / "
            f"{vc.get('error', 0)} error"
        )
        if r.get("resolution"):
            lines.append(f"**Status:** `{r['resolution']}`")
        lines.append("")
    voting_rounds = r.get("voting_rounds") or []
    vote_groups = (
        [(f"Runde {round_data.get('round', index)}", round_data.get("votes") or [])
         for index, round_data in enumerate(voting_rounds, start=1)]
        if voting_rounds
        else [("Einzelvotes", r.get("votes") or [])]
    )
    for group_label, group_votes in vote_groups:
        if not group_votes:
            continue
        lines.append(f"**{group_label}:**")
        for vote in group_votes:
            judge = vote.get("judge") or {}
            judge_name = judge.get("name") or judge.get("model") or "unknown"
            model = judge.get("model")
            label = f"{judge_name} ({model})" if model and model != judge_name else str(judge_name)
            reasoning = str(vote.get("reasoning") or "").strip()
            suffix = f" — {reasoning}" if reasoning else ""
            lines.append(f"- **{label}:** `{vote.get('verdict', 'error')}`{suffix}")
        lines.append("")
    if r.get("reasoning"):
        lines.append(f"**Begründung des Judge:** {r['reasoning']}")
        lines.append("")
    if r.get("evidence"):
        quotes = "; ".join(f"„{e}“" for e in r["evidence"] if e)
        if quotes:
            lines.append(f"**Belege:** {quotes}")
            lines.append("")


def render_outline_grouped(
    lines: list[str],
    outline: list[dict[str, Any]],
    results: list[dict[str, Any]],
    rubric: dict[str, dict[str, Any]],
    votes: int,
) -> None:
    known = set(index_outline(outline))
    by_node: dict[str, list[dict[str, Any]]] = {}
    unmapped: list[dict[str, Any]] = []
    for r in results:
        oid = (rubric.get(r["id"], {}).get("analysis_tags") or {}).get("outline_id")
        if oid in known:
            by_node.setdefault(oid, []).append(r)
        else:
            unmapped.append(r)

    def subtree_stats(node: dict[str, Any]) -> tuple[int, int]:
        group = by_node.get(node["id"], [])
        n = len(group)
        passed = sum(1 for r in group if r["verdict"] == "pass")
        for child in node.get("children") or []:
            cn, cp = subtree_stats(child)
            n += cn
            passed += cp
        return n, passed

    def render_nodes(nodes: list[dict[str, Any]], depth: int) -> None:
        for node in nodes:
            n, passed = subtree_stats(node)
            if n == 0:
                continue
            label = (
                node["label"]
                if node["id"] == UE_ID or node["id"] == node["label"]
                else f"{node['id']} {node['label']}"
            )
            header = f"{label} — {passed}/{n}"
            if depth == 1:
                lines.append(f"### {header}")
            elif depth == 2:
                lines.append(f"#### {header}")
            else:
                lines.append(f"**{header}**")
            lines.append("")
            for r in by_node.get(node["id"], []):
                render_criterion(lines, r, rubric.get(r["id"], {}), votes, heading=None)
            render_nodes(node.get("children") or [], depth + 1)

    render_nodes(outline, 1)
    if unmapped:
        n_pass = sum(1 for r in unmapped if r["verdict"] == "pass")
        lines.append(f"### Ohne Kategorie — {n_pass}/{len(unmapped)}")
        lines.append("")
        for r in unmapped:
            render_criterion(lines, r, rubric.get(r["id"], {}), votes, heading=None)


def build_markdown(scores_path: pathlib.Path) -> str:
    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    submission = pathlib.Path(scores["submission"])
    submission_dir = submission if submission.is_dir() else submission.parent
    task_dir = pathlib.Path(scores["task"]["path"])
    recorded_rubric = pathlib.Path(scores["rubric"]) if scores.get("rubric") else None
    rubric, outline = load_rubric(task_dir, recorded_rubric)
    meta = run_meta(submission_dir)

    lines: list[str] = []
    lines.append(f"# Review: {scores['task'].get('title', task_dir.name)}")
    lines.append("")
    model = meta.get("model", scores.get("judge_model", "?"))
    harness = meta.get("harness", "?")
    variant = f" · Variante {meta['variant']}" if meta.get("variant") else ""
    votes = scores.get("votes_per_criterion", 1)
    lines.append(f"- **System:** {model} ({harness}{variant})")
    lines.append(
        f"- **Inhalt:** {scores['n_passed']}/{scores['n_criteria']} Kriterien erfüllt "
        f"({scores['criterion_pass_rate']:.0%})"
    )
    weighted = scores.get("criticality_weighted_content_score")
    if weighted:
        lines.append(
            f"- **Inhalt nach Wichtigkeit (diagnostisch):** "
            f"{weighted['points_earned']}/{weighted['points_available']} "
            f"({weighted['pass_rate']:.0%})"
        )
    style = scores.get("style_score")
    if style is not None:
        lines.append(
            f"- **Gutachtenstil:** {style['n_passed']}/{style['n_eligible']} "
            f"stilrelevante Kriterien methodisch erfüllt ({style['pass_rate']:.0%})"
        )
    committee = scores.get("judge_committee") or []
    if committee:
        judges = ", ".join(f"{item['name']} ({item['model']})" for item in committee)
        lines.append(f"- **Judge-Komitee:** {judges}; Mehrheitsentscheidung aus {votes} Votes")
    else:
        lines.append(f"- **Judge:** {scores.get('judge_model', '?')}, {votes} Vote(s) pro Kriterium")
    if scores.get("breakdown_by_station"):
        parts = [
            f"{name} {g['n_passed']}/{g['n_criteria']} ({g['pass_rate']:.0%})"
            for name, g in sorted(scores["breakdown_by_station"].items(), key=lambda x: -x[1]["n_criteria"])
        ]
        lines.append(f"- **Nach Station:** {' · '.join(parts)}")
    # Wichtigkeits-Breakdown aus dem Rubric berechnen, damit auch alte
    # scores.json ohne breakdown_by_criticality ihn bekommen.
    tiers: dict[int, dict[str, int]] = {}
    for r in scores["criteria_results"]:
        value = rubric.get(r["id"], {}).get("criticality")
        if value in (1, 2, 3):
            tier = tiers.setdefault(value, {"n": 0, "passed": 0})
            tier["n"] += 1
            tier["passed"] += 1 if r["verdict"] == "pass" else 0
    if tiers:
        parts = [
            f"{'★' * value} {tiers[value]['passed']}/{tiers[value]['n']} ({tiers[value]['passed'] / tiers[value]['n']:.0%})"
            for value in (3, 2, 1)
            if value in tiers
        ]
        lines.append(f"- **Nach Wichtigkeit:** {' · '.join(parts)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Lösung des Systems")
    lines.append("")
    lines.append(read_deliverables(submission))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Bewertung nach Rubrik")
    lines.append("")

    results = scores["criteria_results"]
    has_outline_tags = outline and any(
        (rubric.get(r["id"], {}).get("analysis_tags") or {}).get("outline_id") for r in results
    )
    if has_outline_tags:
        # Nested grouping along the Musterlösung's own Gliederung.
        render_outline_grouped(lines, outline, results, rubric, votes)
        return "\n".join(lines).rstrip() + "\n"

    # Fallback: group by top-level station, preserving criterion order within station.
    stations: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for r in results:
        st = station_of(rubric.get(r["id"], {}))
        if st not in stations:
            stations[st] = []
            order.append(st)
        stations[st].append(r)

    for st in order:
        group = stations[st]
        n_pass = sum(1 for r in group if r["verdict"] == "pass")
        lines.append(f"### {st} — {n_pass}/{len(group)}")
        lines.append("")
        for r in group:
            render_criterion(lines, r, rubric.get(r["id"], {}), votes, heading="####")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    if args.output and len(args.targets) != 1:
        raise SystemExit("--output only works with a single target.")

    for target in args.targets:
        scores_path = resolve_scores_path(target)
        md = build_markdown(scores_path)
        out = args.output if args.output else scores_path.parent / "review.md"
        out = out if out.is_absolute() else REPO_ROOT / out
        out.write_text(md, encoding="utf-8")
        print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
