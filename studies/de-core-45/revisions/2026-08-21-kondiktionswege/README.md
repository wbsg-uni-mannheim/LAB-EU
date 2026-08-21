# Kondiktionswege-Korrektur: Kaufrausch mit Katerstimmung

Diese Revision korrigiert fünf Kriterien der kanonischen Rubrik von
`fortgeschrittenenhausarbeit-kaufrausch-mit-katerstimmung`. Sachverhalt,
Musterlösung und alle übrigen 45 Kriterien bleiben unverändert.

## Befund

Die Rubrik ließ für Frage 2 (Lagerbau auf fremdem Grundstück) nur den Weg der
Musterlösung gelten und schloss den Weg der Rechtsprechung ausdrücklich aus:

- C-048 war „NICHT ERFÜLLT, wenn sie … auf eine Leistungskondiktion stützt".
- C-046 war „NICHT ERFÜLLT, wenn der Ausgleich … auf eine condictio ob rem
  gestützt wird".

BGH, Urt. v. 19.7.2013 – V ZR 93/12 entscheidet genau diese Konstellation
andersherum:

- Wer auf fremdem Grundstück in der Erwartung künftigen Eigentumserwerbs baut,
  hat einen Bereicherungsanspruch aus § 812 Abs. 1 S. 2 Alt. 2 BGB, wenn die
  Erwartung enttäuscht wird.
- Es genügt eine formlose tatsächliche Willensübereinstimmung zwischen Bauendem
  und Eigentümer; ein formwirksamer Vertrag nach § 311b BGB ist nicht nötig.
- Der Anspruch zielt auf die Grundstückswertsteigerung, nicht auf die Baukosten.

Der Sachverhalt trifft die Voraussetzungen: Die Parteien waren sich „über alle
Punkte einig", M baute vor dem Notartermin, „was S auch duldet". Beide Wege
führen zu denselben 30.000 €.

Die Musterlösung verneint eine Leistung mit der Begründung, M habe „in Erwartung
seiner eigenen perspektivischen Eigentümerstellung und nicht zur bewussten und
zweckgerichteten Mehrung fremden Vermögens" gehandelt – das ist genau das
Argument, das der BGH verwirft. Die dogmatische Aussage der Musterlösung zur
Verweisungsreichweite des § 951 Abs. 1 S. 1 BGB bleibt vertretbar; unzulässig
war nur, den zweiten Weg als Fehler zu werten.

Zusätzlich setzte C-017 den Prüfungsweg der Musterlösung voraus („nach dem
Hauptlösungsweg ohne verschärfte Haftung"). Wer die 14.000 € über
§ 816 Abs. 1 S. 1 BGB zuspricht – die h.M.-Route, die die Musterlösung selbst
mitträgt –, konnte das Kriterium strukturell nicht erfüllen.

## Änderungen

| Kriterium | alt | neu |
|---|---|---|
| C-017 | setzte den Zweckkondiktions-Pfad voraus | erfasst zusätzlich § 816 Abs. 1 S. 1 und §§ 687 Abs. 2 S. 1, 681 S. 2, 667 als tragfähige Grundlagen der 14.000 € |
| C-044 | nur § 951 i.V.m. § 812 Abs. 1 S. 1 Alt. 2 | zusätzlich unmittelbare condictio ob rem mit Feststellung des Eigentumsübergangs nach §§ 94, 946 |
| C-046 | verlangte die Ablehnung der condictio ob rem | verlangt die Behandlung des Verhältnisses; beide Ergebnisse zulässig |
| C-048 | schloss die Leistungskondiktion aus | prüft Betrag und Bemessungsmaßstab (objektiver Grundstücksmehrwert), nicht den Kondiktionstyp |
| C-050 | verlangte die Spezialitätsaussage | lässt auch den folgerichtigen Verzicht darauf zu, wenn über eine Leistungs-/Zweckkondiktion ausgeglichen wird |

Alle fünf tragen jetzt einen `review_notes`-Eintrag mit Datum und Grund; die
Rubrik trägt eine entsprechende `validation_warning`.

## Folgen für bestehende Läufe

Geändert hat sich die Bewertung, nicht die Aufgabe. **Ein Re-Solve ist nicht
nötig, ein Re-Judge dieses einen Falls genügt** – die Abgaben aller Arme sind
unverändert verwendbar. Das unterscheidet diese Revision von der
M/H-Korrektur vom 2026-08-13, die den Sachverhalt selbst betraf.

Betroffen sind alle Arme, die den Fall gelöst haben. Bekannt geprüft:
Codex Web erfüllte C-046 und C-048 inhaltlich über die BGH-Route und wurde
dafür als `fail` gewertet.

`judge_run.py` bewertet immer einen ganzen Run, das ist hier aber billig: Der
Vote-Cache-Schlüssel hasht den vollständigen Judge-Prompt, und der enthält den
Kriterientext (`evaluation/run.py`, `vote_cache_path`). Geändert wurden fünf
Kriterien, also werden auch nur diese fünf neu abgestimmt; alle übrigen Voten
kommen aus dem bestehenden Cache. Voraussetzung ist, dass derselbe
`--vote-cache-dir` wie im ursprünglichen Lauf verwendet wird — bei einem Run in
`runs/` ist das der Standard.

```bash
./env/bin/python scripts/judge_run.py runs/codex-web-45/20260806T110110Z --judge-committee configs/judge-committee-gemini-luna-terra-tiebreaker.json --committee-tiebreaker --style-evaluation
```

`results.csv` wird nachgetragen, sobald die Re-Judges gelaufen sind. Bis dahin
sind die Werte dieses Falls in `runs/de-core-45-final.csv` für die fünf
Kriterien überholt.
