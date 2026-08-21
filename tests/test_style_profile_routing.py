from __future__ import annotations

import json
import pathlib
import tempfile
import unittest

from evaluation.run import (
    PROMPTS_DIR,
    combined_content_style_prompt,
    criterion_style_doc_types,
    ensure_style_profiles_supported,
    load_style_profiles,
    render_style_standards,
)

TASK = {"title": "Testfall", "instructions": "Bearbeitervermerk."}
PROFILES = {
    "urteil-sut.md": "gerichtliche_entscheidung",
    "hilfsgutachten-sut.md": "gutachten",
}


def criterion(deliverables: list[str] | None = None) -> dict:
    base = {
        "id": "C-001",
        "title": "Testkriterium",
        "match_criteria": "ERFÜLLT, wenn X. NICHT ERFÜLLT, wenn Y.",
    }
    if deliverables is not None:
        base["deliverables"] = deliverables
    return base


class LoadStyleProfilesTest(unittest.TestCase):
    def write_rubric(self, payload: dict) -> pathlib.Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = pathlib.Path(tmp.name) / "rubric.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_reads_frozen_profiles(self) -> None:
        path = self.write_rubric(
            {
                "criteria": [],
                "deliverable_profiles": [
                    {"file": "urteil-sut.md", "doc_type": "gerichtliche_entscheidung"},
                    {"file": "hilfsgutachten-sut.md", "doc_type": "gutachten"},
                ],
            }
        )
        self.assertEqual(load_style_profiles(path), PROFILES)

    def test_rubric_without_profiles_returns_none(self) -> None:
        path = self.write_rubric({"criteria": []})
        self.assertIsNone(load_style_profiles(path))


class CriterionStyleDocTypesTest(unittest.TestCase):
    def test_single_file_resolves_its_type(self) -> None:
        self.assertEqual(
            criterion_style_doc_types(criterion(["urteil-sut.md"]), PROFILES),
            ["gerichtliche_entscheidung"],
        )

    def test_multiple_files_keep_order_and_dedupe(self) -> None:
        types = criterion_style_doc_types(
            criterion(["urteil-sut.md", "hilfsgutachten-sut.md"]), PROFILES
        )
        self.assertEqual(types, ["gerichtliche_entscheidung", "gutachten"])

    def test_no_deliverables_falls_back_to_all_profiles(self) -> None:
        types = criterion_style_doc_types(criterion(), PROFILES)
        self.assertEqual(sorted(types), ["gerichtliche_entscheidung", "gutachten"])

    def test_no_profiles_means_no_types(self) -> None:
        self.assertEqual(criterion_style_doc_types(criterion(["urteil-sut.md"]), None), [])


class CombinedPromptRoutingTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.task_dir = pathlib.Path(tmp.name)

    def test_without_profiles_stays_byte_identical_to_base_template(self) -> None:
        expected = (PROMPTS_DIR / "combined_content_style_criterion.txt").read_text(
            encoding="utf-8"
        ).format(
            task_title="Testfall",
            task_instructions="Bearbeitervermerk.",
            criterion_sources="(No source documents attached to this criterion.)",
            agent_output="ANTWORT",
            criterion_title="Testkriterium",
            match_criteria="ERFÜLLT, wenn X. NICHT ERFÜLLT, wenn Y.",
        )
        prompt = combined_content_style_prompt(
            TASK, self.task_dir, "ANTWORT", criterion(["urteil-sut.md"])
        )
        self.assertEqual(prompt, expected)

    def test_with_profiles_uses_second_exam_template_and_profile_rules(self) -> None:
        prompt = combined_content_style_prompt(
            TASK, self.task_dir, "ANTWORT", criterion(["urteil-sut.md"]), PROFILES
        )
        self.assertIn("Urteilsstil", prompt)
        self.assertIn("Style standard for urteil-sut.md", prompt)
        self.assertNotIn("Style standard for hilfsgutachten-sut.md", prompt)
        self.assertNotIn("{style_standards}", prompt)
        # The JSON response schema must survive .format() with braces intact.
        self.assertIn('"method_checks"', prompt)

    def test_mixed_locations_render_both_standards_and_the_mixing_rule(self) -> None:
        prompt = combined_content_style_prompt(
            TASK,
            self.task_dir,
            "ANTWORT",
            criterion(["urteil-sut.md", "hilfsgutachten-sut.md"]),
            PROFILES,
        )
        self.assertIn("Urteilsstil", prompt)
        self.assertIn("Gutachtenstil", prompt)
        self.assertIn("never mix standards across files", prompt)

    def test_every_style_profile_file_exists(self) -> None:
        for doc_type in (
            "gutachten",
            "gerichtliche_entscheidung",
            "anwaltlicher_schriftsatz",
            "mandanten_oder_behoerdenschreiben",
        ):
            path = PROMPTS_DIR / "style_profiles" / f"{doc_type}.txt"
            self.assertTrue(path.exists(), path)
            for check in (
                "criterion_specific_premise",
                "explicit_fact_link",
                "completed_path",
            ):
                self.assertIn(check, path.read_text(encoding="utf-8"), doc_type)


class SeparateStyleCallGuardTest(unittest.TestCase):
    def test_non_gutachten_profiles_reject_separate_style_calls(self) -> None:
        with self.assertRaises(SystemExit):
            ensure_style_profiles_supported(PROFILES, combine_content_and_style=False)

    def test_gutachten_only_profiles_allow_separate_style_calls(self) -> None:
        ensure_style_profiles_supported(
            {"hilfsgutachten-sut.md": "gutachten"}, combine_content_and_style=False
        )

    def test_combined_path_allows_all_profiles(self) -> None:
        ensure_style_profiles_supported(PROFILES, combine_content_and_style=True)

    def test_no_profiles_is_always_fine(self) -> None:
        ensure_style_profiles_supported(None, combine_content_and_style=False)


class RenderStyleStandardsTest(unittest.TestCase):
    def test_files_of_same_type_share_one_block(self) -> None:
        profiles = {
            "klageerwiderung-sut.md": "anwaltlicher_schriftsatz",
            "schriftsatz-sut.md": "anwaltlicher_schriftsatz",
        }
        rendered = render_style_standards(
            criterion(["klageerwiderung-sut.md", "schriftsatz-sut.md"]), profiles
        )
        self.assertIn(
            "Style standard for klageerwiderung-sut.md, schriftsatz-sut.md", rendered
        )
        self.assertNotIn("never mix standards", rendered)


if __name__ == "__main__":
    unittest.main()
