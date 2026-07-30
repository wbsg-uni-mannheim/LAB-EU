#!/usr/bin/env python3
"""Repair verified page-column extraction damage in four selected ZJS solutions.

The replacements are deliberately bounded by source-text sentinels.  The script is
idempotent and fails if a neither the damaged nor the repaired form is present.
Substantive editorial additions live directly in the affected solution files and are
not part of this mechanical source restoration.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def replace_span(text: str, start: str, end: str, replacement: str) -> str:
    if replacement in text:
        return text
    start_at = text.find(start)
    if start_at < 0:
        raise ValueError(f"missing start sentinel: {start[:80]}")
    end_at = text.find(end, start_at)
    if end_at < 0:
        raise ValueError(f"missing end sentinel: {end[:80]}")
    return text[:start_at] + replacement + text[end_at + len(end) :]


def replace_exact(text: str, old: str, new: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise ValueError(f"missing exact source text: {old[:80]}")
    return text.replace(old, new, 1)


def repair(path: Path, transforms) -> None:
    text = path.read_text(encoding="utf-8")
    for transform in transforms:
        text = transform(text)
    path.write_text(text, encoding="utf-8")


def span(start: str, end: str, replacement: str):
    return lambda text: replace_span(text, start, end, replacement)


def exact(old: str, new: str):
    return lambda text: replace_exact(text, old, new)


def main() -> None:
    raeumung = ROOT / "tasks/de/oeffentliches-recht/staatshaftungsrecht/ubungsklausur-im-staatshaftungsrecht-raumungsanspruch-und-mietausfallschaden/evals/loesung.md"
    repair(
        raeumung,
        [
            span(
                "Hinweis: Eine andere Ansicht dürfte auch nicht aufgrund der Rechtsprechung des BVerwG",
                "Insgesamt sprechen bessere Argumente dafür, dass weiterhin von einer Unmittelbarkeit der Folgen des hoheitlichen Handelns auszugehen ist, da eine Unterbrechung des Zurechnungszusammenhangs nicht vorliegt.",
                """Hinweis: Eine andere Ansicht dürfte auch nicht aufgrund der Rechtsprechung des BVerwG (BVerwG DÖV 2001, 732) vertretbar sein. Die dort entschiedene Fallkonstellation weicht von der vorliegenden Konstellation ab. Vorliegend geht es nicht um das Verhalten der V als Betroffene, sondern um das der M als Dritte. Dass M aufgrund eigenen Entschlusses nach Ablauf der Einweisungsfrist in der Wohnung verbleibt, unterbricht den Zurechnungszusammenhang nicht. Vielmehr hat sich ein spezifisches Risiko verwirklicht, das in der hoheitlichen Maßnahme typischerweise angelegt war.

Hinweis: Mit dem Ende der Beschlagnahme entfällt zwar der Rechtsgrund, nicht jedoch die Nutzung selbst. Dieser Zustand ist grundsätzlich weiterhin der Behörde zuzurechnen.

Fraglich ist, ob das spätere Verhalten der V eine andere Bewertung verlangt. Nach Ablauf der Einweisungsfrist führte V über einen erheblichen Zeitraum Vertragsverhandlungen mit M und duldete deren Verbleib. Dies könnte als eigenständiger Willensentschluss und als allgemeines Lebensrisiko bewertet werden. Dagegen spricht, dass V kein neues Risiko geschaffen, sondern den bereits eingetretenen rechtswidrigen Zustand lediglich verlängert hat. Entscheidend ist, dass M die Wohnung nach Ablauf der Einweisungsfrist nicht räumte und sich damit gerade die typische Gefahr der behördlichen Einweisung verwirklichte. Spätestens nach dem Scheitern der Verhandlungen Ende März 2020 verlangte V von der Stadt Räumung und Reinigung. Die Verzögerung kann bei Verjährung, Mitverschulden und Treu und Glauben berücksichtigt werden, unterbricht den Zurechnungszusammenhang aber nicht. Insgesamt sprechen die besseren Argumente weiterhin für die Unmittelbarkeit der Folgen des hoheitlichen Handelns.""",
            ),
            span(
                "Der Folgenbeseitigungsanspruch (FBA) ist auf die Beseitigung der Folgen eines öffentlich-rechtlichen Handelns gerichtet.",
                "sodass der allgemeine ordnungsrechtliche Entschädigungsanspruch nach § 39 OBG NRW anwendbar ist.",
                """Der Folgenbeseitigungsanspruch (FBA) ist auf die Beseitigung der Folgen eines öffentlich-rechtlichen Handelns gerichtet. Seine Rechtsfolge beinhaltet grundsätzlich keinen Anspruch auf Geld, sodass der FBA insoweit nicht in Betracht kommt.

#### 2. Ordnungsrechtlicher Entschädigungsanspruch

