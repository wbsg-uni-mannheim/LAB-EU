#!/usr/bin/env bash
# Vendor the OpenCode CLI for the bwrap sandbox profile.
#
# The bwrap jail contains no repository, no $HOME and no npm — the CLI has to
# exist as a self-contained tree that can be bind-mounted read-only. The npm
# package ships a platform binary, so the installed tree needs neither node nor
# network at run time.
#
# Pin the same version the Docker profile builds (docker/opencode-harness.Dockerfile)
# so both enforcement profiles run identical agent code.
set -euo pipefail

VERSION="${OPENCODE_VERSION:-1.17.8}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${OPENCODE_VENDOR_DIR:-$REPO_ROOT/vendor/opencode}"

mkdir -p "$TARGET"
npm install --no-fund --no-audit --prefix "$TARGET" "opencode-ai@${VERSION}"

BIN="$TARGET/node_modules/.bin/opencode"
if [[ ! -x "$BIN" ]]; then
  echo "OpenCode binary missing after install: $BIN" >&2
  exit 1
fi

echo "Vendored OpenCode $("$BIN" --version) at $BIN"
