"""bwrap jail construction: argv shape and secret discipline.

Pure unit tests — no namespace is created here, so they run anywhere. The
escape probes that prove the invariant live in test_sandbox_bwrap_escape.py.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import sandbox_spec  # noqa: E402
from sandbox_spec import BwrapSpec  # noqa: E402


def make_spec(tmp_path: pathlib.Path, **overrides) -> BwrapSpec:
    for name in ("work", "task", "home"):
        (tmp_path / name).mkdir(exist_ok=True)
    kwargs = dict(
        workspace=tmp_path / "work",
        task_input=tmp_path / "task",
        home=tmp_path / "home",
        command=["opencode", "run", "prompt text"],
        env={"PATH": "/usr/bin", "HOME": sandbox_spec.JAIL_HOME},
    )
    kwargs.update(overrides)
    return BwrapSpec(**kwargs)


def test_argv_shape(tmp_path):
    argv = make_spec(tmp_path).to_argv()

    assert pathlib.Path(argv[0]).name == "bwrap"
    for flag in ("--die-with-parent", "--unshare-pid", "--unshare-ipc", "--new-session"):
        assert flag in argv
    # network stays shared: the agent loop calls the provider from inside
    assert "--unshare-net" not in argv

    index = argv.index("--bind")
    assert argv[index + 1] == str(tmp_path / "work")
    assert argv[index + 2] == sandbox_spec.JAIL_WORK
    assert ["--ro-bind", str(tmp_path / "task"), sandbox_spec.JAIL_TASK] == argv[
        argv.index(str(tmp_path / "task")) - 1 : argv.index(str(tmp_path / "task")) + 2
    ]

    # whitelist-by-construction: every --setenv comes after --clearenv
    assert "--clearenv" in argv
    assert argv.index("--clearenv") < argv.index("--setenv")
    assert argv[-3:] == ["opencode", "run", "prompt text"]


def test_absent_ro_source_is_skipped(tmp_path):
    spec = make_spec(tmp_path, ro_binds=[(tmp_path / "missing", "/opt/opencode")])
    assert "/opt/opencode" not in spec.to_argv()


def test_secret_values_never_reach_the_command_line(tmp_path):
    spec = make_spec(tmp_path, secret_env={"OPENROUTER_API_KEY": "sk-or-secret"})

    argv = spec.to_argv(args_fd=7)
    assert "sk-or-secret" not in argv
    assert argv[argv.index("--args") + 1] == "7"
    assert b"sk-or-secret" in spec.secret_args_blob()

    # the audit record names the variable but not its value
    redacted = spec.redacted_argv()
    assert "sk-or-secret" not in redacted
    assert "OPENROUTER_API_KEY" in redacted
    assert sandbox_spec.REDACTED in redacted
    assert "--args" not in redacted


def test_secret_without_fd_is_refused(tmp_path):
    spec = make_spec(tmp_path, secret_env={"OPENROUTER_API_KEY": "sk-or-secret"})
    with pytest.raises(ValueError, match="refusing"):
        spec.to_argv()


def test_jail_env_is_a_closed_whitelist():
    env = sandbox_spec.jail_env("{}", "task-1")
    assert env["HOME"] == sandbox_spec.JAIL_HOME
    assert env["PATH"].startswith(sandbox_spec.JAIL_OPENCODE_BIN)
    # no harness or provider secret names leak in through the non-secret env
    assert not [key for key in env if key.endswith("_API_KEY") or key.endswith("_KEY")]
