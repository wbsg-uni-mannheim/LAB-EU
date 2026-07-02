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
de/verwaltungsrecht/verpflichtungsklage-auf-polizeiliches-einschreiten-wegen-schmaehkritik
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

See [docs/rubric-generation.md](docs/rubric-generation.md) for the proposed workflow for deriving Boolean rubrics from human solutions.
Active prompt templates live under [prompts/](prompts/README.md), separated from code for legal review.

To generate a draft rubric for a task:

```bash
env/bin/python scripts/generate_rubric.py <task-dir> --model gpt-5.5 --write-final
```

To evaluate an answer against `evals/rubric.json`:

```bash
env/bin/python -m evaluation.run <task-dir> <answer-file> --judge-model gpt-5.5
```
