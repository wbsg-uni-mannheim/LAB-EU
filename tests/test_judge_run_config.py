"""judge_run drives evaluation.run — these tests pin what it actually asks for.

The study declares a judge committee and separate style scoring; if the driver
silently drops either, the run still produces scores and nobody notices that
they came from a different configuration than the one on record.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DRIVER = REPO_ROOT / "scripts" / "judge_run.py"
STUDY = REPO_ROOT / "studies" / "de-core-45" / "study.json"


@pytest.fixture()
def run_dir(tmp_path):
    task_dir = sorted(
        p.parent for p in (REPO_ROOT / "tasks").rglob("evals/rubric.json")
    )[0]
    run = tmp_path / "run"
    task_run = run / "tasks" / "stub"
    (task_run / "submission").mkdir(parents=True)
    (task_run / "submission" / "loesung.md").write_text("# Loesung\n")
    (run / "manifest.json").write_text("{}")
    (task_run / "metadata.json").write_text(json.dumps({
        "task_id": "stub/case", "source_task_dir": str(task_dir),
    }))
    return run


def plan(run_dir: pathlib.Path, *extra: str) -> str:
    result = subprocess.run(
        [sys.executable, str(DRIVER), str(run_dir), "--dry-run", *extra],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_study_supplies_committee_and_style(run_dir):
    out = plan(run_dir, "--study", str(STUDY))
    assert "--judge-committee" in out
    assert "judge-committee-professor-pilot.json" in out
    assert "--style-evaluation" in out
    # the committee defines the judges; a single-judge model would be ignored
    assert "--judge-model" not in out
    assert "--votes" not in out


def test_vote_cache_defaults_into_the_run_directory(run_dir):
    out = plan(run_dir, "--study", str(STUDY))
    assert f"--vote-cache-dir {run_dir / 'vote-cache'}" in out
    assert "--vote-cache-dir" not in plan(run_dir, "--no-vote-cache")


def test_explicit_flags_beat_the_study(run_dir):
    out = plan(run_dir, "--study", str(STUDY), "--no-style-evaluation")
    assert "--style-evaluation" not in out
    assert "--judge-committee" in out


def test_default_stays_single_judge(run_dir):
    out = plan(run_dir)
    assert "--judge-model gpt-5.5" in out
    assert "--votes 1" in out
    assert "--judge-committee" not in out
    assert "--style-evaluation" not in out


def test_committee_with_multiple_votes_is_refused(run_dir):
    result = subprocess.run(
        [sys.executable, str(DRIVER), str(run_dir), "--study", str(STUDY),
         "--votes", "3", "--dry-run"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=120,
    )
    assert result.returncode != 0
    assert "one vote per member" in result.stderr


def test_missing_committee_file_fails_before_any_task(run_dir):
    result = subprocess.run(
        [sys.executable, str(DRIVER), str(run_dir), "--judge-committee",
         "configs/does-not-exist.json", "--dry-run"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=120,
    )
    assert result.returncode != 0
    assert "Missing judge committee file" in result.stderr
