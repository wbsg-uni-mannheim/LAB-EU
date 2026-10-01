# Error analysis of LLM agents drafting German legal assessments (LAB-EU)

Status 01.10.2026. The annotation of all content FAILs by two independent AI annotators according to the current error classes (`error-classes.pdf`) is complete. Open are the author's decisions on the content FAILs where the annotators disagree (see Open points). **This folder is being finalised and extended over the coming weekend; a methodology summary follows.**

The error classes (`error-classes.pdf`) and the evidence files are in German, the other files in English.

## Contents

| Entry | What it is |
|---|---|
| `README.md` | This file: contents, status, open points |
| Methodology | Procedure and decisions. A summary follows, not included yet. |
| [`error-classes.pdf`](error-classes.pdf) | The error classes: definitions, boundaries, rules for assignment and counting. |
| [`error-classes-overview.pdf`](error-classes-overview.pdf) | One page: short definition and guiding question per class, the levels of K1, the administrative values and the two flags. `error-classes.pdf` remains authoritative. |
| [`results.pdf`](results.pdf) | Result tables in thesis form: scope, agreement of the annotators, class frequencies by area of law and by arm, the four K1 levels, misstated rules and altered facts behind K1. Every figure is computed from the data. |
| [`assignments.csv`](assignments.csv) | Primary data. One line per content FAIL (arm and criterion), with both annotators' assignments. Columns below. |
| [`evidence/`](evidence/README.md) | One file per case. For every content FAIL the criterion text, both assignments with rationale, and links to case facts, model solution, rubric and answer file in LAB-EU at a fixed commit, down to the cited lines. |
| [`legal-review/`](legal-review/README.md) | Placeholder for the material for the legal review. |

**What the tables count.** Every line of `assignments.csv` is one content FAIL with an assigned class, called a finding. The tables count findings, not errors: one missing part of an answer can produce several findings, because several criteria capture the same gap. Error counts, in which such findings are merged, are not formed yet (see Open points).

## Status of the data

- 30 cases (15 public law, 15 civil law), 20 development cases (phase A) and 10 held-out cases (phase B), eight arms, 3,444 content FAILs, each assigned independently by two AI annotators (Claude and Codex). Potentially the 15 criminal law cases of the de-core-45 study will be added to complete the study.
- 693 content FAILs are open because the annotators disagree: 217 on the class (K1a to K1d merged) and 476 that agree on K1 and differ only in its level. Grouped by criterion, that is 157 decisions for the class and 378 including the levels; deciding the levels also settles the class. `evidence/` marks these 693 as *offen*.
- Each content FAIL gets one class, the first that applies in the order of checks. A second error at the same place is only mentioned in the reasoning of Claude or Codex (`Begründung_Claude`, `Begründung_Codex`). For K1 the annotators additionally recorded whether a misstated rule (K3) or an altered fact (K4) stands at the same place (`Zusatzbefund_*`, counted in `results.pdf`, Table 6). For the other classes this was not asked.
- Observations on PASS ratings and outside the criteria are not part of this folder.

## `assignments.csv`

Semicolon as separator, one header line, 3,444 data lines, column names in German. Class frequencies in `results.pdf` count `Klasse_final`, the K1 level table counts `Stufe_final`.

| Column | Meaning |
|---|---|
| `Phase` | `A` development set (20 cases), `B` held-out set (10 cases) |
| `Fall` | Case identifier, `OER` public law, `ZR` civil law. Titles in `evidence/README.md` |
| `Rechtsgebiet` | `ÖR` or `ZR` |
| `Arm` | `SB` Sol baseline, `SA` Sol agent, `TB` Terra baseline, `TA` Terra agent, `DB` DeepSeek baseline, `DA` DeepSeek agent, `CN` Codex without web, `CW` Codex with web |
| `Kriterium` | Criterion identifier in the case rubric |
| `Kritikalität` | Criticality of the criterion in the rubric, 1 to 3 stars |
| `Funktion` | Function tag of the criterion in the rubric |
| `Klasse_Claude`, `Klasse_Codex` | Class: K1 to K7, OK, R or S (K1 without its level). Rationales may say „Normbeleg“ for what the error classes call „Normzitat“ |
| `Einig` | `ja` if both annotators chose the same class |
| `Stufe_Claude`, `Stufe_Codex` | Level within K1 (K1a to K1d), empty for other classes |
| `Einig_fein` | `ja` if both chose the same class and, for K1, the same level |
| `Begründung_Claude`, `Begründung_Codex` | Rationale with line numbers of the answer |
| `Sicherheit_Claude`, `Sicherheit_Codex` | Stated confidence: hoch, mittel, niedrig |
| `Vermerk_Claude`, `Vermerk_Codex` | Rubric flag: the concrete legal question if the rubric requirement is doubtful. Does not change the class |
| `Zusatzbefund_Claude`, `Zusatzbefund_Codex` | For content FAILs assigned to K1: whether a misstated rule (K3), an altered fact (K4) or both additionally stand at the same place, else `nein`. Empty for other classes |
| `Entscheidung_Autor` | The author's decision on a contested content FAIL: the class, for K1 with its level (for example `K1b`). Empty until decided |
| `Klasse_final` | Class that enters the frequencies: the author's decision, else the unanimous class, else empty |
| `Stufe_final` | K1 level that enters the level table: the author's decision, else the unanimous level, else empty |

Links in `evidence/` point to the private repository `wbsg-uni-mannheim/LAB-EU` at commit `787163a4e06b651545ae73ec54ce7e984624f8c1` and work only with access to it.

## Open points

1. **Author's decisions.** The 217 content FAILs on which the annotators disagree on the class (693 including the K1 levels) are decided by the author. Until then they are excluded from the frequencies and the column `Entscheidung_Autor` is empty.
2. **Error counts.** Findings that capture the same gap in one answer have to be merged into errors (one wholly missing part of a task is one error). This needs a merging rule and a pass over the answers, both still open. Until then the tables report findings.
3. **Legal review.** Five examples per class for a legal expert, to check the definitions and boundaries and to assess the weight of the errors, and potentially the list of rubric flags. Not built yet.
4. **Rubric flags.** Both annotators flagged a large share of the content FAILs as "rubric requirement doubtful" (`Vermerk_*`). How these flags are used, and whether they are set too liberally, is to be decided.
5. **Counting rules to be confirmed.** Two choices of the error classes affect every count and should be reviewed with the supervisors. First, one class per finding: the order of checks records only the primary error at a place, a subordinate error (for example a misstated rule behind an omission) is named in the rationale but not counted; `results.pdf`, Table 6, measures what this hides for K3 and K4. The alternative would be to record several classes per finding. Second, the error count: findings that capture the same gap are to be merged (one wholly missing part of a task is one error, dependent criteria carry the flag "Folgefehler von"), which also decides how chains such as a misstated rule followed by misapplied facts are counted. Both rules are defined in `error-classes.pdf`, Auswertungsregeln.
