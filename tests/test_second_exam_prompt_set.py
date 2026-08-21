from __future__ import annotations

import pathlib
import tempfile
import unittest
from unittest import mock

import scripts.generate_rubric as generate_rubric
from scripts.generate_rubric import (
    DELIVERABLE_DOC_TYPES,
    PROMPTS_DIR,
    criterion_gold_output,
    resolve_prompt_path,
    solution_texts_by_name,
    validate_criteria,
    validate_deliverable_profiles,
)

SECOND_EXAM_DIR = PROMPTS_DIR / "second-exam"


class PromptSetResolutionTest(unittest.TestCase):
    def test_without_prompt_set_resolves_to_base(self) -> None:
        with mock.patch.object(generate_rubric, "PROMPT_SET_DIR", None):
            path = resolve_prompt_path("atomize_solution.user.txt")
        self.assertEqual(path, PROMPTS_DIR / "atomize_solution.user.txt")

    def test_override_wins_and_missing_files_fall_back(self) -> None:
        with mock.patch.object(generate_rubric, "PROMPT_SET_DIR", SECOND_EXAM_DIR):
            override = resolve_prompt_path("atomize_solution.user.txt")
            fallback = resolve_prompt_path("atomize_solution.system.txt")
            roles = resolve_prompt_path("roles/doctrine.txt")
        self.assertEqual(override, SECOND_EXAM_DIR / "atomize_solution.user.txt")
        self.assertEqual(fallback, PROMPTS_DIR / "atomize_solution.system.txt")
        self.assertEqual(roles, PROMPTS_DIR / "roles/doctrine.txt")

    def test_second_exam_set_ships_expected_overrides(self) -> None:
        expected = [
            "classify_deliverables.system.txt",
            "classify_deliverables.user.txt",
            "atomize_solution.user.txt",
            "generate_candidate_criteria.user.txt",
            "prune_rubric.user.txt",
            "refine_rubric.user.txt",
            "extract_outline.user.txt",
        ]
        for name in expected:
            self.assertTrue((SECOND_EXAM_DIR / name).exists(), name)

    def test_classify_prompt_names_every_doc_type(self) -> None:
        text = (SECOND_EXAM_DIR / "classify_deliverables.user.txt").read_text(encoding="utf-8")
        for doc_type in DELIVERABLE_DOC_TYPES:
            self.assertIn(f'"{doc_type}"', text)


class ValidateCriteriaDeliverablesTest(unittest.TestCase):
    def criterion(self, deliverables: list[str] | None) -> dict:
        base = {
            "id": "C-001",
            "criticality": "must_pass",
            "match_criteria": "ERFÜLLT, wenn X. NICHT ERFÜLLT, wenn Y.",
        }
        if deliverables is not None:
            base["deliverables"] = deliverables
        return base

    def test_unknown_deliverable_is_an_error(self) -> None:
        errors = validate_criteria(
            [self.criterion(["urteil-sut.md", "tatbestand.md"])],
            allowed_deliverables=["urteil-sut.md", "hilfsgutachten-sut.md"],
        )
        self.assertTrue(any("tatbestand.md" in error for error in errors))

    def test_known_deliverables_pass(self) -> None:
        errors = validate_criteria(
            [self.criterion(["urteil-sut.md"])],
            allowed_deliverables=["urteil-sut.md", "hilfsgutachten-sut.md"],
        )
        self.assertEqual(errors, [])

    def test_no_allowed_list_skips_the_check(self) -> None:
        errors = validate_criteria([self.criterion(["anything.md"])])
        self.assertEqual(errors, [])


class ValidateDeliverableProfilesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        self.files = []
        for name in ("urteil-sut.md", "hilfsgutachten-sut.md"):
            path = root / name
            path.write_text("x", encoding="utf-8")
            self.files.append(path)
        self.deliverables = ["urteil-sut.md", "hilfsgutachten-sut.md"]

    def profiles(self) -> list[dict]:
        return [
            {"file": "urteil-sut.md", "doc_type": "gerichtliche_entscheidung"},
            {"file": "hilfsgutachten-sut.md", "doc_type": "gutachten"},
        ]

    def test_valid_profiles_pass(self) -> None:
        errors = validate_deliverable_profiles(self.profiles(), self.deliverables, self.files)
        self.assertEqual(errors, [])

    def test_missing_profile_is_an_error(self) -> None:
        errors = validate_deliverable_profiles(
            self.profiles()[:1], self.deliverables, self.files
        )
        self.assertTrue(any("hilfsgutachten-sut.md" in error for error in errors))

    def test_invalid_doc_type_is_an_error(self) -> None:
        broken = self.profiles()
        broken[0]["doc_type"] = "urteilsstil"
        errors = validate_deliverable_profiles(broken, self.deliverables, self.files)
        self.assertTrue(any("urteilsstil" in error for error in errors))

    def test_profile_without_gold_solution_file_is_an_error(self) -> None:
        errors = validate_deliverable_profiles(
            self.profiles(), self.deliverables, self.files[:1]
        )
        self.assertTrue(any("no matching gold solution" in error for error in errors))

    def test_duplicate_profiles_are_an_error(self) -> None:
        doubled = self.profiles() + [self.profiles()[0]]
        errors = validate_deliverable_profiles(doubled, self.deliverables, self.files)
        self.assertTrue(any("repeat" in error for error in errors))


class CriterionGoldOutputTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        (root / "urteil-sut.md").write_text("URTEILSTEXT", encoding="utf-8")
        (root / "hilfsgutachten-sut.md").write_text("GUTACHTENTEXT", encoding="utf-8")
        self.files = [root / "urteil-sut.md", root / "hilfsgutachten-sut.md"]
        self.by_name = solution_texts_by_name(self.files)
        self.full = "## urteil-sut.md\nURTEILSTEXT\n\n## hilfsgutachten-sut.md\nGUTACHTENTEXT"

    def test_restricts_to_named_deliverables(self) -> None:
        output = criterion_gold_output(
            {"deliverables": ["urteil-sut.md"]}, self.by_name, self.full
        )
        self.assertIn("URTEILSTEXT", output)
        self.assertNotIn("GUTACHTENTEXT", output)

    def test_missing_file_yields_file_not_found(self) -> None:
        output = criterion_gold_output(
            {"deliverables": ["fehlt.md"]}, self.by_name, self.full
        )
        self.assertIn("(File not found)", output)

    def test_no_deliverables_sees_full_solution(self) -> None:
        output = criterion_gold_output({}, self.by_name, self.full)
        self.assertEqual(output, self.full)

    def test_or_semantics_include_every_listed_file(self) -> None:
        output = criterion_gold_output(
            {"deliverables": ["urteil-sut.md", "hilfsgutachten-sut.md"]},
            self.by_name,
            self.full,
        )
        self.assertIn("URTEILSTEXT", output)
        self.assertIn("GUTACHTENTEXT", output)


if __name__ == "__main__":
    unittest.main()
