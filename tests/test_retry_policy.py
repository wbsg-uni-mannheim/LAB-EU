"""Retry policy: what gets repeated, what must not, and how long we wait."""

from __future__ import annotations

import json
import pathlib
import random
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import retry_util  # noqa: E402
from retry_util import FATAL, OK, SOLVER, TIMEOUT, TRANSIENT, classify_failure  # noqa: E402


def outcome(**kwargs) -> str:
    base = dict(exit_code=0, timed_out=False, missing_deliverables=False, error_text="")
    base.update(kwargs)
    return classify_failure(**base)[0]


def test_clean_run_is_not_retried():
    assert outcome() == OK


def test_the_observed_openrouter_failure_is_transient():
    # verbatim from runs/bwrap-pilot-.../20260730T150502Z: a 502 injected into
    # the SSE stream 13 minutes into the generation
    error = json.dumps({
        "code": 502,
        "message": "JSON error injected into SSE stream",
        "metadata": {"error_type": "provider_unavailable"},
    })
    assert outcome(exit_code=1, missing_deliverables=True, error_text=error) == TRANSIENT


@pytest.mark.parametrize("error_text", [
    "429 Too Many Requests",
    "503 Service Unavailable",
    "upstream connect error",
    "socket hang up",
    "ECONNRESET",
    "The model is currently overloaded",
])
def test_upstream_failures_are_transient(error_text):
    assert outcome(exit_code=1, missing_deliverables=True, error_text=error_text) == TRANSIENT


@pytest.mark.parametrize("error_text", [
    "401 Unauthorized",
    "No auth credentials found",
    "User not found.",
    "invalid api key",
    "Insufficient credits",
])
def test_configuration_failures_are_fatal(error_text):
    # retrying these ten times per task only delays an unavoidable failure
    assert outcome(exit_code=1, missing_deliverables=True, error_text=error_text) == FATAL


def test_a_finished_solver_without_deliverable_is_never_retried():
    """The line that keeps the benchmark honest: repeating a completed-but-empty
    attempt is best-of-N sampling, not fault tolerance."""
    assert outcome(exit_code=0, missing_deliverables=True) == SOLVER
    assert retry_util.should_retry(SOLVER) is False


def test_provider_error_outranks_a_zero_exit_code():
    # a CLI can report the failure in its event stream and still exit 0
    assert outcome(exit_code=0, missing_deliverables=True,
                   error_text="502 Bad Gateway") == TRANSIENT


def test_timeouts_are_opt_in():
    assert outcome(timed_out=True, missing_deliverables=True) == TIMEOUT
    assert retry_util.should_retry(TIMEOUT) is False
    assert retry_util.should_retry(TIMEOUT, retry_on_timeout=True) is True


def test_backoff_grows_and_is_capped():
    rng = random.Random(0)
    delays = [retry_util.backoff_delay(attempt, rng=rng) for attempt in range(1, 12)]
    # half of each window is fixed, so successive minima strictly increase
    assert delays[0] >= retry_util.BASE_DELAY_SECONDS / 2
    assert delays[3] > delays[0]
    assert all(delay <= retry_util.MAX_DELAY_SECONDS for delay in delays)
    assert delays[-1] >= retry_util.MAX_DELAY_SECONDS / 2


def test_backoff_is_jittered():
    rng = random.Random(1)
    samples = {retry_util.backoff_delay(5, rng=rng) for _ in range(20)}
    # parallel tasks must not resynchronise on a shared fixed delay
    assert len(samples) > 1


def test_default_is_one_attempt_plus_ten_retries():
    assert retry_util.DEFAULT_MAX_ATTEMPTS == 11
