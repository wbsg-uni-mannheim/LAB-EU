#!/usr/bin/env python3
"""Calibrate a rubric with one positive solution and three negative mutants per criterion."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evaluation.run import (  # noqa: E402
    JudgeSpec,
    add_judge_metadata,
    api_key_env_for,
    cached_judge_vote,
    finalize_committee_rounds,
    judge_prompt,
    load_judge_committee,
    make_client,
    needs_committee_recheck,
)
from scripts.generate_rubric import (  # noqa: E402
    DEFAULT_MODEL,
    MAX_FILE_CHARS,
    MAX_TOTAL_CHARS,
    api_call,
    collect_file_bundle,
    discover_solution_files,
    load_env_files,
    load_task,
    make_client as make_generator_client,
    task_bundle_json,
)


MUTANT_TYPES = ("bare_result", "wrong_scope", "material_error")
DEFAULT_COMMITTEE = REPO_ROOT / "configs" / "judge-committee-rubric-calibration.json"
PROMPT_DIR = REPO_ROOT / "prompts" / "rubric_generation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_dir", type=pathlib.Path)
    parser.add_argument("--rubric", type=pathlib.Path, default=None)
    parser.add_argument(
        "--criterion-id",
        action="append",
        default=[],
        help="Calibrate only this criterion ID; repeat to select multiple criteria.",
    )
    parser.add_argument("--solution", action="append", type=pathlib.Path)
    parser.add_argument("--committee", type=pathlib.Path, default=DEFAULT_COMMITTEE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--reasoning-effort", default="high")
    parser.add_argument("--chunk-size", type=int, default=8)
    parser.add_argument("--parallel", type=int, default=8)
    parser.add_argument("--error-retries", type=int, default=1)
    parser.add_argument(
        "--mutants-from",
        type=pathlib.Path,
        default=None,
        help=(
            "Reuse and freeze the mutants from a previous calibration JSON instead of "
            "generating new ones. Judge prompts are still evaluated anew."
        ),
    )
    parser.add_argument("--output", type=pathlib.Path, default=None)
    parser.add_argument("--cache-dir", type=pathlib.Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def chunks(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    size = max(1, size)
    return [items[index : index + size] for index in range(0, len(items), size)]


def validate_mutants(
    raw_mutants: list[dict[str, Any]], criteria: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    expected_ids = {str(criterion["id"]) for criterion in criteria}
    criteria_by_id = {str(criterion["id"]): criterion for criterion in criteria}
    seen: set[tuple[str, str]] = set()
    mutants: list[dict[str, Any]] = []
    for raw in raw_mutants:
        criterion_id = str(raw.get("criterion_id", ""))
        mutant_type = str(raw.get("type", ""))
        applicable = raw.get("applicable", True) is not False
        function = str(
            (criteria_by_id.get(criterion_id, {}).get("analysis_tags") or {}).get(
                "function", ""
            )
        )
        applicability_override = None
        if applicable and mutant_type == "bare_result" and function == "conclusion":
            applicable = False
            applicability_override = (
                "bare_result is not a negative test for a conclusion-only criterion"
            )
        elif applicable and mutant_type == "wrong_scope" and function == "rule_statement":
            applicable = False
            applicability_override = (
                "wrong_scope is not a negative test for a transferable abstract rule statement"
            )
        answer = str(raw.get("answer", "")).strip()
        why = str(raw.get("why_should_fail", "")).strip()
        key = (criterion_id, mutant_type)
        if criterion_id not in expected_ids:
            raise ValueError(f"Unknown mutant criterion_id: {criterion_id!r}")
        if mutant_type not in MUTANT_TYPES:
            raise ValueError(f"Unknown mutant type for {criterion_id}: {mutant_type!r}")
        if key in seen:
            raise ValueError(f"Duplicate mutant: {criterion_id}/{mutant_type}")
        if not why or (applicable and not answer):
            raise ValueError(f"Empty applicable mutant answer or rationale: {criterion_id}/{mutant_type}")
        seen.add(key)
        mutants.append(
            {
                "id": f"{criterion_id}__{mutant_type}",
                "criterion_id": criterion_id,
                "type": mutant_type,
                "applicable": applicable,
                "applicability_override": applicability_override,
                "answer": answer,
                "why_should_fail": why,
            }
        )

    expected = {(criterion_id, mutant_type) for criterion_id in expected_ids for mutant_type in MUTANT_TYPES}
    missing = sorted(expected - seen)
    if missing:
        rendered = ", ".join(f"{criterion_id}/{mutant_type}" for criterion_id, mutant_type in missing)
        raise ValueError(f"Missing mutants: {rendered}")
    return sorted(mutants, key=lambda item: (item["criterion_id"], MUTANT_TYPES.index(item["type"])))


def generate_mutants(
    *,
    task_dir: pathlib.Path,
    task: dict[str, Any],
    criteria: list[dict[str, Any]],
    solution_files: list[pathlib.Path],
    model: str,
    reasoning_effort: str | None,
    chunk_size: int,
    cache_dir: pathlib.Path | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    files, warnings = collect_file_bundle(
        task_dir, solution_files, MAX_FILE_CHARS, MAX_TOTAL_CHARS
    )
    bundle = json.loads(task_bundle_json(task_dir, task, files))
    system = (PROMPT_DIR / "generate_negative_mutants.system.txt").read_text(encoding="utf-8")
    instruction = (PROMPT_DIR / "generate_negative_mutants.user.txt").read_text(encoding="utf-8")
    client = make_generator_client("https://api.openai.com/v1")
    all_mutants: list[dict[str, Any]] = []
    usage: list[dict[str, Any]] = []
    for chunk_number, criterion_chunk in enumerate(chunks(criteria, chunk_size), start=1):
        payload = {
            "task_bundle": bundle,
            "criteria": [
                {
                    "id": criterion["id"],
                    "title": criterion["title"],
                    "match_criteria": criterion["match_criteria"],
                    "criticality": criterion.get("criticality"),
                }
                for criterion in criterion_chunk
            ],
        }
        parsed, response = api_call(
            client=client,
            model=model,
            system=system,
            user=instruction + "\n\nTASK/RUBRIC DATA JSON:\n" + json.dumps(payload, ensure_ascii=False, indent=2),
            required_keys={"mutants"},
            reasoning_effort=reasoning_effort,
            label=f"negative-mutants/chunk-{chunk_number}",
            cache_dir=cache_dir,
        )
        all_mutants.extend(validate_mutants(parsed.get("mutants") or [], criterion_chunk))
        usage.append(response.get("usage") or {})
    if warnings:
        usage.append({"input_warnings": warnings})
    return all_mutants, usage


def run_committee_cases(
    *,
    task: dict[str, Any],
    task_dir: pathlib.Path,
    cases: list[dict[str, Any]],
    specs: list[JudgeSpec],
    parallel: int,
    error_retries: int,
    cache_dir: pathlib.Path | None,
) -> list[dict[str, Any]]:
    clients = [make_client(spec.api_base) for spec in specs]

    def run_jobs(
        jobs: list[tuple[int, int]], phase: str
    ) -> list[list[dict[str, Any]]]:
        collected: list[list[dict[str, Any]]] = [[] for _ in cases]
        for spec_index, spec in enumerate(specs):
            spec_jobs = [job for job in jobs if job[1] == spec_index]
            if not spec_jobs:
                continue
            workers = spec.parallel or parallel

            def run(job: tuple[int, int]) -> tuple[int, dict[str, Any]]:
                case_index, current_spec_index = job
                case = cases[case_index]
                current_spec = specs[current_spec_index]
                client, use_chat = clients[current_spec_index]
                vote = cached_judge_vote(
                    cache_dir=cache_dir,
                    phase=phase,
                    client=client,
                    spec=current_spec,
                    prompt=judge_prompt(
                        task,
                        task_dir,
                        str(case["answer"]),
                        case["criterion"],
                    ),
                    criterion=case["criterion"],
                    use_chat=use_chat,
                )
                return case_index, add_judge_metadata(vote, current_spec)

            with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
                for case_index, vote in pool.map(run, spec_jobs):
                    collected[case_index].append(vote)
        return collected

    def retry_errors(
        current: list[list[dict[str, Any]]], case_indices: list[int], phase_prefix: str
    ) -> list[list[dict[str, Any]]]:
        for attempt in range(1, max(0, error_retries) + 1):
            retry_jobs: list[tuple[int, int]] = []
            for case_index in case_indices:
                by_name = {
                    str((vote.get("judge") or {}).get("name")): vote
                    for vote in current[case_index]
                }
                for spec_index, spec in enumerate(specs):
                    if by_name.get(spec.name, {}).get("verdict") == "error":
                        retry_jobs.append((case_index, spec_index))
            if not retry_jobs:
                break
            retried = run_jobs(retry_jobs, f"{phase_prefix}-error-retry-{attempt}")
            for case_index in case_indices:
                replacement_by_name = {
                    str((vote.get("judge") or {}).get("name")): vote
                    for vote in retried[case_index]
                    if vote.get("verdict") != "error"
                }
                current[case_index] = [
                    replacement_by_name.get(str((vote.get("judge") or {}).get("name")), vote)
                    for vote in current[case_index]
                ]
        return current

    all_indices = list(range(len(cases)))
    first = retry_errors(
        run_jobs(
            [
                (case_index, spec_index)
                for case_index in all_indices
                for spec_index in range(len(specs))
            ],
            "negative-calibration-r1",
        ),
        all_indices,
        "negative-calibration-r1",
    )
    conflict_indices = [
        index for index, votes in enumerate(first) if needs_committee_recheck(votes)
    ]
    second: list[list[dict[str, Any]]] = [[] for _ in cases]
    if conflict_indices:
        second = retry_errors(
            run_jobs(
                [
                    (case_index, spec_index)
                    for case_index in conflict_indices
                    for spec_index in range(len(specs))
                ],
                "negative-calibration-r2",
            ),
            conflict_indices,
            "negative-calibration-r2",
        )

    results: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        result = finalize_committee_rounds(
            case["criterion"], first[index], second[index] or None
        )
        results.append(
            {
                "case_id": case["id"],
                "criterion_id": case["criterion"]["id"],
                "kind": case["kind"],
                "expected_verdict": case["expected_verdict"],
                "actual_verdict": result["verdict"],
                "resolution": result["resolution"],
                "correct": (
                    result["verdict"] == case["expected_verdict"]
                    and result["resolution"] in {"stable", "stable_with_dissent"}
                ),
                "vote_counts": result["vote_counts"],
                "voting_rounds": result.get("voting_rounds"),
                "reasoning": result.get("reasoning"),
                "evidence": result.get("evidence"),
            }
        )
    return results


def build_metrics(
    results: list[dict[str, Any]],
    criteria_by_id: dict[str, dict[str, Any]],
    mutants: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    positives = [result for result in results if result["kind"] == "positive_gold"]
    negatives = [result for result in results if result["kind"] in MUTANT_TYPES]
    positive_failures = [result for result in positives if not result["correct"]]
    negative_false_passes = [result for result in negatives if not result["correct"]]
    blocking_negative_failures = [
        result
        for result in negative_false_passes
        if criteria_by_id[result["criterion_id"]].get("criticality") in (2, 3)
    ]
    by_type = {}
    for mutant_type in MUTANT_TYPES:
        items = [result for result in negatives if result["kind"] == mutant_type]
        failures = [result for result in items if not result["correct"]]
        by_type[mutant_type] = {
            "n": len(items),
            "n_false_pass_or_unresolved": len(failures),
            "rate": len(failures) / len(items) if items else 0.0,
            "n_not_applicable": sum(
                mutant.get("type") == mutant_type and not mutant.get("applicable", True)
                for mutant in (mutants or [])
            ),
        }
    return {
        "positive": {
            "n": len(positives),
            "n_failed_or_unresolved": len(positive_failures),
            "pass_rate": 1 - (len(positive_failures) / len(positives)) if positives else 0.0,
        },
        "negative": {
            "n": len(negatives),
            "n_false_pass_or_unresolved": len(negative_false_passes),
            "false_pass_or_unresolved_rate": (
                len(negative_false_passes) / len(negatives) if negatives else 0.0
            ),
            "by_type": by_type,
        },
        "blocking_criticality_2_or_3": len(blocking_negative_failures),
        "freeze_allowed": not positive_failures and not blocking_negative_failures,
        "gate_rule": (
            "Gold must pass with a stable committee majority for every criterion. Every negative mutant for "
            "criticality 2 or 3 must be stably rejected; criticality 1 failures are warnings."
        ),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    metrics = payload["metrics"]
    lines = [
        "# Positive und negative Rubrikkalibrierung",
        "",
        f"- Rubrik: `{payload['rubric']}`",
        f"- Kriterien: {payload['n_criteria']}",
        f"- Goldkontrolle: {metrics['positive']['n'] - metrics['positive']['n_failed_or_unresolved']}/{metrics['positive']['n']} stabil korrekt",
        f"- Negativmutanten: {metrics['negative']['n_false_pass_or_unresolved']}/{metrics['negative']['n']} False Pass oder ungelöst",
        f"- Blockierende Fehler (★★/★★★): {metrics['blocking_criticality_2_or_3']}",
        f"- Freeze erlaubt: {'ja' if metrics['freeze_allowed'] else 'nein'}",
        "",
        "## Nach Mutantentyp",
        "",
    ]
    for mutant_type, item in metrics["negative"]["by_type"].items():
        lines.append(
            f"- `{mutant_type}`: {item['n_false_pass_or_unresolved']}/{item['n']} "
            f"({item['rate']:.1%}); nicht anwendbar: {item.get('n_not_applicable', 0)}"
        )
    failures = [result for result in payload["results"] if not result["correct"]]
    lines.extend(["", "## Fehler und ungelöste Fälle", ""])
    if not failures:
        lines.append("Keine.")
    for result in failures:
        lines.append(
            f"- **{result['case_id']}**: erwartet `{result['expected_verdict']}`, "
            f"erhalten `{result['actual_verdict']}` (`{result['resolution']}`)."
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    task_dir = args.task_dir.resolve()
    load_env_files(task_dir)
    task = load_task(task_dir)
    rubric_path = (args.rubric or (task_dir / "evals" / "rubric.json")).resolve()
    rubric = json.loads(rubric_path.read_text(encoding="utf-8"))
    criteria = rubric.get("criteria") or []
    if not criteria:
        raise SystemExit(f"No criteria found in {rubric_path}")
    if args.criterion_id:
        requested_ids = set(args.criterion_id)
        known_ids = {str(criterion["id"]) for criterion in criteria}
        unknown_ids = sorted(requested_ids - known_ids)
        if unknown_ids:
            raise SystemExit(f"Unknown criterion IDs: {', '.join(unknown_ids)}")
        criteria = [
            criterion for criterion in criteria if str(criterion["id"]) in requested_ids
        ]
    criteria_by_id = {str(criterion["id"]): criterion for criterion in criteria}
    solution_files = discover_solution_files(task_dir, args.solution)
    specs = load_judge_committee(args.committee)
    output = (
        args.output.resolve()
        if args.output
        else task_dir / "evals" / "rubric-negative-calibration.json"
    )
    cache_dir = (
        args.cache_dir.resolve()
        if args.cache_dir
        else task_dir / "evals" / ".negative-calibration-cache"
    )
    reasoning_effort = None if str(args.reasoning_effort).lower() == "none" else args.reasoning_effort

    if args.dry_run:
        print(f"Task: {task.get('title', task_dir.name)}")
        print(f"Rubric: {rubric_path} ({len(criteria)} criteria)")
        print(f"Positive controls: {len(criteria)}")
        print(f"Negative mutants: {len(criteria) * len(MUTANT_TYPES)}")
        print(f"Base committee votes: {len(criteria) * (1 + len(MUTANT_TYPES)) * len(specs)}")
        print(f"Generator chunks: {len(chunks(criteria, args.chunk_size))}")
        print("No API calls made.")
        return 0

    for endpoint in {spec.api_base for spec in specs}:
        key = api_key_env_for(endpoint)
        if not os.environ.get(key):
            raise SystemExit(f"{key} is not set for {endpoint}")

    if args.mutants_from:
        mutants_source = args.mutants_from.resolve()
        mutants_payload = json.loads(mutants_source.read_text(encoding="utf-8"))
        raw_mutants = (
            mutants_payload.get("mutants")
            if isinstance(mutants_payload, dict)
            else mutants_payload
        )
        if not isinstance(raw_mutants, list):
            raise SystemExit(f"No mutants list found in {mutants_source}")
        selected_ids = {str(criterion["id"]) for criterion in criteria}
        raw_mutants = [
            mutant
            for mutant in raw_mutants
            if str(mutant.get("criterion_id", "")) in selected_ids
        ]
        mutants = validate_mutants(raw_mutants, criteria)
        generator_usage = [{"reused_from": str(mutants_source)}]
    else:
        mutants, generator_usage = generate_mutants(
            task_dir=task_dir,
            task=task,
            criteria=criteria,
            solution_files=solution_files,
            model=args.model,
            reasoning_effort=reasoning_effort,
            chunk_size=args.chunk_size,
            cache_dir=cache_dir,
        )
    positive_answer = "\n\n".join(
        f"## {path.name}\n{path.read_text(encoding='utf-8', errors='replace')}"
        for path in solution_files
    )
    cases = [
        {
            "id": f"{criterion['id']}__positive_gold",
            "criterion": criterion,
            "kind": "positive_gold",
            "expected_verdict": "pass",
            "answer": positive_answer,
        }
        for criterion in criteria
    ]
    cases.extend(
        {
            "id": mutant["id"],
            "criterion": criteria_by_id[mutant["criterion_id"]],
            "kind": mutant["type"],
            "expected_verdict": "fail",
            "answer": mutant["answer"],
        }
        for mutant in mutants
        if mutant.get("applicable", True)
    )
    results = run_committee_cases(
        task=task,
        task_dir=task_dir,
        cases=cases,
        specs=specs,
        parallel=args.parallel,
        error_retries=args.error_retries,
        cache_dir=cache_dir,
    )
    payload = {
        "schema_version": "0.1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "purpose": (
            "Case-internal positive and synthetic-negative calibration. Professor feedback is not input."
        ),
        "task": str(task_dir),
        "rubric": str(rubric_path),
        "n_criteria": len(criteria),
        "generator": {"model": args.model, "usage": generator_usage},
        "committee": [spec.as_dict() for spec in specs],
        "mutants": mutants,
        "metrics": build_metrics(results, criteria_by_id, mutants),
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path = output.with_suffix(".md")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"Freeze allowed: {payload['metrics']['freeze_allowed']}")
    print(f"Wrote {output}")
    print(f"Wrote {markdown_path}")
    return 0 if payload["metrics"]["freeze_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
