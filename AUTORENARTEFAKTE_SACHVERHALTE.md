# Prüfung und Bereinigung autorenbezogener Artefakte in Sachverhalten

Stand: 28. Juli 2026

## Ergebnis

Geprüft wurden alle 300 Dateien unter `tasks/de/**/documents/sachverhalt.md`. In 30 Fällen waren eindeutig Autorenbiografien, Danksagungen, Angaben zur Klausurentstehung oder Publikationskopfzeilen in den eigentlichen Sachverhalt geraten. Alle 30 Fundstellen wurden am 28. Juli 2026 bereinigt.

Davon waren 23 textschädigend (K1), sechs klar fehlplatziert (K2) und einer eine vorgelagerte Metainformation (K3). Beschädigte Wort- und Satzanschlüsse wurden wiederhergestellt. Im zusätzlich abgeschnittenen Fall „Große und kleine Finanzgeschäfte“ wurde der fehlende Sachverhalt einschließlich der Aufgabenstellung aus der Originalquelle ergänzt.

Die beiden Ausgangsbeispiele gehören zu diesen Fällen:

- `sachverhalt-2.docx`: **Anfängerklausur: Caroline**
- `sachverhalt-3.docx`: **Fortgeschrittenenklausur Europarecht: Autofrei – Spaß dabei?**

Die sichtbaren Fehler stammen bereits aus den jeweiligen Markdown-Dateien und werden beim DOCX-Export nur reproduziert. Sie sind nicht durch das DOCX-Feld `creator` verursacht; dieses ist in beiden Beispieldateien leer.

## Einstufung

- **K1 – textschädigend:** Der Einschub trennt ein Wort, einen Satz oder eine zusammengehörige Passage; bei „Große und kleine Finanzgeschäfte“ endet der Sachverhalt sogar unmittelbar im Einschub.
- **K2 – klar fehlplatziert:** Der Autoren-/Quellenblock steht zwischen Aufgaben, Bearbeitungsvermerk und Anlage, ohne den umgebenden Satz zwingend zu zerreißen.
- **K3 – vorgelagerte Metainformation:** Autoren-/Klausurkontext steht vor dem eigentlichen Sachverhalt und sollte nicht Teil der Aufgabenunterlage sein.

## Bereinigte Fälle

