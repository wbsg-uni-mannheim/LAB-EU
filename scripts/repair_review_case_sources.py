#!/usr/bin/env python3
"""Repair verified extraction and transcription damage in eight review cases.

All replacements are bounded by text sentinels, are idempotent, and deliberately
avoid adding legal analysis that is not present in the published solution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
Transform = Callable[[str], str]


def replace_span(text: str, start: str, end: str, replacement: str) -> str:
    if replacement in text:
        return text
    start_at = text.find(start)
    if start_at < 0:
        raise ValueError(f"missing start sentinel: {start[:100]}")
    end_at = text.find(end, start_at)
    if end_at < 0:
        raise ValueError(f"missing end sentinel: {end[:100]}")
    return text[:start_at] + replacement + text[end_at + len(end) :]


def replace_exact(text: str, old: str, new: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise ValueError(f"missing exact source text: {old[:100]}")
    return text.replace(old, new, 1)


def replace_all(text: str, old: str, new: str) -> str:
    if old not in text:
        return text
    return text.replace(old, new)


def span(start: str, end: str, replacement: str) -> Transform:
    return lambda text: replace_span(text, start, end, replacement)


def exact(old: str, new: str) -> Transform:
    return lambda text: replace_exact(text, old, new)


def all_occurrences(old: str, new: str) -> Transform:
    return lambda text: replace_all(text, old, new)


def repair(relative_path: str, transforms: Iterable[Transform]) -> None:
    path = ROOT / relative_path
    text = path.read_text(encoding="utf-8")
    for transform in transforms:
        text = transform(text)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    repair(
        "tasks/de/oeffentliches-recht/europarecht/fortgeschrittenenklausur-europarecht-wohnungsbestand-in-burgerhand/evals/loesung.md",
        [
            exact(
                "so dass die Bundesrepublik Deutschtar EUV/GRCh/AEUV, 2. Aufl. 2023, AEUV Art. 258 Rn. 43. land passiv beteiligungsfähig",
                "so dass die Bundesrepublik Deutschland passiv beteiligungsfähig",
            ),
            span(
                "Der gem. Art. 63 Abs. 1 AEUV geschützte freie Kapitalverkehr erfasst (im Unterschied zum freien Zahlungsverkehr gem.",
                "Art. 63 Abs. 2 AEUV) einseitige Übertragungen",
                "Der gem. Art. 63 Abs. 1 AEUV geschützte freie Kapitalverkehr erfasst (im Unterschied zum freien Zahlungsverkehr gem. Art. 63 Abs. 2 AEUV) einseitige Übertragungen",
            ),
            span(
                "Hinweis: Bereits an dieser Stelle müssen die Bearbeiter*innen also zwischen den Immobilien von M und P",
                "und den Gesellschaftsanteilen der Aktionäre differenzieren.",
                "Hinweis: Bereits an dieser Stelle müssen die Bearbeiter*innen also zwischen den Immobilien von M und P und den Gesellschaftsanteilen der Aktionäre differenzieren.",
            ),
            all_occurrences("zum Nachteil der Vermieter", "zum Nachteil der Mieter*innen"),
        ],
    )

    repair(
        "tasks/de/strafrecht/materielles-strafrecht/fortgeschrittenenklausur-geldabheben-mit-hindernissen/evals/loesung.md",
        [
            exact(
                "Durch Mitnahme des Geldes hat W eigenen Gewahrsam am 100 €-Schein begründet.",
                "Durch Mitnahme des Geldes hat W eigenen Gewahrsam an den ausgezahlten Geldscheinen begründet.",
            ),
            span(
                "Dagegen spricht jedoch zum einen, dass dann auch in den Fällen ein Mitgewahrsam des Kunden vorläge, in denen",
                "sichts fehlender faktischer Zugriffsmöglichkeit auf das Geld",
                "Dagegen spricht jedoch zum einen, dass dann auch in den Fällen ein Mitgewahrsam des Kunden vorläge, in denen angesichts fehlender faktischer Zugriffsmöglichkeit auf das Geld",
            ),
            all_occurrences("mit dem geraubten Geld", "mit dem gestohlenen Geld"),
            exact("der Diebstahl zulasten des E", "der Diebstahl zulasten der S"),
        ],
    )

    repair(
        "tasks/de/strafrecht/materielles-strafrecht/anfangerubungsklausur-alte-feindschaft/evals/loesung.md",
        [
            exact("das körperliche Wohlbefinden des O", "das körperliche Wohlbefinden des N"),
            all_occurrences(
                "Dann ist eine versuchte Körperverletzung zulasten des O sowie eine fahrlässige Körperverletzung gegenüber N zu untersuchen. des vorgestellten vom tatsächlichen Kausalverlauf begründet.",
                "Dann ist eine versuchte Körperverletzung zulasten des O sowie eine fahrlässige Körperverletzung gegenüber N zu untersuchen.",
            ),
        ],
    )

    repair(
        "tasks/de/strafrecht/materielles-strafrecht/examensubungsklausur-strafrecht-nur-bares-ist-wahres/evals/loesung.md",
        [
            exact(
                "Die Ortsverschützt, vgl. nur w.N. änderung kann durch Drohung oder Gewalt, aber auch durch List oder Täuschung bewirkt werden.",
                "Die Ortsveränderung kann durch Drohung oder Gewalt, aber auch durch List oder Täuschung bewirkt werden.",
            ),
            all_occurrences(" § 239a Rn. 4a.", ""),
            exact(
                "##### 2.\n\n##### 3. Ergebnis\n\nA und E sind strafbar gem. §§ 239b",
                "##### 2. Rechtswidrigkeit und Schuld\n\nMangels Rechtfertigungs-, Schuldausschließungs- und/oder Entschuldigungsgründen handelten A und E auch rechtswidrig und schuldhaft.\n\n##### 3. Ergebnis\n\nA und E sind strafbar gem. §§ 239b",
            ),
            exact(
                "##### 2.\n\n##### 3. Ergebnis\n\nA und E haben sich wegen gemeinschaftlich begangener gefährlicher Körperverletzung",
                "##### 2. Rechtswidrigkeit und Schuld\n\nMangels Rechtfertigungs-, Schuldausschließungs- und/oder Entschuldigungsgründen handelten A und E auch rechtswidrig und schuldhaft.\n\n##### 3. Ergebnis\n\nA und E haben sich wegen gemeinschaftlich begangener gefährlicher Körperverletzung",
            ),
        ],
    )

    repair(
        "tasks/de/strafrecht/materielles-strafrecht/fortgeschrittenenhausarbeit-die-lugen-des-finder-schwindlers/evals/loesung.md",
        [
            all_occurrences("OPC-GmbH", "OCP-GmbH"),
            exact("der GmbH als Requisite diente", "der GmbH als Bargeldreserve diente"),
            span(
                "##### 1. Vorprüfung\n\nlichen Voraussetzungen auch auf § 261 Abs. 3 StGB",
                "(siehe § 261 Abs. 7 StGB: „wird nach den Absätzen 1 bis 6 […] bestraft“).",
                """##### 1. Vorprüfung

