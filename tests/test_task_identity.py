"""Anonymization must keep the exam format and drop the case identity."""

from __future__ import annotations

import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from task_identity import (  # noqa: E402
    FORMAT_PATTERNS,
    GENERIC_FORMAT_LABEL,
    task_format_label,
)


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Fortgeschrittenenhausarbeit: „Kaufrausch mit Katerstimmung“", "Fortgeschrittenenhausarbeit"),
        ("Anfänger:innenhausarbeit: Bundeszwang und Rededrang", "Anfängerhausarbeit"),
        ("Anfängerhausarbeit: „Wie du mir, so ich dir“", "Anfängerhausarbeit"),
        ("Examensklausur: Ehe und Espresso", "Examensklausur"),
        ("Original-Examensklausur: Liebesbeweis mit rasanten Folgen", "Examensklausur"),
        ("Examensübungsklausur: Die falsche Gisela", "Examensübungsklausur"),
        ("Fortgeschrittenenübungsklausur: „MoPeG in 3D“", "Fortgeschrittenenübungsklausur"),
        ("Fortgeschrittenenklausur im Immobiliarsachenrecht: Rösterei, Ruin, Regress", "Fortgeschrittenenklausur"),
        ("Anfängerklausur – Grundrechte: Die Rennraddemo auf der Autobahn", "Anfängerklausur"),
        ("Anfängerübungsklausur: Alte Feindschaft", "Anfängerübungsklausur"),
        ("Zwischenprüfungsklausur: Rund um die WG-Party", "Zwischenprüfungsklausur"),
        ("Abschlussklausur Europarecht: „Germany first“", "Abschlussklausur"),
        ("Übungsklausur im Staatshaftungsrecht: Räumungsanspruch", "Übungsklausur"),
        ("Übungsfall zu Verträgen über digitale Produkte: Motivation ist alles", "Übungsfall"),
        (
            "Aufgabe 10 der Zweiten Juristischen Staatsprüfung 2019/2",
            "Klausur der Zweiten Juristischen Staatsprüfung",
        ),
        (
            "Aufgabe 8 der Zweiten Juristische Staatsprüfung 2020/2",
            "Klausur der Zweiten Juristischen Staatsprüfung",
        ),
    ],
)
def test_format_survives_anonymization(title: str, expected: str) -> None:
    assert task_format_label(title) == expected


@pytest.mark.parametrize(
    "title",
    [
        "Anfechtungsklage bei Nebenbestimmungen",
        "Fortsetzungsfeststellungsklage gegen die Untersagung eines politischen Straßentheaters",
        "",
        None,
    ],
)
def test_unknown_format_falls_back_to_generic(title: str | None) -> None:
    assert task_format_label(title) == GENERIC_FORMAT_LABEL


@pytest.mark.parametrize(
    "title",
    [
        "Examensklausur: Ehe und Espresso",
        "Fortgeschrittenenhausarbeit: „Kaufrausch mit Katerstimmung“",
        "Aufgabe 10 der Zweiten Juristischen Staatsprüfung 2019/2",
        "Fortgeschrittenenklausur zum Handels- und Gesellschaftsrecht: „Bezahlen für den Porsche der anderen?“",
    ],
)
def test_no_case_identity_leaks(title: str) -> None:
    """The label may only come from the fixed whitelist, never from the title."""
    label = task_format_label(title)
    assert label in {value for _, value in FORMAT_PATTERNS} | {GENERIC_FORMAT_LABEL}
    for leak in ("Espresso", "Kaufrausch", "Porsche", "Gisela", "2019", "2020", "Aufgabe 10"):
        assert leak.casefold() not in label.casefold()


def test_longest_match_wins_over_generic_klausur() -> None:
    """'Klausur' must not shadow the more specific labels that contain it."""
    assert task_format_label("Examensübungsklausur: X") != "Klausur"
    assert task_format_label("Fortgeschrittenenübungsklausur: X") == "Fortgeschrittenenübungsklausur"
    assert task_format_label("Irgendeine Klausur") == "Klausur"
