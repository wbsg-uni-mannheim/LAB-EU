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
DEFAULT_REASONING_EFFORT = "medium"
DEFAULT_PARALLEL = 4
DEFAULT_API_BASE = "https://api.openai.com/v1"
MAX_SOURCE_CHARS = 16_000
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO_ROOT / "prompts" / "evaluation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a LAB-EU answer with rubric criteria.")
    parser.add_argument("task_dir", type=pathlib.Path, help="Task directory containing task.json and evals/rubric.json.")
    parser.add_argument("submission", type=pathlib.Path, help="Answer file, or output directory with deliverable files.")
    parser.add_argument("--judge-model", default=os.environ.get("OPENAI_JUDGE_MODEL", DEFAULT_JUDGE_MODEL))
    parser.add_argument(
        "--judge-api-base",
        default=os.environ.get("OPENAI_API_BASE", DEFAULT_API_BASE),
        help=(
            "Judge endpoint. Default is the OpenAI Responses API. "
            "Use https://openrouter.ai/api/v1 to judge with an OpenRouter model (chat-completions API)."
        ),
    )
    parser.add_argument(
        "--reasoning-effort",
        default=os.environ.get("OPENAI_JUDGE_REASONING_EFFORT", DEFAULT_REASONING_EFFORT),
        help=(
            "Reasoning effort for the judge model (e.g. low, medium, high). "
            f"Use 'none' to omit the parameter. Defaults to {DEFAULT_REASONING_EFFORT}."
        ),
    )
    parser.add_argument("--parallel", type=int, default=DEFAULT_PARALLEL)
    parser.add_argument(
        "--votes",
        type=int,
        default=1,
        help=(
            "Judge votes per criterion; the majority decides, ties fail. "
            "Use 3 for headline runs to reduce judge variance. Defaults to 1."
        ),
    )
    parser.add_argument(
        "--adaptive",
        action="store_true",
        help=(
            "Adaptive voting: cast one vote per criterion first and escalate to the full "
            "--votes count only when that vote is not a pass. Cuts judge cost on good answers; "
            "a single false pass is not double-checked, so use full voting when false passes matter most."
        ),
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help="Path for the scores JSON. Defaults to scores.json next to the submission.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without calling the judge model.")
    return parser.parse_args()


def load_env_files(task_dir: pathlib.Path) -> None:
    for candidate in [pathlib.Path.cwd() / ".env", task_dir.parent / ".env", task_dir / ".env"]:
        if candidate.exists():
            load_dotenv(candidate, override=False)


def api_key_env_for(api_base: str) -> str:
    host = api_base.lower()
    if "openrouter" in host:
        return "OPENROUTER_API_KEY"
    if "deepseek" in host:
        return "DEEPSEEK_API_KEY"
    return "OPENAI_API_KEY"


def make_client(api_base: str) -> tuple[OpenAI, bool]:
    """Return (client, use_chat_api). use_chat_api=True for non-OpenAI endpoints."""
    if api_base == DEFAULT_API_BASE:
        return OpenAI(), False
    key_env = api_key_env_for(api_base)
    key = os.environ.get(key_env)
    if not key:
        raise SystemExit(f"{key_env} is not set (needed for --judge-api-base {api_base}). Put it in .env.")
    return OpenAI(base_url=api_base, api_key=key), True


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


def load_criterion_sources(task_dir: pathlib.Path, criterion: dict[str, Any]) -> str:
    names = criterion.get("sources") or []
    sections = []
    for name in names:
        path = task_dir / name
        if not path.exists():
            sections.append(f"### {name}\n(File not found)")
            continue
        text = read_text(path)
        if len(text) > MAX_SOURCE_CHARS:
            text = text[:MAX_SOURCE_CHARS] + "\n[TRUNCATED]"
        sections.append(f"### {name}\n{text}")
    return "\n\n".join(sections) if sections else "(No source documents attached to this criterion.)"


