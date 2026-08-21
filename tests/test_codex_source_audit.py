"""Source-report extraction from Codex JSONL and selected deliverables."""

from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from codex_source_audit import source_audit, write_run_summary  # noqa: E402


def test_separates_searches_visited_pages_and_citations(tmp_path):
    stdout = tmp_path / "stdout.jsonl"
    events = [
        {
            "type": "item.completed",
            "item": {
                "type": "web_search",
                "query": "official law",
                "action": {"type": "search", "queries": ["official law", "court case"]},
            },
        },
        {
            "type": "item.completed",
            "item": {
                "type": "command_execution",
                "command": "curl -L https://court.example/decision.html | sed -n '1,20p'",
                "aggregated_output": "unvisited result https://noise.example/style.css",
            },
        },
    ]
    stdout.write_text(
        "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
    )
    answer = tmp_path / "answer.md"
    answer.write_text(
        "Authority: [decision](https://court.example/decision.html) and "
        "[statute](https://law.example/statute#section).",
        encoding="utf-8",
    )

    sidecar = tmp_path / ".codex-used-sources.json"
    sidecar.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "url": "https://research.example/commentary",
                        "title": "Commentary",
                        "purpose": "Checked doctrine",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = source_audit(stdout, [answer], sidecar)

    assert report["counts"] == {
        "search_queries": 2,
        "recorded_open_or_fetch_urls": 1,
        "used_urls": 3,
        "cited_urls": 2,
        "unique_used_source_urls": 3,
        "unique_used_source_domains": 3,
        "unique_source_urls": 3,
        "unique_source_domains": 3,
        "blocked_domain_violations": 0,
        "search_leakage_flags": 0,
        "web_access_violations": 0,
    }
    by_url = {source["url"]: source for source in report["sources"]}
    assert by_url["https://court.example/decision.html"]["visited"] is True
    assert by_url["https://court.example/decision.html"]["cited_in_deliverable"] is True
    assert by_url["https://law.example/statute"]["visited"] is False
    assert (
        by_url["https://research.example/commentary"]["reported_purpose"]
        == "Checked doctrine"
    )
    assert "https://noise.example/style.css" not in by_url


def test_blocked_domain_search_contaminates_run_even_without_citation(tmp_path):
    stdout = tmp_path / "stdout.jsonl"
    event = {
        "type": "item.completed",
        "item": {
            "type": "web_search",
            "action": {
                "type": "search",
                "queries": [
                    'site:zjs-online.com "Musterlösung"',
                    "Art. 5 GG -site:zjs-online.com",
                ],
            },
        },
    }
    stdout.write_text(json.dumps(event) + "\n", encoding="utf-8")

    report = source_audit(stdout, [], blocked_domains=["zjs-online.com"])

    assert report["blocked_domain_policy"]["passed"] is False
    kinds = {item["kind"] for item in report["blocked_domain_policy"]["violations"]}
    assert "positive-search-target" in kinds
    assert "missing-negative-filter" in kinds


def test_negative_site_filter_passes_blocked_domain_policy(tmp_path):
    stdout = tmp_path / "stdout.jsonl"
    event = {
        "type": "item.completed",
        "item": {
            "type": "web_search",
            "action": {
                "type": "search",
                "queries": [
                    "Art. 5 GG vertrauliche Kommunikation -site:zjs-online.com"
                ],
            },
        },
    }
    stdout.write_text(json.dumps(event) + "\n", encoding="utf-8")

    report = source_audit(stdout, [], blocked_domains=["zjs-online.com"])

    assert report["blocked_domain_policy"]["passed"] is True


def test_single_query_search_shape_is_also_domain_audited(tmp_path):
    stdout = tmp_path / "stdout.jsonl"
    event = {
        "type": "item.completed",
        "item": {
            "type": "web_search",
            "action": {"type": "search", "query": "Art. 5 GG Gefangenenbrief"},
        },
    }
    stdout.write_text(json.dumps(event) + "\n", encoding="utf-8")

    report = source_audit(stdout, [], blocked_domains=["zjs-online.com"])

    assert report["blocked_domain_policy"]["passed"] is False
    assert report["blocked_domain_policy"]["violations"] == [
        {
            "domain": "zjs-online.com",
            "kind": "missing-negative-filter",
            "evidence": "Art. 5 GG Gefangenenbrief",
        }
    ]


