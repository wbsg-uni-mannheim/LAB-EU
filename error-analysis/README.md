# Error analysis of LLM agents drafting German legal assessments (LAB-EU)

Status 03.10.2026. The annotation of all content FAILs by two independent AI annotators according to the current error classes (`error-classes.pdf`) is complete, and the author has decided every content FAIL on which the annotators disagreed. **This folder is being finalised this weekend; a methodology summary follows.**

The error classes (`error-classes.pdf`) and the evidence files are in German, the other files in English.

## Contents

| Entry | What it is |
|---|---|
| `README.md` | This file: contents, status, open points |
| [`methodology.md`](methodology.md) | Procedure and decisions of the error analysis. |
| [`error-classes.pdf`](error-classes.pdf) | The error classes: definitions, boundaries, rules for assignment and counting. |
| [`error-classes-overview.pdf`](error-classes-overview.pdf) | One page: short definition and guiding question per class, the levels of K1, the administrative values and the two flags. `error-classes.pdf` remains authoritative. |
| [`results.pdf`](results.pdf) | Result tables in thesis form: scope, agreement of the annotators, class frequencies by area of law and by arm, the four K1 levels, findings merged into errors, misstated rules and altered facts behind K1. Every figure is computed from the data. |
| [`learnings.md`](learnings.md) | Learnings from the error analysis (in German): eight findings with examples and possible levers for the targeted improvement. |
| [`assignments.csv`](assignments.csv) | Primary data. One line per content FAIL (arm and criterion), with both annotators' assignments. Columns below. |
| [`evidence/`](evidence/README.md) | One file per case. For every content FAIL the criterion text, both assignments with reasoning, confidence and flags, the author's decision with its justification where the annotators disagreed, and links to case facts, model solution, rubric and answer file in LAB-EU at a fixed commit, down to the cited lines. |
| [`legal-review/`](legal-review/README.md) | Review form for a legal expert: examples per class and boundary cases, with full texts for reference. |

**What the tables count.** Every line of `assignments.csv` is one content FAIL with an assigned class, called a finding. Most tables count findings, not errors: one missing part of an answer can produce several findings, because several criteria capture the same gap. `results.pdf`, Table 6, merges such findings into errors: a finding that an annotator flagged as a consequence of another error finding of the same answer („Folgefehler von“) counts only at its origin. Where only one annotator set the flag (147 content FAILs), the author decided by the rule of the error classes (column `Folgefehler_final`).

## Status of the data

- 30 cases (15 public law, 15 civil law), eight arms, 3,444 content FAILs, each assigned independently by two AI annotators (Claude and Codex).
- The annotators disagreed on 693 content FAILs: 217 on the class (K1a to K1d merged) and 476 that agree on K1 and differ only in its level. The author decided all of them (column `Entscheidung_Autor`, justification in `evidence/`). During this step three clarifications were added to the error classes: the other solution path, K4 only if the criterion fails because of the deviating fact, and K6 against OK.
- Each content FAIL gets one class, the first that applies in the order of checks. A second error at the same place is only mentioned in the reasoning of Claude or Codex (`Begründung_Claude`, `Begründung_Codex`). For K1 the annotators additionally recorded whether a misstated rule (K3) or an altered fact (K4) stands at the same place (`Zusatzbefund_*`, counted in `results.pdf`). For the other classes this was not asked.
- Observations on PASS ratings and outside the criteria are not part of this folder.

## `assignments.csv`

Semicolon as separator, one header line, 3,444 data lines, 26 columns, column names in German. Class frequencies in `results.pdf` count `Klasse_final`, the K1 level table counts `Stufe_final`, the error table uses `Folgefehler_final`.

