#!/usr/bin/env python3
"""Evaluate a LAB-EU submission against generated rubric criteria."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


DEFAULT_JUDGE_MODEL = "gpt-5.5"
DEFAULT_PARALLEL = 4
DEFAULT_API_BASE = "https://api.openai.com/v1"
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO_ROOT / "prompts" / "evaluation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a LAB-EU answer with rubric criteria.")
    parser.add_argument("task_dir", type=pathlib.Path, help="Task directory containing task.json and evals/rubric.json.")
    parser.add_argument("submission", type=pathlib.Path, help="Answer file, or output directory with deliverable files.")
    parser.add_argument("--judge-model", default=os.environ.get("OPENAI_JUDGE_MODEL", DEFAULT_JUDGE_MODEL))
    parser.add_argument("--parallel", type=int, default=DEFAULT_PARALLEL)
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without calling the judge model.")
    return parser.parse_args()


def load_env_files(task_dir: pathlib.Path) -> None:
    for candidate in [pathlib.Path.cwd() / ".env", task_dir.parent / ".env", task_dir / ".env"]:
        if candidate.exists():
            load_dotenv(candidate, override=False)


def make_client() -> OpenAI:
    api_base = os.environ.get("OPENAI_API_BASE", DEFAULT_API_BASE)
    if api_base == DEFAULT_API_BASE:
        return OpenAI()
    return OpenAI(base_url=api_base)


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_rubric(task_dir: pathlib.Path) -> tuple[pathlib.Path, list[dict[str, Any]]]:
    rubric_path = task_dir / "evals" / "rubric.json"
    rubric = load_json(rubric_path)
    criteria = rubric.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise SystemExit(f"{rubric_path} must contain a non-empty criteria list.")
    for index, criterion in enumerate(criteria, start=1):
        for key in ["id", "title", "match_criteria"]:
            if key not in criterion:
                raise SystemExit(f"{rubric_path}: criterion {index} is missing {key!r}.")
    return rubric_path, criteria


def load_agent_output(submission: pathlib.Path, criterion: dict[str, Any]) -> str:
    if submission.is_file():
        return f"## {submission.name}\n{read_text(submission)}"

    if not submission.is_dir():
        raise SystemExit(f"Submission path is neither file nor directory: {submission}")

    deliverables = criterion.get("deliverables") or []
    files: list[pathlib.Path]
    if deliverables:
        files = [submission / name for name in deliverables]
    else:
        files = sorted(path for path in submission.rglob("*") if path.is_file())

    sections = []
    for path in files:
        label = path.relative_to(submission) if path.exists() else path.name
        if not path.exists():
            sections.append(f"## {label}\n(File not found)")
            continue
        sections.append(f"## {label}\n{read_text(path)}")
    return "\n\n".join(sections) if sections else "(No agent output found)"


def judge_prompt(task: dict[str, Any], agent_output: str, criterion: dict[str, Any]) -> str:
    template = (PROMPTS_DIR / "rubric_criterion.txt").read_text(encoding="utf-8")
    return template.format(
        task_title=task.get("title", ""),
        task_instructions=task.get("instructions", ""),
        agent_output=agent_output,
        criterion_title=criterion["title"],
        match_criteria=criterion["match_criteria"],
    )


def parse_json_response(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1).strip())

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"No JSON object found in judge response: {text[:500]}")


def call_judge(client: OpenAI, model: str, prompt: str) -> dict[str, Any]:
    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=1200,
            text={"format": {"type": "json_object"}},
        )
    except OpenAIError as exc:
        raise RuntimeError(f"OpenAI judge request failed: {exc}") from exc

    result = parse_json_response(response.output_text or "")
    verdict = str(result.get("verdict", "fail")).lower()
    if verdict not in {"pass", "fail"}:
        verdict = "fail"
    return {
        "verdict": verdict,
        "reasoning": str(result.get("reasoning", "")),
        "usage": usage_summary(response.model_dump(mode="json")),
    }


def usage_summary(response_data: dict[str, Any]) -> dict[str, Any]:
    usage = response_data.get("usage") or {}
    return {
        key: usage[key]
        for key in ["input_tokens", "output_tokens", "total_tokens"]
        if key in usage
    }


def score_one(client: OpenAI, model: str, task: dict[str, Any], submission: pathlib.Path, criterion: dict[str, Any]) -> dict[str, Any]:
    agent_output = load_agent_output(submission, criterion)
    result = call_judge(client, model, judge_prompt(task, agent_output, criterion))
    return {
        "id": criterion["id"],
        "title": criterion["title"],
        "verdict": result["verdict"],
        "reasoning": result["reasoning"],
        "usage": result["usage"],
    }


def evaluate(task_dir: pathlib.Path, submission: pathlib.Path, judge_model: str, parallel: int) -> dict[str, Any]:
    task = load_json(task_dir / "task.json")
    rubric_path, criteria = load_rubric(task_dir)
    client = make_client()

    with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        results = list(
            pool.map(
                lambda criterion: score_one(client, judge_model, task, submission, criterion),
                criteria,
            )
        )

    n_passed = sum(1 for result in results if result["verdict"] == "pass")
    n_criteria = len(results)
    all_pass = n_criteria > 0 and n_passed == n_criteria
    return {
        "schema_version": "0.1",
        "evaluator": "rubric",
        "task": {
            "path": str(task_dir),
            "title": task.get("title"),
        },
        "submission": str(submission),
        "rubric": str(rubric_path),
        "judge_model": judge_model,
        "scored_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "score": 1.0 if all_pass else 0.0,
        "all_pass": all_pass,
        "n_criteria": n_criteria,
        "n_passed": n_passed,
        "criterion_pass_rate": n_passed / n_criteria if n_criteria else 0.0,
        "criteria_results": results,
    }


def write_scores(submission: pathlib.Path, scores: dict[str, Any]) -> pathlib.Path:
    output_dir = submission if submission.is_dir() else submission.parent
    path = output_dir / "scores.json"
    path.write_text(json.dumps(scores, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    task_dir = args.task_dir.resolve()
    submission = args.submission.resolve()
    load_env_files(task_dir)

    task = load_json(task_dir / "task.json")
    _rubric_path, criteria = load_rubric(task_dir)
    if args.dry_run:
        print(f"Task: {task.get('title', task_dir.name)}")
        print(f"Submission: {submission}")
        print(f"Judge model: {args.judge_model}")
        print(f"Criteria: {len(criteria)}")
        print(f"Parallel judge calls: {args.parallel}")
        print("No API calls made.")
        return 0

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set. Put it in the environment or .env.")

    scores = evaluate(task_dir=task_dir, submission=submission, judge_model=args.judge_model, parallel=args.parallel)
    scores_path = write_scores(submission, scores)
    print(f"{scores['n_passed']}/{scores['n_criteria']} criteria passed")
    print(f"All-pass: {scores['all_pass']}")
    print(f"Wrote {scores_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
