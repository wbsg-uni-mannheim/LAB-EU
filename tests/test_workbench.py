from __future__ import annotations

import datetime as dt
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

from scripts.baseline_prompt import render_prompt
from workbench import create_app
from workbench.core import (
    REPO_ROOT,
    create_manual_run,
    create_study,
    default_study_system_prompt,
    discover_tasks,
    end_study_early,
    get_task,
    list_studies,
    save_study_answer,
    _unrelated_status_paths,
)


FRENCH_TASK_ID = "fr/droit-des-obligations/cas-pratique/cas-pratique-crfpa-2024-alphadot"


class WorkbenchCoreTests(unittest.TestCase):
    def test_git_readiness_ignores_other_untracked_runs_only(self):
        target = "runs/studies/current/"
        entries = [
            ("??", "runs/studies/current/manifest.json"),
            ("??", "runs/baseline-old/manifest.json"),
            (" M", "README.md"),
            ("A ", "runs/staged-run/manifest.json"),
        ]
        self.assertEqual(
            _unrelated_status_paths(entries, target),
            ["README.md", "runs/staged-run/manifest.json"],
        )

    def test_discovers_german_and_french_tasks(self):
        records = discover_tasks()
        languages = {record.language for record in records}
        self.assertGreater(len(records), 100)
        self.assertIn("de", languages)
        self.assertIn("fr", languages)

    def test_shared_prompt_is_french_and_excludes_reference_solution(self):
        record = get_task(FRENCH_TASK_ID)
        prompt, truncated = render_prompt(
            record.task_id,
            record.task,
            record.task_dir,
            record.deliverable,
            today=dt.date(2026, 7, 14),
        )
        self.assertFalse(truncated)
        self.assertIn("Vous êtes avocat", prompt)
        self.assertIn("2026-07-14", prompt)
        self.assertNotIn("Proposition de solution", prompt)

    def test_manual_run_matches_judge_layout(self):
        record = get_task(FRENCH_TASK_ID)
        with tempfile.TemporaryDirectory() as directory:
            result = create_manual_run(record, "# Consultation\n\nRéponse", "Alice", "Local", "Modèle", pathlib.Path(directory))
            run_dir = pathlib.Path(result["run_dir"])
            manifest = json.loads((run_dir / "manifest.json").read_text())
            metadata_path = next((run_dir / "tasks").glob("*/metadata.json"))
            metadata = json.loads(metadata_path.read_text())
            submission = metadata_path.parent / "submission" / "consultation.md"
            self.assertEqual(manifest["harness"], "manual-copy-paste")
            self.assertEqual(metadata["task_id"], FRENCH_TASK_ID)
            self.assertTrue(submission.is_file())
            dry_run = subprocess.run(
                [sys.executable, "scripts/judge_run.py", str(run_dir), "--dry-run"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertIn("evaluation.run", dry_run.stdout)

    def test_study_stores_configuration_and_advances_case(self):
        with tempfile.TemporaryDirectory() as directory:
            studies_root = pathlib.Path(directory)
            study = create_study(
                name="French model study",
                model="Legal-1",
                language="fr",
                system_prompt="System prompt exact",
                reviewer="Alice",
                provider="Internal",
                capabilities={
                    "agent": False,
                    "single_llm": True,
                    "web_search": True,
                    "databases": False,
                    "other_tools": False,
                },
                judge_ready_only=False,
                studies_root=studies_root,
            )
            self.assertEqual(study["n_tasks"], 1)
            self.assertEqual(study["n_completed"], 0)
            self.assertEqual(study["system_prompt"], "System prompt exact")
            self.assertEqual(study["current_task"]["task_id"], FRENCH_TASK_ID)
            combined = study["current_task"]["combined_prompt"]
            self.assertIn("## SYSTEM INSTRUCTIONS", combined)
            self.assertIn("System prompt exact", combined)
            self.assertIn("## CURRENT LAB-EU TASK", combined)
            self.assertIn("Vous êtes avocat", combined)

            completed = save_study_answer(
                study_id=study["study_id"],
                task_id=FRENCH_TASK_ID,
                response="# Consultation\n\nRéponse",
                confidentiality_confirmed=True,
                studies_root=studies_root,
            )
            self.assertTrue(completed["complete"])
            self.assertEqual(completed["n_completed"], 1)
            self.assertIsNone(completed["judge_command"])
            manifest = json.loads((pathlib.Path(completed["run_dir"]) / "manifest.json").read_text())
            self.assertEqual(manifest["capabilities"]["web_search"], True)
            self.assertEqual(manifest["system_prompt_sha256"], completed["system_prompt_sha256"])
            self.assertEqual(len(list_studies(studies_root)), 1)
            metadata_path = next((pathlib.Path(completed["run_dir"]) / "tasks").glob("*/metadata.json"))
            metadata = json.loads(metadata_path.read_text())
            self.assertTrue((metadata_path.parent / "combined_prompt.md").is_file())
            self.assertIn("combined_prompt_sha256", metadata)
            dry_run = subprocess.run(
                [sys.executable, "scripts/judge_run.py", completed["run_dir"], "--dry-run"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
            self.assertIn("evaluation.run", dry_run.stdout)

    def test_study_requires_one_execution_type(self):
        with tempfile.TemporaryDirectory() as directory:
            studies_root = pathlib.Path(directory)
            with self.assertRaises(ValueError):
                create_study(
                    name="Invalid",
                    model="Model",
                    language="fr",
                    system_prompt="Prompt",
                    reviewer="",
                    provider="",
                    capabilities={"agent": True, "single_llm": True},
                    judge_ready_only=True,
                    studies_root=studies_root,
                )
            self.assertEqual(list(studies_root.iterdir()), [])

    def test_unknown_system_stores_unknown_without_guessed_capabilities(self):
        with tempfile.TemporaryDirectory() as directory:
            study = create_study(
                name="Unknown system",
                model="Proprietary",
                language="fr",
                system_prompt=default_study_system_prompt(),
                reviewer="Alice",
                provider="Vendor",
                capabilities={
                    "agent": True,
                    "single_llm": False,
                    "web_search": True,
                    "databases": True,
                    "other_tools": True,
                    "system_unknown": True,
                },
                judge_ready_only=False,
                studies_root=pathlib.Path(directory),
            )
            self.assertTrue(study["capabilities"]["system_unknown"])
            self.assertFalse(study["capabilities"]["agent"])
            self.assertFalse(study["capabilities"]["web_search"])

    def test_study_can_be_submitted_early_after_one_answer(self):
        with tempfile.TemporaryDirectory() as directory:
            studies_root = pathlib.Path(directory)
            study = create_study(
                name="Early German study",
                model="Legal-1",
                language="de",
                system_prompt=default_study_system_prompt(),
                reviewer="Alice",
                provider="Internal",
                capabilities={"agent": False, "single_llm": True},
                judge_ready_only=True,
                studies_root=studies_root,
            )
            self.assertGreater(study["n_tasks"], 1)
            first_task_id = study["current_task"]["task_id"]
            advanced = save_study_answer(
                study_id=study["study_id"],
                task_id=first_task_id,
                response="# Antwort",
                confidentiality_confirmed=True,
                studies_root=studies_root,
            )
            self.assertFalse(advanced["complete"])

            ended = end_study_early(study["study_id"], True, studies_root)
            self.assertTrue(ended["complete"])
            self.assertTrue(ended["ended_early"])
            self.assertEqual(ended["n_completed"], 1)
            self.assertEqual(ended["n_remaining"], ended["n_tasks"] - 1)
            self.assertIsNone(ended["current_task"])
            self.assertIsNotNone(ended["judge_command"])
            manifest = json.loads((pathlib.Path(ended["run_dir"]) / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "ended_early")
            self.assertEqual(manifest["n_skipped"], ended["n_remaining"])
            self.assertEqual(len(manifest["skipped_task_ids"]), ended["n_remaining"])

    def test_study_cannot_be_submitted_early_without_an_answer(self):
        with tempfile.TemporaryDirectory() as directory:
            studies_root = pathlib.Path(directory)
            study = create_study(
                name="Empty early study",
                model="Legal-1",
                language="de",
                system_prompt=default_study_system_prompt(),
                reviewer="Alice",
                provider="Internal",
                capabilities={"agent": False, "single_llm": True},
                judge_ready_only=True,
                studies_root=studies_root,
            )
            with self.assertRaises(ValueError):
                end_study_early(study["study_id"], True, studies_root)


class WorkbenchAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        temp_root = pathlib.Path(self.temp.name)
        self.app = create_app(
            {
                "TESTING": True,
                "WORKBENCH_TOKEN": "test-token",
                "RUNS_ROOT": temp_root / "manual",
                "STUDIES_ROOT": temp_root / "studies",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_task_api_does_not_expose_evals(self):
        response = self.client.get("/api/task", query_string={"task_id": FRENCH_TASK_ID})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["documents"])
        self.assertNotIn("rubric", payload)
        self.assertNotIn("solution", payload)

    def test_index_contains_lawyer_facing_study_guide(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Vier Schritte", page)
        self.assertIn("Studie einmalig einrichten", page)
        self.assertIn("Fälle nacheinander bearbeiten", page)
        self.assertIn("Bei diesem System nicht bekannt", page)
        self.assertIn("You are solving LAB-EU legal benchmark tasks", page)
        self.assertIn("Gesamten Prompt kopieren", page)
        self.assertNotIn('id="copy-system-prompt"', page)
        self.assertNotIn('id="copy-case-prompt"', page)

    def test_save_requires_confidentiality_confirmation(self):
        response = self.client.post(
            "/api/runs",
            headers={"X-Workbench-Token": "test-token"},
            json={"task_id": FRENCH_TASK_ID, "response": "Réponse"},
        )
        self.assertEqual(response.status_code, 400)

    def test_save_creates_manual_run(self):
        response = self.client.post(
            "/api/runs",
            headers={"X-Workbench-Token": "test-token"},
            json={
                "task_id": FRENCH_TASK_ID,
                "response": "# Consultation\n\nRéponse",
                "reviewer": "Alice",
                "provider": "Interne",
                "model": "Legal-1",
                "confidentiality_confirmed": True,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(pathlib.Path(response.get_json()["run_dir"]).is_dir())

    def test_study_api_starts_and_advances_study(self):
        started = self.client.post(
            "/api/studies",
            headers={"X-Workbench-Token": "test-token"},
            json={
                "name": "French API study",
                "model": "Legal-1",
                "language": "fr",
                "system_prompt": "Stored system prompt",
                "reviewer": "Alice",
                "provider": "Internal",
                "judge_ready_only": False,
                "capabilities": {
                    "agent": False,
                    "single_llm": True,
                    "web_search": False,
                    "databases": True,
                    "other_tools": False,
                },
            },
        )
        self.assertEqual(started.status_code, 201)
        study = started.get_json()
        self.assertEqual(study["current_task"]["task_id"], FRENCH_TASK_ID)
        self.assertEqual(study["system_prompt"], "Stored system prompt")

        advanced = self.client.post(
            f"/api/studies/{study['study_id']}/answers",
            headers={"X-Workbench-Token": "test-token"},
            json={
                "task_id": FRENCH_TASK_ID,
                "response": "# Consultation\n\nRéponse",
                "confidentiality_confirmed": True,
            },
        )
        self.assertEqual(advanced.status_code, 200)
        self.assertTrue(advanced.get_json()["complete"])
        studies = self.client.get("/api/studies").get_json()["studies"]
        self.assertEqual(studies[0]["n_completed"], 1)


if __name__ == "__main__":
    unittest.main()
