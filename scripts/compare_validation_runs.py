#!/usr/bin/env python3
"""Compare judge configurations against the jurist labels of the validation sample.

Each run directory comes from scripts/rescore_validation_sample.py (ideally with
--full-votes, so every committee member voted on every row). Prints, per run, the
accuracy of each single judge, the three-judge majority and the tiebreak rule,
split into too strict / too lenient and by solver family. The published judge
(the verdict shown to the jurist) is listed as "published".
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from rescore_validation_sample import load_rows


def run_votes(run_dir: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    votes = {}
    for path in (run_dir / "scores").glob("*.json"):
        for result in json.loads(path.read_text())["criteria_results"]:
            votes[(path.stem, result["id"])] = {
                v["judge"]["name"]: v["verdict"] for v in result.get("votes", [])
            }
    return votes


def tally(rows: list[dict], predict) -> str:
    c = Counter()
    for row in rows:
        p = predict(row)
        fam = "DS" if row["arm"].startswith("DeepSeek") else "OAI"
        c["ok"] += p == row["gold"]
        c["strict"] += p == "fail" and row["gold"] == "pass"
        c["lenient"] += p == "pass" and row["gold"] == "fail"
        if row["gold"] == "pass":
            c[f"pos_{fam}"] += 1
            c[f"strict_{fam}"] += p == "fail"
    return (f"{c['ok']}/{len(rows)}  streng {c['strict']}  großzügig {c['lenient']}  "
            f"| streng DS {c['strict_DS']}/{c['pos_DS']}  OAI {c['strict_OAI']}/{c['pos_OAI']}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("runs", type=Path, nargs="+")
    p.add_argument("--xlsx", type=Path, required=True)
    p.add_argument("--part", type=int, default=1)
    p.add_argument("--gold-overrides", type=Path)
    args = p.parse_args()

    overrides = json.loads(args.gold_overrides.read_text())["gold"] if args.gold_overrides else None
    rows = [r for r in load_rows(args.xlsx, args.part, overrides) if r["gold"]]
    print(f"{'published':42} {tally(rows, lambda r: r['old'])}")
    for run in args.runs:
        votes = run_votes(run)

        def get(row: dict) -> dict[str, str]:
            key = f"{row['task_id'].replace('/', '__')}__{row['arm'].replace(' · ', '-')}"
            return votes[(key, row["criterion"])]

        judges = list(get(rows[0]))
        print(run.name)
        for name in judges:
            print(f"  {name:40} {tally(rows, lambda r, n=name: get(r).get(n, 'missing'))}")
        if len(judges) == 3:
            a, b, c = judges
            print(f"  {'Mehrheit aus 3':40} "
                  f"{tally(rows, lambda r: 'pass' if list(get(r).values()).count('pass') >= 2 else 'fail')}")
            print(f"  {f'{a}+{b}, {c} als Tiebreaker':40} "
                  f"{tally(rows, lambda r: get(r)[a] if get(r)[a] == get(r)[b] else get(r)[c])}")


if __name__ == "__main__":
    main()
