#!/usr/bin/env python3
"""Evaluate a LAB-EU submission against generated rubric criteria."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


DEFAULT_JUDGE_MODEL = "gpt-5.5"
DEFAULT_REASONING_EFFORT = "medium"
DEFAULT_PARALLEL = 4
DEFAULT_API_BASE = "https://api.openai.com/v1"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 75.0
MAX_SOURCE_CHARS = 16_000
STYLE_ELIGIBLE_FUNCTIONS = {"application", "argumentation"}
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO_ROOT / "prompts" / "evaluation"


@dataclass(frozen=True)
class JudgeSpec:
    """One independently configured committee member."""

    name: str
    model: str
    api_base: str = DEFAULT_API_BASE
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT
    parallel: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "model": self.model,
            "api_base": self.api_base,
            "reasoning_effort": self.reasoning_effort,
            "parallel": self.parallel,
        }


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
    parser.add_argument(
        "--rubric",
        type=pathlib.Path,
        default=None,
        help="Optional rubric JSON. Defaults to <task-dir>/evals/rubric.json.",
    )
    parser.add_argument(
        "--criterion-id",
        action="append",
        default=[],
        help="Evaluate only the named criterion id. Repeat for a targeted stability run.",
    )
    parser.add_argument(
        "--judge-committee",
        type=pathlib.Path,
        default=None,
        help=(
            "JSON file containing an odd-sized 'judges' list with name, model, api_base, "
            "and optional reasoning_effort. Each judge casts one independent vote."
        ),
    )
    parser.add_argument(
        "--style-evaluation",
        action="store_true",
        help=(
            "Return a separate Boolean Gutachtenstil verdict for all application and "
            "argumentation criteria. By default, content and style share one judge call; "
            "other content criteria remain content-only."
        ),
    )
    parser.add_argument(
        "--separate-style-calls",
        action="store_true",
        help=(
            "With --style-evaluation, preserve the legacy second judge call per eligible "
            "criterion. Intended only for calibration against the combined default."
        ),
    )
    parser.add_argument(
        "--committee-conflict-recheck",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "With --judge-committee, rerun only 2:1 criteria with the full committee. "
            "Matching round majorities are kept with a dissent flag; a flip is unresolved. "
            "Enabled by default."
        ),
    )
    parser.add_argument(
        "--committee-error-retries",
        type=int,
        default=1,
        help="Targeted retries per errored committee vote before a criterion remains unresolved.",
    )
    parser.add_argument(
        "--vote-cache-dir",
        type=pathlib.Path,
        default=None,
        help=(
            "Directory for successful per-model, per-criterion votes. Existing matching votes "
            "are reused, making interrupted committee runs resumable."
        ),
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


def make_client(
    api_base: str, timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
) -> tuple[OpenAI, bool]:
    """Return (client, use_chat_api). use_chat_api=True for non-OpenAI endpoints."""
    if api_base == DEFAULT_API_BASE:
        return OpenAI(timeout=timeout_seconds, max_retries=0), False
    key_env = api_key_env_for(api_base)
    key = os.environ.get(key_env)
    if not key:
        raise SystemExit(f"{key_env} is not set (needed for --judge-api-base {api_base}). Put it in .env.")
    return OpenAI(
        base_url=api_base, api_key=key, timeout=timeout_seconds, max_retries=0
    ), True


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_rubric(
    task_dir: pathlib.Path, rubric_override: pathlib.Path | None = None
) -> tuple[pathlib.Path, list[dict[str, Any]]]:
    rubric_path = (rubric_override or (task_dir / "evals" / "rubric.json")).resolve()
    rubric = load_json(rubric_path)
    criteria = rubric.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise SystemExit(f"{rubric_path} must contain a non-empty criteria list.")
    for index, criterion in enumerate(criteria, start=1):
        for key in ["id", "title", "match_criteria"]:
            if key not in criterion:
                raise SystemExit(f"{rubric_path}: criterion {index} is missing {key!r}.")
    return rubric_path, criteria


def select_criteria(
    criteria: list[dict[str, Any]], criterion_ids: list[str] | None
) -> list[dict[str, Any]]:
    if not criterion_ids:
        return criteria
    requested = set(criterion_ids)
    known = {criterion["id"] for criterion in criteria}
    unknown = sorted(requested - known)
    if unknown:
        raise SystemExit(f"Unknown --criterion-id values: {', '.join(unknown)}")
    return [criterion for criterion in criteria if criterion["id"] in requested]


def load_judge_committee(path: pathlib.Path) -> list[JudgeSpec]:
    payload = load_json(path.resolve())
    raw_judges = payload.get("judges")
    if not isinstance(raw_judges, list) or not raw_judges:
        raise SystemExit(f"{path} must contain a non-empty 'judges' list.")
    if len(raw_judges) < 3 or len(raw_judges) % 2 == 0:
        raise SystemExit(f"{path} must contain an odd number of at least three judges.")

    specs: list[JudgeSpec] = []
    seen_names: set[str] = set()
    for index, raw in enumerate(raw_judges, start=1):
        if not isinstance(raw, dict):
            raise SystemExit(f"{path}: judge {index} must be an object.")
        name = str(raw.get("name", "")).strip()
        model = str(raw.get("model", "")).strip()
        api_base = str(raw.get("api_base", DEFAULT_API_BASE)).strip()
        raw_effort = raw.get("reasoning_effort", DEFAULT_REASONING_EFFORT)
        effort = None if raw_effort is None or str(raw_effort).lower() == "none" else str(raw_effort)
        raw_parallel = raw.get("parallel")
        parallel = int(raw_parallel) if raw_parallel is not None else None
        if not name or not model or not api_base:
            raise SystemExit(f"{path}: judge {index} needs non-empty name, model, and api_base.")
        if name in seen_names:
            raise SystemExit(f"{path}: duplicate judge name {name!r}.")
        seen_names.add(name)
        if parallel is not None and parallel < 1:
            raise SystemExit(f"{path}: judge {index} parallel must be at least 1.")
        specs.append(
            JudgeSpec(
                name=name,
                model=model,
                api_base=api_base,
                reasoning_effort=effort,
                parallel=parallel,
            )
        )
    return specs


def single_judge_specs(
    model: str, api_base: str, reasoning_effort: str | None, votes: int
) -> list[JudgeSpec]:
    return [
        JudgeSpec(
            name=f"{model}#{vote + 1}",
            model=model,
            api_base=api_base,
            reasoning_effort=reasoning_effort,
        )
        for vote in range(max(1, votes))
    ]


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


def style_judge_prompt(
    task: dict[str, Any],
    agent_output: str,
    criterion: dict[str, Any],
    content_result: dict[str, Any],
) -> str:
    template = (PROMPTS_DIR / "gutachtenstil_criterion.txt").read_text(encoding="utf-8")
    evidence = content_result.get("evidence") or []
    rendered_evidence = "\n".join(f"- {item}" for item in evidence) or "(No quoted evidence.)"
    return template.format(
        task_title=task.get("title", ""),
        task_instructions=task.get("instructions", ""),
        agent_output=agent_output,
        criterion_title=criterion["title"],
        match_criteria=criterion["match_criteria"],
        content_verdict=content_result.get("verdict", "unknown"),
        content_evidence=rendered_evidence,
    )


def combined_content_style_prompt(
    task: dict[str, Any],
    task_dir: pathlib.Path,
    agent_output: str,
    criterion: dict[str, Any],
) -> str:
    template = (PROMPTS_DIR / "combined_content_style_criterion.txt").read_text(
        encoding="utf-8"
    )
    return template.format(
        task_title=task.get("title", ""),
        task_instructions=task.get("instructions", ""),
        criterion_sources=load_criterion_sources(task_dir, criterion),
        agent_output=agent_output,
        criterion_title=criterion["title"],
        match_criteria=criterion["match_criteria"],
    )


def is_style_eligible_criterion(criterion: dict[str, Any]) -> bool:
    """Limit style scoring to criteria that require legal application or argumentation."""
    function = str((criterion.get("analysis_tags") or {}).get("function") or "")
    if not function:
        # Preserve the previous behavior for legacy rubrics without analysis tags.
        return True
    return function in STYLE_ELIGIBLE_FUNCTIONS


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
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=4000,
        )
    except OpenAIError:
        response = client.chat.completions.create(model=model, messages=messages, max_tokens=4000)
    text = (response.choices[0].message.content or "") if response.choices else ""
    return text, usage_summary(response.model_dump(mode="json"))


def normalize_judge_result(result: dict[str, Any], usage: dict[str, Any]) -> dict[str, Any]:
    """Normalize a vote and enforce contradictions exposed by its own audit fields."""
    verdict = str(result.get("verdict", "fail")).lower()
    if verdict not in {"pass", "fail"}:
        verdict = "fail"

    component_checks = result.get("component_checks")
    if not isinstance(component_checks, list):
        component_checks = []
    else:
        component_checks = [item for item in component_checks if isinstance(item, dict)]
    scope_check = result.get("scope_check")
    if not isinstance(scope_check, dict):
        scope_check = {}
    stated_reason_check = result.get("stated_reason_check")
    if not isinstance(stated_reason_check, dict):
        stated_reason_check = {}

    audit_failure = (
        any(item.get("satisfied") is False for item in component_checks)
        or scope_check.get("same_scope") is False
        or stated_reason_check.get("legally_compatible") is False
    )
    if audit_failure:
        verdict = "fail"

    evidence = result.get("evidence")
    if not isinstance(evidence, list):
        evidence = [str(evidence)] if evidence else []
    return {
        "verdict": verdict,
        "reasoning": str(result.get("reasoning", "")),
        "evidence": [str(item) for item in evidence],
        "component_checks": component_checks,
        "scope_check": scope_check,
        "stated_reason_check": stated_reason_check,
        "usage": usage,
    }


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
        return normalize_judge_result(result, usage)
    raise last_error if last_error else RuntimeError("Judge call failed without error detail.")


def normalize_combined_judge_result(
    result: dict[str, Any], usage: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    content = result.get("content")
    style = result.get("style")
    if not isinstance(content, dict) or not isinstance(style, dict):
        raise ValueError("Combined judge response needs content and style objects.")
    normalized_style = normalize_judge_result(style, {})
    method_checks = style.get("method_checks")
    if not isinstance(method_checks, dict):
        method_checks = {}
    required_method_checks = (
        "same_scope",
        "criterion_specific_premise",
        "explicit_fact_link",
        "completed_path",
        "not_reconstructed_elsewhere",
    )
    if not all(method_checks.get(key) is True for key in required_method_checks):
        normalized_style["verdict"] = "fail"
    normalized_style["method_checks"] = method_checks
    return {
        "content": normalize_judge_result(content, usage),
        # The shared request usage is accounted once on the content vote.
        "style": normalized_style,
    }


def call_combined_judge(
    client: OpenAI,
    model: str,
    prompt: str,
    reasoning_effort: str | None,
    use_chat: bool = False,
) -> dict[str, dict[str, Any]]:
    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            if use_chat:
                text, usage = _judge_call_chat(client, model, prompt)
            else:
                text, usage = _judge_call_responses(
                    client, model, prompt, reasoning_effort
                )
        except OpenAIError as exc:
            last_error = RuntimeError(f"Judge request failed: {exc}")
            continue
        try:
            result = parse_json_response(text or "")
            return normalize_combined_judge_result(result, usage)
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
    raise last_error if last_error else RuntimeError(
        "Combined judge call failed without error detail."
    )


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


def add_judge_metadata(vote: dict[str, Any], spec: JudgeSpec) -> dict[str, Any]:
    return {**vote, "judge": spec.as_dict()}


def cached_judge_vote(
    *,
    cache_dir: pathlib.Path | None,
    phase: str,
    client: OpenAI,
    spec: JudgeSpec,
    prompt: str,
    criterion: dict[str, Any],
    use_chat: bool,
) -> dict[str, Any]:
    cache_payload = {
        "phase": phase,
        "judge": {
            "name": spec.name,
            "model": spec.model,
            "api_base": spec.api_base,
            "reasoning_effort": spec.reasoning_effort,
        },
        "criterion_id": criterion["id"],
        "prompt": prompt,
    }
    cache_key = hashlib.sha256(
        json.dumps(cache_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    cache_path = cache_dir / f"{phase}-{cache_key}.json" if cache_dir else None
    if cache_path and cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            cached["cache_hit"] = True
            return cached
        except (json.JSONDecodeError, OSError):
            pass

    try:
        result = call_judge(
            client, spec.model, prompt, spec.reasoning_effort, use_chat
        )
        vote = {
            "id": criterion["id"],
            "title": criterion["title"],
            "verdict": result["verdict"],
            "reasoning": result["reasoning"],
            "evidence": result["evidence"],
            "component_checks": result.get("component_checks", []),
            "scope_check": result.get("scope_check", {}),
            "stated_reason_check": result.get("stated_reason_check", {}),
            "usage": result["usage"],
            "cache_hit": False,
        }
    except Exception as exc:  # noqa: BLE001 - one broken vote must not kill the run
        return {
            "id": criterion["id"],
            "title": criterion["title"],
            "verdict": "error",
            "reasoning": f"{phase.title()} judge call failed: {exc}",
            "evidence": [],
            "usage": {},
            "cache_hit": False,
        }

    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(vote, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return vote


def cached_combined_judge_vote(
    *,
    cache_dir: pathlib.Path | None,
    phase: str,
    client: OpenAI,
    spec: JudgeSpec,
    prompt: str,
    criterion: dict[str, Any],
    use_chat: bool,
) -> dict[str, dict[str, Any]]:
    cache_payload = {
        "phase": phase,
        "judge": {
            "name": spec.name,
            "model": spec.model,
            "api_base": spec.api_base,
            "reasoning_effort": spec.reasoning_effort,
        },
        "criterion_id": criterion["id"],
        "prompt": prompt,
    }
    cache_key = hashlib.sha256(
        json.dumps(cache_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    cache_path = cache_dir / f"{phase}-{cache_key}.json" if cache_dir else None
    if cache_path and cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            for channel in ("content", "style"):
                cached[channel]["cache_hit"] = True
            return cached
        except (json.JSONDecodeError, KeyError, OSError, TypeError):
            pass

    try:
        result = call_combined_judge(
            client, spec.model, prompt, spec.reasoning_effort, use_chat
        )
        combined: dict[str, dict[str, Any]] = {}
        for channel in ("content", "style"):
            normalized = result[channel]
            combined[channel] = {
                "id": criterion["id"],
                "title": criterion["title"],
                "verdict": normalized["verdict"],
                "reasoning": normalized["reasoning"],
                "evidence": normalized["evidence"],
                "component_checks": normalized.get("component_checks", []),
                "scope_check": normalized.get("scope_check", {}),
                "stated_reason_check": normalized.get("stated_reason_check", {}),
                "method_checks": normalized.get("method_checks", {}),
                "usage": normalized["usage"],
                "cache_hit": False,
            }
    except Exception as exc:  # noqa: BLE001 - one broken vote must not kill the run
        reason = f"{phase.title()} combined judge call failed: {exc}"
        combined = {
            channel: {
                "id": criterion["id"],
                "title": criterion["title"],
                "verdict": "error",
                "reasoning": reason,
                "evidence": [],
                "component_checks": [],
                "scope_check": {},
                "stated_reason_check": {},
                "method_checks": {},
                "usage": {},
                "cache_hit": False,
            }
            for channel in ("content", "style")
        }

    if cache_path and all(
        combined[channel]["verdict"] != "error" for channel in ("content", "style")
    ):
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(combined, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return combined


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
    unresolved = counts["error"] > 0
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
        "resolution": "unresolved" if unresolved else "resolved",
        "reasoning": primary.get("reasoning", ""),
        "evidence": primary.get("evidence", []),
        "vote_counts": counts,
        "judge_agreement": round(agreement, 3),
        "votes": [
            {
                "verdict": vote.get("verdict"),
                "reasoning": vote.get("reasoning", ""),
                "evidence": vote.get("evidence", []),
                "component_checks": vote.get("component_checks", []),
                "scope_check": vote.get("scope_check", {}),
                "stated_reason_check": vote.get("stated_reason_check", {}),
                "method_checks": vote.get("method_checks", {}),
                "judge": vote.get("judge"),
                "cache_hit": bool(vote.get("cache_hit")),
            }
            for vote in vote_results
        ],
        "usage": usage_total,
    }


def needs_committee_recheck(vote_results: list[dict[str, Any]]) -> bool:
    """Return True only for a complete, non-unanimous three-model decision."""
    counts = {"pass": 0, "fail": 0, "error": 0}
    for vote in vote_results:
        verdict = vote.get("verdict", "error")
        counts[verdict] = counts.get(verdict, 0) + 1
    return (
        len(vote_results) == 3
        and counts["error"] == 0
        and sorted((counts["pass"], counts["fail"])) == [1, 2]
    )


def finalize_committee_rounds(
    criterion: dict[str, Any],
    first_votes: list[dict[str, Any]],
    second_votes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Resolve one or two complete committee rounds without pooling six votes."""
    first = aggregate_votes(criterion, first_votes)
    rounds = [
        {
            "round": 1,
            "verdict": first["verdict"],
            "resolution": first["resolution"],
            "vote_counts": first["vote_counts"],
            "votes": first["votes"],
        }
    ]
    if first["vote_counts"]["error"]:
        first["verdict"] = "fail"
        first["resolution"] = "unresolved"
        first["committee_status"] = "incomplete"
        first["voting_rounds"] = rounds
        return first

    if second_votes is None:
        first["resolution"] = "stable"
        first["committee_status"] = "stable"
        first["voting_rounds"] = rounds
        return first

    second = aggregate_votes(criterion, second_votes)
    rounds.append(
        {
            "round": 2,
            "verdict": second["verdict"],
            "resolution": second["resolution"],
            "vote_counts": second["vote_counts"],
            "votes": second["votes"],
        }
    )
    second["voting_rounds"] = rounds
    if second["vote_counts"]["error"]:
        second["verdict"] = "fail"
        second["resolution"] = "unresolved"
        second["committee_status"] = "incomplete"
        return second
    if first["verdict"] == second["verdict"]:
        second["resolution"] = "stable_with_dissent"
        second["committee_status"] = "stable_with_dissent"
        return second

    second["verdict"] = "fail"
    second["resolution"] = "unresolved"
    second["committee_status"] = "majority_flip"
    second["reasoning"] = (
        "The committee majority changed between two independent rounds; "
        "the criterion is conservatively unresolved."
    )
    second["evidence"] = []
    return second


