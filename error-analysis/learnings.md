# Learnings aus der Fehleranalyse

## Was wir gelernt haben

### 1. Am häufigsten fehlt ein ganzer Prüfungspunkt (K1a)

1.100 von 2.896 Fehlern sind K1a, also gut jeder dritte (38 %). Im Zivilrecht fehlt ein ganzer Punkt öfter als im öffentlichen Recht, und zwar in allen acht Armen. Knapp die Hälfte der K1a-Fehler steckt in Kriterien, die kein Arm besteht (mehr dazu in Punkt 7).

In den Traces haben wir nachgesehen, ob der Inhalt erst beim Überarbeiten verloren geht oder von Anfang an fehlt. Bei Sol und Terra als Agent haben wir alle 495 Stellen mit fehlendem Inhalt (K1) mit dem ersten Entwurf verglichen. Bei Sol fehlte der Inhalt an 207 von 207 Stellen schon im ersten Entwurf, bei Terra an 287 von 288. Die eine offene Stelle ist ZR24 bei Terra. Dort standen nötige Angaben im Entwurf, allerdings bei einer anderen Frage, und wurden beim Überarbeiten gestrichen. Die verlangte Vorschrift kam in keiner Fassung vor. 249 Stellen ließen sich automatisch einordnen, weil der Fall nicht mehr überarbeitet wurde oder die Überarbeitung nichts am Kriterium geändert hat. Bei DeepSeek als Agent kam der fehlende Inhalt an 18 von 25 geprüften Stellen nicht einmal im Reasoning vor. Es gibt aber auch den umgekehrten Fall: An 4 Stellen stand der Punkt im Reasoning und kam trotzdem nicht in die Antwort. In ÖR 09 etwa hält DeepSeek im Reasoning fest, dass P kein Bediensteter der Anstalt ist und Nr. 4 deshalb nicht greift. In der Antwort fehlt dieser Ausschluss. An 3 weiteren Stellen war der Punkt im Reasoning angedacht, aber falsch angelegt. Der Inhalt fehlt also meist schon, bevor überarbeitet wird.

Mit Agent oder Websuche gibt es in allen vier Paaren weniger K1a-Fehler. Deutlich ist das aber nur bei DeepSeek und bei Codex. Woran das liegt, wissen wir nicht.

Mögliche Stellschraube (zusätzlicher Agentenschritt): ein Plan vor dem Schreiben, der alle Prüfungspunkte auflistet.

### 2. Oft ist der Punkt angesprochen, aber ohne Maßstab (K1b)

Maßstab heißt: die Definition oder Regel, an der man den Fall misst. 644 Fehler sind K1b, gut jeder fünfte (22 %). Bei Kriterien mit 3 Sternen ist K1b die häufigste Art von fehlendem Inhalt.

Mit Agent oder Websuche ändert sich K1b in keinem Paar deutlich. Bei K1a war die Änderung aber auch nur in zwei von vier Paaren deutlich. Man kann also nicht sagen, dass Agent oder Websuche bei K1a mehr helfen als bei K1b.

Bei knapp der Hälfte der K1b-Fehler (45 %) halten beide Annotatoren die Anforderung der Rubric für fraglich. Ob die Rubric dort zu Recht etwas verlangt, müssen Juristen klären. Die Klasse bleibt trotzdem K1b, der Zweifel steht nur als Vermerk daneben.

Vermutung: Die Modelle schreiben hier wie in einem Urteil. Sie nennen gleich das Ergebnis und lassen die Definition weg.

### 3. Die Regel wird nicht auf die Angaben im Fall angewendet (K1c)

K1c heißt: Regel und Ergebnis stehen da, aber die Anwendung auf den Fall fehlt. Das betrifft 377 Fehler (13 %). Ein Beispiel: In ZR22 prüft Sol als Baseline, ob H ihre Aufsichtspflicht verletzt hat. Die Antwort nennt nur, dass der Hund an dem Tag aufgeregt war. Dass er sonst sehr gut gehorcht und dass die Tante die Tür geöffnet hat, kommt nicht vor.

Manchmal steht die nötige Angabe sogar in der Antwort, nur an anderer Stelle, und wird für die gefragte Prüfung nicht benutzt. Bei Abwägungen fehlt oft, dass die Interessen aus dem Fall wirklich gegeneinander gewichtet werden. Solche Stellen haben wir vor allem im öffentlichen Recht gefunden. Dort verlangt die Rubric aber auch viel öfter eine Abwägung. Wie oft das alles vorkommt, haben wir nicht gezählt.

Vermutung: Die Modelle gehen die Prüfungsschritte der Reihe nach durch und setzen jeweils die naheliegende Angabe aus dem Fall ein. Angaben, die in eine andere Richtung zeigen, lassen sie eher weg. Es kann auch andere Gründe geben, etwa dass das Modell die Antwort kurz halten will.

