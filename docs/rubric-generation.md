# Rubric Generation for LAB-EU

This note proposes the first LAB-EU approach for turning a human legal solution into Boolean LLM-judge criteria. It is based on the public Harvey LAB design, but adapts it for German law, EU law, and later additional European jurisdiction tracks.

## Harvey LAB Takeaways

Harvey LAB evaluates long-horizon legal-agent work with task-specific rubrics. Each task contains instructions, matter documents, expected deliverables, and inline `criteria` in `task.json`. Each criterion has a short title, a `match_criteria` field, relevant deliverables, and optional source files. The judge sees the task description, scoped agent output, criterion title, and `match_criteria`, then returns a JSON `pass` or `fail` verdict with reasoning.

Useful design choices to reuse:

- Criteria are Boolean and semantic, not keyword or regex checks.
- Each criterion is evaluated independently, usually in a separate judge call.
- Criteria are scoped to one or more deliverable files, so the judge does not inspect unrelated output.
- The final task score is all-pass: `1.0` only if every criterion passes, otherwise `0.0`.
- Criterion pass rate is still recorded as a diagnostic, because it explains near-misses.
- The rubric is the evaluation standard; the judge does not need a separate gold answer at scoring time.
- Good `match_criteria` text uses a `PASS if ... FAIL if ...` shape and names facts, dates, numbers, legal issues, clauses, citations, or drafting moves concretely.

Important caveats for LAB-EU:

- Harvey's rubrics are dense. In a current public clone checked on 2026-06-29, the public task set had 1,749 `task.json` files and 104,467 criteria, with a median of 57 criteria per task. Harvey's docs still describe 1,660 tasks and about 101,000 criteria, while the launch post described more than 1,200 tasks and more than 75,000 criteria. The dataset is moving.
- Dense rubrics make all-pass scores harsh and verifier costs high. For LAB-EU, the generator should choose the number of criteria needed for the specific case instead of enforcing a fixed count.
- Some Harvey criteria are very fact-specific. That works well for synthetic diligence tasks, but German and EU law answers often allow several defensible paths. Our criteria must avoid overfitting to one model answer.
- LLM judges disagree. A LangChain/Harvey verifier study found that even frontier verifier models diverge, and that false passes are the dangerous failure mode for legal evaluation. LAB-EU should calibrate judge prompts for conservative passing.
- A rubric derived from only one human solution can inherit omissions and style bias. Multi-LLM proposal plus human legal review should be part of the authoring workflow.

## Proposed LAB-EU Rubric Lifecycle

Use three rubric states:

1. `evals/loesung.md` or equivalent: human-written solution, retained as authoring evidence.
2. `evals/rubric.generated.json`: machine-generated draft with provenance and unresolved review notes.
3. `evals/rubric.json` or inline `task.json.criteria`: frozen, human-reviewed scoring rubric.

For Harvey compatibility, the frozen rubric can be copied into `task.json.criteria`. During development, keeping generated and reviewed files separate makes audit easier.

## Generation Pipeline

### 1. Inputs

The generator should receive:

- `task.json`
- all task documents
- one or more human solutions
- jurisdiction profile, for example `de`, `eu`, `fr`, or `cross_border`
- expected legal-reasoning style, for example `Gutachtenstil`, `Urteilsstil`, EU proportionality/fundamental-rights analysis, or conflict-of-laws method
- an instruction to choose the final criterion count based on the case, without padding

### 2. Solution Atomization

The first LLM pass should convert the human solution into answer-key atoms. Each atom should be one legally relevant proposition:

- issue or admissibility point
- legal basis or authority
- definition/test
- legally relevant fact
- subsumption/application step
- conclusion, remedy, or procedural consequence
- required citation or document reference
- required structure/style move
- explicit non-issue or exclusion, if the task facts make it important

The atomization output is not yet the rubric. It is a coverage map.

### 3. Multi-LLM Rubric Proposals

Run at least three rubric generators with different roles:

- Doctrine generator: extracts necessary legal issues, rules, and conclusions.
- Fact-grounding generator: checks which factual findings and document references must appear.
- Reviewer/adversary generator: looks for missing criteria, ambiguous criteria, and criteria that would reward a wrong but plausible answer.

Each generator should produce 25-50 candidate criteria before pruning. That gives enough surface area for consensus without forcing all generated candidates into the final rubric.

### 4. Normalize and Merge

A separate merge step should:

