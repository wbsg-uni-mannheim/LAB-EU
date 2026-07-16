# LAB-EU Study Workbench

The Study Workbench is a small local website for running reproducible legal
benchmark studies without editing JSON files or using model APIs.

A legal reviewer configures the tested system once and then works through the
selected LAB-EU cases in sequence. For every case, the website creates one
complete prompt containing both the stored system instructions and the current
case. The reviewer copies that prompt into the proprietary AI system and pastes
the unmodified answer back into the website.

The website runs only on the reviewer's computer. It does not send prompts or
answers to a model provider itself.

## Requirements

Install these programs once:

- Git
- Python 3.11 or newer
- the [GitHub CLI](https://cli.github.com/) if studies should be submitted
  through GitHub

You also need access to the LAB-EU GitHub repository.

## First-time setup

### 1. Clone the repository

```bash
git clone https://github.com/wbsg-uni-mannheim/LAB-EU.git
cd LAB-EU
```

If the repository is already present, open a terminal in its directory and
make sure you are on the current `main` branch:

```bash
git switch main
git pull --ff-only
```

### 2. Create the Python environment

On macOS or Linux:

```bash
python3 -m venv env
env/bin/python -m pip install --upgrade pip
env/bin/python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
py -m venv env
env\Scripts\python -m pip install --upgrade pip
env\Scripts\python -m pip install -r requirements.txt
```

### 3. Set up GitHub submission

This step is only required if the reviewer should create commits and pull
requests from the website:

```bash
gh auth login
gh auth status
```

Follow the GitHub CLI login instructions. The website does not store a GitHub
password or token.

## Start the website

On macOS or Linux:

```bash
env/bin/python scripts/run_lawyer_workbench.py
```

On Windows:

```powershell
env\Scripts\python scripts/run_lawyer_workbench.py
```

Leave the terminal window open and visit:

<http://127.0.0.1:5050>

If port `5050` is already occupied, choose another local port:

```bash
env/bin/python scripts/run_lawyer_workbench.py --port 5051
```

The website listens only on `127.0.0.1`; it is not made publicly accessible.

## Start a study

### 1. Describe the tested system

Enter:

- a clear study name;
- the exact model name and version, if known;
- German or French as the language of the cases;
- the provider and the person conducting the study.

Then describe how the system works:

- **Single LLM:** one prompt directly produces one answer.
- **Agent:** the system may plan intermediate steps, call tools, or make
  several model calls.
- **Web search:** the system can consult public websites or search engines.
- **Databases:** the system can query legal databases, internal knowledge
  stores, or other structured sources.
- **Other tools:** the system can use functions such as document analysis,
  calculations, code execution, or file access.
- **System unknown:** use this when these technical properties cannot be
  determined reliably. The website will not guess the other properties.

Use the same model and the same allowed resources for every case in the study.

### 2. Review the system prompt

The text field initially contains the versioned LAB-EU study system prompt from
[`prompts/harness/study_system_prompt.txt`](../prompts/harness/study_system_prompt.txt).

Review it before starting. The exact text is stored with the study and cannot
silently change between cases.

The standard prompt prohibits external sources. If the study intentionally
allows web search or databases, adjust that restriction explicitly before
starting the study.

### 3. Choose the scope

By default, the study includes every available case in the selected language.

Enable **Only use cases with an existing judge rubric** when the completed
study should be evaluated directly with the current LAB-EU LLM judges. The
website displays the resulting number of cases before the study starts.

### 4. Start

Select **Start study**. The configuration and ordered task list are now stored
under:

```text
runs/studies/<study-id>/
```

## Work through the cases

For each case:

1. Read the title and, if useful, inspect the displayed source documents.
2. Select **Copy complete prompt**.
3. Paste the copied text into the proprietary AI system as one input.
4. Wait for the complete answer.
5. Copy the answer without correcting, shortening, or rewriting it.
6. Paste it into the **Model answer** field.
7. Confirm that it contains no confidential client information.
8. Select **Save answer and open next case**.

The complete copied prompt already contains:

- the frozen study system prompt; and
- the current LAB-EU case prompt and documents.

Only one copy operation is therefore needed per case.

Draft text in the answer field is temporarily retained in the browser. A saved
answer is written to the study directory and the next case opens
automatically.

## Pause or resume a study

You may close the browser or stop the local website at any time. Saved answers
and study progress remain on disk.

After restarting the website, choose the study under **Resume existing study**
and select **Resume**.

## Submit early

After at least one answer has been saved, the study can be ended with
**Submit study early**.

The website asks for confirmation because this action is final:

- saved answers are preserved;
- the current and remaining cases are recorded as unanswered;
- the study cannot subsequently be continued;
- the incomplete study remains available for evaluation and submission.

## Evaluate a completed study

For studies restricted to judge-ready cases, the completion screen displays a
command similar to:

```bash
env/bin/python scripts/judge_run.py runs/studies/<study-id> \
  --judge-model gpt-5.5 --votes 3
```

Judging requires a suitable API key in the repository's local `.env` file, for
example:

```text
OPENAI_API_KEY=...
```

The `.env` file is ignored by Git and must never be committed.

## Submit through GitHub

Before starting the website for a submission session, use:

```bash
git switch main
git pull --ff-only
```

On the completion screen:

1. leave `main` as the target branch unless instructed otherwise;
2. choose whether a pull request should be created;
3. confirm the Git action;
4. select **Commit and submit study**.

The website then:

1. creates a dedicated `submission/...` branch;
2. stages only the selected study directory;
3. creates a commit;
4. pushes the branch;
5. optionally opens a GitHub pull request.

Other untracked directories under `runs/` do not block submission. Changes to
source code, documentation, tracked files, or already staged unrelated files
do block it, preventing accidental inclusion in the study commit.

After a successful submission, switch back to `main` before starting another
submission:

```bash
git switch main
git pull --ff-only
```

## Stored study files

```text
runs/studies/<study-id>/
  manifest.json
  system_prompt.md
  tasks/
    <task-id>/
      prompt.md
      combined_prompt.md
      response.md
      metadata.json
      submission/<deliverable>
```

The manifest records the model, provider, reviewer, language, capabilities,
scope, progress, and whether the study ended normally or early. SHA-256 hashes
tie every answer to the exact prompts used.

## Confidentiality

Do not paste client names, personal data, confidential documents, or other
protected information into a benchmark study. The website stores submitted
answers as ordinary files inside the local repository.

## Troubleshooting

### `No module named flask`

Install the dependencies again:

```bash
env/bin/python -m pip install -r requirements.txt
```

### The page does not open

Check that the terminal running the website is still open. Try a different
port if necessary:

```bash
env/bin/python scripts/run_lawyer_workbench.py --port 5051
```

### GitHub submission requires authentication

```bash
gh auth login
gh auth status
```

### Git submission is blocked

Return to `main` and inspect tracked changes:

```bash
git switch main
git status
```

Do not delete study directories merely to clean the status. Untracked
directories below `runs/` are allowed. Resolve only unrelated tracked or staged
changes before retrying.