| Stufe | Fall | Fundstelle und Erscheinungsbild |
|---|---|---|
| K1 | [Examensklausur: Staatshaftungsrecht – Folgenreiche Ermittlungsmaßnahmen](tasks/de/oeffentliches-recht/staatshaftungsrecht/examensklausur-staatshaftungsrecht-folgenreiche-ermittlungsmassnahmen/documents/sachverhalt.md) | Quellenhinweis und „Dr. Sebastian Omlor …“ stehen zwischen „Propaganda-“ und „plakat“. |
| K1 | [Übungsklausur: Ein eisiger Weg zur Universität](tasks/de/oeffentliches-recht/staatshaftungsrecht/ubungsklausur-ein-eisiger-weg-zur-universitat/documents/sachverhalt.md) | Abgeschnittener Affiliationsrest „… und Kommunikationsrecht an der Universität zu Köln“ unterbricht den Gesetzestext. |
| K2 | [Fortgeschrittenenklausur: Gemeinde – Staat – Haftung?](tasks/de/oeffentliches-recht/staatshaftungsrecht/fortgeschrittenenklausur-gemeinde-staat-haftung/documents/sachverhalt.md) | „Dr. Anne Peters, LL.M., Direktorin …“ steht zwischen Bearbeitungsvermerk und Zusatzfrage. |
| K1 | [Hausarbeit: „Deutschland zuerst“?](tasks/de/oeffentliches-recht/staatsrecht/hausarbeit-deutschland-zuerst/documents/sachverhalt.md) | Abgeschnittene Lehrstuhl-/Institutsangabe und Entstehungshinweis unterbrechen den Satz nach der Bundesratsabstimmung. |
| K1 | [Anfängerklausur: Caroline](tasks/de/oeffentliches-recht/staatsrecht/anfangerklausur-caroline-zugleich-ein-beitrag-zur-mittelbaren-drittwirkung-der-grundrechte/documents/sachverhalt.md) | „Dr. Andreas Paulus …“ trennt das Wort „Persönlichkeitsrecht“. Dies ist `sachverhalt-2.docx`. |
| K1 | [Übungshausarbeit: Wirtschaftsförderung in der Pandemie](tasks/de/oeffentliches-recht/staatsrecht/ubungshausarbeit-wirtschaftsforderung-in-der-pandemie/documents/sachverhalt.md) | Fußnotenblock zur Lehrstuhlvertretung samt Danksagung steht mitten zwischen „Hierin heißt es“ und dem Zitat. |
| K2 | [Übungshausarbeit: Gebete in der Schule](tasks/de/oeffentliches-recht/staatsrecht/ubungshausarbeit-gebete-in-der-schule/documents/sachverhalt.md) | Publikationskopf „ÜBUNGSFALL Anna Mrozek/Norman Jäckel“ steht zwischen Aufgabe und Gesetzesanlage. |
| K1 | [Fortgeschrittenenklausur Europarecht: Autofrei – Spaß dabei?](tasks/de/oeffentliches-recht/europarecht/fortgeschrittenenklausur-europarecht-autofrei-spass-dabei/documents/sachverhalt.md) | Abgeschnittene Lehrstuhlangabe und Dank an Prof. Kühling trennen „ausschließlich beruflich genutzte Pkw“. Dies ist `sachverhalt-3.docx`. |
| K1 | [Fortgeschrittenenklausur Europarecht: Wohnungsbestand in Bürgerhand?](tasks/de/oeffentliches-recht/europarecht/fortgeschrittenenklausur-europarecht-wohnungsbestand-in-burgerhand/documents/sachverhalt.md) | Verstümmelte Autorenzeile „Z. ebenda. ad. Rat. a.Z. Dr. Stefan Drechsler …“ trennt Zahl und Bezugswort „Wohnungen“. |
| K1 | [Übungsfall: Biogasanlage versus landschaftliche Ästhetik](tasks/de/oeffentliches-recht/verwaltungsrecht/ubungsfall-biogasanlage-versus-landschaftliche-asthetik/documents/sachverhalt.md) | „Dr. Ivo Appel“ und Klausurherkunft stehen zwischen „am selben“ und „Tag“. |
| K1 | [Fortgeschrittenenhausarbeit: „Unruhe im Altmühltal“](tasks/de/oeffentliches-recht/verwaltungsrecht/fortgeschrittenenhausarbeit-unruhe-im-altmuhltal/documents/sachverhalt.md) | Angaben zu Zeichenzahl, Ergebnissen und Dr. Wegener stehen mitten im Wort-/Satzfluss vor „Nähe“. |
| K1 | [Schwerpunktsbereichsklausur: Die verhängnisvolle Fahrt der Spack Jarrow](tasks/de/oeffentliches-recht/voelkerrecht/schwerpunktsbereichsklausur-die-verhangnisvolle-fahrt-der-spack-jarrow/documents/sachverhalt.md) | Abgeschnittene Autoren-/Absolventenangabe mit „Dr. Alexander Proelß“ unterbricht den Satz. |
| K2 | [Schwerpunktbereichsklausur Kriminologie: Jugendkriminalität in Parks](tasks/de/strafrecht/kriminologie-und-nebengebiete/schwerpunktbereichsklausur-kriminologie-jugendkriminalitat-in-parks/documents/sachverhalt.md) | Autorenbiografie und Danksagung stehen zwischen den nummerierten Aufgaben 1 und 2. |
| K2 | [Anfängerklausur: Klimaprotest mal anders](tasks/de/strafrecht/materielles-strafrecht/anfangerklausur-klimaprotest-mal-anders/documents/sachverhalt.md) | Klausurherkunft und Biografien der Verfasser stehen zwischen Bearbeitungsvermerk und Gesetzesauszug. |
| K1 | [Anfängerübungsklausur: Alte Feindschaft](tasks/de/strafrecht/materielles-strafrecht/anfangerubungsklausur-alte-feindschaft/documents/sachverhalt.md) | Abgeschnittener Tätigkeits-/Lehrstuhlhinweis steht zwischen „Als N am nächsten Morgen“ und „auf dem Weg“. |
| K1 | [Examensklausur – Strafrecht: Amoklauf an der Schule](tasks/de/strafrecht/materielles-strafrecht/examensklausur-strafrecht-amoklauf-an-der-schule/documents/sachverhalt.md) | Langer Entstehungs-, Statistik- und Dankesblock plus „Dr. Dr. h.c. Walter Gropp …“ trennt das Wort „Computer“. |
| K1 | [Examensübungsklausur: Hools, Corona und ein Supersportwagen](tasks/de/strafrecht/materielles-strafrecht/examensubungsklausur-hools-corona-und-ein-supersportwagen/documents/sachverhalt.md) | Danksagung an wissenschaftliche und studentische Mitarbeitende steht zwischen „entsprechend“ und „anspricht“. |
| K1 | [Examensübungsklausur: „Klimakleber“](tasks/de/strafrecht/materielles-strafrecht/examensubungsklausur-klimakleber-mit-exkurs-zur-zurechenbarkeit-eines-todeserfolges-durch/documents/sachverhalt.md) | Abgeschnittene Autorenbiografie und Danksagung unterbrechen die Sachverhaltschronologie. |
| K1 | [Fortgeschrittenenklausur: Geldabheben mit Hindernissen](tasks/de/strafrecht/materielles-strafrecht/fortgeschrittenenklausur-geldabheben-mit-hindernissen/documents/sachverhalt.md) | Vollständige Biografien von Philipp-Alexander Hirsch und Johannes Stefan Weigel stehen mitten im Satz am Geldautomaten. |
| K1 | [Fortgeschrittenenklausur: Must-Haves – Smartphone und Pfefferspray](tasks/de/strafrecht/materielles-strafrecht/fortgeschrittenenklausur-must-haves-smartphone-und-pfefferspray/documents/sachverhalt.md) | Fakultätsdank und Danksagung an Hilfskräfte stehen mitten in der Handlung. |
| K1 | [Übungsfall: Ein Hundeleben](tasks/de/strafrecht/materielles-strafrecht/ubungsfall-ein-hundeleben/documents/sachverhalt.md) | „Dr. Christian Schröder, Martin-Luther-Universität …“ trennt Bezugswort und Verb („Mischlingshündin … zuwendet“). |
| K2 | [Übungsfall: Die Glasflasche](tasks/de/strafrecht/materielles-strafrecht/ubungsfall-die-glasflasche/documents/sachverhalt.md) | Abgeschnittene Autoren-/Affiliationsliste steht unmittelbar vor dem Bearbeitervermerk. |
| K1 | [Fortgeschrittenenhausarbeit: Seeteufel à l‘ancienne](tasks/de/strafrecht/materielles-strafrecht/fortgeschrittenenhausarbeit-seeteufel-a-l-ancienne/documents/sachverhalt.md) | „Dr. Georg Steinberg). Georg Steinberg.“ steht zwischen zwei Handlungssätzen. |
| K3 | [Übungsfall: Korn und Schrot](tasks/de/strafrecht/materielles-strafrecht/ubungsfall-korn-und-schrot/documents/sachverhalt.md) | Hinweis auf den „Erstautor“, Semester, Bearbeitungszeit und Prüfungsstoff steht vor dem eigentlichen „Sachverhalt“. |
| K1 | [Fortgeschrittenenhausarbeit: Große und kleine Finanzgeschäfte](tasks/de/strafrecht/wirtschaftsstrafrecht/fortgeschrittenenhausarbeit-grosse-und-kleine-finanzgeschafte/documents/sachverhalt.md) | Danksagung an Luca Schiliró beginnt nach „Datenaustausch auf kurze Distanz über“; die Datei endet danach, der Sachverhalt ist daher zusätzlich offensichtlich abgeschnitten. |
| K1 | [Übungsfall: Der renitente GmbH-Gesellschafter](tasks/de/zivilrecht/handels-und-gesellschaftsrecht/ubungsfall-der-renitente-gmbh-gesellschafter/documents/sachverhalt.md) | Vollständige Autorenbiografie steht zwischen den Wortteilen „neu be-“ und „zogenen“. |
| K1 | [Fortgeschrittenenübungsklausur: „MoPeG in 3D“](tasks/de/zivilrecht/handels-und-gesellschaftsrecht/fortgeschrittenenubungsklausur-mopeg-in-3d/documents/sachverhalt.md) | Danksagung, Fußnotenziffer, Fundstelle und Publikationskopf „Kroll-Ludwigs/Lennartz … Zivilrecht Übungsfälle“ stehen mitten im Satz. |
| K1 | [Anfängerhausarbeit: Übersinnliche Kräfte und trotzdem nichts als Ärger](tasks/de/zivilrecht/schuldrecht/anfangerhausarbeit-im-zivilrecht-ubersinnliche-krafte-und-trotzdem-nichts-als-arger/documents/sachverhalt.md) | Hinweis auf Herkunft und Semester der Hausarbeit steht zwischen „nicht auf“ und „die Tarot-Karten geboten“. |
| K1 | [Anfängerklausur: Keine Freude am Fahren](tasks/de/zivilrecht/schuldrecht/anfangerklausur-keine-freude-am-fahren/documents/sachverhalt.md) | Autorenbiografien von Dennis Pielsticker und Philipp Reimann stehen zwischen „abgeliefert“ und „hat“. |
| K2 | [Anfängerklausur: Ein gebrochener Arm und viele Scherben](tasks/de/zivilrecht/schuldrecht/anfangerklausur-ein-gebrochener-arm-und-viele-scherben/documents/sachverhalt.md) | Klausurstatistik, Lehrstuhlbezug und Autorenbiografie stehen zwischen Fallfrage 1 und Abwandlung 1. |

## Abgrenzung

Korrekt als eigene Markdown-Fußnote am Dokumentende gespeicherte Autorenangaben, insbesondere in den neueren Referendariatsfällen, wurden **nicht** als Darstellungsfehler gezählt.

Daneben gibt es einzelne nicht autorenbezogene Importreste (beispielsweise Seitenkopf „752 Zivilrecht Übungsfälle“ oder „ZJS 2/2016 208“). Diese sind nicht Teil der Zahl 30 und sollten bei einer späteren allgemeinen Bereinigung separat erfasst werden.

## Umsetzung

Die Attribution ist nicht aus dem Projekt verschwunden: Bei den BenGER-/ZJS-Fällen bleibt sie strukturiert in `task.json` unter `source.autoren` sowie in der Lizenz-/Provenienzangabe erhalten. Entfernt wurden ausschließlich die in den Aufgabentext geratenen Artefakte; beschädigte Übergänge wurden anhand des Satzkontexts beziehungsweise der Originalquelle rekonstruiert.
