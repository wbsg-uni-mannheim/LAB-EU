# German First State Exam Core Study (45 cases)

This study fixes the first broad LAB-EU evaluation set at 45 German-law cases:
15 public-law, 15 criminal-law, and 15 civil-law tasks. Every task has a
calibrated canonical rubric at `evals/rubric.json`.

The study compares two conditions using the same underlying model:

1. `baseline`: one model call, no tools;
2. `agent`: OpenCode in an isolated per-task Docker workspace.

The solver receives only `task.json` and `documents/`. Gold solutions and
rubrics remain outside the solver workspace. Runs are written below `runs/`
and are not version-controlled.

## Reproducibility boundary

- Taskset: `studies/de-core-45/taskset.jsonl`
- Cases: 45
- Rubric commit: `2a31e750f4d43ecbce74860de9666ab70abe0c74`
- Shared system prompt: `prompts/harness/study_system_prompt.txt`
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
  --sandbox docker \
  --parallel 1
```

Each invocation creates a new immutable run directory. Do not expose `evals/`
to the solver and do not reuse answers between the baseline and agent arms.
