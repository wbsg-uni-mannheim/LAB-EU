# Review: Fortgeschrittenenklausur: Kontaktloses Bezahlen

- **System:** deepseek/deepseek-v4-pro (baseline-single-call)
- **Ergebnis:** 25/65 Kriterien erfüllt (38%)
- **Judge:** gpt-5.6-luna, 1 Vote(s) pro Kriterium
- **Nach Station:** Zweiter Handlungsabschnitt: Im Supermarkt 23/56 (41%) · Erster Handlungsabschnitt: Das Einstecken der EC-Karte 2/8 (25%) · Gesamtergebnis 0/1 (0%)
- **Nach Wichtigkeit:** ★★★ 3/7 (43%) · ★★ 21/53 (40%) · ★ 1/5 (20%)

---

## Lösung des Systems

# Falllösung – Fortgeschrittenenklausur: Kontaktloses Bezahlen

**Wie hat sich A nach dem StGB strafbar gemacht?**

---

## A. Strafbarkeit des A wegen Computerbetrugs gemäß § 263a Abs. 1 StGB

A könnte sich wegen Computerbetrugs nach § 263a Abs. 1 StGB strafbar gemacht haben, indem er im Supermarkt die von ihm gefundene EC-Karte des V an das Kartenlesegerät hielt und so einen Zahlungsvorgang über 32,76 € auslöste.

### I. Tatbestand

#### 1. Objektiver Tatbestand

**a) Tathandlung: Einwirken auf das Ergebnis einer Datenverarbeitung durch eine der in § 263a Abs. 1 StGB genannten Begehungsweisen**

§ 263a Abs. 1 StGB setzt voraus, dass der Täter das Ergebnis einer Datenverarbeitung durch unrichtige Gestaltung des Programms, durch Verwendung unrichtiger oder unvollständiger Daten, durch unbefugte Verwendung von Daten oder sonst durch unbefugte Einwirkung auf den Ablauf beeinflußt.

Vorliegend hat A die im Park gefundene EC-Karte des V an das vom Kassenpersonal K aktivierte Kartenlesegerät gehalten. Dadurch wurden über den NFC-Chip die Kartennummer und das Gültigkeitsdatum der Karte an das Lesegerät übertragen. Das Lesegerät sandte diese Daten zusammen mit den Kontodaten der R-GmbH als Zahlungsempfängerin und dem Rechnungsbetrag an das Zahlungssystem der Sparkasse Göttingen. Im Zahlungssystem erfolgte daraufhin eine automatisierte Prüfung (Kartensperre, Verfügungsrahmen, Voraussetzungen für PIN-Verzicht) und schließlich die Autorisierung des Zahlungsvorgangs.

Diese Autorisierung ist das Ergebnis eines Datenverarbeitungsvorgangs. A hat auf dieses Ergebnis durch die Verwendung der auf dem Chip gespeicherten Daten eingewirkt, denn ohne das Vorhalten der Karte wäre die Autorisierung nicht erfolgt.

Fraglich ist, welche Variante des § 263a Abs. 1 StGB einschlägig ist. In Betracht kommt vor allem die unbefugte Verwendung von Daten (§ 263a Abs. 1 Var. 3 StGB). „Daten“ im Sinne der Vorschrift sind alle codierten Informationsgehalte. Die EC-Karte enthielt als elektronische Daten insbesondere die Kartennummer und das Gültigkeitsdatum. Diese Daten hat A verwendet, indem er die Karte an das Lesegerät hielt und so die Übertragung und Verarbeitung dieser Daten veranlasste.

Die Verwendung muss „unbefugt“ sein. Unbefugt handelt, wer Daten gegen den wirklichen oder mutmaßlichen Willen des Berechtigten verwendet. Berechtigter ist hier der Karteninhaber V, dem die EC-Karte von der Sparkasse überlassen wurde. V hatte A zu keiner Zeit gestattet, die Karte zu benutzen. A handelte ohne und gegen den Willen des V. Die Nutzung der Daten war deshalb unbefugt.

Mithin liegt eine unbefugte Verwendung von Daten im Sinne des § 263a Abs. 1 Var. 3 StGB vor.

**b) Taterfolg: Vermögensschaden**

Ein Computerbetrug erfordert weiterhin einen Vermögensschaden. Die durch die Autorisierung entstandene zivilrechtliche Lage führte bei der Sparkasse Göttingen zu einer endgültigen Vermögensminderung. Zwar erwarb die R-GmbH durch die Autorisierung eine einredefreie Forderung gegen die Sparkasse; zugleich wurde auf dem Konto des V zunächst eine Belastung vermerkt. Nachdem V einige Tage später die unberechtigte Buchung reklamierte, schrieb die Sparkasse ihm den Betrag aber gemäß den gesetzlichen Regelungen (§§ 675u, 675v BGB) wieder gut, sodass letztlich die Bank den Schaden in Höhe von 32,76 € trug. Eine Ersatzmöglichkeit gegen A besteht nach den zivilrechtlichen Vorschriften nicht. Damit ist bei der Sparkasse ein effektiver Vermögensschaden in Höhe von 32,76 € eingetreten.

**c) Kausalität und objektive Zurechnung**

Der Vermögensschaden der Sparkasse ist kausal auf die unbefugte Datenverwendung durch A zurückzuführen. Hätte A die Karte nicht an das Lesegerät gehalten, wäre die Autorisierung nicht erfolgt und der Schaden nicht entstanden. Das Verhalten des A hat das spezifische Risiko verwirklicht, das § 263a StGB erfassen will – die zweckwidrige Inanspruchnahme automatisierter Zahlungssysteme. Die objektive Zurechnung ist daher zu bejahen.

**d) Stoffgleichheit**

Schließlich ist erforderlich, dass der vom Täter erstrebte Vermögensvorteil und der eingetretene Schaden stoffgleich sind (§ 263a Abs. 1 i.V.m. § 263 Abs. 1 StGB). A wollte sich durch die Tat einen „kleinen Finderlohn“ verschaffen. Er hat die Lebensmittel und Getränke im Wert von 32,76 € erlangt, ohne dafür eine eigene Gegenleistung zu erbringen. Dieser Vermögensvorteil entspricht exakt dem Schaden, den die Sparkasse erlitten hat, denn die Bank musste den Kaufpreis an die R-GmbH auskehren und kann diesen Betrag nicht zurückerlangen. Vorteil und Schaden sind daher stoffgleich.

#### 2. Subjektiver Tatbestand

**a) Vorsatz**

A handelte mit Wissen und Wollen bezüglich aller objektiven Tatbestandsmerkmale. Ihm war bewusst, dass er die EC-Karte des V ohne dessen Erlaubnis benutzte, und er wusste oder nahm zumindest billigend in Kauf, dass sein Verhalten eine Datenverarbeitung auslöst („ihm ist aber bewusst, dass dabei Daten übertragen und gespeichert werden“). Dass er die genauen technischen Abläufe und die zivilrechtliche Risikoverteilung nicht im Einzelnen kannte, ist unerheblich; es genügt, dass er die wesentliche Bedeutung seines Tuns – die unberechtigte Nutzung eines fremden Zahlungsinstruments – erfasste. Ebenso nahm er billigend in Kauf, dass irgendein Vermögensträger (hier die Bank) letztlich einen Vermögensnachteil erleiden würde. Sein Vorsatz umfasst daher auch den Vermögensschaden.

**b) Bereicherungsabsicht**

Für die Verwirklichung des § 263a Abs. 1 StGB ist zudem die Absicht erforderlich, sich oder einem Dritten einen rechtswidrigen Vermögensvorteil zu verschaffen. A handelte mit dem Ziel, ohne eigenes Entgelt Waren im Wert von 32,76 € zu erhalten. Dieser Vorteil war rechtswidrig, weil A keinen Anspruch auf die Leistung der Sparkasse oder auf eine unentgeltliche Warenlieferung besaß. Die Bereicherungsabsicht ist damit gegeben.

### II. Rechtswidrigkeit

Rechtfertigungsgründe sind nicht ersichtlich. A handelte rechtswidrig.

### III. Schuld

A handelte schuldhaft. Anhaltspunkte für Schuldausschließungs- oder Entschuldigungsgründe sind nicht gegeben. A wusste, dass er die Karte nicht verwenden durfte und handelte dennoch aus Eigennutz.

### IV. Ergebnis zu § 263a StGB

A hat sich wegen Computerbetrugs gemäß § 263a Abs. 1 Var. 3 StGB strafbar gemacht.

---

## B. Strafbarkeit des A wegen Fälschung beweiserheblicher Daten gemäß § 269 Abs. 1 StGB

A könnte sich durch denselben Vorgang auch wegen Fälschung beweiserheblicher Daten gemäß § 269 Abs. 1 StGB strafbar gemacht haben.

### I. Tatbestand

#### 1. Objektiver Tatbestand

**a) Beweiserhebliche Daten**

§ 269 Abs. 1 StGB schützt die Sicherheit und Beweisfunktion von Daten im Rechtsverkehr. Als beweiserheblich gelten Daten, die – ähnlich wie Urkunden – dazu bestimmt und geeignet sind, rechtserhebliche Tatsachen zu beweisen. Die im Zahlungssystem der Sparkasse gespeicherten Datensätze über den Zahlungsvorgang (Transaktionsdaten, Aktualisierung des Verfügungsrahmens und der PIN-Zähler) sind beweiserhebliche Daten. Sie dienen im Rechtsverkehr dem Nachweis von Zahlungsvorgängen, insbesondere gegenüber dem Karteninhaber oder in etwaigen Streitigkeiten.

**b) Tathandlung: Speichern oder Gebrauchen unechter oder verfälschter Daten**

A selbst hat die Daten nicht eigenhändig in das Bankensystem eingegeben, sondern durch das Vorhalten der EC-Karte die automatisierte Speicherung ausgelöst. Die strafbare Handlung kann in dieser Fallkonstellation entweder als mittelbares Speichern oder als Gebrauchen der hierbei entstehenden unechten Daten erfasst werden. Nach der Rechtsprechung und herrschenden Lehre macht sich derjenige, der eine fremde EC-Karte unbefugt einsetzt und dadurch die Erzeugung eines Zahlungsdatensatzes veranlasst, wegen Gebrauchens unechter beweiserheblicher Daten strafbar (§ 269 Abs. 1 Var. 2 StGB).

Die so erzeugten und gespeicherten Daten müssen unecht oder verfälscht sein, d.h. bei ihrer Wahrnehmung würde eine unechte oder verfälschte Urkunde vorliegen. Ein Datensatz ist unecht, wenn er nicht von demjenigen stammt, von dem er scheinbar herrührt. Der hier gespeicherte Zahlungsvorgang erweckt den Anschein, der berechtigte Karteninhaber V habe persönlich die Zahlung autori- siert. Tatsächlich ging die Veranlassung jedoch von dem unbefugten A aus. Damit täuscht der Datensatz über die Identität des wahren Erklärenden und ist folglich unecht. A hat diese unechten Daten gebraucht, indem er sie durch das Vorhalten der Karte hervorrief und sie als Grundlage des Zahlungsvorgangs einsetzte.

**c) Zur Täuschung im Rechtsverkehr**

Die Speicherung und spätere Verwendung der Daten erfolgte, um im Rechtsverkehr über die wirkliche Beteiligung am Zahlungsvorgang zu täuschen. A handelte bei der Benutzung der Karte mit dem Ziel, die R-GmbH und die Sparkasse über seine mangelnde Berechtigung hinwegzutäuschen und so die Waren zu erlangen. Die Tatbestandsvoraussetzung des Handelns zur Täuschung im Rechtsverkehr ist daher erfüllt.

#### 2. Subjektiver Tatbestand

A handelte vorsätzlich. Er wusste, dass er die EC-Karte unbefugt verwendete und dass dadurch ein elektronischer Zahlungsvorgang einschließlich einer dauerhaften Speicherung von Daten ausgelöst würde. Dass ihm die genauen technischen Einzelheiten nicht bekannt waren, ändert nichts an seinem Vorsatz bezüglich des wesentlichen Unrechtsgehalts – er wusste, dass Daten übertragen und gespeichert werden und dass niemand einfach fremde EC-Karten nutzen darf. Auch die Täuschungsabsicht ist gegeben, weil es ihm gerade darauf ankam, der Zahlungsempfängerin und der Bank vorzuspiegeln, es handele sich um einen berechtigten Karteneinsatz.

### II. Rechtswidrigkeit und Schuld

Rechtfertigungs- oder Entschuldigungsgründe sind nicht erkennbar. A handelte rechtswidrig und schuldhaft.

### III. Ergebnis zu § 269 StGB

A hat sich auch wegen Fälschung beweiserheblicher Daten gemäß § 269 Abs. 1 Var. 2 StGB strafbar gemacht.

---

## C. Weitere Straftatbestände

### I. Betrug gemäß § 263 StGB

