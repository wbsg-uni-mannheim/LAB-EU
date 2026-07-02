# Scripts

## Generate a rubric from a human solution

```bash
env/bin/pip install -r requirements.txt

env/bin/python scripts/generate_rubric.py \
  tasks/de/verwaltungsrecht/verpflichtungsklage-auf-polizeiliches-einschreiten-wegen-schmaehkritik \
  --model gpt-5.5 \
  --write-final
```

The script runs three model calls:

1. atomize the human solution into legally material answer atoms;
2. generate an intentionally over-complete candidate rubric;
3. prune the candidate pool to a Boolean rubric with a model-selected number of material criteria.

The generated audit file is written to `evals/rubric.generated.json`. With
`--write-final`, the pruned rubric is also written to `evals/rubric.json` with
`review_status: generated_needs_human_review`.

The active prompt templates are in `prompts/`, so legal reviewers can inspect
or edit the wording without touching the Python scripts.

Use `--dry-run` to check local file discovery without calling the API.

## Evaluate an answer with a rubric

```bash
env/bin/python -m evaluation.run \
  tasks/de/verwaltungsrecht/verpflichtungsklage-auf-polizeiliches-einschreiten-wegen-schmaehkritik \
  path/to/fallloesung-sut.md \
  --judge-model gpt-5.5
```

If the submission is a file, every criterion sees that file. If the submission
is a directory, criteria with `deliverables` only see the matching files in that
directory. The score file is written as `scores.json` next to the submission.

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
