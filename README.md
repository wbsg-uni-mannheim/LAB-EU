LAB-EU is a benchmark for evaluating the capabilities of LLM agents to apply German, French and other European laws and to write long-form legal documents in accordance with different European laws.

LAB-EU builds on Harvey Legal Agent Benchmark (LAB). LAB-EU extends LAB with tasks in different languages covering different European jurisdictions.


## LAB-EU Task Model

Every task is a directory containing `task.json`, a `documents/` and an `evals/` folder:

```text
tasks/
  <legislation>/
	<practice-area>/
		<task-or-workflow>/
			<optional-scenario>/
			task.json
			documents/
			evals/
```

Flat and nested task IDs are both valid:

```text
de/verwaltungsrecht/verpflichtungsklage/fall-05-verpflichtungsklage-auf-polizeiliches-einschreiten-wegen-schmaehkritik
fr/droit-prive/examen-du-contrat-d-achat-d-un-vehicule-automobile
```

Important `task.json` fields:

| Field | Purpose |
|---|---|
| `title` | Human-readable task title |
| `instructions` | Directional prompt sent to the agent |
| `work_type` | `analyze`, `draft`, `review`, or `research` |
| `deliverables` | Expected output filenames |
| `criteria` | Optional or generated Boolean LLM-judge rubric criteria |
| `tags` | Discovery and analysis metadata |
| `license` | License terms that apply to this task |

---

See [docs/generating-rubrics.md](docs/generating-rubrics.md) for the step-by-step guide to generating rubrics (single task and cheaper multi-task batch), and [docs/rubric-generation.md](docs/rubric-generation.md) for the design rationale.
Active prompt templates live under [prompts/](prompts/README.md), separated from code for legal review.

To generate a calibrated draft rubric for a task (three generator roles, then a
judge/refine calibration loop against the gold solution):

```bash
env/bin/python scripts/generate_rubric.py <task-dir> --model gpt-5.5 --write-final
```

To evaluate an answer against `evals/rubric.json` (use `--votes 3` for headline runs):

```bash
env/bin/python -m evaluation.run <task-dir> <answer-file> --judge-model gpt-5.5 --votes 3
```

## Lawyer Workbench

The local bilingual workbench lets legal reviewers run a reproducible manual
study against a proprietary model. A study stores:

- study name, model, provider, reviewer, and German or French task language;
- the exact editable system prompt;
- whether the system is an agent or a single LLM;
- whether web search, databases, or other tools are used;
- one prompt and pasted response per task, presented sequentially.

By default the study contains every task in the selected language. Reviewers
can restrict it to tasks that already have an LLM-judge rubric. Studies can be
closed and resumed later. Completed judge-ready studies use the existing
`scripts/judge_run.py` layout. The workbench can also create a narrow Git commit
and GitHub pull request when the rest of the worktree is clean.

```bash
env/bin/pip install -r requirements.txt
env/bin/python scripts/run_lawyer_workbench.py
```

Then open `http://127.0.0.1:5050`. The server listens on the local loopback
interface only. See [workbench/README.md](workbench/README.md) for the complete
installation and study guide. See
[LAWYER_WORKBENCH_PLAN.md](LAWYER_WORKBENCH_PLAN.md) for the architecture,
safety boundaries, and planned task-authoring phase.

See [scripts/README.md](scripts/README.md) for the OpenCode agent harness and the
single-LLM-call baseline, and [docs/leakage-and-contamination.md](docs/leakage-and-contamination.md)
for the planned contamination controls.
