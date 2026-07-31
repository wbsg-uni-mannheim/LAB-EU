# Scripts

## Generate a rubric from a human solution

```bash
env/bin/pip install -r requirements.txt

env/bin/python scripts/generate_rubric.py \
  tasks/de/oeffentliches-recht/verwaltungsrecht/verpflichtungsklage/fall-05-verpflichtungsklage-auf-polizeiliches-einschreiten-wegen-schmaehkritik \
  --model gpt-5.6-sol \
  --calibration-committee configs/judge-committee-rubric-calibration.json \
  --write-final
```

The script runs this pipeline:

1. atomize the human solution into legally material answer atoms;
2. generate three intentionally over-complete candidate pools from different
   generator roles (doctrine, fact grounding, adversary), in parallel;
3. prune the merged pool to a Boolean rubric with a model-selected number of
   atomic criteria;
4. calibrate: judge the gold solution against every criterion. The recommended
   `--calibration-committee` configuration casts one vote each with Luna, Terra,
   and Gemini instead of asking the generator model to judge its own rubric
   repeatedly. Without a committee, `--calibration-votes` repeated votes from
   `--judge-model` remain available. Criteria the gold solution passes
   unanimously are kept. The rest are sent to a refine step that rewrites,
   splits, or drops them, and the refined criteria are re-judged. After
   `--max-calibration-rounds` (default 2), still-failing criteria are dropped
   and majority-pass-but-flaky criteria are kept with a review flag.

5. outline: one call extracts the solution's own Gliederung as a tree
   (ids like "A", "A.I", "A.I.1" following the solution's markers, plus the
   reserved node "Ü"/Übergreifend for cross-cutting criteria). The tree is
   frozen into `rubric.json` as `outline`.

6. tag: a final non-scoring pass classifies every criterion - `function`
   (Gutachtenstil-step vocabulary: structure, legal_basis, rule_statement,
   application, argumentation, conclusion, form_citation), `outline_id` (the
   deepest outline node the criterion belongs to; `station_path` is derived
   from the tree so all downstream breakdowns keep working), and `criticality`
   1-3 (3 = realistic divergence points that decide the case, target ~10-15%
   of criteria; 2 = expected in a solid solution, at most 60%; 1 = the
   remaining detail/form/bonus criteria). A logically necessary step is not
   automatically tier 3. Criticality is currently
   non-scoring; it feeds the reporting breakdowns and the review documents.
   Disable outline + tagging with `--skip-tagging`.

Only calibrated criteria reach the final rubric, each carrying a
`calibration` field (`status`, `agreement`, `round`). The full audit trail -
all candidate pools, prune decisions, per-round votes, refinements, and drops -
is written to `evals/rubric.generated.json`. With `--write-final`, the
calibrated rubric is also written to `evals/rubric.json` with
`review_status: generated_calibrated_needs_human_review`.
The generator and the lawyer-facing review file emit a freeze warning when the
3/2/1-star target is missed. This remains a reviewable warning rather than a
hard error so small rubrics and documented legal exceptions stay possible.

To add or refresh outline/tags/criticality on an ALREADY frozen rubric, never
re-run the full pipeline - prompt changes since the original generation can
silently invalidate the step cache and trigger a full, expensive regeneration
that REPLACES the frozen criteria. Use the retag mode instead, which loads
`evals/rubric.json`, runs only `extract_outline` + `tag_criteria` (two small
calls), and writes the updated tags back with the criteria untouched:

```bash
env/bin/python scripts/generate_rubric.py <task-dir> --model gpt-5.6-sol --retag-only
```

Useful flags: `--reasoning-effort` (generator, default `high`),
`--judge-model` / `--judge-reasoning-effort` (calibration judge, default:
generator model at `medium`), `--calibration-committee` (one vote per configured
model, recommended), `--calibration-votes`, `--max-calibration-rounds`,
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

## Batch-generate rubrics for many tasks (cheaper)

### Batch the Sol draft stages

For a larger taskset, atomization, the three candidate roles, and pruning can
also run through the Batch API. These steps depend on one another, so the
orchestrator submits three sequential batches and harvests each result into the
normal `evals/.rubric-cache/` before preparing the next phase:

```bash
env/bin/python scripts/generate_rubric_drafts_batch.py \
  --taskset tasksets/de-core-10-batch-pilot.jsonl \
  --artifact-suffix broad-v1 \
  --prepare-only

env/bin/python scripts/generate_rubric_drafts_batch.py \
  --resume runs/rubric-draft-batches/<run-id>
```