In Betracht kommt ein ordnungsrechtlicher Entschädigungsanspruch, soweit spezialgesetzliche Vorschriften nicht vorliegen. Spezialgesetzliche Regelungen, die für Fälle der Obdachloseneinweisung dem Eigentümer eine Entschädigung zusprechen, existieren nicht, sodass der allgemeine ordnungsrechtliche Entschädigungsanspruch nach § 39 OBG NRW anwendbar ist.""",
            ),
            exact(
                "Der Mietausfall für die Zeit bis zum Ablauf der Einweisungsverfügung, insgesamt vier Monate (März bis Juli 2018), ist erstattungsfähig.",
                "Der Mietausfall für die Zeit bis zum Ablauf der Einweisungsverfügung ist erstattungsfähig.",
            ),
            exact(
                "V hat nach § 39 Abs. 1 lit. a OBG NRW einen Anspruch auf den Mietausfall für die Zeit der Einweisungsverfügung von März bis Juli 2018.",
                "V hat nach § 39 Abs. 1 lit. a OBG NRW einen Anspruch auf den Mietausfall für den Zeitraum der Einweisungsverfügung.",
            ),
            exact(
                "Weiter könnte ein Anspruch aus § 839 Abs. 1 BGB i.V.m. Art. 34 GG in Betracht kommen. Wie bereits ausgeführt, ist der Amtshaftungsanspruch neben dem Anspruch nach § 39 Abs. 1 OBG NRW anwendbar, vgl. § 40 Abs. 5 OBG NRW. deliktische Haftung des Beamten, die nach Art. 34 S. 1 GG im Wege der Schuldübernahme auf den Staat übergeht.",
                "Weiter könnte ein Anspruch aus § 839 Abs. 1 BGB i.V.m. Art. 34 GG in Betracht kommen. Wie bereits ausgeführt, ist der Amtshaftungsanspruch neben dem Anspruch nach § 39 Abs. 1 OBG NRW anwendbar, vgl. § 40 Abs. 5 OBG NRW. Es handelt sich um eine persönliche deliktische Haftung des Beamten, die nach Art. 34 S. 1 GG im Wege der Schuldübernahme auf den Staat übergeht.",
            ),
            exact(
                "Ein Haftungsausschluss gem. § 839 Abs. 1 S. 2, Abs. 2 S. 1,",
                "Ein Haftungsausschluss gem. § 839 Abs. 1 S. 2, Abs. 2 S. 1, Abs. 3 BGB ist nicht gegeben. Ein anderweitiger Anspruch gem. § 839 Abs. 1 S. 2 BGB kommt nicht in Betracht.",
            ),
        ],
    )

    wg = ROOT / "tasks/de/strafrecht/materielles-strafrecht/zwischenprufungsklausur-rund-um-die-wg-party/evals/loesung.md"
    repair(
        wg,
        [
            span(
                "Des Weiteren müsste B mit Zueignungsabsicht gehandelt haben.",
                "Der subjektive Tatbestand ist nicht erfüllt.",
                """Des Weiteren müsste B mit Zueignungsabsicht gehandelt haben. Zueignungsabsicht liegt vor, wenn der Täter die Sache selbst oder den in ihr verkörperten funktionsspezifischen Wert seinem Vermögen oder dem Vermögen eines Dritten wenigstens vorübergehend einverleiben und den Berechtigten auf Dauer aus seiner wirtschaftlichen Position verdrängen will. Zum Zeitpunkt des Gewahrsamsbruchs, § 8 S. 1 StGB, wollte B die Sporttasche nur zum Transport benutzen und am nächsten Tag zurückbringen. Somit fehlte ihr der Vorsatz zur dauerhaften Enteignung. Dass sie sich erst zu Hause nach der unerwarteten Verunreinigung entschloss, die Tasche nicht zurückzugeben und in ihren Schrank zu legen, begründet den erforderlichen Vorsatz nicht rückwirkend. Also handelte B ohne Zueignungsabsicht; der subjektive Tatbestand ist nicht erfüllt.""",
            ),
            exact("B hat sich nicht wegen Diebstahls gem. § 242 Abs.", "B hat sich nicht wegen Diebstahls gem. § 242 Abs. 1 StGB an der Sporttasche strafbar gemacht."),
            span(
                "Weiterhin müsste B die zwei Chipstüten und die Flasche Rum weggenommen haben.",
                "Also hat B die zwei Chipstüten und die Flasche Rum weggenommen.",
                """Weiterhin müsste B die zwei Chipstüten und die Flasche Rum weggenommen haben. Ursprünglich standen die Gegenstände im Supermarkt. Bei kleinen, leicht transportierbaren Gegenständen kann neuer Gewahrsam bereits durch das Verbergen in einer höchstpersönlichen Gewahrsamsenklave entstehen. Zwar genügt ein bloßes Verstecken im Herrschaftsbereich des bisherigen Gewahrsamsinhabers regelmäßig nicht. Die verschlossene Sporttasche ordnete B jedoch äußerlich ihrer Privatsphäre zu; ein Öffnen durch Mitarbeitende wäre rechtfertigungsbedürftig gewesen. Durch Einstecken und Verschließen begründete B daher eigenen Gewahrsam ohne Einverständnis der S-GmbH. Spätestens mit dem Verlassen des Supermarkts lag die Wegnahme vor.""",
            ),
            exact(
                "B hat sich wegen Diebstahls in einem besonders schweren Fall gem. § 242 Abs. 1 StGB i.V.m. § 243 Abs. 1 S. 2 Nr. 3 Var.",
                "B hat sich wegen Diebstahls in einem besonders schweren Fall gem. § 242 Abs. 1 StGB i.V.m. § 243 Abs. 1 S. 2 Nr. 2 StGB strafbar gemacht.",
            ),
            span(
                "Hinweis: Eine Sachbeschädigung (§ 303 Abs. 1 StGB) durch Abreißen des Etiketts kommt schon desIV.",
                "Eine Sachbeschädigung durch das Hineinlegen der Chips liegt daher nicht vor.",
                """Hinweis: Eine Sachbeschädigung (§ 303 Abs. 1 StGB) durch Abreißen des Etiketts kommt schon deshalb nicht in Betracht, weil nicht ersichtlich ist, dass dabei etwas beschädigt wurde. Das Etikett ist kein wesentlicher Bestandteil der Tasche, sodass zwei miteinander verbundene Sachen vorliegen.

