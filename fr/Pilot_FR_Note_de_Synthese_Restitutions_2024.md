# French pilot — task 2: the *note de synthèse* (the exercise with no German equivalent)

*Lukas Rass-Masson (UT Capitole / AI-PILoT Chair). Second worked pilot task, built on the real 2024 CRFPA note de synthèse (theme « Les restitutions »). Companion to the cas pratique pilot and the JSON task file `pilot_fr_crfpa_note_de_synthese_2024.json`.*

---

## 1. Why this task earns its place in the benchmark

The *note de synthèse* is the signature French exercise — 5 hours, **coefficient 3** (the highest-weighted CRFPA épreuve) — and it has **no German equivalent**. It is not a legal-reasoning task: the candidate receives a documentary dossier and must produce a **strictly objective synthesis in ≤ 4 pages, using only the information in the dossier**. That makes it three things at once for the benchmark:

1. **A long-context test** — 18 heterogeneous documents (statutes, case law, doctrine, parliamentary texts, press) that must be read, related, and compressed.
2. **A faithfulness / anti-hallucination probe** — the candidate is *penalised for adding any outside knowledge*. A rubric that penalises any statement not traceable to the dossier turns the exercise into a direct measurement of exactly what legal agents are known to fail at: staying grounded and not importing plausible-but-ungrounded law. This is a distinctive research contribution — no German cas/Gutachten format measures it.
3. **A different rubric schema** — it is graded by *dimensions* (structure, coverage, objectivity, fidelity, reformulation, form), not against a single model answer. This is the concrete argument that `exercise_type` must drive different rubric schemas in the harness.

The theme, « **Les restitutions** », is deliberately cross-domain: it spans civil-law restitutions (anéantissement du contrat, indu, possession), « biens mal acquis », spoliated cultural goods and human remains, penal confiscation, ECHR and commercial law — so it also exercises the agent's ability to synthesise *across* fields.

## 2. The task

**Source:** CNB, session 2024, épreuve de note de synthèse (24CRFPA-NS1), public. **Consigne (official):** synthèse objective ≤ 4 pages ; plan apparent recommandé (titres concis) ; **seules les informations du dossier peuvent être utilisées** ; référence aux numéros de documents recommandée ; brève introduction recommandée ; pas de conclusion nécessaire ; qualité rédactionnelle évaluée. **Dossier:** 18 documents (list in the JSON task file; full text in the CNB PDF).

## 3. Reference structure (idées-forces + admissible plans)

*For a note de synthèse the "ground truth" is a set of idées-forces to be captured and related, plus one of several admissible plans — not a single model text.*

**Idées-forces the dossier supports** (each tied to its documents, to be validated against the dossier/grille):

- **Une notion polysémique et transversale.** « Restitution » désigne des réalités hétérogènes : restitutions consécutives à l'anéantissement d'un contrat (DOC 2, art. 1352 s.), répétition de l'indu (DOC 15, art. 1302-1), restitution des fruits et rapports possesseur/propriétaire (DOC 16, art. 549 ; DOC 12), restitution-sanction en droit commercial (DOC 9, art. L. 442-4 ; DOC 4 ; DOC 10), restitution pénale / confiscation (DOC 6 ; DOC 7, art. 41-1 CPP), et restitutions « mémorielles » ou diplomatiques (restes humains DOC 1 ; biens culturels spoliés 1933-1945 DOC 5 ; biens culturels pillés durant la colonisation DOC 14 ; biens mal acquis DOC 3, DOC 11).
- **Des fondements pluriels.** Anéantissement rétroactif de l'acte ; enrichissement injustifié / indu ; propriété et possession ; sanction ; impératifs de politique publique et de justice historique.
- **Des régimes techniques précis.** Étendue des restitutions (valeur, fruits, plus-values et dégradations) selon la bonne ou mauvaise foi (DOC 2, DOC 16) ; modalités procédurales d'exécution (DOC 13) ; articulation avec la CEDH (DOC 8, protection des biens / procès équitable).
- **Une tension structurante.** Restitution comme **mécanisme juridique** (rétablir un équilibre patrimonial entre parties) vs restitution comme **enjeu politique et éthique** (réparer des spoliations, moraliser la vie publique, restituer un patrimoine), cette seconde dimension appelant souvent des **lois spéciales** dérogeant à l'inaliénabilité des collections publiques (DOC 1, DOC 5).

**Admissible plans (thèses défendables — do not privilege one):**
- *Plan A — fondements / régime :* I. La diversité des fondements de la restitution ; II. La diversité des régimes et effets.
- *Plan B — fonctions :* I. La restitution, instrument de rétablissement patrimonial (droit privé) ; II. La restitution, instrument de justice et de politique publique (biens culturels, biens mal acquis, restes humains).
- *Plan C — droit commun / droits spéciaux :* I. Un droit commun des restitutions (civil) ; II. Des régimes spéciaux dérogatoires (pénal, commercial, patrimonial/mémoriel, européen).