`--prepare-only` writes the next JSONL file without uploading it. After the
pruning batch, the normal generator is invoked with calibration and tagging
disabled; the orchestrator first verifies that all five expected calls per task
are cached and refuses a synchronous fallback if any entry is missing. It then
writes `evals/rubric.generated.<suffix>.json` as the draft audit artifact.

Each run directory contains `state.json`, the submitted inputs and returned
outputs, plus `cost-summary.json` and `cost-summary.md`. The cost report covers
only atomization, three candidate roles, and pruning; committee calibration,
negative calibration, outline extraction, and tagging remain separate.

### Batch the calibration votes

For more than a handful of tasks, use the batch orchestrator. It runs the
cheap draft steps synchronously, then routes the expensive part - all round-1
calibration judge votes across all tasks - through the OpenAI Batch API at 50%
of the synchronous price:

```bash
env/bin/python scripts/generate_rubrics_batch.py \
  tasks/de/oeffentliches-recht/verwaltungsrecht/anfechtungsklage/fall-02-anfechtungsklage-bei-nebenbestimmungen \
  tasks/de/oeffentliches-recht/verwaltungsrecht/anfechtungsklage/fall-03-drittanfechtungsklage-gegen-eine-baugenehmigung \
  --model gpt-5.6-sol
```