def evaluate(
    task_dir: pathlib.Path,
    submission: pathlib.Path,
    judge_model: str,
    parallel: int,
    reasoning_effort: str | None,
    votes: int,
    adaptive: bool = False,
    api_base: str = DEFAULT_API_BASE,
    rubric_override: pathlib.Path | None = None,
    judge_committee: list[JudgeSpec] | None = None,
    style_evaluation: bool = False,
    combine_content_and_style: bool = True,
    vote_cache_dir: pathlib.Path | None = None,
    criterion_ids: list[str] | None = None,
    committee_conflict_recheck: bool = True,
    committee_error_retries: int = 1,
) -> dict[str, Any]:
    task = load_json(task_dir / "task.json")
    rubric_path, criteria = load_rubric(task_dir, rubric_override)
    criteria = select_criteria(criteria, criterion_ids)
    votes = max(1, votes)

    if judge_committee:
        if votes != 1:
            raise SystemExit("--judge-committee casts one vote per member; do not combine it with --votes.")
        if adaptive:
            raise SystemExit("--adaptive is not supported with --judge-committee.")
        specs = judge_committee
    else:
        specs = single_judge_specs(judge_model, api_base, reasoning_effort, votes)

    clients: list[tuple[OpenAI, bool]] = [make_client(spec.api_base) for spec in specs]

    committee_error_retries = max(0, committee_error_retries)
    style_eligible_indices = [
        index
        for index, criterion in enumerate(criteria)
        if is_style_eligible_criterion(criterion)
    ]
    style_eligible_index_set = set(style_eligible_indices)
    combined_style = style_evaluation and combine_content_and_style
    if combined_style and adaptive:
        raise SystemExit(
            "Combined content/style evaluation is not supported with --adaptive. "
            "Use full voting or --separate-style-calls."
        )

    def content_vote(index: int, spec_index: int, phase: str) -> tuple[int, dict[str, Any]]:
        spec = specs[spec_index]
        client, use_chat = clients[spec_index]
        criterion = criteria[index]
        agent_output = load_agent_output(submission, criterion)
        if combined_style and index in style_eligible_index_set:
            combined = cached_combined_judge_vote(
                cache_dir=vote_cache_dir,
                phase=phase.replace("content", "combined", 1),
                client=client,
                spec=spec,
                prompt=combined_content_style_prompt(
                    task, task_dir, agent_output, criterion
                ),
                criterion=criterion,
                use_chat=use_chat,
            )
            content = add_judge_metadata(combined["content"], spec)
            content["_combined_style_vote"] = add_judge_metadata(
                combined["style"], spec
            )
            return index, content
        vote = cached_judge_vote(
            cache_dir=vote_cache_dir,
            phase=phase,
            client=client,
            spec=spec,
            prompt=judge_prompt(task, task_dir, agent_output, criterion),
            criterion=criterion,
            use_chat=use_chat,
        )
        return index, add_judge_metadata(vote, spec)

    def run_content_jobs(
        jobs: list[tuple[int, int]], phase: str
    ) -> list[list[dict[str, Any]]]:
        votes_by_criterion: list[list[dict[str, Any]]] = [[] for _ in criteria]
        jobs_by_spec: dict[int, list[tuple[int, int]]] = {}
        for job in jobs:
            jobs_by_spec.setdefault(job[1], []).append(job)
        for spec_index, spec_jobs in jobs_by_spec.items():
            workers = specs[spec_index].parallel or parallel
            with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
                for index, vote_result in pool.map(
                    lambda job: content_vote(*job, phase), spec_jobs
                ):
                    votes_by_criterion[index].append(vote_result)
        return votes_by_criterion

    def retry_content_errors(
        current: list[list[dict[str, Any]]], phase_prefix: str
    ) -> list[list[dict[str, Any]]]:
        if not judge_committee:
            return current
        for attempt in range(1, committee_error_retries + 1):
            jobs: list[tuple[int, int]] = []
            for index, vote_results in enumerate(current):
                by_name = {
                    str((vote.get("judge") or {}).get("name")): vote
                    for vote in vote_results
                }
                for spec_index, spec in enumerate(specs):
                    if by_name.get(spec.name, {}).get("verdict") == "error":
                        jobs.append((index, spec_index))
            if not jobs:
                break
            retried = run_content_jobs(jobs, f"{phase_prefix}-error-retry-{attempt}")
            for index, replacements in enumerate(retried):
                if not replacements:
                    continue
                replacement_by_name = {
                    str((vote.get("judge") or {}).get("name")): vote
                    for vote in replacements
                }
                current[index] = [
                    replacement_by_name.get(
                        str((vote.get("judge") or {}).get("name")), vote
                    )
                    for vote in current[index]
                ]
        return current

    if adaptive and not judge_committee and votes > 1:
        first_votes = run_content_jobs(
            [(index, 0) for index in range(len(criteria))], "content-r1"
        )
        escalate = [
            index
            for index, vote_results in enumerate(first_votes)
            if vote_results[0].get("verdict") != "pass"
        ]
        extra_jobs = [
            (index, spec_index)
            for index in escalate
            for spec_index in range(1, len(specs))
        ]
        extra_votes = (
            run_content_jobs(extra_jobs, "content-r1")
            if extra_jobs
            else [[] for _ in criteria]
        )
        votes_by_criterion = [
            first + extra for first, extra in zip(first_votes, extra_votes)
        ]
    else:
        votes_by_criterion = run_content_jobs(
            [
                (index, spec_index)
                for index in range(len(criteria))
                for spec_index in range(len(specs))
            ],
            "content-r1",
        )

    if judge_committee:
        votes_by_criterion = retry_content_errors(votes_by_criterion, "content-r1")
        second_votes_by_criterion: list[list[dict[str, Any]]] = [
            [] for _ in criteria
        ]
        content_conflict_indices: set[int] = set()
        style_conflict_indices: set[int] = set()
        if committee_conflict_recheck:
            content_conflict_indices = {
                index
                for index, vote_results in enumerate(votes_by_criterion)
                if needs_committee_recheck(vote_results)
            }
            if combined_style:
                style_conflict_indices = {
                    index
                    for index in style_eligible_indices
                    if needs_committee_recheck(
                        [
                            vote["_combined_style_vote"]
                            for vote in votes_by_criterion[index]
                        ]
                    )
                }
            conflict_indices = sorted(
                content_conflict_indices | style_conflict_indices
            )
            if conflict_indices:
                second_votes_by_criterion = run_content_jobs(
                    [
                        (index, spec_index)
                        for index in conflict_indices
                        for spec_index in range(len(specs))
                    ],
                    "content-r2",
                )
                second_votes_by_criterion = retry_content_errors(
                    second_votes_by_criterion, "content-r2"
                )
        results = []
        for index, (criterion, first_votes, second_votes) in enumerate(
            zip(criteria, votes_by_criterion, second_votes_by_criterion)
        ):
            results.append(
                finalize_committee_rounds(
                    criterion,
                    first_votes,
                    second_votes
                    if index in content_conflict_indices and second_votes
                    else None,
                )
            )
    else:
        content_conflict_indices = set()
        style_conflict_indices = set()
        second_votes_by_criterion = [[] for _ in criteria]
        results = [
            aggregate_votes(criterion, vote_results)
            for criterion, vote_results in zip(criteria, votes_by_criterion)
        ]

    style_results: list[dict[str, Any]] | None = None
    if style_evaluation:
        eligible_indices = style_eligible_indices

        if combined_style:
            first_style_votes = {
                index: [
                    vote["_combined_style_vote"]
                    for vote in votes_by_criterion[index]
                ]
                for index in eligible_indices
            }
            second_style_votes: dict[int, list[dict[str, Any]]] = {
                index: [] for index in eligible_indices
            }
            for index in style_conflict_indices:
                extracted = []
                for content_vote_result in second_votes_by_criterion[index]:
                    style_vote_result = dict(
                        content_vote_result["_combined_style_vote"]
                    )
                    if index not in content_conflict_indices:
                        # This shared recheck call is not used by the content result;
                        # account its request usage exactly once on the style result.
                        style_vote_result["usage"] = content_vote_result.get(
                            "usage", {}
                        )
                    extracted.append(style_vote_result)
                second_style_votes[index] = extracted
            if judge_committee:
                style_results = [
                    finalize_committee_rounds(
                        criteria[index],
                        first_style_votes[index],
                        second_style_votes[index]
                        if index in style_conflict_indices
                        and second_style_votes[index]
                        else None,
                    )
                    for index in eligible_indices
                ]
            else:
                style_results = [
                    aggregate_votes(criteria[index], first_style_votes[index])
                    for index in eligible_indices
                ]
        else:
            content_by_id = {result["id"]: result for result in results}

            def style_vote(
                job: tuple[int, int], phase: str
            ) -> tuple[int, dict[str, Any]]:
                index, spec_index = job
                spec = specs[spec_index]
                client, use_chat = clients[spec_index]
                criterion = criteria[index]
                agent_output = load_agent_output(submission, criterion)
                vote = cached_judge_vote(
                    cache_dir=vote_cache_dir,
                    phase=phase,
                    client=client,
                    spec=spec,
                    prompt=style_judge_prompt(
                        task, agent_output, criterion, content_by_id[criterion["id"]]
                    ),
                    criterion=criterion,
                    use_chat=use_chat,
                )
                return index, add_judge_metadata(vote, spec)

            def run_style_jobs(
                jobs: list[tuple[int, int]], phase: str
            ) -> dict[int, list[dict[str, Any]]]:
                collected: dict[int, list[dict[str, Any]]] = {
                    index: [] for index in eligible_indices
                }
                for spec_index, spec in enumerate(specs):
                    spec_jobs = [job for job in jobs if job[1] == spec_index]
                    if not spec_jobs:
                        continue
                    workers = spec.parallel or parallel
                    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
                        for index, vote_result in pool.map(
                            lambda job: style_vote(job, phase), spec_jobs
                        ):
                            collected[index].append(vote_result)
                return collected

            def retry_style_errors(
                current: dict[int, list[dict[str, Any]]], phase_prefix: str
            ) -> dict[int, list[dict[str, Any]]]:
                if not judge_committee:
                    return current
                for attempt in range(1, committee_error_retries + 1):
                    jobs: list[tuple[int, int]] = []
                    for index, vote_results in current.items():
                        by_name = {
                            str((vote.get("judge") or {}).get("name")): vote
                            for vote in vote_results
                        }
                        for spec_index, spec in enumerate(specs):
                            if by_name.get(spec.name, {}).get("verdict") == "error":
                                jobs.append((index, spec_index))
                    if not jobs:
                        break
                    retried = run_style_jobs(
                        jobs, f"{phase_prefix}-error-retry-{attempt}"
                    )
                    for index, replacements in retried.items():
                        if not replacements:
                            continue
                        replacement_by_name = {
                            str((vote.get("judge") or {}).get("name")): vote
                            for vote in replacements
                        }
                        current[index] = [
                            replacement_by_name.get(
                                str((vote.get("judge") or {}).get("name")), vote
                            )
                            for vote in current[index]
                        ]
                return current

            style_jobs = [
                (index, spec_index)
                for index in eligible_indices
                for spec_index in range(len(specs))
            ]
            style_votes = run_style_jobs(style_jobs, "style-r1")
            if judge_committee:
                style_votes = retry_style_errors(style_votes, "style-r1")
                second_style_votes = {
                    index: [] for index in eligible_indices
                }
                if committee_conflict_recheck:
                    conflict_indices = [
                        index
                        for index, vote_results in style_votes.items()
                        if needs_committee_recheck(vote_results)
                    ]
                    if conflict_indices:
                        second_style_votes = run_style_jobs(
                            [
                                (index, spec_index)
                                for index in conflict_indices
                                for spec_index in range(len(specs))
                            ],
                            "style-r2",
                        )
                        second_style_votes = retry_style_errors(
                            second_style_votes, "style-r2"
                        )
                style_results = [
                    finalize_committee_rounds(
                        criteria[index],
                        style_votes[index],
                        second_style_votes[index] or None,
                    )
                    for index in eligible_indices
                ]
            else:
                style_results = [
                    aggregate_votes(criteria[index], style_votes[index])
                    for index in eligible_indices
                ]

    return assemble_scores(
        task_dir=task_dir,
        submission=submission,
        rubric_path=rubric_path,
        task=task,
        criteria=criteria,
        results=results,
        judge_model=judge_model,
        api_base=api_base,
        reasoning_effort=reasoning_effort,
        votes=len(specs),
        adaptive=adaptive,
        judge_committee=specs if judge_committee else None,
        style_results=style_results,
        style_evaluation_mode=(
            "combined" if combined_style else "separate"
        )
        if style_evaluation
        else None,
        committee_conflict_recheck=committee_conflict_recheck if judge_committee else False,
        committee_error_retries=committee_error_retries if judge_committee else 0,
    )


