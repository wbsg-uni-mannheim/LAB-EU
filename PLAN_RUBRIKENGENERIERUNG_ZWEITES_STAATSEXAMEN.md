# Plan: Rubrikengenerierung für 15 Fälle des Zweiten Staatsexamens

## 1. Ziel und Ausgangslage

Für die bereits ausgewählten 15 echten Fälle des Zweiten Staatsexamens bzw. ausdrücklich als Referendarexamensfälle veröffentlichten Fälle sollen belastbare Bewertungsrubriken erzeugt werden. Die Rubriken müssen nicht nur die materiell-rechtliche Lösung abbilden, sondern auch die im Zweiten Staatsexamen verlangten praktischen Arbeitsprodukte korrekt bewerten.

Der aktive Fallsatz ist:

- `tasksets/de-second-exam-15.jsonl`
- 12 offizielle bayerische Assessorexamensfälle
- 3 ausdrücklich veröffentlichte Referendarexamensfälle
- derzeit ausschließlich Öffentliches Recht, mit einem Schwerpunkt im Bau- und Verwaltungsrecht
- 12 Fälle verlangen mehrere Abgabedokumente; 3 Fälle verlangen nur ein Arbeitsergebnis

Die bestehende Pipeline der 45 Fälle kann als technische Grundlage weiterverwendet werden. Sie darf für das Zweite Staatsexamen aber nicht unverändert übernommen werden.

## 2. Wichtigste methodische Änderung

Es soll **nicht pauschal auf Gutachtenstil umgestellt** werden. Der richtige Darstellungsstil hängt vom jeweiligen Arbeitsprodukt ab:

| Arbeitsprodukt | Primär zu bewertender Stil |
| --- | --- |
| Hilfsgutachten oder interne rechtliche Prüfung | Gutachtenstil |
| Urteil, Beschluss oder gerichtliche Entscheidung | Entscheidungs-, Urteils- bzw. Beschlussstil |
| Klageerwiderung, Berufungsbegründung oder sonstiger Schriftsatz | anwaltlich-parteibezogener und prozesszweckmäßiger Schriftsatzstil |
| Mandanten- oder Behördenschreiben | adressatengerechte, handlungsorientierte Beratung |
| Tenor, Anträge oder Verfügungen | knappe, formgerechte und vollstreckungsfähige Fassung |

Materiell-rechtliche Richtigkeit und methodisch-formale Qualität müssen deshalb getrennt bewertet werden.

## 3. Konkrete Lücken der derzeitigen Pipeline

Vor der Massengenerierung müssen folgende Punkte gelöst werden:

1. Der bisherige Codex-Taskset-Runner akzeptiert derzeit nur genau ein Abgabedokument. Für 12 der 15 Fälle muss er mehrere Dateien erzeugen und einlesen können.
2. Die Stilbewertung ist derzeit fest auf den Gutachtenstil ausgerichtet. Sie muss abhängig vom Dokumenttyp geroutet werden.
3. Die Rubrikengenerierung erkennt zwar mehrere Lösungsdateien, kennt aber noch keine explizite Zuordnung von Kriterien zu einzelnen Arbeitsprodukten.
4. Derselbe rechtliche Gesichtspunkt darf nicht mehrfach bepunktet werden, nur weil er in Hauptdokument und Hilfsgutachten vorkommt.
5. Das vollständige Vorliegen aller verlangten Dateien muss gesondert geprüft werden.
6. Die Lösungsskizzen und Quellen müssen vor der Generierung auf Vollständigkeit, Aktualität und zulässige Lösungsalternativen geprüft werden.
7. Die in die Generierung eingebaute Kalibrierung bewertet die Musterlösung bisher als einen zusammenhängenden Gesamttext über alle Lösungsdateien. Sie muss die Fundort-Beschränkung einzelner Kriterien genauso anwenden wie die spätere Evaluation.

## 4. Phase A: Fall- und Quelleninventar einfrieren

Für alle 15 Fälle wird zunächst ein verbindliches Inventar erstellt. Je Fall sind zu dokumentieren:

