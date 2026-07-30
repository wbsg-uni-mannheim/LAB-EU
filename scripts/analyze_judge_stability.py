#!/usr/bin/env python3
"""Measure committee and repeated-run stability for rubric score files."""

from __future__ import annotations

import argparse
import itertools
import json
import pathlib
from collections import defaultdict
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scores",
        action="append",
        required=True,
        metavar="SUBMISSION:REPLICATE=PATH",
        help="Score file for one submission and independent replicate; repeat as needed.",
    )
    parser.add_argument("--output-json", type=pathlib.Path, required=True)
    parser.add_argument("--output-md", type=pathlib.Path, required=True)
    return parser.parse_args()


def resolve(path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else REPO_ROOT / path


def parse_specs(values: list[str]) -> dict[str, dict[str, pathlib.Path]]:
    parsed: dict[str, dict[str, pathlib.Path]] = defaultdict(dict)
    for value in values:
        label, separator, raw_path = value.partition("=")
        submission, colon, replicate = label.partition(":")
        if not separator or not colon or not submission or not replicate or not raw_path:
            raise SystemExit(f"Invalid --scores value {value!r}.")
        if replicate in parsed[submission]:
            raise SystemExit(f"Duplicate score label {submission}:{replicate}.")
        parsed[submission][replicate] = resolve(pathlib.Path(raw_path))
    return dict(parsed)


def load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def results_by_id(scores: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in scores.get("criteria_results") or []}


def vote_by_judge(result: dict[str, Any]) -> dict[str, str]:
    votes: dict[str, str] = {}
    for vote in result.get("votes") or []:
        judge = vote.get("judge") or {}
        name = str(judge.get("name") or judge.get("model") or "unknown")
        votes[name] = str(vote.get("verdict") or "error")
    return votes


def effective_verdict(result: dict[str, Any]) -> str:
    if result.get("resolution") == "unresolved":
        return "unresolved"
    counts = result.get("vote_counts") or {}
    if counts.get("error", 0) and counts.get("pass", 0) < 2 and counts.get("fail", 0) < 2:
        return "unresolved"
    return str(result.get("verdict") or "error")


def agreement(left: dict[str, str], right: dict[str, str]) -> dict[str, Any]:
    shared = sorted(set(left) & set(right))
    comparable = [key for key in shared if left[key] != "error" and right[key] != "error"]
    matches = sum(1 for key in comparable if left[key] == right[key])
    return {
        "n_shared": len(shared),
        "n_compared": len(comparable),
        "n_agree": matches,
        "agreement": matches / len(comparable) if comparable else 0.0,
    }


def analyze_submission(replicates: dict[str, pathlib.Path]) -> dict[str, Any]:
    loaded = {name: load(path) for name, path in replicates.items()}
    indexed = {name: results_by_id(scores) for name, scores in loaded.items()}
    summaries = {
        name: {
            "scores_path": str(replicates[name]),
            "content_score": scores.get("content_score"),
            "style_score": scores.get("style_score"),
            "mean_judge_agreement": scores.get("mean_judge_agreement"),
            "n_unanimous": scores.get("n_unanimous"),
            "content_votes_by_judge": scores.get("content_votes_by_judge"),
            "style_votes_by_judge": scores.get("style_votes_by_judge"),
        }
        for name, scores in loaded.items()
    }

    majority_pairs: list[dict[str, Any]] = []
    model_pairs: list[dict[str, Any]] = []
    disagreement_ids: set[str] = set()

    for replicate, results in indexed.items():
        for criterion_id, result in results.items():
            counts = result.get("vote_counts") or {}
            if counts.get("error", 0) or max(counts.get("pass", 0), counts.get("fail", 0)) < 3:
                disagreement_ids.add(criterion_id)

    for left_name, right_name in itertools.combinations(sorted(indexed), 2):
        left = indexed[left_name]
        right = indexed[right_name]
        left_majority = {key: effective_verdict(value) for key, value in left.items()}
        right_majority = {key: effective_verdict(value) for key, value in right.items()}
        pair = agreement(left_majority, right_majority)
        majority_pairs.append({"left": left_name, "right": right_name, **pair})
        for criterion_id in set(left_majority) & set(right_majority):
            if left_majority[criterion_id] != right_majority[criterion_id]:
                disagreement_ids.add(criterion_id)

        judges = sorted(
            {
                judge
                for result in list(left.values()) + list(right.values())
                for judge in vote_by_judge(result)
            }
        )
        for judge in judges:
            left_votes = {
                key: vote_by_judge(result).get(judge, "error") for key, result in left.items()
            }
            right_votes = {
                key: vote_by_judge(result).get(judge, "error") for key, result in right.items()
            }
            pair = agreement(left_votes, right_votes)
            model_pairs.append(
                {"judge": judge, "left": left_name, "right": right_name, **pair}
            )
            for criterion_id in set(left_votes) & set(right_votes):
                if (
                    left_votes[criterion_id] != "error"
                    and right_votes[criterion_id] != "error"
                    and left_votes[criterion_id] != right_votes[criterion_id]
                ):
                    disagreement_ids.add(criterion_id)

    return {
        "replicates": summaries,
        "majority_repeatability": majority_pairs,
        "model_repeatability": model_pairs,
        "disagreement_criterion_ids": sorted(disagreement_ids),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Judge-Stabilitätsanalyse",
        "",
        "Unabhängige Replikate verwenden getrennte Vote-Caches. Fehlerstimmen werden nicht als fachliche Urteile behandelt.",
    ]
    for submission, result in payload["submissions"].items():
        lines.extend(["", f"## {submission}", "", "### Replikate", ""])
        lines.extend(
            [
                "| Lauf | Inhalt | Stil | Mittlere Modellübereinstimmung | Einstimmig |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for name, summary in result["replicates"].items():
            content = summary.get("content_score") or {}
            style = summary.get("style_score") or {}
            lines.append(
                f"| {name} | {content.get('n_passed', 0)}/{content.get('n_criteria', 0)} "
                f"({content.get('pass_rate', 0):.1%}) | {style.get('n_passed', 0)}/"
                f"{style.get('n_eligible', 0)} ({style.get('pass_rate', 0):.1%}) | "
                f"{summary.get('mean_judge_agreement', 0):.1%} | "
                f"{summary.get('n_unanimous', 0)}/{content.get('n_criteria', 0)} |"
            )
        lines.extend(["", "### Mehrheitsstabilität", ""])
        for pair in result["majority_repeatability"]:
            lines.append(
                f"- {pair['left']} ↔ {pair['right']}: {pair['n_agree']}/{pair['n_compared']} "
                f"({pair['agreement']:.1%})"
            )
        lines.extend(["", "### Modellwiederholbarkeit", ""])
        for pair in result["model_repeatability"]:
            lines.append(
                f"- {pair['judge']} ({pair['left']} ↔ {pair['right']}): "
                f"{pair['n_agree']}/{pair['n_compared']} ({pair['agreement']:.1%})"
            )
        ids = result["disagreement_criterion_ids"]
        lines.extend(
            [
                "",
                f"### Kriterien für den gezielten dritten Lauf ({len(ids)})",
                "",
                ", ".join(f"`{criterion_id}`" for criterion_id in ids) or "Keine.",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    specs = parse_specs(args.scores)
    payload = {
        "schema_version": "0.1",
        "submissions": {
            submission: analyze_submission(replicates)
            for submission, replicates in specs.items()
        },
    }
    output_json = resolve(args.output_json)
    output_md = resolve(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"Wrote {output_json}")
    print(f"Wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
