#!/usr/bin/env python3
"""bwrap jail construction for the OpenCode solver harness.

This is the Linux/cluster enforcement profile, modelled on the AgenticDI
harness (its ``plans/m6_isolation.md``): the agent process runs inside a
filesystem + PID namespace in which the repository, the task's ``evals/``
tree, gold solutions, ``.env`` and every other run simply do not exist.
Leakage protection stops being "the runner only copies sanitized inputs" and
becomes a kernel namespace property.

Why a second profile at all: the Docker profile (``docker/``) needs a Docker
daemon, which compute nodes typically do not have. bwrap runs unprivileged in
a user namespace, so the same enforcement invariant is available on the
cluster.

Jail layout (deliberately identical to the Docker profile so traces, prompts
and deliverable paths are comparable across profiles):

    /task            ro   sanitized task input (task.json + documents/)
    /work            rw   the agent's workspace
    /home/agent      rw   OpenCode's own state (kept out of /work)
    /opt/opencode    ro   the vendored OpenCode CLI
    /tmp             tmpfs
    /usr /bin ...    ro   system runtime

Note that ``/work`` is also a real path on the cluster (``/work/<user>/...``,
where this repository lives). Mounting the workspace there is not incidental:
it shadows the entire host ``/work`` tree, so no absolute path the agent might
guess can reach the repo checkout.

Secret discipline: ``--clearenv`` makes the jail environment a whitelist by
construction, and the whitelist is emitted as ``--setenv`` pairs. Values that
are secrets (the provider API key) are NOT put on the command line — host
``ps`` is world-readable on a shared cluster and the runner records the argv
in ``metadata.json``. They travel through ``--args FD`` instead, a pipe that
only bwrap reads. :func:`BwrapSpec.redacted_argv` is what gets recorded.

Network namespaces are NOT unshared: the agent loop reaches the LLM provider
from inside the jail. Agent egress therefore stays policy-guarded (OpenCode's
``webfetch``/``websearch`` permissions are denied in the harness config), not
enforced — the same posture AgenticDI ships.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# System trees a Linux userland needs read-only. /lib64 and /etc are absent on
# some distros; absent sources are skipped at build time.
DEFAULT_RO_SYSTEM = ("/usr", "/bin", "/sbin", "/lib", "/lib64", "/etc")

JAIL_TASK = "/task"
JAIL_WORK = "/work"
JAIL_HOME = "/home/agent"
JAIL_OPENCODE = "/opt/opencode"
JAIL_OPENCODE_BIN = f"{JAIL_OPENCODE}/node_modules/.bin"

REDACTED = "***"


def bwrap_bin() -> str:
    """Absolute path to bwrap. Resolved here rather than left to the exec-time
    PATH lookup, because the jail is spawned with an empty environment — and it
    also puts the exact binary that ran into the audit record."""
    return shutil.which("bwrap") or "bwrap"


def vendored_opencode_bin(opencode_dir: Path) -> Path:
    """The CLI entry point inside a ``npm install --prefix <dir> opencode-ai``
    tree. The launcher hardlinks the platform binary inside the same tree, so
    binding the tree alone yields a working CLI (no node, no network)."""
    return Path(opencode_dir) / "node_modules" / ".bin" / "opencode"


def opencode_version(opencode_bin: str | Path) -> str:
    try:
        result = subprocess.run(
            [str(opencode_bin), "--version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


@dataclass
class BwrapSpec:
    """One task's jail: what exists inside, what runs, with which environment."""

    workspace: Path                                     # rw -> /work
    task_input: Path                                    # ro -> /task
    home: Path                                          # rw -> /home/agent
    command: list[str]
    ro_binds: list[tuple[Path, str]] = field(default_factory=list)
    ro_system: tuple = DEFAULT_RO_SYSTEM
    env: dict[str, str] = field(default_factory=dict)
    # never placed on the command line; delivered through --args FD
    secret_env: dict[str, str] = field(default_factory=dict)
    unshare_net: bool = False

    def _base_argv(self) -> list[str]:
        argv = [
            bwrap_bin(),
            "--die-with-parent",
            "--unshare-pid",
            "--unshare-ipc",
            "--unshare-uts",
            "--new-session",
            "--proc", "/proc",
            "--dev", "/dev",
            "--tmpfs", "/tmp",
        ]
        if self.unshare_net:
            argv.append("--unshare-net")
        for src in self.ro_system:
            if Path(src).exists():
                argv += ["--ro-bind", str(src), str(src)]
        for src, dest in self.ro_binds:
            if Path(src).exists():
                argv += ["--ro-bind", str(src), dest]
        argv += ["--ro-bind", str(self.task_input), JAIL_TASK]
        argv += ["--bind", str(self.workspace), JAIL_WORK]
        argv += ["--bind", str(self.home), JAIL_HOME]
        argv += ["--chdir", JAIL_WORK]
        # everything after this point is whitelist-by-construction
        argv += ["--clearenv"]
        for key in sorted(self.env):
            argv += ["--setenv", key, self.env[key]]
        return argv

    def secret_args_blob(self) -> bytes:
        """NUL-separated bwrap arguments for the secret --setenv pairs."""
        parts: list[str] = []
        for key in sorted(self.secret_env):
            parts += ["--setenv", key, self.secret_env[key]]
        return b"".join(part.encode() + b"\0" for part in parts)

    def to_argv(self, args_fd: int | None = None) -> list[str]:
        """The real argv. ``args_fd`` must be an inheritable read end holding
        :meth:`secret_args_blob` whenever ``secret_env`` is non-empty."""
        argv = self._base_argv()
        if self.secret_env:
            if args_fd is None:
                raise ValueError(
                    "secret_env is set but no args_fd was provided — refusing "
                    "to put secret values on the command line"
                )
            argv += ["--args", str(args_fd)]
        argv += ["--", *self.command]
        return argv

    def redacted_argv(self) -> list[str]:
        """The full jail specification for the audit record, with secret
        values replaced. This is what belongs in ``metadata.json``."""
        argv = self._base_argv()
        for key in sorted(self.secret_env):
            argv += ["--setenv", key, REDACTED]
        argv += ["--", *self.command]
        return argv


