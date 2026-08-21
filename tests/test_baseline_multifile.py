"""Baseline harness with more than one deliverable (Zweites Staatsexamen)."""

from __future__ import annotations

import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import baseline_prompt as bp  # noqa: E402

DELIVERABLES = ["schriftsatz-sut.md", "mandantenschreiben-sut.md", "hilfsgutachten-sut.md"]


def test_splits_marker_separated_response() -> None:
    text = (
        "=== FILE: schriftsatz-sut.md ===\nAn das Gericht\n\n"
        "=== FILE: mandantenschreiben-sut.md ===\nSehr geehrter Herr M,\n\n"
        "=== FILE: hilfsgutachten-sut.md ===\nDer Rechtsweg ist eröffnet.\n"
    )
    out = bp.split_multi_response(text, DELIVERABLES)
    assert set(out) == set(DELIVERABLES)
    assert out["schriftsatz-sut.md"] == "An das Gericht\n"
    assert out["hilfsgutachten-sut.md"] == "Der Rechtsweg ist eröffnet.\n"


def test_omitted_deliverable_is_absent_not_empty() -> None:
    text = "=== FILE: schriftsatz-sut.md ===\nNur ein Dokument\n"
    out = bp.split_multi_response(text, DELIVERABLES)
    assert set(out) == {"schriftsatz-sut.md"}


def test_unknown_and_repeated_markers_are_ignored() -> None:
    text = (
        "=== FILE: schriftsatz-sut.md ===\nErste Fassung\n"
        "=== FILE: notizen.md ===\nNicht deklariert\n"
        "=== FILE: schriftsatz-sut.md ===\nZweite Fassung\n"
    )
    out = bp.split_multi_response(text, DELIVERABLES)
    assert set(out) == {"schriftsatz-sut.md"}
    assert out["schriftsatz-sut.md"] == "Erste Fassung\n"


def test_response_without_markers_yields_nothing() -> None:
    assert bp.split_multi_response("Ein Fließtext ohne Marker", DELIVERABLES) == {}


def test_empty_section_is_not_written() -> None:
    text = "=== FILE: schriftsatz-sut.md ===\n\n=== FILE: hilfsgutachten-sut.md ===\nInhalt\n"
    out = bp.split_multi_response(text, DELIVERABLES)
    assert set(out) == {"hilfsgutachten-sut.md"}


def test_marker_tolerates_quotes_and_backticks() -> None:
    text = '=== FILE: `schriftsatz-sut.md` ===\nA\n=== FILE: "hilfsgutachten-sut.md" ===\nB\n'
    out = bp.split_multi_response(text, DELIVERABLES)
    assert set(out) == {"schriftsatz-sut.md", "hilfsgutachten-sut.md"}


@pytest.mark.parametrize("count", [2, 3])
def test_multi_prompt_lists_every_deliverable(tmp_path: pathlib.Path, count: int) -> None:
    task_dir = tmp_path / "task"
    (task_dir / "documents").mkdir(parents=True)
    (task_dir / "documents" / "sachverhalt.md").write_text("Sachverhalt", encoding="utf-8")
    names = DELIVERABLES[:count]
    prompt, _ = bp.render_multi_prompt(
        task_id="t", task={"title": "T", "instructions": "I"}, task_dir=task_dir, deliverables=names
    )
    for name in names:
        assert f"- {name}" in prompt
    assert "=== FILE: <filename> ===" in prompt


def test_single_deliverable_template_is_untouched() -> None:
    single = bp.PROMPT_TEMPLATE.read_text(encoding="utf-8")
    assert "{deliverable}" in single
    assert "=== FILE:" not in single
