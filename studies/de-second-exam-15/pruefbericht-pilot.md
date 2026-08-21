# Prüfbericht Pilotrubriken second-exam-pilot-v1: Positiv- und Negativprüfung

Stand: 2026-08-11. Judge: gpt-5.5, 1 Stimme, `--parallel 6`; Positivläufe mit `--style-evaluation`
(kombinierter Content+Stil-Call mit dokumenttypbasiertem Routing über die eingefrorenen
`deliverable_profiles`). Submissions und Ergebnisse unter `positivpruefung/` und `negativpruefung/`;
Soll-Ist-Abgleich reproduzierbar über `auswertung_negativpruefung.py`.

## Positivprüfung (Musterlösung als Verzeichnis-Abgabe durch die echte Pipeline)

| Fall | Content | Stil | Befund |
| --- | --- | --- | --- |
| Allesch | **67/67, all_pass** | 45/47 (96 %) | fehlerfrei |
| Kaess | 44/45 | 27/31 (87 %) | 1 Einzelstimmen-Fail (C-034), behoben |
| Köhl | 60/61 | 47/50 (94 %) | 1 Einzelstimmen-Fail (C-033, zunächst Judge-Timeout), behoben |

- **Stil-Routing live verifiziert:** Die Judge-Begründungen wenden nachweislich je Datei den
  richtigen Maßstab an („adressatengerechter Beratungsstil" im Mandantenschreiben, „anwaltlicher
  Schriftsatzstil" in Klageerwiderung/Zulassungsschriftsatz, Gutachtenstil im Hilfsgutachten,
  Urteilsstil im Urteil). Keine einzige Fundort- oder Routing-Fehlbewertung.
- **Die zwei Content-Fails** waren beide vom Typ „Kriterium verlangt mehr Begründung, als das Gold
  an dieser Stelle liefert" — das Komitee (Luna/Terra/Gemini) hatte beide 3/3 bestanden, der
  gpt-5.5-Einzelrichter las strenger. Beide Kriterien wurden dokumentiert auf Gold-Niveau
  abgeschwächt (`manual_edits`): Kaess C-034, Köhl C-033.
- **Stil-Fails** betreffen ausschließlich Ein-Satz-Feststellungen der Musterlösungen selbst
  (z. B. „ist gemäß § 45 VwGO zuständig", „Eine Anhörung ist erfolgt") — ehrliche Urteile der
  Content/Stil-Trennung, keine Routing-Fehler. Fachreview-Frage: sollen reine
  Feststellungs-Kriterien überhaupt stilpflichtig getaggt sein?
- **Empfehlung:** Die formale Abnahme-Positivprüfung vor dem Freeze mit 3 Stimmen bzw. dem
  Komitee wiederholen; 1 Stimme genügt nur für Pipeline-Smokes.

## Negativprüfung (Phase H, 8 deterministische Mutanten)

Ergebnis: **8/8 OK** — jede Mutation scheitert an genau den vorgesehenen Kriterien, ohne
sachfremde Folgesanktionen (Abgleich gegen `expectations.json`).

