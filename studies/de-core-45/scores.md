# Final historical scores and criterion-level error analysis

The six original study arms' `runs/<arm>/<run-id>/tasks/<task>/scores.json`
now reproduce `runs/de-core-45-final.csv`, the published August 4, 2026 table.
There are 269 scored submissions and one `keine Abgabe` row: the DeepSeek agent
did not submit `anfanger-innenhausarbeit-bundeszwang-und-rededrang` because of a
provider content filter. That case has no `scores.json`; it is not a zero score.

## Which fields to use

- `criteria_results[]`: final content verdict per criterion; select
  `verdict == "fail"` for content error analysis.
- `style_results[]`: separate Gutachtenstil verdicts for eligible criteria.
- Each result includes `id`, `title`, `verdict`, `reasoning`, `evidence`,
  `vote_counts`, `tiebreak_used`, and `votes[]`.
- `votes[]` preserves each participating judge's verdict, reasoning, evidence,
  component checks, judge identity, and primary/tiebreak role. The result-level
  reasoning is taken from a vote supporting the final verdict; it is not a
  separate committee-written explanation. Read `votes[]` to inspect disagreements.
- `content_score` and `style_score` contain the aggregates used by the CSV.

All 10,790 content and 8,682 style results are decided and have result-level
reasoning. One individual vote lacks its reasoning text: Luna's content vote
on C-042 of `original-examensklausur-liebesbeweis-mit-rasanten-folgen-mit-exkurs-zu-paragraph-315d-stgb`
in the DeepSeek agent arm. Its evidence and the other judges' reasons remain
available; the final criterion verdict has a reason. No missing text was invented.

## Provenance and version boundary

The July 31 judging job hit the OpenRouter key limit (HTTP 403) for Gemini.
Many criteria remained unresolved even though jobs exited successfully. Those
old `scores.json` files did not represent the final table and must not be used
for error analysis. They remain in Git history before this publication update.

The August 4 repair read cached Luna and Terra votes, using Gemini to resolve
disagreements, and wrote only the final CSV. On August 21, the cluster checkout
`/work/aasteine/LAB-EU` reconstructed the corresponding score files without new
judge API calls, on branch `fix/de-core-45-score-artifacts` (score commit
`d3bb589`). This publication
copies those 269 score files unchanged. `scored_at` is the reconstruction time.
`judging_pass`, `committee_resolution`, and `rebuilt_from_vote_cache` identify the
evaluation rule and cache sources. Absolute paths refer to the cluster at that
time. The runs' older `judge_config.json` files describe the failed initial job.

This is the **historical August 4 result**, not a re-evaluation against current
rubrics. The August 13 M/H reruns and August 21 Kaufrausch rubric correction are
separate revisions and are not folded into these scores or this CSV.

## Reproduce the CSV without caches or API calls

From the repository root:

```bash
python scripts/build_study_results_csv.py \
  runs/agent-gpt-5.6-sol-high/20260730T221733Z \
  runs/baseline-gpt-5.6-sol-high/20260730T221734Z \
  runs/agent-gpt-5.6-terra-high/20260730T221733Z \
  runs/baseline-gpt-5.6-terra-high/20260730T221744Z \
  runs/agent-deepseek-v4-pro-medium/20260730T214602Z \
  runs/baseline-deepseek-v4-pro/20260730T221734Z \
  --output /tmp/de-core-45-reproduced.csv
cmp runs/de-core-45-final.csv /tmp/de-core-45-reproduced.csv
```

The expected CSV SHA-256 is
`fc68e3ceaee10260e218f78fc7cb9e0a43a1a0d65c3f81a77c593858e1be1fb2`.

## Reconstruct scores from the original caches

`scripts/rebuild_scores_from_vote_cache.py` makes no API calls. Historical
reconstruction requires the August 4 task/rubric/prompt snapshot (cluster base
commit `1f5be8a`), the original submissions, the per-arm `vote-cache/`, and the
additional `runs/recheck-de-core-4-lunaterra/<arm>/vote-cache/`. These caches remain
gitignored. They are not needed to read the published criterion-level scores.

On that historical snapshot, with the reconstruction script available:

```bash
python scripts/rebuild_scores_from_vote_cache.py runs/<arm>/<run-id> \
  --judge-committee configs/judge-committee-professor-pilot.json \
  --primaries luna,terra --tiebreaker gemini-3.6-flash \
  --style-evaluation \
  --extra-cache-dir runs/recheck-de-core-4-lunaterra/<arm>/vote-cache
```

Do not run this command against revised current tasks expecting the historical
table: prompt changes invalidate cache keys and can leave criteria unresolved.
