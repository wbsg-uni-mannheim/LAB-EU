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
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


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


def load_rubric_index(task_dir: pathlib.Path) -> dict[str, dict[str, Any]]:
    rubric_path = task_dir / "evals" / "rubric.json"
    if not rubric_path.exists():
        return {}
    rubric = json.loads(rubric_path.read_text(encoding="utf-8"))
    return {c["id"]: c for c in rubric.get("criteria", []) if "id" in c}


def read_deliverables(submission_dir: pathlib.Path) -> str:
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


def build_markdown(scores_path: pathlib.Path) -> str:
    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    submission_dir = scores_path.parent
    task_dir = pathlib.Path(scores["task"]["path"])
    rubric = load_rubric_index(task_dir)
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
        f"- **Ergebnis:** {scores['n_passed']}/{scores['n_criteria']} Kriterien erfüllt "
        f"({scores['criterion_pass_rate']:.0%})"
    )
    lines.append(f"- **Judge:** {scores.get('judge_model', '?')}, {votes} Vote(s) pro Kriterium")
    if scores.get("breakdown_by_station"):
        parts = [
            f"{name} {g['n_passed']}/{g['n_criteria']} ({g['pass_rate']:.0%})"
            for name, g in sorted(scores["breakdown_by_station"].items(), key=lambda x: -x[1]["n_criteria"])
        ]
        lines.append(f"- **Nach Station:** {' · '.join(parts)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Lösung des Systems")
    lines.append("")
    lines.append(read_deliverables(submission_dir))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Bewertung nach Rubrik")
    lines.append("")

    # Group results by top-level station, preserving criterion order within station.
    results = scores["criteria_results"]
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
            crit = rubric.get(r["id"], {})
            crit_meta = crit.get("analysis_tags") or {}
            extra = []
            if crit.get("criticality") and crit["criticality"] != "must_pass":
                extra.append(crit["criticality"])
            if crit_meta.get("function"):
                extra.append(crit_meta["function"])
            tag = f" _({', '.join(extra)})_" if extra else ""
            lines.append(f"#### {verdict_mark(r['verdict'])} — {r['id']}: {r.get('title', '')}{tag}")
            lines.append("")
            if crit.get("match_criteria"):
                lines.append(f"**Kriterium:** {crit['match_criteria']}")
                lines.append("")
            if votes > 1 and r.get("vote_counts"):
                vc = r["vote_counts"]
                lines.append(f"**Votes:** {vc.get('pass', 0)} pass / {vc.get('fail', 0)} fail")
                lines.append("")
            if r.get("reasoning"):
                lines.append(f"**Begründung des Judge:** {r['reasoning']}")
                lines.append("")
            if r.get("evidence"):
                quotes = "; ".join(f"„{e}“" for e in r["evidence"] if e)
                if quotes:
                    lines.append(f"**Belege:** {quotes}")
                    lines.append("")
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
