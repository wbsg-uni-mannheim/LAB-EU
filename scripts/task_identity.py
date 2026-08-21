"""Task identity handling shared by every LAB-EU solver harness.

The solver must not be able to look up the original case, but it must know the
exam format: the rubrics grade against the depth conventions of that format.
"""

from __future__ import annotations

import re

GENERIC_FORMAT_LABEL = "Juristische Fallbearbeitung"

# Ordered longest/most specific first: the first pattern that matches the
# original title wins. Only the fixed label on the right is ever emitted, so a
# case name can never leak through this table.
FORMAT_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"zweite\w*\s+juristische\w*\s+staatspr[üu]fung", "Klausur der Zweiten Juristischen Staatsprüfung"),
    (r"assessorklausur", "Klausur der Zweiten Juristischen Staatsprüfung"),
    (r"anf[äa]nger[\w:]*hausarbeit", "Anfängerhausarbeit"),
    (r"fortgeschrittenen\w*hausarbeit", "Fortgeschrittenenhausarbeit"),
    (r"examens\w*hausarbeit", "Examenshausarbeit"),
    (r"hausarbeit", "Hausarbeit"),
    (r"examens[üu]bungsklausur", "Examensübungsklausur"),
    (r"examensklausur", "Examensklausur"),
    (r"fortgeschrittenen[üu]bungsklausur", "Fortgeschrittenenübungsklausur"),
    (r"fortgeschrittenenklausur", "Fortgeschrittenenklausur"),
    (r"anf[äa]nger[üu]bungsklausur", "Anfängerübungsklausur"),
    (r"anf[äa]nger[\w:]*klausur", "Anfängerklausur"),
    (r"zwischenpr[üu]fungsklausur", "Zwischenprüfungsklausur"),
    (r"abschlussklausur", "Abschlussklausur"),
    (r"[üu]bungsklausur", "Übungsklausur"),
    (r"[üu]bungsfall", "Übungsfall"),
    (r"klausur", "Klausur"),
)


def task_format_label(title: str | None) -> str:
    """Return the anonymized task title: the exam format, never the case identity.

    The rubrics encode the depth expectation of the original format -- a
    Fortgeschrittenenhausarbeit is graded on parallel Anspruchsgrundlagen, a
    Zweite-Staatsprüfung paper on Urteilsformalia and a full Hilfsgutachten.
    Replacing every title with a generic placeholder hid that expectation from
    the solver while the rubric kept measuring it, which cost the Hausarbeiten
    roughly 15 points of pass rate (see docs/codex-web-fehleranalyse-de-core-45.md).

    Only labels from FORMAT_PATTERNS are returned, so case names, Fundstellen,
    exam years and Aufgabe numbers cannot pass through.
    """
    if not title:
        return GENERIC_FORMAT_LABEL
    haystack = title.casefold()
    for pattern, label in FORMAT_PATTERNS:
        if re.search(pattern, haystack):
            return label
    return GENERIC_FORMAT_LABEL
