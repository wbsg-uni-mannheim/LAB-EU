#!/usr/bin/env python3
"""Compare two judged LAB-EU runs task by task and by rubric category.

Reads scores.json from each task's submission directory in both runs and prints
per-task pass rates, per-criterion verdict flips, and station/function
breakdowns side by side. Use it to measure what a harness adds over a baseline.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two judged LAB-EU runs.")
    parser.add_argument("run_a", type=pathlib.Path, help="First run dir (e.g. the baseline).")
    parser.add_argument("run_b", type=pathlib.Path, help="Second run dir (e.g. the harness).")
    parser.add_argument("--label-a", default="A")
    parser.add_argument("--label-b", default="B")
    return parser.parse_args()


def load_scores(run_dir: pathlib.Path) -> dict[str, dict[str, Any]]:
    run_dir = run_dir if run_dir.is_absolute() else REPO_ROOT / run_dir
    scores: dict[str, dict[str, Any]] = {}
    for path in sorted((run_dir / "tasks").glob("*/submission/scores.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        scores[data["task"]["path"]] = data
    if not scores:
        raise SystemExit(f"No scored submissions under {run_dir}/tasks/*/submission/scores.json")
    return scores


def verdicts(score: dict[str, Any]) -> dict[str, str]:
    return {r["id"]: r["verdict"] for r in score["criteria_results"]}


def bar(rate: float, width: int = 16) -> str:
    return "#" * round(width * rate) + "." * (width - round(width * rate))


def main() -> int:
    args = parse_args()
    a = load_scores(args.run_a)
    b = load_scores(args.run_b)
    la, lb = args.label_a, args.label_b
    shared = [t for t in a if t in b]
    if not shared:
        raise SystemExit("The two runs share no tasks.")

    tot_a = tot_b = n = 0
    print(f"\n{'TASK':<48} {la:>18} {lb:>18}   delta")
    print("-" * 92)
    for task in shared:
        sa, sb = a[task], b[task]
        na, nb = sa["n_passed"], sb["n_passed"]
        tot = sa["n_criteria"]
        tot_a += na
        tot_b += nb
        n += tot
        title = sa["task"]["title"][:46]
        d = nb - na
        print(f"{title:<48} {na:>3}/{tot} ({na/tot:>4.0%}) {nb:>7}/{tot} ({nb/tot:>4.0%})  {d:+4d}")
    print("-" * 92)
    print(f"{'TOTAL':<48} {tot_a:>3}/{n} ({tot_a/n:>4.0%}) {tot_b:>7}/{n} ({tot_b/n:>4.0%})  {tot_b-tot_a:+4d}")

    # Category breakdowns aggregated across shared tasks
    for axis, key in [("station", "breakdown_by_station"), ("function", "breakdown_by_function")]:
        agg: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])  # a_pass, a_tot, b_pass, b_tot
        for task in shared:
            for src, off in [(a[task], 0), (b[task], 2)]:
                for cat, grp in (src.get(key) or {}).items():
                    agg[cat][off] += grp["n_passed"]
                    agg[cat][off + 1] += grp["n_criteria"]
        if not agg:
            continue
        print(f"\nBy {axis}:")
        print(f"  {'category':<40} {la:>14} {lb:>14}")
        for cat, (ap, at, bp, bt) in sorted(agg.items(), key=lambda x: -x[1][1]):
            ar = ap / at if at else 0
            br = bp / bt if bt else 0
            print(f"  {cat:<40} {ap:>2}/{at:<2} {ar:>4.0%} {bar(ar)} {bp:>2}/{bt:<2} {br:>4.0%} {bar(br)}")

    # Where the two runs disagree per criterion
    only_a: list[tuple[str, str, str]] = []
    only_b: list[tuple[str, str, str]] = []
    for task in shared:
        va, vb = verdicts(a[task]), verdicts(b[task])
        titles = {r["id"]: r["title"] for r in a[task]["criteria_results"]}
        short = task.split("/")[-1][:24]
        for cid in va:
            if va[cid] == "pass" and vb.get(cid) == "fail":
                only_a.append((short, cid, titles.get(cid, "")))
            elif va[cid] == "fail" and vb.get(cid) == "pass":
                only_b.append((short, cid, titles.get(cid, "")))
    print(f"\nCriteria only {lb} passes ({len(only_b)}):")
    for t, cid, title in only_b:
        print(f"  [{t}] {cid} - {title[:58]}")
    print(f"\nCriteria only {la} passes ({len(only_a)}):")
    for t, cid, title in only_a:
        print(f"  [{t}] {cid} - {title[:58]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
