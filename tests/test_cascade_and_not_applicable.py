"""depends_on cascade reporting and the opt-in not_applicable verdict.

Both features must be invisible to every rubric that does not use them: the
existing 45-case study is scored with the same numbers as before.
"""

from __future__ import annotations

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from evaluation.run import (  # noqa: E402
    aggregate_votes,
    assemble_scores,
    criterion_applies_when,
    normalize_judge_result,
)


def criterion(cid: str, **extra):
    return {"id": cid, "title": f"Titel {cid}", "match_criteria": "ERFÜLLT, wenn ...", **extra}


def result(cid: str, verdict: str, resolution: str = "resolved"):
    return {
        "id": cid,
        "title": f"Titel {cid}",
        "verdict": verdict,
        "resolution": resolution,
        "reasoning": "",
        "evidence": [],
        "vote_counts": {"pass": 1 if verdict == "pass" else 0, "fail": 0, "error": 0},
        "judge_agreement": 1.0,
        "votes": [],
        "usage": {},
    }


def payload(criteria, results):
    return assemble_scores(
        task_dir=pathlib.Path("."),
        submission=pathlib.Path("sub.md"),
        rubric_path=pathlib.Path("rubric.json"),
        task={"title": "T"},
        criteria=criteria,
        results=results,
        judge_model="m",
        api_base="b",
        reasoning_effort=None,
        votes=1,
        adaptive=False,
    )


# --- not_applicable is strictly opt-in -------------------------------------


def test_not_applicable_is_rejected_without_applies_when():
    vote = normalize_judge_result({"verdict": "not_applicable", "reasoning": "x"}, {})
    assert vote["verdict"] == "fail"


def test_not_applicable_is_accepted_with_applies_when():
    vote = normalize_judge_result(
        {"verdict": "not_applicable", "reasoning": "anderer Weg"}, {}, allow_not_applicable=True
    )
    assert vote["verdict"] == "not_applicable"


def test_not_applicable_ignores_the_pass_decomposition():
    """The unmet components belong to the path the answer did not take."""
    vote = normalize_judge_result(
        {
            "verdict": "not_applicable",
            "component_checks": [{"requirement": "r", "satisfied": False}],
            "scope_check": {"same_scope": False},
        },
        {},
        allow_not_applicable=True,
    )
    assert vote["verdict"] == "not_applicable"


def test_criterion_applies_when_reads_the_field():
    assert criterion_applies_when(criterion("C-1")) == ""
    assert criterion_applies_when(criterion("C-1", applies_when="  ")) == ""
    assert criterion_applies_when(criterion("C-1", applies_when="Weg A")) == "Weg A"
    assert criterion_applies_when(None) == ""


def test_majority_not_applicable_wins_the_aggregate():
    votes = [
        {"verdict": "not_applicable", "reasoning": "", "evidence": []},
        {"verdict": "not_applicable", "reasoning": "", "evidence": []},
        {"verdict": "fail", "reasoning": "", "evidence": []},
    ]
    out = aggregate_votes(criterion("C-1", applies_when="Weg A"), votes)
    assert out["verdict"] == "not_applicable"
    assert out["resolution"] == "not_applicable"


def test_pass_still_beats_not_applicable():
    votes = [
        {"verdict": "pass", "reasoning": "", "evidence": []},
        {"verdict": "pass", "reasoning": "", "evidence": []},
        {"verdict": "not_applicable", "reasoning": "", "evidence": []},
    ]
    out = aggregate_votes(criterion("C-1", applies_when="Weg A"), votes)
    assert out["verdict"] == "pass"


def test_not_applicable_leaves_the_denominator():
    criteria = [criterion("C-1"), criterion("C-2", applies_when="Weg A"), criterion("C-3")]
    results = [result("C-1", "pass"), result("C-2", "not_applicable"), result("C-3", "fail")]
    scores = payload(criteria, results)
    content = scores["content_score"]
    assert content["n_criteria"] == 3
    assert content["n_scored"] == 2
    assert content["n_not_applicable"] == 1
    assert content["pass_rate"] == 0.5
    assert scores["criterion_pass_rate"] == 0.5


def test_all_pass_ignores_not_applicable():
    criteria = [criterion("C-1"), criterion("C-2", applies_when="Weg A")]
    results = [result("C-1", "pass"), result("C-2", "not_applicable")]
    assert payload(criteria, results)["all_pass"] is True


