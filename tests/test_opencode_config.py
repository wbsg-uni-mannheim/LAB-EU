"""Pure tests for OpenCode provider configuration."""

from __future__ import annotations

import pathlib
import sys
from types import SimpleNamespace

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_opencode_taskset  # noqa: E402

from run_opencode_taskset import build_opencode_config  # noqa: E402


def test_unlisted_study_model_is_registered_explicitly():
    config = build_opencode_config("openai/gpt-5.6-sol")

    assert config["provider"]["openai"]["models"] == {"gpt-5.6-sol": {}}
    assert config["permission"]["websearch"] == "deny"


def test_registered_model_does_not_add_provider_override():
    config = build_opencode_config("openai/gpt-5.5")

    assert "provider" not in config


def test_model_limit_is_preserved_in_provider_override():
    config = build_opencode_config("openrouter/z-ai/glm-5.2")

    assert config["provider"]["openrouter"]["models"]["z-ai/glm-5.2"] == {
        "limit": {"context": 1_050_000, "output": 128_000}
    }


def test_docker_preflight_loads_repo_environment(monkeypatch):
    calls = []
    monkeypatch.setattr(
        run_opencode_taskset,
        "load_dotenv",
        lambda path, override: calls.append((path, override)),
    )

    run_opencode_taskset.preflight(SimpleNamespace(sandbox="docker"))

    assert calls == [(REPO_ROOT / ".env", False)]
