#!/usr/bin/env python3
"""Run the case-neutral Gutachtenstil calibration set with a judge committee."""

from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evaluation.run import (  # noqa: E402
    add_judge_metadata,
    aggregate_votes,
    cached_judge_vote,
    load_env_files,
    load_judge_committee,
    make_client,
    style_judge_prompt,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures",
        type=pathlib.Path,
        default=REPO_ROOT / "tests" / "fixtures" / "gutachtenstil_calibration.json",
    )
    parser.add_argument("--judge-committee", type=pathlib.Path, required=True)
    parser.add_argument("--replicates", type=int, default=2)
    parser.add_argument("--cache-dir", type=pathlib.Path, required=True)
    parser.add_argument("--output-json", type=pathlib.Path, required=True)
    parser.add_argument("--output-md", type=pathlib.Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def resolve(path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else REPO_ROOT / path


def effective_verdict(result: dict[str, Any]) -> str:
    if result.get("resolution") == "unresolved":
        return "unresolved"
    return str(result.get("verdict") or "error")


def metric(expected: dict[str, str], actual: dict[str, str]) -> dict[str, Any]:
    shared = sorted(set(expected) & set(actual))
    resolved = [case_id for case_id in shared if actual[case_id] in ("pass", "fail")]
    correct = sum(1 for case_id in resolved if expected[case_id] == actual[case_id])
    false_passes = sum(
        1 for case_id in resolved if expected[case_id] == "fail" and actual[case_id] == "pass"
    )
    false_fails = sum(
        1 for case_id in resolved if expected[case_id] == "pass" and actual[case_id] == "fail"
    )
    return {
        "n_cases": len(shared),
        "n_resolved": len(resolved),
        "n_correct": correct,
        "accuracy": correct / len(resolved) if resolved else 0.0,
        "false_passes": false_passes,
        "false_fails": false_fails,
        "unresolved_or_error": len(shared) - len(resolved),
    }


def agreement(left: dict[str, str], right: dict[str, str]) -> dict[str, Any]:
    shared = sorted(set(left) & set(right))
    comparable = [
        case_id
        for case_id in shared
        if left[case_id] in ("pass", "fail") and right[case_id] in ("pass", "fail")
    ]
    agrees = sum(1 for case_id in comparable if left[case_id] == right[case_id])
    return {
        "n_compared": len(comparable),
        "n_agree": agrees,
        "agreement": agrees / len(comparable) if comparable else 0.0,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Interne Gutachtenstil-Kalibrierung",
        "",
        "Dieses fallneutrale Set ist eine technische Kalibrierung und kein juristisches Expertengold.",
        "Inhaltliche Richtigkeit ist für jedes Beispiel vorgegeben; bewertet wird nur die Darstellungsform.",
        "",
        "## Mehrheit je Replikat",
        "",
        "| Replikat | Richtig | Accuracy | False-Passes | False-Fails | Fehler/ungelöst |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for replicate, result in payload["majority_metrics"].items():
        lines.append(
            f"| {replicate} | {result['n_correct']}/{result['n_resolved']} | "
            f"{result['accuracy']:.1%} | {result['false_passes']} | {result['false_fails']} | "
            f"{result['unresolved_or_error']} |"
        )
    lines.extend(["", "## Einzelmodelle", ""])
    for judge, replicates in payload["judge_metrics"].items():
        for replicate, result in replicates.items():
            lines.append(
                f"- {judge}, {replicate}: {result['n_correct']}/{result['n_resolved']} "
                f"({result['accuracy']:.1%}), FP {result['false_passes']}, "
                f"FF {result['false_fails']}, Fehler {result['unresolved_or_error']}"
            )
    lines.extend(["", "## Wiederholungsstabilität", ""])
    for item in payload["repeatability"]:
        lines.append(
            f"- {item['subject']} ({item['left']} ↔ {item['right']}): "
            f"{item['n_agree']}/{item['n_compared']} ({item['agreement']:.1%})"
        )
    lines.extend(["", "## Fehlentscheidungen der Mehrheit", ""])
    wrong = [
        item
        for item in payload["case_results"]
        if any(
            verdict != item["expected_verdict"]
            for verdict in item["majority_by_replicate"].values()
            if verdict in ("pass", "fail")
        )
    ]
    if not wrong:
        lines.append("Keine.")
    for item in wrong:
        lines.append(
            f"- `{item['id']}`: erwartet `{item['expected_verdict']}`, "
            + ", ".join(
                f"{replicate} `{verdict}`"
                for replicate, verdict in item["majority_by_replicate"].items()
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    fixtures_path = resolve(args.fixtures)
    committee_path = resolve(args.judge_committee)
    cache_dir = resolve(args.cache_dir)
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    cases = fixtures.get("cases") or []
    specs = load_judge_committee(committee_path)
    if args.replicates < 2:
        raise SystemExit("--replicates must be at least 2 for stability measurement.")
    if args.dry_run:
        print(f"Cases: {len(cases)}")
        print(f"Judges: {', '.join(spec.name for spec in specs)}")
        print(f"Replicates: {args.replicates}")
        print(f"Planned calls: {len(cases) * len(specs) * args.replicates}")
        return 0

    load_env_files(REPO_ROOT)
    clients = [make_client(spec.api_base) for spec in specs]
    votes: dict[tuple[str, int, str], dict[str, Any]] = {}

    def run_case(spec_index: int, replicate: int, case: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        spec = specs[spec_index]
        client, use_chat = clients[spec_index]
        criterion = {
            "id": case["id"],
            "title": case["criterion_title"],
            "match_criteria": case["match_criteria"],
        }
        prompt = style_judge_prompt(
            {"title": case["task_title"], "instructions": "Bearbeiten Sie den Fall im Gutachtenstil."},
            case["answer"],
            criterion,
            {"evidence": case.get("content_evidence") or []},
        )
        vote = cached_judge_vote(
            cache_dir=cache_dir,
            phase=f"style-calibration-r{replicate}",
            client=client,
            spec=spec,
            prompt=prompt,
            criterion=criterion,
            use_chat=use_chat,
        )
        return case["id"], add_judge_metadata(vote, spec)

    for spec_index, spec in enumerate(specs):
        for replicate in range(1, args.replicates + 1):
            with ThreadPoolExecutor(max_workers=max(1, spec.parallel or 4)) as pool:
                for case_id, vote in pool.map(
                    lambda case: run_case(spec_index, replicate, case), cases
                ):
                    votes[(case_id, replicate, spec.name)] = vote

    expected = {case["id"]: case["expected_verdict"] for case in cases}
    majority_by_replicate: dict[str, dict[str, str]] = {}
    judge_by_replicate: dict[str, dict[str, dict[str, str]]] = {
        spec.name: {} for spec in specs
    }
    case_results: list[dict[str, Any]] = []
    for replicate in range(1, args.replicates + 1):
        label = f"r{replicate}"
        majority_by_replicate[label] = {}
        for spec in specs:
            judge_by_replicate[spec.name][label] = {}
        for case in cases:
            case_votes = [votes[(case["id"], replicate, spec.name)] for spec in specs]
            aggregate = aggregate_votes(
                {"id": case["id"], "title": case["criterion_title"]}, case_votes
            )
            majority_by_replicate[label][case["id"]] = effective_verdict(aggregate)
            for spec in specs:
                judge_by_replicate[spec.name][label][case["id"]] = votes[
                    (case["id"], replicate, spec.name)
                ]["verdict"]

    for case in cases:
        case_results.append(
            {
                "id": case["id"],
                "area": case["area"],
                "kind": case["kind"],
                "expected_verdict": case["expected_verdict"],
                "majority_by_replicate": {
                    label: values[case["id"]] for label, values in majority_by_replicate.items()
                },
                "votes": {
                    label: {
                        spec.name: votes[(case["id"], int(label[1:]), spec.name)]["verdict"]
                        for spec in specs
                    }
                    for label in majority_by_replicate
                },
            }
        )

    majority_metrics = {
        label: metric(expected, values) for label, values in majority_by_replicate.items()
    }
    judge_metrics = {
        judge: {label: metric(expected, values) for label, values in replicates.items()}
        for judge, replicates in judge_by_replicate.items()
    }
    repeatability: list[dict[str, Any]] = []
    for left, right in itertools.combinations(sorted(majority_by_replicate), 2):
        repeatability.append(
            {
                "subject": "committee-majority",
                "left": left,
                "right": right,
                **agreement(majority_by_replicate[left], majority_by_replicate[right]),
            }
        )
    for judge, replicates in judge_by_replicate.items():
        for left, right in itertools.combinations(sorted(replicates), 2):
            repeatability.append(
                {
                    "subject": judge,
                    "left": left,
                    "right": right,
                    **agreement(replicates[left], replicates[right]),
                }
            )

    payload = {
        "schema_version": "0.1",
        "purpose": fixtures["purpose"],
        "fixtures": str(fixtures_path),
        "committee": [spec.as_dict() for spec in specs],
        "majority_metrics": majority_metrics,
        "judge_metrics": judge_metrics,
        "repeatability": repeatability,
        "case_results": case_results,
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
