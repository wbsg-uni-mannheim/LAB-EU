#!/usr/bin/env python3
"""Generate Boolean LLM-judge rubrics from LAB-EU human solutions.

Pipeline: atomize the solution, generate candidate criteria from three
generator roles (doctrine, fact grounding, adversary), prune the merged pool,
then calibrate the pruned rubric by judging the gold solution against it with
multiple votes per criterion. Criteria the gold solution does not unanimously
pass are refined (or dropped) and re-judged. Only calibrated criteria reach
evals/rubric.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

DEFAULT_MODEL = "gpt-5.6-sol"
DEFAULT_API_BASE = "https://api.openai.com/v1"
DEFAULT_REASONING_EFFORT = "high"
DEFAULT_JUDGE_REASONING_EFFORT = "medium"
DEFAULT_CALIBRATION_VOTES = 3
DEFAULT_MAX_CALIBRATION_ROUNDS = 2
DEFAULT_JUDGE_PARALLEL = 4
MAX_FILE_CHARS = 120_000
MAX_TOTAL_CHARS = 300_000
CANDIDATE_ROLES = [
    ("doctrine", "DOC"),
    ("fact_grounding", "FACT"),
    ("adversary", "ADV"),
]
FUNCTION_TAGS = [
    "structure",
    "legal_basis",
    "rule_statement",
    "application",
    "argumentation",
    "conclusion",
    "form_citation",
]
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO_ROOT / "prompts" / "rubric_generation"

sys.path.insert(0, str(REPO_ROOT))

from evaluation.run import (  # noqa: E402
    JudgeSpec,
    call_judge,
    judge_prompt as build_judge_prompt,
    load_judge_committee,
    make_client as make_judge_client,
)
from scripts.outline_util import UE_ID, index_outline, normalize_outline, with_ue_node  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a calibrated draft LAB-EU rubric from a task directory and human solution."
    )
    parser.add_argument(
        "task_dir",
        type=pathlib.Path,
        help="Path to a task directory containing task.json, documents/, and evals/.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_RUBRIC_MODEL", DEFAULT_MODEL),
        help=f"OpenAI model to use. Defaults to {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--solution",
        action="append",
        type=pathlib.Path,
        help="Solution file to use. Can be passed multiple times. Defaults to Markdown/text files in evals/.",
    )
    parser.add_argument(
        "--write-final",
        action="store_true",
        help="Also write the calibrated rubric to evals/rubric.json.",
    )
    parser.add_argument(
        "--artifact-suffix",
        default="",
        help=(
            "Optional safe filename suffix for comparison runs, e.g. 'sol' writes "
            "evals/rubric.generated.sol.json and, with --write-final, evals/rubric.sol.json."
        ),
    )
    parser.add_argument(
        "--reasoning-effort",
        default=os.environ.get("OPENAI_RUBRIC_REASONING_EFFORT", DEFAULT_REASONING_EFFORT),
        help=(
            "Reasoning effort for the generator model (e.g. low, medium, high). "
            f"Use 'none' to omit the parameter. Defaults to {DEFAULT_REASONING_EFFORT}."
        ),
    )
    parser.add_argument(
        "--judge-model",
        default=os.environ.get("OPENAI_JUDGE_MODEL", ""),
        help="Judge model for calibration. Defaults to --model.",
    )
    parser.add_argument(
        "--judge-reasoning-effort",
        default=os.environ.get("OPENAI_JUDGE_REASONING_EFFORT", DEFAULT_JUDGE_REASONING_EFFORT),
        help=f"Reasoning effort for calibration judge calls. Defaults to {DEFAULT_JUDGE_REASONING_EFFORT}.",
    )
    parser.add_argument(
        "--calibration-votes",
        type=int,
        default=DEFAULT_CALIBRATION_VOTES,
        help=f"Judge votes per criterion during calibration. Defaults to {DEFAULT_CALIBRATION_VOTES}.",
    )
    parser.add_argument(
        "--calibration-committee",
        type=pathlib.Path,
        default=None,
        help=(
            "JSON judge committee. Each configured model casts one calibration vote per criterion; "
            "this replaces repeated votes from --judge-model."
        ),
    )
    parser.add_argument(
        "--max-calibration-rounds",
        type=int,
        default=DEFAULT_MAX_CALIBRATION_ROUNDS,
        help=(
            "Judge/refine rounds. Criteria that still fail on the gold solution in the last round "
            f"are dropped. Defaults to {DEFAULT_MAX_CALIBRATION_ROUNDS}."
        ),
    )
    parser.add_argument(
        "--skip-calibration",
        action="store_true",
        help="Skip the calibration gate (not recommended; the rubric is then untested).",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=DEFAULT_JUDGE_PARALLEL,
        help=f"Parallel judge calls during calibration. Defaults to {DEFAULT_JUDGE_PARALLEL}.",
    )
    parser.add_argument(
        "--retag-only",
        action="store_true",
        help=(
            "Do NOT generate anything: load the frozen criteria from evals/rubric.json, "
            "run only extract_outline + tag_criteria, and write the updated tags/outline back. "
            "Never touches candidates, pruning, or calibration."
        ),
    )
    parser.add_argument(
        "--skip-tagging",
        action="store_true",
        help="Skip the non-scoring analysis-tag pass (function + station per criterion).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help=(
            "Disable the step cache. By default every model call is cached under "
            "evals/.rubric-cache/ keyed on its exact request, so a failed or repeated run "
            "reuses completed steps instead of paying for them again."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and validate local inputs, then print the planned API calls without calling OpenAI.",
    )
    return parser.parse_args()


def cache_key(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:24]


def cache_read(cache_dir: pathlib.Path | None, step: str, key: str) -> dict[str, Any] | None:
    if cache_dir is None:
        return None
    path = cache_dir / f"{step}-{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def cache_write(cache_dir: pathlib.Path | None, step: str, key: str, value: dict[str, Any]) -> None:
    if cache_dir is None:
        return
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{step}-{key}.json"
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


def read_text(path: pathlib.Path, max_chars: int) -> tuple[str, bool]:
    data = path.read_text(encoding="utf-8", errors="replace")
    truncated = len(data) > max_chars
    if truncated:
        data = data[:max_chars] + "\n\n[TRUNCATED]\n"
    return data, truncated


def load_env_files(task_dir: pathlib.Path) -> None:
    for candidate in [pathlib.Path.cwd() / ".env", task_dir.parent / ".env", task_dir / ".env"]:
        if candidate.exists():
            load_dotenv(candidate, override=False)


def discover_solution_files(task_dir: pathlib.Path, explicit: list[pathlib.Path] | None) -> list[pathlib.Path]:
    if explicit:
        return [(p if p.is_absolute() else pathlib.Path.cwd() / p).resolve() for p in explicit]

    evals_dir = task_dir / "evals"
    if not evals_dir.exists():
        raise SystemExit(f"No evals/ directory found under {task_dir}")

    files = [
        p
        for p in sorted(evals_dir.iterdir())
        if p.is_file()
        and not p.name.startswith("rubric")
        and p.name != "scores.json"
        and p.suffix.lower() in {".md", ".txt", ".json"}
    ]
    if not files:
        raise SystemExit(f"No solution files found in {evals_dir}; pass --solution explicitly.")
    return files


def collect_file_bundle(
    task_dir: pathlib.Path,
    solution_files: list[pathlib.Path],
    max_file_chars: int,
    max_total_chars: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    files: list[dict[str, Any]] = []
    used_chars = 0

    def add_file(path: pathlib.Path, role: str) -> None:
        nonlocal used_chars
        text, truncated_by_file = read_text(path, max_file_chars)
        remaining = max_total_chars - used_chars
        if remaining <= 0:
            warnings.append(f"Skipped {path}: max total character budget reached.")
            return
        truncated_by_total = len(text) > remaining
        if truncated_by_total:
            text = text[:remaining] + "\n\n[TRUNCATED_BY_TOTAL_BUDGET]\n"
        used_chars += len(text)
        try:
            rel = path.relative_to(task_dir)
        except ValueError:
            rel = path
        if truncated_by_file or truncated_by_total:
            severity = (
                "Rubric will be generated from a PARTIAL ground truth."
                if role == "solution"
                else "Model sees only part of this document."
            )
            warnings.append(f"Truncated {rel} ({role}). {severity}")
        files.append(
            {
                "path": str(rel),
                "role": role,
                "truncated": truncated_by_file or truncated_by_total,
                "content": text,
            }
        )
        lowered = text.lower()
        incomplete_markers = (
            "please complete",
            "only a part of the solution",
            "bitte vervoll",
        )
        completion_markers = (
            "completed manually",
            "vollständig",
            "complete solution",
        )
        if role == "solution" and any(m in lowered for m in incomplete_markers) and not any(
            m in lowered for m in completion_markers
        ):
            warnings.append(f"Solution file {rel} appears to be incomplete.")

    documents_dir = task_dir / "documents"
    if documents_dir.exists():
        for path in sorted(p for p in documents_dir.rglob("*") if p.is_file()):
            add_file(path, "document")

    for path in solution_files:
        add_file(path, "solution")

    return files, warnings


def load_task(task_dir: pathlib.Path) -> dict[str, Any]:
    task_path = task_dir / "task.json"
    if not task_path.exists():
        raise SystemExit(f"No task.json found at {task_path}")
    with task_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def make_client(api_base: str) -> OpenAI:
    if api_base == DEFAULT_API_BASE:
        return OpenAI()
    return OpenAI(base_url=api_base)


def build_api_request(
    *,
    model: str,
    system: str,
    user: str,
    reasoning_effort: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Build the canonical Responses request and its local step-cache key."""
    key = cache_key(
        {
            "model": model,
            "system": system,
            "user": user,
            "reasoning_effort": reasoning_effort,
        }
    )
    request: dict[str, Any] = {
        "model": model,
        "instructions": system,
        "input": user,
        "text": {"format": {"type": "json_object"}},
    }
    if reasoning_effort:
        request["reasoning"] = {"effort": reasoning_effort}
    return key, request


