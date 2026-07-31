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

# Prepare the plugin tree the jail binds read-only.
#
# Inside the bwrap jail OpenCode cannot resolve its plugin dependencies and
# reinstalls them into $HOME/.config/opencode on EVERY task: 54 MB and 3,442
# files each, which came to 21 GB across one 45-case study. Preparing the tree
# once and binding it read-only cuts the per-task jail state from ~3,500 files
# to ~35 and removes the install step from every run.
#
# The install is triggered by a real run, not by --version, so this needs one
# throwaway model call. Skipped when the tree is already there.
PLUGINS="${OPENCODE_PLUGIN_HOME:-$REPO_ROOT/vendor/opencode-home}"
if [[ -d "$PLUGINS/opencode/node_modules" ]]; then
  echo "Plugin tree already prepared at $PLUGINS/opencode/node_modules"
  exit 0
fi
if [[ -z "${OPENAI_API_KEY:-}${OPENROUTER_API_KEY:-}" ]]; then
  echo "No provider key in the environment - skipping plugin preparation." >&2
  echo "Run again with a key set, or the jail falls back to per-task installs." >&2
  exit 0
fi

SEED="$(mktemp -d)"
trap 'rm -rf "$SEED"' EXIT
mkdir -p "$SEED/home" "$SEED/work"
MODEL="${OPENCODE_SEED_MODEL:-openai/gpt-5.6-luna}"
echo "Preparing the plugin tree with one throwaway call to $MODEL ..."
bwrap --die-with-parent --unshare-pid --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind /usr /usr --ro-bind /bin /bin --ro-bind /sbin /sbin \
  --ro-bind /lib /lib $([[ -d /lib64 ]] && echo "--ro-bind /lib64 /lib64") \
  --ro-bind /etc /etc --ro-bind "$TARGET" /opt/opencode \
  --bind "$SEED/work" /work --bind "$SEED/home" /home/agent --chdir /work \
  --setenv HOME /home/agent --setenv PATH /opt/opencode/node_modules/.bin:/usr/bin:/bin \
  --setenv NO_COLOR 1 --setenv TMPDIR /tmp \
  -- opencode run --dir /work --model "$MODEL" --format json "Reply OK." >/dev/null 2>&1 || true

if [[ -d "$SEED/home/.config/opencode/node_modules" ]]; then
  mkdir -p "$PLUGINS"
  cp -a "$SEED/home/.config/opencode" "$PLUGINS/opencode"
  echo "Plugin tree prepared: $(find "$PLUGINS/opencode" -type f | wc -l) files, $(du -sh "$PLUGINS/opencode" | cut -f1)"
else
  echo "OpenCode did not install plugins during the seed run; the jail will" >&2
  echo "fall back to per-task installs. Not fatal, just wasteful." >&2
fi
