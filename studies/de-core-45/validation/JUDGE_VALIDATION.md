# Juristische Validierung von Rubriken und Judge (de-core-45)

Stand: 14.10.2026. Gutachter: Benedikt Asal (Jurist, Lehrstuhl Müller-Terpitz, Mannheim).

## 1. Stichprobe

- Grundgesamtheit: 1.777 Inhaltskriterien der 45 Erstexamensfälle. Ausgeschlossen sind der Fall
  `fall-02-anfechtungsklage-bei-nebenbestimmungen` (27 Kriterien, Solver-Prompt fragte nach M statt H)
  und Wertpapier C-032/C-033 (KCanG-Auszug fehlte beim Bewerten). Das Zweite Staatsexamen ist nicht Teil
  dieser Validierung.
- Zufallsstichprobe von 250 Kriterien, geschichtet nach Rechtsgebiet und Gewichtung, Seed 20261007
  (`scripts/build_validation_export.py`). Pro Zeile wird die Antwort eines zufällig gewählten Laufs gezeigt.
- Teil 1 (Nr. 1 bis 100) ist das Entwicklungsset für den Judge. Teil 2 (Nr. 101 bis 200) ist das Testset.
  Der Judge wurde vor der Auswertung von Teil 2 eingefroren (Abschnitt 5).
- Die Excel mit Benedikts Labels liegt außerhalb des Repos (Drive-Ordner "Überprüfung der Juristen",
  Rückgabe per Mail am 13.10.2026). Die Skripte lesen sie über `--xlsx`.

## 2. Ergebnis Teil 1: Rubriken

| Kriterium juristisch korrekt? | Anzahl |
|---|---:|
| ja | 92 |
| teilweise | 8 |
| nein | 0 |

Die acht "teilweise" sind zu eng oder zu fallspezifisch formuliert oder machen aus Hinweisen der Musterlösung
eigene Kriterien. Zwei davon (Casanova C-043, Wertpapier C-021) waren schon vorher als Rubrikfehler gefunden
und neu gefasst worden. Nie gelöste Kriterien sind häufiger betroffen (4 von 17) als die übrigen (4 von 83).

## 3. Ergebnis Teil 1: veröffentlichter Judge

Veröffentlichter Judge: Prompt v1, GPT-5.6 Luna und GPT-5.6 Terra, Gemini 3.6 Flash als Tiebreaker
(Urteile vom 4.8.2026).

Goldlabel je Zeile: das gezeigte Urteil bei "Urteil korrekt: ja", das Gegenteil bei "nein", kein Label bei
"unklar". Im Meeting am 13.10.2026 hat Benedikt einige Zeilen geklärt
(`teil1_klaerungen_2026-10-13.json`: Nr. 17, 26, 87 nicht erfüllt, Nr. 32 vorerst ausgeschlossen). Die
Klärungen erfolgten nach Sicht auf Abweichungen der Judges. Beide Stände werden berichtet.

| | vor Klärung | nach Klärung |
|---|---:|---:|
| Zeilen mit Label | 92 | 94 |
| Urteil richtig | 83 (90,2 %) | 85 (90,4 %, 95-%-KI 82,8 bis 94,9) |
| zu streng (nicht erfüllt statt erfüllt) | 8 | 7 |
| zu großzügig | 1 | 2 |
| Cohens κ | 0,79 | 0,80 |

Finale Labels (14.10.2026): Benedikt hat die offenen Zeilen selbst festgelegt (Datei
`00_Validierung_Stichprobe-1.xlsx`). Nur Nr. 83 und 96 bleiben unklar, weil dort schon das Kriterium nur
teilweise korrekt ist. Die Klärungsdatei vom 13.10. ist damit überholt. Nr. 32 behält sein ursprüngliches Label.