| Mutant | Getestete Mechanik | Ergebnis |
| --- | --- | --- |
| m1/m5 Hilfsgutachten fehlt | Vollständigkeitskriterium + reguläres Failen dateigebundener Kriterien (Regel 6) | exakt die HG-Kriterien failen, sonst nichts |
| m2 Ossram in falscher Datei | **Fundort-Beschränkung** (Asal-Muster „falscher Prüfungsort") | alle 6 Ossram-Kriterien failen trotz inhaltlich richtigem Text |
| m3/m6 Antrag fehlt | dokumenttypische Formkriterien (★★★) | genau C-005 bzw. C-001 |
| m4 Mandantenschreiben als Gutachten | Dokumenttyp-/Adressaten-Kriterien + Oder-Fundort-Semantik | Typ- und Substanzkriterien failen; C-015 belegt den intakten Oder-Pfad über die KE |
| m7 Tenor-Widerspruch | Widerspruchsfreiheit Tenor↔Gründe | genau C-006 |
| m8 Begründung entfernt | „Ergebnis richtig, tragende Begründung fehlt" | genau C-035 |

Iterationen (transparent dokumentiert):

- m4: Erwartungskatalog präzisiert — acht Oder-Kriterien, deren Gold-Substanz nur im
  Mandantenschreiben stand, failen mutationsbedingt korrekt (`expected_substance_loss`).
- m6: Mutant geschärft — der erste Schnitt ließ den Satz „Hiergegen richtet sich der Antrag auf
  Zulassung der Berufung" stehen, den der Judge nachvollziehbar als Antrag wertete.

## Judge-Stabilität (Einzelstimme)

Zwei Flips ohne Mutationsbezug in den Mutantenläufen (Kaess C-039, C-023) plus die zwei
Gold-Fails: gemessene Einzelstimmen-Varianz ~1–2 Kriterien pro Lauf, konsistent mit der
Juli-Messung (±2/48). Für gewertete Läufe 3 Stimmen bzw. `--adaptive` verwenden;
C-039 (langes Alternativpfad-Kriterium) auf die Stabilitäts-Beobachtungsliste.

## Noch offene Phase-H-Mutationstypen

Drei Mutationstypen brauchen LLM-Umschreibungen ganzer Dokumente und stehen noch aus:
gerichtliche Entscheidung vollständig im Gutachtenstil (testet primär den separaten Stilscore,
der über die Stilkalibrierungs-Fixture bereits abgedeckt ist), vertretbare Alternativlösung als
durchgängiger Lösungsweg, derselbe Gedanke doppelt in Haupt- und Hilfsdokument (bei Boolean-
Kriterien konstruktionsbedingt ohne Doppelkredit; Test dokumentiert den Ist-Zustand).

## Nachtrag 2026-08-12: Review-Edits und Revalidierung v2

Nach dem externen Review (6,5/10) wurden 8 Kriterien entfernt bzw. zusammengeführt
(Details im Reviewprotokoll; neue Zahlen: Allesch 64, Kaess 42, Köhl 59) und die
Positivläufe wiederholt.

**Betriebsbefund:** Die Vote-Caches lagen in `/private/tmp` und gingen mit dem Reboot
verloren — alle Kriterien wurden frisch gejudgt statt nur der geänderten. Konsequenz für
formale Läufe: Caches an einen persistenten Ort legen. Der Frischlauf würfelte die
gemessene Einzelstimmen-Varianz neu und deckte dabei drei weitere Kriterien der bekannten
Kategorie „verlangt mehr als die Gold-Passage an dieser Stelle liefert" auf, die auf
Gold-Niveau geöffnet wurden: Allesch C-040 (Ordnungsruf-Element in der
Zwangsmittel-Auswahl), Kaess C-023 (Muster C-022, zweifacher Frischlauf-Fail), Köhl C-044
(Aufzählungszwang der Vormaßnahmen).

**Finale Bestätigung (2026-08-12):** Allesch **64/64**, Kaess **42/42**, Köhl **59/59** —
`all_pass` bei allen drei Rubriken. Kaess-Mutant m6 wurde gegen die aktuelle Rubrik
nachgejudgt, nachdem der alte Lauf ein Altdaten-Artefakt zeigte (C-034-Fail aus der
Vor-Öffnungs-Fassung).

**Solver-Läufe (Review Punkt 7):** Zwei Codex-Arme (web / no-web) über die drei Piloten
gestartet (`runs/codex-web-pilot3/`, `runs/codex-no-web-pilot3/`); die Baseline unterstützt
nur Einzeldatei-Tasks. Für den Taskset-Loader wurde die Pilot-Rubrik je Fall zusätzlich als
`evals/rubric.json` abgelegt (identische Kopie von `rubric.second-exam-pilot-v1.json`,
Stand nach den Review-Edits).

## Solver-Läufe über die Piloten (Review Punkt 7, 2026-08-12)

Zwei Codex-Arme (gpt-5.5, konfigurierter Default; web / no-web), gejudgt mit gpt-5.5,
1 Stimme, inkl. Stilbewertung. Alle sechs Abgaben waren vollständig (jede Pflichtdatei,
korrekte Namen, keine überzähligen Dateien) — der Mehrdatei-Runner ist damit im Ernstfall
verifiziert.

| Fall | Arm | Content | Gewichtet | Stil | ★★★-Kern |
| --- | --- | --- | --- | --- | --- |
| Allesch | web | 45/64 (70 %) | 72 % | 36/46 | 7/9 |
| Allesch | no-web | 42/64 (66 %) | 69 % | 33/46 | 7/9 |
| Kaess | web | 30/42 (71 %) | 73 % | 23/30 | 5/5 |
| Kaess | no-web | 29/42 (69 %) | 69 % | 23/30 | 4/5 |
| Köhl | web | 37/59 (63 %) | 70 % | 32/49 | 7/8 |
| Köhl | no-web | 43/59 (73 %) | 79 % | 37/49 | 7/8 |

Befunde:

- **Die Rubriken diskriminieren:** 63–73 % Content, weder Decke noch Boden; all_pass
  erwartungsgemäß nirgends erreicht.
- **★★★-Kern weit überwiegend bestanden (38/44 über alle Läufe):** Das Modell gewinnt die
  ergebnistragenden Weichen und verliert in der Breite (★1/★2-Detailkriterien) — ein
  examensplausibles Profil. Die Review-Sorge „Kürze und Schwerpunktsetzung werden bestraft"
  zeigt kein Totalausfall-Muster; der gewichtete Score liegt konsistent über dem ungewichteten.
- **Stil beim Urteilsfall am schwächsten** (Köhl 65–76 %): passt zum bekannten Muster
  „Feststellen statt Begründen"; das dokumenttypbasierte Routing liefert hier erstmals einen
  differenzierten Stilbefund je Arbeitsprodukt.
- **Websuche ohne klaren Vorteil** (Mittel web ≈ 68 %, no-web ≈ 69 %; Köhl sogar deutlich
  besser ohne Web): bei kodifiziertem bayerischem Landesrecht plausibel, aber n=3 mit
  1 Judge-Stimme — keine belastbare Aussage, nur eine Beobachtung für die Studienplanung.

Damit sind alle Punkte des externen Reviews vom 2026-08-12 abgearbeitet oder begründet
abweichend entschieden (Score: Aarons Entscheidung pro All-Pass-Feld + %-Reporting;
deliverable_profiles bleiben gemäß Plan).

## Risikowelle (Welle 2: Oertel 104 ff., Schömig — 2026-08-12)

Generierung mit dem verbesserten second-exam-Promptsatz (inkl. Gold-Knappheits-Regel),
Komitee-Kalibrierung, Suffix `second-exam-v1`.

| Fall | Kriterien | Kalibrierung | Komitee-Positivprüfung | Mutanten |
| --- | --- | --- | --- | --- |
| Oertel | 43 (nach HG-Fix) | 0 Drops, 0 flaky, 6 Reparaturen R1 | **43/43 all_pass, einstimmig, auf Anhieb** | m9 ✓, m10 ✓ |
| Schömig | 66 (nach HG-Fix) | 0 Drops, 0 flaky, 2 Reparaturen R1 | **66/66 all_pass, einstimmig, auf Anhieb** | m11 ✓, m12 ✓ |

Befunde:

- **Die Gold-Knappheits-Regel wirkt messbar:** Reparaturquote in Kalibrierungsrunde 1 sank von
  12/9/3 (Piloten) auf 6/2; erstmals bestehen Rubriken die Komitee-Positivprüfung ohne eine
  einzige inhaltliche Nachbesserung.
- **Beide Risiko-Hypothesen entschärft:** Oertels Binärdatei (Lageplan) läuft als Platzhalter
  durch die gesamte Pipeline (kein Kriterium stützt sich auf Bildinformation); die
  Rechtsstand-Fixierung (BayBO n.F.) steht im Task-Prompt und die Kriterien zitieren konsistent n.F.
- **„Weg frei, Ergebnis fix"-Alternativen sauber kodiert** (Schömig C-043-S1: beide
  § 201-Auslegungen; C-038: beide Zwangsgeld-Begründungswege enden zwingend bei der
  Rechtswidrigkeit).