- Herkunft, Examensbezug und Veröffentlichungsjahr
- Rechtsgebiet und prozessuale Situation
- Rolle des Bearbeiters, etwa Gericht, Behörde oder Rechtsanwalt
- alle Sachverhalts- und Anlagendateien
- alle Lösungsteile
- alle ausdrücklich verlangten Abgabedokumente
- zulässige oder notwendige Hilfsgutachten
- maßgeblicher Rechtsstand
- bekannte vertretbare Alternativlösungen
- Lizenz- bzw. Freigabestatus von Sachverhalt und Lösung

### Rechtsstandsregel

Maßgeblich ist der Rechtsstand der Musterlösung. Die Rubrik bewertet gegen diesen Stand, und der fixierte Rechtsstand wird dem Bearbeiter in der Aufgabe ausdrücklich mitgeteilt, damit aktuelle Gesetzesfassungen nicht zu unfairen Fails führen. Normen, die sich seit der Veröffentlichung geändert haben, werden im Inventar vermerkt; die betroffenen Kriterien gehen mit diesem Vermerk in das juristische Fachreview. Das ist nicht theoretisch: Allesch ist eine Examensaufgabe aus 2019/2.

### Abnahmebedingung

Kein Fall geht in die Generierung, solange eine zentrale Anlage, ein Lösungsteil oder der verlangte Rechtsstand unklar ist. Ein offener Lizenzstatus blockiert die Generierung nicht, wird aber im Inventar als Publikationsblocker geführt (derzeit z. B. Allesch: „license type pending“).

## 5. Phase B: Vorhandenes Aufgabenschema weiterverwenden

Es werden **keine neuen Pflichtfelder** eingeführt. Die vorhandenen Angaben reichen aus:

- `deliverables` nennt die verlangten Dateien.
- Aufgabenstellung und Bearbeitervermerk bestimmen Rolle, Adressat und Dokumenttyp.
- Die Lösung zeigt den erwarteten Aufbau und die zulässigen Lösungswege.

Dokumenttyp und passender Stil werden bei der Rubrikengenerierung aus diesen vorhandenen Quellen abgeleitet und je Abgabedatei im Rubrik-Artefakt eingefroren (siehe Phase E). Nur wenn die Ableitung bei einem konkreten Fall tatsächlich nicht eindeutig möglich ist, wird der Fall manuell korrigiert. Dafür wird kein neues allgemeines Schema gebaut.

## 6. Phase C: Rubrikenschema für das Zweite Staatsexamen definieren

Jedes Kriterium soll weiterhin atomar, beobachtbar und eindeutig bepunktbar sein. Bei Mehrdokumentfällen wird lediglich das bereits vorhandene Feld `deliverables` genutzt, um anzugeben, in welchen Dateien das Kriterium erfüllt werden darf. Die Liste ist eine Oder-Liste zulässiger Fundorte: Evidenz zählt nur aus diesen Dateien, und bei mehreren Einträgen genügt einer. Verlangt die Aufgabe denselben Gesichtspunkt in mehreren Dokumenten als jeweils eigenständige Leistung – etwa formgerechter Antrag im Schriftsatz und verständliche Erklärung desselben Punkts im Mandantenschreiben –, erhält jedes Dokument ein eigenes Kriterium mit eigenem Fundort (Regel 4). Ein einzelnes Kriterium mit Und-Semantik über mehrere Dateien gibt es nicht: Es wäre nicht mehr atomar bepunktbar, und die Evaluation konkateniert die erlaubten Dateien ohnehin zu einem Text, kann also das Vorkommen in jeder einzelnen Datei nicht prüfen.

Weitere Felder wie `location_requirement`, `issue_group` oder `criterion_type` sind nicht erforderlich. Deduplizierung und Gewichtung werden bei der Generierung bzw. Kalibrierung erledigt und nicht als neue Metadatenschicht im Taskset gespeichert. Einzige Ausnahme: Der je Abgabedatei abgeleitete Dokumenttyp wird im generierten Rubrik-Artefakt abgelegt (Phase E), damit die Evaluation deterministisch bleibt und nichts zur Laufzeit neu klassifiziert. Das Taskset-Schema bleibt unverändert.