| Judge | richtig (von 98) | Übereinstimmung | κ | zu streng | zu großzügig | Erfolgsquote laut Judge |
|---|---:|---:|---:|---:|---:|---:|
| veröffentlicht | 87 | 88,8 % (KI 81,0 bis 93,6) | 0,76 | 9 | 2 | 59,2 % |
| eingefroren (Abschnitt 5) | 88 | 89,8 % (KI 82,2 bis 94,4) | 0,78 | 7 | 3 | 62,2 % |

Erfolgsquote laut Gutachter: 66,3 %. Weitere Konfigurationen mit finalen Labels: nur DeepSeek V4.1 Flash (v4)
88, nur Gemini 3.6 Flash (v4) 89, GPT-6 Sol (v4) 79.

Nach Klärung: Sensitivität 0,887, Spezifität 0,938. Erfolgsquote laut Judge 60,6 %, laut Gutachter 66,0 %.
Die Rogan-Gladen-Korrektur mit diesen Raten ergibt 66,0 %. Die Scores des Judges sind damit eher eine
Untergrenze.

Zu-streng-Fehler treten bei DeepSeek-Antworten häufiger auf (5 von 18 erfüllten Kriterien) als bei
OpenAI-Antworten (2 von 44). Der Effekt zeigt sich auch beim DeepSeek-Judge selbst. Er spricht daher eher für
den knapperen Antwortstil von DeepSeek als für eine Bevorzugung der eigenen Modellfamilie. Auf Teil 2 erneut
prüfen.

Einordnung: PRBench (Recht/Finanzen) berichtet 80,2 % Judge-Mensch-Übereinstimmung bei 79,6 % zwischen zwei
Fachleuten, LexRubric 79,4 % (κ 0,59), FinResearchBench II 84,8 % (κ 0,69). Harvey LAB berichtet keinen
Abgleich mit Juristen. Ein Vergleich zwischen zwei Juristen fehlt hier noch (Abschnitt 7).

## 4. Judge-Experimente auf Teil 1

Alle Läufe bewerten genau die 100 Zeilen von Teil 1 mit dem Rubriktext, den der Gutachter gesehen hat
(Aufgabenstand Commit 1f5be8a). Ergebnisse unter `runs/validation-teil1-*`, Vergleich mit
`scripts/compare_validation_runs.py`. Zahlen nach Klärung, 94 Zeilen.

Prompts (`prompts/evaluation/`, Schalter `--judge-prompt-version`):

- v1: veröffentlichter Prompt.
- v2: "im Zweifel nicht erfüllt" ersetzt, zwingend mitgemeinte Bestandteile zählen, Prüfungsort in beide Richtungen.
- v3: v2, aber nur Inhalte, die die Antwort selbst enthält, zählen als mitgemeint.
- v4: v1 plus Benedikts drei Maßstäbe: Ergebnis und Begründung müssen an der Stelle stehen, die genau diese
  Frage prüft. Implizite Erfüllung zählt, wenn sie aus den Ausführungen klar wird. Beim "weil"-Teil reicht
  ein richtiges Ergebnis an der richtigen Stelle mit vertretbarer, kürzerer Begründung.

| Konfiguration | Prompt | richtig | zu streng | zu großzügig |
|---|---|---:|---:|---:|
| veröffentlicht (Luna 5.6 + Terra, Gemini 3.6 Tiebreaker) | v1 | 85 | 7 | 2 |
| GPT-6 Luna + DeepSeek V4.1 Flash + Gemini 3.8 Flash | v1 | 84 | 8 | 2 |
| GPT-6 Luna + DeepSeek V4.1 Flash + Gemini 3.8 Flash | v2 | 83 | 7 | 4 |
| GPT-6 Luna + DeepSeek V4.1 Flash + Gemini 3.8 Flash | v3 | 83 | 6 | 5 |
| **GPT-6 Luna + DeepSeek V4.1 Flash + Gemini 3.8 Flash** | **v4** | **85** | **6** | **3** |
| Luna 5.6 + Terra + Gemini 3.6 | v4 | 84 | 7 | 3 |
| Luna 5.6 + DeepSeek V4.1 + Gemini 3.6 (aus vorhandenen Stimmen) | v4 | 85 | 5 | 4 |
| nur DeepSeek V4.1 Flash | v2 | 85 | 5 | 4 |
| nur Gemini 3.6 Flash | v4 | 87 | 6 | 1 |
| nur GPT-6 Sol, Reasoning high | v1 | 79 | 13 | 2 |
| nur GPT-6 Sol, Reasoning high | v4 | 77 | 14 | 3 |