def test_no_web_arm_rejects_any_web_search_event(tmp_path):
    stdout = tmp_path / "stdout.jsonl"
    event = {
        "type": "item.completed",
        "item": {
            "type": "web_search",
            "action": {"type": "search", "query": "§ 823 BGB"},
        },
    }
    stdout.write_text(json.dumps(event) + "\n", encoding="utf-8")

    report = source_audit(stdout, [], web_search_allowed=False)

    assert report["web_access_policy"]["passed"] is False
    assert report["web_access_policy"]["violations"] == [
        {"kind": "web-search-event", "evidence": "1 web_search event(s)"}
    ]


def test_no_web_arm_rejects_explicit_shell_fetch(tmp_path):
    stdout = tmp_path / "stdout.jsonl"
    event = {
        "type": "item.completed",
        "item": {
            "type": "command_execution",
            "command": "curl https://law.example/statute",
        },
    }
    stdout.write_text(json.dumps(event) + "\n", encoding="utf-8")

    report = source_audit(stdout, [], web_search_allowed=False)

    assert report["web_access_policy"]["passed"] is False
    assert report["web_access_policy"]["violations"] == [
        {
            "kind": "explicit-network-fetch",
            "evidence": "https://law.example/statute",
        }
    ]


def test_exact_title_search_is_flagged_but_does_not_fail_policy(tmp_path):
    stdout = tmp_path / "stdout.jsonl"
    event = {
        "type": "item.completed",
        "item": {
            "type": "web_search",
            "action": {
                "type": "search",
                "queries": [
                    '"Examensübungsklausur Falsche Liebe" -site:zjs-online.com'
                ],
            },
        },
    }
    stdout.write_text(json.dumps(event) + "\n", encoding="utf-8")

    report = source_audit(
        stdout,
        [],
        blocked_domains=["zjs-online.com"],
        forbidden_search_identifiers=["Examensübungsklausur: Falsche Liebe"],
    )

    assert report["blocked_domain_policy"]["passed"] is True
    assert report["search_leakage_audit"]["flagged"] is True
    assert report["search_leakage_audit"]["enforcement"] == "informational-only"
    assert report["counts"]["search_leakage_flags"] >= 1


def test_fact_search_is_allowed_even_when_task_phrase_is_flagged(tmp_path):
    stdout = tmp_path / "stdout.jsonl"
    query = (
        "verdeckter Ermittler Liebesbeziehung Brief Gefangene Meinungsfreiheit "
        "Verfassungsbeschwerde Briefkontrolle -site:zjs-online.com"
    )
    event = {
        "type": "item.completed",
        "item": {
            "type": "web_search",
            "action": {"type": "search", "queries": [query]},
        },
    }
    stdout.write_text(json.dumps(event) + "\n", encoding="utf-8")

    report = source_audit(
        stdout,
        [],
        blocked_domains=["zjs-online.com"],
        protected_task_texts=[query.replace(" -site:zjs-online.com", "")],
    )

    assert report["blocked_domain_policy"]["passed"] is True
    assert report["search_leakage_audit"]["flagged"] is True
    # The flag is telemetry only and cannot contaminate the task.
    assert "passed" not in report["search_leakage_audit"]


def test_generic_legal_search_is_not_flagged(tmp_path):
    stdout = tmp_path / "stdout.jsonl"
    event = {
        "type": "item.completed",
        "item": {
            "type": "web_search",
            "action": {
                "type": "search",
                "queries": ["Art. 5 GG Gefangenenbrief BVerfG -site:zjs-online.com"],
            },
        },
    }
    stdout.write_text(json.dumps(event) + "\n", encoding="utf-8")

    report = source_audit(
        stdout,
        [],
        blocked_domains=["zjs-online.com"],
        forbidden_search_identifiers=["Examensübungsklausur: Falsche Liebe"],
        protected_task_texts=["Ein völlig anderer und charakteristischer Sachverhalt."],
    )

    assert report["blocked_domain_policy"]["passed"] is True
    assert report["search_leakage_audit"]["flagged"] is False


def test_run_summary_does_not_count_leakage_flag_as_contamination(tmp_path):
    run_dir = tmp_path / "run"
    task_dir = run_dir / "tasks" / "case"
    (task_dir / "submission").mkdir(parents=True)
    (task_dir / "work").mkdir()
    event = {
        "type": "item.completed",
        "item": {
            "type": "web_search",
            "action": {
                "type": "search",
                "queries": ["Musterlösung Art. 5 GG -site:zjs-online.com"],
            },
        },
    }
    (task_dir / "stdout.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")

    summary = write_run_summary(run_dir, ["zjs-online.com"])

    assert summary["n_contaminated_tasks"] == 0
    assert summary["contaminated_tasks"] == []
    assert summary["n_search_leakage_flagged_tasks"] == 1
    assert summary["search_leakage_flagged_tasks"] == ["case"]
