#!/usr/bin/env bash
set -euo pipefail

: "${OPENCODE_MODEL:?OPENCODE_MODEL is required}"

PROMPT_FILE="${PROMPT_FILE:-/out/prompt.md}"
TASK_TITLE="${TASK_ID:-task}"

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Missing prompt file: $PROMPT_FILE" >&2
  exit 2
fi

variant_args=()
if [[ -n "${OPENCODE_VARIANT:-}" ]]; then
  variant_args=(--variant "$OPENCODE_VARIANT")
fi

agent_args=()
if [[ -n "${OPENCODE_AGENT:-}" ]]; then
  agent_args=(--agent "$OPENCODE_AGENT")
fi

cd /work

exec opencode run \
  --dir /work \
  --model "$OPENCODE_MODEL" \
  "${variant_args[@]}" \
  "${agent_args[@]}" \
  --format json \
  --title "LAB-EU ${TASK_TITLE}" \
  --dangerously-skip-permissions \
  "$(cat "$PROMPT_FILE")"
