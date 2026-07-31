#!/bin/bash
#SBATCH --job-name=lab-eu-judge
#SBATCH --partition=cpu
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=12:00:00
#SBATCH --output=runs/_slurm/%x-%j.out
#SBATCH --error=runs/_slurm/%x-%j.out
#
# Judging for one LAB-EU study arm, or the shared Batch-API prewarm.
#
#   sbatch scripts/judge_study.sbatch batch  --study <study.json> <run-dir>...
#   sbatch scripts/judge_study.sbatch scores --study <study.json> <run-dir>
#
# 'batch' submits the committee's OpenAI members (luna, terra) to the Batch API
# at half price and writes their votes into each run's vote-cache. 'scores' then
# runs the normal committee judging, which finds those votes cached and only
# calls the non-batchable judge (gemini via OpenRouter) live.
#
# Run one 'scores' job per arm and model so they judge in parallel, with
# --dependency=afterok:<batch-job> so they start on a warm cache. Both phases
# are resumable: the vote cache survives a job that runs out of wall time, and
# 'batch' takes --resume runs/judge-batches/<id> after an interrupted poll.
#
# Judging needs BOTH keys: luna and terra on OpenAI, gemini via OpenRouter.

set -euo pipefail

REPO=/work/aasteine/LAB-EU
cd "$REPO"
mkdir -p runs/_slurm

PHASE="${1:-}"
shift || true
case "$PHASE" in
  batch)  SCRIPT=scripts/judge_committee_batch.py ;;
  scores) SCRIPT=scripts/judge_run.py ;;
  *) echo "Usage: sbatch scripts/judge_study.sbatch {batch|scores} [args...]" >&2
     exit 2 ;;
esac

echo "=== phase=$PHASE node=$(hostname -s) job=${SLURM_JOB_ID:-none} started=$(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "=== args: $* ==="

exec "$REPO/env/bin/python" "$SCRIPT" "$@"