Erkenntnisse:

- Alle Komitees liegen bei 83 bis 85 von 94. Die Bootstrap-Konfidenzintervalle der Differenz zum
  veröffentlichten Judge schließen bei allen gemischten Komitees 0 ein (etwa minus 4 bis plus 4 Zeilen).
- Der Vergleich begünstigt den veröffentlichten Judge, weil der Gutachter dessen Urteile beim Bewerten sah.
- Wiederholbarkeit: Bei identischer Wiederholung ändert GPT-6 Luna 7 von 100 Urteilen, DeepSeek V4.1 Flash 4.
- Ein stärkeres Modell hilft nicht. GPT-6 Sol mit hohem Reasoning liest die Kriterien wörtlicher und wird
  strenger.
- Fünf Zeilen (Nr. 2, 12, 22, 56, 86) scheitern in jeder Konfiguration. Vier davon sind Fälle, in denen der
  Gutachter eine Erfüllung aus dem Zusammenhang oder per Erst-recht-Schluss anerkennt, die kein Modell sieht.

Kosten aller Experimente: grob 25 bis 35 USD.

Behobener Fehler: `evaluation/run.py` hat bei Judges über OpenRouter (DeepSeek, Gemini) die Reasoning-Stufe
aus der Komitee-Datei nie übergeben. Es galt immer die Voreinstellung des Anbieters. Seit 13.10.2026 wird sie
übergeben. Für Einträge `"none"` ändert sich nichts, deren Cache-Einträge bleiben gültig.

## 5. Eingefrorener Judge (14.10.2026)

Entscheidung: Komitee aus drei Modellfamilien, keine stellt die Mehrheit.

- Prompt v4 (`combined_content_style_criterion.v4.txt`, `rubric_criterion.v4.txt`)
- Komitee `configs/judge-committee-luna6-deepseek41-gemini38-tiebreaker.json`: GPT-6 Luna und DeepSeek V4.1
  Flash als Primärjudges, Gemini 3.8 Flash nur bei Dissens, alle mit Reasoning medium
- Modus: `--committee-tiebreaker --style-evaluation --judge-prompt-version v4`, 2 Wiederholungen bei Fehlern

Auf Teil 1 gleichauf mit dem veröffentlichten Judge (nach Klärung 85 von 94, mit finalen Labels 88 von 98 gegenüber 87 von 98), mit ausgewogeneren Fehlern. Da v4 auf Teil 1
entwickelt wurde, entscheidet Teil 2 über die Übernahme. Die Vorhersagen des eingefrorenen Judges für Teil 2
wurden vor Eingang der Labels berechnet (`runs/validation-teil2-v4-frozen-*`).

Änderung am 14.10.2026 (vor Beginn von Teil 2): Teil 2 zeigt nicht mehr die Urteile des veröffentlichten,
sondern des eingefrorenen Judges aus der Neubewertung aller Läufe (`scores-v4-frozen.json`, aktueller
Rubrikstand). Die gezeigte Antwort wurde für Nr. 101 bis 250 neu und ausgewogen aus acht Systemen gezogen
(je 18 bis 19 Zeilen, Seed 20261015): Sol, Terra, DeepSeek (je Agent und Baseline), Claude Opus 5.5, GPT-6
Astra. Neue Spalte "Begründung des Judges trägt?". Teil 2 misst damit die Genauigkeit des finalen Judges im
selben Verfahren wie Teil 1. Ein Vergleich alt gegen neu auf Teil 2 ist dadurch nicht mehr unverzerrt, weil
der Gutachter das neue Urteil sieht. Die Vorhersagen in `runs/validation-teil2-v4-frozen-20261014` beziehen
sich auf die frühere Zuordnung und dienen nur noch als Nachweis.

