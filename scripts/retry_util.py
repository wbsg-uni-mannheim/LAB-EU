#!/usr/bin/env python3
"""Retry policy shared by the solver harnesses.

The rule that matters here is *what* may be retried. A provider that drops the
connection is an infrastructure failure: the task never got a fair attempt, and
repeating it costs nothing but tokens. A model that runs to completion and
simply does not write its deliverable is a solver failure — repeating that is
best-of-N sampling, and silently reporting the best of ten attempts as one
benchmark score would inflate every number in the run. :func:`classify_failure`
draws that line, and only ``TRANSIENT`` is retried.

Fatal failures (a rejected key, a malformed request, an unknown model) are
separated out too: retrying those ten times per task just multiplies the
waiting on a run that cannot succeed.
"""

from __future__ import annotations

import random
import re
import time

# 1 initial attempt + 10 retries.
DEFAULT_MAX_ATTEMPTS = 11

BASE_DELAY_SECONDS = 5.0
MAX_DELAY_SECONDS = 300.0

# How often an UNNAMED failure may repeat identically before we call it
# deterministic and stop.
REPEAT_LIMIT = 3

UNNAMED_FAILURE_PREFIX = "solver exited with code"

OK = "ok"
TRANSIENT = "transient"
FATAL = "fatal"
SOLVER = "solver"
TIMEOUT = "timeout"

# Upstream problems that say nothing about the task: worth repeating.
TRANSIENT_PATTERNS = (
    r"\b(429|500|502|503|504)\b",
    r"provider_unavailable",
    r"overloaded",
    r"rate.?limit",
    r"temporarily unavailable",
    r"service unavailable",
    r"internal server error",
    r"bad gateway",
    r"upstream",
    r"timed? ?out",
    r"econnreset|econnrefused|etimedout|epipe",
    r"connection (reset|closed|error|aborted)",
    r"socket hang up",
    r"error injected into sse stream",
    r"stream (closed|interrupted|ended) unexpectedly",
)

# Deterministic refusals and configuration problems: repeating them cannot help.
FATAL_PATTERNS = (
    # A provider content filter is a property of (model, prompt): it fires again
    # on every identical attempt. Observed on the de-core-45 agent arm, where
    # DeepSeek blocked one constitutional-law case 11 times in a row while the
    # baseline arm solved the same case (run 20260730T214602Z).
    r"content.?filter",
    r"content.?policy",
    r"response was blocked",
    r"\b(400|401|403|404)\b",
    r"invalid.?api.?key",
    r"no auth credentials",
    r"user not found",
    r"missing authentication",
    r"unauthorized",
    r"forbidden",
    r"model .*not found",
    r"unknown model",
    r"insufficient (credits|funds|quota)",
    r"quota exceeded",
)


def _matches(text: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        found = re.search(pattern, text, flags=re.IGNORECASE)
        if found:
            return found.group(0)
    return None


def classify_failure(
    exit_code: int | None,
    timed_out: bool,
    missing_deliverables: bool,
    error_text: str = "",
) -> tuple[str, str]:
    """Return ``(outcome, reason)`` for one solver attempt.

    ``error_text`` is whatever the harness could recover about the failure —
    for OpenCode the message of its error events, for the baseline the
    exception string.
    """
    if timed_out:
        return TIMEOUT, "solver exceeded the task timeout"

    # An explicit provider error decides the class regardless of exit code:
    # a CLI can drop a 502 into its event stream and still exit 0.
    fatal_hit = _matches(error_text, FATAL_PATTERNS)
    if fatal_hit:
        return FATAL, f"provider rejected the request ({fatal_hit})"
    transient_hit = _matches(error_text, TRANSIENT_PATTERNS)
    if transient_hit:
        return TRANSIENT, f"upstream failure ({transient_hit})"

    if exit_code not in (0, None):
        # Nothing in the output named a cause. Retry, but see `stalled()`: an
        # unnamed failure that repeats identically is deterministic, not an
        # outage, and must not consume every remaining attempt.
        return TRANSIENT, f"{UNNAMED_FAILURE_PREFIX} {exit_code}"
    if missing_deliverables:
        # Ran to completion, wrote nothing we asked for. Not a retry: that
        # would turn the benchmark into best-of-N.
        return SOLVER, "solver finished without producing the deliverable"
    return OK, ""


def stalled(reasons: list[str], limit: int = REPEAT_LIMIT) -> bool:
    """True when the last ``limit`` failures were identical AND unnamed.

    A named upstream failure may legitimately repeat — that is what an outage
    looks like, and cutting those retries short defeats the point. But a
    non-zero exit the classifier could not explain, reproducing byte-identically,
    is a deterministic failure: a content filter, a crash, a prompt the model
    always refuses. Retrying it to exhaustion burns the wall clock and buys
    nothing.
    """
    recent = reasons[-limit:]
    return (len(recent) == limit
            and len(set(recent)) == 1
            and recent[0].startswith(UNNAMED_FAILURE_PREFIX))


def should_retry(outcome: str, retry_on_timeout: bool = False) -> bool:
    if outcome == TIMEOUT:
        return retry_on_timeout
    return outcome == TRANSIENT


def backoff_delay(attempt: int,
                  base: float = BASE_DELAY_SECONDS,
                  cap: float = MAX_DELAY_SECONDS,
                  rng: random.Random | None = None) -> float:
    """Equal-jitter exponential backoff for the ``attempt``-th failure.

    Half the window is fixed so a provider outage is actually waited out, half
    is random so parallel tasks do not resynchronise on every retry.
    """
    window = min(cap, base * (2 ** max(0, attempt - 1)))
    half = window / 2
    return half + (rng or random).uniform(0, half)


def sleep_before_retry(attempt: int, **kwargs) -> float:
    delay = backoff_delay(attempt, **kwargs)
    time.sleep(delay)
    return delay