def spawn(spec: BwrapSpec, **popen_kwargs) -> subprocess.Popen:
    """Start the jail, delivering ``secret_env`` over a pipe.

    The environment of the bwrap process itself is emptied as well: with
    ``--clearenv`` it cannot reach the child, but an empty parent environment
    means an accidental removal of ``--clearenv`` still cannot leak the
    harness environment into the jail.
    """
    if not spec.secret_env:
        return subprocess.Popen(spec.to_argv(), env={}, **popen_kwargs)

    read_fd, write_fd = os.pipe()
    try:
        os.set_inheritable(read_fd, True)
        os.write(write_fd, spec.secret_args_blob())  # small; no deadlock risk
        os.close(write_fd)
        write_fd = -1
        return subprocess.Popen(
            spec.to_argv(read_fd),
            env={},
            pass_fds=(read_fd,),
            **popen_kwargs,
        )
    finally:
        if write_fd != -1:
            os.close(write_fd)
        os.close(read_fd)


def bwrap_preflight() -> str | None:
    """None when bwrap can build a namespace here; otherwise the reason."""
    try:
        proc = subprocess.run(
            ["bwrap", "--version"], capture_output=True, text=True, timeout=10
        )
    except FileNotFoundError:
        return "bwrap not installed (Linux only; install bubblewrap)"
    except (subprocess.TimeoutExpired, OSError) as exc:
        return f"bwrap not runnable: {exc}"
    if proc.returncode != 0:
        return f"bwrap --version failed: {proc.stderr.strip()[:200]}"

    # Cheapest namespace smoke: /bin/true inside a jail. The binds come from
    # DEFAULT_RO_SYSTEM rather than a shorter hardcoded list: on distros where
    # /lib64 is its own symlink (RHEL 9 x86_64 — the cluster) omitting it hides
    # the ELF loader and every binary fails with a bare "No such file or
    # directory", i.e. a preflight that fails where the real jail works.
    probe_binds: list[str] = []
    for src in DEFAULT_RO_SYSTEM:
        if Path(src).exists():
            probe_binds += ["--ro-bind", src, src]
    probe = subprocess.run(
        ["bwrap", "--die-with-parent", "--unshare-pid", "--proc", "/proc",
         "--dev", "/dev", *probe_binds, "--", "/bin/true"],
        capture_output=True, text=True, timeout=30,
    )
    if probe.returncode != 0:
        return ("bwrap namespace probe failed (unprivileged user namespaces "
                f"disabled?): {probe.stderr.strip()[:200]}")
    return None


