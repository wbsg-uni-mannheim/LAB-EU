---
name: github-safe-collaboration
description: Safely use Git and GitHub to inspect changes, create a separate branch, stage exact files, commit, push, and open a pull request. Use whenever a user asks to submit work to GitHub, create commits or pull requests, work with branches, or resolve Git conflicts, especially when the user may be unfamiliar with Git. Never push directly to main, never use force operations, and never resolve merge conflicts without explicit per-conflict user direction.
---

# Safe GitHub Collaboration

Use GitHub for versioned collaboration through a separate branch and pull
request. Treat the user's files and repository history as valuable data.

## Non-negotiable safety rules

- Never push directly to `main`, `master`, or another protected default branch.
- Never use `git push --force`, `git push --force-with-lease`, `git reset
  --hard`, `git clean -f`, `git clean -fd`, `git branch -D`, destructive
  `git checkout`, destructive `git restore`, history pruning, or an equivalent
  irreversible command.
- Never use `git commit --amend` or rebase published work unless the user
  specifically requests history rewriting and fully understands it. In this
  skill, prefer a new commit.
- Never discard, overwrite, hide, or silently include unrelated user changes.
- Never stage the whole repository without first inspecting the worktree.
  Prefer exact paths.
- Never guess how to resolve a merge conflict.
- Never expose credentials, tokens, `.env` contents, or private keys.

## Calibrate explanations and permission

Start with read-only commands such as:

```bash
git status --short
git branch --show-current
git remote -v
git diff --stat
```

If the user has not used GitHub before, says they do not understand Git, or
appears uncertain:

1. Explain the purpose and effect of the next state-changing action in plain
   language.
2. Name the branch, files, remote, and expected result.
3. Ask for explicit permission before each of these phases:
   - updating the local default branch;
   - creating or switching a branch;
   - staging files;
   - creating a commit;
   - pushing;
   - opening a pull request.
4. Allow the user to approve a clearly enumerated sequence at once, but never
   treat a vague request as approval for additional destructive or unrelated
   actions.

For an experienced user who explicitly asks to commit and open a pull request,
the normal branch, stage, commit, push, and PR sequence is authorized. Still
report what will happen and preserve all safety rules.

## Safe branch workflow

### 1. Inspect

Check the current branch, changes, staged files, and remotes. Identify unrelated
changes and generated artifacts before changing state.

### 2. Synchronize safely

Do not switch branches while that could overwrite local work. Explain any dirty
worktree first.

When safe and authorized:

```bash
git switch main
git fetch origin
git merge --ff-only origin/main
```

Use `--ff-only` so synchronization stops instead of creating an unexpected
merge commit. If the repository uses another default branch, use that branch.

### 3. Create a separate branch

Choose a descriptive branch such as:

```bash
git switch -c case/fr-short-case-name
```

or:

```bash
git switch -c docs/update-study-guide
```

Never perform the requested work directly on `main`.

### 4. Stage exact files

Show the user which files will be included. Stage only intended paths:

```bash
git add -- path/to/task.json path/to/documents path/to/evals
git diff --cached --stat
git diff --cached --check
git diff --cached
```

Do not include runs, credentials, temporary files, unrelated documents, or
other changes unless the user explicitly requests them.

### 5. Commit

Explain that a commit records the staged snapshot locally. Use a concise
message:

```bash
git commit -m "Add French obligations case"
```

If the commit fails, inspect and explain the failure. Do not bypass hooks or
validation without explicit user approval.

### 6. Push the branch

Explain that pushing uploads the branch to GitHub without changing `main`:

```bash
git push -u origin case/fr-short-case-name
```

Confirm the actual current branch immediately before pushing. Refuse a command
that would push to the protected default branch.

### 7. Open a pull request

Explain that a pull request asks maintainers to review and merge the branch:

```bash
gh pr create \
  --base main \
  --head case/fr-short-case-name \
  --title "Add French obligations case" \
  --body "Adds a draft French case with sources, reference solution, and rubric."
```

Report the pull-request URL. Do not merge the pull request unless the user
separately asks and has authority to do so.

## Merge conflicts

If any merge, update, or pull produces a conflict:

1. Stop immediately. Do not stage or commit a resolution.
2. Run read-only inspection:

   ```bash
   git status --short
   git diff --name-only --diff-filter=U
   git diff -- path/to/conflicted-file
   ```

3. List every conflicted file separately.
4. For each conflict, explain both versions in plain language:
   - current/local branch version;
   - incoming GitHub version;
   - any safe combined alternative you can identify.
5. Ask the user which version to use for each file or each distinct conflict.
6. Apply only the resolution the user explicitly selects.
7. Show the resolved diff before staging it.

Never automatically choose `ours`, `theirs`, the newer-looking version, or a
combined version.

If the user cannot decide, or resolving the conflict would be risky:

- leave the conflict untouched;
- explain that no data has been discarded;
- offer, after explicit permission, to abort the merge and create a fresh
  branch from the current remote default branch while preserving the work in a
  non-destructive form;
- tell the user to email the repository maintainer, such as Aaron, with the
  branch name and conflict list so the issue can be resolved together.

Do not abort a merge, move work, or create the replacement branch without
explicit user permission.

## Authentication

If GitHub authentication is missing, explain and use:

```bash
gh auth login
gh auth status
```

Let the user complete browser login, passwords, one-time codes, or security
prompts. Never request that credentials be pasted into chat.

## Handoff

At completion, report:

- branch name;
- commit hash and message;
- pushed remote branch;
- pull-request URL, if created;
- validations performed;
- files intentionally left uncommitted;
- any remaining conflict or required human review.
