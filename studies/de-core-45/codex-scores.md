# Codex experiments: 45 cases, with and without web access

This release publishes the existing Codex artifacts for the same 45-case taskset
as the original study. It contains **45 submissions per arm**, all with resolved
content and legal-style judgments. No solver or judge was rerun for publication.

| Arm | Run | Mean content (%) | Mean legal style (%) |
| --- | --- | ---: | ---: |
| [Workspace only](../../runs/codex-no-web-45/20260806T190042Z) | `20260806T190042Z` | 70.04 | 79.62 |
| [Web access](../../runs/codex-web-45/20260806T110110Z) | `20260806T110110Z` | 77.09 | 83.77 |

These are arithmetic means of per-case pass rates, not examination grades.
The [90-row CSV](../../runs/de-core-45-codex-results.csv) contains the counts,
fractional pass rates and scoring dates for each case.

## Inspect an answer and its evaluation

Within each run, open `tasks/<task-id>/`:

- `submission/*.md`: the submitted answer, with its original filename.
- `scores.json`: canonical content and style results, including individual
  judge votes, reasons, evidence and tiebreak decisions. Use `criteria_results`
  for content and `style_results` for legal method/presentation.
- `prompt.md`, `metadata.json`, `response.md`: the recorded solver prompt,
  configuration and final response.
- `sources.json`, `sources.md`: recorded source-use and search-audit information.

The run-level `manifest.json`, `judge_config.json` and `source-summary.*`
provide configuration and source summaries. Each arm has 1,806 content and
1,452 style decisions. No final verdict is unresolved, and all final verdicts
and participating judge votes have nonempty reasoning.

## Configuration and historical boundary

The solver manifests record `gpt-5.6-sol` with medium reasoning effort. They
also state that the resolved model and reasoning effort cannot be independently
verified from the Codex event stream. The no-web arm uses workspace tool access;
the web arm uses full tool access and live search. Both record anonymized case
identities. The source-journal domain `zjs-online.com` was blocked in the web arm.
Search-leakage flags are informational; this policy does not establish that
underlying judgments or solutions elsewhere were never retrieved.

The judging committee uses Gemini and Luna as primaries and Terra as tiebreaker.
For each arm, 44 scores are dated 7 August 2026; Kaufrausch was re-scored on
21 August. This publication includes that correction. The score files are copied
byte-for-byte, including their original paths and timestamps. Absolute paths
refer to the original local checkout and do not need to exist to read the data.

These experiments are a **separate evaluation revision** from the six original
baseline/OpenCode arms and their [August 4 results](scores.md). Judging,
reasoning configurations, task anonymization and rubric revisions differ.
Do not merge them into one common leaderboard or treat current mutable rubrics
as a frozen record of every historical evaluation. Uncommitted rubric edits
are not included in this publication.

Raw event logs, vote caches, working directories, duplicate submission-side
scores and later single-judge diagnostic runs are excluded. Source and licence
provenance for the cases remains in their task records. The Second State
Examination runs are not part of this release.

## Verify the published artifacts

From the repository root, verify the copied artifacts and summary CSV:

```bash
shasum -a 256 -c studies/de-core-45/codex-artifacts.sha256
```

The checksum list covers 638 copied files plus the derived CSV. It verifies
file integrity, not the legal correctness of the judgments. This release
supports inspection and recomputation of the reported aggregates; recreating
historical judging also requires its corresponding rubric/prompt state.
