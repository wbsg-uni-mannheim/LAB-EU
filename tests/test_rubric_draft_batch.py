from __future__ import annotations

import json
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts import generate_rubric as gr
from scripts import generate_rubric_drafts_batch as batch


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PILOT_TASKSET = REPO_ROOT / "tasksets/de-core-10-batch-pilot.jsonl"


class RubricDraftBatchTests(unittest.TestCase):
    def test_canonical_request_builder_matches_responses_shape(self):
        key, body = gr.build_api_request(
            model="gpt-5.6-sol",
            system="system",
            user="user",
            reasoning_effort="high",
        )
        self.assertEqual(len(key), 24)
        self.assertEqual(body["model"], "gpt-5.6-sol")
        self.assertEqual(body["instructions"], "system")
        self.assertEqual(body["input"], "user")
        self.assertEqual(body["reasoning"], {"effort": "high"})
        self.assertEqual(body["text"], {"format": {"type": "json_object"}})

    def test_batch_body_parser_enforces_required_keys(self):
        body = {
            "status": "completed",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": '{"language":"de","criteria":[]}'},
                    ],
                }
            ],
        }
        self.assertEqual(
            batch.parse_batch_body(body, {"language", "criteria"}),
            {"language": "de", "criteria": []},
        )
        self.assertIsNone(batch.parse_batch_body(body, {"language", "missing"}))

    def test_pruning_coverage_requires_disposition_for_every_core_atom(self):
        atoms = {
            "atoms": [
                {"id": "A-001", "expectation": "core"},
                {"id": "A-002", "expectation": "core"},
                {"id": "A-003", "expectation": "bonus"},
            ]
        }
        pruned = {
            "criteria": [{"derived_from_atoms": ["A-001"]}],
            "coverage_audit": {
                "uncovered_core_atoms": [
                    {"id": "A-002", "reason": "Aggregate result already represented."}
                ]
            },
        }
        self.assertEqual(gr.validate_pruning_coverage(pruned, atoms), [])
        pruned["coverage_audit"]["uncovered_core_atoms"] = []
        self.assertIn(
            "Core atoms lack a pruning disposition: A-002",
            gr.validate_pruning_coverage(pruned, atoms),
        )

    def test_pruning_coverage_normalizes_atoms_already_covered_by_criteria(self):
        pruned = {
            "criteria": [{"derived_from_atoms": ["A-001"]}],
            "coverage_audit": {
                "uncovered_core_atoms": [
                    {"id": "A-001", "reason": "Contradictory model audit."},
                    {"id": "A-002", "reason": "Intentionally omitted."},
                ]
            },
        }

        warnings = gr.normalize_pruning_coverage_audit(pruned)

        self.assertEqual(
            pruned["coverage_audit"]["uncovered_core_atoms"],
            [{"id": "A-002", "reason": "Intentionally omitted."}],
        )
        self.assertEqual(len(warnings), 1)
        self.assertIn("A-001", warnings[0])

    def test_pruner_prompt_limits_scope_compliance_and_audits_long_criteria(self):
        prompt = (REPO_ROOT / "prompts/rubric_generation/prune_rubric.user.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("at most one scope-compliance criterion per deliverable", prompt)
        self.assertIn("roughly 900 characters", prompt)
        self.assertIn("coverage_audit.uncovered_core_atoms", prompt)

    def test_harvest_writes_the_normal_generator_cache_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = pathlib.Path(tmp)
            mapping = {
                "atom-1": {
                    "task_dir": str(task_dir),
                    "label": "atomize_solution",
                    "step": "atomize_solution",
                    "key": "abc123",
                    "required_keys": ["atoms", "language"],
                }
            }
            content = json.dumps(
                {
                    "custom_id": "atom-1",
                    "response": {
                        "status_code": 200,
                        "body": {
                            "status": "completed",
                            "output": [
                                {
                                    "type": "message",
                                    "content": [
                                        {
                                            "type": "output_text",
                                            "text": '{"atoms":[],"language":"de"}',
                                        }
                                    ],
                                }
                            ],
                            "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
                        },
                    },
                    "error": None,
                }
            )
            usage: dict[str, dict] = {}
            ok, bad = batch.harvest_output(content, mapping, usage)
            self.assertEqual((ok, bad), (1, 0))
            cached = gr.cache_read(task_dir / "evals/.rubric-cache", "atomize_solution", "abc123")
            self.assertEqual(cached["parsed"], {"atoms": [], "language": "de"})
            self.assertEqual(usage["atom-1"]["usage"]["total_tokens"], 15)

    def test_candidate_phase_creates_three_role_requests(self):
        with mock.patch.object(
            batch,
            "task_context",
            return_value={"task": {"title": "T"}, "files": [], "warnings": [], "bundle": {}},
        ), mock.patch.object(batch, "cached_parsed", return_value={"atoms": []}), mock.patch.object(
            gr, "prompt_pair", return_value=("system", "user")
        ), mock.patch.object(gr, "read_prompt_template", return_value="role"):
            specs = batch.candidate_specs(pathlib.Path("/tmp/task"), "gpt-5.6-sol", "high")
        self.assertEqual(len(specs), 3)
        self.assertEqual(
            [spec["label"] for spec in specs],
            ["candidates/doctrine", "candidates/fact_grounding", "candidates/adversary"],
        )

    def test_batch_cost_uses_cached_and_cache_write_rates(self):
        usage = {
            "input_tokens": 100_000,
            "output_tokens": 10_000,
            "input_tokens_details": {
                "cached_tokens": 20_000,
                "cache_write_tokens": 30_000,
            },
        }
        expected = 0.05 * 2.50 + 0.02 * 0.25 + 0.03 * 3.125 + 0.01 * 15.00
        self.assertAlmostEqual(batch.estimated_batch_cost(usage), expected)

    def test_pilot_taskset_has_ten_first_exam_cases_across_all_areas(self):
        rows = [json.loads(line) for line in PILOT_TASKSET.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), 10)
        counts = {
            area: sum(f"/{area}/" in row["task_dir"] for row in rows)
            for area in ("oeffentliches-recht", "strafrecht", "zivilrecht")
        }
        self.assertEqual(counts, {"oeffentliches-recht": 4, "strafrecht": 3, "zivilrecht": 3})
        self.assertTrue(all("/referendariat/" not in row["task_dir"] for row in rows))


if __name__ == "__main__":
    unittest.main()
