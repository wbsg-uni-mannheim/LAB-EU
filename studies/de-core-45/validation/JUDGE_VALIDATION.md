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

Auf Teil 1 gleichauf mit dem veröffentlichten Judge (85 von 94), mit ausgewogeneren Fehlern. Da v4 auf Teil 1
entwickelt wurde, entscheidet Teil 2 über die Übernahme. Die Vorhersagen des eingefrorenen Judges für Teil 2
wurden vor Eingang der Labels berechnet (`runs/validation-teil2-v4-frozen-*`).

Entscheidungsregel für Teil 2: Der eingefrorene Judge ersetzt den veröffentlichten, wenn er auf Teil 2 nicht
schlechter abschneidet und keine deutlich höhere Rate zu großzügiger Urteile hat. Dann werden alle Läufe neu
bewertet.

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
- Benedikt klärt die übrigen "unklar"-Zeilen (57, 70, 82, 83, 96) und Nr. 32.
- Teil 2 (Nr. 101 bis 200) bis 20.10.2026, danach Auswertung nach der Regel in Abschnitt 5.
- Die acht "teilweise"-Kriterien in der Rubrik nachschärfen und als Revision dokumentieren.
