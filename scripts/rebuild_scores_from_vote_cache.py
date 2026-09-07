#!/usr/bin/env python3
"""Rebuild scores.json for a study arm from its vote cache. Makes no API calls.

Why this exists
---------------
The de-core-45 headline numbers were never written to scores.json. The judging
job of 2026-07-31 ran the full professor-pilot committee, but the third member
(gemini via OpenRouter) hit the account credit limit and returned 403 for most
criteria. A committee criterion with an error vote is unresolved, so ~78% of
the verdicts collapsed while every job still exited 0. The published numbers
came out of a later pass that read the two working judges from the vote cache
and paid gemini only for the criteria where they disagreed -- and that pass
wrote a CSV, not score files. This script closes that gap: it replays the same
resolution rule over the cached votes and produces the score files the rest of
the repo expects.

Resolution rule ("3judge-tiebreak")
-----------------------------------
Two primary judges vote on every criterion. Where they agree, the criterion is
decided. Where they disagree, the tie-breaker's cached vote decides it. A
disagreement with no cached tie-break vote stays unresolved rather than being
guessed -- that band is reported, not hidden.

This is deliberately not the same as the majority rule in evaluation.run: there
a criterion needs all three votes present, and a missing third vote poisons the
criterion. Here a missing third vote is only consulted where it can matter.

Cache lookup
------------
A vote cache key hashes the judge identity, the phase and the full judge prompt,
and the prompt embeds both the criterion text and the answer under review. A
cached vote can therefore never be read against a criterion it was not cast on.
That makes it safe to search several cache directories in order: pass the arm's
own cache plus any recheck cache, and revised criteria resolve out of the
recheck cache while the rest resolve out of the arm's -- no stale vote can be
picked up by accident.

    python scripts/rebuild_scores_from_vote_cache.py runs/<arm>/<runid> \
        --judge-committee configs/judge-committee-professor-pilot.json \
        --primaries luna,terra --tiebreaker gemini-3.6-flash \
        --style-evaluation \
        --extra-cache-dir runs/recheck-de-core-4-lunaterra/<arm>/vote-cache
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from evaluation.run import (  # noqa: E402
    JudgeSpec,
    assemble_scores,
    combined_content_style_prompt,
    is_style_eligible_criterion,
    judge_prompt,
    load_agent_output,
    load_json,
    load_judge_committee,
    load_rubric,
    vote_cache_path,
    write_scores,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild scores.json from cached committee votes (no API calls).")
    parser.add_argument("run_dirs", nargs="+", type=pathlib.Path,
                        help="Run directories holding tasks/<task>/submission and vote-cache/.")
    parser.add_argument("--judge-committee", type=pathlib.Path, required=True)
    parser.add_argument("--primaries", default="luna,terra",
                        help="Comma-separated judge names that vote on every criterion.")
    parser.add_argument("--tiebreaker", default="gemini-3.6-flash",
                        help="Judge name consulted only where the primaries disagree.")
    parser.add_argument("--style-evaluation", action="store_true",
                        help="Also rebuild the Gutachtenstil verdicts (combined judge calls).")
    parser.add_argument("--extra-cache-dir", action="append", type=pathlib.Path, default=[],
                        help="Additional vote caches to search after the run's own. Repeatable.")
    parser.add_argument("--output-name", default="scores.json",
                        help="File name written under tasks/<task>/. Default scores.json.")
    parser.add_argument("--mirror-to-submission", action="store_true",
                        help="Also write the same file under tasks/<task>/submission/.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would be written without writing anything.")
    return parser.parse_args()


def read_vote(cache_dirs, phase, spec, criterion_id, prompt) -> dict[str, Any] | None:
    """First cached vote for this exact (judge, phase, criterion, prompt), or None."""
    for cache_dir in cache_dirs:
        path = vote_cache_path(cache_dir, phase, spec, criterion_id, prompt)
        if path is None or not path.exists():
            continue
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
    return None


def split_vote(vote: dict[str, Any] | None, combined: bool, side: str) -> dict[str, Any] | None:
    """A combined cache entry holds a content and a style vote; unwrap the wanted side."""
    if vote is None:
        return None
    return vote.get(side) if combined else (vote if side == "content" else None)


def decide(votes: list[tuple[JudgeSpec, dict[str, Any] | None]],
           tiebreak: tuple[JudgeSpec, dict[str, Any] | None],
           criterion: dict[str, Any]) -> dict[str, Any]:
    """Apply the tie-break rule and shape the result like evaluation.run does."""
    verdicts = [(v or {}).get("verdict") for _spec, v in votes]
    known = [v for v in verdicts if v in ("pass", "fail")]
    used_tiebreak = False
    tb_spec, tb_vote = tiebreak
    tb_verdict = (tb_vote or {}).get("verdict")

    if len(known) < len(verdicts):
        verdict, resolution = "error", "unresolved"          # a primary never voted
    elif all(v == known[0] for v in known):
        verdict, resolution = known[0], "resolved"
    elif tb_verdict in ("pass", "fail"):
        verdict, resolution = tb_verdict, "resolved"
        used_tiebreak = True
    else:
        verdict, resolution = "error", "unresolved"          # disputed, no tie-break vote

    cast = list(votes) + ([tiebreak] if used_tiebreak else [])
    counts = {"pass": 0, "fail": 0, "error": 0}
    for _spec, vote in cast:
        counts[(vote or {}).get("verdict", "error")] = \
            counts.get((vote or {}).get("verdict", "error"), 0) + 1
    valid = counts["pass"] + counts["fail"]
    agreement = (max(counts["pass"], counts["fail"]) / valid) if valid else 0.0
    primary = next((v for _s, v in cast if (v or {}).get("verdict") == verdict), None) or {}

    return {
        "id": criterion["id"],
        "title": criterion["title"],
        "verdict": verdict,
        "resolution": resolution,
        "reasoning": primary.get("reasoning", ""),
        "evidence": primary.get("evidence", []),
        "vote_counts": counts,
        "judge_agreement": round(agreement, 3),
        "tiebreak_used": used_tiebreak,
        "votes": [
            {
                "verdict": (vote or {}).get("verdict", "error"),
                "reasoning": (vote or {}).get("reasoning", ""),
                "evidence": (vote or {}).get("evidence", []),
                "component_checks": (vote or {}).get("component_checks", []),
                "judge": spec.as_dict(),
                "cache_hit": vote is not None,
                "role": "tiebreak" if spec is tb_spec else "primary",
            }
            for spec, vote in cast
        ],
        "usage": {},
    }


def rebuild_task(task_dir: pathlib.Path, submission: pathlib.Path, cache_dirs,
                 primaries, tiebreaker, style_evaluation: bool):
    task = load_json(task_dir / "task.json")
    rubric_path, criteria = load_rubric(task_dir)
    results, style_results = [], ([] if style_evaluation else None)

    for criterion in criteria:
        output = load_agent_output(submission, criterion)
        combined = style_evaluation and is_style_eligible_criterion(criterion)
        phase = "combined-r1" if combined else "content-r1"
        prompt = (combined_content_style_prompt(task, task_dir, output, criterion)
                  if combined else judge_prompt(task, task_dir, output, criterion))
        raw = {spec.name: read_vote(cache_dirs, phase, spec, criterion["id"], prompt)
               for spec in list(primaries) + [tiebreaker]}

        results.append(decide(
            [(s, split_vote(raw[s.name], combined, "content")) for s in primaries],
            (tiebreaker, split_vote(raw[tiebreaker.name], combined, "content")),
            criterion))
        if combined:
            style_results.append(decide(
                [(s, split_vote(raw[s.name], combined, "style")) for s in primaries],
                (tiebreaker, split_vote(raw[tiebreaker.name], combined, "style")),
                criterion))

    return task, rubric_path, criteria, results, style_results


def main() -> int:
    args = parse_args()
    specs = load_judge_committee(args.judge_committee if args.judge_committee.is_absolute()
                                 else REPO_ROOT / args.judge_committee)
    by_name = {spec.name: spec for spec in specs}
    try:
        primaries = [by_name[name] for name in args.primaries.split(",")]
        tiebreaker = by_name[args.tiebreaker]
    except KeyError as exc:
        print(f"judge {exc} is not in {args.judge_committee}; "
              f"committee has: {', '.join(by_name)}", file=sys.stderr)
        return 2

    written = 0
    for run_dir in args.run_dirs:
        run_dir = run_dir if run_dir.is_absolute() else REPO_ROOT / run_dir
        cache_dirs = [run_dir / "vote-cache"] + [
            d if d.is_absolute() else REPO_ROOT / d for d in args.extra_cache_dir]
        for metadata_path in sorted((run_dir / "tasks").glob("*/metadata.json")):
            task_root = metadata_path.parent
            metadata = load_json(metadata_path)
            submission = task_root / "submission"
            # A task with no deliverable is "no submission", not a task that failed
            # every criterion -- the judge's own scores.json living under submission/
            # makes the directory look non-empty, so check the deliverables.
            if metadata.get("missing_deliverables") or not submission.is_dir():
                print(f"  skip (no submission): {task_root.name}")
                continue
            task_dir = pathlib.Path(metadata["source_task_dir"])
            task, rubric_path, criteria, results, style_results = rebuild_task(
                task_dir, submission, cache_dirs, primaries, tiebreaker, args.style_evaluation)

            scores = assemble_scores(
                task_dir=task_dir, submission=submission, rubric_path=rubric_path,
                task=task, criteria=criteria, results=results,
                judge_model="committee", api_base="mixed", reasoning_effort=None,
                votes=1, adaptive=False, judge_committee=specs,
                style_results=style_results,
                style_evaluation_mode="combined" if args.style_evaluation else None,
                committee_conflict_recheck=False, committee_error_retries=0)
            scores["judging_pass"] = "3judge-tiebreak"
            # Short judge labels: the CSV column is read by people, and the
            # exact model ids are already in judge_committee inside the file.
            scores["committee_resolution"] = (
                f"{'+'.join(s.name.split('-')[0] for s in primaries)}, "
                f"{tiebreaker.name.split('-')[0]} tie-break")
            scores["rebuilt_from_vote_cache"] = [str(d) for d in cache_dirs]
            scores["n_tiebreaks"] = sum(1 for r in results if r["tiebreak_used"])
            scores["style_n_tiebreaks"] = sum(1 for r in style_results or [] if r["tiebreak_used"])

            unresolved = scores["content_score"]["n_unresolved"]
            flag = f"  UNRESOLVED {unresolved}" if unresolved else ""
            print(f"  {task_root.name}: {scores['n_passed']}/{scores['n_criteria']} "
                  f"tiebreaks={scores['n_tiebreaks']}{flag}")
            if args.dry_run:
                continue
            write_scores(submission, scores, task_root / args.output_name)
            if args.mirror_to_submission:
                write_scores(submission, scores, submission / args.output_name)
            written += 1

    print(f"\n{'would write' if args.dry_run else 'wrote'} {written} score file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