def judge_prompt(
    task: dict[str, Any],
    task_dir: pathlib.Path,
    agent_output: str,
    criterion: dict[str, Any],
) -> str:
    template = (PROMPTS_DIR / "rubric_criterion.txt").read_text(encoding="utf-8")
    return template.format(
        task_title=task.get("title", ""),
        task_instructions=task.get("instructions", ""),
        criterion_sources=load_criterion_sources(task_dir, criterion),
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


def _judge_call_responses(client: OpenAI, model: str, prompt: str, reasoning_effort: str | None):
    request: dict[str, Any] = {
        "model": model,
        "input": prompt,
        "text": {"format": {"type": "json_object"}},
    }
    if reasoning_effort:
        request["reasoning"] = {"effort": reasoning_effort}
    response = client.responses.create(**request)
    return response.output_text or "", usage_summary(response.model_dump(mode="json"))


def _judge_call_chat(client: OpenAI, model: str, prompt: str):
    # OpenAI-compatible chat endpoints (e.g. OpenRouter). Ask for a JSON object;
    # some models reject response_format, so retry once without it.
    messages = [{"role": "user", "content": prompt}]
    try:
        response = client.chat.completions.create(
            model=model, messages=messages, response_format={"type": "json_object"}
        )
    except OpenAIError:
        response = client.chat.completions.create(model=model, messages=messages)
    text = (response.choices[0].message.content or "") if response.choices else ""
    return text, usage_summary(response.model_dump(mode="json"))


def call_judge(
    client: OpenAI, model: str, prompt: str, reasoning_effort: str | None, use_chat: bool = False
) -> dict[str, Any]:
    # No max_output_tokens: token usage is recorded per criterion in scores.json.
    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            if use_chat:
                text, usage = _judge_call_chat(client, model, prompt)
            else:
                text, usage = _judge_call_responses(client, model, prompt, reasoning_effort)
        except OpenAIError as exc:
            last_error = RuntimeError(f"Judge request failed: {exc}")
            continue
        try:
            result = parse_json_response(text or "")
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            continue
        verdict = str(result.get("verdict", "fail")).lower()
        if verdict not in {"pass", "fail"}:
            verdict = "fail"
        evidence = result.get("evidence")
        if not isinstance(evidence, list):
            evidence = [str(evidence)] if evidence else []
        return {
            "verdict": verdict,
            "reasoning": str(result.get("reasoning", "")),
            "evidence": [str(item) for item in evidence],
            "usage": usage,
        }
    raise last_error if last_error else RuntimeError("Judge call failed without error detail.")


def usage_summary(response_data: dict[str, Any]) -> dict[str, Any]:
    usage = response_data.get("usage") or {}
    summary = {
        key: usage[key]
        for key in ["input_tokens", "output_tokens", "total_tokens"]
        if key in usage
    }
    details = usage.get("input_tokens_details") or {}
    if isinstance(details, dict) and "cached_tokens" in details:
        summary["cached_input_tokens"] = details["cached_tokens"]
    return summary


def score_one(
    client: OpenAI,
    model: str,
    task: dict[str, Any],
    task_dir: pathlib.Path,
    submission: pathlib.Path,
    criterion: dict[str, Any],
    reasoning_effort: str | None,
    use_chat: bool = False,
) -> dict[str, Any]:
    try:
        agent_output = load_agent_output(submission, criterion)
        result = call_judge(
            client, model, judge_prompt(task, task_dir, agent_output, criterion), reasoning_effort, use_chat
        )
    except Exception as exc:  # noqa: BLE001 - one broken judge call must not kill the run
        return {
            "id": criterion["id"],
            "title": criterion["title"],
            "verdict": "error",
            "reasoning": f"Judge call failed: {exc}",
            "evidence": [],
            "usage": {},
        }
    return {
        "id": criterion["id"],
        "title": criterion["title"],
        "verdict": result["verdict"],
        "reasoning": result["reasoning"],
        "evidence": result["evidence"],
        "usage": result["usage"],
    }


def aggregate_votes(criterion: dict[str, Any], vote_results: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"pass": 0, "fail": 0, "error": 0}
    usage_total: dict[str, int] = {}
    for vote in vote_results:
        counts[vote.get("verdict", "error")] = counts.get(vote.get("verdict", "error"), 0) + 1
        for key in ["input_tokens", "output_tokens", "total_tokens", "cached_input_tokens"]:
            value = (vote.get("usage") or {}).get(key)
            if isinstance(value, int):
                usage_total[key] = usage_total.get(key, 0) + value

    n_votes = len(vote_results)
    if counts["pass"] * 2 > n_votes:
        verdict = "pass"
    elif counts["error"] == n_votes:
        verdict = "error"
    else:
        verdict = "fail"

    valid = counts["pass"] + counts["fail"]
    agreement = (max(counts["pass"], counts["fail"]) / valid) if valid else 0.0
    primary = next((vote for vote in vote_results if vote.get("verdict") == verdict), vote_results[0])
    return {
        "id": criterion["id"],
        "title": criterion["title"],
        "verdict": verdict,
        "reasoning": primary.get("reasoning", ""),
        "evidence": primary.get("evidence", []),
        "vote_counts": counts,
        "judge_agreement": round(agreement, 3),
        "votes": [
            {
                "verdict": vote.get("verdict"),
                "reasoning": vote.get("reasoning", ""),
                "evidence": vote.get("evidence", []),
            }
            for vote in vote_results
        ],
        "usage": usage_total,
    }


def evaluate(
    task_dir: pathlib.Path,
    submission: pathlib.Path,
    judge_model: str,
    parallel: int,
    reasoning_effort: str | None,
    votes: int,
    adaptive: bool = False,
    api_base: str = DEFAULT_API_BASE,
) -> dict[str, Any]:
    task = load_json(task_dir / "task.json")
    rubric_path, criteria = load_rubric(task_dir)
    client, use_chat = make_client(api_base)
    votes = max(1, votes)

    def run_job(job: tuple[int, int]) -> tuple[int, dict[str, Any]]:
        index, _vote = job
        return index, score_one(
            client, judge_model, task, task_dir, submission, criteria[index], reasoning_effort, use_chat
        )

    votes_by_criterion: list[list[dict[str, Any]]] = [[] for _ in criteria]

    def run_jobs(jobs: list[tuple[int, int]]) -> None:
        with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
            for index, vote_result in pool.map(run_job, jobs):
                votes_by_criterion[index].append(vote_result)

    run_jobs([(index, 0) for index in range(len(criteria))])
    if votes > 1:
        if adaptive:
            escalate = [
                index
                for index, vote_results in enumerate(votes_by_criterion)
                if vote_results[0].get("verdict") != "pass"
            ]
        else:
            escalate = list(range(len(criteria)))
        run_jobs([(index, vote) for index in escalate for vote in range(1, votes)])

    results = [
        aggregate_votes(criterion, vote_results)
        for criterion, vote_results in zip(criteria, votes_by_criterion)
    ]

    criteria_by_id = {criterion["id"]: criterion for criterion in criteria}

    def make_breakdown(key_of: Any) -> dict[str, dict[str, Any]]:
        groups: dict[str, dict[str, Any]] = {}
        for result in results:
            tags = (criteria_by_id.get(result["id"], {}).get("analysis_tags")) or {}
            key = key_of(tags) or "untagged"
            group = groups.setdefault(key, {"n_criteria": 0, "n_passed": 0, "n_failed": 0, "n_errors": 0})
            group["n_criteria"] += 1
            if result["verdict"] == "pass":
                group["n_passed"] += 1
            elif result["verdict"] == "error":
                group["n_errors"] += 1
            else:
                group["n_failed"] += 1
        for group in groups.values():
            group["pass_rate"] = round(group["n_passed"] / group["n_criteria"], 3)
        return groups

    has_tags = any(criterion.get("analysis_tags") for criterion in criteria)

    n_passed = sum(1 for result in results if result["verdict"] == "pass")
    n_errors = sum(1 for result in results if result["verdict"] == "error")
    n_criteria = len(results)
    all_pass = n_criteria > 0 and n_passed == n_criteria
    agreements = [result["judge_agreement"] for result in results if result["vote_counts"]["pass"] + result["vote_counts"]["fail"] > 0]
    judge_usage_total: dict[str, int] = {}
    for result in results:
        for key, value in (result.get("usage") or {}).items():
            if isinstance(value, int):
                judge_usage_total[key] = judge_usage_total.get(key, 0) + value
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
        "judge_api_base": api_base,
        "judge_reasoning_effort": reasoning_effort,
        "votes_per_criterion": votes,
        "adaptive_voting": adaptive,
        "scored_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "score": 1.0 if all_pass else 0.0,
        "all_pass": all_pass,
        "n_criteria": n_criteria,
        "n_passed": n_passed,
        "n_errors": n_errors,
        "criterion_pass_rate": n_passed / n_criteria if n_criteria else 0.0,
        "mean_judge_agreement": round(sum(agreements) / len(agreements), 3) if agreements else 0.0,
        "n_unanimous": sum(1 for result in results if result["judge_agreement"] == 1.0),
        "breakdown_by_station": make_breakdown(lambda tags: (tags.get("station_path") or [None])[0]) if has_tags else None,
        "breakdown_by_function": make_breakdown(lambda tags: tags.get("function")) if has_tags else None,
        "judge_usage_total": judge_usage_total,
        "criteria_results": results,
    }


