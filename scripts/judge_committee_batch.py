#!/usr/bin/env python3
"""Prewarm a run's judge vote cache with the Batch-API-capable committee members.

A committee judges every criterion with several models. Two of ours (luna,
terra) sit on the OpenAI endpoint, which offers a Batch API at half price; the
third (gemini via OpenRouter) does not. This script submits the OpenAI members'
round-1 votes as a batch and writes each verdict into the run's `vote-cache/`
in exactly the format `evaluation.run` reads.

The synchronous committee run afterwards is then unchanged in every respect
except cost: it finds the batched votes in the cache and only calls the
non-batchable judge live.

    python scripts/judge_committee_batch.py runs/a/<id> runs/b/<id> \\
        --study studies/de-core-45/study.json
    python scripts/judge_run.py runs/a/<id> --study studies/de-core-45/study.json

Nothing here is load-bearing for correctness: a vote that fails to batch is
simply absent from the cache, and the synchronous run judges it live. The only
thing that must be exact is the cache key, which is why it comes from
`evaluation.run.vote_cache_path` rather than being recomputed here.

Interrupted after submission? Re-run with --resume runs/judge-batches/<id>.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import time
from typing import Any

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from evaluation.run import (  # noqa: E402
    DEFAULT_API_BASE,
    JudgeSpec,
    combined_content_style_prompt,
    is_style_eligible_criterion,
    judge_prompt,
    load_agent_output,
    load_env_files,
    load_json,
    load_judge_committee,
    load_rubric,
    make_client,
    normalize_combined_judge_result,
    normalize_judge_result,
    parse_json_response,
    vote_cache_path,
)

# Batch API limits: 50k requests per batch, and an input file the upload will
# actually accept. Judge prompts embed the full answer under review (~30 KB
# each here), so the size ceiling binds long before the request count does —
# 21,664 votes came to 656 MB in one file.
MAX_LINES_PER_CHUNK = 40_000
MAX_CHUNK_BYTES = 150 * 1024 * 1024
ROUND1_CONTENT_PHASE = "content-r1"
ROUND1_COMBINED_PHASE = "combined-r1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch-prewarm the vote cache for a committee's OpenAI judges.")
    parser.add_argument("run_dirs", nargs="*", type=pathlib.Path,
                        help="Run dirs containing manifest.json and tasks/.")
    parser.add_argument("--study", type=pathlib.Path, default=None,
                        help="Study definition supplying the committee and style setting.")
    parser.add_argument("--judge-committee", type=pathlib.Path, default=None)
    parser.add_argument("--style-evaluation", dest="style_evaluation",
                        action="store_true", default=None)
    parser.add_argument("--no-style-evaluation", dest="style_evaluation",
                        action="store_false")
    parser.add_argument("--batches-dir", type=pathlib.Path,
                        default=REPO_ROOT / "runs" / "judge-batches")
    parser.add_argument("--resume", type=pathlib.Path, default=None,
                        help="Existing batch dir: skip to poll/harvest.")
    parser.add_argument("--prepare-only", action="store_true",
                        help="Write the batch input files without uploading.")
    parser.add_argument("--poll-seconds", type=int, default=120)
    parser.add_argument("--max-wait-hours", type=float, default=24.0)
    parser.add_argument("--completion-window", default="24h")
    return parser.parse_args()


def resolve_config(args: argparse.Namespace) -> tuple[list[JudgeSpec], bool]:
    committee_path = args.judge_committee
    style = args.style_evaluation
    if args.study:
        study = json.loads(
            (args.study if args.study.is_absolute() else REPO_ROOT / args.study)
            .read_text(encoding="utf-8"))
        evaluation = study.get("evaluation", {})
        if committee_path is None and evaluation.get("judge_committee"):
            committee_path = pathlib.Path(evaluation["judge_committee"])
        if style is None and "aggregate_content_and_style" in evaluation:
            style = not evaluation["aggregate_content_and_style"]
    if committee_path is None:
        raise SystemExit("No judge committee given (--study or --judge-committee).")
    path = committee_path if committee_path.is_absolute() else REPO_ROOT / committee_path
    if not path.exists():
        raise SystemExit(f"Missing judge committee file: {path}")
    return load_judge_committee(path), bool(style)


def batchable(specs: list[JudgeSpec]) -> tuple[list[JudgeSpec], list[JudgeSpec]]:
    """Split the committee into Batch-API members and live-only members."""
    batch = [s for s in specs if s.api_base == DEFAULT_API_BASE]
    live = [s for s in specs if s.api_base != DEFAULT_API_BASE]
    return batch, live


def collect_jobs(run_dirs: list[pathlib.Path], specs: list[JudgeSpec],
                 style: bool) -> tuple[list[dict], dict[str, dict]]:
    """Build one batch line per (task, criterion, judge) vote still missing."""
    lines: list[dict[str, Any]] = []
    mapping: dict[str, dict[str, Any]] = {}
    counter = 0
    skipped = 0

    for run_dir in run_dirs:
        cache_dir = run_dir / "vote-cache"
        for metadata_path in sorted((run_dir / "tasks").glob("*/metadata.json")):
            metadata = load_json(metadata_path)
            task_run_dir = metadata_path.parent
            task_dir = pathlib.Path(metadata["source_task_dir"])
            submission = task_run_dir / "submission"
            if not submission.is_dir() or not any(submission.iterdir()):
                print(f"WARNING: no submission for {task_run_dir.name}, skipping",
                      file=sys.stderr)
                continue
            task = load_json(task_dir / "task.json")
            _rubric_path, criteria = load_rubric(task_dir)
            for criterion in criteria:
                agent_output = load_agent_output(submission, criterion)
                combined = style and is_style_eligible_criterion(criterion)
                phase = ROUND1_COMBINED_PHASE if combined else ROUND1_CONTENT_PHASE
                prompt = (combined_content_style_prompt(task, task_dir, agent_output, criterion)
                          if combined else
                          judge_prompt(task, task_dir, agent_output, criterion))
                for spec in specs:
                    path = vote_cache_path(cache_dir, phase, spec, criterion["id"], prompt)
                    if path is not None and path.exists():
                        skipped += 1
                        continue
                    custom_id = f"c-{counter:07d}"
                    counter += 1
                    body: dict[str, Any] = {
                        "model": spec.model,
                        "input": prompt,
                        "text": {"format": {"type": "json_object"}},
                    }
                    if spec.reasoning_effort and spec.reasoning_effort != "none":
                        body["reasoning"] = {"effort": spec.reasoning_effort}
                    lines.append({"custom_id": custom_id, "method": "POST",
                                  "url": "/v1/responses", "body": body})
                    mapping[custom_id] = {
                        "cache_path": str(path),
                        "phase": phase,
                        "combined": combined,
                        "criterion_id": criterion["id"],
                        "criterion_title": criterion["title"],
                        "judge": spec.name,
                    }
    if skipped:
        print(f"{skipped} vote(s) already cached; not re-batched.")
    return lines, mapping


def extract_output_text(body: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in body.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if content.get("type") == "output_text":
                parts.append(content.get("text") or "")
    return "".join(parts)


def usage_from_body(body: dict[str, Any]) -> dict[str, Any]:
    usage = body.get("usage") or {}
    summary = {k: usage[k] for k in ("input_tokens", "output_tokens", "total_tokens")
               if k in usage}
    details = usage.get("input_tokens_details") or {}
    if isinstance(details, dict) and "cached_tokens" in details:
        summary["cached_input_tokens"] = details["cached_tokens"]
    return summary


def cache_entry(body: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any] | None:
    """Turn one batch response into exactly what evaluation.run caches."""
    if body.get("status") == "incomplete":
        return None
    try:
        parsed = parse_json_response(extract_output_text(body))
    except (ValueError, json.JSONDecodeError):
        return None
    usage = usage_from_body(body)
    identity = {"id": entry["criterion_id"], "title": entry["criterion_title"]}
    try:
        if entry["combined"]:
            normalized = normalize_combined_judge_result(parsed, usage)
            return {
                channel: {**identity,
                          "verdict": vote["verdict"],
                          "reasoning": vote["reasoning"],
                          "evidence": vote["evidence"],
                          "component_checks": vote.get("component_checks", []),
                          "scope_check": vote.get("scope_check", {}),
                          "stated_reason_check": vote.get("stated_reason_check", {}),
                          "method_checks": vote.get("method_checks", {}),
                          "usage": vote["usage"],
                          "cache_hit": False}
                for channel, vote in normalized.items()
            }
        vote = normalize_judge_result(parsed, usage)
        return {**identity,
                "verdict": vote["verdict"],
                "reasoning": vote["reasoning"],
                "evidence": vote["evidence"],
                "component_checks": vote.get("component_checks", []),
                "scope_check": vote.get("scope_check", {}),
                "stated_reason_check": vote.get("stated_reason_check", {}),
                "usage": vote["usage"],
                "cache_hit": False}
    except (ValueError, KeyError, TypeError):
        return None


def write_chunks(lines: list[dict[str, Any]], batch_dir: pathlib.Path) -> list[pathlib.Path]:
    """Split by model first, then by encoded size and line count.

    The Batch API rejects an input file that mixes models ("Each batch must
    contain requests for a single model"), and our lines interleave the
    committee members criterion by criterion — so grouping is mandatory, not an
    optimisation.
    """
    by_model: dict[str, list[dict[str, Any]]] = {}
    for line in lines:
        by_model.setdefault(line["body"]["model"], []).append(line)
    chunks: list[pathlib.Path] = []
    for model in sorted(by_model):
        chunks.extend(_write_model_chunks(by_model[model], batch_dir, len(chunks)))
    return chunks


def _write_model_chunks(lines: list[dict[str, Any]], batch_dir: pathlib.Path,
                        start_index: int) -> list[pathlib.Path]:
    """Split by encoded size as well as line count — see MAX_CHUNK_BYTES."""
    chunks: list[pathlib.Path] = []
    buffer: list[str] = []
    buffered_bytes = 0

    def flush() -> None:
        nonlocal buffer, buffered_bytes
        if not buffer:
            return
        chunk = batch_dir / f"input-{start_index + len(chunks):03d}.jsonl"
        chunk.write_text("".join(buffer), encoding="utf-8")
        chunks.append(chunk)
        buffer, buffered_bytes = [], 0

    for line in lines:
        encoded = json.dumps(line, ensure_ascii=False) + "\n"
        size = len(encoded.encode("utf-8"))
        if buffer and (buffered_bytes + size > MAX_CHUNK_BYTES
                       or len(buffer) >= MAX_LINES_PER_CHUNK):
            flush()
        buffer.append(encoded)
        buffered_bytes += size
    flush()
    return chunks


def save_state(batch_dir: pathlib.Path, state: dict[str, Any]) -> None:
    (batch_dir / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def harvest(client, state: dict[str, Any], batch_dir: pathlib.Path,
            args: argparse.Namespace) -> tuple[int, int]:
    """Poll every batch to completion, then write the votes into the caches."""
    deadline = time.time() + args.max_wait_hours * 3600
    pending = {b["id"]: b for b in state["batches"] if not b.get("harvested")}
    outputs: dict[str, str] = {}
    failed: list[str] = []
    while pending:
        for batch_id in list(pending):
            info = client.batches.retrieve(batch_id)
            if info.status in ("completed", "failed", "expired", "cancelled"):
                pending.pop(batch_id)
                if info.status == "completed" and info.output_file_id:
                    outputs[batch_id] = client.files.content(info.output_file_id).text
                else:
                    failed.append(batch_id)
                    detail = ""
                    error_file = getattr(info, "error_file_id", None)
                    if error_file:
                        # the API explains WHY here; without it the log says
                        # only "failed" and the cause stays invisible
                        detail = client.files.content(error_file).text[:600]
                    elif getattr(info, "errors", None):
                        detail = str(info.errors)[:600]
                    print(f"batch {batch_id}: {info.status} {detail}", file=sys.stderr)
        if pending:
            if time.time() > deadline:
                raise SystemExit(f"batches still pending after {args.max_wait_hours}h; "
                                 f"resume with --resume {batch_dir}")
            time.sleep(args.poll_seconds)

    mapping = json.loads((batch_dir / "mapping.json").read_text(encoding="utf-8"))
    written = unusable = 0
    for content in outputs.values():
        for line in content.splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            entry = mapping.get(record.get("custom_id"))
            if entry is None:
                continue
            body = ((record.get("response") or {}).get("body")) or {}
            vote = cache_entry(body, entry)
            if vote is None:
                unusable += 1
                continue
            path = pathlib.Path(entry["cache_path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(vote, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
            written += 1
    for batch in state["batches"]:
        batch["harvested"] = True
    state["failed_batches"] = failed
    save_state(batch_dir, state)
    if failed:
        raise SystemExit(
            f"{len(failed)} of {len(state['batches'])} batch(es) failed; only "
            f"{written:,} vote(s) cached. Fix the cause and re-run — do NOT let "
            f"the scoring jobs start on a cold cache, they would pay full price "
            f"for every vote."
        )
    return written, unusable


def main() -> int:
    args = parse_args()
    load_env_files(REPO_ROOT)

    if args.resume:
        batch_dir = args.resume if args.resume.is_absolute() else REPO_ROOT / args.resume
        state = json.loads((batch_dir / "state.json").read_text(encoding="utf-8"))
    else:
        if not args.run_dirs:
            raise SystemExit("Give at least one run dir (or --resume).")
        specs, style = resolve_config(args)
        batch_specs, live_specs = batchable(specs)
        if not batch_specs:
            raise SystemExit("No committee member uses the OpenAI endpoint; "
                             "nothing to batch.")
        run_dirs = [d if d.is_absolute() else REPO_ROOT / d for d in args.run_dirs]
        for run_dir in run_dirs:
            if not (run_dir / "manifest.json").exists():
                raise SystemExit(f"Missing run manifest: {run_dir / 'manifest.json'}")

        print(f"Batching: {', '.join(s.name for s in batch_specs)}")
        print(f"Live during the judge run: "
              f"{', '.join(s.name for s in live_specs) or '(none)'}")
        print(f"Style evaluation: {style}")

        lines, mapping = collect_jobs(run_dirs, batch_specs, style)
        if not lines:
            print("Nothing to batch — every vote is already cached.")
            return 0

        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        batch_dir = args.batches_dir / stamp
        batch_dir.mkdir(parents=True, exist_ok=True)
        (batch_dir / "mapping.json").write_text(
            json.dumps(mapping, ensure_ascii=False) + "\n", encoding="utf-8")
        chunks = write_chunks(lines, batch_dir)
        state = {
            "created_at": stamp,
            "run_dirs": [str(d) for d in run_dirs],
            "judges": [s.name for s in batch_specs],
            "live_judges": [s.name for s in live_specs],
            "style_evaluation": style,
            "n_votes": len(lines),
            "chunks": [str(c) for c in chunks],
            "batches": [],
        }
        save_state(batch_dir, state)
        print(f"{len(lines):,} vote(s) in {len(chunks)} chunk(s) -> {batch_dir}")
        if args.prepare_only:
            print("--prepare-only: nothing uploaded.")
            return 0

        client, _ = make_client(DEFAULT_API_BASE)
        for chunk in chunks:
            with open(chunk, "rb") as handle:
                uploaded = client.files.create(file=handle, purpose="batch")
            batch = client.batches.create(
                input_file_id=uploaded.id, endpoint="/v1/responses",
                completion_window=args.completion_window)
            state["batches"].append({"id": batch.id, "chunk": str(chunk),
                                     "harvested": False})
            save_state(batch_dir, state)
            print(f"submitted {batch.id} ({chunk.name})")

    client, _ = make_client(DEFAULT_API_BASE)
    written, unusable = harvest(client, state, batch_dir, args)
    print(f"cached {written:,} vote(s); {unusable:,} unusable (judged live later)")
    print(f"Now run judge_run.py --study ... on the same run dirs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
