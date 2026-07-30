#!/usr/bin/env python3
"""Compare judged scores with external expert labels without modifying a rubric."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=pathlib.Path, required=True)
    parser.add_argument(
        "--scores",
        action="append",
        required=True,
        metavar="SUBMISSION_ID=PATH",
        help="Scores JSON mapped to a submission id from the gold file; repeat as needed.",
    )
    parser.add_argument("--output-json", type=pathlib.Path)
    parser.add_argument("--output-md", type=pathlib.Path)
    return parser.parse_args()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else REPO_ROOT / path


def parse_score_mapping(values: list[str]) -> dict[str, pathlib.Path]:
    mapping: dict[str, pathlib.Path] = {}
    for value in values:
        submission_id, separator, raw_path = value.partition("=")
        if not separator or not submission_id or not raw_path:
            raise SystemExit(f"Invalid --scores value {value!r}; expected SUBMISSION_ID=PATH.")
        if submission_id in mapping:
            raise SystemExit(f"Duplicate --scores submission id {submission_id!r}.")
        mapping[submission_id] = resolve(pathlib.Path(raw_path))
    return mapping


def compare_submission(
    submission_id: str, gold_submission: dict[str, Any], scores: dict[str, Any]
) -> dict[str, Any]:
    actual_by_id = {item["id"]: item for item in scores.get("criteria_results") or []}
    comparisons: list[dict[str, Any]] = []
    for label in gold_submission.get("labels") or []:
        criterion_id = label["criterion_id"]
        actual = actual_by_id.get(criterion_id)
        actual_verdict = actual.get("verdict") if actual else "missing"
        vote_counts = (actual or {}).get("vote_counts") or {}
        if (
            vote_counts.get("error", 0) > 0
            and vote_counts.get("pass", 0) < 2
            and vote_counts.get("fail", 0) < 2
        ):
            actual_verdict = "unresolved"
        expected = label["expected_verdict"]
        comparisons.append(
            {
                **label,
                "actual_verdict": actual_verdict,
                "correct": actual_verdict == expected,
                "error_type": (
                    "false_pass"
                    if expected == "fail" and actual_verdict == "pass"
                    else "false_fail"
                    if expected == "pass" and actual_verdict == "fail"
                    else "missing"
                    if actual_verdict == "missing"
                    else "unresolved"
                    if actual_verdict == "unresolved"
                    else None
                ),
            }
        )

    n_labels = len(comparisons)
    resolved = [item for item in comparisons if item["actual_verdict"] in ("pass", "fail")]
    n_resolved = len(resolved)
    n_correct = sum(1 for item in resolved if item["correct"])
    return {
        "submission_id": submission_id,
        "scores_path": scores.get("submission"),
        "n_labels": n_labels,
        "n_resolved": n_resolved,
        "n_correct": n_correct,
        "accuracy": n_correct / n_resolved if n_resolved else 0.0,
        "false_passes": sum(1 for item in comparisons if item["error_type"] == "false_pass"),
        "false_fails": sum(1 for item in comparisons if item["error_type"] == "false_fail"),
        "missing": sum(1 for item in comparisons if item["error_type"] == "missing"),
        "unresolved": sum(1 for item in comparisons if item["error_type"] == "unresolved"),
        "comparisons": comparisons,
        "excluded_labels": gold_submission.get("excluded_labels") or [],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Judge-Übereinstimmung mit dem externen Professorinnenreview",
        "",
        "Das Professorinnenfeedback dient ausschließlich als externes Testset. Es wurde nicht zur Erzeugung oder Kalibrierung der Rubrik verwendet.",
        "",
        "| Antwort | Übereinstimmung | False-Passes | False-Fails | Ungelöst | Fehlende IDs |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for result in payload["results"]:
        lines.append(
            f"| {result['submission_id']} | {result['n_correct']}/{result['n_resolved']} "
            f"({result['accuracy']:.1%}) | {result['false_passes']} | "
            f"{result['false_fails']} | {result['unresolved']} | {result['missing']} |"
        )
    for result in payload["results"]:
        lines.extend(["", f"## {result['submission_id']}", ""])
        for item in result["comparisons"]:
            mark = "✅" if item["correct"] else "❌"
            lines.append(
                f"- {mark} `{item['criterion_id']}`: erwartet `{item['expected_verdict']}`, "
                f"erhalten `{item['actual_verdict']}` — {item['reason']}"
            )
        if result["excluded_labels"]:
            lines.extend(["", "Nicht in die Kennzahl aufgenommen:", ""])
            for item in result["excluded_labels"]:
                lines.append(f"- `{item['criterion_id']}`: {item['reason']}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    gold_path = resolve(args.gold)
    gold = load_json(gold_path)
    score_mapping = parse_score_mapping(args.scores)
    gold_submissions = gold.get("submissions") or {}
    unknown = sorted(set(score_mapping) - set(gold_submissions))
    if unknown:
        raise SystemExit(f"Submission ids not found in gold file: {', '.join(unknown)}")

    results = [
        compare_submission(submission_id, gold_submissions[submission_id], load_json(path))
        for submission_id, path in score_mapping.items()
    ]
    payload = {
        "schema_version": "0.1",
        "gold_path": str(gold_path),
        "contamination_boundary": "external_evaluation_only",
        "results": results,
    }
    rendered = render_markdown(payload)
    if args.output_json:
        output_json = resolve(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {output_json}")
    if args.output_md:
        output_md = resolve(args.output_md)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(rendered, encoding="utf-8")
        print(f"Wrote {output_md}")
    if not args.output_json and not args.output_md:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
