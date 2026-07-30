#!/usr/bin/env python3
"""Run the small professor-feedback judge regression suite."""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
from typing import Any

from dotenv import load_dotenv

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evaluation.run import (  # noqa: E402
    DEFAULT_API_BASE,
    DEFAULT_JUDGE_MODEL,
    call_judge,
    judge_prompt,
    load_json,
    make_client,
)

DEFAULT_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "professor_judge_regressions.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=pathlib.Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--judge-model", default=os.environ.get("OPENAI_JUDGE_MODEL", DEFAULT_JUDGE_MODEL))
    parser.add_argument("--judge-api-base", default=os.environ.get("OPENAI_API_BASE", DEFAULT_API_BASE))
    parser.add_argument("--reasoning-effort", default=os.environ.get("OPENAI_JUDGE_REASONING_EFFORT", "medium"))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_cases(path: pathlib.Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise SystemExit(f"{path} must contain a non-empty cases list.")
    return cases


def criterion_for(task_dir: pathlib.Path, criterion_id: str) -> dict[str, Any]:
    criteria = load_json(task_dir / "evals" / "rubric.json").get("criteria") or []
    for criterion in criteria:
        if criterion.get("id") == criterion_id:
            return criterion
    raise SystemExit(f"Criterion {criterion_id!r} not found under {task_dir}.")


def main() -> int:
    args = parse_args()
    fixtures = args.fixtures.resolve()
    load_dotenv(REPO_ROOT / ".env", override=False)
    cases = load_cases(fixtures)
    prepared: list[tuple[dict[str, Any], str]] = []
    for case in cases:
        task_dir = REPO_ROOT / case["task_dir"]
        task = load_json(task_dir / "task.json")
        criterion = case.get("criterion") or criterion_for(task_dir, str(case["criterion_id"]))
        prompt = judge_prompt(task, task_dir, str(case["answer"]), criterion)
        prepared.append((case, prompt))

    if args.dry_run:
        print(f"Validated {len(prepared)} regression cases from {fixtures}.")
        return 0

    client, use_chat = make_client(args.judge_api_base)
    effort = None if args.reasoning_effort.lower() == "none" else args.reasoning_effort
    failures = 0
    for case, prompt in prepared:
        result = call_judge(client, args.judge_model, prompt, effort, use_chat)
        actual = result["verdict"]
        expected = case["expected_verdict"]
        ok = actual == expected
        failures += int(not ok)
        marker = "PASS" if ok else "FAIL"
        print(f"{marker} {case['id']}: expected={expected} actual={actual}")
        if not ok:
            print(f"  {result['reasoning']}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
