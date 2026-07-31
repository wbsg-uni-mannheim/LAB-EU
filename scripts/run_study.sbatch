#!/bin/bash
#SBATCH --job-name=lab-eu
#SBATCH --partition=cpu
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=24:00:00
#SBATCH --output=runs/_slurm/%x-%j.out
#SBATCH --error=runs/_slurm/%x-%j.out
#
# One LAB-EU study arm on a compute node.
#
# Usage:
#   sbatch scripts/run_study.sbatch agent    --taskset studies/de-core-45/taskset.jsonl ...
#   sbatch scripts/run_study.sbatch baseline --taskset studies/de-core-45/taskset.jsonl ...
#
# The first argument picks the runner; everything after it is forwarded
# verbatim, so the full CLI (--model, --variant, --parallel, --max-attempts, …)
# stays available without editing this file.
#
# The agent arm gets --sandbox bwrap unless the caller passes their own
# --sandbox: compute nodes have no Docker daemon, and bwrap is the cluster
# enforcement profile (scripts/sandbox_spec.py). The runner's own preflight
# then proves, on THIS node, that a namespace can be built and that the
# vendored OpenCode actually executes inside it — a login node that can do
# both is no guarantee for a compute node.
#
# Resources: the solver spends nearly all its wall time waiting on the
# provider, so 4 CPUs and 16G are generous (OpenCode peaked at ~0.5G RSS).
# Wall time is the real constraint — 45 cases at ~6-10 min each, plus retry
# backoff. Neither runner resumes a partial run, so give the job more time
# than you expect to need.

set -euo pipefail

REPO=/work/aasteine/LAB-EU
cd "$REPO"
mkdir -p runs/_slurm

ARM="${1:-}"
shift || true
case "$ARM" in
  agent)    RUNNER=scripts/run_opencode_taskset.py ;;
  baseline) RUNNER=scripts/run_baseline_taskset.py ;;
  *) echo "Usage: sbatch scripts/run_study.sbatch {agent|baseline} [runner args...]" >&2
     exit 2 ;;
esac

echo "=== arm=$ARM node=$(hostname -s) job=${SLURM_JOB_ID:-none} started=$(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "=== args: $* ==="

args=("$@")
if [[ "$ARM" == "agent" ]]; then
  case " $* " in
    *" --sandbox "*) ;;
    *) args+=(--sandbox bwrap) ;;
  esac
fi

exec "$REPO/env/bin/python" "$RUNNER" "${args[@]}"
