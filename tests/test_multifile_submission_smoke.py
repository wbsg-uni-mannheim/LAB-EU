"""Offline smoke test for single- and multi-file submissions (plan Phase F).

Covers the evaluation-side assembly for a complete and a deliberately
incomplete multi-file submission. The full end-to-end smoke including judge
calls runs against the pilot rubrics once they exist.
"""

from __future__ import annotations

import pathlib
import tempfile
import unittest

from evaluation.run import load_agent_output


def criterion(deliverables: list[str] | None = None) -> dict:
    base = {
        "id": "C-001",
        "title": "Testkriterium",
        "match_criteria": "ERFÜLLT, wenn X. NICHT ERFÜLLT, wenn Y.",
    }
    if deliverables is not None:
        base["deliverables"] = deliverables
    return base


class MultiFileSubmissionSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name)

    def complete_submission(self) -> pathlib.Path:
        submission = self.root / "complete"
        submission.mkdir()
        (submission / "klageerwiderung-sut.md").write_text("KLAGEERWIDERUNG", encoding="utf-8")
        (submission / "mandantenschreiben-sut.md").write_text("MANDANTENSCHREIBEN", encoding="utf-8")
        (submission / "hilfsgutachten-sut.md").write_text("HILFSGUTACHTEN", encoding="utf-8")
        return submission

    def incomplete_submission(self) -> pathlib.Path:
        submission = self.root / "incomplete"
        submission.mkdir()
        (submission / "klageerwiderung-sut.md").write_text("KLAGEERWIDERUNG", encoding="utf-8")
        return submission

    def test_complete_submission_restricted_criterion_sees_only_its_file(self) -> None:
        output = load_agent_output(
            self.complete_submission(), criterion(["klageerwiderung-sut.md"])
        )
        self.assertIn("## klageerwiderung-sut.md", output)
        self.assertIn("KLAGEERWIDERUNG", output)
        self.assertNotIn("HILFSGUTACHTEN", output)

    def test_complete_submission_or_list_sees_every_permitted_file(self) -> None:
        output = load_agent_output(
            self.complete_submission(),
            criterion(["mandantenschreiben-sut.md", "hilfsgutachten-sut.md"]),
        )
        self.assertIn("MANDANTENSCHREIBEN", output)
        self.assertIn("HILFSGUTACHTEN", output)
        self.assertNotIn("KLAGEERWIDERUNG", output)

    def test_incomplete_submission_missing_file_yields_file_not_found(self) -> None:
        output = load_agent_output(
            self.incomplete_submission(), criterion(["hilfsgutachten-sut.md"])
        )
        self.assertIn("## hilfsgutachten-sut.md", output)
        self.assertIn("(File not found)", output)

    def test_incomplete_submission_or_list_still_sees_present_file(self) -> None:
        output = load_agent_output(
            self.incomplete_submission(),
            criterion(["klageerwiderung-sut.md", "hilfsgutachten-sut.md"]),
        )
        self.assertIn("KLAGEERWIDERUNG", output)
        self.assertIn("(File not found)", output)

    def test_unrestricted_criterion_sees_all_files_of_the_submission(self) -> None:
        output = load_agent_output(self.complete_submission(), criterion())
        for marker in ("KLAGEERWIDERUNG", "MANDANTENSCHREIBEN", "HILFSGUTACHTEN"):
            self.assertIn(marker, output)

    def test_single_file_submission_path_keeps_working(self) -> None:
        answer = self.root / "answer.md"
        answer.write_text("EINZELDATEI", encoding="utf-8")
        output = load_agent_output(answer, criterion(["answer.md"]))
        self.assertIn("## answer.md", output)
        self.assertIn("EINZELDATEI", output)


if __name__ == "__main__":
    unittest.main()
