# Anleitung für Claude: Neue Fälle in LAB-EU anlegen

## Ziel

Lege neue juristische Benchmark-Fälle so an, dass sie ohne nachträgliche
Umstrukturierung von der LAB-EU Workbench, den Runnern und den LLM Judges
verwendet werden können.

Arbeite quellennah, ändere nur die Dateien des neuen Falls und erfinde niemals
fehlende Lizenz-, Quellen- oder Rechtsinformationen. Kennzeichne unfertige oder
noch nicht fachlich validierte Inhalte ausdrücklich als Entwurf.

## Vor Beginn

1. Lies die Repository-Dateien:
   - `README.md`
   - `workbench/README.md`
   - `tasks/fr/README.md` für französische Fälle
2. Prüfe mindestens einen bestehenden Fall derselben Sprache und desselben
   Aufgabentyps.
3. Verwende für französische CRFPA-Fälle insbesondere diesen Pilot als
   Strukturbeispiel:

   ```text
   tasks/fr/droit-des-obligations/cas-pratique/
     cas-pratique-crfpa-2024-alphadot/
   ```

4. Kläre vor dem Schreiben:
   - Rechtsordnung und Sprache;
   - Aufgabentyp;
   - verbindliche Aufgabenstellung;
   - vollständige Quelldokumente;
   - Herkunft und Lizenz jedes Materials;
   - Referenzlösung;
   - fachliche Prüferinnen oder Prüfer.

Wenn diese Angaben nicht vorliegen, frage nach. Fülle Lücken nicht stillschweigend
mit Vermutungen.

## Wichtig: Keine Rubrik erstellen

Erstelle für einen neuen Fall **keine** `rubric.json` und keine sonstige
Bewertungsrubrik. Entwirf auch keine Bewertungskriterien, Punktetabellen,
Gewichtungen oder Judge-Anweisungen.

Die Rubriken werden später separat durch das LAB-EU Benchmark-Team erstellt und
geprüft. Der Beitrag für einen neuen Fall umfasst ausschließlich:

- `task.json`;
- die für die Bearbeitung freigegebenen Dokumente unter `documents/`;
- die juristische Referenzlösung unter `evals/loesung.md`.

Falls ein bestehender Beispielfall eine `evals/rubric.json` enthält, dient diese
nicht als Vorlage für den neuen Fall. Öffne, kopiere, ändere oder ergänze sie
nicht. Weise bei der Übergabe ausdrücklich darauf hin, dass die Rubrik noch vom
Benchmark-Team erstellt werden muss.

## Verzeichnisstruktur

Jeder Fall ist ein eigenes Verzeichnis unter `tasks/<sprache>/`.

```text
tasks/
  fr/
    <rechtsgebiet>/
      <aufgabentyp>/
        <kurzer-eindeutiger-fall-slug>/
          task.json
          documents/
            sujet.md
            <weitere-dokumente>.md
          evals/
            loesung.md
```

Für deutsche Fälle wird typischerweise `documents/sachverhalt.md` verwendet.
Für französische Fälle kann `documents/sujet.md` verwendet werden.

Regeln für Pfade:

- Verwende ausschließlich Kleinbuchstaben, Zahlen und Bindestriche.
- Verwende sprechende französische oder deutsche Begriffe.
- Verwende keine Leerzeichen, Umlaute oder Akzente in Verzeichnis- und
  Dateinamen.
- Verschiebe oder ändere keine bestehenden Fälle.
- Der relative Verzeichnispfad ist die technische Task-ID. Lege nicht zusätzlich
  eine abweichende Task-ID in `task.json` an.

## `task.json`

Verwende gültiges UTF-8-JSON. Für einen französischen Fall ist folgende Form ein
guter Ausgangspunkt:

```json
{
  "title": "Cas pratique — titre lisible",
  "language": "fr",
  "jurisdiction": "FR",
  "exercise_type": "cas_pratique_consultation",
  "work_type": "draft",
  "tags": [
    "CRFPA",
    "droit-des-obligations",
    "theme-juridique"
  ],
  "instructions": "Vous êtes avocat. Rédigez ... Vous ne pouvez utiliser que les documents fournis.",
  "deliverables": "consultation.md",
  "validation_status": "draft_needs_french_expert_review",
  "source": "Référence complète et vérifiable de la source.",
  "license": "Licence exacte ou statut de réutilisation à confirmer."
}
```