### Regeln für Mehrdokumentfälle

1. Jede Musterlösungsdatei wird zunächst getrennt in mögliche Kriterien zerlegt.
2. Danach erfolgt eine fallweite Deduplizierung über alle Dokumente. Sie nimmt der dokumentweisen Prüfung nichts weg: Zusammengelegt werden ausschließlich inhaltsgleiche Kandidaten desselben Gesichtspunkts, deren zulässige Fundorte dabei vereinigt werden. Eigenständige Leistungen je Dokument (Regel 4) bleiben getrennte Kriterien, und konjunktive Sammelkriterien sind verboten. Ohne diesen Schritt wäre Regel 3 nicht umsetzbar, weil derselbe Gesichtspunkt aus Hauptdokument und Hilfsgutachten doppelt bepunktet würde. 
3. Ein Problem wird grundsätzlich nur einmal inhaltlich bepunktet.
4. Eine zusätzliche Bewertung an anderer Stelle ist nur zulässig, wenn dort eine eigenständige Leistung verlangt wird, etwa ein formgerechter Antrag oder eine adressatengerechte Erklärung.
5. Ist ein Gesichtspunkt laut Aufgabe wahlweise im Hauptprodukt oder Hilfsgutachten zulässig, darf die Rubrik keinen einzigen Fundort erzwingen.
6. Fehlt eine gesamte Pflichtdatei, failen alle ausschließlich auf diese Datei beschränkten Kriterien regulär. Das ist examensrealistisch und keine künstliche Vervielfachung. Zusätzlich scheitert ein eigenes Vollständigkeitskriterium, und die Auswertung weist getrennt aus, welcher Anteil der Fails allein auf der fehlenden Datei beruht, damit Inhalts- und Vollständigkeitsfehler unterscheidbar bleiben. Verboten bleibt nur die künstliche Vervielfachung desselben Grundfehlers, etwa zusätzliche Folgefehler-Sanktionen in anderen Dateien.
7. Tenor, Anträge, Begründung und Ergebnis müssen untereinander widerspruchsfrei sein.

## 7. Phase D: Generierungsprompts anpassen

Für das Zweite Staatsexamen wird ein eigener, versionierter Promptsatz angelegt – abgeleitet von den bestehenden Prompts in `prompts/rubric_generation/`, etwa als eigenes Unterverzeichnis, das `generate_rubric.py` per Flag auswählt. Die Prompts der bisherigen Fälle bleiben unverändert, aus zwei Gründen:

1. Die vorhandenen Rubriken sind mit ihren Promptversionen eingefroren. Promptänderungen machen die Step-Cache-Keys stale; ein späterer Re-Run eines alten Falls würde still und teuer komplett neu generieren statt aus dem Cache zu lesen (dieser Vorfall ist bereits einmal passiert).
2. Ein-Dokument-Gutachtenfälle brauchen die Mehrdokument-Anweisungen nicht und bekämen nur zusätzliches Prompt-Rauschen.

Verbesserungen, die beiden Prompt-Sätzen nützen, werden später bewusst und einzeln zurückportiert. Der neue Promptsatz enthält zusätzlich folgende Anweisungen:

- Rolle und Arbeitsauftrag aus dem Sachverhalt bestimmen
- verlangte Dokumenttypen vollständig erfassen
- Kriterien dokumentbezogen erzeugen
- materielles Recht von Darstellungsstil und Formalia trennen
- prozessuale Zweckmäßigkeit ausdrücklich berücksichtigen
- vertretbare Alternativlösungen positiv zulassen
- keine Doppelbepunktung über mehrere Dateien
- keine bloßen Schlagwortkriterien ohne nachprüfbare Leistung
- keine übermäßige Zersplitterung eines einzigen Fehlers
- klare Fundstelle in der Musterlösung für jedes inhaltliche Kriterium

Die Generierung soll in zwei Schritten erfolgen:

1. **Dokumentweise Extraktion:** Kandidaten aus jedem Lösungsteil erzeugen.
2. **Fallweite Konsolidierung:** Kandidaten zusammenführen, deduplizieren, gewichten und den zulässigen Abgabedokumenten zuordnen.

### Kalibrierung mit Fundort-Beschränkung

Die in `scripts/generate_rubric.py` eingebaute Kalibrierung bewertet die Musterlösung bisher als einen zusammenhängenden Text über alle Lösungsdateien. Für Mehrdokumentfälle muss sie dieselbe Datei-Beschränkung anwenden wie die spätere Evaluation: Ein Kriterium besteht die Positivprüfung nur mit Evidenz aus seinen erlaubten Dateien. Andernfalls können Kriterien die Kalibrierung mit Evidenz vom falschen Fundort bestehen – genau der im Professorenreview dokumentierte Fehlertyp „Kontext/Prüfungsort“.

## 8. Phase E: Dynamische Stil- und Formbewertung einführen

Die Stil- und Formbewertung besteht aus zwei getrennten Baustellen, die nicht vermischt werden dürfen.

### E1: Dokumenttypische Form- und Methodenkriterien (Teil der Rubrik)

Prüfbare Einzelleistungen sind normale Rubrikkriterien. Sie entstehen in der Generierung (Phase D), werden kalibriert und wie alle anderen Kriterien bewertet; sie brauchen keinen eigenen Mechanismus in der Evaluation. Beispiele je Dokumenttyp:

- Gutachten: Obersatz, Voraussetzungen, Subsumtion, Ergebnis und sinnvolle Schwerpunktsetzung
- Gerichtliche Entscheidung: Entscheidungsaufbau, Tenor, tragende Gründe, Umgang mit Streitstand und Entscheidungserheblichkeit
- Schriftsatz: korrekte Anträge, Parteiperspektive, prozessuale Zweckmäßigkeit, überzeugende Auswahl und Gewichtung des Vortrags
- Schreiben: klare Handlungsempfehlung, verständliche Risikodarstellung, Fristen und nächste Schritte

### E2: Routing des Pro-Kriterium-Stilurteils (Teil der Evaluation)

Das bestehende separate Stilurteil pro Anwendungs- und Argumentationskriterium ist derzeit fest auf den Gutachtenstil-Prompt verdrahtet. Es wird auf vier Promptvarianten erweitert; nur die Gutachten-Variante existiert bereits, die drei übrigen sind neu zu schreiben:

1. `gutachten` (vorhanden)
2. `gerichtliche_entscheidung` (neu)
3. `anwaltlicher_schriftsatz` (neu)
4. `mandanten_oder_behoerdenschreiben` (neu)

Welche Variante gilt, hängt am Dokumenttyp der Datei, in der die Evidenz des Kriteriums tatsächlich gefunden wurde – bei Kriterien mit mehreren zulässigen Fundorten also am tatsächlichen Fundort, nicht an einer festen Zuordnung.

### Einfrieren des Dokumenttyps

Der Dokumenttyp je Abgabedatei wird genau einmal bei der Rubrikengenerierung aus Aufgabenstellung, Bearbeitervermerk und Dateiname abgeleitet und im Rubrik-Artefakt pro Deliverable gespeichert. Die Evaluation liest ihn von dort und leitet zur Laufzeit nichts neu ab. Das Taskset erhält weiterhin kein neues Feld; das Rubrik-Artefakt ist ohnehin generiert und versioniert.

Die Stilpunkte werden als eigener Teilscore ausgewiesen und dürfen materiell-rechtliche Fehler nicht verdecken.

## 9. Phase F: Mehrdatei-Abgaben technisch unterstützen

Vor den eigentlichen Solver-Experimenten wird der Taskset-Runner so erweitert, dass er:

- alle Pflichtdateien aus `deliverables` erzeugt,
- eine Abgabe als Verzeichnis behandelt,
- Dateinamen und Vollständigkeit prüft,
- zusätzliche oder falsch benannte Dateien nachvollziehbar meldet,
- die vorhandene Ein-Datei-Logik rückwärtskompatibel lässt,
- die Zuordnung der Rubrikkriterien zu den zulässigen Dateien an die Evaluation weitergibt.

