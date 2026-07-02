# OpenCode Harness Plan

This plan describes how to run OpenCode as a legal-benchmark solver for a fixed
task list, with one sandboxed task workspace per run and judge-ready results in a
separate output tree.

## Goals

- Run only tasks named in a single explicit taskset file.
- Give OpenCode access only to the active task directory while solving a task.
- Require OpenCode to write the requested legal solution deliverable as Markdown.
- Store every run under a separate results directory.
- Feed those result directories into the existing `evaluation.run` LLM judge.
- Record enough metadata to reproduce the model, provider, reasoning variant,
  prompt, sandbox command, timing, and exit status.

## Current Repo Fit

The repo already has the right task contract:

```text
tasks/<jurisdiction>/<practice-area>/<task-id>/
  task.json
  documents/
  evals/rubric.json
```

The existing judge already accepts either one answer file or a directory of
deliverables:

```bash
env/bin/python -m evaluation.run <task-dir> <submission-file-or-dir> --judge-model gpt-5.5
```

The harness should therefore be a thin runner around the current task model, not
a second benchmark format.

## External Tool Facts To Rely On

- OpenCode supports non-interactive execution through `opencode run [message..]`.
- `opencode run` supports `--model provider/model`, `--variant`, `--dir`,
  `--format json`, `--agent`, and auto-approval flags.
- OpenCode permissions can deny or allow tools and can restrict external
  directories, but they are not the hard isolation boundary for this benchmark.
  Use an OS/container sandbox for isolation, and use OpenCode permissions as a
  second guardrail.
- On this machine, OpenCode exposes DeepSeek V4 Pro through OpenRouter as
  `openrouter/deepseek/deepseek-v4-pro`.
- The local OpenRouter model entry exposes `low`, `medium`, and `high` reasoning
  variants for DeepSeek V4 Pro. Record the requested variant in run metadata.

Sources checked on 2026-06-30:

- [OpenCode CLI](https://opencode.ai/docs/cli/)
- [OpenCode models and variants](https://opencode.ai/docs/models/)
- [OpenCode permissions](https://opencode.ai/docs/permissions/)
- [OpenCode providers](https://opencode.ai/docs/providers/)
- [DeepSeek OpenCode integration](https://api-docs.deepseek.com/quick_start/agent_integrations/opencode)
- [DeepSeek thinking mode](https://api-docs.deepseek.com/guides/thinking_mode)

## Proposed Files

```text
tasksets/
  opencode-smoke.jsonl
scripts/
  run_opencode_taskset.py
  judge_run.py
docker/
  opencode-harness.Dockerfile
  opencode-runner-entrypoint.sh
runs/
  .gitignore
```

`runs/` should be ignored by Git because it will contain solver outputs,
transcripts, logs, and judge scores.

## Taskset Manifest

Use JSONL so a run can be limited to one exact list of tasks and extended without
merge-heavy array edits.

Example `tasksets/opencode-smoke.jsonl`:

```jsonl
{"task_id":"de/verwaltungsrecht/verpflichtungsklage-auf-polizeiliches-einschreiten-wegen-schmaehkritik","task_dir":"tasks/de/verwaltungsrecht/verpflichtungsklage-auf-polizeiliches-einschreiten-wegen-schmaehkritik"}
```

Runner validation:

- Each row must resolve under `tasks/`.
- Each task must contain `task.json`, `documents/`, and `evals/rubric.json`.
- Duplicate `task_id` values fail the run.
- `task.json.deliverables` should be normalized to a list in the runner because
  the current sample task stores it as a string.

## Run Layout

Use a stable results tree independent of `tasks/`:

```text
runs/opencode-openrouter-deepseek-v4-pro-medium/<run-id>/
  manifest.json
  tasks/
    de__verwaltungsrecht__verpflichtungsklage-.../
      input_task_dir.txt
      prompt.md
      stdout.jsonl
      stderr.log
      trace.jsonl
      trace.md
      workspace.before.json
      workspace.after.json
      fs_changes.json
      metadata.json
      workspace.tar.gz
      submission/
        fallloesung-sut.md
      scores.json
```

`manifest.json` should include:

```json
{
  "schema_version": "0.1",
  "harness": "opencode",
  "opencode_version": "1.17.8",
  "model_requested": "openrouter/deepseek/deepseek-v4-pro",
  "reasoning_requested": "medium",
  "taskset": "tasksets/opencode-smoke.jsonl",
  "started_at": "2026-06-30T00:00:00Z"
}
```

Each per-task `metadata.json` should include:

- task id and source task path
- sandbox command
- OpenCode command
- raw OpenCode event stream path
- normalized trace paths
- workspace before/after snapshot paths
- filesystem change summary
- started/ended timestamps and duration
- exit code
- expected deliverables
- actual deliverables found
- timeout status
- file hashes for generated deliverables

## Sandbox Model

Use Docker or another container runtime as the primary sandbox. The key property
is that each OpenCode process sees only:

- `/task` mounted read-only from the source task directory
- `/work` as a fresh writable copy of `/task`
- `/out` as a fresh writable per-task result directory
- a minimal home/config directory containing only OpenCode config and credentials

Recommended bind mounts:

```bash
docker run --rm \
  --network bridge \
  --cpus 2 \
  --memory 4g \
  --pids-limit 256 \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  -e DEEPSEEK_API_KEY \
  -v "$TASK_DIR:/task:ro" \
  -v "$WORK_DIR:/work:rw" \
  -v "$OUT_DIR:/out:rw" \
  lab-eu-opencode-harness:latest \
  /runner/opencode-runner-entrypoint.sh
```

For stricter reproducibility, also pin:

- OpenCode version
- Node/runtime version
- image digest
- timezone, locale, and current date passed in the prompt
- network policy

Network policy decision:

- If the legal task is closed-book, allow network only for model API traffic.
- If the agent must not browse, deny OpenCode `webfetch` and `websearch` and block
  general outbound traffic except the model provider endpoint.
- If future tasks explicitly test research, add `allow_network: true` to the
  taskset row and make that exception visible in metadata.

## OpenCode Configuration

Preflight on the host:

```bash
opencode --version
opencode providers list
opencode models --refresh
opencode models openrouter --verbose
```

If OpenRouter is not configured, run OpenCode once and connect the provider:

```text
/connect
openrouter
<OpenRouter API key>
/models
DeepSeek V4 Pro
```

The actual runner should still pass the model explicitly:

```bash
opencode run \
  --dir /work \
  --model openrouter/deepseek/deepseek-v4-pro \
  --variant medium \
  --format json \
  --agent lab-eu-solver \
  --title "LAB-EU ${TASK_ID}" \
  "$(cat /runner/prompt.md)"
```

If the provider/model string differs after `opencode models --refresh`, use the
string printed by OpenCode and store it in `manifest.json`.

Recommended local OpenCode config in the container:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "*": "deny",
    "read": "allow",
    "glob": "allow",
    "grep": "allow",
    "edit": {
      "*": "deny",
      "/work/**": "allow",
      "/out/**": "allow"
    },
    "bash": {
      "*": "deny",
      "ls *": "allow",
      "find *": "allow",
      "sed *": "allow",
      "cat *": "allow",
      "pwd": "allow"
    },
    "webfetch": "deny",
    "websearch": "deny",
    "external_directory": "deny"
  }
}
```

The container sandbox is still required because `bash` can be difficult to
constrain perfectly with command-pattern permissions alone.

## Solver Prompt Contract

The runner should generate a prompt per task from `task.json`.

Prompt skeleton:

```text
You are solving one LAB-EU legal benchmark task.

You may use only the files in this task workspace. Do not use external legal
sources, internet search, or files outside the workspace.

Task title:
{title}

Task instructions:
{instructions}

Available documents are in ./documents.

Required deliverables:
{deliverables}

Write the final answer as Markdown. Do not write analysis notes, scratch files,
or alternative answers. Save only the required deliverable file(s).
```

For the current sample task, the required output should be:

```text
fallloesung-sut.md
```

After OpenCode exits, the entrypoint should copy required deliverables from
`/work` into `/out/submission/`. If OpenCode writes directly to `/out/submission`,
the runner should still verify file names and hash contents.

## Runner Flow

`scripts/run_opencode_taskset.py` should:

1. Parse `--taskset`, `--run-name`, `--model`, `--variant`, `--timeout-seconds`,
   `--parallel`.
2. Create `runs/<run-name>/<run-id>/manifest.json`.
3. For each task row, create an isolated host-side work dir and result dir.
4. Copy the task directory into the work dir.
5. Generate `prompt.md`.
6. Start one sandboxed OpenCode process for that task.
7. Stream OpenCode JSON events to `stdout.jsonl` and stderr to `stderr.log`.
8. Enforce wall-clock timeout and mark timeout in metadata.
9. Extract `trace.jsonl` and `trace.md` from the raw OpenCode JSON events.
10. Diff before/after workspace snapshots into `fs_changes.json`.
11. Verify required deliverables exist under `submission/`.
12. Archive the final task workspace to `workspace.tar.gz` for audit.
13. Write per-task `metadata.json`.

The default should be serial execution. Add `--parallel` only after API rate
limits and judge cost are known.

## Judge Flow

`scripts/judge_run.py` should walk the result tree and call the current judge:

```bash
env/bin/python -m evaluation.run \
  "$TASK_DIR" \
  "$RESULT_TASK_DIR/submission" \
  --judge-model "$JUDGE_MODEL"
```

The judge writes `scores.json` into each `submission/` directory today. The
wrapper should copy or symlink that file to the per-task root as:

```text
runs/<run-name>/<run-id>/tasks/<task-id-safe>/scores.json
```

This keeps all result artifacts in one place and avoids modifying task source
directories.

## CLI Examples

Preflight:

```bash
opencode --version
opencode providers list
opencode models --refresh
opencode models openrouter --verbose
```

Build runner image:

```bash
docker build -f docker/opencode-harness.Dockerfile -t lab-eu-opencode-harness:latest .
```

Run the taskset:

```bash
env/bin/python scripts/run_opencode_taskset.py \
  --taskset tasksets/opencode-smoke.jsonl \
  --run-name opencode-openrouter-deepseek-v4-pro-medium \
  --model openrouter/deepseek/deepseek-v4-pro \
  --variant medium \
  --timeout-seconds 7200
```

Judge the run:

```bash
env/bin/python scripts/judge_run.py \
  runs/opencode-openrouter-deepseek-v4-pro-medium/<run-id> \
  --judge-model gpt-5.5
```

## Acceptance Checks

A setup is benchmark-ready when:

- Running with a one-task taskset produces exactly one per-task result directory.
- A task run cannot read another task directory or the repo root.
- A task run cannot write into `tasks/`.
- The required Markdown deliverable appears under `submission/`.
- `metadata.json` records model, variant, sandbox command, exit status, and file
  hashes.
- `trace.md`, `trace.jsonl`, and `fs_changes.json` are written for every task,
  including failed or timed-out runs.
- `evaluation.run` can score the submission directory without manual file moves.
- A failed or timed-out OpenCode run still writes metadata and logs.
- Re-running the same taskset creates a new run id without overwriting prior
  results.

## Implementation Order

1. Add `runs/.gitignore` and one smoke taskset.
2. Implement `scripts/run_opencode_taskset.py` without Docker first, using a
   copied temporary workspace and `opencode run --dir`.
3. Implement the Docker entrypoint and switch the runner to Docker execution.
4. Add OpenCode config and agent prompt inside the container image.
5. Add deliverable verification and metadata hashing.
6. Add `scripts/judge_run.py` wrapper around `evaluation.run`.
7. Run the one-task smoke test.
8. Tighten network policy after confirming the OpenRouter provider/model string.
9. Add CI-style dry-run checks that validate tasksets without model calls.

## Open Questions Before Running

- Should the runner use the locally configured OpenRouter auth file, an
  `OPENROUTER_API_KEY` environment variable, or both?
- Should closed-book legal tasks block all non-model outbound network traffic?
- Should OpenCode be allowed any shell commands, or should the solver be limited
  to file read/write tools only?
- Should failed or missing deliverables be judged as empty submissions, or only
  recorded as harness failures?
