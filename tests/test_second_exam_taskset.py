import json
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
FIRST_EXAM_MARKER = "Ersten Juristischen"
SECOND_EXAM_MARKERS = ("Zweiten Juristischen", "Zweiten Juristische", "Referendar")


def load_taskset(path: pathlib.Path) -> list[dict[str, str]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


class SecondExamTasksetTest(unittest.TestCase):
    def test_taskset_contains_fifteen_unique_second_exam_cases(self):
        second_exam = load_taskset(REPO_ROOT / "tasksets/de-second-exam-15.jsonl")

        self.assertEqual(len(second_exam), 15)
        self.assertEqual(len({row["task_id"] for row in second_exam}), 15)

    def test_every_selected_case_is_source_labeled_for_the_second_exam(self):
        rows = load_taskset(REPO_ROOT / "tasksets/de-second-exam-15.jsonl")

        for row in rows:
            task_dir = REPO_ROOT / row["task_dir"]
            task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
            title = task["title"]

            self.assertNotIn(FIRST_EXAM_MARKER, title, row["task_id"])
            self.assertTrue(
                any(marker in title for marker in SECOND_EXAM_MARKERS),
                f"Missing second-exam source label: {row['task_id']} ({title})",
            )
            self.assertTrue((task_dir / "documents").is_dir())
            self.assertTrue(any((task_dir / "documents").iterdir()))
            self.assertTrue((task_dir / "evals").is_dir())
            self.assertTrue(any((task_dir / "evals").iterdir()))

    def test_known_first_exam_misclassification_is_excluded(self):
        selected = {
            row["task_id"]
            for row in load_taskset(REPO_ROOT / "tasksets/de-second-exam-15.jsonl")
        }

        self.assertNotIn(
            "de/oeffentliches-recht/referendariat/KahlPracht-VBlBW-2024",
            selected,
        )


if __name__ == "__main__":
    unittest.main()