- split compound candidates into atomic Boolean checks;
- remove duplicates and near-duplicates;
- rewrite vague criteria into observable checks;
- add `PASS if ... FAIL if ...` language;
- attach deliverables and source files;
- assign criticality;
- keep the final set lean, material, and complete for the case.

Do not average model outputs blindly. Treat agreement across generators as a signal, but let the human reviewer preserve a minority criterion if it captures a material legal point.

### 5. Boolean Audit

Every criterion must pass these checks before human review:

- It can be answered from the agent output alone, with source documents only as context if needed.
- It resolves to exactly `pass` or `fail`.
- It does not require the judge to infer the agent's intent.
- It is not merely "good style", "thoroughness", or "quality" unless rewritten as an observable requirement.
- It tolerates equivalent legal language and citations where legally acceptable.
- It does not require the exact wording or structure of the human solution unless the task specifically tests form.
- It is not a nice-to-have. Under all-pass scoring, every criterion is material.

### 6. Calibration

Before freezing a rubric:

- Score the human solution. It should pass unless the solution is intentionally partial. This works today without extra tooling: `env/bin/python -m evaluation.run <task-dir> <task-dir>/evals/loesung.md` (see scripts/README.md).
- Score one weak baseline answer and one strong LLM answer.
- Inspect all false passes first, then false fails.
- Rewrite criteria that judges apply inconsistently.
- If a criterion cannot be made stable, remove it or move it into a non-scoring reviewer note.

### 7. Freeze

The frozen rubric should include:

- criteria IDs stable within the task;
- source and deliverable scoping;
- jurisdiction and reasoning-style metadata;
- generator provenance;
- reviewer identity or review status;
- rubric version.

## Avoid Fixed Rubric Categories (in Generation)

Do not force generated criteria into a predefined category taxonomy. Even broad labels such as `issue_spotting`, `legal_basis`, or `application` can bias generation toward a particular legal-writing model and away from the structure of the human solution. The generator should instead derive the material checks from the solution itself.

## Post-Hoc Analysis Tags

Categories are still valuable for reporting, so tagging happens in a separate pass after calibration, on the frozen criteria, as non-scoring metadata (`analysis_tags` per criterion). This keeps generation category-free while letting evaluation report pass rates in categories lawyers understand.

Germany has no single official assessment taxonomy for legal exams - grading under the 1981 Noten- und Punkteverordnung is holistic. The two structures every German lawyer knows are used instead:

- `function`: the kind of legal work checked, following the Gutachtenstil steps plus structure and form: `structure`, `legal_basis`, `rule_statement`, `application`, `argumentation`, `conclusion`, `form_citation`. This maps onto the French syllogisme juridique (majeure = rule_statement, mineure = application, conclusion), so the axis is jurisdiction-portable.
- `outline_id` / `station_path`: where the criterion sits in the case's own Prüfungsaufbau. A dedicated `extract_outline` step first freezes the solution's own Gliederung as a tree in `rubric.json` (ids follow the solution's markers: "A", "A.I", "A.I.1", ...; "Ü" is reserved for cross-cutting criteria). The tagger then picks a node id instead of inventing labels; `station_path` (the full label path) is derived from the tree, so labels stay consistent and arbitrarily deep. Solutions without explicit structure get a reconstructed shallow outline marked `derived`.

The same pass also rates each criterion's importance for this case as `criticality` 1-3 (top-level criterion field, not inside `analysis_tags`):

- `3` ergebnistragend: the few points the case is decided by - correct Klageart/Grundlage, the decisive contested points, the final result. Hard budget: ~10-15% of criteria (typically 5-12). Test: missing this single point would make an examiner fail the whole solution.
- `2` wichtig: the default for every real legal step; expected in a solid solution; missing it costs substance but the Gutachten stands.
- `1` eher unwichtig: details, form/citation, bonus knowledge.

Criticality is assigned after calibration on the frozen criteria, so it cannot bias generation. It is currently non-scoring (all-pass stays the headline metric) but is reported everywhere: `breakdown_by_criticality` in `scores.json`, per-criterion stars in `review.md`, and a legend plus per-criterion tier in `rubric-review.md`. Before tagging, the pipeline-internal `criticality` string (`must_pass`/`diagnostic`) is only a keep/drop signal for the pruner; the tag pass overwrites it with the 1-3 tier.

`evaluation.run` aggregates verdicts into `breakdown_by_station`, `breakdown_by_function`, and `breakdown_by_criticality` in `scores.json` whenever the rubric carries tags.

## Suggested Criterion JSON

```json
{
  "id": "C-001",
  "criticality": 3,
  "title": "Identifies the correct action type",
  "match_criteria": "PASS if the answer identifies the claim as a Verpflichtungsklage under Section 42 I Alt. 2 VwGO because J seeks issuance of a deletion order by the authority. FAIL if the answer treats the case primarily as an Anfechtungsklage, Feststellungsklage, or omits the action type.",
  "deliverables": ["fallloesung-sut.md"],
  "sources": ["documents/sachverhalt.md"],
  "derived_from": ["evals/loesung.md"],
  "jurisdiction": "de",
  "reasoning_style": "Gutachtenstil"
}
```

For EU law, the same shape should work:

```json
{
  "id": "C-007",
  "criticality": 2,
  "title": "Applies proportionality in separate steps",
  "match_criteria": "PASS if the answer analyzes suitability, necessity, and proportionality stricto sensu as distinct steps and applies each step to the facts. FAIL if it only states that the measure is proportionate without separate analysis.",
  "deliverables": ["legal-memo.md"],
  "sources": ["documents/facts.md", "documents/eu-law-extracts.md"],
  "derived_from": ["evals/model-solution.md"],
  "jurisdiction": "eu",
  "reasoning_style": "EU_proportionality"
}
```

## Active Prompt Templates

The implementation uses the prompt templates in `prompts/` as the source of truth:

- `prompts/rubric_generation/atomize_solution.system.txt`
- `prompts/rubric_generation/atomize_solution.user.txt`
- `prompts/rubric_generation/generate_candidate_criteria.system.txt`
- `prompts/rubric_generation/generate_candidate_criteria.user.txt`
- `prompts/rubric_generation/roles/doctrine.txt`
- `prompts/rubric_generation/roles/fact_grounding.txt`
- `prompts/rubric_generation/roles/adversary.txt`
- `prompts/rubric_generation/prune_rubric.system.txt`
- `prompts/rubric_generation/prune_rubric.user.txt`
- `prompts/rubric_generation/refine_rubric.system.txt`
- `prompts/rubric_generation/refine_rubric.user.txt`
- `prompts/evaluation/rubric_criterion.txt`
- `prompts/harness/solve_task.txt`
- `prompts/harness/solve_task_baseline.txt`

Legal reviewers should edit those files directly rather than copying prompt text from this design document.

Implementation status: the multi-role proposal step (section 3) runs as three
parallel candidate calls with the role prompts above, and the calibration step
(section 6) is built into `scripts/generate_rubric.py` as a judge/refine loop
against the gold solution with majority voting. Criteria that fail calibration
never reach `evals/rubric.json`. See `scripts/README.md` for the flags.

## Recommended First Iteration

For the first LAB-EU implementation, build only the authoring path:

1. Add a schema for `evals/rubric.generated.json` and `evals/rubric.json`.
2. Add a command such as `python -m evaluation.generate_rubric --task <task-id> --models <m1,m2,m3>`.
3. Implement atomize, generate, merge, Boolean-audit, and export steps.
4. Keep scoring simple and Harvey-like: one criterion, one judge call, `pass` or `fail`.
5. Report both all-pass and criterion pass rate.
6. Review the first 5-10 tasks manually before scaling.

The first milestone should not try to solve model training, benchmark leakage, or full multi-agent evaluation. It should produce reliable, inspectable rubrics from human solutions.

The implementation keeps active prompt templates in `prompts/` so legal reviewers can review wording independently of the Python code.

## Open Design Decisions

- Whether the frozen rubric lives only in `task.json.criteria` or in `evals/rubric.json` with a build step that injects criteria into `task.json`.
- Whether all criteria are equally weighted forever, or whether LAB-EU keeps all-pass for headline scoring and adds separate diagnostic reports later.
- Which judge models are accepted for German and EU law, and whether each jurisdiction profile requires a different judge-model configuration.
- How to handle partially correct alternative legal answers, especially in EU and international-law tasks where the ground truth may be less determinate.
- Whether generated rubrics should be public with the task or held out to reduce leakage.

## References Checked

- Harvey LAB GitHub repository: https://github.com/harveyai/harvey-labs
- Harvey LAB evaluation methodology: https://github.com/harveyai/harvey-labs/blob/main/docs/eval-strategies.md
- Harvey LAB launch post: https://www.harvey.ai/blog/introducing-harveys-legal-agent-benchmark
- LangChain/Harvey verifier study: https://www.langchain.com/blog/designing-efficient-verifiers-for-legal-agents
