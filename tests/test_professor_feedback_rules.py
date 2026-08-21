from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from evaluation.run import (
    JudgeSpec,
    _judge_call_responses,
    aggregate_votes,
    assemble_scores,
    combined_content_style_prompt,
    evaluate,
    finalize_committee_tiebreaker,
    finalize_committee_rounds,
    is_style_eligible_criterion,
    load_judge_committee,
    needs_committee_recheck,
    needs_committee_tiebreaker,
    normalize_combined_judge_result,
    normalize_judge_result,
    prompt_cache_key_for_criterion,
    responses_input_with_cache_breakpoint,
    select_criteria,
    usage_summary,
)
from scripts.generate_rubric import DEFAULT_MODEL, criticality_distribution_warnings
from scripts.export_review_md import build_markdown
from scripts.run_negative_rubric_calibration import (
    build_metrics,
    generate_mutants,
    validate_mutants,
)


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMITTEE = REPO_ROOT / "configs/judge-committee-professor-pilot.json"
SOL_COMMITTEE = REPO_ROOT / "configs/judge-committee-sol-pilot.json"
CALIBRATION_COMMITTEE = REPO_ROOT / "configs/judge-committee-rubric-calibration.json"
GOLD = REPO_ROOT / "tests/fixtures/zauderndes_trio_professor_gold.json"
STYLE_CALIBRATION = REPO_ROOT / "tests/fixtures/gutachtenstil_calibration.json"
STYLE_CALIBRATION_V2 = REPO_ROOT / "tests/fixtures/gutachtenstil_calibration_v2.json"
TRIO_TASK = (
    REPO_ROOT
    / "tasks/de/strafrecht/materielles-strafrecht/ubungsfall-ein-zauderndes-trio"
)


