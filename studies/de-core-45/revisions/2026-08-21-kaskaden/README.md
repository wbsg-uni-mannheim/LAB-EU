# Kaskaden-Auszeichnung und Pfad-Skopus

Diese Revision führt zwei optionale Rubrikfelder ein und zeichnet die
verifizierte Kaskade in `examensklausur-ehe-und-espresso` aus. **Keine
Bewertung ändert sich.** 60 bestehende `scores.json` aus `codex-web-45` und
`se15-codex-web` wurden mit dem neuen Code nachgerechnet: null Abweichungen bei
`n_passed`, `n_criteria`, `criterion_pass_rate`, `all_pass`, dem
kritikalitätsgewichteten Score und allen vier Breakdowns.

## `depends_on` — Kaskaden sichtbar machen

Rubrikkriterien sind nicht unabhängig. In `ehe-und-espresso` hängen neun
Kriterien an einer einzigen Weiche:

```
C-012  Keine dingliche Wirkung des § 1357 BGB
 └─ C-016  Kein Anwartschaftsrecht der F
     └─ C-017  Alleineigentum des M bei der Zerstörung
         ├─ C-018  Recht der F zum Mitbesitz
         ├─ C-020  Berechtigter Mitbesitz als sonstiges Recht
         ├─ C-021  Verletzung des berechtigten Mitbesitzes
         ├─ C-024  Kein Substanzersatz aus § 823 Abs. 1 BGB
         ├─ C-025  Kein Substanzersatz über § 858 BGB
         ├─ C-026  Kein Substanzersatz über § 303 StGB
         └─ C-027  Kein Substanzersatz aus § 826 BGB
```

Wer § 1357 Abs. 1 S. 2 BGB dingliche Wirkung zuspricht, verliert alle neun --
unabhängig davon, wie gut der Rest ist. Die Pass-Rate kann das nicht von neun
unabhängigen Fehlern unterscheiden. Zwei Effekte:

- **Varianz.** Ein Zufallstreffer an der Weiche verschiebt den Fallwert um 17
  Punkte. Die effektive Stichprobengröße ist kleiner als die Kriterienzahl, was
  Signifikanztests über Modelle hinweg verzerrt.
- **Gewichtung durch die Hintertür.** Wie stark eine dogmatische Weiche zählt,
  hängt davon ab, wie fein die Rubrikgenerierung ihre Folgen zerlegt hat, nicht
  davon, wie wichtig sie juristisch ist. Das Feld `criticality` gewichtet
  bereits explizit; die Kaskade wirkt daneben als zweites, unsichtbares Gewicht,
  das mit dem ersten nicht korreliert.

`depends_on` nennt den direkten Vorgänger; die Kette löst das Scoring transitiv
auf und meldet nur die oberste Weiche, damit eine dreistufige Kette einen
Eintrag ergibt statt drei überlappender. `scores.json` erhält
`cascade_report`:

```
Pass-Rate                            43.4 %   (unverändert)
Unabhängige Weichen                  23/44 = 52.3 %
Fehler hinter gescheiterten Weichen  9
  C-012 (Keine dingliche Wirkung des § 1357 BGB): 9/9 Folgekriterien ebenfalls fail
```

Die zweite Zahl beantwortet beim Vergleich zweier Läufe die Frage, die die erste
offenlässt: Kommt der Unterschied aus vielen Einzelfehlern oder aus einer Weiche?

## `applies_when` — „Pfad nicht beschritten"

Bisher kannte der Judge nur `pass` und `fail`. Damit gab es keinen Weg,
zwischen zwei sehr verschiedenen Situationen zu unterscheiden:

| Situation | bisher | jetzt |
|---|---|---|
| Weg gegangen, richtig | pass | pass |
| Weg gegangen, falsch | fail | fail |
| Anderer tragfähiger Weg gegangen | fail | `not_applicable`, fällt aus dem Nenner |
| Gar nichts dazu geschrieben | fail | fail |

Der vierte Fall ist der Grund für die strenge Ausgestaltung: Würde man jedes
nicht beschrittene Kriterium neutralisieren, würde Auslassen belohnt. Deshalb:

- `not_applicable` ist **opt-in pro Kriterium**. Nur ein Kriterium mit
  `applies_when` bekommt die Option überhaupt in den Judge-Prompt; jedes andere
  behält das strikte pass/fail-Vokabular.
- Der Prompt verlangt ausdrücklich einen Pfad, den die Skopusnotiz **namentlich
  nennt**, und dass die Antwort ihn bis zu einem Ergebnis durchträgt. Wer das
  Thema auslässt, abbricht oder schweigt, hat keinen anderen Weg gewählt und
  bekommt `fail`.
- Bei der Abstimmung schlägt `pass` weiterhin `not_applicable`; nur eine
  Mehrheit für `not_applicable` setzt den Zustand.

Der Prompt liegt als eigene Variante `rubric_criterion.applies_when.txt` vor.
Das ist kein Stilentscheid: Der Vote-Cache-Schlüssel hasht den vollständigen
Prompt, eine Änderung an der Basisvorlage hätte jeden gecachten Vote in jedem
Lauf entwertet. So bleiben alle Prompts ohne `applies_when` byteidentisch.

## Umfang dieser Revision

- `evaluation/run.py`: `criterion_applies_when`, `not_applicable` in
  Normalisierung, Abstimmung und Scoring, `cascade_report`, Konsolenausgabe.
- `scripts/judge_committee_batch.py`: gleiche Behandlung im Batch-Pfad, damit
  beide Wege identische Voten cachen.
- `prompts/evaluation/rubric_criterion.applies_when.txt`: neue Promptvariante.
- `prompts/rubric_generation/prune_rubric.user.txt`: der Pruner setzt beide
  Felder künftig selbst und weiß, wann nicht.
- `tasks/.../examensklausur-ehe-und-espresso/evals/rubric.json`: die neun
  `depends_on`-Angaben oben.
- `tests/test_cascade_and_not_applicable.py`: 15 Tests, darunter der Nachweis,
  dass beide Felder ohne Verwendung wirkungslos sind.

## Offen

Zwei weitere Kaskaden sind belegt, aber noch nicht ausgezeichnet, weil sie
Rubriken außerhalb dieses Falls betreffen:

- `fortgeschrittenenklausur-die-reise-ins-gericht`: Vollendung des § 153 StGB
  trägt C-030, C-031, C-032, C-041.
- `Oertel-BayVBl-2025_537ff_572ff` (de-second-exam-15): die Gebietseinstufung
  faktisches Gewerbegebiet gegen Kerngebiet trägt zwölf Kriterien.
