# Lawyer Workbench: local submission app

## Goal

The Lawyer Workbench lets a legal reviewer use LAB-EU without editing JSON,
running model APIs, or knowing Git commands. Its primary workflow is now a
multi-case model study:

1. enter study name, model, provider/reviewer and task language;
2. edit and freeze the exact system prompt;
3. record whether the system is an agent or single LLM and which external
   resources it uses;
4. choose all language tasks or only judge-ready tasks;
5. process each task sequentially by copying its case prompt and pasting the
   result;
6. resume interrupted studies from disk;
7. judge the completed run and optionally submit it through GitHub.

The original single-task manual-run backend remains available for compatibility,
but the user interface is study-first.

Task authoring is a second workflow. It should reuse the same task contract,
but it should not be mixed into the first MVP because authoring also requires
source, licence, reference-solution and rubric review.

## Recommended MVP

Use a small local Python web application, started explicitly by the user and
bound to `127.0.0.1`. A server-rendered framework such as Flask is sufficient:
there is no need for a separate frontend build or database. `gh` remains the
GitHub authentication and pull-request client, so the app never stores a
GitHub token.

The app has four screens:

### 1. Choose a task

- scan `tasks/de/**/task.json` and `tasks/fr/**/task.json`;
- filter by language, jurisdiction, practice area, work type and tags;
- show title, instructions, deliverable and validation status;
- warn clearly when a task or rubric is a draft pilot.

### 2. Copy the prompt

- render the prompt with the same code and template as
  `scripts/run_baseline_taskset.py`;
- show the complete prompt read-only;
- offer one `Copy prompt` button;
- record a SHA-256 digest of the prompt so the submitted answer can later be
  tied to the exact input.

Prompt rendering must first be extracted into one shared module. A regression
test should assert that the CLI baseline and the workbench render identical
text for the same task and date.

### 3. Paste and review the answer

- one large Markdown input labelled in the selected UI language;
- optional model/provider and reviewer fields;
- word/character count and Markdown preview;
- save drafts outside Git, for example in `.lab-eu-workbench/drafts/`;
- require an explicit confirmation that no confidential client data was added.

The answer is stored verbatim apart from the baseline runner's existing outer
code-fence normalization. The app must never rewrite legal content.

### 4. Save and submit

Create the same essential shape as an automated run:

```text
runs/manual/<run-id>/
  manifest.json
  tasks/<safe-task-id>/
    prompt.md
    response.md
    metadata.json
    submission/<deliverable>
```

`metadata.json` should include at least task id, source task directory,
language, model/provider as entered by the reviewer, prompt digest, timestamps,
expected deliverable and `harness: manual-copy-paste`.

The submission action should:

1. refuse to continue when the repository has unrelated changes;
2. create a branch such as `submission/<reviewer>/<date>-<task-slug>`;
3. stage only the newly created manual-run files by exact path;
4. show the staged diff and proposed commit message;
5. commit only after a separate confirmation;
6. use `gh pr create` to open a pull request, again after confirmation;
7. show the resulting commit hash and pull-request URL.

Every Git command must use an argument list without a shell. All paths must be
resolved below the repository root, and task ids must be converted with the
existing `safe_task_id` function.

## German and French support

Content language and UI language are separate:

- the task language comes from `task.json` and falls back to the first path
  component below `tasks/`;
- the user can switch the interface between German and French at any time;
- the prompt already instructs the model to answer in the task language;
- UI text lives in two small dictionaries (`de`, `fr`), not in task files;
- filenames remain task-defined (`fallloesung-sut.md`, `consultation.md`, and
  so on).

French pilot tasks must remain labelled as drafts until source fidelity, legal
cross-check, French expert sign-off and rubric calibration are complete. A
successful technical judge run is not legal certification.

## Task authoring after the MVP

The authoring wizard can be added once the submission path is stable:

1. language and jurisdiction;
2. title, work type, instructions and deliverable filename;
3. source documents and provenance/licence;
4. reference solution;
5. rubric import or generation;
6. validation summary;
7. preview of the resulting `tasks/<language>/...` directory;
8. exact-path commit and pull request.

Incomplete work should be saved as a draft and must not be presented as a
benchmark-ready task. A task becomes runnable only when `task.json`,
`documents/` and `evals/rubric.json` pass the existing loader checks. Human
review remains mandatory for reference solutions and rubrics.

## Delivery phases and acceptance checks

### Phase 1: prompt and manual-run core

- extract shared task loading and prompt rendering;
- add tests for DE and FR prompt parity;
- write judge-compatible manual runs without invoking Git.

Acceptance: a pasted French or German answer can be dry-run validated by
`python -m evaluation.run <task-dir> <submission> --dry-run`.

### Phase 2: local bilingual UI

- implement the four-screen workflow;
- add DE/FR UI strings and persistent drafts;
- validate paths, required fields and Markdown output.

Acceptance: a non-technical reviewer can complete the flow without editing a
file or using the terminal.

### Phase 3: GitHub submission

- add clean-tree check, exact-path staging, diff preview, commit and `gh` pull
  request creation;
- surface actionable messages when Git or GitHub authentication is missing.

Acceptance: the pull request contains only one manual run and can be judged by
the existing batch tooling after checkout.

### Phase 4: task authoring

- add the guided task wizard and validation report;
- integrate the existing rubric generation/review workflow without making an
  LLM-generated rubric look approved.

Acceptance: a draft task PR contains the complete canonical directory shape,
provenance, review status and no generated run artefacts.

## Decisions to make before implementation

- whether manual model answers should be committed to this repository or to a
  separate private submissions repository;
- whether reviewers may submit directly to the main repository or only through
  forks;
- which metadata about proprietary model/provider/version is mandatory;
- whether a reference solution must remain hidden from reviewers testing a
  model;
- who is allowed to change a task's validation status from draft to approved.