Ein zurechenbarer Betrug scheidet aus. Zwar könnte in dem Auftreten des A an der Kasse eine Täuschung des Kassenpersonals K über seine Zahlungsberechtigung liegen. Ein Betrug erfordert jedoch einen hierdurch verursachten Irrtum, der zu einer Vermögensverfügung und einem unmittelbaren Vermögensschaden bei dem Getäuschten oder einem Dritten führt. Vorliegend verliert weder K noch die R-GmbH eigenes Vermögen; die R-GmbH erwirbt durch die Autorisierung eine einredefreie Forderung gegen die Sparkasse, sodass sie keinen Schaden erleidet. Der einzige Schaden entsteht später bei der Sparkasse. Deren Vermögensverfügung (die Autorisierung der Zahlung) beruht jedoch nicht auf einer Täuschung des K durch A, sondern auf dem automatisierten Datenverarbeitungsvorgang. Die Täuschung des K ist für den Schaden der Bank weder kausal noch diesem objektiv zurechenbar. Im Übrigen tritt § 263 StGB hinter den spezielleren Computerbetrug nach § 263a StGB zurück, wenn das Vermögen durch manipulierte Datenverarbeitung geschädigt wird. Eine Strafbarkeit gemäß § 263 StGB liegt daher nicht vor.

### II. Mißbrauch von Scheck- und Kreditkarten gemäß § 266b StGB

§ 266b StGB setzt voraus, dass der Täter die Karte vom Karteninhaber oder Aussteller überlassen bekommen hat. A hat die EC-Karte des V jedoch auf dem Spielplatz gefunden, nicht von V oder der Sparkasse ausgehändigt erhalten. Es fehlt mithin an dem erforderlichen Überlassungsverhältnis. Eine Strafbarkeit nach § 266b StGB scheidet aus.

### III. Unterschlagung der EC-Karte gemäß § 246 StGB

A könnte sich den Besitz an der EC-Karte durch die Wegnahme vom Boden rechtswidrig zugeeignet haben. Eine Unterschlagung erfordert jedoch die Zueignung der Sache, d.h. der Täter muss sich oder einem Dritten die Sache auf Dauer oder zumindest für eine nicht ganz unerhebliche Zeit aneignen. A hat die Karte zunächst an sich genommen, um sie zur Sparkasse zu bringen; zu diesem Zeitpunkt fehlte ihm jeglicher Zueignungswille. Als er sich später entschloss, die Karte kurz zum Bezahlen zu benutzen, hatte er nicht die Absicht, die Karte dauerhaft zu behalten, sondern sie anschließend wie ursprünglich geplant in den Briefkasten der Sparkasse zu werfen. Eine bloß vorübergehende Nutzung ohne dauerhafte Enteignung des Eigentümers genügt nicht für den Zueignungstatbestand. A hat sich die EC-Karte daher nicht i.S.v. § 246 StGB zugeeignet. Eine Unterschlagung liegt nicht vor.

### IV. Diebstahl der Waren gemäß § 242 StGB

Indem A die Waren an sich nahm und den Supermarkt verließ, könnte ein Diebstahl vorliegen. Jedoch hat A die Waren aufgrund eines zivilrechtlich wirksamen Kaufvertrags mit der R-GmbH erworben; durch die Einigung über den Eigentumsübergang und die Übergabe wurde A Eigentümer. Die Autorisierung der Kartenzahlung war zivilrechtlich selbst dann wirksam, wenn A nicht der berechtigte Karteninhaber war, da K keine positive Kenntnis von der fehlenden Berechtigung hatte. A hat die Waren daher nicht „weggenommen“, sondern als Erfüllung des Kaufvertrags erhalten. Ein Diebstahl scheidet aus.

---

## D. Konkurrenzen und Gesamtergebnis

Die durch Computerbetrug gemäß § 263a Abs. 1 StGB und die durch Fälschung beweiserheblicher Daten gemäß § 269 Abs. 1 StGB verwirklichten Straftatbestände wurden durch ein und dieselbe Handlung des A – das Vorhalten der EC-Karte an der Kasse und das Auslösen der anschließenden Datenverarbeitung – begangen. Beide Tatbestände stehen daher im Verhältnis der Tateinheit (Idealkonkurrenz) gemäß § 52 StGB.

Sonstige Straftatbestände sind nicht verwirklicht.

**A hat sich damit wegen Computerbetrugs in Tateinheit mit Fälschung beweiserheblicher Daten strafbar gemacht.**

---

## Bewertung nach Rubrik

### A Erster Handlungsabschnitt: Das Einstecken der EC-Karte — 2/8

#### A.I Diebstahl der EC-Karte gem. § 242 Abs. 1 StGB — 0/5

**A.I.1 Tatbestandsmäßigkeit — 0/5**

**❌ FALSE — C-001: EC-Karte als Diebstahlsobjekt** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort die im Cheltenham-Park gefundene, auf V ausgestellte EC-Karte bei § 242 Abs. 1 StGB als für A fremde bewegliche Sache einordnet. NICHT ERFÜLLT, wenn sie die Karte als nicht körperlich, nicht beweglich, A gehörend oder als untaugliches Diebstahlsobjekt behandelt.

**Begründung des Judge:** Die Antwort behandelt die EC-Karte bei § 246 StGB als Sache und erwähnt ihre Wegnahme vom Boden, ordnet sie aber bei § 242 Abs. 1 StGB nicht ausdrücklich als für A fremde bewegliche Sache ein. Der Abschnitt zu § 242 betrifft ausschließlich die Waren.

**Belege:** „A könnte sich den Besitz an der EC-Karte durch die Wegnahme vom Boden rechtswidrig zugeeignet haben.“; „Eine Unterschlagung erfordert jedoch die Zueignung der Sache“

**❌ FALSE — C-002: Wegnahmebegriff bei § 242 StGB** _(★★, rule_statement)_

**Kriterium:** ERFÜLLT, wenn die Antwort Wegnahme im Sinne des § 242 Abs. 1 StGB als Bruch fremden Gewahrsams bei Begründung neuen Gewahrsams oder sinngleich definiert. NICHT ERFÜLLT, wenn sie bloßes Auffinden, Einstecken oder Sachentziehung ohne Gewahrsamsbruch genügen lässt.

**Begründung des Judge:** Die Antwort prüft zwar den Begriff der Wegnahme, definiert ihn aber nicht als Bruch fremden Gewahrsams bei Begründung neuen Gewahrsams und lässt auch keine sinngleiche Definition erkennen.

**Belege:** „Indem A die Waren an sich nahm und den Supermarkt verließ, könnte ein Diebstahl vorliegen.“; „A hat die Waren daher nicht „weggenommen“, sondern als Erfüllung des Kaufvertrags erhalten.“

**❌ FALSE — C-003: Kein Gewahrsam des V an der verlorenen Karte** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort feststellt, dass V im Zeitpunkt des Einsteckens durch A keinen Gewahrsam mehr an der EC-Karte hatte, weil sie im öffentlich zugänglichen Cheltenham-Park außerhalb seines räumlichen Herrschaftsbereichs zurückblieb. NICHT ERFÜLLT, wenn sie V allein wegen Eigentums, Rückerlangungswillens oder späterer Verlustbemerkung weiterhin Gewahrsam zuschreibt.

**Begründung des Judge:** Die Antwort stellt nicht fest, dass V im Zeitpunkt des Einsteckens durch A keinen Gewahrsam mehr an der Karte hatte. Insbesondere fehlt die Begründung, dass die Karte im öffentlich zugänglichen Park außerhalb von V's räumlichem Herrschaftsbereich zurückgeblieben war. Die Ausführungen behandeln lediglich den fehlenden Zueignungswillen des A.

**Belege:** „A könnte sich den Besitz an der EC-Karte durch die Wegnahme vom Boden rechtswidrig zugeeignet haben.“; „Eine Unterschlagung liegt nicht vor.“

**❌ FALSE — C-004: Kein Drittgewahrsam im öffentlichen Park** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort verneint, dass vor A ein Dritter Gewahrsam an der unter einer Bank im öffentlich zugänglichen Cheltenham-Park liegenden EC-Karte erlangt hatte. NICHT ERFÜLLT, wenn sie ohne tragfähige Begründung Gewahrsam der Stadt, eines Parkbetreibers oder sonstiger Dritter annimmt.

**Begründung des Judge:** Die Antwort behandelt lediglich den fehlenden Zueignungswillen und verneint nicht ausdrücklich, dass die Stadt, ein Parkbetreiber oder ein sonstiger Dritter Gewahrsam an der unter der Bank liegenden Karte hatte. Eine tragfähige Prüfung des Drittgewahrsams im öffentlich zugänglichen Park fehlt.

**Belege:** „A könnte sich den Besitz an der EC-Karte durch die Wegnahme vom Boden rechtswidrig zugeeignet haben.“; „A hat die Karte zunächst an sich genommen, um sie zur Sparkasse zu bringen; zu diesem Zeitpunkt fehlte ihm jeglicher Zueignungswille.“

**❌ FALSE — C-005: Keine Wegnahme der EC-Karte** _(★★, conclusion)_

**Kriterium:** ERFÜLLT, wenn die Antwort den Diebstahl der EC-Karte durch das Einstecken im Park mangels Wegnahme ablehnt, weil A keinen fremden Gewahrsam brach. NICHT ERFÜLLT, wenn sie A wegen Diebstahls der EC-Karte bestraft oder den Gewahrsamsbruch ungeprüft unterstellt.

**Begründung des Judge:** Die Antwort prüft keinen Diebstahl der EC-Karte und lehnt eine Wegnahme mangels fehlenden fremden Gewahrsams nicht ab. Vielmehr bezeichnet sie das Aufnehmen der Karte als „Wegnahme“ und verneint lediglich die Zueignungsabsicht für eine Unterschlagung. Damit ist das geforderte Fehlen eines Gewahrsamsbruchs nicht festgestellt.

**Belege:** „A könnte sich den Besitz an der EC-Karte durch die Wegnahme vom Boden rechtswidrig zugeeignet haben.“; „A hat die Karte zunächst an sich genommen, um sie zur Sparkasse zu bringen; zu diesem Zeitpunkt fehlte ihm jeglicher Zueignungswille.“

#### A.II Unterschlagung der EC-Karte gem. § 246 Abs. 1 StGB — 2/3

**❌ FALSE — C-006: Zueignungserfordernis bei § 246 StGB** _(★★, rule_statement)_

**Kriterium:** ERFÜLLT, wenn die Antwort für § 246 Abs. 1 StGB eine objektiv manifestierte Zueignung verlangt, deren Wille zumindest einen Vorsatz dauernder Enteignung umfasst. NICHT ERFÜLLT, wenn sie bloßen Besitz, bloßen Gebrauch, bloßes Finden oder kurzfristiges Behalten als Zueignung genügen lässt.

**Begründung des Judge:** Die Antwort verlangt zutreffend einen zumindest auf dauernde Enteignung gerichteten Willen und lässt bloßen kurzfristigen Gebrauch nicht genügen. Eine objektiv manifestierte Zueignung wird jedoch nicht ausdrücklich verlangt oder geprüft; zudem wird die Aneignung teilweise fälschlich an eine gewisse zeitliche Dauer geknüpft.

**Belege:** „Eine Unterschlagung erfordert jedoch die Zueignung der Sache, d.h. der Täter muss sich oder einem Dritten die Sache auf Dauer oder zumindest für eine nicht ganz unerhebliche Zeit aneignen.“; „Eine bloß vorübergehende Nutzung ohne dauerhafte Enteignung des Eigentümers genügt nicht für den Zueignungstatbestand.“

**✅ TRUE — C-007: Kein anfänglicher Zueignungswille an der EC-Karte** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort beim Einstecken der EC-Karte im Park den Zueignungswillen des A verneint, weil A die Karte zunächst in einer Sparkassenfiliale abgeben wollte. NICHT ERFÜLLT, wenn sie trotz dieses Rückführungswillens aus dem Einstecken allein einen Enteignungsvorsatz herleitet.

**Begründung des Judge:** Die Antwort verneint beim Einstecken der EC-Karte ausdrücklich den Zueignungswillen, weil A sie zunächst zur Sparkasse bringen und abgeben wollte.

**Belege:** „A hat die Karte zunächst an sich genommen, um sie zur Sparkasse zu bringen; zu diesem Zeitpunkt fehlte ihm jeglicher Zueignungswille.“

**✅ TRUE — C-008: Keine anfängliche Unterschlagung der EC-Karte** _(★★, conclusion)_

**Kriterium:** ERFÜLLT, wenn die Antwort eine Strafbarkeit des A nach § 246 Abs. 1 StGB durch das bloße Einstecken der gefundenen EC-Karte ablehnt. NICHT ERFÜLLT, wenn sie § 246 Abs. 1 StGB bereits wegen des Auffindens oder Mitnehmens bejaht, obwohl A die Karte zunächst bei der Sparkasse abgeben wollte.

**Begründung des Judge:** Die Antwort lehnt eine Strafbarkeit nach § 246 Abs. 1 StGB aufgrund des bloßen Auffindens und Einsteckens der EC-Karte ausdrücklich ab, weil A sie zunächst bei der Sparkasse abgeben wollte und anfänglich keinen Zueignungswillen hatte.

**Belege:** „A hat die Karte zunächst an sich genommen, um sie zur Sparkasse zu bringen; zu diesem Zeitpunkt fehlte ihm jeglicher Zueignungswille.“; „A hat sich die EC-Karte daher nicht i.S.v. § 246 StGB zugeeignet. Eine Unterschlagung liegt nicht vor.“