def opencode_preflight(opencode_dir: Path,
                       workdir: Path | None = None) -> str | None:
    """None when the vendored CLI actually executes inside the jail.

    Checking that the binary exists on the host is not enough: a tool that
    starts outside and dies inside costs a whole run (AgenticDI lost episodes
    to exactly this with a tmux build that accepted ``new-session`` and then
    died on the first pane access). So this runs the real binary, through the
    real binds, and insists on seeing its version.
    """
    opencode_dir = Path(opencode_dir)
    if not vendored_opencode_bin(opencode_dir).exists():
        return (f"vendored OpenCode CLI not found under {opencode_dir} — run "
                "scripts/install_opencode.sh")

    binds: list[str] = []
    for src in DEFAULT_RO_SYSTEM:
        if Path(src).exists():
            binds += ["--ro-bind", src, src]
    binds += ["--ro-bind", str(opencode_dir.resolve()), JAIL_OPENCODE]

    parent = str(workdir) if workdir else None
    with tempfile.TemporaryDirectory(dir=parent) as tmp:
        home = Path(tmp) / "home"
        work = Path(tmp) / "work"
        home.mkdir()
        work.mkdir()
        argv = [
            "bwrap", "--die-with-parent", "--unshare-pid", "--unshare-ipc",
            "--unshare-uts", "--new-session", "--proc", "/proc", "--dev",
            "/dev", "--tmpfs", "/tmp", *binds,
            "--bind", str(work), JAIL_WORK,
            "--bind", str(home), JAIL_HOME,
            "--chdir", JAIL_WORK,
            "--clearenv",
            "--setenv", "PATH", f"{JAIL_OPENCODE_BIN}:/usr/bin:/bin",
            "--setenv", "HOME", JAIL_HOME,
            "--setenv", "TMPDIR", "/tmp",
            "--setenv", "LANG", "C.UTF-8",
            "--setenv", "NO_COLOR", "1",
            "--", "opencode", "--version",
        ]
        try:
            probe = subprocess.run(argv, capture_output=True, text=True,
                                   timeout=120)
        except (subprocess.TimeoutExpired, OSError) as exc:
            return f"OpenCode probe not runnable inside the jail: {exc}"

    if probe.returncode == 0 and probe.stdout.strip():
        return None
    detail = (probe.stdout + probe.stderr).strip().replace("\n", " ")[:200]
    return f"OpenCode cannot run inside the jail: {detail}"


def jail_env(model_config_content: str, task_id: str,
             extra: dict[str, str] | None = None) -> dict[str, str]:
    """The COMPLETE non-secret environment the agent process sees."""
    env = {
        "PATH": f"{JAIL_OPENCODE_BIN}:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": JAIL_HOME,
        "TMPDIR": "/tmp",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "NO_COLOR": "1",
        "TERM": "dumb",
        "XDG_CONFIG_HOME": f"{JAIL_HOME}/.config",
        "XDG_DATA_HOME": f"{JAIL_HOME}/.local/share",
        "XDG_CACHE_HOME": f"{JAIL_HOME}/.cache",
        "XDG_STATE_HOME": f"{JAIL_HOME}/.local/state",
        "OPENCODE_CONFIG_CONTENT": model_config_content,
        "TASK_ID": task_id,
    }
    if extra:
        env.update(extra)
    return env