def assemble_scores(
    *,
    task_dir: pathlib.Path,
    submission: pathlib.Path,
    rubric_path: pathlib.Path,
    task: dict[str, Any],
    criteria: list[dict[str, Any]],
    results: list[dict[str, Any]],
    judge_model: str,
    api_base: str,
    reasoning_effort: str | None,
    votes: int,
    adaptive: bool,
    judge_committee: list[JudgeSpec] | None = None,
    style_results: list[dict[str, Any]] | None = None,
    style_evaluation_mode: str | None = None,
    committee_conflict_recheck: bool = False,
    committee_error_retries: int = 0,
) -> dict[str, Any]:
    """Build the scores.json payload from per-criterion aggregated results.

    Shared by the synchronous evaluate() path and the Batch-API judging path so
    both produce byte-identical score files.
    """
    criteria_by_id = {criterion["id"]: criterion for criterion in criteria}

    def make_breakdown(key_of: Any) -> dict[str, dict[str, Any]]:
        groups: dict[str, dict[str, Any]] = {}
        for result in results:
            criterion = criteria_by_id.get(result["id"], {})
            tags = criterion.get("analysis_tags") or {}
            key = key_of(criterion, tags) or "untagged"
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
    has_criticality = any(criterion.get("criticality") in (1, 2, 3) for criterion in criteria)
    criticality_labels = {3: "3 (ergebnistragend)", 2: "2 (wichtig)", 1: "1 (eher unwichtig)"}

    n_passed = sum(1 for result in results if result["verdict"] == "pass")
    n_errors = sum(1 for result in results if result["verdict"] == "error")
    n_unresolved = sum(1 for result in results if result.get("resolution") == "unresolved")
    n_criteria = len(results)
    all_pass = n_criteria > 0 and n_passed == n_criteria and n_unresolved == 0
    n_criteria_with_error_votes = sum(
        1 for result in results if (result.get("vote_counts") or {}).get("error", 0) > 0
    )
    agreements = [result["judge_agreement"] for result in results if result["vote_counts"]["pass"] + result["vote_counts"]["fail"] > 0]
    content_judge_usage_total: dict[str, int] = {}
    for result in results:
        for key, value in (result.get("usage") or {}).items():
            if isinstance(value, int):
                content_judge_usage_total[key] = content_judge_usage_total.get(key, 0) + value

    style_judge_usage_total: dict[str, int] = {}
    for result in style_results or []:
        for key, value in (result.get("usage") or {}).items():
            if isinstance(value, int):
                style_judge_usage_total[key] = style_judge_usage_total.get(key, 0) + value

    judge_usage_total = dict(content_judge_usage_total)
    for key, value in style_judge_usage_total.items():
        judge_usage_total[key] = judge_usage_total.get(key, 0) + value

    weighted_total = 0
    weighted_passed = 0
    for result in results:
        criterion = criteria_by_id.get(result["id"], {})
        weight = criterion.get("criticality")
        weight = weight if weight in (1, 2, 3) else 1
        weighted_total += weight
        if result["verdict"] == "pass":
            weighted_passed += weight

    style_n_eligible = len(style_results or [])
    style_n_passed = sum(1 for result in style_results or [] if result["verdict"] == "pass")
    style_n_errors = sum(1 for result in style_results or [] if result["verdict"] == "error")
    style_n_unresolved = sum(
        1 for result in style_results or [] if result.get("resolution") == "unresolved"
    )
    style_score = None
    if style_results is not None:
        style_score = {
            "n_passed": style_n_passed,
            "n_eligible": style_n_eligible,
            "n_errors": style_n_errors,
            "n_unresolved": style_n_unresolved,
            "pass_rate": style_n_passed / style_n_eligible if style_n_eligible else 0.0,
            "denominator_rule": (
                "all application/argumentation criteria regardless of content verdict; "
                "untagged legacy criteria remain eligible"
            ),
        }

    serialized_committee = [spec.as_dict() for spec in judge_committee] if judge_committee else None

    def vote_breakdown(items: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
        breakdown: dict[str, dict[str, int]] = {}
        for item in items:
            for vote in item.get("votes") or []:
                judge = vote.get("judge") or {}
                name = judge.get("name") or judge.get("model") or "unknown"
                counts = breakdown.setdefault(
                    str(name), {"pass": 0, "fail": 0, "error": 0, "cache_hits": 0}
                )
                verdict = vote.get("verdict")
                if verdict in ("pass", "fail", "error"):
                    counts[verdict] += 1
                if vote.get("cache_hit"):
                    counts["cache_hits"] += 1
        return breakdown

    return {
        "schema_version": "0.2",
        "evaluator": "rubric",
        "task": {
            "path": str(task_dir),
            "title": task.get("title"),
        },
        "submission": str(submission),
        "rubric": str(rubric_path),
        "judge_model": "committee" if serialized_committee else judge_model,
        "judge_api_base": "mixed" if serialized_committee else api_base,
        "judge_reasoning_effort": None if serialized_committee else reasoning_effort,
        "judge_committee": serialized_committee,
        "votes_per_criterion": votes,
        "adaptive_voting": adaptive,
        "committee_conflict_recheck": committee_conflict_recheck,
        "committee_error_retries": committee_error_retries,
        "scored_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "score": 1.0 if all_pass else 0.0,
        "all_pass": all_pass,
        "n_criteria": n_criteria,
        "n_passed": n_passed,
        "n_errors": n_errors,
        "n_criteria_with_error_votes": n_criteria_with_error_votes,
        "n_unresolved": n_unresolved,
        "criterion_pass_rate": n_passed / n_criteria if n_criteria else 0.0,
        "content_score": {
            "n_passed": n_passed,
            "n_criteria": n_criteria,
            "n_errors": n_errors,
            "n_unresolved": n_unresolved,
            "pass_rate": n_passed / n_criteria if n_criteria else 0.0,
        },
        "criticality_weighted_content_score": {
            "points_earned": weighted_passed,
            "points_available": weighted_total,
            "pass_rate": weighted_passed / weighted_total if weighted_total else 0.0,
            "weights": {"criticality_3": 3, "criticality_2": 2, "criticality_1": 1},
            "status": "diagnostic_only",
        },
        "style_score": style_score,
        "style_evaluation_mode": style_evaluation_mode,
        "content_votes_by_judge": vote_breakdown(results),
        "style_votes_by_judge": vote_breakdown(style_results or []) if style_results is not None else None,
        "mean_judge_agreement": round(sum(agreements) / len(agreements), 3) if agreements else 0.0,
        "n_unanimous": sum(1 for result in results if result["judge_agreement"] == 1.0),
        "breakdown_by_station": make_breakdown(lambda _c, tags: (tags.get("station_path") or [None])[0]) if has_tags else None,
        "breakdown_by_outline": make_breakdown(lambda _c, tags: " › ".join(tags.get("station_path", [])[:2]) or None) if has_tags else None,
        "breakdown_by_function": make_breakdown(lambda _c, tags: tags.get("function")) if has_tags else None,
        "breakdown_by_criticality": make_breakdown(lambda c, _tags: criticality_labels.get(c.get("criticality"))) if has_criticality else None,
        "judge_usage_total": judge_usage_total,
        "content_judge_usage_total": content_judge_usage_total,
        "style_judge_usage_total": style_judge_usage_total if style_results is not None else None,
        "criteria_results": results,
        "style_results": style_results,
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
    rubric_override = args.rubric.resolve() if args.rubric else None
    rubric_path, criteria = load_rubric(task_dir, rubric_override)
    criteria = select_criteria(criteria, args.criterion_id)
    reasoning_effort = None if args.reasoning_effort.lower() == "none" else args.reasoning_effort
    api_base = args.judge_api_base
    committee = load_judge_committee(args.judge_committee) if args.judge_committee else None
    vote_cache_dir = args.vote_cache_dir.resolve() if args.vote_cache_dir else None
    if committee and args.votes != 1:
        raise SystemExit("--judge-committee cannot be combined with --votes other than 1.")
    if committee and args.adaptive:
        raise SystemExit("--judge-committee cannot be combined with --adaptive.")
    if args.dry_run:
        print(f"Task: {task.get('title', task_dir.name)}")
        print(f"Submission: {submission}")
        print(f"Rubric: {rubric_path}")
        if committee:
            print("Judge committee:")
            for spec in committee:
                print(
                    f"  {spec.name}: {spec.model} @ {spec.api_base} "
                    f"(effort {spec.reasoning_effort}, key {api_key_env_for(spec.api_base)})"
                )
            print(f"Votes per criterion: {len(committee)} (one per committee member)")
        else:
            print(f"Judge model: {args.judge_model}")
            print(f"Judge endpoint: {api_base} (key: {api_key_env_for(api_base)})")
            print(f"Judge reasoning effort: {reasoning_effort}")
            print(f"Votes per criterion: {max(1, args.votes)}")
        if args.style_evaluation:
            style_mode = "separate" if args.separate_style_calls else "combined"
        else:
            style_mode = "disabled"
        print(f"Style evaluation: {style_mode}")
        print(f"Vote cache: {vote_cache_dir if vote_cache_dir else 'disabled'}")
        print(f"Criteria: {len(criteria)}")
        print(f"Parallel judge calls: {args.parallel}")
        print("No API calls made.")
        return 0

    endpoints = [spec.api_base for spec in committee] if committee else [api_base]
    for endpoint in sorted(set(endpoints)):
        key_env = api_key_env_for(endpoint)
        if not os.environ.get(key_env):
            raise SystemExit(
                f"{key_env} is not set (needed for judge endpoint {endpoint}). Put it in .env."
            )

    scores = evaluate(
        task_dir=task_dir,
        submission=submission,
        judge_model=args.judge_model,
        parallel=args.parallel,
        reasoning_effort=reasoning_effort,
        votes=args.votes,
        adaptive=args.adaptive,
        api_base=api_base,
        rubric_override=rubric_override,
        judge_committee=committee,
        style_evaluation=args.style_evaluation,
        combine_content_and_style=not args.separate_style_calls,
        vote_cache_dir=vote_cache_dir,
        criterion_ids=args.criterion_id,
        committee_conflict_recheck=args.committee_conflict_recheck,
        committee_error_retries=args.committee_error_retries,
    )
    scores_path = write_scores(submission, scores, args.output)
    print(f"{scores['n_passed']}/{scores['n_criteria']} criteria passed")
    for breakdown_key, label in [
        ("breakdown_by_station", "By station"),
        ("breakdown_by_function", "By function"),
        ("breakdown_by_criticality", "By criticality"),
    ]:
        breakdown = scores.get(breakdown_key)
        if breakdown:
            print(f"{label}:")
            for name, group in sorted(breakdown.items(), key=lambda item: -item[1]["n_criteria"]):
                print(f"  {name}: {group['n_passed']}/{group['n_criteria']} ({group['pass_rate']:.0%})")
    weighted = scores["criticality_weighted_content_score"]
    print(
        "Criticality-weighted content (diagnostic): "
        f"{weighted['points_earned']}/{weighted['points_available']} ({weighted['pass_rate']:.0%})"
    )
    if scores["content_score"].get("n_unresolved"):
        print(f"Unresolved content criteria: {scores['content_score']['n_unresolved']}")
    if scores.get("style_score") is not None:
        style = scores["style_score"]
        print(
            f"Gutachtenstil: {style['n_passed']}/{style['n_eligible']} stilrelevante Kriterien "
            f"({style['pass_rate']:.0%})"
        )
        if style.get("n_unresolved"):
            print(f"Unresolved style criteria: {style['n_unresolved']}")
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