Die vorhandene Evaluation kann Abgabeverzeichnisse und kriterienspezifische Dateien bereits grundsätzlich verarbeiten. Vor dem Pilot ist dennoch ein End-to-End-Smoke-Test mit einer vollständigen und einer bewusst unvollständigen Mehrdatei-Abgabe erforderlich.

## 10. Phase G: Drei repräsentative Pilotfälle

Die Anpassungen werden zuerst an drei unterschiedlichen Arbeitsproduktkombinationen validiert:

1. **Allesch** – Klageerwiderung, Mandantenschreiben und Hilfsgutachten
2. **Kaess 2026** – Rechtsmittel- bzw. Schriftsatzarbeit, Behördenschreiben und Hilfsgutachten
3. **Köhl 2025** – gerichtliche Entscheidung und Hilfsgutachten

Für jeden Pilotfall werden erzeugt:

- eine Rubrik mit Inhalts-, Methoden-, Form- und Vollständigkeitskriterien
- eine dokumentbezogene Zuordnung aller Kriterien
- ein Bericht über entfernte Dubletten
- eine Positivprüfung gegen die Musterlösung
- mehrere gezielte Negativtests
- ein kurzes manuelles Reviewprotokoll

## 11. Phase H: Negativtests für die neuen Rubriken

Die Rubriken müssen typische Fehlleistungen des Zweiten Staatsexamens zuverlässig erkennen. Dafür werden pro Pilotfall gezielte Mutationen angelegt:

- eine Pflichtdatei fehlt vollständig
- die richtige Aussage steht in der falschen Datei
- eine gerichtliche Entscheidung ist vollständig im Gutachtenstil verfasst
- ein Schriftsatz enthält keinen brauchbaren Antrag
- ein Mandantenschreiben ist nur ein internes Rechtsgutachten
- Tenor bzw. Antrag und Begründung widersprechen sich
- derselbe Gedanke wird in Hauptdokument und Hilfsgutachten nur doppelt wiederholt
- das Ergebnis ist richtig, aber die tragende Begründung fehlt
- eine vertretbare Alternativlösung wird sachwidrig als Fehler behandelt

### Abnahmebedingung

Die Musterlösung muss alle unverzichtbaren Kriterien bestehen. Die gezielten Mutationen müssen an den vorgesehenen Kriterien scheitern, ohne sachfremde Folgesanktionen auszulösen.

## 12. Phase I: Kalibrierung durch Modellkomitee und Fachreview

Nach dem erfolgreichen Pilot werden die Rubriken wie bei den bisherigen Fällen kalibriert:

- Erstgenerierung mit dem festgelegten Generator
- unabhängige Prüfung durch das bestehende Modellkomitee
- getrennte Prüfung von Inhalt und dokumenttypischem Stil
- Tiebreaker bei Uneinigkeit über Muss-Kriterien oder Gewichtung
- juristisches Fachreview der risikoreichen und hoch gewichteten Kriterien
- Protokollierung aller entfernten, zusammengelegten oder umformulierten Kriterien

Besonders zu prüfen sind:

- richtiger Prüfungsgegenstand und richtige Verfahrensstufe
- Zulässigkeit alternativer Lösungswege
- keine Doppelbestrafung desselben Grundfehlers
- aktuelle Gesetzeslage bei älteren Fällen
- korrekte Abgrenzung von materieller Richtigkeit und Prozesszweckmäßigkeit

## 13. Phase J: Gestufte Ausrollung auf alle 15 Fälle

Nach Freigabe der drei Pilotfälle erfolgt die Generierung in drei Wellen:

1. **Pilotwelle:** Allesch, Kaess 2026 und Köhl 2025
2. **Risikowelle:** Oertel 104 ff. wegen der vielen Quelldokumente sowie Schömig wegen der Rechtsstandsprüfung
3. **Restwelle:** die übrigen zehn Fälle