### 4. Bei Kriterien mit 3 Sternen ist der Inhalt öfter falsch (K2, K3)

Bei Kriterien mit 3 Sternen (in LAB-EU „ergebnistragend“) sind 39 % der Fehler eine falsche Anwendung auf den Sachverhalt (K2) oder eine falsch dargestellte Regel (K3). Bei Kriterien mit 1 Stern sind es nur 7 %. Auch bei 3 Sternen ist fehlender Inhalt (K1) aber häufiger als falscher.

Das ist zum Teil zu erwarten. Zu einem zentralen Punkt schreibt fast jede Antwort etwas, weil sie ein Ergebnis braucht. Ist es falsch, ist es K2 oder K3. Details lässt eine Antwort dagegen eher ganz weg, das ist dann K1. Der Befund sagt also weniger, dass die Modelle an wichtigen Stellen schlechter sind. Er sagt eher, dass es an zentralen Punkten auf Richtigkeit ankommt und bei Details auf Vollständigkeit.

Auch falscher Inhalt entsteht meist früh. Bei Sol und Terra als Agent haben wir alle Stellen angesehen, die sie beim Überarbeiten geändert haben und an denen etwas Falsches steht. An 21 von 32 dieser Stellen stand der Fehler schon im ersten Entwurf. Bei DeepSeek als Agent stand er an 8 von 10 geprüften Stellen schon im Reasoning.

Mit Agent oder Websuche werden K2 und K3 mal seltener, mal häufiger. Deutlich ist nur eins: Sol als Agent macht weniger K2-Fehler als Sol als Baseline. Dafür steigen bei Sol die K3-Fehler. Zusammen bleibt es etwa gleich.

Mögliche Stellschraube (kontrollierte Websuche und zusätzlicher Agentenschritt): An zentralen Punkten eher ein Regel-Check. Der Agent prüft die tragende Regel nicht nur an seinem eigenen Text, sondern am Gesetz oder am wichtigsten Urteil zu der Frage. Bei Details eher ein Plan oder eine Checkliste (Punkt 1).

### 5. Nach dem ersten Entwurf ändern die Agenten wenig

DeepSeek als Agent überarbeitet fast nie, nur in 2 von 29 Fällen. Sol und Terra als Agent überarbeiten öfter, ändern dabei aber wenig. Bei Sol ändern sich in der Hälfte der überarbeiteten Fälle höchstens etwa 4 von 100 Zeilen der Antwort, bei Terra höchstens etwa 8 von 100. Diese Zahlen beschreiben, wie jeder Agent arbeitet. Sie sind kein Vergleich der Modelle.

Was Sol und Terra als Agent nach dem ersten Entwurf tun, haben wir in allen 60 Fällen Schritt für Schritt angesehen. In allen 60 Fällen lesen sie ihre eigene Lösung noch einmal. Den Sachverhalt und die Aufgabe öffnen sie danach in keinem Fall noch einmal, obwohl sie beides vor dem Entwurf gelesen hatten. Einen gezielten Abgleich mit dem Bearbeitungshinweis gab es nur bei Sol als Agent, in 2 von 30 Fällen. Sonst prüfen oder ändern die Agenten vor allem Normzitate und einzelne Punkte. Jeder der beiden Agenten hat 30 Fälle. Sol als Agent hat 27 davon nach dem Entwurf überarbeitet. Dabei ging es in 20 Fällen um Normzitate und in 13 um einzelne inhaltliche Punkte, teils um beides. Terra als Agent hat 15 seiner 30 Fälle überarbeitet. Dabei ging es in 6 Fällen um Normzitate und in 10 um einzelne inhaltliche Punkte, teils um beides. In den anderen 15 Fällen hat Terra als Agent nichts mehr geändert.

Oft kündigen die Agenten eine bestimmte Prüfung an, lesen dann die Lösung einmal durch und suchen oder ändern danach nichts zu diesem Punkt. Bei Sol als Agent ist das in 22 von 30 Fällen so, bei Terra als Agent in 8 von 30. Ein Beispiel: In ZR22 schreibt Terra als Agent, er prüfe noch, ob alle drei Fallfragen vollständig behandelt sind. Kurz davor hat er die Lösung einmal ganz gelesen. Danach sieht er nur noch nach, ob die Datei da ist, und meldet am Ende, die Lösung behandle alle drei Fallfragen. Ob er dabei im Kopf geprüft hat, wissen wir nicht, weil das Reasoning nicht als Text im Protokoll steht.

Sol und DeepSeek als Agent bestehen insgesamt deutlich mehr Kriterien als ihre Baseline, Terra als Agent nicht. Ob das an der Überarbeitung liegt, ist offen. Der Agent unterscheidet sich auch sonst von der Baseline. Er bekommt den Sachverhalt als Datei statt im Prompt. DeepSeek als Agent läuft außerdem mit einer anderen Reasoning-Stufe.