### B Zweiter Handlungsabschnitt: Im Supermarkt — 23/56

#### B.I Betrug ggü. K zu Lasten der R-GmbH gem. § 263 Abs. 1 StGB — 5/8

**B.I.1 Tatbestandsmäßigkeit — 4/7**

**B.I.1.a Objektiver Tatbestand — 4/7**

**❌ FALSE — C-013: Vermögensverfügung bei bejahtem Irrtum** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei bejahtem Irrtum des K die Vermögensverfügung in der Übereignung oder Besitzübertragung der Waren durch K als Vertreter der R-GmbH sieht; ebenfalls ERFÜLLT, wenn sie den Betrug bereits vertretbar am Irrtum scheitern lässt. NICHT ERFÜLLT, wenn sie bei bejahtem Irrtum die Verfügung allein in der Autorisierung durch das Zahlungssystem, die Sparkasse oder V verortet.

**Begründung des Judge:** Die Antwort lässt einen Irrtum des K offen, ordnet die maßgebliche Vermögensverfügung bei bejahtem Irrtum aber nicht in der Übereignung oder Besitzübertragung der Waren durch K als Vertreter der R-GmbH ein. Stattdessen verortet sie die Vermögensverfügung allein in der Autorisierung durch das Zahlungssystem. Ein vertretbares Scheitern des Betrugs bereits am Irrtum wird ebenfalls nicht angenommen.

**Belege:** „„Zwar könnte in dem Auftreten des A an der Kasse eine Täuschung des K über seine Zahlungsberechtigung liegen.““; „„Deren Vermögensverfügung (die Autorisierung der Zahlung) beruht jedoch nicht auf einer Täuschung des K durch A, sondern auf dem automatisierten Datenverarbeitungsvorgang.““

**✅ TRUE — C-014: Kein Betrugsschaden der R-GmbH** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei der Betrugsschadensprüfung berücksichtigt, dass die R-GmbH durch die Autorisierung des Zahlungsvorgangs über 32,76 € eine einredefreie Forderung gegen die Sparkasse erwirbt und deshalb durch die Warenhingabe keinen endgültigen Schaden erleidet; ebenfalls ERFÜLLT, wenn sie den Betrug bereits vertretbar am Irrtum scheitern lässt. NICHT ERFÜLLT, wenn sie einen Schaden der R-GmbH allein aus dem Verlust der Waren bejaht und den Forderungserwerb ignoriert.

**Begründung des Judge:** Die Antwort berücksichtigt ausdrücklich, dass die R-GmbH durch die Autorisierung eine einredefreie Forderung gegen die Sparkasse erwirbt. Daher erleidet sie durch die Warenhingabe keinen endgültigen Vermögensschaden.

**Belege:** „Die R-GmbH erwirbt durch die Autorisierung eine einredefreie Forderung gegen die Sparkasse, sodass sie keinen Schaden erleidet.“; „Vorliegend verliert weder K noch die R-GmbH eigenes Vermögen“

**✅ TRUE — C-015: Keine unmittelbare Betrugsverfügung zulasten V oder Sparkasse** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei einem möglichen Schaden der Sparkasse oder des V im Rahmen von § 263 StGB erkennt, dass dieser nicht unmittelbar aus der Warenverfügung des K folgt, sondern allenfalls aus dem computergestützten Zahlungsvorgang; ebenfalls ERFÜLLT, wenn sie den Betrug bereits vertretbar vorher ablehnt. NICHT ERFÜLLT, wenn sie einen Betrug zulasten V oder der Sparkasse über K bejaht, ohne den fehlenden Unmittelbarkeitszusammenhang zu prüfen.

**Begründung des Judge:** Die Antwort lehnt einen Betrug zulasten der Sparkasse beziehungsweise der R-GmbH vertretbar ab und erkennt ausdrücklich, dass der Schaden der Sparkasse nicht unmittelbar aus der Warenverfügung des K folgt, sondern aus dem automatisierten Zahlungsvorgang. Damit wird der fehlende Unmittelbarkeitszusammenhang geprüft und zutreffend berücksichtigt.

**Belege:** „„Ein Betrug erfordert jedoch einen hierdurch verursachten Irrtum, der zu einer Vermögensverfügung und einem unmittelbaren Vermögensschaden bei dem Getäuschten oder einem Dritten führt.““; „„Deren Vermögensverfügung (die Autorisierung der Zahlung) beruht jedoch nicht auf einer Täuschung des K durch A, sondern auf dem automatisierten Datenverarbeitungsvorgang.““; „„Eine Strafbarkeit gemäß § 263 StGB liegt daher nicht vor.““

**B.I.1.a.aa Täuschung — 1/1**