Phases: draft (sync, parallel) -> build vote requests (votes already in a
task's step cache are skipped) -> submit batch files and poll -> write results
into each task's `evals/.rubric-cache` -> finalize each task with a normal
`generate_rubric.py --write-final` run, in which every round-1 vote is a cache
hit and only refine, re-judging, and tagging run synchronously.

Batches usually finish well within the 24h window. If the script is
interrupted after submitting, re-run with `--resume runs/rubric-batches/<id>`.
Failed batch lines are simply re-judged synchronously during finalize.
`--prepare-only` writes the batch input files without uploading, for
inspection. Everything is idempotent through the step cache: re-running a
partially completed run only pays for what is missing.

Cost notes:

- The Batch API halves the price of the calibration votes, which dominate
  rubric-generation cost (~1.5-4M input tokens per task).
- The judge prompt is ordered so that the large invariant blocks (rules, task,
  gold solution or answer) form one shared prefix and the per-criterion parts
  come last; on the synchronous path OpenAI prompt caching then bills most of
  each call's input at the cached rate. The same idea applies to the three
  candidate-role calls, which share the full task payload as prefix.
- Watch `cached=` in the per-call `tokens[...]` log lines and
  `cached_input_tokens` in usage summaries to verify caching is working.

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

## Generate a lawyer-facing rubric review file

```bash
env/bin/python scripts/generate_rubric_review.py \
  tasks/de/oeffentliches-recht/verwaltungsrecht/verpflichtungsklage/fall-05-verpflichtungsklage-auf-polizeiliches-einschreiten-wegen-schmaehkritik
```

This writes `evals/rubric-review.md` with the task, case, solution, and each
rubric criterion's title, match criteria, and review notes.

## Evaluate an answer with a rubric

```bash
env/bin/python -m evaluation.run \
  tasks/de/oeffentliches-recht/verwaltungsrecht/verpflichtungsklage/fall-05-verpflichtungsklage-auf-polizeiliches-einschreiten-wegen-schmaehkritik \
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
rates in categories lawyers recognize, instead of one flat score. Rubrics with
`criticality` tiers (1-3) additionally get `breakdown_by_criticality`, so you
can see at a glance whether failures hit central points (3) or details (1),
and rubrics with an `outline` get `breakdown_by_outline` (level-2 Gliederung).
`export_review_md.py` and `generate_rubric_review.py` render criteria nested
along the Musterlösung's Gliederung when the rubric carries an outline.

### Three-model committee and separate Gutachtenstil score

For the professor-feedback pilot, use the checked-in mixed-provider committee:

```bash
env/bin/python -m evaluation.run <task-dir> <submission> \
  --judge-committee configs/judge-committee-professor-pilot.json \
  --style-evaluation \
  --vote-cache-dir <output-dir>/votes \
  --output <output-dir>/scores.json
```

The three committee members cast one independent content vote per criterion. Only a
strict majority passes. For criteria tagged `application` or `argumentation`, the same
request returns a second, independent Boolean style verdict; the full answer and task
context are therefore not transmitted twice. Models run sequentially with model-specific
parallelism, while votes within one model run concurrently. Successful votes are cached
by the exact model, prompt, criterion, and phase, so interrupted runs resume without
repeating them. Use `--separate-style-calls` only for calibration against the former
two-request design.

`scores.json` reports three distinct diagnostics:

- `content_score`: unweighted fulfilled criteria;
- `criticality_weighted_content_score`: 3/2/1-star weighted content, diagnostic only;
- `style_score`: Boolean Gutachtenstil pass rate among all criteria tagged as
  `application` or `argumentation`, regardless of whether their content verdict is pass
  or fail. Definitions, legal bases, structure, form, and pure conclusions remain content
  criteria but are excluded from the style denominator. A substantively wrong argument
  may therefore receive style `1` when its legal reasoning form is sound. Style nevertheless
  fails when the reasoning belongs to another person or examination station, has to be
  assembled from scattered statements, leaves its chosen examination path incomplete, or
  states a result without expressly connecting the decisive facts to the legal premise.
  `style_evaluation_mode` records whether a score used the recommended `combined` calls
  or the legacy `separate` calls. Shared-request token usage is counted exactly once under
  content; `judge_usage_total` remains the complete billable total.

Errored votes are einmal gezielt nachgeholt. Bleibt ein Fehler bestehen, wird das
Kriterium konservativ als `fail` mit `resolution: "unresolved"` ausgewiesen. Ein
vollständiges 2:1 löst standardmäßig einen unabhängigen zweiten Komiteelauf nur für
dieses Kriterium aus: Bleibt die Mehrheitsrichtung gleich, lautet der Status
`stable_with_dissent`; kippt sie, ist das Kriterium `unresolved`. Mit
`--no-committee-conflict-recheck` beziehungsweise `--committee-error-retries 0` lässt
sich dieses Verhalten für Diagnosen abschalten. `content_score.n_unresolved` und
`style_score.n_unresolved` verhindern, dass technische oder instabile Entscheidungen
als reguläre Passes erscheinen.

Professor review labels under `tests/fixtures/` are external evaluation data. Never pass
those files to `generate_rubric.py`. Generate rubrics only from the task, source
documents, and supplied model solution; measure expert agreement afterwards with
`scripts/compare_expert_labels.py`.

`--adaptive` casts one vote first and escalates to the full `--votes` count
only when that vote is not a pass. On an answer passing ~70% of criteria this
cuts judge calls roughly in half. Trade-off: a single false pass ends the
check early, so prefer full voting where false passes matter most (e.g.
calibration). `--output <path>` writes the scores JSON somewhere other than
`scores.json` next to the submission - useful for judge-model comparisons.

### Sol comparison and stability pilot

Generate a comparison rubric without replacing the frozen `rubric.json`:

```bash
env/bin/python scripts/generate_rubric.py <task-dir> \
  --model gpt-5.6-sol \
  --calibration-committee configs/judge-committee-rubric-calibration.json \
  --artifact-suffix sol \
  --write-final
```

This writes `evals/rubric.generated.sol.json` and `evals/rubric.sol.json`.

Before freezing a generated rubric, run the positive/negative discrimination gate:

```bash
env/bin/python scripts/run_negative_rubric_calibration.py <task-dir> \
  --rubric <task-dir>/evals/rubric.sol.json \
  --solution <task-dir>/evals/loesung.md \
  --committee configs/judge-committee-rubric-calibration.json \
  --output <output-dir>/negative-calibration.json \
  --cache-dir <output-dir>/negative-calibration-votes
```

Sol generates three case-internal negative variants per criterion: a bare result, a
wrong person/station/object, and a material legal or factual error. Sol does not vote.
Each type remains visible in the artifact, but a type is marked not applicable and is
excluded from judging when it cannot violate a literal rubric requirement without
inventing a new one (for example a bare-result test for a conclusion-only criterion).
Every positive reference control must pass with a stable committee majority; every negative variant of a
two- or three-star criterion must be stably rejected. One-star failures remain visible
warnings. The script never rewrites a rubric automatically and never receives external
professor labels.

Create two genuinely independent committee replicates by using separate vote-cache
directories with `configs/judge-committee-sol-pilot.json`. Analyze them with:

```bash
env/bin/python scripts/analyze_judge_stability.py \
  --scores baseline:r1=<baseline-r1.json> \
  --scores baseline:r2=<baseline-r2.json> \
  --scores agent:r1=<agent-r1.json> \
  --scores agent:r2=<agent-r2.json> \
  --output-json <stability.json> \
  --output-md <stability.md>
```

Use repeated `evaluation.run --criterion-id <ID>` flags for the targeted third run.
The case-neutral internal style calibration is run separately:

```bash
env/bin/python scripts/run_style_calibration.py \
  --fixtures tests/fixtures/gutachtenstil_calibration_v2.json \
  --judge-committee configs/judge-committee-sol-pilot.json \
  --replicates 2 \
  --cache-dir <style-votes> \
  --output-json <style-calibration.json> \
  --output-md <style-calibration.md>
```

The v2 style fixture contains 18 balanced minimal pairs across civil, criminal, and
public law. It is deliberately marked `draft_requires_jurist_review`: it is engineering
calibration, not juristic expert gold, until the labels have been reviewed externally.

## Export a Markdown review of a judged submission

For legal reviewers who want to read the system's answer and the scoring side by
side:

```bash
env/bin/python scripts/export_review_md.py \
  runs/<run>/<id>/tasks/<task>/submission
```

Writes `review.md` next to the submission: header with pass rate and
per-station breakdown, the full solution, then every rubric criterion grouped by
Prüfungsstation with its TRUE/FALSE verdict, the criterion text, the judge's
reasoning, and its evidence quotes. Pass several submission dirs at once, or
`--output FILE` for a single one.

## Run OpenCode as a solver harness

Validate the smoke taskset without model calls:

```bash
env/bin/python scripts/run_opencode_taskset.py \
  --taskset tasksets/opencode-smoke.jsonl \
  --dry-run
```

### Enforcement profiles

`--sandbox` picks how the solver is confined. Both enforced profiles give the
same invariant — the repository, `evals/`, gold solutions, `.env` and other
runs do not exist for the agent — and both record which profile ran in
`manifest.json`.

| Profile | Requirement | Use |
|---|---|---|
| `docker` | Docker daemon | Local workstations |
| `bwrap` | Linux, unprivileged user namespaces | Cluster / compute nodes |
| `local` | none | Debugging only — unconfined, never for headline runs |

**Docker profile.** Build the image once:

```bash
docker build -f docker/opencode-harness.Dockerfile -t lab-eu-opencode-harness:latest .
```

**bwrap profile.** Compute nodes generally have no Docker daemon, so the jail
is built from unprivileged namespaces instead. It needs the OpenCode CLI as a
bind-mountable tree (pinned to the same version the image builds):

```bash
scripts/install_opencode.sh
```

This vendors OpenCode into `vendor/opencode/` (gitignored, ~320 MB, no node or
network needed afterwards) and prepares `vendor/opencode-home/opencode/` — the
plugin tree the jail binds read-only. Inside the jail OpenCode cannot resolve
its plugin dependencies and reinstalls them into `$HOME` on *every* task: 54 MB
and 3,442 files each, 21 GB across one 45-case study. With the prepared tree
bound over that path, per-task jail state drops to ~35 files and the install
step disappears from every run. Preparation needs one throwaway model call, so
run the script with a provider key in the environment; without the tree the
harness still works, just wastefully. Then run with `--sandbox bwrap`. Before the first
model call the runner refuses to start unless bwrap can build a namespace
*and* the vendored CLI actually executes inside one.

Inside the jail the agent sees `/task` (read-only sanitized input), `/work`
(its writable workspace), `/home/agent` (OpenCode's own state, kept out of the
workspace), `/opt/opencode` and the system runtime — nothing else. Because the
repository lives under `/work/<user>/`, mounting the workspace at `/work`
also shadows the entire host tree it sits in. The environment is a whitelist
built by `--clearenv`, and the provider key is handed to bwrap over a pipe, so
it appears neither in host `ps` output nor in the recorded `metadata.json`
command. Network namespaces are *not* unshared — the agent loop calls the
provider from inside the jail — so agent egress stays policy-guarded by the
OpenCode permission config (`webfetch`/`websearch` denied), not enforced.
`scripts/sandbox_spec.py` is the whole specification; the probes in
`tests/test_sandbox_bwrap_escape.py` assert the invariant from inside a real
jail.

Run OpenCode through OpenRouter DeepSeek V4 Pro with medium reasoning:

```bash
env/bin/python scripts/run_opencode_taskset.py \
  --taskset tasksets/opencode-smoke.jsonl \
  --sandbox bwrap \
  --model openrouter/deepseek/deepseek-v4-pro \
  --variant medium
```

`OPENROUTER_API_KEY` is read from the repo-root `.env` (or the ambient
environment).

The runner sanitizes task inputs before solving: OpenCode only sees `task.json`
and `documents/`, not `evals/`, rubrics, or gold solutions. Results are written
under `runs/<run-name>/<run-id>/`.

### Retries

Long agent runs die to things that have nothing to do with the task — a
provider dropping a 502 into the response stream twelve minutes into a
generation costs the whole task. Both runners therefore retry: 1 attempt plus
10 retries by default (`--max-attempts`), with equal-jitter exponential
backoff from 5 s up to 5 min (`--retry-base-delay`).

What is retried is deliberately narrow:

| Outcome | Example | Retried |
|---|---|---|
| `transient` | 429/5xx, `provider_unavailable`, dropped stream, non-zero exit | yes |
| `timeout` | solver exceeded `--timeout-seconds` | only with `--retry-on-timeout` |
| `fatal` | rejected key, unknown model, no credits | no — fails in seconds |
| `solver` | ran to completion, wrote no deliverable | **no** |

The last row is the important one. Repeating a solver that finished without
producing its deliverable is best-of-N sampling: with 10 retries the reported
score would quietly become the best of ten attempts, which is not what a
benchmark number is supposed to mean. Infrastructure failures are repeated
because the task never got a fair attempt; solver failures are recorded as
failures. The policy is in `scripts/retry_util.py` and is written into every
run's `manifest.json` under `retry_policy`.

Each retry starts from a clean workspace — a rebuilt `work/`, a discarded
`submission/`, and for the bwrap profile a fresh OpenCode state — so a partial
file from a failed attempt is never presented to the next one as its own prior
work. The failed attempt's diagnostics are kept under
`tasks/<task>/attempts/NN/`, and `metadata.json` lists every attempt with its
outcome and reason.

Each task result includes audit artifacts:

- `stdout.jsonl`: raw OpenCode JSON event stream.
- `trace.jsonl`: normalized tool/file trace extracted from OpenCode events.
- `trace.md`: human-readable trace summary.
- `reasoning_trace.summary.json`: summary and size metadata for provider-emitted
  reasoning details, without expanding full private reasoning text.
- `workspace.before.json` and `workspace.after.json`: file snapshots.
- `fs_changes.json`: created, modified, and deleted files with hashes.
- `metadata.json`: includes the exact sandbox invocation (`command`), with
  secret values masked.
- `jail_home/` (bwrap profile): OpenCode's own state from inside the jail.
- `attempts/NN/` (only when a task was retried): stdout, stderr and jail
  state of each failed attempt.

Judge a completed run:

```bash
env/bin/python scripts/judge_run.py \
  runs/opencode-openrouter-deepseek-v4-pro-medium/<run-id> \
  --judge-model gpt-5.5
```

`judge_run.py` defaults to `--votes 1`: measured judge agreement on real
submissions is ~95% unanimous, so a single vote flips only ~1-2% of verdicts
at a third of the cost. Pass `--votes 3` for final headline runs where that
last bit of stability matters. Rubric calibration during generation is
unaffected - it keeps its own 3-vote setting.

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
  --api-base https://openrouter.ai/api/v1
```

The API key is read from the repo-root `.env`, selected by endpoint:
`OPENROUTER_API_KEY` for OpenRouter, `DEEPSEEK_API_KEY` for the DeepSeek API,
`OPENAI_API_KEY` otherwise.

The model sees the task instructions plus all documents inlined into one
prompt (evals/ is never included) and its entire response is saved as the
deliverable under `submission/`. Baseline tasks must have exactly one
deliverable. `--reasoning-effort` is optional and only for endpoints that
accept the chat-completions `reasoning_effort` parameter.

The baseline uses the same retry policy as the OpenCode harness
(`--max-attempts`, default 1 + 10 retries): upstream failures and empty
completions are repeated with backoff, a rejected key or unknown model fails
immediately.

One invocation processes the whole taskset (`--parallel N` for concurrent
tasks). Add `--judge` to score all submissions immediately after the run in
the same command (`--judge-model`, `--judge-votes`; judging needs
`OPENAI_API_KEY`).
