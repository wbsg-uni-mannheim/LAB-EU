"""Every row of the de-core-45 CSV has to point at a score file that says the same.

The published table once drifted away from the tree it claimed to summarise: the
numbers came out of a vote-cache pass that never wrote score files, while the
scores.json sitting in the run directories were a failed judging job whose third
committee member had returned 403 for most criteria. Both looked fine in
isolation. This pins the two together, so a row that no longer matches its
scores.json fails here rather than in somebody's analysis.
"""

from __future__ import annotations

import csv
import json
import pathlib
import subprocess
import sys
from collections import Counter

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CSV_PATH = REPO_ROOT / "runs" / "de-core-45-final.csv"

# The six study arms, in the order the CSV lists them.
ARMS = [
    ("Sol", "Agent", "agent-gpt-5.6-sol-high/20260730T221733Z"),
    ("Sol", "Baseline", "baseline-gpt-5.6-sol-high/20260730T221734Z"),
    ("Terra", "Agent", "agent-gpt-5.6-terra-high/20260730T221733Z"),
    ("Terra", "Baseline", "baseline-gpt-5.6-terra-high/20260730T221744Z"),
    ("DeepSeek", "Agent", "agent-deepseek-v4-pro-medium/20260730T214602Z"),
    ("DeepSeek", "Baseline", "baseline-deepseek-v4-pro/20260730T221734Z"),
]
RUN_DIR = {(model, methode): path for model, methode, path in ARMS}


def rows():
    with CSV_PATH.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.skipif(not CSV_PATH.exists(), reason="results CSV not present")
def test_every_scored_row_matches_its_scores_json():
    mismatches = []
    checked = 0
    for row in rows():
        if row["status"] != "ok":
            continue
        run = RUN_DIR[(row["model"], row["methode"])]
        task = row["task_id"].replace("/", "__")
        path = REPO_ROOT / "runs" / run / "tasks" / task / "scores.json"
        if not path.exists():
            mismatches.append(f"{run}/{task}: no scores.json")
            continue
        content = json.loads(path.read_text(encoding="utf-8"))["content_score"]
        found = (content["n_passed"], content["n_criteria"])
        want = (int(row["content_passed"]), int(row["content_criteria"]))
        if found != want:
            mismatches.append(f"{run}/{task}: csv {want} vs scores.json {found}")
        checked += 1
    assert checked, "no scored rows were checked"
    assert not mismatches, "\n".join(mismatches[:20])


@pytest.mark.skipif(not CSV_PATH.exists(), reason="results CSV not present")
def test_no_scored_row_rests_on_unresolved_criteria():
    """An unresolved criterion is a missing verdict, not a failed one.

    The 2026-07-31 job produced whole cases where every criterion was unresolved
    and the pass rate read 0.0 with n_errors: 0 — indistinguishable from a real
    zero unless the unresolved count is checked.
    """
    offenders = []
    for row in rows():
        if row["status"] != "ok":
            continue
        run = RUN_DIR[(row["model"], row["methode"])]
        task = row["task_id"].replace("/", "__")
        path = REPO_ROOT / "runs" / run / "tasks" / task / "scores.json"
        if not path.exists():
            continue
        scores = json.loads(path.read_text(encoding="utf-8"))
        unresolved = scores["content_score"].get("n_unresolved", 0)
        if unresolved:
            offenders.append(f"{run}/{task}: {unresolved} unresolved")
    assert not offenders, "\n".join(offenders[:20])


def test_csv_reproduces_byte_for_byte(tmp_path):
    output = tmp_path / "results.csv"
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/build_study_results_csv.py"),
         *[str(REPO_ROOT / "runs" / run) for _, _, run in ARMS],
         "--output", str(output)],
        check=True, capture_output=True, text=True,
    )
    assert output.read_bytes() == CSV_PATH.read_bytes()


def test_published_verdicts_and_both_aggregates_follow_recorded_votes():
    totals = Counter()
    for row in rows():
        run = RUN_DIR[(row["model"], row["methode"])]
        task = row["task_id"].replace("/", "__")
        task_root = REPO_ROOT / "runs" / run / "tasks" / task
        path = task_root / "scores.json"
        if row["status"] != "ok":
            assert row["status"] == "keine Abgabe"
            assert not path.exists()
            assert json.loads((task_root / "metadata.json").read_text())["missing_deliverables"]
            totals["no_submission"] += 1
            continue
        scores = json.loads(path.read_text())
        totals["scored"] += 1
        for group, aggregate, count_key in (
            ("criteria_results", "content_score", "n_criteria"),
            ("style_results", "style_score", "n_eligible"),
        ):
            results = scores[group]
            assert len({c["id"] for c in results}) == len(results)
            assert scores[aggregate][count_key] == len(results)
            assert scores[aggregate]["n_passed"] == sum(c["verdict"] == "pass" for c in results)
            for criterion in results:
                assert criterion["verdict"] in ("pass", "fail")
                assert criterion["reasoning"]
                primary = [v for v in criterion["votes"] if v["role"] == "primary"]
                tie = [v for v in criterion["votes"] if v["role"] == "tiebreak"]
                assert len(primary) == 2
                assert {v["judge"]["name"] for v in primary} == {"luna", "terra"}
                assert all(v["verdict"] in ("pass", "fail") for v in primary + tie)
                if primary[0]["verdict"] == primary[1]["verdict"]:
                    assert not tie and not criterion["tiebreak_used"]
                    assert criterion["verdict"] == primary[0]["verdict"]
                else:
                    assert len(tie) == 1 and criterion["tiebreak_used"]
                    assert tie[0]["judge"]["name"] == "gemini-3.6-flash"
                    assert criterion["verdict"] == tie[0]["verdict"]
    assert totals == {"scored": 269, "no_submission": 1}