**✅ TRUE — C-010: Erklärungswert des kontaktlosen Karteneinsatzes** _(★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort entweder im Halten der auf V ausgestellten EC-Karte an das Lesegerät eine konkludente Erklärung sieht, A sei berechtigter Karteninhaber oder bevollmächtigt, und dies etwa mit Namenszuordnung, Bankbedingungen oder Verkehrserwartung begründet, oder diese Erklärung verneint und dies mit der zivilrechtlichen Risikoverteilung begründet, wonach die R-GmbH grundsätzlich unabhängig von der Berechtigung des Kartennutzers eine einredefreie Forderung gegen die Sparkasse erwirbt. NICHT ERFÜLLT, wenn sie den Erklärungswert gar nicht prüft oder eine ausdrückliche Berechtigungsbehauptung erfindet.

**Begründung des Judge:** Die Antwort prüft den Erklärungswert des Karteneinsatzes zumindest an: Sie erwägt eine Täuschung über die Zahlungsberechtigung und begründet das Ausscheiden des Betrugs maßgeblich mit der zivilrechtlichen Risikoverteilung, nach der die R-GmbH unabhängig von der Berechtigung des Kartennutzers eine einredefreie Forderung gegen die Sparkasse erwirbt. Damit ist die verlangte Alternative inhaltlich erfüllt.

**Belege:** „Zwar könnte in dem Auftreten des A an der Kasse eine Täuschung des Kassenpersonals K über seine Zahlungsberechtigung liegen.“; „Die R-GmbH erwirbt durch die Autorisierung eine einredefreie Forderung gegen die Sparkasse, sodass sie keinen Schaden erleidet.“; „In zivilrechtlicher Hinsicht ... unabhängig von der Berechtigung des tatsächlichen Kartennutzers“

**B.I.1.a.bb Irrtum — 1/3**

**✅ TRUE — C-009: K als möglicher Irrender beim Betrug** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort beim möglichen Betrug nach § 263 Abs. 1 StGB im Supermarkt als Irrenden nur K als natürliche Person an der Kasse der R-GmbH in Betracht zieht. NICHT ERFÜLLT, wenn sie einen Irrtum des Kartenlesegeräts, Zahlungssystems oder Computers genügen lässt.

**Begründung des Judge:** Die Antwort zieht beim möglichen Betrug ausschließlich K als natürliche Person an der Kasse als möglichen Irrenden in Betracht. Einen Irrtum des Kartenlesegeräts, des Zahlungssystems oder eines sonstigen Computers lässt sie ausdrücklich nicht genügen, sondern ordnet die automatisierte Verarbeitung dem § 263a StGB zu.

**Belege:** „Zwar könnte in dem Auftreten des A an der Kasse eine Täuschung des Kassenpersonals K über seine Zahlungsberechtigung liegen.“; „Die Täuschung des K ist für den Schaden der Bank weder kausal noch diesem objektiv zurechenbar.“; „Deren Vermögensverfügung ... beruht jedoch nicht auf einer Täuschung des K durch A, sondern auf dem automatisierten Datenverarbeitungsvorgang.“

**❌ FALSE — C-011: Sachgedankliches Mitbewusstsein des K** _(★★, rule_statement)_

**Kriterium:** ERFÜLLT, wenn die Antwort erkennt, dass für einen Irrtum des K mangels konkreter Angaben allenfalls ein sachgedankliches Mitbewusstsein in Betracht kommt, etwa die Vorstellung, beim Kartenzahlungsvorgang sei alles in Ordnung. NICHT ERFÜLLT, wenn sie konkrete positive Gedanken des K über die Berechtigung des A behauptet, ohne dass der Sachverhalt dies mitteilt.

**Begründung des Judge:** Die Antwort erkennt zwar eine mögliche Täuschung des K an, setzt sich aber nicht damit auseinander, dass mangels konkreter Angaben zu seinen Vorstellungen allenfalls ein sachgedankliches Mitbewusstsein („beim Kartenzahlungsvorgang sei alles in Ordnung“) angenommen werden kann. Konkrete positive Gedanken des K behauptet sie nicht, die erforderliche Einordnung des möglichen Irrtums fehlt jedoch.

**Belege:** „Zwar könnte in dem Auftreten des A an der Kasse eine Täuschung des K über seine Zahlungsberechtigung liegen.“; „Deren Vermögensverfügung (die Autorisierung der Zahlung) beruht jedoch nicht auf einer Täuschung des K durch A, sondern auf dem automatisierten Datenverarbeitungsvorgang.“

**❌ FALSE — C-012: Irrtum des K über die Kartenberechtigung** _(★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort entweder einen Irrtum des K verneint, weil K wegen des einredefreien Forderungserwerbs der R-GmbH gegen die Sparkasse keine Vorstellung über die Berechtigung des A bilden musste, oder einen Irrtum aufgrund sachgedanklichen Mitbewusstseins annimmt und dann die weiteren Betrugsmerkmale eigenständig prüft. NICHT ERFÜLLT, wenn sie einen Irrtum des K schlicht unterstellt oder den Irrtum mit einer rein technischen Autorisierung verwechselt.

**Begründung des Judge:** Die Antwort stellt eine Täuschung des K lediglich als Möglichkeit dar und behandelt den Irrtum des K nicht eigenständig. Sie verneint insbesondere nicht, dass K wegen des einredefreien Forderungserwerbs keine Vorstellung über die Kartenberechtigung bilden musste, und nimmt auch keinen Irrtum aufgrund sachgedanklichen Mitbewusstseins mit anschließender Prüfung der weiteren Betrugsmerkmale an. Die Aussage, K habe keine positive Kenntnis gehabt, ersetzt die erforderliche Prüfung eines Irrtums nicht.

**Belege:** „„Zwar könnte in dem Auftreten des A an der Kasse eine Täuschung des K über seine Zahlungsberechtigung liegen.““; „„Die Täuschung des K ist für den Schaden der Bank weder kausal noch diesem objektiv zurechenbar.““; „„da K keine positive Kenntnis von der fehlenden Berechtigung hatte““

**B.I.2 Ergebnis — 1/1**

**✅ TRUE — C-016: Kein vollendeter Betrug nach § 263 StGB** _(★★★, conclusion)_

**Kriterium:** ERFÜLLT, wenn die Antwort eine Strafbarkeit des A wegen Betrugs nach § 263 Abs. 1 StGB im Zusammenhang mit dem Supermarktkauf ablehnt, sei es mangels Irrtums des K, mangels Schadens der R-GmbH oder mangels Unmittelbarkeit eines Schadens bei V oder Sparkasse. NICHT ERFÜLLT, wenn sie A wegen Betrugs verurteilt, ohne Forderungserwerb der R-GmbH und Unmittelbarkeit tragfähig zu verarbeiten.

**Begründung des Judge:** Die Antwort lehnt eine vollendete Strafbarkeit wegen Betrugs nach § 263 StGB ausdrücklich ab und begründet dies insbesondere mit dem fehlenden Vermögensschaden der R-GmbH sowie der fehlenden Unmittelbarkeit einer Vermögensverfügung aufgrund der Täuschung.

**Belege:** „Ein zurechenbarer Betrug scheidet aus.“; „Vorliegend verliert weder K noch die R-GmbH eigenes Vermögen“; „Deren Vermögensverfügung (die Autorisierung der Zahlung) beruht jedoch nicht auf einer Täuschung des K durch A, sondern auf dem automatisierten Datenverarbeitungsvorgang.“; „Eine Strafbarkeit gemäß § 263 StGB liegt daher nicht vor.“

#### B.II Computerbetrug gem. § 263a Abs. 1 Var. 3 StGB — 13/29

**B.II.1 Tatbestandsmäßigkeit — 11/27**

**B.II.1.a Objektiver Tatbestand — 7/20**

**B.II.1.a.aa Verwendung von Daten — 2/2**

**✅ TRUE — C-017: Datenverwendung beim kontaktlosen Bezahlen** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort den kontaktlosen Einsatz der EC-Karte des V am Lesegerät als Verwendung von Daten im Sinne des § 263a Abs. 1 Var. 3 StGB einordnet. NICHT ERFÜLLT, wenn sie § 263a StGB schon deshalb ablehnt, weil A keine PIN eingab, keine Tastatur benutzte oder nur eine körperliche Karte vorhielt.

**Begründung des Judge:** Die Antwort ordnet den kontaktlosen Einsatz der EC-Karte am Lesegerät ausdrücklich als Verwendung der auf dem Chip gespeicherten Daten nach § 263a Abs. 1 Var. 3 StGB ein. Sie lehnt die Strafbarkeit nicht wegen fehlender PIN-Eingabe, fehlender Tastaturbenutzung oder des bloßen Vorhaltens der Karte ab.

**Belege:** „In Betracht kommt vor allem die unbefugte Verwendung von Daten (§ 263a Abs. 1 Var. 3 StGB).“; „Diese Daten hat A verwendet, indem er die Karte an das Lesegerät hielt und so die Übertragung und Verarbeitung dieser Daten veranlasste.“; „Mithin liegt eine unbefugte Verwendung von Daten im Sinne des § 263a Abs. 1 Var. 3 StGB vor.“

**✅ TRUE — C-018: Technischer Inhalt der Datenverwendung** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort die Datenverwendung damit verknüpft, dass Daten der auf V ausgestellten EC-Karte, etwa Kartennummer oder Gültigkeitsdatum, in eine Autorisierungsanfrage für die Zahlung über 32,76 € einflossen und an das Zahlungssystem der Sparkasse übermittelt wurden. NICHT ERFÜLLT, wenn sie den Vorgang rein manuell beschreibt oder keine Autorisierungsanfrage mit Kartendaten erkennen lässt.

**Begründung des Judge:** Die Antwort verknüpft die Verwendung der Kartendaten ausdrücklich mit der Übermittlung einer Autorisierungsanfrage über 32,76 € an das Zahlungssystem der Sparkasse.

**Belege:** „„Dadurch wurden über den NFC-Chip die Kartennummer und das Gültigkeitsdatum der Karte an das Lesegerät übertragen.““; „„Das Lesegerät sandte diese Daten zusammen mit den Kontodaten der R-GmbH als Zahlungsempfängerin und dem Rechnungsbetrag an das Zahlungssystem der Sparkasse Göttingen.““; „„Im Zahlungssystem erfolgte daraufhin eine automatisierte Prüfung [...] und schließlich die Autorisierung des Zahlungsvorgangs.““

**B.II.1.a.bb Unbefugt — 1/12**

**❌ FALSE — C-019: Streit um unbefugte Datenverwendung** _(★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort erkennt, dass das Merkmal „unbefugt“ in § 263a Abs. 1 Var. 3 StGB beim PIN-losen Einsatz einer fremden EC-Karte streitig auszulegen ist. NICHT ERFÜLLT, wenn sie die Unbefugtheit ohne Auslegungsmaßstab allein aus der Fremdheit der Karte oder allein aus dem technisch ordnungsgemäßen Ablauf ableitet.

**Begründung des Judge:** Die Antwort leitet die Unbefugtheit allein aus dem fehlenden Willen des Karteninhabers V ab. Sie erkennt nicht, dass die Auslegung des Merkmals „unbefugt“ beim PIN-losen Einsatz einer fremden EC-Karte streitig ist, und erörtert keinen entsprechenden Auslegungsmaßstab oder Gegenansatz.

**Belege:** „Die Verwendung muss „unbefugt“ sein.“; „Unbefugt handelt, wer Daten gegen den wirklichen oder mutmaßlichen Willen des Berechtigten verwendet.“; „A handelte ohne und gegen den Willen des V. Die Nutzung der Daten war deshalb unbefugt.“

**B.II.1.a.bb.1 Vertragsspezifische/subjektivierende Auslegung — 1/2**

**✅ TRUE — C-020: Subjektivierende Auslegung von „unbefugt“** _(★★, rule_statement)_

**Kriterium:** ERFÜLLT, wenn die Antwort die subjektivierende oder vertragsspezifische Auslegung dahin beschreibt, dass Daten unbefugt verwendet werden, wenn die Verwendung dem tatsächlichen oder mutmaßlichen Willen des Berechtigten widerspricht. NICHT ERFÜLLT, wenn sie diese Ansicht mit der computerspezifischen Kontrollmechanismuslehre verwechselt.

**Begründung des Judge:** Die Antwort beschreibt ausdrücklich die subjektivierende bzw. vertragsspezifische Auslegung: Maßgeblich ist der wirkliche oder mutmaßliche Wille des Berechtigten. Sie verwechselt diese Auslegung nicht mit der computerspezifischen Kontrollmechanismuslehre.

**Belege:** „„Unbefugt handelt, wer Daten gegen den wirklichen oder mutmaßlichen Willen des Berechtigten verwendet.““; „„V hatte A zu keiner Zeit gestattet, die Karte zu benutzen. A handelte ohne und gegen den Willen des V.““

**❌ FALSE — C-021: Subjektivierende Auslegung im Fall** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei Darstellung der subjektivierenden Auslegung erkennt, dass A danach unbefugt handelte, weil weder V als Karteninhaber noch die Sparkasse mit der Nutzung der EC-Karte durch A einverstanden waren. NICHT ERFÜLLT, wenn sie nach dieser Ansicht eine Befugnis des A aus dem bloßen Besitz der gefundenen Karte ableitet.

**Begründung des Judge:** Die Antwort wendet zwar die subjektivierende Auslegung an und bejaht die Unbefugtheit wegen des fehlenden Einverständnisses des V. Sie erkennt jedoch nicht ausdrücklich, dass auch die Sparkasse mit der Nutzung durch A nicht einverstanden war. Damit wird das im Kriterium geforderte fehlende Einverständnis beider maßgeblicher Berechtigter nicht vollständig festgestellt.

**Belege:** „„Berechtigter ist hier der Karteninhaber V““; „„V hatte A zu keiner Zeit gestattet, die Karte zu benutzen. A handelte ohne und gegen den Willen des V.““

**B.II.1.a.bb.2 Computerspezifische Auslegung — 0/2**

**❌ FALSE — C-022: Computerspezifische Auslegung von „unbefugt“** _(★★, rule_statement)_

**Kriterium:** ERFÜLLT, wenn die Antwort die computerspezifische Auslegung dahin beschreibt, dass Daten nur unbefugt verwendet werden, wenn ein im Programm angelegter Kontroll- oder Prüfmechanismus irregulär überwunden wird. NICHT ERFÜLLT, wenn sie diese Ansicht auf bloße Willenswidrigkeit gegenüber V oder Sparkasse reduziert.

**Begründung des Judge:** Die Antwort reduziert die Unbefugtheit auf die Nutzung gegen den Willen des Karteninhabers V. Sie beschreibt nicht, dass ein im Programm angelegter Kontroll- oder Prüfmechanismus irregulär überwunden werden muss. Damit fehlt die computerspezifische Auslegung.

**Belege:** „„Unbefugt handelt, wer Daten gegen den wirklichen oder mutmaßlichen Willen des Berechtigten verwendet.““; „„V hatte A zu keiner Zeit gestattet, die Karte zu benutzen. A handelte ohne und gegen den Willen des V.““; „„Die Nutzung der Daten war deshalb unbefugt.““

**❌ FALSE — C-023: Computerspezifische Auslegung im Fall** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort nach computerspezifischer Auslegung die Unbefugtheit verneint, weil das Zahlungssystem beim kontaktlosen Bezahlen ohne PIN keine Berechtigung des Kartenverwenders prüfte, sondern nur technische Kriterien wie Kartensperre, Verfügungsrahmen oder PIN-Verzichtsvoraussetzungen. NICHT ERFÜLLT, wenn sie nach dieser Ansicht Unbefugtheit bejaht, ohne eine überwundene programmierte Berechtigungsprüfung zu benennen.

**Begründung des Judge:** Die Antwort bejaht die Unbefugtheit nach dem Willen des Karteninhabers V. Sie verneint sie nicht nach computerspezifischer Auslegung und benennt keine überwundene programmierte Berechtigungsprüfung; vielmehr wird nur die technische Prüfung von Kartensperre, Verfügungsrahmen und PIN-Verzichtsvoraussetzungen beschrieben.

**Belege:** „Die Nutzung der Daten war deshalb unbefugt.“; „Im Zahlungssystem erfolgte daraufhin eine automatisierte Prüfung (Kartensperre, Verfügungsrahmen, Voraussetzungen für PIN-Verzicht) und schließlich die Autorisierung des Zahlungsvorgangs.“

**B.II.1.a.bb.3 Betrugsspezifische Auffassung — 0/4**

**❌ FALSE — C-024: Betrugsspezifische Auslegung von „unbefugt“** _(★★, rule_statement)_

**Kriterium:** ERFÜLLT, wenn die Antwort die betrugsspezifische Auslegung dahin beschreibt, dass die Datenverwendung täuschungsäquivalent sein muss, also einem täuschenden Verhalten gegenüber einer natürlichen Person entsprechen muss. NICHT ERFÜLLT, wenn sie betrugsspezifische Unbefugtheit mit bloßer Vertragswidrigkeit oder bloßer technischer Fehlerfreiheit gleichsetzt.

**Begründung des Judge:** Die Antwort stellt die Unbefugtheit allein auf den fehlenden beziehungsweise entgegenstehenden Willen des Karteninhabers ab. Eine betrugsspezifische Auslegung, wonach die Datenverwendung täuschungsäquivalent sein und einem täuschenden Verhalten gegenüber einer natürlichen Person entsprechen muss, wird nicht beschrieben.

**Belege:** „„Unbefugt handelt, wer Daten gegen den wirklichen oder mutmaßlichen Willen des Berechtigten verwendet.““; „„A handelte ohne und gegen den Willen des V. Die Nutzung der Daten war deshalb unbefugt.““

**❌ FALSE — C-025: OLG-Hamm-Linie zur Täuschungsäquivalenz** _(★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort die vertretbare OLG-Hamm-nahe Linie erfasst, wonach beim kontaktlosen Bezahlen ohne PIN ein fiktiver Bank- oder Schalterangestellter nur die im Programm angelegten Kriterien prüfen würde und deshalb keine Täuschungsäquivalenz hinsichtlich der Kartenberechtigung vorläge. NICHT ERFÜLLT, wenn sie diese Gegenansicht falsch darstellt oder bei Verneinung der Unbefugtheit keine fehlende Berechtigungsprüfung benennt.

**Begründung des Judge:** Die Antwort erfasst die OLG-Hamm-nahe Gegenansicht zur Täuschungsäquivalenz nicht. Sie stellt vielmehr allein auf den fehlenden Willen des Karteninhabers ab und bejaht deshalb die Unbefugtheit. Es fehlt insbesondere der erforderliche Hinweis, dass ein fiktiver Bank- oder Schalterangestellter beim kontaktlosen Bezahlen ohne PIN nur die im Programm vorgesehenen Kriterien prüfen würde und daher keine Berechtigungsprüfung hinsichtlich des tatsächlichen Karteninhabers stattfindet.

**Belege:** „„Die Nutzung der Daten war deshalb unbefugt.““; „„Mithin liegt eine unbefugte Verwendung von Daten im Sinne des § 263a Abs. 1 Var. 3 StGB vor.““; „„Die Täuschung des K ist für den Schaden der Bank weder kausal““

**❌ FALSE — C-026: Maßstab der hypothetischen Kartenvorlage** _(★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei betrugsspezifischer Konkretisierung entweder darauf abstellt, welchen Erklärungswert die Vorlage der EC-Karte des V gegenüber einem hypothetischen Bankangestellten hätte, oder vertretbar stattdessen auf die im Computerprogramm angelegten Prüfungen und die fehlende PIN- beziehungsweise Berechtigungsprüfung abstellt. NICHT ERFÜLLT, wenn sie die Täuschungsäquivalenz nicht auf die konkrete PIN-lose EC-Kartenzahlung anwendet.

**Begründung des Judge:** Die Antwort bejaht die Unbefugtheit allein anhand des entgegenstehenden Willens des Karteninhabers. Sie konkretisiert die Täuschungsäquivalenz jedoch weder anhand des Erklärungswerts der konkreten PIN-losen Kartenvorlage gegenüber einem hypothetischen Bankangestellten noch anhand der im Programm vorgesehenen Prüfungen und der fehlenden PIN- bzw. Berechtigungsprüfung. Die bloße Wiedergabe des automatisierten Prüfablaufs genügt nicht.

**Belege:** „„Fraglich ist, welche Variante des § 263a Abs. 1 StGB einschlägig ist. In Betracht kommt vor allem die unbefugte Verwendung von Daten““; „„Unbefugt handelt, wer Daten gegen den wirklichen oder mutmaßlichen Willen des Berechtigten verwendet.““; „„Im Zahlungssystem erfolgte daraufhin eine automatisierte Prüfung (Kartensperre, Verfügungsrahmen, Voraussetzungen für PIN-Verzicht) und schließlich die Autorisierung des Zahlungsvorgangs.““

**❌ FALSE — C-027: Kartenvorlage als Berechtigungsbehauptung** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei dem Maßstab der hypothetischen Kartenvorlage erkennt, dass die Vorlage der auf V ausgestellten EC-Karte gegenüber einem Bankangestellten konkludent erklärt, der Nutzer sei berechtigter Karteninhaber oder bevollmächtigt. NICHT ERFÜLLT, wenn sie bei diesem Maßstab den Besitz der auf V ausgestellten Karte als völlig erklärungsneutral behandelt.

**Begründung des Judge:** Die Antwort erkennt zwar eine Täuschung über die fehlende Berechtigung bzw. den Anschein einer Autorisierung. Sie stellt jedoch nicht ausdrücklich fest, dass die Vorlage der auf V ausgestellten Karte gegenüber einem Bankangestellten nach dem Maßstab der hypothetischen Kartenvorlage konkludent die Berechtigung oder Bevollmächtigung des Nutzers erklärt. Die Aussage zum gespeicherten Datensatz ersetzt diese konkrete Erklärung nicht.

**Belege:** „Der hier gespeicherte Zahlungsvorgang erweckt den Anschein, der berechtigte Karteninhaber V habe persönlich die Zahlung autorisiert.“; „A handelte bei der Benutzung der Karte mit dem Ziel, die R-GmbH und die Sparkasse über seine mangelnde Berechtigung hinwegzutäuschen“

**B.II.1.a.bb.4 Streitentscheid — 0/2**

**❌ FALSE — C-029: Kritik an bloß subjektivierender Auslegung** _(★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort beim Streitentscheid zu § 263a StGB berücksichtigt, dass ein bloßer Willenswiderspruch § 263a StGB über die Betrugsnähe zu § 263 StGB hinaus auf bloß vertragswidriges Verhalten ausweiten würde; ebenfalls ERFÜLLT, wenn sie die subjektivierende Ansicht ausdrücklich übernimmt und diese Ausweitung substantiiert begründet. NICHT ERFÜLLT, wenn sie den bloßen Willenswiderspruch ohne jede Auseinandersetzung als allein maßgeblich behandelt.

**Begründung des Judge:** Die Antwort behandelt den entgegenstehenden Willen des V als allein maßgebliches Kriterium, setzt sich beim Streitentscheid aber nicht damit auseinander, dass ein bloßer Willenswiderspruch den § 263a StGB über die Betrugsnähe hinaus auf bloß vertragswidriges Verhalten ausweiten würde. Eine substantiiert begründete Übernahme der subjektivierenden Ansicht liegt ebenfalls nicht vor.

**Belege:** „„Unbefugt handelt, wer Daten gegen den wirklichen oder mutmaßlichen Willen des Berechtigten verwendet.““; „„A handelte ohne und gegen den Willen des V. Die Nutzung der Daten war deshalb unbefugt.““

**❌ FALSE — C-030: Kritik an rein computerspezifischer Auslegung** _(★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei Ablehnung oder Relativierung der computerspezifischen Auslegung erkennt, dass diese die Strafbarkeit von der Programmierung von Schutzmechanismen durch den Vermögensinhaber abhängig macht; ebenfalls ERFÜLLT, wenn sie der computerspezifischen Ansicht folgt und konkret erklärt, weshalb gerade die fehlende Berechtigungsprüfung beim kontaktlosen Bezahlen ohne PIN zur Straflosigkeit nach § 263a StGB führt. NICHT ERFÜLLT, wenn sie die fehlende PIN-Eingabe pauschal mit Befugnis gleichsetzt.

**Begründung des Judge:** Die Antwort legt die Unbefugtheit allein anhand des Willens des Karteninhabers aus und setzt sich nicht mit der computerspezifischen Auslegung auseinander. Insbesondere erkennt sie nicht, dass diese Auslegung die Strafbarkeit von der Programmierung einer Berechtigungsprüfung bzw. von Schutzmechanismen durch den Vermögensinhaber abhängig machen kann. Ebenso erklärt sie nicht, weshalb gerade die fehlende PIN-Eingabe beim kontaktlosen Bezahlen nach dieser Ansicht zur Straflosigkeit führen würde. Die bloße Feststellung, dass A ohne Zustimmung handelte, genügt daher nicht.

**Belege:** „„Unbefugt handelt, wer Daten gegen den wirklichen oder mutmaßlichen Willen des Berechtigten verwendet.““; „„V hatte A zu keiner Zeit gestattet, die Karte zu benutzen. A handelte ohne und gegen den Willen des V.““; „„Mithin liegt eine unbefugte Verwendung von Daten im Sinne des § 263a Abs. 1 Var. 3 StGB vor.““

**B.II.1.a.bb.5 Zwischenergebnis — 0/1**

**❌ FALSE — C-028: Fallbezogene Entscheidung zur Unbefugtheit** _(★★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort entweder unbefugte Datenverwendung bejaht, weil der PIN-lose Einsatz der auf V ausgestellten EC-Karte täuschungsäquivalent eine Berechtigung behauptet, oder sie nach OLG Hamm beziehungsweise computerspezifischer Betrachtung verneint, weil keine programmierte PIN- oder Berechtigungsprüfung überwunden wurde. NICHT ERFÜLLT, wenn sie zur Unbefugtheit ein Ergebnis nennt, ohne es auf eine benannte Auslegung und die konkrete Funktionsweise des kontaktlosen Bezahlens ohne PIN zu stützen.

**Begründung des Judge:** Die Antwort bejaht die Unbefugtheit lediglich mit dem fehlenden Willen des Karteninhabers. Sie ordnet dies aber weder einer benannten täuschungsäquivalenten Auslegung zu noch setzt sie sich mit der computerspezifischen Auslegung beziehungsweise der PIN- und Berechtigungsprüfung auseinander. Die konkrete Funktionsweise des kontaktlosen, PIN-losen Zahlungsvorgangs wird zwar beschrieben, jedoch nicht zur fallbezogenen Begründung der Unbefugtheit herangezogen.

**Belege:** „„Unbefugt handelt, wer Daten gegen den wirklichen oder mutmaßlichen Willen des Berechtigten verwendet.““; „„V hatte A zu keiner Zeit gestattet, die Karte zu benutzen. A handelte ohne und gegen den Willen des V.““; „„Im Zahlungssystem erfolgte daraufhin eine automatisierte Prüfung (Kartensperre, Verfügungsrahmen, Voraussetzungen für PIN-Verzicht) und schließlich die Autorisierung des Zahlungsvorgangs.““

**B.II.1.a.cc Beeinflussung des Ergebnisses eines Datenverarbeitungsvorgangs — 2/2**

**✅ TRUE — C-031: Beeinflussung eines Datenverarbeitungsvorgangs** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort, soweit sie § 263a StGB nicht bereits vertretbar an der Unbefugtheit scheitern lässt, feststellt, dass A durch den Einsatz der EC-Karte das Ergebnis eines elektronischen Datenverarbeitungsvorgangs beeinflusste. NICHT ERFÜLLT, wenn sie bei bejahter unbefugter Datenverwendung keine Beeinflussung eines Datenverarbeitungsvorgangs prüft oder diese trotz Autorisierung der Zahlung verneint.

**Begründung des Judge:** Die Antwort stellt ausdrücklich fest, dass A durch das Vorhalten der EC-Karte die Übertragung und Verarbeitung der Kartendaten auslöste und dadurch die Autorisierung als Ergebnis des Datenverarbeitungsvorgangs beeinflusste.

**Belege:** „Diese Autorisierung ist das Ergebnis eines Datenverarbeitungsvorgangs.“; „A hat auf dieses Ergebnis durch die Verwendung der auf dem Chip gespeicherten Daten eingewirkt, denn ohne das Vorhalten der Karte wäre die Autorisierung nicht erfolgt.“

**✅ TRUE — C-032: Vervollständigung der Autorisierungsanfrage** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort, soweit sie § 263a StGB weiterprüft, die Beeinflussung darin sieht, dass die Autorisierungsanfrage der R-GmbH mit den Karten- oder Kontodaten des V vervollständigt und an das Zahlungssystem der Sparkasse übermittelt wurde. NICHT ERFÜLLT, wenn sie die Beeinflussung ausschließlich in einer menschlichen Erklärung gegenüber K sieht und den maschinellen Autorisierungsvorgang nicht erfasst.

**Begründung des Judge:** Die Antwort erfasst ausdrücklich, dass die Kartendaten des V an das Lesegerät übertragen und mit den Zahlungsdaten der R-GmbH an das Zahlungssystem der Sparkasse übermittelt wurden. Darin sieht sie die Einwirkung auf das Ergebnis der Datenverarbeitung und nicht lediglich eine menschliche Erklärung gegenüber K.

**Belege:** „„Dadurch wurden über den NFC-Chip die Kartennummer und das Gültigkeitsdatum der Karte an das Lesegerät übertragen.““; „„Das Lesegerät sandte diese Daten zusammen mit den Kontodaten der R-GmbH als Zahlungsempfängerin und dem Rechnungsbetrag an das Zahlungssystem der Sparkasse Göttingen.““; „„A hat auf dieses Ergebnis durch die Verwendung der auf dem Chip gespeicherten Daten eingewirkt, denn ohne das Vorhalten der Karte wäre die Autorisierung nicht erfolgt.““

**B.II.1.a.dd Vermögensschaden — 2/4**

**✅ TRUE — C-033: Einredefreie Forderung der R-GmbH** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort erkennt, dass die R-GmbH durch die Autorisierung des kontaktlosen Zahlungsvorgangs über 32,76 € grundsätzlich eine einredefreie Forderung gegen die Sparkasse erwirbt, obwohl A nicht berechtigter Kartennutzer war. NICHT ERFÜLLT, wenn sie annimmt, die R-GmbH habe wegen der unberechtigten Kartennutzung keinen Zahlungsanspruch gegen die Sparkasse, ohne die Ausnahme positiver Kenntnis des K tragfähig zu behandeln.

**Begründung des Judge:** Die Antwort erkennt zutreffend, dass die R-GmbH trotz der unberechtigten Nutzung der Karte durch A grundsätzlich eine einredefreie Forderung gegen die Sparkasse erwirbt. Sie behandelt außerdem die maßgebliche Ausnahme der positiven Kenntnis des K und verneint diese im konkreten Fall.

**Belege:** „Die R-GmbH erwirbt durch die Autorisierung eine einredefreie Forderung gegen die Sparkasse“; „da K keine positive Kenntnis von der fehlenden Berechtigung hatte“

**✅ TRUE — C-034: Vermögensschaden der Sparkasse** _(★★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort, soweit sie den § 263a-Tatbestand bis zur Schadensprüfung fortführt, einen Vermögensschaden der Sparkasse darin erkennt, dass diese der R-GmbH aus der Autorisierung über 32,76 € verpflichtet wurde, ohne gegen V Ersatz verlangen zu können. NICHT ERFÜLLT, wenn sie bei bejahter unbefugter Datenverwendung keinen Vermögensschaden feststellt oder den Schaden nur bei der R-GmbH verortet.

**Begründung des Judge:** Die Antwort verortet den Vermögensschaden ausdrücklich bei der Sparkasse: Diese ist der R-GmbH aufgrund der Autorisierung zur Zahlung verpflichtet und trägt nach der Erstattung an V den Schaden, ohne eine Ersatzmöglichkeit gegen A zu haben. Damit ist das Kriterium erfüllt.

**Belege:** „„bei der Sparkasse ein effektiver Vermögensschaden in Höhe von 32,76 € eingetreten““; „„die Bank den Schaden in Höhe von 32,76 € trug““; „„Eine Ersatzmöglichkeit gegen A besteht nach den zivilrechtlichen Vorschriften nicht.““; „„die R-GmbH durch die Autorisierung eine einredefreie Forderung gegen die Sparkasse““

**❌ FALSE — C-035: Kein Ersatzanspruch der Sparkasse gegen V** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei der Schadensverteilung berücksichtigt, dass die Sparkasse wegen des ohne PIN und damit ohne starke Kundenauthentifizierung ausgelösten Zahlungsvorgangs keinen Ersatzanspruch gegen V aus § 675v Abs. 1 BGB hat, insbesondere wegen § 675v Abs. 4 Nr. 1 BGB. NICHT ERFÜLLT, wenn sie den endgültigen Schaden der Sparkasse verneint, weil V die Zahlung angeblich tragen müsse, ohne §§ 675u, 675v BGB oder die fehlende PIN zu behandeln.

**Begründung des Judge:** Die Antwort berücksichtigt zwar, dass die Sparkasse den endgültigen Schaden trägt und verweist auf §§ 675u, 675v BGB. Sie stellt jedoch nicht ausdrücklich fest, dass wegen der fehlenden PIN bzw. fehlenden starken Kundenauthentifizierung kein Ersatzanspruch der Sparkasse gegen V nach § 675v Abs. 1 BGB besteht, insbesondere aufgrund von § 675v Abs. 4 Nr. 1 BGB. Die erforderliche rechtliche Begründung der Schadensverteilung fehlt daher.

**Belege:** „„Nachdem V einige Tage später die unberechtigte Buchung reklamierte, schrieb die Sparkasse ihm den Betrag aber gemäß den gesetzlichen Regelungen (§§ 675u, 675v BGB) wieder gut, sodass letztlich die Bank den Schaden in Höhe von 32,76 € trug.““

**❌ FALSE — C-036: Gefährdungsschaden des V** _(★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort die zunächst vermerkte Kontobelastung des V über 32,76 € zumindest als möglichen Gefährdungsschaden oder gegenwärtige Vermögensverschlechterung einordnet und die spätere Gutschrift berücksichtigt. NICHT ERFÜLLT, wenn sie V endgültig als geschädigt darstellt, ohne spätere Gutschrift und gesetzliche Risikotragung zu behandeln, oder die Kontobelastung von vornherein als irrelevant bezeichnet.

**Begründung des Judge:** Die Antwort berücksichtigt zwar die zunächst vermerkte Belastung des Kontos des V und die spätere Gutschrift unter Hinweis auf die gesetzliche Risikotragung. Sie ordnet die Belastung des V jedoch nicht ausdrücklich als möglichen Gefährdungsschaden oder gegenwärtige Vermögensverschlechterung ein, sondern verlagert den maßgeblichen Vermögensschaden ausschließlich auf die Sparkasse. Das genügt dem Kriterium nicht.

**Belege:** „„zugleich wurde auf dem Konto des V zunächst eine Belastung vermerkt““; „„Nachdem V einige Tage später die unberechtigte Buchung reklamierte, schrieb die Sparkasse ihm den Betrag aber gemäß den gesetzlichen Regelungen (§§ 675u, 675v BGB) wieder gut““; „„Damit ist bei der Sparkasse ein effektiver Vermögensschaden in Höhe von 32,76 € eingetreten.““

**B.II.1.b Subjektiver Tatbestand — 4/7**

**B.II.1.b.aa Vorsatz — 1/1**

**✅ TRUE — C-037: Vorsatz beim Computerbetrug** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei § 263a StGB den Vorsatz des A nicht wegen fehlender Detailkenntnis über NFC-Technik oder §§ 675u, 675v BGB ausschließt, sondern eine Parallelwertung in der Laiensphäre genügen lässt. NICHT ERFÜLLT, wenn sie A allein mangels genauer Kenntnis des Autorisierungssystems oder der zivilrechtlichen Risikotragung für vorsatzlos hält.

**Begründung des Judge:** Die Antwort lässt den Vorsatz nicht an fehlender Detailkenntnis über die NFC-Technik oder die §§ 675u, 675v BGB scheitern, sondern bejaht ausdrücklich eine Parallelwertung in der Laiensphäre.

**Belege:** „Dass er die genauen technischen Abläufe und die zivilrechtliche Risikoverteilung nicht im Einzelnen kannte, ist unerheblich“; „es genügt, dass er die wesentliche Bedeutung seines Tuns – die unberechtigte Nutzung eines fremden Zahlungsinstruments – erfasste“

**B.II.1.b.bb Absicht rechtswidriger und stoffgleicher Bereicherung — 3/6**

**✅ TRUE — C-038: Vermögensvorteil durch Warenerhalt** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort als von A erstrebten Vermögensvorteil im Rahmen des § 263a StGB den Erhalt von Besitz oder Eigentum an den Lebensmitteln und Getränken im Wert von 32,76 € benennt. NICHT ERFÜLLT, wenn sie keinen konkreten Vermögensvorteil des A bestimmt oder den Vorteil allein in der Nutzung der EC-Karte sieht.

**Begründung des Judge:** Die Antwort benennt konkret den Erhalt der Lebensmittel und Getränke im Wert von 32,76 € als von A erstrebten Vermögensvorteil und sieht den Vorteil nicht lediglich in der Nutzung der EC-Karte.

**Belege:** „Er hat die Lebensmittel und Getränke im Wert von 32,76 € erlangt“; „A handelte mit dem Ziel, ohne eigenes Entgelt Waren im Wert von 32,76 € zu erhalten.“

**❌ FALSE — C-039: Rechtswidrigkeit der Warenbereicherung** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort die von A erstrebte Bereicherung durch die Waren als rechtswidrig einordnet, weil A keinen fälligen und einredefreien Anspruch auf Übereignung oder Übergabe der Waren hatte und nicht mit eigenen berechtigten Mitteln zahlte. NICHT ERFÜLLT, wenn sie aus der tatsächlichen Herausgabe durch K oder dem Forderungserwerb der R-GmbH gegen die Sparkasse einen Anspruch des A auf die Waren ableitet.

**Begründung des Judge:** Die Antwort bejaht zwar zunächst die Rechtswidrigkeit des Vermögensvorteils, begründet sie aber nicht mit dem fehlenden fälligen und einredefreien Anspruch des A auf Übereignung oder Übergabe der Waren und dem Fehlen eigener berechtigter Zahlungsmittel. Zudem leitet sie später ausdrücklich aus dem wirksamen Kaufvertrag und der tatsächlichen Übergabe einen Anspruch bzw. Eigentumserwerb des A ab. Damit ist die erforderliche Einordnung widersprüchlich und materiell nicht erfüllt.

**Belege:** „Dieser Vorteil war rechtswidrig, weil A keinen Anspruch auf die Leistung der Sparkasse oder auf eine unentgeltliche Warenlieferung besaß.“; „A hat die Waren aufgrund eines zivilrechtlich wirksamen Kaufvertrags mit der R-GmbH erworben; durch die Einigung über den Eigentumsübergang und die Übergabe wurde A Eigentümer.“; „A hat die Waren daher nicht „weggenommen“, sondern als Erfüllung des Kaufvertrags erhalten.“

**✅ TRUE — C-040: Vorsatz zur Rechtswidrigkeit der Bereicherung** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort feststellt, dass A hinsichtlich der Rechtswidrigkeit der erstrebten Bereicherung vorsätzlich handelte, weil ihm bewusst war, dass er eine fremde EC-Karte nicht nutzen durfte. NICHT ERFÜLLT, wenn sie A einen Anspruch auf die Waren oder einen unvermeidbaren Irrtum über die Berechtigung zuschreibt, obwohl der Sachverhalt sein Bewusstsein der Unzulässigkeit fremder Kartennutzung mitteilt.

**Begründung des Judge:** Die Antwort stellt ausdrücklich fest, dass A bewusst und ohne Erlaubnis eine fremde EC-Karte nutzte, und dass der erstrebte Vermögensvorteil deshalb rechtswidrig war. Damit ist sein Vorsatz hinsichtlich der Rechtswidrigkeit der Bereicherung bejaht.

**Belege:** „„Ihm war bewusst, dass er die EC-Karte des V ohne dessen Erlaubnis benutzte““; „„Dieser Vorteil war rechtswidrig, weil A keinen Anspruch auf die Leistung der Sparkasse oder auf eine unentgeltliche Warenlieferung besaß.““

**❌ FALSE — C-041: Problem der Stoffgleichheit** _(★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort erkennt, dass die Stoffgleichheit beim Computerbetrug problematisch ist, weil der Schaden jedenfalls bei der Sparkasse eintritt, während A die Waren aus dem Vermögen der R-GmbH erhält. NICHT ERFÜLLT, wenn sie Stoffgleichheit schematisch bejaht, ohne das Auseinanderfallen von geschädigter Bank und leistender R-GmbH zu bemerken.

**Begründung des Judge:** Die Antwort benennt zwar, dass A die Waren von der R-GmbH erhält und der Schaden letztlich bei der Sparkasse eintritt. Sie erkennt die daraus folgende Problematik der Stoffgleichheit jedoch nicht an, sondern bejaht sie schematisch mit der unzutreffenden Begründung, Vorteil und Bankschaden entsprächen „exakt“ einander. Damit fehlt eine sachgerechte Auseinandersetzung mit dem Auseinanderfallen von geschädigter Bank und leistender R-GmbH.

**Belege:** „„Schließlich ist erforderlich, dass der vom Täter erstrebte Vermögensvorteil und der eingetretene Schaden stoffgleich sind““; „„A hat die Lebensmittel und Getränke im Wert von 32,76 € erlangt““; „„Dieser Vermögensvorteil entspricht exakt dem Schaden, den die Sparkasse erlitten hat““

**❌ FALSE — C-042: Fallbezogene Entscheidung der Stoffgleichheit** _(★★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort entweder Stoffgleichheit bejaht, weil Warenerhalt des A und Schaden der Sparkasse als Kehrseiten desselben einheitlichen Kassen- und Zahlungsvorgangs erscheinen, oder Stoffgleichheit verneint, weil der Schaden bei der Sparkasse eintritt, während die Waren aus dem Vermögen der R-GmbH stammen, und daraus folgerichtig Probleme der rechtswidrigen Bereicherungsabsicht ableitet. NICHT ERFÜLLT, wenn sie die Stoffgleichheit trotz Auseinanderfallens von Sparkasse und R-GmbH nur formelhaft behauptet.

**Begründung des Judge:** Die Antwort bejaht die Stoffgleichheit lediglich mit der formelhaften Behauptung, der Warenvorteil des A entspreche exakt dem Schaden der Sparkasse. Sie setzt sich nicht damit auseinander, dass A die Waren aus dem Vermögen der R-GmbH erlangt, während der Schaden bei der Sparkasse eintritt, und begründet nicht, weshalb beide als Kehrseiten desselben einheitlichen Kassen- und Zahlungsvorgangs anzusehen sein sollen. Damit erfüllt sie die fallbezogene Begründungsanforderung nicht.

**Belege:** „Dieser Vermögensvorteil entspricht exakt dem Schaden, den die Sparkasse erlitten hat, denn die Bank musste den Kaufpreis an die R-GmbH auskehren und kann diesen Betrag nicht zurückerlangen.“; „A wollte sich durch die Tat einen „kleinen Finderlohn“ verschaffen. Er hat die Lebensmittel und Getränke im Wert von 32,76 € erlangt“

**✅ TRUE — C-043: Keine rechtswidrige Drittbereicherung der R-GmbH** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort eine Bereicherungsabsicht des A nicht tragend darauf stützt, dass die R-GmbH rechtswidrig bereichert werde, weil deren Forderung gegen die Sparkasse nach dem Sachverhalt einredefrei und zivilrechtlich rechtmäßig besteht. NICHT ERFÜLLT, wenn sie die Forderung der R-GmbH gegen die Sparkasse als rechtswidrige Drittbereicherung behandelt, ohne den gesicherten Anspruch zu berücksichtigen.

**Begründung des Judge:** Die Antwort stützt die Bereicherungsabsicht auf den rechtswidrigen Vorteil des A, nämlich den Erhalt der Waren ohne eigene Gegenleistung. Die Forderung der R-GmbH gegen die Sparkasse wird ausdrücklich als einredefrei und rechtmäßig behandelt und nicht als rechtswidrige Drittbereicherung eingeordnet.

**Belege:** „A handelte mit dem Ziel, ohne eigenes Entgelt Waren im Wert von 32,76 € zu erhalten.“; „Dieser Vorteil war rechtswidrig, weil A keinen Anspruch auf die Leistung der Sparkasse oder auf eine unentgeltliche Warenlieferung besaß.“; „Die R-GmbH erwirbt durch die Autorisierung eine einredefreie Forderung gegen die Sparkasse, sodass sie keinen Schaden erleidet.“

**B.II.2 Rechtswidrigkeit und Schuld — 1/1**

**✅ TRUE — C-044: Rechtswidrigkeit und Schuld bei § 263a StGB** _(★★, conclusion)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei bejahtem Tatbestand des § 263a Abs. 1 Var. 3 StGB Rechtswidrigkeit und Schuld des A bejaht oder feststellt, dass Rechtfertigungs- oder Entschuldigungsgründe nicht ersichtlich sind. NICHT ERFÜLLT, wenn sie A bei bejahtem Tatbestand ohne Sachverhaltsgrund rechtfertigt oder entschuldigt.

**Begründung des Judge:** Bei bejahtem Tatbestand des § 263a Abs. 1 Var. 3 StGB bejaht die Antwort sowohl die Rechtswidrigkeit als auch die Schuld des A und verneint ausdrücklich das Vorliegen von Rechtfertigungs- oder Entschuldigungsgründen.

**Belege:** „Rechtfertigungsgründe sind nicht ersichtlich. A handelte rechtswidrig.“; „A handelte schuldhaft. Anhaltspunkte für Schuldausschließungs- oder Entschuldigungsgründe sind nicht gegeben.“

**B.II.3 Ergebnis — 1/1**

**✅ TRUE — C-045: Vertretbares Ergebnis zum Computerbetrug** _(★★★, conclusion)_

**Kriterium:** ERFÜLLT, wenn die Antwort A wegen Computerbetrugs nach § 263a Abs. 1 Var. 3 StGB strafbar nennt oder § 263a StGB ausdrücklich wegen einer benannten vertretbaren Streitfrage verneint, nämlich fehlender unbefugter Datenverwendung nach OLG Hamm beziehungsweise computerspezifischer Sicht oder fehlender Stoffgleichheit. NICHT ERFÜLLT, wenn sie § 263a StGB gar nicht prüft, mit Betrug des Computers verwechselt oder ohne Auseinandersetzung mit PIN-loser fremder Kartennutzung, Sparkassenschaden oder Stoffgleichheit entscheidet.

**Begründung des Judge:** Die Antwort prüft § 263a Abs. 1 Var. 3 StGB ausdrücklich und bejaht die unbefugte Verwendung der fremden EC-Kartendaten trotz kontaktloser PIN-loser Zahlung. Sie behandelt außerdem den letztlichen Schaden der Sparkasse und die Stoffgleichheit zwischen dem erlangten Warenwert und dem Bankschaden. Damit liegt ein vom Kriterium gefordertes vertretbares Ergebnis vor.

**Belege:** „A hat sich wegen Computerbetrugs gemäß § 263a Abs. 1 Var. 3 StGB strafbar gemacht.“; „A hat die im Park gefundene EC-Karte des V an das vom Kassenpersonal K aktivierte Kartenlesegerät gehalten.“; „Nachdem V einige Tage später die unberechtigte Buchung reklamierte, schrieb die Sparkasse ihm den Betrag ... wieder gut, sodass letztlich die Bank den Schaden in Höhe von 32,76 € trug.“; „Schließlich ist erforderlich, dass der vom Täter erstrebte Vermögensvorteil und der eingetretene Schaden stoffgleich sind.“

#### B.IV Urkundenunterdrückung gem. § 274 Abs. 1 Nr. 2 StGB — 2/16

**B.IV.1 Tatbestandsmäßigkeit — 2/15**

**B.IV.1.a Objektiver Tatbestand — 2/7**

**❌ FALSE — C-047: Datenveränderung im Sparkassensystem bei § 274 StGB** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei § 274 Abs. 1 Nr. 2 StGB erkennt, dass der von A ausgelöste Zahlungsvorgang Daten im Zahlungssystem der Sparkasse veränderte oder aktualisierte. NICHT ERFÜLLT, wenn sie § 274 Abs. 1 Nr. 2 StGB mit der Begründung ablehnt, es seien überhaupt keine gespeicherten Daten verändert worden.

**Begründung des Judge:** Die Antwort erwähnt zwar, dass gespeicherte Datensätze im Sparkassensystem aktualisiert wurden, prüft § 274 Abs. 1 Nr. 2 StGB jedoch überhaupt nicht und ordnet diese Datenveränderung nicht diesem Tatbestand zu. Damit fehlt die geforderte Erkenntnis bei § 274 StGB.

**Belege:** „Die im Zahlungssystem der Sparkasse gespeicherten Datensätze über den Zahlungsvorgang (Transaktionsdaten, Aktualisierung des Verfügungsrahmens und der PIN-Zähler) sind beweiserhebliche Daten.“

**✅ TRUE — C-048: Verfügungsrahmen als veränderter Datensatz** _(★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort als durch den Zahlungsvorgang veränderten Datensatz den verfügbaren Betrag bis zum Erreichen des Verfügungsrahmens des Kontos des V oder gleichwertig die Anpassung des verfügbaren Limits beschreibt. NICHT ERFÜLLT, wenn sie bei § 274 Abs. 1 Nr. 2 StGB nur allgemein von Daten spricht und die Anpassung des Verfügungsrahmens nicht verarbeitet.

**Begründung des Judge:** Die Antwort beschreibt ausdrücklich die Aktualisierung des Verfügungsrahmens als durch den Zahlungsvorgang veränderten Datensatz. Dies ist gleichwertig mit der Anpassung des verfügbaren Limits.

**Belege:** „Die im Zahlungssystem der Sparkasse gespeicherten Datensätze über den Zahlungsvorgang (Transaktionsdaten, Aktualisierung des Verfügungsrahmens und der PIN-Zähler) sind beweiserhebliche Daten.“

**❌ FALSE — C-049: PIN-Verzichtsdaten als veränderte Datensätze** _(★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort als veränderte Daten die für künftige kontaktlose Zahlungen ohne PIN maßgeblichen Datensätze erfasst, insbesondere Anzahl oder Gesamtvolumen bisheriger PIN-loser Zahlungsvorgänge. NICHT ERFÜLLT, wenn sie die im Sachverhalt genannten PIN-Verzichtsvoraussetzungen bei § 274 Abs. 1 Nr. 2 StGB völlig ignoriert.

**Begründung des Judge:** Die Antwort erwähnt zwar einen „PIN-Zähler“, ordnet ihn aber lediglich als beweiserhebliche Daten im Rahmen des § 269 StGB ein. Sie behandelt weder § 274 Abs. 1 Nr. 2 StGB noch stellt sie klar, dass die für künftige PIN-lose kontaktlose Zahlungen maßgeblichen Datensätze – insbesondere die Anzahl oder das Gesamtvolumen bisheriger PIN-loser Zahlungsvorgänge – verändert wurden. Damit werden die PIN-Verzichtsdaten bei § 274 Abs. 1 Nr. 2 StGB im Ergebnis ignoriert.

**Belege:** „Die im Zahlungssystem der Sparkasse gespeicherten Datensätze über den Zahlungsvorgang (Transaktionsdaten, Aktualisierung des Verfügungsrahmens und der PIN-Zähler) sind beweiserhebliche Daten.“; „A hat sich damit wegen Computerbetrugs in Tateinheit mit Fälschung beweiserheblicher Daten strafbar gemacht.“

**❌ FALSE — C-050: Beweiserheblichkeit der veränderten Daten** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort die im Sparkassensystem veränderten Daten für § 274 Abs. 1 Nr. 2 StGB als beweiserheblich einordnet, weil sie für die Autorisierung weiterer Kartenzahlungen oder künftiger PIN-Verzichtsprüfungen relevant sind. NICHT ERFÜLLT, wenn sie die Beweiserheblichkeit ohne Bezug zu künftigen Autorisierungen verneint oder nur wegen beliebiger Speicherung bejaht.

**Begründung des Judge:** Die Antwort bejaht die Beweiserheblichkeit zwar, ordnet sie aber § 269 StGB zu und begründet sie lediglich mit dem Nachweis des Zahlungsvorgangs. Ein Bezug der veränderten Daten zu künftigen Autorisierungen oder zu späteren Prüfungen des PIN-Verzichts im Rahmen von § 274 Abs. 1 Nr. 2 StGB wird nicht hergestellt.

**Belege:** „„Die im Zahlungssystem der Sparkasse gespeicherten Datensätze über den Zahlungsvorgang (Transaktionsdaten, Aktualisierung des Verfügungsrahmens und der PIN-Zähler) sind beweiserhebliche Daten.““; „„Sie dienen im Rechtsverkehr dem Nachweis von Zahlungsvorgängen““

**❌ FALSE — C-051: Keine Verfügungsbefugnis des A über Sparkassendaten** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort feststellt, dass A als Finder und nichtberechtigter Nutzer der auf V ausgestellten EC-Karte kein Verfügungsrecht über die im Zahlungssystem der Sparkasse gespeicherten und veränderten Daten hatte. NICHT ERFÜLLT, wenn sie A wegen Kartenbesitzes oder erfolgreicher Zahlung als datenverfügungsbefugt behandelt.

**Begründung des Judge:** Die Antwort stellt zwar die fehlende Berechtigung des A zur Nutzung der EC-Karte und der Kartendaten fest. Sie sagt jedoch nicht ausdrücklich, dass A als Finder keine Verfügungsbefugnis über die im Zahlungssystem der Sparkasse gespeicherten und veränderten Daten hatte. Die Begründung bleibt auf der Ebene des entgegenstehenden Willens des V und der unbefugten Kartennutzung.

**Belege:** „A handelte ohne und gegen den Willen des V. Die Nutzung der Daten war deshalb unbefugt.“; „A handelte bei der Benutzung der Karte mit dem Ziel, ... die Sparkasse über seine mangelnde Berechtigung hinwegzutäuschen“

**❌ FALSE — C-052: Beweisführungsrecht der Sparkasse** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort der Sparkasse Göttingen ein Beweisführungsrecht oder eine beweisbezogene Verfügungsbefugnis an den veränderten Zahlungsdaten zuschreibt. NICHT ERFÜLLT, wenn sie die Sparkasse als bloße technische Durchleitungsstelle ohne geschütztes Dateninteresse behandelt.

**Begründung des Judge:** Die Antwort ordnet die Zahlungsdaten zwar der Sparkasse zu und beschreibt ihre Beweisfunktion. Sie schreibt der Sparkasse jedoch kein eigenes Beweisführungsrecht oder eine beweisbezogene Verfügungsbefugnis an den veränderten Daten ausdrücklich oder hinreichend eindeutig zu. Die Sparkasse wird damit nicht als bloße technische Durchleitungsstelle behandelt, aber das geforderte konkrete Beweisführungsrecht bleibt offen.

**Belege:** „Die im Zahlungssystem der Sparkasse gespeicherten Datensätze über den Zahlungsvorgang ... sind beweiserhebliche Daten.“; „Sie dienen im Rechtsverkehr dem Nachweis von Zahlungsvorgängen, insbesondere gegenüber dem Karteninhaber oder in etwaigen Streitigkeiten.“

**✅ TRUE — C-053: Beweisführungsrecht des V** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort V als berechtigtem Karteninhaber ein Beweisführungsrecht oder beweisbezogenes Interesse an den veränderten Zahlungsdaten zuschreibt. NICHT ERFÜLLT, wenn sie V wegen späterer Gutschrift oder fehlender technischer Kontrolle jedes geschützte Beweisinteresse abspricht.

**Begründung des Judge:** Die Antwort erkennt V ausdrücklich als berechtigten Karteninhaber an und beschreibt die veränderten Zahlungsdaten als beweiserheblich, insbesondere für den Nachweis des Zahlungsvorgangs gegenüber dem Karteninhaber und in Streitigkeiten. Damit wird V ein beweisbezogenes Interesse an diesen Daten zugeschrieben.

**Belege:** „Die im Zahlungssystem der Sparkasse gespeicherten Datensätze über den Zahlungsvorgang ... sind beweiserhebliche Daten.“; „Sie dienen im Rechtsverkehr dem Nachweis von Zahlungsvorgängen, insbesondere gegenüber dem Karteninhaber oder in etwaigen Streitigkeiten.“; „Der hier gespeicherte Zahlungsvorgang erweckt den Anschein, der berechtigte Karteninhaber V habe persönlich die Zahlung autorisiert.“

**B.IV.1.b Subjektiver Tatbestand — 0/8**

**B.IV.1.b.aa Vorsatz — 0/1**

**❌ FALSE — C-054: Vorsatz bei § 274 Abs. 1 Nr. 2 StGB** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei § 274 Abs. 1 Nr. 2 StGB Vorsatz des A hinsichtlich der Veränderung fremder beweiserheblicher Daten jedenfalls in Parallelwertung der Laiensphäre bejaht, weil A wusste, dass beim elektronischen Zahlungsvorgang Daten übertragen oder gespeichert werden. NICHT ERFÜLLT, wenn sie den Vorsatz allein wegen fehlender technischer Detailkenntnisse verneint.

**Begründung des Judge:** Die Antwort prüft § 274 Abs. 1 Nr. 2 StGB überhaupt nicht und bejaht daher insbesondere keinen Vorsatz hinsichtlich der Veränderung fremder beweiserheblicher Daten. Die Ausführungen zum Vorsatz beziehen sich ausschließlich auf § 269 StGB und genügen dem ausdrücklich geforderten Prüfungspunkt nicht.

**Belege:** „## B. Strafbarkeit des A wegen Fälschung beweiserheblicher Daten gemäß § 269 Abs. 1 StGB“; „A handelte vorsätzlich.“; „er wusste, dass Daten übertragen und gespeichert werden“

**B.IV.1.b.bb Nachteilzufügungsabsicht — 0/7**

**❌ FALSE — C-055: Nachteilszufügungsabsicht als Merkmal des § 274 StGB** _(★★, rule_statement)_

**Kriterium:** ERFÜLLT, wenn die Antwort erkennt, dass § 274 Abs. 1 Nr. 2 StGB zusätzlich zum Vorsatz eine Absicht voraussetzt, einem anderen einen Nachteil zuzufügen. NICHT ERFÜLLT, wenn sie § 274 Abs. 1 Nr. 2 StGB allein aus vorsätzlicher Datenveränderung bejaht.

**Begründung des Judge:** Die Antwort behandelt § 274 Abs. 1 Nr. 2 StGB überhaupt nicht und erkennt daher weder das zusätzliche Erfordernis einer Nachteilszufügungsabsicht noch prüft sie dieses. Das Kriterium ist nicht erfüllt.

**Belege:** „Sonstige Straftatbestände sind nicht verwirklicht.“

**❌ FALSE — C-056: Gegenansicht zur Nachteilszufügungsabsicht** _(★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort die OLG-Hamm- beziehungsweise h.M.-nahe Ansicht erfasst, nach der für die Nachteilszufügungsabsicht sicheres Wissen um einen Nachteilseintritt genügen kann und die Kenntnis der Relevanz geänderter Daten für weitere Zahlungsvorgänge zur Bejahung herangezogen wird. NICHT ERFÜLLT, wenn sie eine Bejahung von § 274 Abs. 1 Nr. 2 StGB auf Nachteilsabsicht stützt, ohne einen sicher gekannten oder gewollten beweisbezogenen Nachteil zu erklären.

**Begründung des Judge:** Die Antwort behandelt § 274 Abs. 1 Nr. 2 StGB und die Nachteilszufügungsabsicht überhaupt nicht. Insbesondere fehlt die OLG-Hamm- beziehungsweise h.M.-nahe Erwägung, dass sich die sichere Kenntnis eines Nachteils genügen lassen kann und dass die Kenntnis der Relevanz der geänderten Daten für weitere Zahlungsvorgänge einen beweisbezogenen Nachteil begründet.

**Belege:** „## C. Weitere Straftatbestände“; „Sonstige Straftatbestände sind nicht verwirklicht.“

**❌ FALSE — C-057: Verschleifungsverbot bei § 274 StGB** _(★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort die Gleichsetzung der Nachteilszufügungsabsicht mit bloßer Kenntnis der Datenänderung kritisch behandelt, insbesondere mit dem Argument, dass sonst Vorsatz und Absichtsmerkmal verschliffen würden; ebenfalls ERFÜLLT, wenn sie diese Kritik ausdrücklich verwirft und die Eigenständigkeit des Nachteilsmerkmals anderweitig begründet. NICHT ERFÜLLT, wenn sie die Nachteilszufügungsabsicht ohne eigenständigen Nachteilsbezug aus dem Vorsatz ableitet.

**Begründung des Judge:** Die Antwort behandelt § 274 StGB und das Verschleifungsverbot nicht. Insbesondere fehlt eine kritische Auseinandersetzung damit, dass die Nachteilszufügungsabsicht nicht lediglich aus der Kenntnis der Datenänderung bzw. dem Vorsatz abgeleitet werden darf.

**❌ FALSE — C-058: Beweisnachteil statt bloßem Vermögensabfluss** _(★★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort die Nachteilszufügungsabsicht verneint, weil die Aktualisierung der Sparkassendaten die Beweissituation von Sparkasse und V nicht verschlechtert, oder sie abweichend einen konkreten Beweisnachteil gerade durch die Datenveränderung darlegt. NICHT ERFÜLLT, wenn sie einen Nachteil nur mit dem Vermögensabfluss von 32,76 € begründet, ohne einen Nachteil für Beweisführungsrechte an den Daten zu bestimmen.

**Begründung des Judge:** Die Antwort begründet den Nachteil im Wesentlichen mit dem Vermögensschaden von 32,76 € und behandelt die Daten lediglich als beweiserheblich bzw. als Grundlage einer Täuschung. Sie verneint keine Nachteilszufügungsabsicht wegen unveränderter Beweissituation und legt auch keinen konkreten Beweisnachteil für Sparkasse oder V durch die Datenveränderung dar.

**Belege:** „Die durch die Autorisierung entstandene zivilrechtliche Lage führte bei der Sparkasse Göttingen zu einer endgültigen Vermögensminderung.“; „Die im Zahlungssystem der Sparkasse gespeicherten Datensätze über den Zahlungsvorgang ... sind beweiserhebliche Daten.“; „Die Speicherung und spätere Verwendung der Daten erfolgte, um im Rechtsverkehr über die wirkliche Beteiligung am Zahlungsvorgang zu täuschen.“

**❌ FALSE — C-059: Datenänderung als Reflex des Vermögensvorgangs** _(★★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei Ablehnung der Nachteilszufügungsabsicht herausarbeitet, dass die Datenveränderung nur Reflex des von A gewollten Vermögensvorgangs war und nicht Mittel einer beabsichtigten Beweisvereitelung; ebenfalls ERFÜLLT, wenn sie § 274 Abs. 1 Nr. 2 StGB nach der Gegenansicht bejaht. NICHT ERFÜLLT, wenn sie § 274 verneint, ohne zwischen Vermögensschaden und Beweisnachteil zu unterscheiden.

**Begründung des Judge:** Die Antwort behandelt § 274 Abs. 1 Nr. 2 StGB überhaupt nicht. Insbesondere fehlt die erforderliche Unterscheidung zwischen dem Vermögensschaden und einem möglichen Beweisnachteil sowie die Einordnung der Datenänderung als bloßer Reflex des gewollten Vermögensvorgangs beziehungsweise eine Bejahung nach der Gegenansicht.

**Belege:** „Sonstige Straftatbestände sind nicht verwirklicht.“

**❌ FALSE — C-060: Beweisinteresse der Sparkasse an aktualisierten Daten** _(★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei Ablehnung eines § 274-Nachteils berücksichtigt, dass die Sparkasse ein Interesse an der Aktualisierung der Datensätze hat, etwa für künftige PIN-Verzichtsprüfungen oder die Dokumentation des Kartenmissbrauchs; ebenfalls ERFÜLLT, wenn sie § 274 Abs. 1 Nr. 2 StGB nach der Gegenansicht bejaht. NICHT ERFÜLLT, wenn sie bei Ablehnung des Nachteils ein Interesse der Sparkasse am unveränderten alten Datenstand behauptet.

**Begründung des Judge:** Die Antwort behandelt § 274 StGB und insbesondere einen möglichen Nachteil der Sparkasse durch die Aktualisierung der Datensätze nicht. Sie berücksichtigt daher weder das Interesse der Sparkasse an den aktualisierten Daten, etwa für künftige PIN-Verzichtsprüfungen oder die Dokumentation des Kartenmissbrauchs, noch bejaht sie § 274 Abs. 1 Nr. 2 StGB nach einer Gegenansicht.

**Belege:** „Sonstige Straftatbestände sind nicht verwirklicht.“; „Die im Zahlungssystem der Sparkasse gespeicherten Datensätze über den Zahlungsvorgang ... sind beweiserhebliche Daten.“

**❌ FALSE — C-061: Beweisinteresse des V an aktualisierten Daten** _(★, argumentation)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei Ablehnung eines § 274-Nachteils berücksichtigt, dass aktualisierte Daten V helfen können, die unbefugte Zahlung zu erkennen und gegenüber der Sparkasse geltend zu machen; ebenfalls ERFÜLLT, wenn sie § 274 Abs. 1 Nr. 2 StGB nach der Gegenansicht bejaht. NICHT ERFÜLLT, wenn sie bei Ablehnung des Nachteils jedes Interesse des V an der Dokumentation der missbräuchlichen Zahlung verkennt.

**Begründung des Judge:** Die Antwort prüft § 274 Abs. 1 Nr. 2 StGB nicht und setzt sich insbesondere nicht mit dem Beweisinteresse des V an den aktualisierten Daten auseinander. Zwar erwähnt sie, dass V die unberechtigte Buchung später reklamierte, erkennt aber nicht an, dass die dokumentierten bzw. aktualisierten Daten ihm dabei helfen können, die missbräuchliche Zahlung zu erkennen und gegenüber der Sparkasse geltend zu machen. Damit wird bei der impliziten Ablehnung eines weiteren Straftatbestands das erforderliche Interesse des V nicht berücksichtigt.

**Belege:** „Nachdem V einige Tage später die unberechtigte Buchung reklamierte, schrieb die Sparkasse ihm den Betrag aber gemäß den gesetzlichen Regelungen (§§ 675u, 675v BGB) wieder gut“; „Sonstige Straftatbestände sind nicht verwirklicht.“

**B.IV.2 Ergebnis — 0/1**

**❌ FALSE — C-062: Vertretbares Ergebnis zu § 274 Abs. 1 Nr. 2 StGB** _(★★★, conclusion)_

**Kriterium:** ERFÜLLT, wenn die Antwort § 274 Abs. 1 Nr. 2 StGB mangels Nachteilszufügungsabsicht ablehnt, weil kein beweisbezogener Nachteil für V oder Sparkasse vorliegt, oder § 274 Abs. 1 Nr. 2 StGB unter Übernahme der OLG-Hamm- beziehungsweise h.M.-nahen Ansicht bejaht und den Nachteil aus der Relevanz geänderter Daten für künftige Zahlungsvorgänge ableitet. NICHT ERFÜLLT, wenn sie § 274 StGB gar nicht auf die aktualisierten Sparkassendaten bezieht oder ohne Prüfung der Nachteilszufügungsabsicht entscheidet.

**Begründung des Judge:** Die Antwort prüft § 274 Abs. 1 Nr. 2 StGB nicht in Bezug auf die aktualisierten Sparkassendaten und setzt sich insbesondere nicht mit der erforderlichen Nachteilszufügungsabsicht auseinander. Die bloße abschließende Aussage zu sonstigen Straftatbeständen genügt nicht.

**Belege:** „Sonstige Straftatbestände sind nicht verwirklicht.“

#### B.V Missbrauch von Scheck- und Kreditkarten gem. § 266b Abs. 1 StGB — 1/1

**✅ TRUE — C-063: A kein tauglicher Täter des § 266b StGB** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort § 266b Abs. 1 StGB ablehnt, weil A nicht der berechtigte Inhaber der auf V ausgestellten EC-Karte ist und § 266b StGB nur den berechtigten Karteninhaber als tauglichen Täter erfasst. NICHT ERFÜLLT, wenn sie A als unberechtigten Finder wegen Missbrauchs von Scheck- oder Kreditkarten nach § 266b StGB bestraft.

**Begründung des Judge:** Die Antwort lehnt eine Strafbarkeit nach § 266b StGB ausdrücklich ab, weil A die Karte nicht vom Karteninhaber oder Aussteller überlassen bekommen hat, sondern sie als Finder an sich nahm. Damit wird das geforderte Ergebnis in der Sache erfüllt, auch wenn die Formulierung nicht ausdrücklich den Begriff „berechtigter Karteninhaber“ verwendet.

**Belege:** „§ 266b StGB setzt voraus, dass der Täter die Karte vom Karteninhaber oder Aussteller überlassen bekommen hat.“; „A hat die EC-Karte des V jedoch auf dem Spielplatz gefunden, nicht von V oder der Sparkasse ausgehändigt erhalten.“; „Es fehlt mithin an dem erforderlichen Überlassungsverhältnis. Eine Strafbarkeit nach § 266b StGB scheidet aus.“

#### B.VII Unterschlagung gem. § 246 Abs. 1 StGB — 2/2

**✅ TRUE — C-064: Keine Unterschlagung der EC-Karte im Supermarkt** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort im Einsatz der EC-Karte im Supermarkt keine Unterschlagung der Karte sieht, weil A weiterhin vorhatte, die Karte zurückgelangen zu lassen, und sie später in den Sparkassenbriefkasten warf; eine Einordnung als straflose Gebrauchsanmaßung genügt. NICHT ERFÜLLT, wenn sie die bloße vorübergehende Nutzung der Karte als Zueignung der Karte nach § 246 Abs. 1 StGB bewertet.

**Begründung des Judge:** Die Antwort bewertet die vorübergehende Nutzung der EC-Karte im Supermarkt nicht als Zueignung. Sie stellt ausdrücklich fest, dass A weiterhin vorhatte, die Karte zurückzugeben, und sie anschließend in den Briefkasten der Sparkasse warf. Damit erfüllt sie das Kriterium.

**Belege:** „Eine bloß vorübergehende Nutzung ohne dauerhafte Enteignung des Eigentümers genügt nicht für den Zueignungstatbestand.“; „A hat sich die EC-Karte daher nicht i.S.v. § 246 StGB zugeeignet. Eine Unterschlagung liegt nicht vor.“

**✅ TRUE — C-065: Keine Unterschlagung der Waren** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort eine Unterschlagung der im Supermarkt erlangten Lebensmittel und Getränke ablehnt, weil K sie für die R-GmbH an A übereignete und sie danach nicht mehr fremd waren. NICHT ERFÜLLT, wenn sie § 246 Abs. 1 StGB an den Waren bejaht, ohne die Übereignung im Kassiervorgang zu berücksichtigen.

**Begründung des Judge:** Die Antwort stellt ausdrücklich fest, dass K die Waren für die R-GmbH durch Einigung und Übergabe an A übereignete und A dadurch Eigentümer wurde. Damit waren die Waren anschließend nicht mehr fremd, was eine Unterschlagung nach § 246 StGB ausschließt, auch wenn die Antwort dies nicht in einem eigenen Abschnitt unter diesem Tatbestand behandelt.

**Belege:** „„A hat die Waren daher nicht ‚weggenommen‘, sondern als Erfüllung des Kaufvertrags erhalten.““; „„Durch die Einigung über den Eigentumsübergang und die Übergabe wurde A Eigentümer.““; „„Sonstige Straftatbestände sind nicht verwirklicht.““

### Gesamtergebnis — 0/1

**❌ FALSE — C-046: Strafantrag bei geringwertigem Computerbetrug** _(★★, application)_

**Kriterium:** ERFÜLLT, wenn die Antwort bei bejahtem Computerbetrug wegen des Rechnungsbetrags von 32,76 € das Antragserfordernis nach §§ 263a Abs. 2, 263 Abs. 4, 248a StGB erkennt und feststellt, dass die erforderlichen Strafanträge laut Sachverhalt gestellt sind. NICHT ERFÜLLT, wenn sie bei bejahtem § 263a StGB das Strafantragserfordernis übersieht, die Verfolgung wegen Geringwertigkeit endgültig ausschließt oder fälschlich meint, kein Strafantrag liege vor.

**Begründung des Judge:** Die Antwort bejaht Computerbetrug bei einem Betrag von 32,76 €, behandelt aber das Antragserfordernis nach §§ 263a Abs. 2, 263 Abs. 4, 248a StGB nicht und stellt insbesondere nicht fest, dass die erforderlichen Strafanträge laut Sachverhalt gestellt wurden.

**Belege:** „Damit ist bei der Sparkasse ein effektiver Vermögensschaden in Höhe von 32,76 € eingetreten.“; „A hat sich wegen Computerbetrugs gemäß § 263a Abs. 1 Var. 3 StGB strafbar gemacht.“
