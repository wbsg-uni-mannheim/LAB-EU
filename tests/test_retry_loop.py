"""The retry loop, driven end-to-end through the real runner.

A stub solver stands in for OpenCode (``--sandbox local --opencode-bin``): it
fails the way OpenRouter failed on 2026-07-30 — an error event in the JSON
stream, non-zero exit — for a configured number of attempts, then succeeds.
That exercises the parts unit tests cannot reach: workspace reset between
attempts, archived diagnostics, and what lands in metadata.json.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "run_opencode_taskset.py"

STUB = r"""#!/bin/sh
# Stub solver. Counts its invocations; fails FAIL_TIMES times, then delivers.

# the runner probes the binary for the manifest before any task runs; that
# probe is not an attempt
if [ "$1" = "--version" ]; then echo "stub-0.0.0"; exit 0; fi

for a in "$@"; do
  if [ "$prev" = "--dir" ]; then workdir="$a"; fi
  prev="$a"
done

count=$(cat "$STUB_COUNTER" 2>/dev/null || echo 0)
count=$((count + 1))
echo "$count" > "$STUB_COUNTER"

# leave a partial file behind so a retry that fails to reset is visible
echo "partial junk from attempt $count" > "$workdir/scratch.md"

if [ "$count" -le "$FAIL_TIMES" ]; then
  printf '%s\n' '{"type":"error","error":{"data":{"message":"{\"code\":502,\"metadata\":{\"error_type\":\"provider_unavailable\"}}"}}}'
  exit 1
fi

if [ "$STUB_DELIVER" = "1" ]; then
  echo "# Loesung (attempt $count)" > "$workdir/loesung.md"
fi
printf '%s\n' '{"type":"step_finish","part":{"reason":"stop"}}'
exit 0
"""


@pytest.fixture()
def scenario(tmp_path):
    # the runner only accepts tasks under <repo>/tasks (resolve_under), so the
    # stub task has to live there; it is removed again on teardown
    task_dir = REPO_ROOT / "tasks" / "_pytest" / tmp_path.name
    (task_dir / "documents").mkdir(parents=True)
    (task_dir / "evals").mkdir()
    (task_dir / "documents" / "sachverhalt.md").write_text("Sachverhalt\n")
    (task_dir / "evals" / "rubric.json").write_text("{}\n")
    (task_dir / "task.json").write_text(json.dumps({
        "title": "Stub", "work_type": "draft", "instructions": "Loese den Fall.",
        "deliverables": "loesung.md",
    }))

    taskset = tmp_path / "taskset.jsonl"
    taskset.write_text(json.dumps({"task_id": "stub/case", "task_dir": str(task_dir)}) + "\n")

    stub = tmp_path / "stub-opencode"
    stub.write_text(STUB)
    stub.chmod(0o755)

    def run(fail_times: int, deliver: bool = True, max_attempts: int = 4):
        run_name = f"stub-{fail_times}-{int(deliver)}"
        env = dict(os.environ)
        env.update({
            "FAIL_TIMES": str(fail_times),
            "STUB_DELIVER": "1" if deliver else "0",
            "STUB_COUNTER": str(tmp_path / f"counter-{run_name}"),
        })
        result = subprocess.run(
            [sys.executable, str(RUNNER),
             "--taskset", str(taskset),
             "--sandbox", "local",
             "--opencode-bin", str(stub),
             "--runs-dir", str(tmp_path / "runs"),
             "--run-name", run_name,
             "--max-attempts", str(max_attempts),
             "--retry-base-delay", "0.05",
             "--skip-workspace-archive",
             "--timeout-seconds", "120"],
            capture_output=True, text=True, env=env, cwd=str(REPO_ROOT), timeout=300,
        )
        runs = sorted((tmp_path / "runs" / run_name).iterdir())
        assert runs, f"no run directory written; stderr:\n{result.stderr}"
        task_run_dir = runs[-1] / "tasks" / "stub__case"
        metadata = json.loads((task_run_dir / "metadata.json").read_text())
        return result, metadata, task_run_dir

    try:
        yield run
    finally:
        shutil.rmtree(task_dir, ignore_errors=True)


def test_transient_failures_are_retried_until_success(scenario):
    result, metadata, task_run_dir = scenario(fail_times=2)

    assert metadata["attempt_count"] == 3
    assert [a["outcome"] for a in metadata["attempts"]] == ["transient", "transient", "ok"]
    assert metadata["exit_code"] == 0
    assert metadata["missing_deliverables"] == []
    assert result.returncode == 0

    # each failed attempt keeps its own diagnostics
    for attempt in (1, 2):
        archived = task_run_dir / "attempts" / f"{attempt:02d}" / "stdout.jsonl"
        assert archived.exists(), f"missing diagnostics for attempt {attempt}"
        assert "provider_unavailable" in archived.read_text()


def test_retry_starts_from_a_clean_workspace(scenario):
    _result, _metadata, task_run_dir = scenario(fail_times=1)
    work = task_run_dir / "work"

    # the stub drops scratch.md on every attempt; exactly one must survive,
    # written by the final attempt — not carried over from the failed one
    assert work.joinpath("scratch.md").read_text().strip().endswith("attempt 2")
    assert "attempt 2" in work.joinpath("loesung.md").read_text()


def test_a_solver_failure_is_not_retried(scenario):
    """Exit 0 without a deliverable: the model had its chance. Repeating it
    would silently turn one benchmark score into best-of-N."""
    result, metadata, _ = scenario(fail_times=0, deliver=False)

    assert metadata["attempt_count"] == 1
    assert metadata["attempts"][0]["outcome"] == "solver"
    assert metadata["missing_deliverables"] == ["loesung.md"]
    assert result.returncode != 0


def test_attempts_are_bounded_by_max_attempts(scenario):
    result, metadata, task_run_dir = scenario(fail_times=99, max_attempts=3)

    assert metadata["attempt_count"] == 3
    assert [a["outcome"] for a in metadata["attempts"]] == ["transient"] * 3
    assert sorted(p.name for p in (task_run_dir / "attempts").iterdir()) == ["01", "02"]
    assert result.returncode != 0


def test_manifest_records_the_retry_policy(scenario):
    _result, metadata, task_run_dir = scenario(fail_times=0)
    manifest = json.loads((task_run_dir.parents[1] / "manifest.json").read_text())

    assert manifest["retry_policy"]["max_attempts"] == 4
    assert manifest["retry_policy"]["retried_outcomes"] == ["transient"]
    assert "solver" in manifest["retry_policy"]["never_retried"]
    assert metadata["attempt_count"] == 1