### IV. § 303 Abs. 1 StGB durch das Hineinlegen der Chips in die Tasche

B könnte sich gem. § 303 Abs. 1 StGB wegen Sachbeschädigung strafbar gemacht haben, indem sie die Chips in die Sporttasche legte. Allerdings wäre die Tasche leicht zu reinigen gewesen, sodass keine Substanzverletzung und damit keine Beschädigung vorliegt. Auch handelte B ohne Vorsatz. Eine Sachbeschädigung liegt daher nicht vor.""",
            ),
            span(
                "Das Zufahren auf M könnte einen ähnlichen, ebenso gefährlichen Eingriff i.S.d. § 315b Abs. 1 Nr. 3",
                "###### aa) Grobe Einwirkung von einigem Gewicht",
                """Das Zufahren auf M könnte einen ähnlichen, ebenso gefährlichen Eingriff i.S.d. § 315b Abs. 1 Nr. 3 StGB darstellen. § 315b StGB erfasst grundsätzlich verkehrsfremde Eingriffe, während § 315c StGB Fehler im fließenden oder ruhenden Verkehr pönalisiert. F fuhr im fließenden öffentlichen Straßenverkehr auf M zu. Eine Ausnahme gilt jedoch, wenn der Fahrzeugführer das Fahrzeug bewusst zweckwidrig als Mittel zur Verletzung von Menschen oder zur Beschädigung von Sachen einsetzt (verkehrsfeindlicher Inneneingriff).

