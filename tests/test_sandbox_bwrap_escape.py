"""bwrap escape probes: the enforcement invariant, checked from inside.

These build a real jail and try, from inside it, to reach the things a solver
run must never see — the repository checkout, a task's ``evals/`` tree and its
gold solution, ``.env``, other runs, the host process table. Every probe must
fail, while the workspace and the sanitized task input must be readable.

Skipped where bwrap cannot build a namespace (macOS, hardened kernels).
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import sandbox_spec  # noqa: E402

_reason = sandbox_spec.bwrap_preflight()
pytestmark = pytest.mark.skipif(
    _reason is not None, reason=f"bwrap unavailable: {_reason}"
)


def jailed(tmp_path: pathlib.Path, script: str, secret_env=None) -> subprocess.CompletedProcess:
    """Run a shell script inside a jail built exactly like a solver task's."""
    work = tmp_path / "work"
    task = tmp_path / "task"
    home = tmp_path / "home"
    for path in (work, task, home):
        path.mkdir(exist_ok=True)
    (work / "canary.txt").write_text("workspace is visible\n")
    (task / "task.json").write_text("{}\n")

    spec = sandbox_spec.BwrapSpec(
        workspace=work.resolve(),
        task_input=task.resolve(),
        home=home.resolve(),
        command=["/bin/sh", "-c", script],
        env=sandbox_spec.jail_env("{}", "probe"),
        secret_env=secret_env or {},
    )
    process = sandbox_spec.spawn(
        spec, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    stdout, _ = process.communicate(timeout=60)
    return subprocess.CompletedProcess(
        spec.redacted_argv(), process.returncode, stdout.decode(errors="replace"), ""
    )


def test_workspace_and_task_input_are_visible(tmp_path):
    result = jailed(tmp_path, "cat /work/canary.txt && ls /task/task.json")
    assert result.returncode == 0, result.stdout
    assert "workspace is visible" in result.stdout


def test_repo_gold_and_secrets_do_not_exist_in_jail(tmp_path):
    forbidden = [
        str(REPO_ROOT),                      # the whole checkout
        str(REPO_ROOT / ".env"),             # provider credentials
        str(REPO_ROOT / "tasks"),            # every task incl. evals/ and gold
        str(REPO_ROOT / "runs"),             # other runs and their submissions
        str(REPO_ROOT / "scripts"),          # harness source
        str(pathlib.Path.home()),            # host dotfiles, opencode auth.json
    ]
    script = "\n".join(f'ls {path} >/dev/null 2>&1 && echo "BREACH {path}"' for path in forbidden)
    result = jailed(tmp_path, script + "\ntrue\n")
    assert "BREACH" not in result.stdout, result.stdout


def test_task_evals_are_unreachable_by_absolute_path(tmp_path):
    """The sanitized copy is not the whole story: the ORIGINAL task directory
    still holds evals/ and the gold solution, and a capable agent can guess an
    absolute path. In the jail that path does not resolve at all."""
    evals = sorted(path for path in (REPO_ROOT / "tasks").rglob("evals") if path.is_dir())
    if not evals:
        pytest.skip("no task with evals/ in this checkout")
    target = evals[0]
    result = jailed(tmp_path, f'ls {target} >/dev/null 2>&1 && echo "BREACH"; true')
    assert "BREACH" not in result.stdout


def test_environment_is_the_declared_whitelist(tmp_path):
    result = jailed(tmp_path, "env | sort")
    seen = {line.split("=", 1)[0] for line in result.stdout.splitlines() if "=" in line}
    expected = set(sandbox_spec.jail_env("{}", "probe"))
    # PWD/SHLVL/_ are added by the shell itself, not inherited from the host
    assert seen - expected <= {"PWD", "SHLVL", "_"}


def test_provider_key_reaches_the_jail_but_not_the_command_line(tmp_path):
    result = jailed(
        tmp_path,
        'echo "KEY=$OPENROUTER_API_KEY"',
        secret_env={"OPENROUTER_API_KEY": "sk-or-probe-value"},
    )
    assert "KEY=sk-or-probe-value" in result.stdout
    # ...and the recorded argv (metadata.json, host `ps`) never carries it
    assert "sk-or-probe-value" not in " ".join(result.args)


def test_jail_cannot_see_host_processes(tmp_path):
    result = jailed(tmp_path, "ls /proc | grep -c '^[0-9]*$'")
    # a PID namespace of its own: the shell, grep and ls — not the host's table
    assert int(result.stdout.strip().splitlines()[-1]) < 10


def test_workspace_is_writable_and_task_input_is_not(tmp_path):
    result = jailed(
        tmp_path,
        'echo ok > /work/out.md && echo WROTE_WORK; '
        'echo bad > /task/task.json 2>/dev/null && echo BREACH_TASK_WRITABLE; true',
    )
    assert "WROTE_WORK" in result.stdout
    assert "BREACH_TASK_WRITABLE" not in result.stdout
    assert (tmp_path / "work" / "out.md").read_text() == "ok\n"
