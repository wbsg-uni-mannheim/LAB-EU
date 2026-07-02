# Scripts

## Generate a rubric from a human solution

```bash
env/bin/pip install -r requirements.txt

env/bin/python scripts/generate_rubric.py \
  tasks/de/verwaltungsrecht/verpflichtungsklage/fall-05-verpflichtungsklage-auf-polizeiliches-einschreiten-wegen-schmaehkritik \
  --model gpt-5.5 \
  --write-final
```

The script runs this pipeline:

1. atomize the human solution into legally material answer atoms;
2. generate three intentionally over-complete candidate pools from different
   generator roles (doctrine, fact grounding, adversary), in parallel;
3. prune the merged pool to a Boolean rubric with a model-selected number of
   atomic criteria;
4. calibrate: judge the gold solution against every criterion with
   `--calibration-votes` votes (default 3). Criteria the gold solution passes
   unanimously are kept. The rest are sent to a refine step that rewrites,
   splits, or drops them, and the refined criteria are re-judged. After
   `--max-calibration-rounds` (default 2), still-failing criteria are dropped
   and majority-pass-but-flaky criteria are kept with a review flag.

5. tag: a final non-scoring pass adds `analysis_tags` to every criterion -
   `function` (Gutachtenstil-step vocabulary: structure, legal_basis,
   rule_statement, application, argumentation, conclusion, form_citation) and
   `station_path` (the case's own Prüfungsaufbau station, e.g.
   ["Zulässigkeit", "Klagebefugnis"]). Disable with `--skip-tagging`.

Only calibrated criteria reach the final rubric, each carrying a
`calibration` field (`status`, `agreement`, `round`). The full audit trail -
all candidate pools, prune decisions, per-round votes, refinements, and drops -
is written to `evals/rubric.generated.json`. With `--write-final`, the
calibrated rubric is also written to `evals/rubric.json` with
`review_status: generated_calibrated_needs_human_review`.

Useful flags: `--reasoning-effort` (generator, default `high`),
`--judge-model` / `--judge-reasoning-effort` (calibration judge, default:
generator model at `medium`), `--calibration-votes`, `--max-calibration-rounds`,
`--skip-calibration`, `--parallel` (judge calls, default 4).

Solution and document files are truncated only above generous size limits; if a
solution is truncated anyway, the script warns loudly because the rubric would
be built from partial ground truth.

Every model call (including each calibration judge vote) is cached under
`evals/.rubric-cache/`, keyed on the exact request. If a run fails or is
repeated, completed steps are reused instead of paid for again. Changing the
model, reasoning effort, prompts, or inputs changes the key, so stale results
are never reused. Failed judge calls are not cached. Delete the directory or
pass `--no-cache` to force a fresh run. Token usage is logged per call as
`tokens[step]: ...` on stderr and recorded in `rubric.generated.json`; there
are no output-token caps.

To re-check an already-frozen rubric by hand (for example after editing
criteria), score the gold solution against it:

```bash
env/bin/python -m evaluation.run <task-dir> <task-dir>/evals/loesung.md --votes 3
```

Every criterion should pass. Ideally also score one deliberately weak answer;
criteria that still pass on it are too lax.

The active prompt templates are in `prompts/`, so legal reviewers can inspect
or edit the wording without touching the Python scripts.

Use `--dry-run` to check local file discovery without calling the API.

## Evaluate an answer with a rubric

```bash
env/bin/python -m evaluation.run \
  tasks/de/verwaltungsrecht/verpflichtungsklage/fall-05-verpflichtungsklage-auf-polizeiliches-einschreiten-wegen-schmaehkritik \
  path/to/fallloesung-sut.md \
  --judge-model gpt-5.5
```

If the submission is a file, every criterion sees that file. If the submission
is a directory, criteria with `deliverables` only see the matching files in that
directory. Files listed in a criterion's `sources` are injected into the judge
prompt as read-only context. The judge returns verbatim evidence quotes,
reasoning, and then the verdict; failed judge calls are retried once and then
recorded as `error` verdicts instead of aborting the run. The score file is
written as `scores.json` next to the submission.