###### aa) Grobe Einwirkung von einigem Gewicht""",
            ),
            span(
                "F müsste einen Tatentschluss gefasst haben.",
                "F hat unmittelbar angesetzt.",
                """F müsste einen Tatentschluss gefasst haben. Er wusste, dass M eine für ihn fremde Sache war, und wollte den Pudel überfahren und töten. Das Töten eines Tieres ist ein Zerstören i.S.d. § 303 Abs. 1 StGB. F hatte daher Tatentschluss zur Zerstörung einer fremden Sache.

###### b) Unmittelbares Ansetzen

F setzte nach seiner Vorstellung unmittelbar an, als er zielgerichtet auf M zufuhr und ihn nur wegen dessen Ausweichbewegung verfehlte. Er hatte die Schwelle zum „Jetzt-geht-es-los“ überschritten; weitere wesentliche Zwischenakte waren nach seinem Tatplan nicht erforderlich.""",
            ),
            exact(
                "Außerdem wird durch die Gesamtbetrachtungslehre dem Täter ein Anreiz zum Rücktritt gegeben, was wiederum dem Opferschutz dient. Dementspre",
                "Außerdem wird durch die Gesamtbetrachtungslehre dem Täter ein Anreiz zum Rücktritt gegeben, was wiederum dem Opferschutz dient. Dementsprechend wird der Gesamtbetrachtungslehre gefolgt. Der Versuch ist nicht fehlgeschlagen.",
            ),
            exact("A könnte sich wegen Anstiftung zum gefährlichen Eingriff im Straßenverkehr gem. §§ 315b Abs. 1", "A könnte sich wegen Anstiftung zum gefährlichen Eingriff im Straßenverkehr gem. §§ 315b Abs. 1 Nr. 3, 26 StGB strafbar gemacht haben, indem sie F zurief, M zu überfahren."),
            exact("A hat sich wegen Anstiftung zur versuchten Sachbeschädigung gem. §§ 303 Abs. 1, Abs.", "A hat sich wegen Anstiftung zur versuchten Sachbeschädigung gem. §§ 303 Abs. 1, Abs. 3, 26 StGB strafbar gemacht."),
        ],
    )

    liebe = ROOT / "tasks/de/strafrecht/materielles-strafrecht/original-examensklausur-liebesbeweis-mit-rasanten-folgen-mit-exkurs-zu-paragraph-315d-stgb/evals/loesung.md"
    repair(
        liebe,
        [
            span(
                "B müsste auch Vorsatz hinsichtlich der vorsätzlichen rechtswidrigen Tat des A gehabt haben.",
                "Anmerkung: Ein anderes Ergebnis ist vertretbar, wenn man darauf abstellt, dass auch bei Gegenständen in der Wohnung des C nicht ausgeschlossen ist, dass diese Dritten gehören (etwa bei Kauf unter Eigentumsvorbehalt oder geliehenen Gegenständen).",
                """B müsste auch Vorsatz hinsichtlich der vorsätzlichen rechtswidrigen Tat des A gehabt haben. A und B gingen davon aus, der Monitor des C werde zerstört; tatsächlich gehörte der Monitor der M-GmbH. A unterlag einem error in obiecto. Nach einer Ansicht ist dieser Irrtum auch für den Hintermann unbeachtlich. Eine andere Ansicht behandelt ihn beim Anstifter als aberratio ictus; Rechtsprechung und vermittelnde Literatur stellen darauf ab, ob die Verwechslung in den Grenzen des Vorhersehbaren lag beziehungsweise wem das Verwechslungsrisiko zuzurechnen ist. A erhöhte das Risiko eigenständig, indem er entgegen dem Vorschlag des B in ein anderes Gebäude einbrach. Danach fehlte B der Vorsatz hinsichtlich der Sachbeschädigung am Monitor. Die Gegenauffassung ist vertretbar, wenn sie die mögliche Drittzugehörigkeit von Gegenständen in Cs Wohnung tragfähig einbezieht.""",
            ),
            exact(
                "B könnte sich wegen versuchter Anstiftung zum Einbruchdiebstahl in eine dauerhaft genutzte Privatwohnung gem. §§ 242 Abs. 1, 244 Abs. 4, 30 Abs. 1 S. 1 Var.",
                "B könnte sich wegen versuchter Anstiftung zum Einbruchdiebstahl in eine dauerhaft genutzte Privatwohnung gem. §§ 242 Abs. 1, 244 Abs. 4, 30 Abs. 1 S. 1 Var. 1 StGB strafbar gemacht haben.",
            ),
            span(
                "A müsste einen Tatentschluss gefasst haben.",
                "B hat alle Handlungen vollbracht, die aus seiner Sicht zum Bestimmen des A erforderlich waren, und damit unmittelbar angesetzt.",
                """B müsste Tatentschluss zur Anstiftung eines Einbruchdiebstahls in eine dauerhaft genutzte Privatwohnung gehabt haben. Er stellte sich vor, A werde die Scheibe der Penthouse-Wohnung des C einschlagen, dort einsteigen und Bargeld aus der Schreibtischschublade nehmen. Die Wohnung war als einzige Wohnung des C auf längerfristige Nutzung angelegt. B hatte daher Vorsatz bezüglich des Verbrechens nach §§ 242 Abs. 1, 244 Abs. 4 StGB und bezüglich des Bestimmens. Mit seinem vollständig unterbreiteten Vorschlag hatte er aus seiner Sicht alle erforderlichen Bestimmungshandlungen vorgenommen und unmittelbar angesetzt.""",
            ),
            exact(
                "C hat sich wegen Mordes gem. §§ 212 Abs. 1, 211 Abs. 1 und Abs. 2, Gr. 3 Var. 1 StGB strafbar gemacht haben, indem er auf 200 km/h beschleunigte und mit Höchstgeschwindigkeit auf die rote Ampel zufuhr.",
                "C hat sich wegen Mordes gem. §§ 212 Abs. 1, 211 Abs. 2 StGB strafbar gemacht. Tragfähig ist der in der Lösung vertretene Weg über sonstige niedrige Beweggründe; wer die ausdrücklich als vertretbar bezeichnete Ermöglichungsabsicht bejaht, darf denselben Rennzweck nicht zusätzlich nochmals als niedrigen Beweggrund verwerten.",
            ),
        ],
    )

    print("Repaired verified extraction damage in 3 source files; the fourth was patched directly.")


if __name__ == "__main__":
    main()