T hat O nichts auf ihr Schweizer Nummernkonto zurückgezahlt. In der Folge kam es auch nicht zu den von O geplanten, die Herkunft des Geldbetrages verschleiernden Transaktionen. Mangels Vornahme einer tauglichen Geldwäschehandlung gem. § 261 Abs. 1 S. 1, Abs. 7 StGB ist die Geldwäsche der O daher nicht vollendet. Der Versuch der Geldwäsche ist gem. §§ 23 Abs. 1 Alt. 2, 261 Abs. 3 StGB strafbar. § 261 Abs. 7 StGB erstreckt die Strafbarkeit der Selbstgeldwäsche bei Vorliegen ihrer zusätzlichen Voraussetzungen auch auf § 261 Abs. 3 StGB, sodass die versuchte Selbstgeldwäsche ebenfalls strafbar ist (siehe § 261 Abs. 7 StGB: „wird nach den Absätzen 1 bis 6 […] bestraft“).""",
            ),
            span(
                "O hat sich wegen leichtfertiger Geldwäsche nach § 261 Abs. 1 S. 1 Nr. 3 Alt. 1, Abs. 6 S. 1 StGB strafbar gemacht, indem sie sich das mit dem Drogengeld des G finanzierte E-Bike durch Täuschung gegenüber T verschaffte.",
                "da auch O davon ausgehen konnte, dass T einen Luxusgegenstand wie das E-Bike wohl nicht aus seinen eigenen Ersparnissen finanziert hat.",
                """O hat sich wegen leichtfertiger Geldwäsche nach § 261 Abs. 1 S. 1 Nr. 3 Alt. 1, Abs. 6 S. 1 StGB strafbar gemacht, indem sie sich das mit dem Drogengeld des G finanzierte E-Bike durch Täuschung gegenüber T verschaffte. Sie wusste zwar nichts davon, dass das E-Bike mit den Drogengeldern des G gekauft wurde. Allerdings war sich O aufgrund der medialen Berichterstattung inzwischen darüber bewusst, dass T durch seinen „Finder-Schwindel“ mehrere Frauen um große Summen betrogen hat. Mit Blick auf diese von O durchschaute Serien-Betrugstäterschaft musste sich ihr durchaus der Gedanke aufdrängen, dass das E-Bike aus einer Straftat herrührt. Folglich hat O die rechtswidrige Herkunft des E-Bikes leichtfertig nicht erkannt. Sie verschaffte sich somit leichtfertig einen Gegenstand, der aus einer rechtswidrigen Tat herrührt. O ist strafbar wegen leichtfertiger Geldwäsche nach § 261 Abs. 1 S. 1 Nr. 3 Alt. 1, Abs. 6 S. 1 StGB.