def write_scores(submission: pathlib.Path, scores: dict[str, Any], output: pathlib.Path | None = None) -> pathlib.Path:
    if output is not None:
        path = output.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
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
    reasoning_effort = None if args.reasoning_effort.lower() == "none" else args.reasoning_effort
    api_base = args.judge_api_base
    if args.dry_run:
        print(f"Task: {task.get('title', task_dir.name)}")
        print(f"Submission: {submission}")
        print(f"Judge model: {args.judge_model}")
        print(f"Judge endpoint: {api_base} (key: {api_key_env_for(api_base)})")
        print(f"Judge reasoning effort: {reasoning_effort}")
        print(f"Votes per criterion: {max(1, args.votes)}")
        print(f"Criteria: {len(criteria)}")
        print(f"Parallel judge calls: {args.parallel}")
        print("No API calls made.")
        return 0

    key_env = api_key_env_for(api_base)
    if not os.environ.get(key_env):
        raise SystemExit(f"{key_env} is not set (needed for judge endpoint {api_base}). Put it in .env.")

    scores = evaluate(
        task_dir=task_dir,
        submission=submission,
        judge_model=args.judge_model,
        parallel=args.parallel,
        reasoning_effort=reasoning_effort,
        votes=args.votes,
        adaptive=args.adaptive,
        api_base=api_base,
    )
    scores_path = write_scores(submission, scores, args.output)
    print(f"{scores['n_passed']}/{scores['n_criteria']} criteria passed")
    for breakdown_key, label in [("breakdown_by_station", "By station"), ("breakdown_by_function", "By function")]:
        breakdown = scores.get(breakdown_key)
        if breakdown:
            print(f"{label}:")
            for name, group in sorted(breakdown.items(), key=lambda item: -item[1]["n_criteria"]):
                print(f"  {name}: {group['n_passed']}/{group['n_criteria']} ({group['pass_rate']:.0%})")
    if scores["votes_per_criterion"] > 1:
        print(
            f"Judge agreement: mean {scores['mean_judge_agreement']}, "
            f"{scores['n_unanimous']}/{scores['n_criteria']} unanimous"
        )
    if scores["n_errors"]:
        print(f"WARNING: {scores['n_errors']} criteria have 'error' verdicts (all votes failed).")
    print(f"All-pass: {scores['all_pass']}")
    print(f"Wrote {scores_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