def test_not_applicable_leaves_the_weighted_score_too():
    criteria = [
        criterion("C-1", criticality=3),
        criterion("C-2", criticality=3, applies_when="Weg A"),
    ]
    results = [result("C-1", "pass"), result("C-2", "not_applicable")]
    weighted = payload(criteria, results)["criticality_weighted_content_score"]
    assert weighted["points_available"] == 3
    assert weighted["pass_rate"] == 1.0


# --- depends_on is reporting only ------------------------------------------


def test_cascade_report_is_inert_without_depends_on():
    criteria = [criterion("C-1"), criterion("C-2")]
    results = [result("C-1", "fail"), result("C-2", "fail")]
    scores = payload(criteria, results)
    assert scores["cascade_report"]["declared"] is False
    assert scores["cascade_report"]["cascades"] == []
    # The headline number is untouched by the feature.
    assert scores["content_score"]["pass_rate"] == 0.0
    assert scores["content_score"]["n_scored"] == 2


def test_cascade_is_reported_but_not_rescored():
    criteria = [
        criterion("C-1"),
        criterion("C-2", depends_on=["C-1"]),
        criterion("C-3", depends_on=["C-1"]),
        criterion("C-4"),
    ]
    results = [
        result("C-1", "fail"),
        result("C-2", "fail"),
        result("C-3", "fail"),
        result("C-4", "pass"),
    ]
    scores = payload(criteria, results)
    # Headline stays 1/4: the dependents still count against the answer.
    assert scores["content_score"]["pass_rate"] == 0.25
    cascade = scores["cascade_report"]
    assert cascade["declared"] is True
    # Only C-1 and C-4 are independent forks.
    assert cascade["n_root_criteria"] == 2
    assert cascade["n_root_passed"] == 1
    assert cascade["root_pass_rate"] == 0.5
    assert cascade["n_failures_behind_failed_roots"] == 2
    assert cascade["cascades"] == [
        {
            "root_id": "C-1",
            "root_title": "Titel C-1",
            "n_dependents": 2,
            "n_dependents_failed": 2,
            "dependents_failed": ["C-2", "C-3"],
        }
    ]


def test_no_cascade_entry_when_the_root_passed():
    criteria = [criterion("C-1"), criterion("C-2", depends_on=["C-1"])]
    results = [result("C-1", "pass"), result("C-2", "fail")]
    cascade = payload(criteria, results)["cascade_report"]
    assert cascade["cascades"] == []
    assert cascade["n_failures_behind_failed_roots"] == 0


def test_unknown_dependency_is_surfaced_not_silently_dropped():
    criteria = [criterion("C-1"), criterion("C-2", depends_on=["C-99"])]
    results = [result("C-1", "pass"), result("C-2", "fail")]
    cascade = payload(criteria, results)["cascade_report"]
    assert cascade["unknown_dependencies"] == ["C-2 -> C-99"]


def test_root_pass_rate_ignores_not_applicable_roots():
    criteria = [
        criterion("C-1"),
        criterion("C-2", applies_when="Weg A"),
        criterion("C-3", depends_on=["C-1"]),
    ]
    results = [result("C-1", "pass"), result("C-2", "not_applicable"), result("C-3", "fail")]
    cascade = payload(criteria, results)["cascade_report"]
    assert cascade["n_root_criteria"] == 1
    assert cascade["root_pass_rate"] == 1.0


def test_cascade_walks_the_whole_chain_not_just_direct_children():
    """A three-level chain reports one fork with all nine consequences."""
    criteria = [criterion("C-1")]
    criteria.append(criterion("C-2", depends_on=["C-1"]))
    criteria.append(criterion("C-3", depends_on=["C-2"]))
    criteria += [criterion(f"C-{i}", depends_on=["C-3"]) for i in range(4, 11)]
    results = [result(c["id"], "fail") for c in criteria]
    cascade = payload(criteria, results)["cascade_report"]
    assert [entry["root_id"] for entry in cascade["cascades"]] == ["C-1"]
    entry = cascade["cascades"][0]
    assert entry["n_dependents"] == 9
    assert entry["n_dependents_failed"] == 9
    assert cascade["n_root_criteria"] == 1
