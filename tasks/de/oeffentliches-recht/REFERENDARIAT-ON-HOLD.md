# Referendariat cases: on hold, and how to get them back

`tasks/de/oeffentliches-recht/referendariat/` is not tracked. All 25 cases carry
`"license": "Private, need to obtain license. license type pending."` and no
`ip_cleared` flag, so they stay out of the repository until the licence is
settled. A repository-wide scan on 2026-08-21 found no other task in that state:
278 tasks are CC BY, these 25 were the only pending ones.

Nothing was lost. The files are still on disk, every one of them is in this
repository's history, and their home repository holds them too.

## Their actual home

<https://github.com/wbsg-uni-mannheim/LAB-DE-UrhG-60d> (private) is where these
cases live. Its description states the purpose: "cases and solutions that we can
use under §60d UrhG but which we cannot republish due to license restrictions".
LAB-EU imported them from there on 2026-07-21; see
`tasks/de/provenance/lab-de-urhg-60d/`.

On 2026-08-21 the derived rubrics and the corrections made here were pushed back
to that repository on the branch `feat/rubrics-and-case-corrections` (45 rubric
files, 17 corrected case files). So the licence-restricted material and
everything derived from it now sit together in the repository designed for it.

## Where they are

| Commit | Contents |
|---|---|
| `c5aea86` | **237 files — the complete set.** Sachverhalte, Anlagen, Musterlösungen (`evals/*-sut.md`), footnote mappings, `task.json`, plus the 45 frozen and generated rubrics. |
| `5aceffa` | 192 files: the same case materials without the rubrics. |
| `38256ef` | The commit that removed them from tracking. |

Verified on 2026-08-21: the 237 files in `c5aea86` are exactly the 237 files on
disk outside `.rubric-cache/`. Nothing exists only locally. The ~2,600 files
under `.rubric-cache/` are rubric generation intermediates and were never
tracked by design (`.gitignore`).

## Getting them back

Restore into the working tree without re-adding them to git:

```bash
git archive c5aea86 tasks/de/oeffentliches-recht/referendariat/ | tar -x
```

Or restore and stage in one step. The explicit pathspec overrides `.gitignore`,
so this works even while the ignore rule is in place:

```bash
git checkout c5aea86 -- tasks/de/oeffentliches-recht/referendariat/
```

To undo that staging while keeping the files:

```bash
git reset HEAD -- tasks/de/oeffentliches-recht/referendariat/
```

## Once the licence is settled

1. Delete the `/tasks/de/oeffentliches-recht/referendariat/` line from
   `.gitignore`, and the second-exam block below it if those artefacts should
   return too (`tasksets/de-second-exam-*.jsonl`,
   `studies/de-second-exam-15/`, `tests/test_second_exam_taskset.py`,
   `PLAN_RUBRIKENGENERIERUNG_ZWEITES_STAATSEXAMEN.md`).
2. Set the real licence and `ip_cleared` in each `task.json`, the way the
   de-core-45 cases record theirs.
3. `git add` the directory and commit.
4. Delete this file.

## Two things to keep in mind

**The working copy is no longer protected by git.** Because the directory is
untracked and ignored, `git status` will not warn you about changes to it and
nothing is pushed anywhere. If the machine is lost, only what is in history
survives — that is the state of `c5aea86`, not any later edit. Keep a separate
backup if you keep working on these cases.

**Pulling deletes them on other checkouts.** Anyone who pulls `38256ef` loses
the directory from their working tree, including the cluster at
`/work/aasteine/LAB-EU`. Copy it aside before pulling, then copy it back.

**The blobs stay in history.** Untracking removes them from future checkouts,
not from the repository. Anyone with access can still read them through the
commits above. If the licence question ever requires them to be genuinely gone,
that needs a history rewrite (`git filter-repo`) and a force push, which
invalidates every existing clone.
