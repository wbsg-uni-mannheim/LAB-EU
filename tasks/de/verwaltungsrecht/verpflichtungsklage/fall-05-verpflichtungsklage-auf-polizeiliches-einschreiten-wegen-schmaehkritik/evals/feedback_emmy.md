# Meeting-Vorbereitung: Juristisches Review der Bewertungsrubriken

**Stand:** 2026-07-05 · **Anlass:** Vorbesprechung für das Meeting mit den Juristen

## Kontext in einem Satz

LAB-EU misst die Leistung von KI-Systemen beim Lösen juristischer Fälle. Da wir
über ~150 Fälle × viele Systeme nicht von Hand korrigieren können, übernehmen
maschinenlesbare **Rubriken** (Boolesche Einzelkriterien) die Benotung durch
einen LLM-Judge. Es geht heute nur um die Qualität dieser Rubriken.

## Ausgangslage

Ein erstes juristisches Review der Rubrik zum Fall „Schmähkritik" (88 Kriterien)
kam zum Ergebnis: die Kriterien sind **grundsätzlich gut und decken den Fall
weitgehend ab**. Der Ansatz, jedes Kriterium zusätzlich einer Kategorie
(Prüfungsstation, Gutachtenstil-Schritt) zuzuordnen, trägt. Die folgenden Punkte
sind Verbesserungen, keine Grundsatzkritik.

## Kernfindings

1. **Reihenfolge und Struktur zählen.** Die juristische Gliederung ist ein Baum:
   biegt man an einer Stelle anders ab, ändert sich der Rest. Reine
   „drin/nicht drin"-Prüfung erfasst das nicht vollständig.
2. **Gewichtung fehlt (1-/2-/3-Sterne).** Basale Pflichtpunkte, „normale"
   Probleme und schwere Schwerpunktprobleme dürfen nicht gleich zählen. Ein
   System, das die Schwerpunkte trifft, aber Basispflichten reißt, ist nicht gut.
3. **Handwerk wird noch nicht bewertet.** Ein Kriterium kann inhaltlich erfüllt
   sein, obwohl die Antwort die Norm nur zitiert statt zu argumentieren
   (Urteilsstil statt Gutachtenstil). Juristisch ist das ein klarer Mangel — für
   die Bewertung bisher unsichtbar.
4. **Vertretbare Alternativen.** Wählt das System an einer der wenigen offenen
   Stellen eine vertretbare Gegenauffassung, läuft der restliche Fall anders und
   passt nicht mehr zur Musterlösung. Kernfrage juristischen Korrigierens.
5. **Vollständigkeit.** Vereinzelt fehlen Pflichtpunkte, die zwar unproblematisch,
   aber zu erwähnen sind (z. B. Vertretung einer nicht natürlichen Person).

## Was wir daraus ableiten (Umsetzung geplant)

- **Drei Wertungsstufen** (essenziell / normal / vertiefend) je Kriterium, statt
  einheitlicher Gewichtung — bildet die 1-/2-/3-Sterne-Logik ab.
- **Dreiteilige Bewertung je Prüfungspunkt:** Inhalt · Gutachtenstil ·
  juristische Argumentation, getrennt ausgewiesen (z. B. „inhaltlich 70 %,
  Gutachtenstil 85 %, Argumentation 30 %").
- **Alternativpfad-Erkennung:** erkennt das System eine vertretbare
  Gegenauffassung, wird der Lauf markiert und die betroffenen Folgekriterien
  nicht als Fehler gezählt. Zusätzlich messen wir, wie häufig das überhaupt
  vorkommt (Erwartung: selten, da Modelle den Standardweg bevorzugen).
- **Hierarchie** der Kriterien an der Lösungsgliederung verankern
  (Ober-/Unterpunkte), damit Schwerpunkt und Einzelaspekte zusammenpassen.

## Fragen an die Juristen

1. **Sterne-Schema:** Ist die Einteilung essenziell / normal / vertiefend für
   diese Fälle sinnvoll und intersubjektiv vergebbar?
2. **Handwerk:** Bestätigt sich die Trennung von Inhalt, Gutachtenstil und
   juristischer Argumentationsweise als eigene Bewertungsdimensionen?
3. **Grundverständnis / Schema:** Wie prüft man ab, ob eine Antwort das richtige
   Prüfungsschema anwendet und Spezialnormen (lex specialis) erkennt? Könnten
   Standard-Prüfungsschemata je Klageart bereitgestellt werden?
4. **Reihenfolge:** Wann ist die Reihenfolge so wichtig, dass Abweichung
   Punkte kostet — und wann nicht?

## Validierung (nächster Schritt)

Bislang wurden nur die Kriterien geprüft, nicht das KI-Gutachten samt Bewertung.
Geplant: eine Teilmenge (~25 Fälle) parallel von Juristen und vom LLM-Judge
bewerten und die Übereinstimmung messen. Ist sie hoch genug, kann der Judge die
restlichen Fälle übernehmen.

*Motivierende Idee für später:* eine KI-Lösung anonym in einen echten
Korrekturdurchgang geben und sehen, wie sie neutral benotet wird.