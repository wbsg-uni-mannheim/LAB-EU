# Manuelles Reviewprotokoll: Pilotrubriken second-exam-pilot-v1

Stand: 2026-08-11. Reviewer: Claude (Sitzung Pilot-Generierung), beauftragt von Aaron.
Gegenstand: `rubric.second-exam-pilot-v1.json` für Allesch-BayVBl-2024 und Kaess-BayVBl-2026
(Köhl-BayVBl-2025 folgt nach Abschluss der Generierung).

Alle manuellen Änderungen sind zusätzlich je Rubrik im Feld `manual_edits` dokumentiert.
Das jeweilige `rubric.generated.second-exam-pilot-v1.json` bleibt als unveränderter
Generierungs-Audit-Trail bestehen; die finale Rubrik weicht ab diesem Review dokumentiert davon ab.
Keine Neukalibrierung erforderlich: Sämtliche Textänderungen erweitern die PASS-Seite oder die
Fundort-Listen; die Musterlösung besteht dadurch weiterhin.

## Gesamturteil

Beide Rubriken sind strukturell tragfähig. Die Mehrdokument-Mechanik (eingefrorene Typ-Karte,
Oder-Fundorte, je ein Vollständigkeitskriterium pro Datei, Scope-Compliance, keine Kriterien zu
erlassenen Bestandteilen) hat auf Anhieb funktioniert. Alle im Inventar markierten vertretbaren
Alternativen sind mit benannten Anforderungen kodiert; die dokumentierten Quellfehler der
Kaess-Lösung (BayBO/BayDSchG-Tippfehler, Verlöbnis-Verdreher) wurden nicht übernommen.
Kein Doppel-Scoring und keine konjunktiven Bündel gefunden. Sterne-Verteilungen in den
Zielkorridoren, ★★★ auf den ergebnistragenden Weichen.

## Durchgeführte Änderungen (2026-08-11)

### Allesch-BayVBl-2024 (67 Kriterien, unverändert 67)

1. **C-011 (örtliche Zuständigkeit, ★):** PASS-Seite geöffnet — jede tragfähige Herleitung aus
   § 52 VwGO i. V. m. Art. 1 Abs. 2 Nr. 2 AGVwGO genügt, Nr. 5 ist nur noch Beispiel.
   Grund: Äquivalenzrisiko (Asal-Muster); die Normnummer ist erkennbar strittig — die
   Köhl-Musterlösung zitiert in gleicher Lage § 52 Nr. 1.
2. **C-008 (gutachtliche Methode im Hilfsgutachten, ★):** Review-Note ergänzt — misst
   Methodenleistung (E1) neben dem separaten Pro-Kriterium-Stilscore (E2); im Reporting
   nicht addieren. Kriterientext unverändert.

### Kaess-BayVBl-2026 (45 Kriterien, unverändert 45)

1. **C-046 (Vollständigkeit Hilfsgutachten, ★):** Auf Existenz + Dokumenttyp reduziert; die
   Anforderung „mindestens eine konkrete Rechtsfrage" entfernt. Grund: Der Hilfsgutachten-Auftrag
   ist bedingt formuliert und das Gold-Hilfsgutachten selbst minimal (423 Bytes); eine
   Mindesttiefe würde legitime Verteilungen bestrafen (Inventar-Konsequenz Nr. 2).
2. **C-008 / C-009 (Postulationsfähigkeit, LABV-Zuständigkeit, ★):** Fundort-Oder-Liste um das
   Behördenschreiben erweitert; die Aufgabe erlaubt die Behandlung dieser Punkte auch dort.
3. **C-022 (Wiederholungsgefahr Klageantrag II, war flaky):** Auf die Knappheit der Musterlösung
   abgeschwächt (Gold verneint in einem Halbsatz) und von ★★ auf ★ herabgestuft. Damit ist die
   Ursache der Komitee-Uneinigkeit adressiert; das Kalibrierungs-Flag bleibt als Historie stehen.