## 4. Weighted rubric (20 points) — dimensional, coverage-based, faithfulness-aware

*Distinct from the cas pratique rubric: scored by dimension + idée-force coverage, with an explicit faithfulness penalty. Weights map to the note de synthèse's own grading conventions.*

### A. Structure / plan apparent — 4 pts
- **S1 [E]** Plan apparent avec titres concis et **deux parties équilibrées**, annoncées en introduction.
- **S2 [S]** Brève **introduction** cernant le sujet et annonçant le plan ; pas de conclusion imposée. *(any of Plans A/B/C admissible — [thèse défendable])*

### B. Exhaustivité / couverture — 6 pts
- **C1 [E]** Couvre le **droit privé des restitutions** : anéantissement du contrat (DOC 2), indu (DOC 15), fruits/possession (DOC 16, DOC 12).
- **C2 [E]** Couvre la dimension **mémorielle / politique** : restes humains (DOC 1), biens culturels spoliés (DOC 5) et pillés en contexte colonial (DOC 14), biens mal acquis (DOC 3, DOC 11).
- **C3 [S]** Couvre les **régimes spéciaux** pénal (DOC 6, DOC 7), commercial (DOC 9, DOC 4, DOC 10) et **procédural** (DOC 13).
- **C4 [S]** Intègre la dimension **européenne** (DOC 8, CEDH).
- **C5 [A]** **Exploite l'ensemble** des 18 documents sans oubli majeur ni document « oublié ».

### C. Objectivité & neutralité — 3 pts
- **O1 [E]** **Aucune opinion personnelle** ni prise de position ; ton neutre.
- **O2 [S]** Restitue fidèlement des positions contrastées (ex. débats sur les biens culturels) sans les trancher.

### D. Fidélité au dossier / anti-hallucination — 3 pts *(the distinctive criterion)*
- **F1 [E]** **N'utilise que des informations du dossier** : aucun apport de connaissance juridique extérieure. *Toute affirmation non rattachable à un document est signalée et pénalisée.*
- **F2 [E]** **Aucun contresens** ni attribution erronée d'une idée à un document (référence DOC n exacte).

### E. Reformulation / synthèse — 2 pts
- **R1 [S]** **Reformule** (pas de copier-coller de passages) et **met en relation** les documents entre eux — une synthèse, non un catalogue document par document.

### F. Forme / langue / format — 2 pts
- **M1 [E]** Respecte la **limite de 4 pages** ; langue correcte (orthographe, syntaxe, style, lisibilité).

*Scoring: sum the weighted points; report the six dimension sub-scores separately (as in the German three-dimension redesign, extended). The **faithfulness sub-score (D)** is the headline metric for the anti-hallucination study. Mark the plan chosen and do not penalise for not adopting another admissible plan.*

## 5. How to score synthesis automatically (note for Aaron/Mannheim)

The coverage criteria (C1–C5) are LAB-friendly atomic checks ("captures idée-force X, grounded in DOC n"). The **faithfulness dimension inverts the usual judge prompt**: instead of "is criterion present?", the judge is asked "list every assertion in the note **not** supported by the dossier" — each unsupported assertion is a penalty. That gives a clean, quantifiable hallucination rate per agent, comparable across jurisdictions. This is the piece the German pipeline cannot produce, and a strong candidate for a joint paper.

## 6. Licensing caveat — this is where the open-data gap bites hardest

Unlike the cas pratique (sujet = public statutes + facts), the note de synthèse **dossier is a compilation of third-party copyrighted works** (Le Monde, RFI, Dalloz Hypercours, annotated case law). Redistributing the dossier as open benchmark data is **not** straightforward. Options to raise Friday:

1. Use the CNB dossier under a **research/exam-reuse arrangement** (the licensing action item, via the IEJ/CNB) — not open redistribution.
2. **Reconstruct dossiers from open sources only** — Légifrance texts (open) + Judilibre case law (open) + public parliamentary documents (open) — omitting paywalled press/doctrine. Fully open, benchmark-redistributable, and a natural AI-PILoT deliverable (a « French OpenRewi » for note de synthèse dossiers).
3. Keep the dossier **behind access control** (password/CAPTCHA) as the German team already plans for leakage, which also mitigates the copyright exposure.

Recommended: build the **first pilot with the real CNB dossier under arrangement**, and in parallel produce **one fully open reconstructed dossier** to prove the redistributable path.

## 7. Integration & next steps

- **Harness:** same LAB task file, with `exercise_type: note_de_synthese` in the `jurisdiction_profile` selecting the dimensional rubric schema (distinct from the cas pratique schema).
- **Smoke test:** run one agent over the dossier; score coverage + the faithfulness inversion; eyeball whether the 4-page limit and objectivity hold.
- **Action items:** (Lukas) CNB/IEJ arrangement for the dossier + confirm official grille; (Toulouse jurists) validate the idées-forces and admissible plans; (Mannheim) add `exercise_type`-driven rubric selection and the faithfulness-inversion judge prompt.