Jede Welle wird abgeschlossen und geprüft, bevor die nächste beginnt. Für neue Artefakte werden eindeutige Suffixe verwendet, etwa:

- `second-exam-pilot-v1`
- `second-exam-v1`

Vorhandene Rubriken oder Resultate werden nicht überschrieben.

## 14. Verbindliche Qualitäts-Gates

Eine Rubrik gilt erst als freigegeben, wenn alle folgenden Punkte erfüllt sind:

- sämtliche Aufgaben-, Anlagen- und Lösungsdateien wurden vollständig eingelesen
- kein zentraler Quelltext wurde durch Längenlimits abgeschnitten
- jedes Kriterium ist atomar und eindeutig formuliert
- die über `deliverables` erlaubten Fundstellen sind korrekt abgebildet
- der Dokumenttyp jeder Abgabedatei ist im Rubrik-Artefakt eingefroren
- die Kalibrierung hat die Fundort-Beschränkung der Kriterien angewandt
- es gibt keine unbeabsichtigte Doppelbepunktung über mehrere Dokumente
- die Musterlösung besteht alle Muss-Kriterien
- die definierten Negativmutationen werden zuverlässig erkannt
- Inhalt, Stil, Form und Dateivollständigkeit sind getrennt auswertbar
- Rechtsstand und vertretbare Alternativen wurden geprüft
- ein juristisches Review hat die hoch gewichteten Kriterien freigegeben
- Prompt-, Modell-, Konfigurations- und Rubrikversionen sind reproduzierbar dokumentiert

## 15. Erwartete Ergebnisartefakte

Am Ende sollen mindestens folgende Artefakte vorliegen:

- 15 versionierte Rubrikdateien
- ein fallübergreifender Kalibrierungsbericht
- ein Deduplizierungsbericht für Mehrdokumentfälle
- Negativtestfälle und deren erwartete Fehlerbilder
- ein Smoke-Test für Ein- und Mehrdatei-Abgaben
- ein Ergebnisdatensatz mit getrennten Scores für Inhalt, Methode/Stil, Form und Vollständigkeit, inklusive der getrennten Ausweisung von Fails, die allein auf einer fehlenden Pflichtdatei beruhen
- eine kurze README zur reproduzierbaren Neuerzeugung

## 16. Empfohlene unmittelbare Reihenfolge

1. Inventar (inklusive Lizenzstatus) und Rechtsstandsprüfung für Allesch, Kaess 2026 und Köhl 2025 abschließen.
2. Vorhandene `deliverables` auf Vollständigkeit prüfen; kein neues Aufgabenschema einführen.
3. Eigenen Promptsatz für das Zweite Staatsexamen anlegen (dokumentweise Extraktion, fallweite Deduplizierung, Einfrieren des Dokumenttyps je Abgabedatei); Kalibrierung auf die Fundort-Beschränkung umstellen.
4. Die drei fehlenden Stil-Promptvarianten schreiben und das Routing über den im Rubrik-Artefakt eingefrorenen Dokumenttyp anbinden.
5. Mehrdatei-Unterstützung im Codex-Taskset-Runner ergänzen und testen.
6. Die drei Pilotrubriken unter einem neuen Suffix erzeugen.
7. Positivprüfung, Negativmutationen, Modellkomitee und juristisches Review durchführen.
8. Nach Pilotfreigabe die beiden Risikofälle bearbeiten.
9. Danach die restlichen zehn Fälle in Batches erzeugen und kalibrieren.
10. Konfigurationen und Rubriken einfrieren und erst anschließend die eigentlichen Modellläufe für alle 15 Fälle starten.

## 17. Definition of Done

Die Erweiterung ist abgeschlossen, wenn alle 15 Fälle eine freigegebene, reproduzierbare Rubrik besitzen, die das jeweils verlangte praktische Arbeitsprodukt und alle Pflichtdateien korrekt bewertet, vertretbare Lösungen zulässt, typische Fehler zuverlässig erkennt und mit der bestehenden Evaluationspipeline automatisiert ausgeführt werden kann.
