# German First State Exam Core Study (45 cases)

This study fixes the first broad LAB-EU evaluation set at 45 German-law cases:
15 public-law, 15 criminal-law, and 15 civil-law tasks. Every task has a
calibrated canonical rubric at `evals/rubric.json`.

The task and rubric set is frozen as of 2026-07-31. Later corrections require
an explicit new study revision instead of silently changing this snapshot.

The study compares two original conditions using the same underlying model:

1. `baseline`: one model call, no tools;
2. `agent`: OpenCode in an isolated per-task workspace — Docker on
   workstations, a bwrap jail on cluster nodes (compute nodes have no Docker
   daemon). Both enforce the same boundary; `manifest.json` records which
   profile ran.

An additional Codex condition is available for app-account experiments. It
uses the non-interactive Codex CLI with the same ChatGPT login as the Codex
app. Every case gets a fresh OS temporary directory outside this repository,
an ephemeral non-persisted session, disabled memories, live web search, and
the user's configured MCP/plugin tools. It therefore does not appear as a
project or resumable task in the app. With `--tool-access full` (the default),
local tools also run without a sandbox or approval prompt; use this only on a
trusted machine and trusted task inputs.

The solver receives an anonymized `task.json` plus the unchanged `documents/`.
The anonymized file retains the substantive instructions, work type, and
deliverable, but omits the original task ID, source, tags, authors,
fundstelle, license, and other provenance metadata. Gold solutions and rubrics
remain outside the solver workspace. Runs are written below `runs/` and are
not version-controlled.

The title is replaced by the exam format alone -- `Fortgeschrittenenhausarbeit`,
`Examensklausur`, `Klausur der Zweiten Juristischen Staatsprüfung` and so on --
via `scripts/task_identity.py`, which only ever emits labels from a fixed
whitelist, so case names, Fundstellen and exam years cannot pass through. Runs
before 2026-08-21 replaced every title with the generic placeholder
`Juristische Fallbearbeitung`, and only the Codex arm was anonymized at all --
the baseline and agent arms saw the full original title, a directly searchable
string. Both are fixed, on methodological grounds: the arms have to receive the
same information, and the rubrics grade against the depth conventions of the
exam format.

How much the placeholder cost is not established. Hausarbeiten score below
Klausuren in every arm (-0.087 on average for the six arms that saw the title,
-0.143 for the two anonymized ones). The direction fits the format-signal
explanation, but with five Hausarbeiten and two arms against six the difference
carries no weight. Treat it as a design defect that was fixed, not as a measured
effect.

## Reproducibility boundary

- Taskset: `studies/de-core-45/taskset.jsonl`
- Cases: 45
- Rubric commit: `848d532f6f53fc5e48420a97603ba17c7ed82349`
- Solver prompts: `prompts/harness/solve_task_baseline.txt` (baseline),
  `prompts/harness/solve_task.txt` (agent),
  `prompts/harness/solve_task_codex_web.txt` (Codex web),
  `prompts/harness/study_system_prompt.txt` (manual workbench condition only)
- Final judge committee: `configs/judge-committee-professor-pilot.json`
- Content and legal style remain separate Boolean outcomes.

Use the same model and comparable reasoning configuration in both conditions.
Run tasks serially by default (`--parallel 1`) to reduce provider-side
contention and make failures easier to resume.

## Validate the study without API calls

```bash
./env/bin/python scripts/run_baseline_taskset.py \
  --taskset studies/de-core-45/taskset.jsonl \
  --run-name baseline-study-smoke \
  --model gpt-5.5 \
  --parallel 1 \
  --dry-run

./env/bin/python scripts/run_opencode_taskset.py \
  --taskset studies/de-core-45/taskset.jsonl \
  --run-name agent-study-smoke \
  --model openrouter/deepseek/deepseek-v4-pro \
  --variant medium \
  --sandbox docker \
  --parallel 1 \
  --dry-run
```

## Run one baseline arm

```bash
./env/bin/python scripts/run_baseline_taskset.py \
  --taskset studies/de-core-45/taskset.jsonl \
  --run-name baseline-<model-name> \
  --model <provider/model> \
  --api-base <openai-compatible-endpoint> \
  --parallel 1
```

## Run the matching agent arm

```bash
./env/bin/python scripts/run_opencode_taskset.py \
  --taskset studies/de-core-45/taskset.jsonl \
  --run-name agent-<model-name> \
  --model <opencode-provider/model> \
  --variant <variant> \
  --sandbox bwrap \
  --parallel 1
```

## Run the 45-case Codex app-account arm

First validate the installed CLI, ChatGPT login, all 45 inputs, and the exact
command shape without starting a model run:

```bash
./env/bin/python scripts/run_codex_taskset.py \
  --taskset studies/de-core-45/taskset.jsonl \
  --run-name codex-web-45 \
  --model gpt-5.6-sol \
  --reasoning-effort medium \
  --parallel 1 \
  --dry-run
```

Then start the serial run:

```bash
./env/bin/python scripts/run_codex_taskset.py \
  --taskset studies/de-core-45/taskset.jsonl \
  --run-name codex-web-45 \
  --model gpt-5.6-sol \
  --reasoning-effort medium \
  --parallel 1 \
  --tool-access full
```

For a one-case end-to-end smoke run, add `--limit 1`.

The frozen Codex condition uses `gpt-5.6-sol` at reasoning level `medium`,
pinned by the two CLI options above. Do not omit them for the 45-case study:
the Codex JSONL event stream does not independently report the resolved model
or reasoning level. `zjs-online.com` is always excluded from web research:
the solver must add a negative site filter to every search, and the harness
marks a case as contaminated and unsuccessful if the domain is nevertheless
targeted, opened, fetched, cited, or used. Additional exclusions can be added
with repeated `--blocked-domain <domain>` options. Each case writes the final response,
raw JSONL event stream, stderr, metadata, and judge-compatible submission
under `runs/codex-web-45/<run-id>/tasks/`. Every task also receives
`sources.md` and `sources.json`; `source-summary.md` and
`source-summary.json` aggregate URLs and domains over the full run.

The source audit also flags searches resembling the hidden original title or
fundstelle, solution-seeking terms, and copied task phrases. These flags are
informational review signals only: researching the facts is permitted and a
flag neither contaminates nor rejects a case. Research is not restricted to a
domain allowlist.

Add `--judge` to score the completed submissions with the standard LAB-EU
judge. For a safer shell boundary, replace
`--tool-access full` with `--tool-access workspace`; live web search and
configured MCP/plugin tools remain available.

Regenerate the source reports for an existing Codex run with:

```bash
./env/bin/python scripts/codex_source_audit.py runs/<run-name>/<run-id>
```

## Run an arm as a Slurm job

On the cluster, submit each arm instead of running it on the login node. The
first argument selects the runner; everything after it is forwarded verbatim:

```bash
sbatch --job-name=lab-eu-agent-45 --time=24:00:00 scripts/run_study.sbatch agent \
  --taskset studies/de-core-45/taskset.jsonl \
  --run-name agent-<model-name> \
  --model <opencode-provider/model> --variant <variant> --parallel 1
```

The agent arm defaults to `--sandbox bwrap` there. Neither runner resumes a
partial run, so allow more wall time than you expect to need. Job logs land in
`runs/_slurm/`.

Each invocation creates a new immutable run directory. Do not expose `evals/`
to the solver and do not reuse answers between the baseline and agent arms.