Mögliche Stellschraube (zusätzlicher Agentenschritt): ein Schlusscheck, der Plan und Fallfragen ausdrücklich mit der fertigen Antwort vergleicht.

### 6. Mit Websuche besteht Codex mehr Kriterien, hat aber kaum weniger falsche Inhalte

Mit Websuche hat Codex 82 Kriterien mehr bestanden als ohne. Das sind im Schnitt knapp 3 je Fall. In 22 von 30 Fällen war Codex mit Websuche besser, in 4 schlechter.

Bei falschen Inhalten ändert sich zusammen wenig. Falsch dargestellte Regeln (K3) gibt es mit Websuche 14 weniger, falsche Anwendungen auf den Sachverhalt (K2) 9 mehr. Keins von beiden zeigt sich deutlich über die Fälle. Von den falschen Normzitaten (K5) ohne Websuche ist mit Websuche gut die Hälfte behoben. Dafür gibt es neue.

Ein Teil des Gewinns kann aus Lösungen im Netz kommen. In zwei Fällen (OER15, ZR30) gibt Codex selbst an, eine im Netz veröffentlichte Lösung genau dieses Falls benutzt zu haben. In zwei weiteren Fällen (OER10, OER13) hat Codex die Gerichtsentscheidung gefunden, auf der der Fall beruht. Bei OER13 wissen wir das nur aus der eigenen Angabe von Codex. So eine Entscheidung zu finden ist erlaubte Recherche. Der Fall wird dadurch aber eher zum Nachschlagen. Lässt man diese vier Fälle weg, hat Codex mit Websuche noch 50 Kriterien mehr bestanden statt 82.

Welche Quelle welche Verbesserung gebracht hat, wissen wir nicht. Was benutzt wurde, sagt nur Codex selbst.

Mögliche Stellschraube (kontrollierte Websuche): die Websuche gezielt auf Gesetzestexte und wichtige Urteile lenken.

### 7. Ein Drittel der Fehler steckt in Kriterien, die kein Arm besteht

144 von 1.121 Kriterien hat kein einziger Arm bestanden. Auf diese Kriterien fällt ein Drittel aller Fehler (32 %). Gut die Hälfte dieser Fehler ist K1a. Sie zählen also auch bei Punkt 1.

Dort mischen sich zwei Dinge: echte Lücken der Modelle und Anforderungen der Rubric, die die Annotatoren für fraglich halten. Ob diese Anforderungen über das juristisch Nötige hinausgehen, müssen Juristen prüfen. Welche Gruppe größer ist, wissen wir nicht. Wir haben 15 dieser Kriterien genauer angesehen. 9 davon wurden als echte Lücke eingeordnet. Eine Nachprüfung hat 5 dieser 9 Einordnungen beanstandet. Echte Lücken sind also zwischen 4 und 9 von 15.

Juristen sollten diese Kriterien prüfen, bevor Schritt 2 sie als Ziel nimmt.

Mögliche Stellschraube (Skill): für bestätigte Lücken eher ein Skill als ein geänderter Prompt. Der Skill enthält Sonderregeln und sagt, welche Vorschrift gilt, wenn mehrere passen.

### 8. Ob ein einzelnes Kriterium wegen des Agenten wechselt, ist unsicher

Gemeint ist: Ein Kriterium fällt bei der Baseline durch und besteht beim Agent, oder umgekehrt. Das kann auch an den Judges liegen. Wie stark das Komitee der Studie bei derselben Antwort schwankt, wurde nie direkt gemessen. Es gibt nur zwei Hinweise. Im Hauptlauf waren sich die beiden ersten Judges bei 830 von 8.922 Bewertungen (9 %) uneinig, dort hat der dritte entschieden. Und bei einer Nachbewertung zweier Zivilrechtsfälle mit einem anderen Komitee änderte sich das Ergebnis bei 5 bis 8 von 100 Kriterien.

Nehmen wir grob an, die Judges der Studie schwanken ähnlich wie bei der Nachbewertung. Dann könnte bei Sol, Terra und DeepSeek ein Fünftel bis die Hälfte der Wechsel zwischen Baseline und Agent nur von den Judges kommen. Das ist eine grobe Schätzung. Für Codex lässt sich das nicht sagen, weil die Judges dort andere Rollen haben. Bei Codex bewerten gemini-3.6-flash und luna zuerst, bei Uneinigkeit entscheidet terra. Bei den übrigen sechs Armen bewerten luna und terra zuerst, und gemini-3.6-flash entscheidet.

Dazu kommt, dass die Antworten selbst von Lauf zu Lauf schwanken. Das ist nicht gemessen, weil jeder Arm nur einmal lief. Der Anteil der Wechsel, der nur Zufall ist, kann also noch höher sein.

Verlassen kann man sich deshalb nur auf die Summe über viele Fälle, also wie viele Kriterien mit Agent insgesamt mehr bestanden werden. Ein einzelner Wechsel sagt wenig.
