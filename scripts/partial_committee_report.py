#!/usr/bin/env python3
"""Read a study's result out of the vote cache, using only some committee members.

When one judge is unavailable, the cached votes of the others are still there.
Two judges cannot outvote each other, so this reports what they agree on and
keeps the rest explicitly undecided rather than resolving it silently — the
undecided band is the honest measure of how much the missing judge could still
move the numbers.

    python scripts/partial_committee_report.py runs/a/<id> runs/b/<id> \
        --study studies/de-core-45/study.json

Reads only cache files; makes no API calls.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from evaluation.run import (  # noqa: E402
    DEFAULT_API_BASE,
    combined_content_style_prompt,
    is_style_eligible_criterion,
    judge_prompt,
    load_agent_output,
    load_json,
    load_judge_committee,
    load_rubric,
    load_style_profiles,
    vote_cache_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Partial-committee readout from cached votes.")
    parser.add_argument("run_dirs", nargs="+", type=pathlib.Path)
    parser.add_argument("--study", type=pathlib.Path, required=True)
    parser.add_argument("--json", type=pathlib.Path, default=None)
    return parser.parse_args()


def read_verdicts(cache_dir, phase, specs, criterion_id, prompt, combined):
    """Cached (content, style) verdicts per judge; None where a vote is missing."""
    content, style = [], []
    for spec in specs:
        path = vote_cache_path(cache_dir, phase, spec, criterion_id, prompt)
        if path is None or not path.exists():
            content.append(None); style.append(None); continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            content.append(None); style.append(None); continue
        if combined:
            content.append(data.get("content", {}).get("verdict"))
            style.append(data.get("style", {}).get("verdict"))
        else:
            content.append(data.get("verdict"))
            style.append(None)
    return content, style


def resolve(verdicts: list[str | None]) -> str:
    """Unanimous verdicts count; anything else stays undecided."""
    known = [v for v in verdicts if v in ("pass", "fail")]
    if len(known) < len(verdicts) or not known:
        return "missing"
    if all(v == "pass" for v in known):
        return "pass"
    if all(v == "fail" for v in known):
        return "fail"
    return "split"


def main() -> int:
    args = parse_args()
    study = json.loads((args.study if args.study.is_absolute()
                        else REPO_ROOT / args.study).read_text(encoding="utf-8"))
    committee = study["evaluation"]["judge_committee"]
    specs = [s for s in load_judge_committee(REPO_ROOT / committee)
             if s.api_base == DEFAULT_API_BASE]
    style_on = not study["evaluation"].get("aggregate_content_and_style", True)
    print(f"Judges read from cache: {', '.join(s.name for s in specs)}\n")

    report = {}
    for run_dir in args.run_dirs:
        run_dir = run_dir if run_dir.is_absolute() else REPO_ROOT / run_dir
        cache_dir = run_dir / "vote-cache"
        content_counts, style_counts = Counter(), Counter()
        by_criticality = {1: Counter(), 2: Counter(), 3: Counter()}
        tasks = 0
        no_submission = 0
        for metadata_path in sorted((run_dir / "tasks").glob("*/metadata.json")):
            metadata = load_json(metadata_path)
            submission = metadata_path.parent / "submission"
            task_dir = pathlib.Path(metadata["source_task_dir"])
            # A task without a deliverable is "no submission", not a task that
            # failed every criterion. Counting it as failures would silently
            # penalise an arm for a provider refusal (the de-core-45 DeepSeek
            # agent arm lost one case to a content filter) — and the judge's
            # own scores.json living under submission/ makes the directory look
            # non-empty, so the deliverable list is what has to be checked.
            if metadata.get("missing_deliverables"):
                no_submission += 1
                continue
            if not submission.is_dir() or not any(submission.iterdir()):
                no_submission += 1
                continue
            tasks += 1
            task = load_json(task_dir / "task.json")
            rubric_path, criteria = load_rubric(task_dir)
            style_profiles = load_style_profiles(rubric_path) if style_on else None
            for criterion in criteria:
                output = load_agent_output(submission, criterion)
                combined = style_on and is_style_eligible_criterion(criterion)
                phase = "combined-r1" if combined else "content-r1"
                prompt = (combined_content_style_prompt(
                              task, task_dir, output, criterion, style_profiles)
                          if combined else judge_prompt(task, task_dir, output, criterion))
                content, style = read_verdicts(
                    cache_dir, phase, specs, criterion["id"], prompt, combined)
                outcome = resolve(content)
                content_counts[outcome] += 1
                crit = criterion.get("criticality")
                if crit in by_criticality:
                    by_criticality[crit][outcome] += 1
                if combined:
                    style_counts[resolve(style)] += 1
        report[run_dir.parent.name] = {
            "tasks": tasks,
            "no_submission": no_submission,
            "content": dict(content_counts),
            "style": dict(style_counts),
            "by_criticality": {k: dict(v) for k, v in by_criticality.items()},
        }

    decided = lambda c: c.get("pass", 0) + c.get("fail", 0)  # noqa: E731
    print(f"{'run':<32}{'scored':>7}{'no sub':>7}{'content':>10}{'undecided':>11}{'style':>9}")
    for name, data in report.items():
        c, s = data["content"], data["style"]
        total = sum(c.values())
        rate = c.get("pass", 0) / decided(c) if decided(c) else 0
        undecided = (c.get("split", 0) + c.get("missing", 0)) / total if total else 0
        srate = s.get("pass", 0) / decided(s) if decided(s) else 0
        print(f"{name:<32}{data['tasks']:>7}{data['no_submission']:>7}"
              f"{rate:>9.1%}{undecided:>11.1%}{srate:>8.1%}")

    print(f"\n{'run':<32}" + "".join(f"{f'crit {k}':>12}" for k in (3, 2, 1)))
    for name, data in report.items():
        cells = ""
        for k in (3, 2, 1):
            c = data["by_criticality"][k]
            d = decided(c)
            cells += f"{(c.get('pass', 0) / d if d else 0):>11.1%} "
        print(f"{name:<32}{cells}")

    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
        print(f"\nWrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