| Column | Meaning |
|---|---|
| `Fall` | Case identifier, `OER` public law, `ZR` civil law. Titles in `evidence/README.md` |
| `Rechtsgebiet` | `ÖR` or `ZR` |
| `Arm` | `SB` Sol baseline, `SA` Sol agent, `TB` Terra baseline, `TA` Terra agent, `DB` DeepSeek baseline, `DA` DeepSeek agent, `CN` Codex without web, `CW` Codex with web |
| `Kriterium` | Criterion identifier in the case rubric |
| `Kritikalität` | Criticality of the criterion in the rubric, 1 to 3 stars |
| `Funktion` | Function tag of the criterion in the rubric |
| `Klasse_Claude`, `Klasse_Codex` | Class at annotation time: K1 to K5, K7, OK, R or S (K1 without its level). Here and in the reasonings, K7 is today's K6 (designation missing). K6 here was self-contradiction, a class that was dropped: its three findings also met K2 or K3, which take precedence, and were assigned there by the author (`Entscheidung_Autor`). The reasoning may say „Normbeleg“ for what the error classes call „Normzitat“ |
| `Einig` | `ja` if both annotators chose the same class |
| `Stufe_Claude`, `Stufe_Codex` | Level within K1 (K1a to K1d), empty for other classes |
| `Einig_fein` | `ja` if both chose the same class and, for K1, the same level |
| `Begründung_Claude`, `Begründung_Codex` | Reasoning with line numbers of the answer |
| `Sicherheit_Claude`, `Sicherheit_Codex` | Stated confidence: hoch, mittel, niedrig. Not used in the analysis |
| `Vermerk_Claude`, `Vermerk_Codex` | Rubric flag: the concrete legal question if the rubric requirement is doubtful. Does not change the class |
| `Zusatzbefund_Claude`, `Zusatzbefund_Codex` | For content FAILs assigned to K1: whether a misstated rule (K3), an altered fact (K4) or both additionally stand at the same place, else `nein`. Empty for other classes |
| `Entscheidung_Autor` | The author's decision on a contested content FAIL, and on the three findings of the dropped class self-contradiction: the class, for K1 with its level (for example `K1b`). Empty where both annotators agree otherwise |
| `Klasse_final` | Class that enters the frequencies (K1 to K6, OK): the author's decision, else the unanimous class, else empty |
| `Stufe_final` | K1 level that enters the level table: the author's decision, else the unanimous level, else empty |
| `Folgefehler_Claude`, `Folgefehler_Codex` | Origin criterion if the annotator flagged the finding as a consequence of another error finding of the same answer („Folgefehler von“, taken from the reasoning or the flag), else empty. Only origins that are themselves content FAILs of the same answer with an error class are listed |
| `Folgefehler_final` | Origin used for the error count: the annotators' common flag, or the author's decision where only one annotator set it. Empty if the finding counts as an error of its own |

Links in `evidence/` point to the private repository `wbsg-uni-mannheim/LAB-EU` at commit `787163a4e06b651545ae73ec54ce7e984624f8c1` and work only with access to it.

## Open points

### To be clarified

Rules that are applied in the data and should be confirmed with the supervisors, and one choice still to be made.

1. **One class per finding.** The order of checks records only the primary error at a place. A subordinate error (for example a misstated rule behind missing content) is named in the reasoning but not counted; `results.pdf` measures what this hides for K3 and K4. The alternative would be to record several classes per finding.
2. **Error count and Folgefehler.** Findings that capture the same gap are merged: one wholly missing part of a task is one error, and dependent criteria carry the flag "Folgefehler von". This also decides how chains such as a misstated rule followed by misapplied facts are counted. Two readings of this rule were applied and should be confirmed: a claim or examination that is only named or answered with a blanket sentence counts as wholly missing, and the same missing statement required at two places of the answer counts as one error. Both rules are defined in `error-classes.pdf`, Auswertungsregeln.
3. **Rubric flags.** Both annotators flagged a large share of the content FAILs as "rubric requirement doubtful" (`Vermerk_*`). How these flags are used, and whether they are set too liberally, is to be decided.

### Still to do

1. **Legal review.** A legal expert reviews examples per class and boundary cases, to check the definitions and boundaries and to assess the weight of the errors, and potentially the list of rubric flags. The material is in `legal-review/`.
2. **Criminal law.** The 15 criminal law cases of the de-core-45 study may be added. Their rubrics and ratings are complete. Whether the error classes fit them unchanged is to be tested.
3. **PASS ratings.** A criterion can be marked as met although the required content is missing. Depending on the time available, such findings may be examined in more detail and reported separately. They are not part of the error counts so far.
4. **Style criteria.** The judges also rated the legal style (Gutachtenstil) separately from the content. These ratings are not part of the analysis so far. Whether they are examined is open.