### Pflichtfelder

- `title`: verständlicher Titel in der Sprache des Falls;
- `work_type`: `analyze`, `draft`, `review` oder `research`;
- `instructions`: vollständige Aufgabenstellung für das getestete System;
- `deliverables`: exakt ein erwarteter Markdown-Dateiname;
- `tags`: sachliche Such- und Analysetags;
- `license`: konkrete Lizenz- und Attributionsangabe.

### Empfohlene Felder für neue französische Fälle

- `language`: `fr`;
- `jurisdiction`: `FR`;
- `exercise_type`: zum Beispiel `cas_pratique_consultation` oder
  `note_de_synthese`;
- `validation_status`: bei neuen Fällen zunächst ein eindeutiger Draft-Status;
- `source`: vollständige Fundstelle und Herkunft.

### Anforderungen an `instructions`

Die Anweisungen müssen:

- die Rolle und das verlangte Arbeitsergebnis klar benennen;
- alle Bearbeitervermerke und Einschränkungen enthalten;
- die verlangte Sprache festlegen oder aus dem Fall eindeutig erkennen lassen;
- zum Dateinamen unter `deliverables` passen;
- ausdrücklich festlegen, ob nur die bereitgestellten Dokumente verwendet
  werden dürfen;
- bei einer französischen Prüfung die erwartete Methode nennen, etwa den
  syllogisme juridique;
- keine Referenzlösung oder versteckten Bewertungshinweise offenlegen.

## Dokumente unter `documents/`

Speichere dort ausschließlich Material, das das getestete System tatsächlich
sehen darf:

- Sachverhalt oder sujet;
- Gesetzesauszüge;
- Urteile;
- Vertragsunterlagen;
- Anlagen;
- sonstige ausdrücklich zugelassene Quellen.

Anforderungen:

- Übertrage Texte vollständig und genau.
- Erhalte Überschriften, Nummerierung und für die Lösung relevante Struktur.
- Nenne bei jedem Dokument die Herkunft.
- Verwende keine verkürzten Platzhalter anstelle notwendiger Dokumenttexte.
- Entferne keine Tatsachen, die für die Lösung relevant sein könnten.
- Lege die Referenzlösung niemals unter `documents/` ab.
- Nimm keine vertraulichen, personenbezogenen oder nicht zur Weitergabe
  freigegebenen Unterlagen auf.

Bei einer Note de synthèse muss das vollständige zulässige Dossier vorliegen.
Eine bloße Liste der Dokumenttitel reicht für einen offiziellen Benchmark-Fall
nicht aus.

## Referenzlösung unter `evals/loesung.md`

Die Referenzlösung ist die fachliche Grundlage der Bewertung.

Sie muss:

- in der Sprache des Falls geschrieben sein;
- den Sachverhalt und die bereitgestellten Dokumente vollständig abdecken;
- das verlangte Format und die verlangte juristische Methode einhalten;
- Normen und Rechtsprechung präzise belegen;
- Tatsachenanwendung und Schlussfolgerungen sichtbar verbinden;
- vertretbare Alternativlösungen ausdrücklich kennzeichnen;
- keine Tatsachen oder Quellen erfinden;
- von einer fachkundigen Juristin oder einem fachkundigen Juristen geprüft
  werden.

Eine von Claude erstellte Lösung ist zunächst nur ein Entwurf. Stelle sie nie
als fachlich validierte Ground Truth dar, solange die menschliche Prüfung nicht
dokumentiert ist. Beschreibe vertretbare alternative Lösungswege in der
Referenzlösung selbst, ohne daraus Bewertungskriterien oder eine Rubrik
abzuleiten.

## Quellen und Lizenzen

Prüfe die Wiederverwendung vor dem Import.

Dokumentiere mindestens:

- Urheber oder herausgebende Institution;
- Titel und Fundstelle;
- URL oder DOI, soweit vorhanden;
- konkrete Lizenz;
- erforderliche Attribution;
- vorgenommene Änderungen;
- offene rechtliche Unsicherheiten.

Wichtig:

- Öffentlich zugänglich bedeutet nicht automatisch frei wiederverwendbar.
- Die Lizenz des Repository-Codes gilt nicht automatisch für Falldaten oder
  Dokumente.
- Erfinde niemals eine Lizenz.
- Wenn die Nutzung noch nicht geklärt ist, schreibe dies ausdrücklich in
  `license` und halte den Fall im Draft-Status.
- Nimm urheberrechtlich geschützte Drittdokumente nicht vollständig auf, wenn
  keine ausreichende Erlaubnis besteht.

## Validierungsstatus

Ein technisch lauffähiger Fall ist noch kein fachlich validierter Benchmark.

Neue französische Fälle sollen grundsätzlich als Entwurf beginnen, zum
Beispiel:

```text
draft_needs_french_expert_review
```

Ein Fall darf erst als validiert bezeichnet werden, wenn mindestens geprüft
wurden:

1. Quellentreue;
2. rechtliche Richtigkeit;
3. Vollständigkeit der Referenzlösung;
4. vertretbare Alternativwege;
5. Lizenz und Attribution;
6. technische Ausführbarkeit;
7. fachliche Freigabe durch französische Rechtsexpertinnen oder Rechtsexperten.

Bei CRFPA-Fällen ersetzt ein technischer Smoke-Test nicht die fachliche
Freigabe.

## Technische Prüfung

Führe mindestens folgende nichtdestruktive Prüfungen aus:

```bash
python3 -m json.tool tasks/fr/<...>/task.json
```

Prüfe zusätzlich:

- `task.json`, `documents/` und `evals/loesung.md` existieren;
- der Deliverable-Dateiname in `task.json` ist eindeutig;
- die Referenzlösung liegt nicht unter `documents/`;
- für den neuen Fall wurde keine `rubric.json` erstellt oder bearbeitet;
- keine geheimen Dateien, API-Schlüssel oder lokalen Runs wurden hinzugefügt;
- `git diff --check` meldet keine Formatfehler.

Führe keine Modell- oder Judge-Aufrufe aus. Die Einrichtung und Prüfung der
Rubrik erfolgt später durch das Benchmark-Team.

## GitHub-Einreichung

Verwende für GitHub den Skill `github-safe-collaboration`.

Grundregeln:

- niemals direkt auf `main` pushen;
- separaten, sprechenden Branch erstellen;
- nur die Dateien des neuen Falls stagen;
- Pull Request zur fachlichen Prüfung eröffnen;
- Runs, Zugangsdaten und fremde Änderungen ausschließen;
- bei jedem Merge-Konflikt stoppen und den Nutzer einzeln entscheiden lassen.

Ein geeigneter Branchname ist zum Beispiel:

```text
case/fr-crfpa-obligations-short-title
```

Ein geeigneter Pull-Request-Text nennt:

- Quelle und Lizenz;
- Aufgabentyp;
- enthaltene Dokumente;
- Status der Referenzlösung;
- den ausdrücklichen Hinweis, dass keine Rubrik erstellt wurde;
- noch offene fachliche oder rechtliche Prüfungen.

## Abschlusscheckliste

Vor der Übergabe bestätigen:

- [ ] Der Fall liegt im richtigen Sprach- und Rechtsgebietsverzeichnis.
- [ ] `task.json` ist gültig und vollständig.
- [ ] Alle zugelassenen Dokumente liegen unter `documents/`.
- [ ] Die Referenzlösung liegt ausschließlich unter `evals/`.
- [ ] Es wurde keine `rubric.json` erstellt oder bearbeitet.
- [ ] Deliverable-Dateinamen stimmen überall überein.
- [ ] Quellen und Lizenzen sind konkret dokumentiert.
- [ ] Ungeklärte Punkte sind als Draft markiert.
- [ ] Die Referenzlösung wird dem Solver nicht offengelegt.
- [ ] Technische Prüfungen sind erfolgreich.
- [ ] Menschliche Fachprüfung ist erfolgt oder klar als offen dokumentiert.
- [ ] Bei der Übergabe wird vermerkt, dass das Benchmark-Team die Rubrik
      separat erstellt.
- [ ] Die Änderungen werden auf einem separaten Branch per Pull Request
      eingereicht.