class ProfessorFeedbackRuleTests(unittest.TestCase):
    def test_sol_is_the_default_rubric_generator(self):
        self.assertEqual(DEFAULT_MODEL, "gpt-5.6-sol")

    def test_judge_prompt_contains_reviewed_evidence_rules(self):
        prompt = (REPO_ROOT / "prompts/evaluation/rubric_criterion.txt").read_text(encoding="utf-8")
        self.assertIn("same claim, administrative act, subject matter, participant/person", prompt)
        self.assertIn("A bare mention, heading, issue statement, or result", prompt)
        self.assertIn("material fact absent from or contradicted", prompt)
        self.assertIn("Decide by legal meaning, not by keyword overlap", prompt)
        self.assertIn("Treat the examination station as part of the legal issue", prompt)
        self.assertIn("A named fact-pattern variant, hypothetical, or subpart", prompt)
        self.assertIn("Do not fail solely because the answer omits the variant label", prompt)
        self.assertIn("Evaluate the reason the answer actually gives", prompt)
        self.assertIn("do not replace that stated reason", prompt)

    def test_style_prompt_is_separate_from_content(self):
        prompt = (REPO_ROOT / "prompts/evaluation/gutachtenstil_criterion.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("Do not reconsider, confirm, or correct the substantive verdict", prompt)
        self.assertIn("functional Gutachtenstil, not a rigid phrase template", prompt)
        self.assertIn("a substantive error does not imply bad legal reasoning style", prompt)
        self.assertIn("need not be substantively correct", prompt)
        self.assertIn("does not attempt this criterion at all", prompt)
        self.assertIn("Mere proximity of a rule, facts, and result is not enough", prompt)
        self.assertIn("good definition standing alone", prompt)
        self.assertIn("This is a hard requirement", prompt)
        self.assertIn("statements scattered elsewhere in the answer", prompt)
        self.assertIn("chosen line of examination must be completed", prompt)
        self.assertIn("standard for a neighboring issue is not", prompt)
        self.assertIn("complicity standard does not by itself examine", prompt)
        self.assertIn("Do not supply a missing premise", prompt)
        self.assertIn("same person, legal object, issue, and examination station", prompt)
        self.assertIn("A substantively wrong but methodically complete argument", prompt)

    def test_combined_prompt_keeps_content_and_style_independent(self):
        prompt = combined_content_style_prompt(
            {"title": "Test", "instructions": "Prüfen."},
            TRIO_TASK,
            "Die Antwort.",
            {
                "id": "C-001",
                "title": "Prüfungspunkt",
                "match_criteria": "ERFÜLLT, wenn geprüft.",
            },
        )
        self.assertIn("two independent verdicts", prompt)
        self.assertIn("`content: fail`, `style: pass`", prompt)
        self.assertIn("`content: pass`, `style: fail`", prompt)
        self.assertIn('"content": {', prompt)
        self.assertIn('"style": {', prompt)
        self.assertIn("standard for a neighboring issue", prompt)
        self.assertIn("A named fact-pattern variant, hypothetical, or subpart", prompt)
        self.assertIn("Do not fail solely because the answer omits the", prompt)
        self.assertIn("variant label when its surrounding context", prompt)

    def test_responses_prompt_breakpoint_precedes_sources_and_criterion(self):
        prompt = combined_content_style_prompt(
            {"title": "Test", "instructions": "Prüfen."},
            TRIO_TASK,
            "Die vollständige Antwort.",
            {
                "id": "C-001",
                "title": "Individuelles Kriterium",
                "match_criteria": "ERFÜLLT, wenn geprüft.",
            },
        )
        response_input = responses_input_with_cache_breakpoint(prompt)
        stable, variable = response_input[0]["content"]

        self.assertEqual(stable["prompt_cache_breakpoint"], {"mode": "explicit"})
        self.assertIn("Instructions:\nPrüfen.", stable["text"])
        self.assertIn("Die vollständige Antwort.", stable["text"])
        self.assertNotIn("## Source documents", stable["text"])
        self.assertIn("## Source documents", variable["text"])
        self.assertIn("Individuelles Kriterium", variable["text"])
        self.assertEqual(stable["text"] + variable["text"], prompt)

    def test_prompt_cache_keys_are_stably_partitioned_below_burst_limit(self):
        first = prompt_cache_key_for_criterion("answer", "luna", 0)
        fourth = prompt_cache_key_for_criterion("answer", "luna", 3)
        fifth = prompt_cache_key_for_criterion("answer", "luna", 4)

        self.assertEqual(first, fourth)
        self.assertNotEqual(first, fifth)
        self.assertEqual(first, "lab-eu-answer-luna-p00")

    def test_usage_summary_records_cache_reads_and_writes(self):
        summary = usage_summary(
            {
                "usage": {
                    "input_tokens": 2000,
                    "input_tokens_details": {
                        "cached_tokens": 1500,
                        "cache_write_tokens": 400,
                    },
                }
            }
        )

        self.assertEqual(summary["cached_input_tokens"], 1500)
        self.assertEqual(summary["cache_write_tokens"], 400)

    def test_gpt56_responses_request_uses_explicit_cache_mode(self):
        client = mock.Mock()
        response = mock.Mock()
        response.output_text = "{}"
        response.model_dump.return_value = {"usage": {}}
        client.responses.create.return_value = response

        _judge_call_responses(
            client,
            "gpt-5.6-luna",
            "stable task and answer\n## Source documents\nvariable criterion",
            "medium",
            cache_key="lab-eu-answer-luna-p00",
        )

        request = client.responses.create.call_args.kwargs
        self.assertEqual(request["prompt_cache_key"], "lab-eu-answer-luna-p00")
        self.assertEqual(
            request["extra_body"], {"prompt_cache_options": {"mode": "explicit"}}
        )
        self.assertEqual(
            request["input"][0]["content"][0]["prompt_cache_breakpoint"],
            {"mode": "explicit"},
        )

    def test_combined_result_preserves_opposite_binary_verdicts(self):
        normalized = normalize_combined_judge_result(
            {
                "content": {
                    "verdict": "fail",
                    "reasoning": "Legally wrong.",
                    "evidence": ["wrong rule"],
                },
                "style": {
                    "verdict": "pass",
                    "reasoning": "Methodically complete.",
                    "evidence": ["rule, facts, conclusion"],
                    "method_checks": {
                        "same_scope": True,
                        "criterion_specific_premise": True,
                        "explicit_fact_link": True,
                        "completed_path": True,
                        "not_reconstructed_elsewhere": True,
                    },
                },
            },
            {"input_tokens": 100, "output_tokens": 20},
        )
        self.assertEqual(normalized["content"]["verdict"], "fail")
        self.assertEqual(normalized["style"]["verdict"], "pass")
        self.assertEqual(normalized["content"]["usage"]["input_tokens"], 100)
        self.assertEqual(normalized["style"]["usage"], {})

    def test_combined_style_check_failure_overrides_pass(self):
        normalized = normalize_combined_judge_result(
            {
                "content": {"verdict": "pass", "evidence": [], "reasoning": "ok"},
                "style": {
                    "verdict": "pass",
                    "evidence": [],
                    "reasoning": "assembled elsewhere",
                    "method_checks": {
                        "same_scope": True,
                        "criterion_specific_premise": True,
                        "explicit_fact_link": True,
                        "completed_path": True,
                        "not_reconstructed_elsewhere": False,
                    },
                },
            },
            {},
        )
        self.assertEqual(normalized["content"]["verdict"], "pass")
        self.assertEqual(normalized["style"]["verdict"], "fail")

    def test_style_eligibility_is_limited_to_application_and_argumentation(self):
        for function in ("application", "argumentation"):
            self.assertTrue(
                is_style_eligible_criterion({"analysis_tags": {"function": function}})
            )
        for function in (
            "structure",
            "legal_basis",
            "rule_statement",
            "conclusion",
            "form_citation",
        ):
            self.assertFalse(
                is_style_eligible_criterion({"analysis_tags": {"function": function}})
            )
        self.assertTrue(is_style_eligible_criterion({}))

    def test_generator_does_not_invent_alternatives(self):
        atomizer = (REPO_ROOT / "prompts/rubric_generation/atomize_solution.user.txt").read_text(
            encoding="utf-8"
        )
        candidates = (
            REPO_ROOT / "prompts/rubric_generation/generate_candidate_criteria.user.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("only alternatives expressly accepted by the supplied solution", atomizer)
        self.assertIn("Never invent another alternative from model knowledge", candidates)

    def test_pruner_preserves_expressly_accepted_result_relevant_alternatives(self):
        pruner = (REPO_ROOT / "prompts/rubric_generation/prune_rubric.user.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("must not be removed merely because", pruner)
        self.assertIn("carry its consequences through dependent interim and final results", pruner)
        self.assertIn("Do not invent missing amounts or consequences", pruner)

    def test_generator_uses_independent_partial_credit_as_granularity_boundary(self):
        candidates = (
            REPO_ROOT / "prompts/rubric_generation/generate_candidate_criteria.user.txt"
        ).read_text(encoding="utf-8")
        pruner = (REPO_ROOT / "prompts/rubric_generation/prune_rubric.user.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("independent partial credit as the boundary", candidates)
        self.assertIn("do not routinely turn definitions", candidates)
        self.assertIn("combine the necessary rule or definition", pruner)
        self.assertIn("Do not make separate criteria for individual facts", pruner)

    def test_negative_mutant_prompt_and_gate_are_case_neutral(self):
        prompt = (
            REPO_ROOT
            / "prompts/rubric_generation/generate_negative_mutants.user.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("bare_result", prompt)
        self.assertIn("wrong_scope", prompt)
        self.assertIn("material_error", prompt)
        self.assertNotIn("zauderndes trio", prompt.lower())

        criteria = [
            {"id": "C-001", "title": "one", "match_criteria": "x", "criticality": 2}
        ]
        mutants = validate_mutants(
            [
                {
                    "criterion_id": "C-001",
                    "type": mutant_type,
                    "answer": f"answer-{mutant_type}",
                    "why_should_fail": "reason",
                }
                for mutant_type in ("bare_result", "wrong_scope", "material_error")
            ],
            criteria,
        )
        self.assertEqual(len(mutants), 3)

        results = [
            {
                "kind": "positive_gold",
                "criterion_id": "C-001",
                "correct": True,
            },
            *[
                {
                    "kind": mutant_type,
                    "criterion_id": "C-001",
                    "correct": mutant_type != "bare_result",
                }
                for mutant_type in ("bare_result", "wrong_scope", "material_error")
            ],
        ]
        metrics = build_metrics(results, {"C-001": criteria[0]})
        self.assertFalse(metrics["freeze_allowed"])
        self.assertEqual(metrics["blocking_criticality_2_or_3"], 1)

        with_not_applicable = validate_mutants(
            [
                {
                    "criterion_id": "C-001",
                    "type": mutant_type,
                    "applicable": mutant_type != "bare_result",
                    "answer": "" if mutant_type == "bare_result" else "answer",
                    "why_should_fail": "No literal application requirement."
                    if mutant_type == "bare_result"
                    else "reason",
                }
                for mutant_type in ("bare_result", "wrong_scope", "material_error")
            ],
            criteria,
        )
        self.assertFalse(with_not_applicable[0]["applicable"])
        self.assertEqual(with_not_applicable[0]["answer"], "")

    def test_negative_mutant_generation_collects_real_task_bundle(self):
        criterion = {
            "id": "C-001",
            "title": "Test",
            "match_criteria": "ERFÜLLT, wenn geprüft. NICHT ERFÜLLT, wenn nur erwähnt.",
            "criticality": 2,
        }
        raw_mutants = [
            {
                "criterion_id": "C-001",
                "type": mutant_type,
                "answer": f"answer-{mutant_type}",
                "why_should_fail": "reason",
            }
            for mutant_type in ("bare_result", "wrong_scope", "material_error")
        ]
        with (
            mock.patch(
                "scripts.run_negative_rubric_calibration.make_generator_client",
                return_value=object(),
            ),
            mock.patch(
                "scripts.run_negative_rubric_calibration.api_call",
                return_value=({"mutants": raw_mutants}, {"usage": {}}),
            ) as api_call_mock,
        ):
            mutants, _usage = generate_mutants(
                task_dir=TRIO_TASK,
                task=json.loads((TRIO_TASK / "task.json").read_text(encoding="utf-8")),
                criteria=[criterion],
                solution_files=[TRIO_TASK / "evals" / "loesung.md"],
                model="test",
                reasoning_effort=None,
                chunk_size=8,
                cache_dir=None,
            )
        self.assertEqual(len(mutants), 3)
        sent_user_prompt = api_call_mock.call_args.kwargs["user"]
        self.assertNotIn('"analysis_tags"', sent_user_prompt)

    def test_mutant_applicability_respects_criterion_function(self):
        criteria = [
            {
                "id": "C-CONCLUSION",
                "title": "Conclusion",
                "match_criteria": "PASS if the answer reaches the result.",
                "analysis_tags": {"function": "conclusion"},
            },
            {
                "id": "C-RULE",
                "title": "Rule",
                "match_criteria": "PASS if the answer states the abstract rule.",
                "analysis_tags": {"function": "rule_statement"},
            },
        ]
        raw = []
        for criterion in criteria:
            for mutant_type in ("bare_result", "wrong_scope", "material_error"):
                raw.append(
                    {
                        "criterion_id": criterion["id"],
                        "type": mutant_type,
                        "applicable": True,
                        "answer": "test answer",
                        "why_should_fail": "test rationale",
                    }
                )
        mutants = validate_mutants(raw, criteria)
        by_id = {mutant["id"]: mutant for mutant in mutants}
        self.assertFalse(by_id["C-CONCLUSION__bare_result"]["applicable"])
        self.assertFalse(by_id["C-RULE__wrong_scope"]["applicable"])
        self.assertTrue(by_id["C-CONCLUSION__material_error"]["applicable"])

    def test_criticality_distribution_warns_without_blocking(self):
        compliant = ([{"criticality": 3}] * 1) + ([{"criticality": 2}] * 6) + ([{"criticality": 1}] * 3)
        self.assertEqual(criticality_distribution_warnings(compliant), [])
        warnings = criticality_distribution_warnings([{"criticality": 2}] * 10)
        self.assertEqual(len(warnings), 2)
        self.assertIn("target is about 10-15%", warnings[0])
        self.assertIn("target maximum is 60%", warnings[1])

    def test_generation_prompts_are_generic_and_do_not_contain_review_case_data(self):
        prompt_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((REPO_ROOT / "prompts/rubric_generation").glob("*.txt"))
        ).lower()
        for forbidden in ["zauderndes trio", "svenja behrendt", "professorinnenfeedback", "c-052"]:
            self.assertNotIn(forbidden, prompt_text)

    def test_professor_gold_is_marked_external_only(self):
        if not GOLD.exists():
            self.skipTest("private professor gold fixture is not checked into Git")
        payload = json.loads(GOLD.read_text(encoding="utf-8"))
        self.assertIn("must never be supplied", payload["purpose"])
        self.assertEqual(len(payload["submissions"]["baseline"]["labels"]), 21)
        self.assertEqual(len(payload["submissions"]["agent"]["labels"]), 10)

    def test_committee_has_three_distinct_requested_models(self):
        specs = load_judge_committee(COMMITTEE)
        self.assertEqual(len(specs), 3)
        self.assertEqual(
            {spec.model for spec in specs},
            {"gpt-5.6-luna", "gpt-5.6-terra", "google/gemini-3.6-flash"},
        )

    def test_sol_pilot_committee_uses_luna_terra_and_gemini(self):
        specs = load_judge_committee(SOL_COMMITTEE)
        self.assertEqual(
            {spec.model for spec in specs},
            {"gpt-5.6-luna", "gpt-5.6-terra", "google/gemini-3.6-flash"},
        )

    def test_style_calibration_is_balanced_and_case_neutral(self):
        payload = json.loads(STYLE_CALIBRATION.read_text(encoding="utf-8"))
        cases = payload["cases"]
        self.assertEqual(len(cases), 24)
        self.assertEqual(
            {area: sum(case["area"] == area for case in cases) for area in {case["area"] for case in cases}},
            {"zivilrecht": 8, "strafrecht": 8, "oeffentliches-recht": 8},
        )
        self.assertEqual(sum(case["expected_verdict"] == "pass" for case in cases), 12)
        self.assertEqual(sum(case["expected_verdict"] == "fail" for case in cases), 12)
        self.assertNotIn("zauderndes trio", STYLE_CALIBRATION.read_text(encoding="utf-8").lower())

    def test_style_calibration_v2_has_balanced_minimal_pairs(self):
        payload = json.loads(STYLE_CALIBRATION_V2.read_text(encoding="utf-8"))
        cases = payload["cases"]
        self.assertEqual(payload["label_status"], "draft_requires_jurist_review")
        self.assertEqual(len(cases), 36)
        self.assertEqual(
            {
                area: sum(case["area"] == area for case in cases)
                for area in {case["area"] for case in cases}
            },
            {"zivilrecht": 12, "strafrecht": 12, "oeffentliches-recht": 12},
        )
        self.assertEqual(sum(case["expected_verdict"] == "pass" for case in cases), 18)
        self.assertEqual(sum(case["expected_verdict"] == "fail" for case in cases), 18)
        pairs = {case["pair_id"] for case in cases}
        self.assertEqual(len(pairs), 18)
        for pair_id in pairs:
            labels = sorted(
                case["expected_verdict"]
                for case in cases
                if case["pair_id"] == pair_id
            )
            self.assertEqual(labels, ["fail", "pass"], pair_id)
        fixture_text = STYLE_CALIBRATION_V2.read_text(encoding="utf-8").lower()
        self.assertNotIn("zauderndes trio", fixture_text)
        self.assertNotIn("behrendt", fixture_text)

    def test_sol_comparison_artifact_dry_run_does_not_replace_default_rubric(self):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/generate_rubric.py",
                str(TRIO_TASK),
                "--artifact-suffix",
                "sol",
                "--dry-run",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("rubric.generated.sol.json", result.stdout)
        self.assertNotIn("Output: " + str(TRIO_TASK / "evals/rubric.generated.json") + "\n", result.stdout)

    def test_rubric_calibration_can_use_the_three_model_committee(self):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/generate_rubric.py",
                str(TRIO_TASK),
                "--solution",
                str(TRIO_TASK / "evals/loesung.md"),
                "--calibration-committee",
                str(CALIBRATION_COMMITTEE),
                "--dry-run",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Calibration committee:", result.stdout)
        self.assertIn("gpt-5.6-luna", result.stdout)
        self.assertIn("gpt-5.6-terra", result.stdout)
        self.assertIn("google/gemini-3.6-flash", result.stdout)
        self.assertIn("Calibration votes: 3", result.stdout)

    def test_content_style_and_weighted_scores_are_separate(self):
        criteria = [
            {"id": "C-001", "title": "one", "match_criteria": "x", "criticality": 3},
            {"id": "C-002", "title": "two", "match_criteria": "y", "criticality": 1},
        ]
        vote = {"pass": 1, "fail": 0, "error": 0}
        content = [
            {"id": "C-001", "title": "one", "verdict": "pass", "vote_counts": vote, "judge_agreement": 1.0, "usage": {}},
            {"id": "C-002", "title": "two", "verdict": "fail", "vote_counts": {"pass": 0, "fail": 1, "error": 0}, "judge_agreement": 1.0, "usage": {}},
        ]
        style = [
            {"id": "C-001", "title": "one", "verdict": "fail", "vote_counts": {"pass": 0, "fail": 1, "error": 0}, "judge_agreement": 1.0, "usage": {}}
        ]
        scores = assemble_scores(
            task_dir=REPO_ROOT,
            submission=REPO_ROOT / "README.md",
            rubric_path=REPO_ROOT / "rubric.json",
            task={"title": "test"},
            criteria=criteria,
            results=content,
            judge_model="test",
            api_base="test",
            reasoning_effort=None,
            votes=1,
            adaptive=False,
            judge_committee=[JudgeSpec(name="test", model="test")],
            style_results=style,
            style_evaluation_mode="combined",
        )
        self.assertEqual(scores["content_score"]["pass_rate"], 0.5)
        self.assertEqual(scores["criticality_weighted_content_score"]["pass_rate"], 0.75)
        self.assertEqual(scores["style_score"]["pass_rate"], 0.0)
        self.assertEqual(scores["style_score"]["n_eligible"], 1)
        self.assertIn(
            "regardless of content verdict",
            scores["style_score"]["denominator_rule"],
        )
        self.assertEqual(scores["style_evaluation_mode"], "combined")

    def test_split_vote_with_model_error_is_reported_unresolved(self):
        result = aggregate_votes(
            {"id": "C-001", "title": "one"},
            [
                {"verdict": "pass", "usage": {}},
                {"verdict": "fail", "usage": {}},
                {"verdict": "error", "usage": {}},
            ],
        )
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["resolution"], "unresolved")

    def test_structured_judge_audit_can_only_make_pass_stricter(self):
        normalized = normalize_judge_result(
            {
                "verdict": "pass",
                "evidence": ["result from the wrong legal station"],
                "component_checks": [
                    {"requirement": "correct controlling reason", "satisfied": False}
                ],
                "scope_check": {"same_scope": True},
                "stated_reason_check": {"legally_compatible": False},
                "reasoning": "The answer states a materially wrong provision.",
            },
            {},
        )
        self.assertEqual(normalized["verdict"], "fail")
        self.assertFalse(normalized["component_checks"][0]["satisfied"])

    def test_committee_conflict_recheck_requires_same_round_majority(self):
        def votes(*verdicts):
            return [
                {
                    "verdict": verdict,
                    "usage": {},
                    "reasoning": f"{name}-{verdict}",
                    "evidence": [],
                    "judge": {"name": name, "model": name},
                }
                for name, verdict in zip(("luna", "terra", "gemini"), verdicts)
            ]

        first = votes("pass", "pass", "fail")
        self.assertTrue(needs_committee_recheck(first))
        stable = finalize_committee_rounds(
            {"id": "C-001", "title": "one"}, first, votes("pass", "fail", "pass")
        )
        self.assertEqual(stable["verdict"], "pass")
        self.assertEqual(stable["resolution"], "stable_with_dissent")
        self.assertEqual(len(stable["voting_rounds"]), 2)

        flipped = finalize_committee_rounds(
            {"id": "C-001", "title": "one"}, first, votes("fail", "pass", "fail")
        )
        self.assertEqual(flipped["verdict"], "fail")
        self.assertEqual(flipped["resolution"], "unresolved")
        self.assertEqual(flipped["committee_status"], "majority_flip")

    def test_committee_tiebreaker_resolves_one_to_one_without_stability_round(self):
        criterion = {"id": "C-001", "title": "one"}
        primary_votes = [
            {"verdict": "pass", "usage": {}, "judge": {"name": "luna"}},
            {"verdict": "fail", "usage": {}, "judge": {"name": "terra"}},
        ]
        tiebreaker = [
            {"verdict": "pass", "usage": {}, "judge": {"name": "haiku-4.5"}}
        ]

        self.assertTrue(needs_committee_tiebreaker(primary_votes))
        result = finalize_committee_tiebreaker(
            criterion, primary_votes, tiebreaker
        )

        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["resolution"], "resolved")
        self.assertEqual(result["committee_status"], "resolved_by_tiebreaker")
        self.assertEqual(result["vote_counts"], {"pass": 2, "fail": 1, "error": 0})
        self.assertEqual([stage["stage"] for stage in result["voting_rounds"]], ["primary", "tiebreaker"])

    def test_committee_tiebreaker_calls_third_judge_only_for_primary_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            task_dir = root / "task"
            evals = task_dir / "evals"
            evals.mkdir(parents=True)
            (task_dir / "task.json").write_text(
                json.dumps({"title": "test", "instructions": "test"}),
                encoding="utf-8",
            )
            (evals / "rubric.json").write_text(
                json.dumps(
                    {
                        "criteria": [
                            {"id": "C-001", "title": "consensus", "match_criteria": "x"},
                            {"id": "C-002", "title": "conflict", "match_criteria": "y"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            submission = root / "answer.md"
            submission.write_text("answer", encoding="utf-8")
            committee = [
                JudgeSpec("luna", "luna", "openai", None),
                JudgeSpec("terra", "terra", "openai", None),
                JudgeSpec("haiku", "haiku", "openrouter", None),
            ]
            calls: list[tuple[str, str]] = []

            def fake_vote(*, spec, criterion, **kwargs):
                calls.append((criterion["id"], spec.name))
                verdicts = {
                    ("C-001", "luna"): "pass",
                    ("C-001", "terra"): "pass",
                    ("C-002", "luna"): "pass",
                    ("C-002", "terra"): "fail",
                    ("C-002", "haiku"): "fail",
                }
                return {
                    "id": criterion["id"],
                    "title": criterion["title"],
                    "verdict": verdicts[(criterion["id"], spec.name)],
                    "reasoning": "test",
                    "evidence": [],
                    "usage": {},
                }

            with mock.patch("evaluation.run.make_client", return_value=(object(), False)), mock.patch(
                "evaluation.run.cached_judge_vote", side_effect=fake_vote
            ):
                scores = evaluate(
                    task_dir=task_dir,
                    submission=submission,
                    judge_model="unused",
                    parallel=1,
                    reasoning_effort=None,
                    votes=1,
                    judge_committee=committee,
                    committee_tiebreaker=True,
                    committee_error_retries=0,
                )

        self.assertNotIn(("C-001", "haiku"), calls)
        self.assertIn(("C-002", "haiku"), calls)
        self.assertEqual(scores["n_unresolved"], 0)
        self.assertEqual(
            scores["committee_voting_mode"], "primary_pair_with_tiebreaker"
        )
        self.assertFalse(scores["committee_conflict_recheck"])
        self.assertTrue(scores["committee_tiebreaker"])

    def test_persistent_committee_error_is_conservatively_not_passed(self):
        result = finalize_committee_rounds(
            {"id": "C-001", "title": "one"},
            [
                {"verdict": "pass", "usage": {}},
                {"verdict": "pass", "usage": {}},
                {"verdict": "error", "usage": {}},
            ],
        )
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["resolution"], "unresolved")
        self.assertEqual(result["committee_status"], "incomplete")

    def test_review_export_uses_recorded_submission_and_shows_individual_votes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            task_dir = root / "task"
            evals = task_dir / "evals"
            evals.mkdir(parents=True)
            rubric_path = evals / "rubric.json"
            rubric_path.write_text(
                json.dumps(
                    {
                        "criteria": [
                            {
                                "id": "C-001",
                                "title": "Test",
                                "match_criteria": "ERFÜLLT, wenn x. NICHT ERFÜLLT, wenn y.",
                                "criticality": 2,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            submission = root / "run" / "submission" / "answer.md"
            submission.parent.mkdir(parents=True)
            submission.write_text("TATSÄCHLICHE AGENTENANTWORT", encoding="utf-8")
            output_dir = root / "output"
            output_dir.mkdir()
            (output_dir / "baseline-review.md").write_text(
                "FALSCHE BASELINE-EINBETTUNG", encoding="utf-8"
            )
            scores_path = output_dir / "scores.json"
            scores_path.write_text(
                json.dumps(
                    {
                        "task": {"path": str(task_dir), "title": "Testfall"},
                        "submission": str(submission),
                        "rubric": str(rubric_path),
                        "judge_model": "committee",
                        "judge_committee": [
                            {"name": "luna", "model": "gpt-5.6-luna"},
                            {"name": "terra", "model": "gpt-5.6-terra"},
                            {"name": "gemini", "model": "gemini"},
                        ],
                        "votes_per_criterion": 3,
                        "n_passed": 0,
                        "n_criteria": 1,
                        "criterion_pass_rate": 0.0,
                        "criteria_results": [
                            {
                                "id": "C-001",
                                "title": "Test",
                                "verdict": "fail",
                                "resolution": "unresolved",
                                "reasoning": "Mehrheit nicht belastbar.",
                                "evidence": [],
                                "vote_counts": {"pass": 1, "fail": 1, "error": 1},
                                "votes": [
                                    {"verdict": "pass", "judge": {"name": "luna", "model": "gpt-5.6-luna"}},
                                    {"verdict": "fail", "judge": {"name": "terra", "model": "gpt-5.6-terra"}},
                                    {"verdict": "error", "judge": {"name": "gemini", "model": "gemini"}},
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            review = build_markdown(scores_path)
            self.assertIn("TATSÄCHLICHE AGENTENANTWORT", review)
            self.assertNotIn("FALSCHE BASELINE-EINBETTUNG", review)
            self.assertIn("1 pass / 1 fail / 1 error", review)
            self.assertIn("luna (gpt-5.6-luna)", review)
            self.assertIn("`unresolved`", review)

    def test_targeted_judge_run_filters_the_evaluated_criteria(self):
        criteria = [{"id": "C-001"}, {"id": "C-002"}, {"id": "C-003"}]
        self.assertEqual(
            [criterion["id"] for criterion in select_criteria(criteria, ["C-003", "C-001"])],
            ["C-001", "C-003"],
        )
        with self.assertRaises(SystemExit):
            select_criteria(criteria, ["C-999"])

    def test_regression_fixtures_are_dry_run_ready(self):
        result = subprocess.run(
            [sys.executable, "scripts/run_judge_regressions.py", "--dry-run"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated 5 regression cases", result.stdout)


if __name__ == "__main__":
    unittest.main()