Hinweis: Eine andere Ansicht ist mit entsprechender Begründung vertretbar, wenn auch eher fernliegend. Mit Blick auf die verfassungsrechtlich ohnehin problematische Weite des Leichtfertigkeitstatbestandes kann für eine restriktive Auslegung dieses Merkmals argumentiert werden. Die Leichtfertigkeit der O könnte mit dem Argument verneint werden, dass sich ihr auch die Zurechnung des E-Bikes zum Kreis inkriminierter Gegenstände gerade nicht aufdrängen musste. Dies vermag jedoch nur bedingt zu überzeugen, da auch O davon ausgehen konnte, dass T einen Luxusgegenstand wie das E-Bike wohl nicht aus seinen eigenen Ersparnissen finanziert hat.""",
            ),
            exact(
                "###### a) Tatentschluss bzgl. Gegenstand, der aus rechtswidriger Vortat herrührt\n\n###### b) Tatentschluss bzgl. Verschaffen",
                """###### a) Tatentschluss bzgl. Gegenstand, der aus rechtswidriger Vortat herrührt

Die rechtswidrige Vortat liegt in dem Betrug der O gegenüber und zulasten T. Auch als Täterin der Vortat kann O wegen Geldwäsche zu bestrafen sein, § 261 Abs. 7 StGB. O war über ihre Vortat umfassend orientiert und handelte diesbezüglich mit Tatentschluss. O wusste auch, dass das ihr übergebene E-Bike aus der Betrugs-Vortat „herrührt“ i.S.d. § 261 Abs. 1 S. 1 StGB. Ihr war klar, dass es sich hierbei um den unmittelbar aus der Vortat herrührenden Ursprungsgegenstand handelt.

