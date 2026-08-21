# M/H-Korrektur: Anfechtungsklage bei Nebenbestimmungen

Diese Revision korrigiert ausschließlich die Klägerbezeichnung im Fall
`fall-02-anfechtungsklage-bei-nebenbestimmungen`:

- alt: Klage des M
- neu: Klage des H

Sachverhalt, Musterlösung und kanonische Rubric behandelten bereits H als
Kläger. Die historische 45-Fall-Auswertung und ihre Run-Artefakte bleiben
unverändert. Die korrigierte Fassung wurde mit dem Ein-Fall-Taskset
`tasksets/fall02-recheck.jsonl` in allen sechs ursprünglichen Modell- und
Harness-Bedingungen neu gelöst und mit dem ursprünglichen
Luna/Terra-plus-Gemini-Tiebreaker bewertet.

Die vollständigen Ergebnisse stehen in `results.csv`. Alle sechs Reruns
behandelten H als Kläger. Besonders relevant ist der DeepSeek-Agent: In der
eingefrorenen Studie folgte er als einziger Arm ausschließlich der fehlerhaften
M-Aufgabe; nach der Korrektur stieg er von 8/27 auf 17/27 Inhaltskriterien und
von 9/24 auf 17/24 Gutachtenstilkriterien.

Die Differenzen der anderen Arme dürfen nicht vollständig als kausaler Effekt
der Textkorrektur gelesen werden. Es handelt sich jeweils um einen neuen,
stochastischen Solver-Lauf; fünf der sechs alten Antworten hatten die
Inkonsistenz bereits selbst erkannt und H geprüft.

## Erfolgreiche Reruns

- `runs/de-core-45-v2-mh-baseline-gpt-5.6-sol-high/20260813T101021Z`
- `runs/de-core-45-v2-mh-baseline-gpt-5.6-terra-high/20260813T101021Z`
- `runs/de-core-45-v2-mh-baseline-deepseek-v4-pro/20260813T101021Z`
- `runs/de-core-45-v2-mh-agent-gpt-5.6-sol-high/20260813T103226Z`
- `runs/de-core-45-v2-mh-agent-gpt-5.6-terra-high/20260813T103226Z`
- `runs/de-core-45-v2-mh-agent-deepseek-v4-pro-medium/20260813T101959Z`

Zwei frühere Sol/Terra-Agent-Startversuche unter den Run-IDs
`20260813T101959Z` und `20260813T102517Z` scheiterten vor der Lösung, weil die
im Docker-Image gebündelte OpenCode-Modellliste GPT-5.6 noch nicht kannte. Sie
enthalten keine Submission und sind nicht Teil der Ergebnisse. Der Harness
registriert die beiden verifizierten Studienmodelle nun explizit.