`--votes N` (default 1) judges every criterion N times and takes the majority;
ties fail. Use `--votes 3` for headline runs. The score file then also reports
per-criterion `vote_counts` and `judge_agreement` plus `mean_judge_agreement`
and `n_unanimous` overall - criteria with low agreement are rubric or judge
problems and should be reviewed.

If the rubric carries `analysis_tags`, the score file and console output also
report `breakdown_by_station` (Zulässigkeit, Begründetheit, ...) and
`breakdown_by_function` (legal_basis, application, argumentation, ...) - pass
rates in categories lawyers recognize, instead of one flat score.

`--adaptive` casts one vote first and escalates to the full `--votes` count
only when that vote is not a pass. On an answer passing ~70% of criteria this
cuts judge calls roughly in half. Trade-off: a single false pass ends the
check early, so prefer full voting where false passes matter most (e.g.
calibration). `--output <path>` writes the scores JSON somewhere other than
`scores.json` next to the submission - useful for judge-model comparisons.

## Run OpenCode as a solver harness

Validate the smoke taskset without model calls:

```bash
env/bin/python scripts/run_opencode_taskset.py \
  --taskset tasksets/opencode-smoke.jsonl \
  --dry-run
```

Build the Docker sandbox image:

```bash
docker build -f docker/opencode-harness.Dockerfile -t lab-eu-opencode-harness:latest .
```

Run OpenCode through OpenRouter DeepSeek V4 Pro with medium reasoning:

```bash
env/bin/python scripts/run_opencode_taskset.py \
  --taskset tasksets/opencode-smoke.jsonl \
  --sandbox docker \
  --model openrouter/deepseek/deepseek-v4-pro \
  --variant medium
```

The runner sanitizes task inputs before solving: OpenCode only sees `task.json`
and `documents/`, not `evals/`, rubrics, or gold solutions. Results are written
under `runs/<run-name>/<run-id>/`.

Each task result includes audit artifacts:

- `stdout.jsonl`: raw OpenCode JSON event stream.
- `trace.jsonl`: normalized tool/file trace extracted from OpenCode events.
- `trace.md`: human-readable trace summary.
- `reasoning_trace.summary.json`: summary and size metadata for provider-emitted
  reasoning details, without expanding full private reasoning text.
- `workspace.before.json` and `workspace.after.json`: file snapshots.
- `fs_changes.json`: created, modified, and deleted files with hashes.

Judge a completed run:

```bash
env/bin/python scripts/judge_run.py \
  runs/opencode-openrouter-deepseek-v4-pro-medium/<run-id> \
  --judge-model gpt-5.5
```

`judge_run.py` defaults to `--votes 3` (majority per criterion) because it is
the headline-run wrapper; pass `--votes 1` for cheap smoke checks.

## Run the single-LLM-call baseline

One plain model call per task - no agent loop, no tools. This is the reference
point for the question whether agent scaffolding helps at all. The run layout
matches the OpenCode harness, so `judge_run.py` works on baseline runs
unchanged.

```bash
# OpenAI model
env/bin/python scripts/run_baseline_taskset.py \
  --taskset tasksets/opencode-smoke.jsonl \
  --run-name baseline-gpt-5.5 \
  --model gpt-5.5

# OpenRouter model (same model family as the OpenCode runs)
env/bin/python scripts/run_baseline_taskset.py \
  --taskset tasksets/opencode-smoke.jsonl \
  --run-name baseline-deepseek-v4-pro \
  --model deepseek/deepseek-v4-pro \
  --api-base https://openrouter.ai/api/v1 \
  --api-key-env OPENROUTER_API_KEY
```

The model sees the task instructions plus all documents inlined into one
prompt (evals/ is never included) and its entire response is saved as the
deliverable under `submission/`. Baseline tasks must have exactly one
deliverable. `--reasoning-effort` is optional and only for endpoints that
accept the chat-completions `reasoning_effort` parameter.