###### b) Tatentschluss bzgl. Verschaffen""",
            ),
            span(
                "Sie setzte auch unmittelbar zur Tatbestandsverwirklichung an i.S.d. § 22 StGB",
                "Online-Plattform zum Verkauf anbot.",
                """Sie setzte auch unmittelbar zur Tatbestandsverwirklichung an i.S.d. § 22 StGB, indem sie mit dem Erstellen des Online-Angebots bereits erste Ausführungshandlungen vornahm. Aus ihrer Sicht hatte O bereits alles zur Tatbestandsverwirklichung Erforderliche getan und sie hat subjektiv die Schwelle zum „Jetzt-geht-es-los“ überschritten. Um das E-Bike zu kaufen, musste der*die Dritte nur noch auf den „Jetzt-kaufen“-Button klicken. Nach Os Vorstellung von der Tat waren keine weiteren wesentlichen Zwischenakte mehr zur Tatbestandsverwirklichung nötig. Sie hat zudem objektiv mit dem Einstellen des Angebots bereits solche Handlungen vorgenommen, dass bei weiterem Fortgang des Geschehens mit einem Kauf des E-Bikes und somit einem Verschaffen des inkriminierten Gegenstandes an einen Dritten zu rechnen war.

##### 4. Ergebnis

Sofern ein Betrug der O an T im Zusammenhang mit der Erlangung des E-Bikes bejaht wird, hat O sich wegen versuchter Selbstgeldwäsche gem. §§ 261 Abs. 1 S. 1 Nr. 3 Alt. 2, Abs. 3, Abs. 7, 22, 23 Abs. 1 StGB strafbar gemacht, indem sie das durch einen Betrug erlangte E-Bike auf der Online-Plattform zum Verkauf anbot.""",
            ),
        ],
    )

    repair(
        "tasks/de/strafrecht/materielles-strafrecht/anfangerklausur-das-haus-am-see/documents/sachverhalt.md",
        [exact("tritt Norbert mit ihren Stollenschuhen", "tritt Ludwig mit ihren Stollenschuhen")],
    )

    repair(
        "tasks/de/zivilrecht/schuldrecht/anfangerklausur-bgb-at-schuldrecht-at-gefalschter-dalvador-sali/evals/loesung.md",
        [
            all_occurrences(" 11. Aufl. 2022, § 10 Rn. 4.", ""),
            exact("das Verfügungsgeschäft über die Replik", "das Verfügungsgeschäft über die Geldscheine"),
            exact(
                "V dürfte weiterhin kein Recht zum Besitz nach § 986 BGB haben. § 986 BGB darstellen.",
                "V dürfte weiterhin kein Recht zum Besitz nach § 986 BGB haben. Das hier einzig denkbare Recht zum Besitz könnte sich aus dem zwischen K und V geschlossenen Kaufvertrag ergeben. Dieser ist allerdings von Anfang an aufgrund der durch K vorgenommenen Anfechtung nichtig und kann damit kein Recht zum Besitz i.S.d. § 986 BGB darstellen.",
            ),
            exact(
                "K müsste ohne Rechtsgrund geleistet haben. Der einzig in Betracht kommende Rechtsgrund ist hier der zwischen K und V abgeschlossene Kaufvertrag. 1 BGB. Damit leistete K ohne Rechtsgrund.",
                "K müsste ohne Rechtsgrund geleistet haben. Der einzig in Betracht kommende Rechtsgrund ist hier der zwischen K und V abgeschlossene Kaufvertrag. Dieser ist allerdings nach erfolgter Anfechtung von Anfang an nichtig, § 142 Abs. 1 BGB. Damit leistete K ohne Rechtsgrund.",
            ),
        ],
    )

    repair(
        "tasks/de/zivilrecht/schuldrecht/fortgeschrittenenhausarbeit-kaufrausch-mit-katerstimmung/evals/loesung.md",
        [
            exact(
                "Veräußerung der Sache, die sich auf Herausgabe des Erlöses richten, bestehen daher neben und unabhängig von den §§ 987 ff. BGB.",
                "Wiederum stellt sich die Frage nach der Sperrwirkung eines etwaigen EBVs. Eine solche Sperrwirkung besteht jedoch nicht im Hinblick auf Ansprüche, die auf einen Ausgleich für die Nichtherausgabe der Sache gerichtet sind. Denn auch hier gilt, dass die §§ 987 ff. BGB nur Ansprüche wegen Nutzung oder Verschlechterung der Sache und wegen Verwendungen auf die Sache regeln. Ansprüche wegen Veräußerung der Sache, die sich auf Herausgabe des Erlöses richten, bestehen daher neben und unabhängig von den §§ 987 ff. BGB.",
            ),
            exact(
                "tung bezweckte, das Grundstück zu verbessern und diente folglich nicht dessen Erhalt oder Wieder-herstellung. § 536a Abs. 2 Nr. 2 BGB ist daher nicht anwendbar.",
                "Demnach dürfte keine notwendige Aufwendung zur Mängelbeseitigung i.S.d. § 536a Abs. 2 Nr. 2 BGB gegeben sein. Eine notwendige Aufwendung liegt vor, wenn sie der Mietsache unmittelbar zugutekommt und gerade ihrem Erhalt, ihrer ordnungsgemäßen Bewirtschaftung oder ihrer Wiederherstellung dient (enge Auslegung). § 539 Abs. 1 BGB erfasst hingegen alle sonstigen Maßnahmen, die die Mietsache lediglich verbessern oder verändern, d.h. nützliche Aufwendungen und Luxusaufwendungen. Der Bau des Lagers diente ersichtlich nicht der Mängelbeseitigung am Grundstück. Die Errichtung bezweckte, das Grundstück zu verbessern und diente folglich nicht dessen Erhalt oder Wiederherstellung. § 536a Abs. 2 Nr. 2 BGB ist daher nicht anwendbar.",
            ),
            exact(
                "jedoch noch vor Ablauf der ordentlichen Kündigungsfrist (und damit Wegfall der Besitzberechtigung) zurückgegeben und damit den Besitz verloren. Zusammenfassend stand M zunächst ein Recht zum Besitz i.S.d. § 986 Abs. 1 S. 1 BGB zu, im Zeit-punkt des Wegfalls dieses Besitzrechts war M bereits nicht mehr Besitzer des Grundstücks.",
                "Nach der Rechtsprechung reicht es folglich auch aus, wenn M zwischen der Vornahme der Verwendungen und der Geltendmachung von Verwendungsersatzansprüchen zu irgendeinem Zeitpunkt Besitzer ohne Besitzrecht war. Dies ist indes auch nicht der Fall. Zwar war M durch die ordentliche Kündigung des Mietvertrags gegenüber S nicht mehr zum Besitz berechtigt. M hat das Grundstück jedoch noch vor Ablauf der ordentlichen Kündigungsfrist (und damit Wegfall der Besitzberechtigung) zurückgegeben und damit den Besitz verloren. Zusammenfassend stand M zunächst ein Recht zum Besitz i.S.d. § 986 Abs. 1 S. 1 BGB zu, im Zeitpunkt des Wegfalls dieses Besitzrechts war M bereits nicht mehr Besitzer des Grundstücks.",
            ),
            exact(
                "rechtliche Ebene zu verlagern. Fraglich ist daher, ob M gegen S ein bereicherungsrechtlicher Ersatzanspruch zusteht.",
                "Gem. § 951 Abs. 1 S. 1 BGB kann er daher von S eine Vergütung in Geld nach den Vorschriften über die Herausgabe einer ungerechtfertigten Bereicherung verlangen. Der Ersatzanspruch in § 951 Abs. 1 S. 1 BGB ist nach allgemeiner Ansicht eine Rechtsgrundverweisung auf das Bereicherungsrecht. Sie drückt die Entscheidung des Gesetzgebers aus, den gesetzlichen Eigentumserwerb nach §§ 946 f. BGB sachenrechtlich endgültig zu gestalten und den notwendigen Vermögensausgleich auf die schuldrechtliche Ebene zu verlagern. Fraglich ist daher, ob M gegen S ein bereicherungsrechtlicher Ersatzanspruch zusteht.",
            ),
        ],
    )

    print("Repaired verified extraction and transcription damage in 8 review cases.")


if __name__ == "__main__":
    main()
