#!/usr/bin/env python3
"""Judge all submissions in a LAB-EU harness run directory."""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Judge a LAB-EU harness run.")
    parser.add_argument("run_dir", type=pathlib.Path, help="Run directory containing manifest.json and tasks/.")
    parser.add_argument(
        "--study",
        type=pathlib.Path,
        default=None,
        help=(
            "Study definition (e.g. studies/de-core-45/study.json). Its "
            "evaluation block supplies the judge committee and whether content "
            "and style are scored separately, so the study's own configuration "
            "is what runs. Explicit flags below still win."
        ),
    )
    parser.add_argument(
        "--judge-committee",
        type=pathlib.Path,
        default=None,
        help=(
            "Committee JSON with an odd-sized 'judges' list; each member casts "
            "one independent vote. Mutually exclusive with --votes > 1."
        ),
    )
    parser.add_argument("--judge-model", default="gpt-5.5")
    parser.add_argument(
        "--judge-api-base",
        default=None,
        help="Judge endpoint for single-judge mode (default: the OpenAI Responses API).",
    )
    parser.add_argument(
        "--style-evaluation",
        dest="style_evaluation",
        action="store_true",
        default=None,
        help=(
            "Score legal style as a separate Boolean verdict on every "
            "application/argumentation criterion, alongside the content verdict."
        ),
    )
    parser.add_argument(
        "--no-style-evaluation",
        dest="style_evaluation",
        action="store_false",
        help="Content verdicts only, even when the study asks for style.",
    )
    parser.add_argument(
        "--vote-cache-dir",
        type=pathlib.Path,
        default=None,
        help=(
            "Where individual judge votes are cached. Defaults to "
            "<run-dir>/vote-cache. The cache key hashes the full judge prompt "
            "(criterion AND answer), so one directory is safe for a whole run "
            "and a re-run after a timeout only pays for the missing votes."
        ),
    )
    parser.add_argument(
        "--no-vote-cache",
        action="store_true",
        help="Disable the vote cache. A committee run then restarts from zero.",
    )
    parser.add_argument(
        "--service-tier",
        default=None,
        help="Pass through to evaluation.run; 'flex' = Batch pricing plus prompt caching.",
    )
    parser.add_argument(
        "--committee-error-retries",
        type=int,
        default=None,
        help="Targeted retries per errored committee vote before a criterion stays unresolved.",
    )
    parser.add_argument(
        "--committee-tiebreaker",
        action="store_true",
        help=(
            "Use committee members 1 and 2 as primary judges and member 3 only "
            "as a tiebreaker; do not repeat a valid 2:1 result."
        ),
    )
    parser.add_argument(
        "--votes",
        type=int,
        default=1,
        help=(
            "Judge votes per criterion (majority decides). Defaults to 1; measured judge "
            "agreement is ~95%% unanimous, so single votes flip ~1-2%% of verdicts. "
            "Use 3 for final headline runs."
        ),
    )
    parser.add_argument("--reasoning-effort", default="medium", help="Judge reasoning effort; 'none' omits it.")
    parser.add_argument(
        "--adaptive",
        action="store_true",
        help="Adaptive voting: 1 vote per criterion, escalate to --votes only on a non-pass first vote.",
    )
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument(
        "--scores-name",
        default="scores.json",
        help=(
            "Per-task score filename. Defaults to scores.json. Use a distinct "
            "basename for non-voting shadow judges so their results do not "
            "replace the committee outcome."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help=(
            "Skip tasks that already have a complete scores.json (no error verdicts). "
            "Makes the run resumable: re-run after an interruption and only the "
            "unjudged or partially-judged tasks are re-scored."
        ),
    )
    return parser.parse_args()


def apply_study(args: argparse.Namespace) -> dict[str, Any]:
    """Fold a study definition into the arguments and return the effective config.

    The study file is the reproducibility record; making judge_run read it means
    the scores are produced by the configuration the study actually declares,
    instead of by whatever the driver happened to default to.
    """
    study: dict[str, Any] = {}
    if args.study:
        study_path = args.study if args.study.is_absolute() else REPO_ROOT / args.study
        study = json.loads(study_path.read_text(encoding="utf-8"))
        evaluation = study.get("evaluation", {})
        committee = evaluation.get("judge_committee")
        if committee and args.judge_committee is None:
            args.judge_committee = pathlib.Path(committee)
        if args.style_evaluation is None and "aggregate_content_and_style" in evaluation:
            # separate Boolean outcomes == do not aggregate them
            args.style_evaluation = not evaluation["aggregate_content_and_style"]

    if args.style_evaluation is None:
        args.style_evaluation = False

    scores_name = pathlib.Path(args.scores_name)
    if (
        scores_name.name != args.scores_name
        or scores_name.suffix != ".json"
        or args.scores_name in {"", ".json"}
    ):
        raise SystemExit("--scores-name must be a JSON basename such as scores.shadow.json")

    if args.judge_committee is not None:
        path = (args.judge_committee if args.judge_committee.is_absolute()
                else REPO_ROOT / args.judge_committee)
        if not path.exists():
            raise SystemExit(f"Missing judge committee file: {path}")
        if args.votes != 1:
            # evaluation.run refuses this too; catching it here saves finding out
            # after the first task of a six-run batch
            raise SystemExit(
                "--judge-committee casts exactly one vote per member; drop --votes."
            )
        args.judge_committee = path

    return {
        "study": str(args.study) if args.study else None,
        "judge_committee": str(args.judge_committee) if args.judge_committee else None,
        "judge_model": None if args.judge_committee else args.judge_model,
        "judge_api_base": args.judge_api_base,
        "votes": 1 if args.judge_committee else args.votes,
        "reasoning_effort": args.reasoning_effort,
        "style_evaluation": args.style_evaluation,
        "committee_tiebreaker": args.committee_tiebreaker,
        "adaptive": args.adaptive,
        "scores_name": args.scores_name,
    }


def report_incomplete(run_dir: pathlib.Path,
                      paths: list[pathlib.Path],
                      scores_name: str = "scores.json") -> int:
    """Refuse to call a run judged when a committee member was not answering.

    A committee that loses one voter still writes scores.json — every affected
    criterion just becomes `unresolved`, and the pass rate collapses toward
    zero. That looks like a result and is not one. This happened for real: an
    exhausted OpenRouter credit limit made the third judge return 403 for most
    of a six-run batch, and every job still exited 0.
    """
    unresolved = criteria = errored = 0
    affected: list[str] = []
    for metadata_path in paths:
        scores_path = metadata_path.parent / scores_name
        if not scores_path.exists():
            continue
        try:
            scores = json.loads(scores_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        n_unresolved = scores.get("n_unresolved", 0) + len(
            [r for r in scores.get("style_results", [])
             if r.get("resolution") == "unresolved"])
        criteria += scores.get("n_criteria", 0)
        unresolved += n_unresolved
        errored += scores.get("n_errors", 0)
        if n_unresolved:
            affected.append(metadata_path.parent.name)
    if not criteria or not (unresolved or errored):
        return 0
    share = unresolved / criteria if criteria else 0
    print(
        f"\nWARNING: {unresolved:,} unresolved and {errored:,} errored verdict(s) "
        f"across {len(affected)} task(s) ({share:.0%} of criteria). Scores are "
        f"NOT usable as results — check judge.stderr.log / the vote records for "
        f"a judge that stopped answering, fix it, and re-run: cached votes are "
        f"reused, so only the missing ones are paid for again.",
        file=sys.stderr,
    )
    return 1


def already_judged(
    metadata_path: pathlib.Path, scores_name: str = "scores.json"
) -> bool:
    """True if this task has a complete scores.json with no error verdicts."""
    scores_path = metadata_path.parent / scores_name
    if not scores_path.exists():
        return False
    try:
        scores = json.loads(scores_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    results = scores.get("criteria_results")
    if not results:
        return False
    if any(r.get("verdict") == "error" for r in results):
        return False
    # An unresolved criterion means the committee could not decide — usually a
    # member that stopped answering. Treating that as "judged" would make a
    # resume skip exactly the tasks that need redoing.
    if scores.get("n_unresolved"):
        return False
    return not any(r.get("resolution") == "unresolved"
                   for r in scores.get("style_results", []))


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def task_metadata_paths(run_dir: pathlib.Path) -> list[pathlib.Path]:
    tasks_dir = run_dir / "tasks"
    if not tasks_dir.is_dir():
        raise SystemExit(f"Missing tasks directory: {tasks_dir}")
    return sorted(tasks_dir.glob("*/metadata.json"))


def judge_one(args: argparse.Namespace, metadata_path: pathlib.Path) -> tuple[pathlib.Path, int]:
    metadata = load_json(metadata_path)
    task_dir = pathlib.Path(metadata["source_task_dir"])
    submission_dir = metadata_path.parent / "submission"
    if not task_dir.exists():
        raise RuntimeError(f"Missing source task dir for {metadata_path}: {task_dir}")
    if not submission_dir.is_dir():
        raise RuntimeError(f"Missing submission dir for {metadata_path}: {submission_dir}")

    command = [
        args.python,
        "-m",
        "evaluation.run",
        str(task_dir),
        str(submission_dir),
        "--reasoning-effort",
        args.reasoning_effort,
    ]
    if args.judge_committee:
        # the committee defines its own judges; --judge-model/--votes would
        # either be ignored or rejected
        command.extend(["--judge-committee", str(args.judge_committee)])
    else:
        command.extend(["--judge-model", args.judge_model, "--votes", str(args.votes)])
        if args.judge_api_base:
            command.extend(["--judge-api-base", args.judge_api_base])
    if args.style_evaluation:
        command.append("--style-evaluation")
    if args.service_tier:
        command.extend(["--service-tier", args.service_tier])
    if args.committee_error_retries is not None:
        command.extend(["--committee-error-retries", str(args.committee_error_retries)])
    if args.committee_tiebreaker:
        command.append("--committee-tiebreaker")
    if args.vote_cache_dir is not None:
        command.extend(["--vote-cache-dir", str(args.vote_cache_dir)])
    if args.adaptive:
        command.append("--adaptive")
    command.extend(
        ["--output", str(submission_dir / args.scores_name)]
    )

    if args.dry_run:
        print(" ".join(command))
        return metadata_path, 0

    score_stem = pathlib.Path(args.scores_name).stem
    log_infix = "" if args.scores_name == "scores.json" else f".{score_stem}"
    stdout_path = metadata_path.parent / f"judge{log_infix}.stdout.log"
    stderr_path = metadata_path.parent / f"judge{log_infix}.stderr.log"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        result = subprocess.run(command, cwd=REPO_ROOT, stdout=stdout, stderr=stderr, check=False)

    submission_scores = submission_dir / args.scores_name
    task_scores = metadata_path.parent / args.scores_name
    if submission_scores.exists():
        shutil.copy2(submission_scores, task_scores)

    return metadata_path, result.returncode


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir if args.run_dir.is_absolute() else REPO_ROOT / args.run_dir
    if not (run_dir / "manifest.json").exists():
        raise SystemExit(f"Missing run manifest: {run_dir / 'manifest.json'}")

    config = apply_study(args)

    if args.no_vote_cache:
        args.vote_cache_dir = None
    elif args.vote_cache_dir is None:
        # one directory per run: the cache key hashes the full prompt, so votes
        # for different tasks and different answers can never collide
        args.vote_cache_dir = run_dir / "vote-cache"
    if args.vote_cache_dir is not None:
        args.vote_cache_dir.mkdir(parents=True, exist_ok=True)
    config["vote_cache_dir"] = str(args.vote_cache_dir) if args.vote_cache_dir else None

    paths = task_metadata_paths(run_dir)
    if not paths:
        raise SystemExit(f"No task metadata found under {run_dir / 'tasks'}")

    print(f"Judging {len(paths)} task(s) in {run_dir}")
    for key, value in config.items():
        if value not in (None, False):
            print(f"  {key}: {value}")
    if not args.dry_run:
        config_suffix = pathlib.Path(args.scores_name).stem
        config_name = (
            "judge_config.json"
            if args.scores_name == "scores.json"
            else f"judge_config.{config_suffix}.json"
        )
        (run_dir / config_name).write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    if args.skip_existing:
        kept = [p for p in paths if not already_judged(p, args.scores_name)]
        skipped = len(paths) - len(kept)
        if skipped:
            print(f"Skipping {skipped} already-judged task(s); {len(kept)} to judge.")
        paths = kept
        if not paths:
            print("All tasks already judged. Nothing to do.")
            return 1 if report_incomplete(
                run_dir, task_metadata_paths(run_dir), args.scores_name
            ) else 0

    failures = 0
    max_workers = max(1, args.parallel)
    if max_workers == 1:
        for path in paths:
            _path, code = judge_one(args, path)
            failures += int(code != 0)
            print(f"{path.parent.name}: judge_exit={code}")
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_path = {pool.submit(judge_one, args, path): path for path in paths}
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    _path, code = future.result()
                except Exception as exc:  # noqa: BLE001
                    failures += 1
                    print(f"{path.parent.name}: judge failed: {exc}", file=sys.stderr)
                    continue
                failures += int(code != 0)
                print(f"{path.parent.name}: judge_exit={code}")

    incomplete = report_incomplete(run_dir, paths, args.scores_name)
    return 1 if (failures or incomplete) else 0


if __name__ == "__main__":
    raise SystemExit(main())