- **Kostenquoten-Prüfung validiert:** Schömig tenoriert die Kostenquote selbst (nicht erlassen,
  anders als Köhl); Mutant m11 (Vollabweisung bei stehengelassener 3/4-Quote) ließ neben den
  Tenor-Kriterien auch C-011 (Kostenquote) korrekt anschlagen.
- **HG-Politik nachgeschärft:** Die Generierung reproduzierte zunächst HG-Existenzkriterien
  (Promptsatz war noch nicht auf die Review-Entscheidung angepasst) — post-hoc entfernt,
  Promptsatz korrigiert. Die m10/m12-Mutanten deckten zudem einen Design-Fehler des
  Weglass-Freibriefs auf: konditional formuliert („…weil die Fragen anderswo behandelt werden")
  ist er für den fundortbeschränkten Judge unentscheidbar → unkonditionalisiert
  (fehlend/leer/minimal = ERFÜLLT), im Promptsatz für Welle 3 verankert, Gold-Recheck 3/3.
- Endstand Negativprüfung: **12/12 Mutanten über beide Wellen treffen exakt ihre Ziele**
  („GESAMT: alle Mutanten wie erwartet").

## Negativprüfung Welle 3 Batch 1 (2026-08-13, Mutanten m13–m18)

Sechs deterministische Mutanten, zwei je Fall, Referenz-Judge gpt-5.5 wie bei m1–m12.
Ergebnis nach einer Rubrikkorrektur: **18/18 Mutanten über alle drei Wellen treffen exakt
ihre Ziele** („GESAMT: alle Mutanten wie erwartet").

| Mutant | Getestete Mechanik | Ergebnis |
| --- | --- | --- |
| decker-m13-tenor-widerspruch | Tenor weist ab, Gründe bleiben stattgebend | C-004 fällt, Kostenkriterien unberührt |
| decker-m14-hilfsgutachten-fehlt | HG geleert | keine Existenzsanktion; C-008 (Methode) passt nach Waiver-Regel |
| gregor-m15-tenor-widerspruch | Vollabweisung bei teilstattgebenden Gründen | C-004 fällt |
| gregor-m16-hilfsgutachten-fehlt | HG geleert (10 HG-only-Kriterien) | 11 Kriterien fallen als echter Substanzverlust; C-048 passt |
| hasl-kleiber-m17-ohne-antraege | Antragsblock entfernt | C-006, C-007, C-008 fallen |
| hasl-kleiber-m18-bauherr-in-falscher-datei | Inhalt in die unzulässige Datei verschoben | C-016 fällt |

**Zwei neue Testmechaniken gegenüber den Wellen 1 und 2:**

- **m16** ist der erste Mutant an einem materiell tragenden Hilfsgutachten (Gregor hat als
  einziger Fall 10 HG-exklusive Kriterien). Er zeigt, dass OR-Fundortlisten den
  Substanzverlust nicht kaschieren: C-009, C-032 und C-033 sind für beide Dateien zugelassen,
  die Entscheidung lässt die Fragen aber ausdrücklich dahinstehen, sodass ihr Ausfall bei
  geleertem HG korrekt ist.
- **m18** prüft die Fundort-Restriktion in Reinform: Der Text zur Bauherreneigenschaft ist
  vollständig vorhanden, nur im Mandantenschreiben statt im Schriftsatz. C-016 fällt — die
  Location-Beschränkung wirkt.

**Rubrikfund durch den Mutantentest (Gregor C-017 „Klagebefugnis hinsichtlich Ziffer 1"):**
Im ersten m16-Lauf fiel C-017 gegen die **unveränderte** Entscheidungsdatei. Der Recheck mit
drei Stimmen ergab 3:0 fail — also keine Judge-Varianz, sondern ein zu enger Fundort: Das
Kriterium verlangte die Garagenblockade-Begründung im Klagebefugnis-Abschnitt, während das
Gold sie in der Begründetheit behandelt und der PRAXISTIPP des Falls die Verortung
ausdrücklich freigibt. Die Komitee-Positivprüfung hatte C-017 durchgewunken (48/48), der
strengere gpt-5.5 nicht — der Mutantentest hat den Defekt also gefunden, den der Positivlauf
verfehlte. C-017 wurde auf Gold-Niveau geöffnet (manual_edits dokumentiert), Rechecks: Gold
3/3 pass, Mutant 3/3 pass. Beide Gregor-Mutanten wurden anschließend gegen die geänderte
Rubrik neu bewertet.

Lehre: Der Positivlauf allein reicht als Abnahme nicht aus. Erst die Kombination aus
Komitee-Positivprüfung und Mutanten deckt zu eng verortete Kriterien auf.

## Negativprüfung Welle 3 Batch 2 (2026-08-13, Mutanten m19–m26)

Acht Mutanten, zwei je Fall, Referenz-Judge gpt-5.5. Ergebnis nach zwei Rubrikkorrekturen und
einer Korrektur eigener Erwartungsdeklarationen: **26/26 Mutanten über alle Wellen treffen
exakt ihre Ziele.**

| Mutant | Getestete Mechanik | Ergebnis |
| --- | --- | --- |
| kaess-ex2-m19 | Feststellungstenor I ins Gegenteil verkehrt | C-005 fällt |
| kaess-ex2-m20 | HG geleert | keine Existenzsanktion, C-009 passt |
| koehl-2024-m21 | Verweisungsziffer des Hilfsantrags entfernt | C-006 und C-007 fallen (nach Korrektur) |
| koehl-2024-m22 | HG geleert | C-041 und C-043 fallen als Substanzverlust, C-004 passt |
| oertel-537-m23 | Tenor abweisend bei stattgebenden Gründen | C-004 und C-005 fallen |
| oertel-537-m24 | HG geleert | C-003 passt (Test des entkonditionalisierten Waivers), C-008–C-015 Substanzverlust |
| possart-m25 | Gemischter Eiltenor durch Gesamtablehnung ersetzt | C-005 fällt |
| possart-m26 | HG geleert | 9 OR-Kriterien Substanzverlust, C-004 passt |

**Zwei Rubrikfunde durch den Mutantentest (Köhl_BayVBl-2024):**

- **C-014 „Richtige Antragsgegnerin"** fiel bei *unveränderter* Entscheidungsdatei. Recheck
  gegen Gold mit drei Stimmen: 1:2 fail. Ursache war Gold-Knappheit — das Kriterium verlangte
  die namentliche Nennung der „Stadt Spielberg" als Antragsgegnerin, während das Gold an
  dieser Prüfungsstelle nur „gegen den richtigen Antragsgegner gerichtet" sagt; der Name fällt
  im ganzen Dokument genau einmal, und zwar zum Stadtratsbeschluss. Das Rubrum ist zudem
  erlassen. Auf Gold-Niveau geöffnet.
- **C-006 „Tenorielle Zuständigkeitsentscheidung"** blieb bei entfernter Verweisungsziffer
  unbeanstandet, weil die PASS-Seite die Aussage auch in den Gründen akzeptierte — obwohl
  Titel und Dokumenttyp `gerichtliche_entscheidung` die Tenorierung prüfen und das
  Schwesterkriterium C-007 sie verlangt. Auf den Tenor beschränkt.

Nach beiden Korrekturen: Köhl_2024 Positivlauf 43/43 einstimmig, m21 trifft C-006 und C-007.

**Drei eigene Fehldeklarationen, keine Rubrikfehler** (dokumentiert, weil sie ein
wiederkehrendes Risiko zeigen): Bei possart-m25 hatte ich C-005 und C-006 vertauscht —
Possarts Tenorziffer I entspricht **Antrag II**, „Im Übrigen abgelehnt" deckt die Anträge I
und III. Genau die Ziffernverwechslung, vor der das Inventar für diesen Fall gewarnt hatte.
Bei oertel-537-m24, possart-m26 und koehl-2024-m22 hatte ich den Substanzverlust der
OR-Kriterien zu niedrig angesetzt: Rechtsweg, Zuständigkeit, Klagefrist, Beteiligte, Beiladung
und Sofortvollzug sind zwar für beide Dateien zugelassen, stehen im Gold aber ausschließlich
im Hilfsgutachten (Haupttext: 0 Treffer). Die Rubriken verhielten sich korrekt.

Lehre: Die Erwartungsdeklaration muss aus dem Gold-Text belegt werden, nicht aus der
Kriterienliste geschlossen. Ein „sachfremder Fail" im Auswerter ist zunächst eine Frage an die
Deklaration, erst danach an die Rubrik.

## Negativprüfung Welle 3 Batch 3 (2026-08-13, Mutanten m27–m32)

Sechs Mutanten. Endstand nach einem Harness-Fix, einer Rubrikkorrektur und einer
Mutantenschärfung: **32/32 Mutanten über alle Wellen treffen exakt ihre Ziele.**

| Mutant | Getestete Mechanik | Ergebnis |
| --- | --- | --- |
| wolff-m27 | Tenor verpflichtet statt abzuweisen | C-005 fällt |
| wolff-m28 | HG geleert | C-048/049/052 Substanzverlust, C-004 passt |
| weber-m29 | Antrag auf mündliche Verhandlung entfernt | C-004 fällt (nach Schärfung) |
| weber-m30 | HG geleert | keine Sanktion, C-007 passt |
| zoellner-m31 | Bestimmter Eilantrag entfernt | C-006 fällt |
| **zoellner-m32** | **Praxisformat zu Gutachten gewandelt** | **fünf Formkriterien fallen, alle materiellen halten** |

**m32 ist der bisher stärkste Nachweis für die Praxisform-Messung.** Entfernt wurden Absender,
Adressat, Rubrum, Vollmachtsanzeige, Antrag, Unterschrift und Anlagenvermerk; der anwaltliche
Schlusssatz wurde in eine gutachterliche Ergebnisfeststellung gewandelt. Die juristische
Argumentation blieb Wort für Wort erhalten (41,5 von 42,9 kB). Es fielen C-001 (Vollständigkeit
des anwaltlichen Eilschriftsatzes), C-002 (Adressierung), C-004 (Fraktion als Antragsgegnerin),
C-006 (bestimmter Antrag) und C-008 (anwaltliche Antragstellerperspektive) — sämtliche
materiellen Kriterien blieben erfüllt. Damit ist belegt, dass die Rubriken im
Zweitexamens-Set die Dokumentform tatsächlich messen und nicht nur den Inhalt.

**Harness-Fund (gravierendster der Serie): Audit-Flip bei Alternativ-Zweigen.**
`normalize_judge_result` erzwang ein „fail", sobald **ein** `component_check` unerfüllt war. Für
kumulative Kriterien ist das richtig; die Rubrik-Prompts kodieren zulässige Alternativen aber als
zweiten PASS-Zweig („ERFÜLLT, wenn A. **ERFÜLLT auch**, wenn B."). Zerlegt ein Judge beide Zweige
in Komponenten, ist der nicht gewählte zwangsläufig unerfüllt — das Kriterium wurde gegen das
eigene Urteil des Judges auf „fail" gedreht. Aufgefallen an Wolff m27: C-004 fiel bei
byte-identischer Hilfsgutachten-Datei, während die Judge-Begründung ausdrücklich die PASS-Seite
bejahte. Betroffen sind **44 der 751 Kriterien (6 %)** — systematisch die Waiver- und
Vertretbarkeits-Konstruktionen, also genau die Stellen, an denen der Benchmark faire
Alternativwege zulassen soll. Der Fehler feuerte nur, wenn ein Judge die Zweige zerlegte, und
erschien deshalb als sporadische Varianz.

Fix in `evaluation/run.py`: Enthält die PASS-Seite Alternativ-Marker („ERFÜLLT auch", „Ebenfalls
ERFÜLLT", „Alternativ", plus englische Entsprechungen), zählt ein unerfüllter Komponenten-Check
nur dann als Widerspruch, wenn **kein einziger** erfüllt ist; für kumulative Kriterien bleibt die
strenge Regel. Verifiziert an vier Konstellationen.

**Rückwirkende Prüfung der Wellen 1 und 2: nicht betroffen.** Der Bug hinterlässt eine eindeutige
Signatur (Fail auf einem Alternativ-Kriterium mit gemischten Komponenten-Checks). Ein Scan über
sämtliche Score-Dateien beider Prüfungsarten fand **drei betroffene Stimmen, alle in Batch 3**.
Die Wellen-1/2-Läufe speichern `component_checks` lückenlos (67/67, 61/61, 66/66 Stimmen), der
Nullbefund ist also belastbar. Grund: In den Wellen 1 und 2 sind alle Positivläufe all_pass, und
in ihren Mutantenläufen zerlegte kein Judge die Alternativ-Zweige.

**Rubrikfund (Zöllner C-002 „Adressierung"):** Der m32-Mutant passierte das Kriterium, weil der
Gutachtentext das VG Ansbach noch in der Zuständigkeitsprüfung erwähnt — dasselbe Muster wie bei
Köhl C-006. Auf die tatsächliche Adressierung im Schriftsatzkopf verengt; Recheck gegen Gold 3/3.

**Eigener Fehler (Weber m29):** Der erste Schnitt entfernte nur den förmlichen Antragssatz, während
die Begründung weiterhin feststellte „Der Antrag auf Durchführung der mündlichen Verhandlung ist
zulässig". C-004 passierte damit zu Recht; der Mutant war zu schwach (Präzedenz kaess-m6). Nach der
Schärfung fällt C-004. Bemerkenswert: Vor dem Harness-Fix hatte der Audit-Flip C-004 fälschlich auf
„fail" gedreht, sodass der zu schwache Mutant zufällig richtig aussah — ein Fehler hatte den
anderen verdeckt.
