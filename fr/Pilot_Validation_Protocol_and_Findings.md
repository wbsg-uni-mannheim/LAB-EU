# Validation protocol for benchmark pilot tasks — and findings from the two 2024 pilots

*Lukas Rass-Masson (UT Capitole / AI-PILoT Chair). A reusable checklist for certifying any French pilot task, and the results of applying it to the two 2024 CRFPA pilots (droit des obligations; note de synthèse « Les restitutions »).*

---

## Part A — Reusable validation protocol

Apply to every task before it enters the benchmark. Ordered cheapest → most authoritative; a task is **certified** only after Layer 2.

**Layer 0 — Source fidelity.** Confirm the sujet text matches the CNB PDF verbatim and the barème is transcribed exactly. *(Cheap, do first.)*

**Layer 1 — Legal cross-check (two independent references).**
- Compare the reference solution against **published corrigés** (Dalloz, Objectif Barreau, Cap'Barreau, doc-du-juriste) and a **manuel**. Flag every issue they raise that the solution omits, and every citation that diverges.
- Spot-check article numbers and arrêts against **Légifrance / Judilibre** (primary sources).
- *Pass criterion:* no missing lead issue; no wrong citation.

**Layer 2 — Expert sign-off (the step that confers validity).** The core-team jurist for the matière reads the solution **and** the rubric and signs off. Until then the task is a *draft*, not ground truth. This is the "humans own the standard" principle operationalised.

**Layer 3 — Rubric-quality checks.**
- *Weighting:* does the barème mapping put the Schwerpunkt above procedural/citation points?
- *Alternative paths:* feed a solution taking each defensible fork and confirm the rubric/judge does **not** penalise it.
- *(Note de synthèse)* *Faithfulness:* feed a synthesis containing one true-but-outside-the-dossier point and confirm the fidelity criterion flags it.

**Layer 4 — Reliability & difficulty (empirical).**
- *Inter-rater:* 2–3 graders score the same output independently → agreement (kappa). Low = rewrite ambiguous criteria.
- *Human-vs-judge:* run the LLM-as-judge vs the human graders → correlation. This is the number that licenses the automated score.
- *Difficulty/leakage:* run several agents; meaningful spread and sub-30 % on the hard task = discriminating; probe whether models already "know" the public corrigé (→ move to fresh sujets).

**Layer 5 — Technical.** End-to-end smoke test in the harness (`jurisdiction_profile: FR`, stages 2–5) produces a scored output.

**Authoritative anchor (parallel action):** obtain the **official CNB grille de notation** via the IEJ; it settles content *and* weighting and supersedes any reconstructed rubric.

---

## Part B — Findings from applying Layers 0–1 to the two pilots

### Task 1 — Droit des obligations (cas pratique)

**Confirmed against the published corrigé** (doc-du-juriste, tutor-written): the whole spine of my reference solution matches — obligation de moyens/résultat; résolution unilatérale (art. 1224/1226) with gravité + mise en demeure/urgence; effets (art. 1229, restitution partielle vs intégrale); the **location financière / ensemble interdépendant** analysis (art. 1186–1187) for SOFISPE; and, in Part II, the fait des choses / garde / faute de la victime / minorité indifférente (Ass. plén. 9 mai 1984) chain.

**One real gap found and fixed** — and this is the value of the exercise:

- **Part II omitted art. 1244 C. civ. (responsabilité du fait des bâtiments en ruine).** For a *garage roof collapsing through poor maintenance*, the 1242-vs-1244 arbitrage is arguably the central expected issue, and my draft went straight to 1242. **Corrected:** added the 1244 régime spécial as the lead step (new criterion **R15 [E]**).
- **Part II over-asserted the *rôle actif*.** The corrigé flags that if the tiles gave way *only under the victim's weight*, the rôle actif fails (Cass. 2e civ., 25 mai 2022, n° 20-17123). **Corrected:** R18 reframed as a genuine **[thèse défendable]** (anormalité established *or* rôle actif excluded).
- **Part I.A enrichments:** added préjudice **prévisible** (art. 1231-3) and the **fait du tiers / force majeure** exoneration (art. 1218) — the cyberattack is hard to call unforeseeable in a cybersecurity contract.
- **Part I.B reframing:** my "divisibilité du bail" alternative collided with the rule that divisibility clauses are *réputées non écrites* in location financière. **Corrected:** the defensible fork is now the **scope of the ensemble** (does the Services contract belong to the same operation as the matériel financing?), and I added the **délictuel** route for SOFISPE as a third party suing AlphaDot (jurispr. *Bootshop*, Ass. plén. 6 oct. 2006; Com. 3 juill. 2024, n° 21-14947, on opposability of clauses to third parties).

*Net:* the cas pratique pilot is now aligned with the published corrigé. It still needs **Layer 2 (expert sign-off)** — Zoé Jacquemin for obligations — before it is certified.

### Task 2 — Note de synthèse (« Les restitutions »)

**Well validated.** The published corrigé's plan (I. L'encadrement de la restitution — reconnaissance positive / mise en œuvre jurisprudentielle ; II. Les fondements — atteinte à la personne humaine / biens mal acquis ou spoliés) maps almost exactly onto the **idées-forces** and the **admissible plans** in the pilot. No missing major theme; my coverage list (droit privé, mémoriel/politique, pénal, commercial, procédural, européen) is confirmed.

**Two minor refinements to fold in:**
- Sharpen two idées-forces that the corrigé names explicitly: **DOC 18** (lambeau de peau tatoué; cause immorale/illicite; dignité) and **DOC 17** (joyaux de fiançailles; restitution en droit de la famille).
- **DOC 8 (CEDH Blake)** — my structure flags a European dimension; the published corrigé *omits* doc 8. This is itself a useful data point: two competent corrigés cover different subsets, which confirms the design choice to score the note de synthèse by **idée-force coverage**, not against a single model text. It also means the faithfulness/coverage rubric must be validated against the **official grille**, which lists the expected idées-forces.

*Net:* the note de synthèse pilot needs no substantive correction; fold in the two refinements and take it through Layer 2.

---

## Bottom line for Friday

The double-check did its job: it confirmed both pilots are on solid ground **and** caught a genuine omission (art. 1244) that a single AI pass missed — which is precisely the argument for the human-validation layer the benchmark is built around. The pilots are now internally consistent with published corrigés; the remaining steps before either is *certified* are the **official CNB grille** (authoritative anchor) and **Toulouse expert sign-off** (Layer 2).