def api_call(
    *,
    client: OpenAI,
    model: str,
    system: str,
    user: str,
    required_keys: set[str],
    reasoning_effort: str | None = None,
    label: str = "",
    cache_dir: pathlib.Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    step = re.sub(r"[^A-Za-z0-9_.-]+", "_", label) or "call"
    key, request = build_api_request(
        model=model,
        system=system,
        user=user,
        reasoning_effort=reasoning_effort,
    )
    cached = cache_read(cache_dir, step, key)
    if cached is not None:
        print(f"tokens[{label}]: cache hit, no API call", file=sys.stderr)
        return cached["parsed"], cached["response"]

    # No max_output_tokens: the model may use its full output budget. Token
    # usage is logged per call and recorded in the generated audit file, so
    # caps can be reintroduced later if costs demand it.
    try:
        response = client.responses.create(**request)
    except OpenAIError as exc:
        raise RuntimeError(f"OpenAI API request failed: {exc}") from exc

    response_data = response.model_dump(mode="json")
    if label:
        usage = usage_summary(response_data)
        reasoning_tokens = (usage.get("output_tokens_details") or {}).get("reasoning_tokens")
        cached_tokens = (usage.get("input_tokens_details") or {}).get("cached_tokens")
        print(
            f"tokens[{label}]: input={usage.get('input_tokens')} (cached={cached_tokens}) "
            f"output={usage.get('output_tokens')} (reasoning={reasoning_tokens})",
            file=sys.stderr,
        )
    if response_data.get("status") == "incomplete":
        details = response_data.get("incomplete_details") or {}
        raise RuntimeError(
            f"Model response is incomplete (reason: {details.get('reason', 'unknown')}); "
            "the model hit its own output limit."
        )
    try:
        parsed = json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Model returned invalid JSON: {response.output_text[:2000]}") from exc
    missing = sorted(required_keys - set(parsed))
    if missing:
        raise RuntimeError(f"Model JSON is missing required keys: {', '.join(missing)}")
    cache_write(
        cache_dir,
        step,
        key,
        {"parsed": parsed, "response": {"usage": response_data.get("usage")}},
    )
    return parsed, response_data


def usage_summary(response_data: dict[str, Any]) -> dict[str, Any]:
    usage = response_data.get("usage") or {}
    keep = [
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "input_tokens_details",
        "output_tokens_details",
    ]
    return {key: usage[key] for key in keep if key in usage}


def task_bundle_json(task_dir: pathlib.Path, task: dict[str, Any], files: list[dict[str, Any]]) -> str:
    bundle = {
        "task_dir": str(task_dir),
        "task_json": task,
        "files": files,
    }
    return json.dumps(bundle, ensure_ascii=False, indent=2)


def read_prompt_template(name: str) -> str:
    path = PROMPTS_DIR / name
    if not path.exists():
        raise SystemExit(f"Missing prompt template: {path}")
    return path.read_text(encoding="utf-8")


def prompt_pair(name: str) -> tuple[str, str]:
    return (
        read_prompt_template(f"{name}.system.txt"),
        read_prompt_template(f"{name}.user.txt"),
    )


def build_user_payload(base_instruction: str, payload: dict[str, Any]) -> str:
    return base_instruction + "\n\nTASK/RUBRIC DATA JSON:\n" + json.dumps(
        payload, ensure_ascii=False, indent=2
    )


def validate_criteria(criteria: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not criteria:
        errors.append("Final rubric contains no criteria.")
    seen: set[str] = set()
    for index, criterion in enumerate(criteria, start=1):
        cid = criterion.get("id", f"<missing-{index}>")
        if cid in seen:
            errors.append(f"Duplicate criterion id: {cid}")
        seen.add(cid)
        match = criterion.get("match_criteria", "")
        if not has_boolean_labels(match):
            errors.append(f"{cid} does not contain explicit Boolean pass/fail labels.")
        # Untagged pipelines still carry the internal keep/drop marker "must_pass";
        # after tagging, criticality is the reviewer-facing importance tier 1-3.
        if criterion.get("criticality") not in (1, 2, 3, "must_pass"):
            errors.append(f"{cid} has invalid criticality {criterion.get('criticality')!r}.")
    return errors


def validate_pruning_coverage(
    pruned: dict[str, Any], atoms: dict[str, Any]
) -> list[str]:
    """Verify that every core atom is either covered or explicitly dispositioned."""
    criteria = pruned.get("criteria") or []
    core_ids = {
        str(atom.get("id"))
        for atom in (atoms.get("atoms") or [])
        if isinstance(atom, dict) and atom.get("expectation") == "core" and atom.get("id")
    }
    covered_ids = {
        str(atom_id)
        for criterion in criteria
        if isinstance(criterion, dict)
        for atom_id in (criterion.get("derived_from_atoms") or [])
    }
    audit = pruned.get("coverage_audit")
    errors: list[str] = []
    if not isinstance(audit, dict):
        return ["Pruning output is missing coverage_audit."]
    raw_uncovered = audit.get("uncovered_core_atoms")
    if not isinstance(raw_uncovered, list):
        return ["coverage_audit.uncovered_core_atoms must be a list."]

    audited_ids: list[str] = []
    for index, item in enumerate(raw_uncovered, start=1):
        if not isinstance(item, dict):
            errors.append(f"Coverage audit entry {index} must be an object.")
            continue
        atom_id = str(item.get("id", "")).strip()
        reason = str(item.get("reason", "")).strip()
        if not atom_id or not reason:
            errors.append(f"Coverage audit entry {index} needs id and reason.")
            continue
        audited_ids.append(atom_id)

    duplicates = sorted({atom_id for atom_id in audited_ids if audited_ids.count(atom_id) > 1})
    if duplicates:
        errors.append(f"Coverage audit repeats core atoms: {', '.join(duplicates)}")
    audited = set(audited_ids)
    unknown = sorted(audited - core_ids)
    if unknown:
        errors.append(f"Coverage audit references non-core or unknown atoms: {', '.join(unknown)}")
    both = sorted(audited & covered_ids)
    if both:
        errors.append(f"Core atoms are both covered and audited as uncovered: {', '.join(both)}")
    missing = sorted(core_ids - covered_ids - audited)
    if missing:
        errors.append(f"Core atoms lack a pruning disposition: {', '.join(missing)}")
    return errors


def criticality_distribution_warnings(criteria: list[dict[str, Any]]) -> list[str]:
    """Return reviewer-facing warnings for the agreed 3/2/1-star target.

    The distribution is deliberately a warning rather than a validation error:
    small rubrics and documented legal exceptions still need to be possible.
    """
    tagged = [criterion for criterion in criteria if criterion.get("criticality") in (1, 2, 3)]
    if not tagged:
        return []

    total = len(tagged)
    counts = {
        tier: sum(1 for criterion in tagged if criterion.get("criticality") == tier)
        for tier in (3, 2, 1)
    }
    tier_three_share = counts[3] / total
    tier_two_share = counts[2] / total
    warnings: list[str] = []
    if not 0.10 <= tier_three_share <= 0.15:
        warnings.append(
            f"Tier 3 is {counts[3]}/{total} ({tier_three_share:.1%}); target is about 10-15%."
        )
    if tier_two_share > 0.60:
        warnings.append(
            f"Tier 2 is {counts[2]}/{total} ({tier_two_share:.1%}); target maximum is 60%."
        )
    return warnings


def has_boolean_labels(match_criteria: str) -> bool:
    label_pairs = [
        (r"\bPASS\b", r"\bFAIL\b"),
        (r"(^|[.;:\n]\s*)ERFÜLLT\b|(?<!NICHT )\bERFÜLLT,\s*wenn\b", r"\bNICHT\s+ERFÜLLT\b"),
        (r"(^|[.;:\n]\s*)ERFUELLT\b|(?<!NICHT )\bERFUELLT,\s*wenn\b", r"\bNICHT\s+ERFUELLT\b"),
        (
            r"(^|[.;:\n]\s*)BESTANDEN\b|(?<!NICHT )\bBESTANDEN,\s*wenn\b",
            r"\bNICHT\s+BESTANDEN\b",
        ),
        (r"\bRÉUSSI\b", r"\bÉCHOUÉ\b"),
        (r"\bREUSSI\b", r"\bECHOUE\b"),
        (r"\bWAHR\b", r"\bFALSCH\b"),
        (r"\bTRUE\b", r"\bFALSE\b"),
    ]
    return any(
        re.search(pass_label, match_criteria, re.IGNORECASE)
        and re.search(fail_label, match_criteria, re.IGNORECASE)
        for pass_label, fail_label in label_pairs
    )


def generate_role_candidates(
    *,
    client: OpenAI,
    model: str,
    reasoning_effort: str | None,
    candidate_system: str,
    candidate_user: str,
    role_name: str,
    role_code: str,
    cache_dir: pathlib.Path | None,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    role_text = read_prompt_template(f"roles/{role_name}.txt")
    # Role focus goes at the END of the user message, not into the system prompt:
    # the three role calls then share one long identical prefix (system + full
    # task payload), which OpenAI prompt caching can reuse across the calls.
    parsed, response = api_call(
        client=client,
        model=model,
        system=candidate_system,
        user=candidate_user + "\n\n" + role_text,
        required_keys={"language", "criteria", "generation_notes"},
        reasoning_effort=reasoning_effort,
        label=f"candidates/{role_name}",
        cache_dir=cache_dir,
    )
    for index, criterion in enumerate(parsed.get("criteria", []), start=1):
        criterion["id"] = f"K-{role_code}-{index:03d}"
        criterion["generator_role"] = role_name
    return role_name, parsed, response


def solution_output_text(solution_files: list[pathlib.Path]) -> str:
    sections = []
    for path in solution_files:
        text, _truncated = read_text(path, MAX_FILE_CHARS)
        sections.append(f"## {path.name}\n{text}")
    return "\n\n".join(sections)


def summarize_votes(vote_results: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"pass": 0, "fail": 0, "error": 0}
    for vote in vote_results:
        counts[vote.get("verdict", "error")] = counts.get(vote.get("verdict", "error"), 0) + 1
    return counts


def trimmed_vote(vote: dict[str, Any]) -> dict[str, Any]:
    evidence = [str(item)[:500] for item in (vote.get("evidence") or [])[:3]]
    trimmed = {
        "verdict": vote.get("verdict"),
        "reasoning": str(vote.get("reasoning", ""))[:1000],
        "evidence": evidence,
    }
    if isinstance(vote.get("judge"), dict):
        trimmed["judge"] = vote["judge"]
    return trimmed


def add_usage(total: dict[str, int], usage: dict[str, Any]) -> None:
    for key in ["input_tokens", "output_tokens", "total_tokens", "cached_input_tokens"]:
        if isinstance(usage.get(key), int):
            total[key] = total.get(key, 0) + usage[key]


def judge_criteria_votes(
    *,
    judges: list[tuple[JudgeSpec, OpenAI, bool]],
    task: dict[str, Any],
    task_dir: pathlib.Path,
    solution_output: str,
    criteria: list[dict[str, Any]],
    parallel: int,
    judge_usage: dict[str, int],
    judge_usage_by_member: dict[str, dict[str, int]],
    cache_dir: pathlib.Path | None,
) -> list[list[dict[str, Any]]]:
    jobs = [(index, judge_index) for index in range(len(criteria)) for judge_index in range(len(judges))]

    def run_job(job: tuple[int, int]) -> tuple[int, dict[str, Any]]:
        index, judge_index = job
        spec, client, use_chat = judges[judge_index]
        criterion = criteria[index]
        prompt = build_judge_prompt(task, task_dir, solution_output, criterion)
        key = cache_key(
            {"judge": spec.as_dict(), "prompt": prompt}
        )
        cached = cache_read(cache_dir, "judge", key)
        if cached is not None:
            return index, cached
        try:
            result = call_judge(client, spec.model, prompt, spec.reasoning_effort, use_chat)
        except Exception as exc:  # noqa: BLE001 - one broken judge call must not kill calibration
            result = {"verdict": "error", "reasoning": f"Judge call failed: {exc}", "evidence": [], "usage": {}}
        result["judge"] = spec.as_dict()
        if result.get("verdict") != "error":
            cache_write(cache_dir, "judge", key, result)
        return index, result

    votes_by_criterion: list[list[dict[str, Any]]] = [[] for _ in criteria]
    with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        for index, result in pool.map(run_job, jobs):
            add_usage(judge_usage, result.get("usage") or {})
            judge_name = str((result.get("judge") or {}).get("name", "unknown"))
            add_usage(judge_usage_by_member.setdefault(judge_name, {}), result.get("usage") or {})
            votes_by_criterion[index].append(result)
    return votes_by_criterion


def base_criterion_id(criterion_id: str) -> str:
    return re.sub(r"-S\d+$", "", criterion_id)


def calibrate_rubric(
    *,
    client: OpenAI,
    generator_model: str,
    generator_effort: str | None,
    judges: list[tuple[JudgeSpec, OpenAI, bool]],
    task: dict[str, Any],
    task_dir: pathlib.Path,
    solution_output: str,
    criteria: list[dict[str, Any]],
    max_rounds: int,
    parallel: int,
    cache_dir: pathlib.Path | None,
) -> dict[str, Any]:
    refine_system, refine_user_base = prompt_pair("refine_rubric")
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    rounds_log: list[dict[str, Any]] = []
    refine_usages: list[dict[str, Any]] = []
    judge_usage: dict[str, int] = {}
    judge_usage_by_member: dict[str, dict[str, int]] = {}
    to_test = list(criteria)
    votes = len(judges)

    for round_number in range(1, max_rounds + 1):
        if not to_test:
            break
        print(
            f"Calibration round {round_number}: judging {len(to_test)} criteria "
            f"with {votes} votes each against the gold solution",
            file=sys.stderr,
        )
        votes_by_criterion = judge_criteria_votes(
            judges=judges,
            task=task,
            task_dir=task_dir,
            solution_output=solution_output,
            criteria=to_test,
            parallel=parallel,
            judge_usage=judge_usage,
            judge_usage_by_member=judge_usage_by_member,
            cache_dir=cache_dir,
        )

        round_entries: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        for criterion, vote_results in zip(to_test, votes_by_criterion):
            counts = summarize_votes(vote_results)
            entry: dict[str, Any] = {
                "id": criterion.get("id"),
                "title": criterion.get("title"),
                "vote_counts": counts,
                "votes": [trimmed_vote(vote) for vote in vote_results],
            }
            if counts["pass"] == votes:
                criterion["calibration"] = {
                    "status": "pass",
                    "agreement": f"{counts['pass']}/{votes}",
                    "round": round_number,
                }
                kept.append(criterion)
                entry["action"] = "keep"
            elif round_number == max_rounds:
                if counts["pass"] * 2 > votes:
                    criterion["calibration"] = {
                        "status": "flaky",
                        "agreement": f"{counts['pass']}/{votes}",
                        "round": round_number,
                    }
                    criterion.setdefault("review_notes", []).append(
                        "Kalibrierung: Urteil des Judges nicht einstimmig; Kriterium bei der "
                        "menschlichen Prüfung besonders beachten."
                    )
                    kept.append(criterion)
                    entry["action"] = "keep_flagged"
                else:
                    dropped.append(
                        {
                            "id": criterion.get("id"),
                            "title": criterion.get("title"),
                            "reason": "Gold solution did not pass after refinement (majority fail).",
                            "vote_counts": counts,
                            "criterion": criterion,
                            "by": "calibration",
                        }
                    )
                    entry["action"] = "drop"
            else:
                failures.append({"criterion": criterion, "votes": [trimmed_vote(vote) for vote in vote_results]})
                entry["action"] = "refine"
            round_entries.append(entry)

        rounds_log.append({"round": round_number, "n_tested": len(to_test), "results": round_entries})
        if not failures or round_number == max_rounds:
            break

        print(f"Calibration round {round_number}: refining {len(failures)} criteria", file=sys.stderr)
        refine_payload = {
            "task_json": task,
            "gold_solution": solution_output,
            "kept_criteria_for_context": [
                {"id": criterion.get("id"), "title": criterion.get("title")} for criterion in kept
            ],
            "calibration_failures": failures,
        }
        refined, refine_response = api_call(
            client=client,
            model=generator_model,
            system=refine_system,
            user=build_user_payload(refine_user_base, refine_payload),
            required_keys={"language", "refined_criteria", "dropped_criteria", "refinement_notes"},
            reasoning_effort=generator_effort,
            label=f"refine_rubric/round-{round_number}",
            cache_dir=cache_dir,
        )
        refine_usages.append(usage_summary(refine_response))

        refined_criteria = [c for c in refined.get("refined_criteria", []) if isinstance(c, dict)]
        refiner_dropped = [d for d in refined.get("dropped_criteria", []) if isinstance(d, dict)]
        for item in refiner_dropped:
            dropped.append({**item, "by": "refiner"})

        handled_ids = {base_criterion_id(str(c.get("id", ""))) for c in refined_criteria}
        handled_ids |= {str(d.get("id", "")) for d in refiner_dropped}
        for failure in failures:
            original = failure["criterion"]
            if str(original.get("id", "")) not in handled_ids:
                # The refiner ignored this criterion; re-test the original instead of losing it.
                refined_criteria.append(original)

        for criterion in refined_criteria:
            criterion.setdefault("criticality", "must_pass")
        to_test = refined_criteria

    return {
        "kept": kept,
        "dropped": dropped,
        "rounds": rounds_log,
        "judge_usage": judge_usage,
        "judge_usage_by_member": judge_usage_by_member,
        "refine_usage": refine_usages,
    }


def extract_solution_outline(
    *,
    client: OpenAI,
    model: str,
    reasoning_effort: str | None,
    task: dict[str, Any],
    solution_output: str,
    cache_dir: pathlib.Path | None,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[str]]:
    outline_system, outline_user_base = prompt_pair("extract_outline")
    payload = {
        "task_json": {"title": task.get("title"), "work_type": task.get("work_type")},
        "solution": solution_output,
    }
    parsed, response = api_call(
        client=client,
        model=model,
        system=outline_system,
        user=build_user_payload(outline_user_base, payload),
        required_keys={"language", "outline"},
        reasoning_effort=reasoning_effort,
        label="extract_outline",
        cache_dir=cache_dir,
    )
    nodes, warnings = normalize_outline(parsed.get("outline"))
    if not nodes:
        warnings.append("Outline extraction returned no usable nodes.")
    nodes = with_ue_node(nodes)
    return parsed, response, nodes, warnings


def tag_final_criteria(
    *,
    client: OpenAI,
    model: str,
    reasoning_effort: str | None,
    task: dict[str, Any],
    atoms: dict[str, Any],
    criteria: list[dict[str, Any]],
    outline_nodes: list[dict[str, Any]] | None,
    cache_dir: pathlib.Path | None,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    tag_system, tag_user_base = prompt_pair("tag_criteria")
    payload = {
        "task_json": task,
        "atomization": atoms,
        "criteria": [
            {
                "id": criterion.get("id"),
                "title": criterion.get("title"),
                "match_criteria": criterion.get("match_criteria"),
            }
            for criterion in criteria
        ],
    }
    if outline_nodes:
        payload["outline"] = outline_nodes
    parsed, response = api_call(
        client=client,
        model=model,
        system=tag_system,
        user=build_user_payload(tag_user_base, payload),
        required_keys={"language", "tags"},
        reasoning_effort=reasoning_effort,
        label="tag_criteria",
        cache_dir=cache_dir,
    )
    warnings: list[str] = []
    outline_index = index_outline(outline_nodes) if outline_nodes else {}
    tags_by_id = {
        str(entry.get("id")): entry
        for entry in parsed.get("tags", [])
        if isinstance(entry, dict) and entry.get("id")
    }
    for criterion in criteria:
        entry = tags_by_id.get(str(criterion.get("id")))
        if entry is None:
            warnings.append(f"No analysis tag returned for {criterion.get('id')}.")
            continue
        function = entry.get("function")
        if function not in FUNCTION_TAGS:
            warnings.append(f"{criterion.get('id')}: unknown function tag {function!r}.")
        if outline_index:
            outline_id = str(entry.get("outline_id", "")).strip()
            if outline_id not in outline_index:
                warnings.append(
                    f"{criterion.get('id')}: unknown outline_id {outline_id!r}, assigned to {UE_ID!r}."
                )
                outline_id = UE_ID
            criterion["analysis_tags"] = {
                "function": function,
                "outline_id": outline_id,
                "station_path": outline_index[outline_id]["path_labels"],
            }
        else:
            station_path = entry.get("station_path") or []
            criterion["analysis_tags"] = {
                "function": function,
                "station_path": [str(step) for step in station_path if str(step)],
            }
        criticality = entry.get("criticality")
        if criticality in (1, 2, 3):
            criterion["criticality"] = criticality
        else:
            warnings.append(
                f"{criterion.get('id')}: invalid criticality {criticality!r}, defaulting to 2."
            )
            criterion["criticality"] = 2
    return parsed, response, warnings


def main() -> int:
    args = parse_args()
    task_dir = args.task_dir.resolve()
    load_env_files(task_dir)

    task = load_task(task_dir)
    solution_files = discover_solution_files(task_dir, args.solution)
    files, input_warnings = collect_file_bundle(
        task_dir, solution_files, MAX_FILE_CHARS, MAX_TOTAL_CHARS
    )
    bundle = json.loads(task_bundle_json(task_dir, task, files))

    artifact_suffix = args.artifact_suffix.strip()
    if artifact_suffix and not re.fullmatch(r"[A-Za-z0-9_-]+", artifact_suffix):
        raise SystemExit("--artifact-suffix may contain only letters, digits, '_' and '-'.")
    if args.retag_only and artifact_suffix:
        raise SystemExit("--artifact-suffix is not supported with --retag-only.")
    suffix = f".{artifact_suffix}" if artifact_suffix else ""
    output_path = task_dir / "evals" / f"rubric.generated{suffix}.json"
    final_path = task_dir / "evals" / f"rubric{suffix}.json"

    reasoning_effort = None if args.reasoning_effort.lower() == "none" else args.reasoning_effort
    judge_model = args.judge_model or args.model
    judge_effort = None if args.judge_reasoning_effort.lower() == "none" else args.judge_reasoning_effort
    calibrate = not args.skip_calibration
    calibration_committee = (
        load_judge_committee(args.calibration_committee) if args.calibration_committee else None
    )
    calibration_vote_count = (
        len(calibration_committee) if calibration_committee else max(1, args.calibration_votes)
    )
    cache_dir = None if args.no_cache else task_dir / "evals" / ".rubric-cache"

    # Fail fast on missing prompt templates, including in dry runs.
    atom_system, atom_user_base = prompt_pair("atomize_solution")
    candidate_system, candidate_user_base = prompt_pair("generate_candidate_criteria")
    pruner_system, pruner_user_base = prompt_pair("prune_rubric")
    prompt_pair("refine_rubric")
    prompt_pair("tag_criteria")
    prompt_pair("extract_outline")
    for role_name, _code in CANDIDATE_ROLES:
        read_prompt_template(f"roles/{role_name}.txt")

    if args.dry_run:
        print(f"Task: {task.get('title', task_dir.name)}")
        print(f"Model: {args.model}")
        print(f"Reasoning effort: {reasoning_effort}")
        print(f"Candidate roles: {[name for name, _ in CANDIDATE_ROLES]}")
        print(f"Calibration: {'on' if calibrate else 'off'}")
        if calibrate:
            if calibration_committee:
                print("Calibration committee:")
                for spec in calibration_committee:
                    print(
                        f"- {spec.name}: {spec.model} via {spec.api_base} "
                        f"(effort {spec.reasoning_effort})"
                    )
            else:
                print(f"Calibration judge: {judge_model} (effort {judge_effort})")
            print(f"Calibration votes: {calibration_vote_count}, max rounds: {args.max_calibration_rounds}")
        print(f"Analysis tagging: {'off' if args.skip_tagging else 'on'}")
        print(f"Solution files: {[str(p) for p in solution_files]}")
        print(f"Input files: {len(files)}")
        print(f"Step cache: {cache_dir if cache_dir else 'disabled'}")
        print(f"Output: {output_path}")
        print(f"Write final rubric: {args.write_final}")
        for warning in input_warnings:
            print(f"WARNING: {warning}")
        print(
            "Planned API calls: atomize_solution -> generate_candidates (3 roles) -> prune_candidates"
            + (" -> calibrate/refine loop" if calibrate else "")
            + ("" if args.skip_tagging else " -> extract_outline -> tag_criteria")
        )
        return 0

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set. Put it in the environment or .env.")

    for warning in input_warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    client = make_client(os.environ.get("OPENAI_API_BASE", DEFAULT_API_BASE))
    if calibration_committee:
        calibration_judges = [
            (spec, *make_judge_client(spec.api_base, timeout_seconds=300.0))
            for spec in calibration_committee
        ]
    else:
        calibration_judges = [
            (
                JudgeSpec(
                    name=f"{judge_model}#{vote + 1}",
                    model=judge_model,
                    api_base=os.environ.get("OPENAI_API_BASE", DEFAULT_API_BASE),
                    reasoning_effort=judge_effort,
                ),
                client,
                False,
            )
            for vote in range(calibration_vote_count)
        ]

    if args.retag_only:
        if not final_path.exists():
            raise SystemExit(f"--retag-only needs an existing frozen rubric at {final_path}")
        rubric = json.loads(final_path.read_text(encoding="utf-8"))
        criteria = rubric.get("criteria") or []
        if not criteria:
            raise SystemExit(f"{final_path} contains no criteria.")
        atoms_for_tagging: dict[str, Any] = {}
        if output_path.exists():
            atoms_for_tagging = json.loads(output_path.read_text(encoding="utf-8")).get("atomization") or {}
        print("Calling OpenAI: extract_outline", file=sys.stderr)
        outline_parsed, _outline_resp, outline_nodes, outline_warnings = extract_solution_outline(
            client=client,
            model=args.model,
            reasoning_effort=reasoning_effort,
            task=task,
            solution_output=solution_output_text(solution_files),
            cache_dir=cache_dir,
        )
        print("Calling OpenAI: tag_criteria", file=sys.stderr)
        _tag_parsed, _tag_resp, tag_warnings = tag_final_criteria(
            client=client,
            model=args.model,
            reasoning_effort=reasoning_effort,
            task=task,
            atoms=atoms_for_tagging,
            criteria=criteria,
            outline_nodes=outline_nodes,
            cache_dir=cache_dir,
        )
        for warning in outline_warnings + tag_warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        distribution = {
            tier: sum(1 for c in criteria if c.get("criticality") == tier) for tier in (3, 2, 1)
        }
        print(
            "Criticality distribution: "
            + ", ".join(f"{tier}: {count}" for tier, count in distribution.items()),
            file=sys.stderr,
        )
        for warning in criticality_distribution_warnings(criteria):
            print(f"WARNING: Criticality distribution: {warning}", file=sys.stderr)
        rubric["criteria"] = criteria
        rubric["outline"] = outline_nodes
        rubric["retagged_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        final_path.write_text(json.dumps(rubric, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {final_path} (criteria unchanged, tags/outline updated)")
        return 0

    print("Calling OpenAI: atomize_solution", file=sys.stderr)
    atoms, atom_response = api_call(
        client=client,
        model=args.model,
        system=atom_system,
        user=build_user_payload(atom_user_base, bundle),
        required_keys={"language", "jurisdiction", "reasoning_style", "atoms", "solution_gaps_or_warnings"},
        reasoning_effort=reasoning_effort,
        label="atomize_solution",
        cache_dir=cache_dir,
    )

    print("Calling OpenAI: generate_candidate_criteria (3 roles)", file=sys.stderr)
    candidate_payload = {
        "task_json": task,
        "task_files": files,
        "atomization": atoms,
    }
    candidate_user = build_user_payload(candidate_user_base, candidate_payload)
    with ThreadPoolExecutor(max_workers=len(CANDIDATE_ROLES)) as pool:
        role_results = list(
            pool.map(
                lambda role: generate_role_candidates(
                    client=client,
                    model=args.model,
                    reasoning_effort=reasoning_effort,
                    candidate_system=candidate_system,
                    candidate_user=candidate_user,
                    role_name=role[0],
                    role_code=role[1],
                    cache_dir=cache_dir,
                ),
                CANDIDATE_ROLES,
            )
        )

    merged_criteria: list[dict[str, Any]] = []
    candidates_by_role: dict[str, dict[str, Any]] = {}
    candidate_usage: dict[str, dict[str, Any]] = {}
    for role_name, parsed, response in role_results:
        candidates_by_role[role_name] = parsed
        candidate_usage[role_name] = usage_summary(response)
        merged_criteria.extend(parsed.get("criteria", []))
    candidates = {
        "language": next(iter(candidates_by_role.values())).get("language") if candidates_by_role else None,
        "criteria": merged_criteria,
        "generation_notes_by_role": {
            role: parsed.get("generation_notes", []) for role, parsed in candidates_by_role.items()
        },
    }
    print(
        "Candidate pool: "
        + ", ".join(f"{role}={len(parsed.get('criteria', []))}" for role, parsed in candidates_by_role.items()),
        file=sys.stderr,
    )

    print("Calling OpenAI: prune_criteria", file=sys.stderr)
    prune_payload = {
        "task_json": task,
        "atomization": atoms,
        "candidate_rubric": candidates,
    }
    pruned, pruned_response = api_call(
        client=client,
        model=args.model,
        system=pruner_system,
        user=build_user_payload(pruner_user_base, prune_payload),
        required_keys={
            "language",
            "criteria",
            "rejected_candidates",
            "pruning_notes",
            "coverage_audit",
        },
        reasoning_effort=reasoning_effort,
        label="prune_criteria",
        cache_dir=cache_dir,
    )

    calibration_result: dict[str, Any] | None = None
    if calibrate:
        solution_output = solution_output_text(solution_files)
        calibration_result = calibrate_rubric(
            client=client,
            generator_model=args.model,
            generator_effort=reasoning_effort,
            judges=calibration_judges,
            task=task,
            task_dir=task_dir,
            solution_output=solution_output,
            criteria=pruned.get("criteria", []),
            max_rounds=max(1, args.max_calibration_rounds),
            parallel=args.parallel,
            cache_dir=cache_dir,
        )
        final_criteria = calibration_result["kept"]
        print(
            f"Calibration result: kept {len(final_criteria)}, dropped {len(calibration_result['dropped'])} "
            f"over {len(calibration_result['rounds'])} round(s)",
            file=sys.stderr,
        )
        print(f"tokens[calibration_judge]: {calibration_result['judge_usage']}", file=sys.stderr)
    else:
        final_criteria = pruned.get("criteria", [])

    tagging_parsed: dict[str, Any] | None = None
    tagging_response: dict[str, Any] | None = None
    tag_warnings: list[str] = []
    outline_parsed: dict[str, Any] | None = None
    outline_response: dict[str, Any] | None = None
    outline_nodes: list[dict[str, Any]] | None = None
    outline_warnings: list[str] = []
    if final_criteria and not args.skip_tagging:
        print("Calling OpenAI: extract_outline", file=sys.stderr)
        outline_parsed, outline_response, outline_nodes, outline_warnings = extract_solution_outline(
            client=client,
            model=args.model,
            reasoning_effort=reasoning_effort,
            task=task,
            solution_output=solution_output_text(solution_files),
            cache_dir=cache_dir,
        )
        for warning in outline_warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        print("Calling OpenAI: tag_criteria", file=sys.stderr)
        tagging_parsed, tagging_response, tag_warnings = tag_final_criteria(
            client=client,
            model=args.model,
            reasoning_effort=reasoning_effort,
            task=task,
            atoms=atoms,
            criteria=final_criteria,
            outline_nodes=outline_nodes,
            cache_dir=cache_dir,
        )
        for warning in tag_warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        distribution = {
            tier: sum(1 for c in final_criteria if c.get("criticality") == tier)
            for tier in (3, 2, 1)
        }
        print(
            "Criticality distribution: "
            + ", ".join(f"{tier}: {count}" for tier, count in distribution.items()),
            file=sys.stderr,
        )
        for warning in criticality_distribution_warnings(final_criteria):
            print(f"WARNING: Criticality distribution: {warning}", file=sys.stderr)

    validation_errors = validate_criteria(final_criteria)
    validation_errors.extend(validate_pruning_coverage(pruned, atoms))
    validation_warnings = [
        f"Criticality distribution: {warning}"
        for warning in criticality_distribution_warnings(final_criteria)
    ]
    validation_warnings.extend(
        f"Long criterion for manual bundling review: {criterion.get('id')} "
        f"({len(str(criterion.get('match_criteria', '')))} characters)"
        for criterion in final_criteria
        if len(str(criterion.get("match_criteria", ""))) > 900
    )
    generated = {
        "schema_version": "0.2",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generator": {
            "provider": "openai",
            "model": args.model,
            "reasoning_effort": reasoning_effort,
            "api_base": os.environ.get("OPENAI_API_BASE", DEFAULT_API_BASE),
            "rubric_count_policy": "model_selected",
            "candidate_roles": [name for name, _ in CANDIDATE_ROLES],
            "calibration": {
                "enabled": calibrate,
                "mode": "committee" if calibrate and calibration_committee else "repeated_model",
                "judge_model": judge_model if calibrate and not calibration_committee else None,
                "judge_reasoning_effort": judge_effort if calibrate and not calibration_committee else None,
                "committee": (
                    [spec.as_dict() for spec in calibration_committee]
                    if calibrate and calibration_committee
                    else None
                ),
                "votes": calibration_vote_count if calibrate else None,
                "max_rounds": args.max_calibration_rounds if calibrate else None,
            },
        },
        "task": {
            "path": str(task_dir),
            "title": task.get("title"),
            "work_type": task.get("work_type"),
            "deliverables": task.get("deliverables"),
        },
        "input_files": [
            {"path": f["path"], "role": f["role"], "truncated": f["truncated"]} for f in files
        ],
        "input_warnings": input_warnings,
        "atomization": atoms,
        "candidate_rubric": candidates,
        "pruned_rubric": pruned,
        "calibration": (
            {
                "rounds": calibration_result["rounds"],
                "dropped": calibration_result["dropped"],
            }
            if calibration_result
            else None
        ),
        "outline": (
            {
                "nodes": outline_nodes,
                "derived": bool(outline_parsed.get("derived")),
                "outline_notes": outline_parsed.get("outline_notes", []),
                "warnings": outline_warnings,
            }
            if outline_parsed is not None
            else None
        ),
        "analysis_tagging": (
            {
                "enabled": True,
                "function_vocabulary": FUNCTION_TAGS,
                "criticality_scale": {
                    "3": "realistischer ergebnisentscheidender Divergenzpunkt; Ziel ~10-15%",
                    "2": "wichtig - in einer soliden Lösung erwartet; höchstens 60%",
                    "1": "eher unwichtig - Detail, Form, Bonuswissen; verbleibender Anteil",
                },
                "tagging_notes": tagging_parsed.get("tagging_notes", []),
                "warnings": tag_warnings,
            }
            if tagging_parsed is not None
            else {"enabled": False}
        ),
        "final_criteria": final_criteria,
        "validation_errors": validation_errors,
        "validation_warnings": validation_warnings,
        "usage": {
            "atomize_solution": usage_summary(atom_response),
            "generate_candidate_criteria": candidate_usage,
            "prune_criteria": usage_summary(pruned_response),
            "calibration_judge": calibration_result["judge_usage"] if calibration_result else None,
            "calibration_judge_by_member": (
                calibration_result["judge_usage_by_member"] if calibration_result else None
            ),
            "refine_rubric": calibration_result["refine_usage"] if calibration_result else None,
            "extract_outline": usage_summary(outline_response) if outline_response else None,
            "tag_criteria": usage_summary(tagging_response) if tagging_response else None,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")

    if args.write_final:
        final = {
            "schema_version": "0.2",
            "generated_at": generated["generated_at"],
            "review_status": (
                "generated_calibrated_needs_human_review"
                if calibrate
                else "generated_uncalibrated_needs_human_review"
            ),
            "language": pruned.get("language"),
            "task_title": task.get("title"),
            "outline": outline_nodes,
            "criteria": final_criteria,
            "validation_warnings": validation_warnings,
            "provenance": {
                "source": str(output_path.relative_to(task_dir)) if output_path.is_relative_to(task_dir) else str(output_path),
                "provider": "openai",
                "model": args.model,
                "candidate_roles": [name for name, _ in CANDIDATE_ROLES],
                "calibration": generated["generator"]["calibration"],
            },
        }
        final_path.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {final_path}")

    if validation_errors:
        print("Validation warnings:", file=sys.stderr)
        for error in validation_errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