Entscheidungsregel für Teil 2: Der eingefrorene Judge ersetzt den veröffentlichten, wenn er auf Teil 2 nicht
schlechter abschneidet und keine deutlich höhere Rate zu großzügiger Urteile hat. Dann werden alle Läufe neu
bewertet.

## 5a. Ergebnis Teil 2 (19.10.2026)

Datei `00_Validierung_Stichprobe-2.xlsx`, Nr. 101 bis 200, gezeigt wird das Urteil des eingefrorenen Judges.

| Kriterium juristisch korrekt? | Anzahl |
|---|---:|
| ja | 96 |
| teilweise | 2 (Nr. 175, 183) |
| nein | 2 (Nr. 116, 151) |

| | Wert |
|---|---:|
| Zeilen mit Label | 98 (Nr. 121 leere Abgabe wie Nr. 87, eine Zeile "unklar") |
| Urteil richtig | 96 (98,0 %, 95-%-KI 92,9 bis 99,4) |
| zu streng | 2 (Nr. 113, 165, beide GPT-6-Astra-Antworten, implizite Erfüllung) |
| zu großzügig | 0 |
| Cohens κ | 0,96 |

Die Spalte "Begründung des Judges trägt?" ist nur bei 8 Zeilen als Freitext gefüllt, alle kritisch. Hinweise
auf veraltetes Recht: Nr. 104 (HGB vor MoPeG), Nr. 151 (ältere Rechtsprechung).

Vorbehalt: Der Gutachter sah das Urteil des Judges (Ankereffekt). Die Quote ist deshalb eher eine Obergrenze,
der blinde Zweitgutachter (Abschnitt 7) bleibt wichtig.

Entscheidung: Die Regel aus Abschnitt 5 ist erfüllt. Der eingefrorene Judge ersetzt den veröffentlichten. Seine
Urteile liegen als `scores-v4-frozen.json` neben jeder `scores.json` der sechs Hauptarme (Agent und Baseline
für Sol, Terra, DeepSeek), die Konfiguration als `judge_config.scores-v4-frozen.json` im Laufordner. DeepSeek
Agent hat bei `anfanger-innenhausarbeit-bundeszwang-und-rededrang` keine Abgabe und daher keine neue Datei.

## 6. Reproduktion

```bash
# Teil 1 neu bewerten (Beispiel eingefrorener Judge, alle drei stimmen ab)
python3 scripts/rescore_validation_sample.py --xlsx <Excel> --part 1 \
  --runs-root <origin/main runs> --tasks-snapshot <git archive 1f5be8a>/tasks \
  --committee configs/judge-committee-luna6-deepseek41-gemini38-tiebreaker.json \
  --prompt-version v4 --full-votes \
  --gold-overrides studies/de-core-45/validation/teil1_klaerungen_2026-10-13.json \
  --output-dir runs/validation-teil1-v4-newcommittee-20261013

# Konfigurationen vergleichen
cd scripts && python3 compare_validation_runs.py ../runs/validation-teil1-* --xlsx <Excel> \
  --gold-overrides ../studies/de-core-45/validation/teil1_klaerungen_2026-10-13.json
```

Die veröffentlichten Urteile (`runs/<arm>/<run>/tasks/*/scores.json`) liegen auf `origin/main` (Commit 9ffbd17).

## 7. Offen

- Zweiter Jurist bewertet etwa 50 Zeilen ohne Judge-Urteil, für die Übereinstimmung zwischen Menschen.
- Zeilen 201 bis 250 sind noch nicht bewertet.
- Die acht "teilweise"-Kriterien in der Rubrik nachschärfen und als Revision dokumentieren.
