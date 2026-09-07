#!/usr/bin/env python3
"""Build the de-core-45 results CSV out of the per-task scores.json files.

One row per (arm, case). Every number in the row is read from that case's
scores.json -- nothing is recomputed from votes, nothing is carried over from a
previous CSV -- so a row can always be traced back to the file it came from via
(task_id, content_passed, content_criteria).

Arm metadata (model id, reasoning effort, agent vs. baseline) comes from each
run's manifest.json, and the judging pass from the score files themselves, so
adding an arm means passing another run directory and nothing else.

A case with no submission still gets a row, with status "keine Abgabe" and empty
score columns: the de-core-45 DeepSeek agent arm lost one constitutional-law case
to the provider's content filter on all 11 attempts, and a blank row cannot be
misread as a 0% result the way a zero would be.

    python scripts/build_study_results_csv.py \
        runs/agent-gpt-5.6-sol-high/20260730T221733Z ... \
        --output runs/de-core-45-final.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

COLUMNS = [
    "task_id", "case", "rechtsgebiet", "teilgebiet", "model", "methode",
    "model_id", "reasoning", "judging", "committee", "status",
    "content_passed", "content_criteria", "content_rate", "tiebreaks",
    "style_passed", "style_eligible", "style_rate",
]

# Display names for the model families in this study. A model outside the map
# keeps its bare id rather than being silently folded into a neighbouring family.
MODEL_LABELS = {
    "gpt-5.6-sol": "Sol",
    "gpt-5.6-terra": "Terra",
    "deepseek-v4-pro": "DeepSeek",
}
RECHTSGEBIET_LABELS = {
    "zivilrecht": "Zivilrecht",
    "strafrecht": "Strafrecht",
    "oeffentliches-recht": "Öffentliches Recht",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Study results CSV from scores.json files.")
    parser.add_argument("run_dirs", nargs="+", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--scores-name", default="scores.json",
                        help="Score file to read under tasks/<task>/. Default scores.json.")
    return parser.parse_args()


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def model_label(model_id: str) -> str:
    bare = model_id.split("/")[-1]
    return MODEL_LABELS.get(bare, bare)


def arm_metadata(run_dir: pathlib.Path) -> dict[str, str]:
    manifest = load(run_dir / "manifest.json")
    model_id = manifest["model"]
    baseline = manifest.get("harness") == "baseline-single-call"
    reasoning = manifest.get("variant") or manifest.get("reasoning_effort") or "-"
    return {
        "model": model_label(model_id),
        "methode": "Baseline" if baseline else "Agent",
        # The two harnesses record the model id in their own notation; the CSV
        # keeps whichever the run actually used rather than normalising it away.
        "model_id": model_id,
        "reasoning": reasoning,
    }


def task_fields(task_id: str) -> dict[str, str]:
    parts = task_id.split("/")
    rechtsgebiet = parts[1] if len(parts) > 1 else ""
    return {
        "task_id": task_id,
        "case": parts[-1],
        "rechtsgebiet": RECHTSGEBIET_LABELS.get(rechtsgebiet, rechtsgebiet),
        "teilgebiet": parts[2] if len(parts) > 2 else "",
    }


def rate(passed: int, total: int) -> str:
    """Four decimals with trailing zeros trimmed, as the published CSV carries them."""
    if not total:
        return ""
    text = f"{round(passed / total, 4):g}"
    return text if "." in text else f"{text}.0"


def task_relpath(task_dir: pathlib.Path) -> str:
    """Path under tasks/, e.g. de/zivilrecht/schuldrecht/<case>.

    Taken relative to the tasks/ root rather than by counting segments from the
    end: a handful of cases sit one level deeper (verwaltungsrecht groups its
    Anfechtungsklage and Fortsetzungsfeststellungsklage cases into subfolders),
    and a fixed segment count silently drops the language prefix on those.
    """
    parts = task_dir.parts
    if "tasks" in parts:
        return "/".join(parts[parts.index("tasks") + 1:])
    return "/".join(parts[-4:])


def main() -> int:
    args = parse_args()
    rows: list[dict[str, str]] = []
    missing: list[str] = []

    for run_dir in args.run_dirs:
        run_dir = run_dir if run_dir.is_absolute() else REPO_ROOT / run_dir
        arm = arm_metadata(run_dir)
        for metadata_path in sorted((run_dir / "tasks").glob("*/metadata.json")):
            task_root = metadata_path.parent
            metadata = load(metadata_path)
            task_id = task_relpath(pathlib.Path(metadata["source_task_dir"]))
            row = {**task_fields(task_id), **arm}

            score_path = task_root / args.scores_name
            if not score_path.exists():
                # No score file and no deliverable is the content-filter case;
                # no score file with a deliverable is a gap worth shouting about.
                if not metadata.get("missing_deliverables"):
                    missing.append(f"{run_dir.name}/{task_root.name}")
                rows.append({**row, "judging": "", "committee": "", "status": "keine Abgabe",
                             **{c: "" for c in COLUMNS[11:]}})
                continue

            scores = load(score_path)
            content = scores["content_score"]
            style = scores.get("style_score") or {}
            rows.append({
                **row,
                "judging": scores.get("judging_pass", ""),
                "committee": scores.get("committee_resolution", ""),
                "status": "ok",
                "content_passed": content["n_passed"],
                "content_criteria": content["n_criteria"],
                "content_rate": rate(content["n_passed"], content["n_criteria"]),
                "tiebreaks": scores.get("n_tiebreaks", ""),
                "style_passed": style.get("n_passed", ""),
                "style_eligible": style.get("n_eligible", ""),
                "style_rate": rate(style.get("n_passed", 0), style.get("n_eligible", 0)),
            })

            unresolved = content.get("n_unresolved", 0)
            if unresolved:
                print(f"  {run_dir.name}/{task_root.name}: {unresolved} unresolved criteria",
                      file=sys.stderr)

    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {output}")
    if missing:
        print(f"WARNING: {len(missing)} case(s) had a submission but no {args.scores_name}:",
              file=sys.stderr)
        for name in missing:
            print(f"  {name}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
