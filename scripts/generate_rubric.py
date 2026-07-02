#!/usr/bin/env python3
"""Generate Boolean LLM-judge rubrics from LAB-EU human solutions.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


DEFAULT_MODEL = "gpt-5.5"
DEFAULT_API_BASE = "https://api.openai.com/v1"
MAX_FILE_CHARS = 40_000
MAX_TOTAL_CHARS = 180_000
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO_ROOT / "prompts" / "rubric_generation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a draft LAB-EU rubric from a task directory and human solution."
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
        help="Also write the pruned rubric to evals/rubric.json.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and validate local inputs, then print the planned API calls without calling OpenAI.",
    )
    return parser.parse_args()


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


def api_call(
    *,
    client: OpenAI,
    model: str,
    system: str,
    user: str,
    max_output_tokens: int,
    required_keys: set[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        response = client.responses.create(
            model=model,
            instructions=system,
            input=user,
            max_output_tokens=max_output_tokens,
            text={"format": {"type": "json_object"}},
        )
    except OpenAIError as exc:
        raise RuntimeError(f"OpenAI API request failed: {exc}") from exc

    response_data = response.model_dump(mode="json")
    try:
        parsed = json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Model returned invalid JSON: {response.output_text[:2000]}") from exc
    missing = sorted(required_keys - set(parsed))
    if missing:
        raise RuntimeError(f"Model JSON is missing required keys: {', '.join(missing)}")
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


def atomizer_prompt() -> tuple[str, str]:
    return prompt_pair("atomize_solution")


def candidate_prompt() -> tuple[str, str]:
    return prompt_pair("generate_candidate_criteria")


def pruner_prompt() -> tuple[str, str]:
    return prompt_pair("prune_rubric")


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
        if criterion.get("criticality") != "must_pass":
            errors.append(f"{cid} has non-scoring criticality {criterion.get('criticality')!r}.")
    return errors


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

    output_path = task_dir / "evals" / "rubric.generated.json"
    final_path = task_dir / "evals" / "rubric.json"

    if args.dry_run:
        print(f"Task: {task.get('title', task_dir.name)}")
        print(f"Model: {args.model}")
        print(f"Solution files: {[str(p) for p in solution_files]}")
        print(f"Input files: {len(files)}")
        print(f"Output: {output_path}")
        print(f"Write final rubric: {args.write_final}")
        for warning in input_warnings:
            print(f"WARNING: {warning}")
        print("Planned API calls: atomize_solution -> generate_candidates -> prune_candidates")
        return 0

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set. Put it in the environment or .env.")

    client = make_client(os.environ.get("OPENAI_API_BASE", DEFAULT_API_BASE))

    print("Calling OpenAI: atomize_solution", file=sys.stderr)
    atom_system, atom_user_base = atomizer_prompt()
    atoms, atom_response = api_call(
        client=client,
        model=args.model,
        system=atom_system,
        user=build_user_payload(atom_user_base, bundle),
        max_output_tokens=20_000,
        required_keys={"language", "jurisdiction", "reasoning_style", "atoms", "solution_gaps_or_warnings"},
    )

    print("Calling OpenAI: generate_candidate_criteria", file=sys.stderr)
    candidate_system, candidate_user_base = candidate_prompt()
    candidate_payload = {
        "task_json": task,
        "task_files": files,
        "atomization": atoms,
    }
    candidates, candidate_response = api_call(
        client=client,
        model=args.model,
        system=candidate_system,
        user=build_user_payload(candidate_user_base, candidate_payload),
        max_output_tokens=24_000,
        required_keys={"language", "criteria", "generation_notes"},
    )

    print("Calling OpenAI: prune_criteria", file=sys.stderr)
    pruner_system, pruner_user_base = pruner_prompt()
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
        max_output_tokens=16_000,
        required_keys={"language", "criteria", "rejected_candidates", "pruning_notes"},
    )

    validation_errors = validate_criteria(pruned.get("criteria", []))
    generated = {
        "schema_version": "0.1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "generator": {
            "provider": "openai",
            "model": args.model,
            "api_base": os.environ.get("OPENAI_API_BASE", DEFAULT_API_BASE),
            "rubric_count_policy": "model_selected",
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
        "validation_errors": validation_errors,
        "usage": {
            "atomize_solution": usage_summary(atom_response),
            "generate_candidate_criteria": usage_summary(candidate_response),
            "prune_criteria": usage_summary(pruned_response),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")

    if args.write_final:
        final = {
            "schema_version": "0.1",
            "generated_at": generated["generated_at"],
            "review_status": "generated_needs_human_review",
            "language": pruned.get("language"),
            "task_title": task.get("title"),
            "criteria": pruned.get("criteria", []),
            "provenance": {
                "source": str(output_path.relative_to(task_dir)) if output_path.is_relative_to(task_dir) else str(output_path),
                "provider": "openai",
                "model": args.model,
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
