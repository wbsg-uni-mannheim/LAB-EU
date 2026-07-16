# Review — German benchmark example (Verpflichtungsklage / Schmähkritik case)

*Lukas Rass-Masson, for Christian Bizer / Aaron Steiner. Review of the OpenRewi Verwaltungsrecht case, its 88 LLM-generated rubrics, and the two graded solutions (SUT deepseek-v4 81%, baseline single-call 72%).*

---

## Headline finding

**The SUT solution reached the *opposite* legal result from the Musterlösung — Klage zulässig but *unbegründet* (no Ermessensreduzierung auf Null, no Bescheidungsanspruch) — and still scored 81 %.** A solution that gets the ultimate answer wrong, partly via a real doctrinal error, scores 81 % because it passed the many procedural atomic points (Zulässigkeit 23/25). This is the clearest possible demonstration that unweighted atomic rubrics do not track legal quality, and it validates every one of the Doktorandin's four proposals.

## 1. Musterlösung — legally sound

Correct on all the hard points: § 40 I 1 VwGO / modifizierte Subjektstheorie; Versagungsgegenklage; Schutznormtheorie; **§ 60 II 4 VwGO** (Wiedereinsetzung without a formal Antrag through timely Nachholung); notwendige Beiladung § 65 II; § 59 III RStV blocked by the § 54 exclusion → fallback to **§ 9 I POG via § 9 II**; § 1 III POG subsidiarity overcome by the objective Strafgesetz-Verstoß; narrow Schmähkritik definition; Menschenwürde for "nicht lebenswert"; Ermessensreduzierung auf Null (with a.A. flagged). No substantive errors.

*One design note (not an error):* the case runs on the **RStV**, replaced by the **Medienstaatsvertrag (MStV)** in Nov 2020. Correct for a 2019 fact pattern, but for agents with web access, build in date-anchoring or accept MStV-equivalent citations, or the "current law" will look like a mismatch.

## 2. The 88 rubrics — high quality, with two notes

Atomic, well-anchored (clean ERFÜLLT / NICHT-ERFÜLLT poles), and — better than flat Harvey LAB — they **already encode alternative paths** for the genuinely contested points (C-021, C-032, C-037, C-082, C-087, C-088 carry review notes requiring the a.A. to be named and carried through consistently). Good work.

- *Nits:* C-039 is appended out of order after C-088; the "Gesamtfeedback" field is left blank.
- *Substantive concern:* C-049/C-050/C-051/C-053 hard-code the Musterlösung's **Schmähkritik shortcut**. A doctrinally *superior* answer that declines the shortcut and runs a full Einzelfallabwägung (reaching the same illegality via Menschenwürde + the knowingly untrue Tatsachenbehauptung) would be under-credited. Recommend treating "Schmähkritik **or** full Abwägung reaching the same result" as alternative-satisfying, exactly like the other a.A. notes.

## 3. The judge's 17 "FALSE" calls fall into three very different buckets

**(a) Genuine substantive errors — judge correct, high value.**
- **C-042 / C-043:** the SUT held that § 1 III POG *bars* the authority because a civil-law route exists, and treated the Antrags-/Privatklagedelikt character as a block. Settled doctrine (and the Musterlösung) say the **objective Strafgesetz-Verstoß overrides** the private-rights subsidiarity. This is the real error that produced its wrong "unbegründet" result.
- **C-022** (named the ADD, not the Land, as Beklagter), **C-026** (omitted the notwendige Beiladung of X), **C-035** (missed § 9 II POG). Legitimate misses.

**(b) Alternative-path penalties — not real errors.** C-066, C-072, C-079–C-088 are marked FALSE only because the SUT took the *deny-the-Anspruch* fork — which the Musterlösung **itself blesses as vertretbar** (Lösungshinweis: a.A. vertretbar on the Ermessensreduzierung, given the available civil route). Once that defensible fork is chosen, scoring the downstream "einschreiten" criteria as independent misses is wrong on the merits.

**(c) Formalistic / label / order false-negatives — judge over-literal.**
- **C-049:** FALSE because the answer "went straight to Schmähkritik without first situating the Werturteile in Art. 5 I protection." That is an Aufbau/structure point, not wrong law — the substantive conclusion is right.
- **C-058:** FALSE for not reciting the ex-ante-Wahrscheinlichkeit definition of Gefahr, although it applied the concept.
- **C-008:** FALSE for not assessing "per Schutznormtheorie," although the same solution passed **C-009, C-010, C-011** — which *are* the Schutznorm/Drittschutz application. Internally inconsistent; a likely false-negative caused by overlapping criteria.

**Consequence:** the 81 % is misleading in *both* directions — it over-credits (wrong final result, still 81 %) and it over-counts misses (several "FALSE" are not real errors). The baseline at 72 % is genuinely weaker (it fails core substance: C-047, C-052, C-062, C-064, C-067, C-069), so the ranking 81 > 72 is directionally right but for partly wrong reasons.

## 4. What this validates for the evaluation redesign

The single example confirms all four planned improvements — and adds a fifth:

1. **Weighting** — the § 1 III POG error (C-042) and the whole grundrechtliche Abwägung (C-072) must outweigh reciting a Fristende (C-014). Essential.
2. **Hierarchy / dependency** — once the C-042 fork is taken, C-066/C-072/C-079–088 must not be scored as independent misses; anchor them to the Gliederungsbaum.
3. **Three dimensions (Inhalt / Gutachtenstil / Argumentation)** — C-049 shows structure being conflated with substance; separate them.
4. **Alternative-path detection** — the SUT's "unbegründet" result is a textbook vertretbare Gegenauffassung the flat rubric mishandles.
5. **Judge reliability needs human calibration** — C-008 / C-049 / C-058 are plausible false-negatives from over-literal criterion reading. The 84 %/81 % agreement figures need a human-validated gold set, especially on the argumentation and Abwägung criteria, before they mean much.

## 5. Relevance for the French track

This is the concrete argument for anchoring French rubrics to the **official CNB grilles de correction** — which are natively **weighted (barème)** and routinely flag **thèses défendables**. Those two features structurally pre-empt exactly the two hardest problems this example exposes: weighting (bucket-a vs procedural points) and alternative paths (bucket-b).