4. **C-002 (Substantiierungsmaßstab ernstliche Zweifel, ★★★):** Review-Note für das juristische
   Fachreview — Aggregations-Grenzfall gegenüber den konkreten Angriffskriterien C-021 ff.;
   Entscheidung bewusst nicht vorweggenommen. Kriterientext unverändert.

### Köhl-BayVBl-2025 (61 Kriterien, unverändert 61; Review 2026-08-11 nach Abschluss der Generierung)

Befund: sauberster der drei Fälle — 0 Validierungswarnungen, 0 flaky, 1 Kalibrierungs-Drop.
Positiv hervorzuheben:

- **C-001** nimmt die erlassenen Bestandteile (Rubrum, Tatbestand, Kosten, Vollstreckbarkeit,
  Rechtsmittelbelehrung, Streitwert) ausdrücklich von der Vollständigkeitsprüfung aus.
- **Asymmetrische Vertretbarkeit korrekt kodiert:** C-057 lässt die Gegenansicht zum
  1.000-Euro-Zwangsgeld mit denselben Bemessungsfaktoren zu („mit entsprechender Begründung
  vertretbar"); C-061/C-062 verlangen für die Billigung der 10.000 Euro eine konkrete
  Begründung („nur mit guter Begründung vertretbar"). Die Tenor-Kriterien C-006/C-009
  spiegeln beide Alternativen mit Folgerichtigkeits-Anforderung.
- **§ 44 Abs. 1 StVO als zugelassene Alternative** zur sachlichen Zuständigkeit in C-032
  (Lösungshinweis: „sollte nicht negativ gewertet werden").
- Der „Klägerin"-Quellfehler des Gold-Hilfsgutachtens wurde nicht übernommen; der
  Fälligkeits-Komplex (C-026 bis C-029) ist atomar sauber getrennt.

Änderungen:

1. **C-011 (örtliche Zuständigkeit, ★):** PASS-Seite auf jede tragfähige §-52-Herleitung
   geöffnet (vorher zwingend Nr. 1) — Gegenstück zum Allesch-C-011-Fix; die Musterlösungen
   beider Fälle zitieren in Parallellage unterschiedliche Nummern (Nr. 1 vs. Nr. 5).
2. **C-005 (gutachterliche Methode Verwaltungsrechtsweg, ★):** Weglass-Freibrief ergänzt.
   Der Lösungshinweis erklärt die Rechtswegprüfung für unproblematisch und ihr Fehlen für
   nicht negativ zu werten; das Kriterium prüft jetzt nur noch die Methode, wenn die Prüfung
   vorhanden ist.
3. **C-006:** Review-Note Fehlerfortpflanzung (siehe Fachreview).
4. **C-010/C-011:** Review-Note — klären, ob der Weglass-Freibrief des Lösungshinweises auch
   die Zuständigkeitsprüfung erfasst (sie steht im Gold-Hilfsgutachten im selben Block, ist im
   Hinweis aber nicht wörtlich genannt).

## Für das juristische Fachreview vorgemerkt

- Kaess C-002: Aggregations-Grenzfall (siehe oben).
- Rechtsstands-Prüfpunkte aus dem Inventar (BayDSchG-Novelle 2023, Art. 57 BayBO,
  PAG-Novellen 2021/2023, § 49 StVO-Nummerierung) — betrifft die Norm-Zitate in den Kriterien.
- Kalibrierungs-Drops aller Fälle (Allesch 5, Kaess 2, Köhl 1) stichprobenartig gegenlesen
  (dokumentiert in `rubric.generated.second-exam-pilot-v1.json` unter `calibration.dropped`).
- Köhl C-006/C-061/C-062: Fehlerfortpflanzung Tenor/Begründung beim 10.000-Euro-Komplex —
  drei eigenständige Leistungen oder Doppelzählung eines Grundfehlers?
- Köhl C-010/C-011: Reichweite des Weglass-Freibriefs für die Zuständigkeitsprüfung im
  Hilfsgutachten.

## Positiv- und Negativprüfung (durchgeführt 2026-08-11)

Ergebnisse im Detail in `pruefbericht-pilot.md`. Kurzfassung: Positivprüfung durch die echte
Pipeline bestanden (Allesch 67/67 all_pass; Kaess 44/45 und Köhl 60/61 mit je einem
Einzelstimmen-Fail, beide Kriterien dokumentiert auf Gold-Niveau abgeschwächt: C-034, C-033);
Stil-Routing live verifiziert. Negativprüfung: 8/8 deterministische Phase-H-Mutanten scheitern
an exakt den vorgesehenen Kriterien ohne sachfremde Folgesanktionen.

Zusätzliche manuelle Edits aus der Prüfung: Kaess C-034 und Köhl C-033 (siehe `manual_edits`
der Rubriken).

## Externes Review (2026-08-12, Gesamtnote 6,5/10) und Umsetzung

Entscheidungen (Aaron):

- **Gesamtscore bleibt All-Pass** — reportet werden ohnehin primär die Prozentwerte
  (criterion_pass_rate, criticality_weighted). Kein Umbau von evaluation.run.
- Rest in der differenzierten Form umgesetzt (Umsetzung an Claude delegiert).

Umgesetzte Änderungen (je Rubrik in `manual_edits` dokumentiert, inkl. `removed_criteria`):

1. **HG-Existenzkriterien entfernt** (Allesch C-003, Kaess C-046, Köhl C-002): Der
   Hilfsgutachten-Auftrag ist bedingt formuliert; die Substanz sichern die Inhaltskriterien mit
   Oder-Fundorten. Runner-seitig bleibt das HG angefordertes Deliverable, `missing_deliverables`
   meldet nachrichtlich. Vollständigkeitskriterien der unbedingten Hauptdokumente bleiben.
2. **Merges gegen Mehrfachsanktionierung:** Allesch C-017+C-018 (eine tragfähige
   FFI-Begründung genügt, Oder-Struktur), Allesch C-049-S1+S3 (Zurechnung samt prozessualer
   Folge; S2 bleibt als eigenständige Art.-12-POG-Widerlegung), Kaess C-039→C-040-S1
   (Befangenheitsanlass + Offenbarungspflicht), Köhl C-061+C-062 (ein Begründungsmangel mit
   zwei alternativen Gesichtspunkten; C-006/Tenor bleibt getrennt — fängt Mutant m7).
3. **Kaess C-002 gestrichen** (Aggregat; Substanz in C-021 ff.).
4. **`deliverable_profiles` bleiben** — der abgenommene Plan sieht das Feld ausdrücklich vor
   (Phase C „Einzige Ausnahme", Phase E „Einfrieren des Dokumenttyps"); eine Entfernung würde
   einen nichtdeterministischen Laufzeit-Klassifikator wieder einführen und Vote-Caches/
   Reproduzierbarkeit brechen. Vom Review abweichende Entscheidung, Begründung im Chat vom
   2026-08-12, Umsetzung von Aaron delegiert.

Neue Kriterienzahlen: Allesch 64, Kaess 42, Köhl 59. Erwartungskataloge der Negativmutanten
entsprechend bereinigt (expectations.json).

## Offen

- ~~Positivläufe v2~~ erledigt 2026-08-12: Allesch 64/64, Kaess 42/42, Köhl 59/59 (all_pass);
  dabei vier weitere Gold-Niveau-Öffnungen (C-040, C-023, C-044, C-007), siehe Prüfbericht.
- ~~Zwei echte Modelllösungen je Pilotfall~~ erledigt 2026-08-12: codex-web-pilot3 und
  codex-no-web-pilot3 gejudgt (63–73 % Content, ★★★-Kern 38/44) — Ergebnistabelle und
  Befunde im Prüfbericht.
- Drei Phase-H-Mutationstypen mit LLM-Dokumentumschreibung (Urteil im Gutachtenstil,
  Alternativlösung als durchgängiger Weg, doppelter Gedanke) — siehe Prüfbericht.
- Juristisches Fachreview der oben vorgemerkten Punkte; zusätzlich aus der Prüfung:
  Stil-Tagging reiner Feststellungs-Kriterien.

## Komitee-Abnahme (2026-08-12, Luna/Terra/Gemini; Vote-Caches persistent in ~/.cache/lab-eu/)

- **Allesch: abgenommen** — 63/64 einstimmig; C-040 nach zweiter Öffnung (Gold stellt die
  Ungeeignetheit anderer Zwangsmittel nur fest) im Recheck 3/3.
- **Kaess: substanziell abgenommen** — 38/42 einstimmig; 4 Kriterien mit 2:0-Pass und
  ausschließlich technischem Fehler der dritten Stimme (OpenRouter 402), kein inhaltliches
  Fail-Votum. Formaler Abschluss nach Guthaben-Auffüllung (4 Gemini-Calls).
- **Köhl: substanziell weitgehend abgenommen** — 56/59 mit 2:0 (Luna/Terra; Gemini-Spalte
  komplett 402). Drei echte 1:1-Splits (C-011, C-030, C-057), alle erneut die
  Gold-Knappheits-Klasse; am 2026-08-12 geöffnet (siehe `manual_edits`). Formaler Abschluss
  nach Guthaben-Auffüllung (Gemini-Spalte + Recheck der drei geöffneten Kriterien).
- ~~Blocker OpenRouter-Guthaben~~ aufgelöst 2026-08-12: Nach Auffüllung wurden die Nachträge
  gefahren. **Endstand der Komitee-Abnahme: Allesch 64/64, Kaess 42/42, Köhl 59/59 — jeweils
  all_pass, einstimmig, keine unresolved.** Alle drei Pilot-Rubriken sind formal abgenommen.
- Lehre bestätigt: Die Gold-Knappheits-Fehlerklasse trat in der Abnahme erneut auf (vier
  weitere Öffnungen); die am 2026-08-12 ergänzte Promptsatz-Regel verhindert sie für die
  Wellen 2 und 3 bereits in der Generierung.

## Nächste Schritte

1. Komitee-Abnahme formal abschließen (nach OpenRouter-Auffüllung): 4 Kaess-Kriterien,
   Köhl-Gemini-Spalte, Recheck Köhl C-011/C-030/C-057.
2. ~~Risikowelle generieren~~ erledigt 2026-08-12: Oertel (43 Kriterien) und Schömig (66)
   generiert, komitee-validiert (43/43 bzw. 66/66 all_pass, einstimmig, auf Anhieb) und per
   Mutanten geprüft (12/12 über beide Wellen) — Details im Prüfbericht.
3. Restwelle (10 Fälle): zuerst Phase-A-Inventar (Plan-Abnahmebedingung), dann Generierung
   in Batches mit dem nachgeschärften Promptsatz; verkürzte Prüfung nach Welle-2-Vorbild
   (Komitee-Positivlauf + gezielte Mutanten je Batch).

## Nachtrag 2026-08-13: Kalibrierungs-Komitee v2, Nachvalidierung, Welle 3 Batch 1

**Komitee-Wechsel (Bias-Reduktion):** Ab Welle 3 kalibriert das v2-Komitee
(`configs/judge-committee-rubric-calibration-v2.json`): Terra ist durch
**deepseek-v4-flash-0731** (OpenRouter) ersetzt. Begründung: Der Generator ist gpt-5.6-sol;
mit Luna+Terra stellten zuvor zwei von drei Stimmen dieselbe gpt-5.6-Familie. Jetzt sind
drei Modellfamilien vertreten (OpenAI/DeepSeek/Google), keine hat die Mehrheit.

**Nachvalidierung der 5 abgenommenen Rubriken mit dem v2-Komitee** (Setup identisch zur
Original-Abnahme: full_committee, conflict-recheck, kein Style-Scoring; Luna/Gemini-Votes
aus dem persistenten Cache, nur die DeepSeek-Spalte neu; Ergebnisse in
`scores.committee-v2.json` neben den historischen Dateien):

| Fall | Ergebnis | Einstimmig | DeepSeek-Dissens (überstimmt) |
| --- | --- | --- | --- |
| Allesch | 64/64 all_pass | 64 | — |
| Kaess | 42/42 all_pass | 42 | — |
| Köhl | 59/59 all_pass | 58 | C-003 (Fehlvotum: „Im Namen des Volkes!" steht im Gold, Z. 13) |
| Oertel | 43/43 all_pass | 43 | — |
| Schömig | 66/66 all_pass | 65 | C-032 (Fehlvotum: § 29-Behandlung steht wörtlich im Gold, Z. 65) |

Fazit: **Kein Hinweis auf gpt-5.6-Familien-Bias in den bestehenden Abnahmen** — die
familienfremde Stimme bestätigt 272/274 Kriterien einstimmig; beide Dissense sind
verifizierte Fehlvoten des neuen Judges (leere Begründung, Aussage steht wörtlich im Gold)
und wurden vom Konflikt-Recheck korrekt als `stable_with_dissent` überstimmt.
DeepSeek-False-Fail-Rate auf Gold: 2/274 (0,7 %).

**Welle 3, Batch 1 generiert** (v2-Komitee, nachgeschärfter second-exam-Promptsatz):

| Fall | Kriterien | Kalibrierung | Anmerkungen |
| --- | --- | --- | --- |
| Decker | 52 | kept 52 / dropped 0 (2 Runden, 9 refined) | C-048 flaky (2/3, Review-Note); Tier-3 9,6 % knapp unter Ziel |
| Gregor | 48 | kept 48 / dropped 0 (5 refined) | sauber |
| Hasl-Kleiber | 50 | kept 50 / dropped 1 (14 refined) | sauber; 3 Deliverable-Profile korrekt |

Alle Deliverable-Profile korrekt klassifiziert, keine validation_errors. Verkürzte Prüfung
des Batches (Komitee-Positivlauf + gezielte Mutanten) steht aus.

**Judge-Kostentest läuft:** tencent/hy3 (ca. Faktor 11–14 billiger als gemini-3.6-flash)
als Ablöse-Kandidat; Testkorpus = 5 Gold-Abnahmen (False-Fail-Rate) + 12 Mutanten
(expectations.json). Ergebnis folgt.

## Nachtrag 2026-08-13 (2): Drei Judge-Harness-Bugs, Kostenmessung, Judge-Entscheidung

**Anlass:** Kostentest von `tencent/hy3` und `z-ai/glm-5.2` als Gemini-Ablöse. Beide Modelle
schienen zunächst unbrauchbar (~35 % unparsbare Antworten, ~30 % False-Fails). Ursache waren
drei Fehler im eigenen Harness, nicht die Modelle:

1. **Content im falschen Feld.** Manche OpenRouter-Provider (Novita bei glm-5.2, Tencent bei
   hy3) liefern bei Thinking-Modellen `content: null` und schreiben die JSON-Antwort ins
   `reasoning`-Feld. `_judge_call_chat` las nur `content` → "No JSON object found". Behoben
   durch Fallback auf `reasoning`.
2. **`max_tokens=4000` zu knapp.** Auf dem Chat-Pfad zählen die versteckten Reasoning-Tokens
   gegen dieses Budget; das JSON wurde abgeschnitten. Jetzt `CHAT_JUDGE_MAX_TOKENS = 16000`.
3. **Abgeschnittenes JSON wurde still zu "fail".** `normalize_judge_result` defaultet ein
   fehlendes `verdict` auf `"fail"` — ein technischer Ausfall wurde zu einem inhaltlichen
   Urteil, ohne Spur im Log. Jetzt: Retry, dann expliziter Fehler.
4. **Kostenrechnung war unmöglich.** `usage_summary` las nur die Responses-API-Namen; für
   OpenRouter-Judges (`prompt_tokens`/`completion_tokens`) ging der Input/Output-Split
   verloren. Jetzt beide Namensschemata.

**Rückwirkung auf frühere Befunde (Korrektur):** Sämtliche DeepSeek-"Dissense" waren
Abschneide-Artefakte mit leerer Vote-Struktur — Köhl C-003, Schömig C-032 und zwei Splits in
Batch 1. DeepSeeks echte False-Fail-Rate auf Gold ist **0/274, nicht 0,7 %**; die
v2-Nachvalidierung liest sich korrekt als **274/274 einstimmig**. Ebenso war Deckers
vermeintlicher Gold-Knappheits-Fall C-042 ein Artefakt.

**Judge-Qualität, gemessen auf 274 Gold-Kriterien + 12 Mutanten (gefixter Harness):**

| Judge | False-Fails auf Gold | Mutanten-Erkennung |
| --- | --- | --- |
| luna | 0/274 | (Komiteemitglied, 12/12) |
| deepseek-v4-flash | 0/274 | (Komiteemitglied, 12/12) |
| gemini-3.6-flash | 0/274 | fängt alle 3 von glm übersehenen Fehler |
| glm-5.2 | 0/274 | **übersieht 3 von 12 Mutationen**, 2 Fehlsanktionen |

glm-5.2 ist auf Gold makellos, aber **nachsichtig**: Es liest Wohlwollen in Lücken hinein
(Allesch m3: hält den entfernten Klageabweisungsantrag für "unmissverständlich" enthalten).
Für die Tie-Breaker-Rolle, die definitionsgemäß die strittigen Fälle entscheidet, ist das die
gefährlichste Verzerrungsrichtung — sie triebe die Solver-Scores nach oben.

**Kosten pro Fall, gemessen (Köhl, 59 Kriterien, jeder Judge solo, keine Cache-Treffer):**

| Judge | Output/Kriterium | Cache-Trefferquote | $/Fall |
| --- | --- | --- | --- |
| gemini-3.6-flash | 1106 | 61 % | 0,992 |
| deepseek-v4-flash | 1446 | 91 % | 0,033 |
| glm-5.2 | 593 | 99 % | 0,141 |

DeepSeek braucht 31 % mehr Output-Tokens als Gemini (Thinking-Modell), bleibt durch den
42-fachen Preisunterschied beim Output dennoch 30× billiger. Die Preisliste allein hätte hier
in die Irre führen können — deshalb die Messung.

**Entscheidung Solver-Judging:** `configs/judge-committee-luna-deepseek-gemini-tiebreaker.json`
mit `--committee-tiebreaker`. Luna und DeepSeek sind Primärjudges, Gemini entscheidet nur den
Dissens. Das Ergebnis ist **mathematisch identisch** zur Mehrheit aus drei vollen Stimmen
(stimmen die Primärjudges überein, könnte die dritte die Mehrheit nicht kippen), kostet aber
statt 1,025 nur **0,136 USD pro Fall** — die gemessene Dissensrate auf echten Solver-Ausgaben
liegt bei 10,4 % (252/2416 Kriterien aus 60 Komiteeläufen).

**Entscheidung Rubrik-Kalibrierung:** bleibt beim v2-Komitee (luna/deepseek/gemini, alle
stimmen). Dort ist der Maßstab Einstimmigkeit, ein Tie-Breaker-Pfad existiert nicht, und ein
nachsichtiger Judge würde zu anspruchsvolle Kriterien durchwinken statt sie in die
Refine-Runde zu schicken.

**Welle 3, Batch 1 — Komitee-Abnahme bestanden** (v2-Komitee, gefixter Harness):
Decker 52/52, Gregor 48/48, Hasl-Kleiber 50/50 — jeweils all_pass und **einstimmig**, keine
Splits, keine unresolved. Offen bleibt die Mutantenprüfung des Batches.

## Nachtrag 2026-08-13 (3): Taskset-Tausch — ZJS-Fälle raus, drei Originalaufgaben rein

**Anlass:** Auf Nachfrage geprüft, warum das Set überhaupt drei ZJS-Referendarexamensklausuren
enthält. Befund: Zum Auswahlzeitpunkt (2026-08-10) bot das Quell-Repo nur zwölf echte bayerische
Zweitexamens-Aufgaben; die übrigen zehn der damals 22 Fälle sind acht Erstexamensaufgaben, dazu
Kahl/Pracht (im Titel Referendarexamensklausur, im Sachverhalt aber BW-Erstprüfung 2022) und Schaks
(„Original-Examensklausur" ohne Examensstufen-Angabe, reines Rechtsgutachten). Die ZJS-Fälle waren
also eine Notlösung, um auf 15 zu kommen.

**Neuer Befund:** Das Quell-Repo war seit dem Erstimport auf 27 Fälle gewachsen. Drei der fünf
neuen sind echte Zweitexamens-Aufgaben (Weber ZJS 2020/1 Aufgabe 10, Wolff ZJS 2021/2 Aufgabe 9,
Zöllner ZJS 2020/2 Aufgabe 9). Nachimport am 2026-08-13, Provenienz auf Commit `a44241b5` gehoben.

**Entscheidung (von Aaron freigegeben):** Tausch. Das Set besteht jetzt ausschließlich aus
amtlichen Originalaufgaben. Gewinn: echte Praxis-Arbeitsprodukte statt Universitätsgutachten,
Wegfall des höchsten Kontaminationsrisikos (ZJS Open Access + HuggingFace). Preis: Die drei einzigen
CC-BY-4.0-Fälle sind raus, die Publikation hängt damit vollständig an der Boorberg-Lizenzklärung —
die ohnehin für die zwölf übrigen Fälle nötig ist.

**Phase-A-Inventar der drei Neuzugänge** (Abschnitte 16–18 im Inventar): alle drei bestanden nach
Fixes, keine Blocker. Umgesetzt: Weber zwei Formfixes (Anlage-1-Überschrift datierte den Bescheid
auf den 28. statt 20. Januar 2020 — daran hängt der Fristenstrang; widersprüchlicher Einschub „wie
vorgesehen" im Tagesordnungssatz) plus Rechtsstand TA Luft 2002; Wolff Rechtsstand 22.11.2021 mit
Ausklammerung der PBefG-Novelle 2021 (Fachreview-Punkt); Zöllner Entfernung der
Hilfsgutachten-Klausel, die bei nur einem Deliverable zum Auslagern in eine nicht bewertete Datei
verleitet hätte.

**Zwei fallübergreifende Befunde:**

1. **Dokumenttyp-Erkennung ist robust gegen Dateinamens-Artefakte — belegt.** Wolffs Hauptprodukt
   heißt `gutachten-sut.md`, enthält aber ein Urteil („Im Namen des Volkes / **Urteil:** / I. Die
   Klage wird abgewiesen"). `classify_deliverables` vergab korrekt `gerichtliche_entscheidung`,
   orientierte sich also am Urteilskopf und am Bearbeitervermerk statt am Dateinamen. Damit ist der
   im Plan offen gelassene Fehlerpfad („aus Aufgabenstellung, Bearbeitervermerk und Dateiname
   abgeleitet") empirisch geschlossen.
2. **Die Autorenfußnote steht korpusweit im Aufgabenmaterial.** Alle geprüften Fälle enthalten in
   `documents/sachverhalt.md` eine verwaiste Definition `[^*]: Verf. ist …` ohne Referenz im
   Fließtext — Import-Artefakt des Zeitschriften-Sternchens, keine Besonderheit einzelner Fälle. Für
   die Leakage-Betrachtung gleichwohl relevant, weil der Verfassername der publizierten Lösung dem
   Solver vorliegt. Entscheidung über Entfernen sollte einheitlich für den Gesamtbestand fallen.

**Housekeeping-Fund:** Sechs bereits generierten Fällen fehlte die kanonische `evals/rubric.json`,
die `validate_task_dir` im Solver-Runner verlangt (nur Gregor und Köhl_2024 hatten sie, weil sie bei
Korrekturen mitsynchronisiert wurden). Das wäre beim ersten Solver-Lauf als Abbruch aufgeschlagen;
für alle zwölf generierten Fälle nachgezogen.
