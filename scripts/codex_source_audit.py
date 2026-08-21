#!/usr/bin/env python3
"""Extract reproducible source-use reports from Codex CLI run artifacts."""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import unicodedata
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

URL_RE = re.compile(r"https?://[^\s\"'<>`)\\]+")
DEFAULT_BLOCKED_DOMAINS = ("zjs-online.com",)
SOLUTION_SEEKING_TERMS = (
    "musterlösung",
    "musterloesung",
    "lösungsvorschlag",
    "loesungsvorschlag",
    "examensübungsklausur",
    "examensuebungsklausur",
)


def normalize_domain(value: str) -> str:
    value = value.strip().lower()
    if "://" in value:
        value = urlsplit(value).netloc
    return value.strip(".").removeprefix("www.")


def normalize_blocked_domains(values: Iterable[str]) -> list[str]:
    return sorted({domain for value in values if (domain := normalize_domain(value))})


def host_matches_blocked_domain(host: str, blocked_domain: str) -> bool:
    host = normalize_domain(host)
    return host == blocked_domain or host.endswith(f".{blocked_domain}")


def negative_site_filter(query: str, blocked_domain: str) -> bool:
    pattern = rf"-site:\s*(?:www\.)?{re.escape(blocked_domain)}(?:\b|$)"
    return re.search(pattern, query, flags=re.IGNORECASE) is not None


def positive_domain_reference(query: str, blocked_domain: str) -> bool:
    without_filter = re.sub(
        rf"-site:\s*(?:www\.)?{re.escape(blocked_domain)}(?:\b|$)",
        "",
        query,
        flags=re.IGNORECASE,
    )
    return (
        re.search(
            rf"(?:^|[^a-z0-9-])(?:www\.)?{re.escape(blocked_domain)}(?:\b|$)",
            without_filter,
            flags=re.IGNORECASE,
        )
        is not None
    )


def normalize_search_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"[\w§]+", value, flags=re.UNICODE))


def search_guard_material(task_dir: pathlib.Path) -> tuple[list[str], list[str]]:
    """Return hidden identifiers and task text that searches must not reproduce."""
    task_path = task_dir / "task.json"
    try:
        task = json.loads(task_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        task = {}

    identifiers: set[str] = set()
    title = task.get("title")
    if isinstance(title, str) and title.strip():
        identifiers.add(title.strip())
    identifiers.add(task_dir.name.replace("-", " "))
    source = task.get("source") if isinstance(task.get("source"), dict) else {}
    for key in ("fundstelle", "autoren"):
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            identifiers.add(value.strip())
    for tag in task.get("tags") or []:
        if isinstance(tag, str) and (
            "zjs" in tag.casefold() or any(char.isdigit() for char in tag)
        ):
            identifiers.add(tag.strip())

    protected_texts: list[str] = []
    documents = task_dir / "documents"
    if documents.is_dir():
        for path in sorted(documents.rglob("*")):
            if path.is_file():
                protected_texts.append(
                    path.read_text(encoding="utf-8", errors="replace")
                )
    return sorted(identifiers), protected_texts


def quoted_fragments(query: str) -> list[str]:
    fragments: list[str] = []
    for pattern in (r'"([^"\n]+)"', r"„([^“\n]+)“", r"“([^”\n]+)”"):
        fragments.extend(re.findall(pattern, query))
    return fragments


def is_legal_citation(value: str) -> bool:
    normalized = normalize_search_text(value)
    return bool(
        re.match(r"^(?:art|§|§§)\b", normalized)
        or re.search(r"\b\d+\s+bvr\s+\d+", normalized)
        or re.match(r"^bverfge\s+\d+", normalized)
    )


def search_leakage_flags(
    queries: Iterable[str], identifiers: Iterable[str], protected_texts: Iterable[str]
) -> list[dict[str, str]]:
    normalized_documents = [normalize_search_text(text) for text in protected_texts]
    normalized_identifiers = [
        (identifier, normalize_search_text(identifier))
        for identifier in identifiers
        if normalize_search_text(identifier)
    ]
    violations: list[dict[str, str]] = []
    for query in sorted(set(queries)):
        normalized_query = normalize_search_text(query)
        for term in SOLUTION_SEEKING_TERMS:
            if normalize_search_text(term) in normalized_query:
                violations.append(
                    {"kind": "solution-seeking-term", "evidence": query, "match": term}
                )
        for identifier, normalized_identifier in normalized_identifiers:
            if normalized_identifier in normalized_query:
                violations.append(
                    {"kind": "task-identifier", "evidence": query, "match": identifier}
                )
        for fragment in quoted_fragments(query):
            normalized_fragment = normalize_search_text(fragment)
            if (
                len(normalized_fragment) >= 8
                and not is_legal_citation(fragment)
                and any(
                    normalized_fragment in document for document in normalized_documents
                )
            ):
                violations.append(
                    {
                        "kind": "quoted-task-fragment",
                        "evidence": query,
                        "match": fragment,
                    }
                )
        query_tokens = normalized_query.split()
        for size in range(min(12, len(query_tokens)), 7, -1):
            copied = next(
                (
                    " ".join(query_tokens[start : start + size])
                    for start in range(len(query_tokens) - size + 1)
                    if any(
                        " ".join(query_tokens[start : start + size]) in document
                        for document in normalized_documents
                    )
                ),
                None,
            )
            if copied:
                violations.append(
                    {"kind": "copied-task-fragment", "evidence": query, "match": copied}
                )
                break
    unique = {
        (item["kind"], item["evidence"], item["match"]): item for item in violations
    }
    return list(unique.values())


def normalize_url(value: str) -> str:
    value = html.unescape(value).rstrip(".,;:!?]}›")
    parsed = urlsplit(value)
    return urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, parsed.query, "")
    )


def urls_in_text(text: str) -> set[str]:
    return {normalize_url(match.group(0)) for match in URL_RE.finditer(text)}


def iter_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_dicts(child)


def load_events(path: pathlib.Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.is_file():
        return events
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def reported_sources(path: pathlib.Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    rows = payload.get("sources", []) if isinstance(payload, dict) else []
    result: dict[str, dict[str, str]] = {}
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("url"), str):
            continue
        urls = urls_in_text(row["url"])
        if len(urls) != 1:
            continue
        url = next(iter(urls))
        result[url] = {
            "title": str(row.get("title", "")).strip(),
            "purpose": str(row.get("purpose", "")).strip(),
        }
    return result


def source_audit(
    stdout_path: pathlib.Path,
    deliverables: list[pathlib.Path],
    reported_sources_path: pathlib.Path | None = None,
    blocked_domains: Iterable[str] = (),
    forbidden_search_identifiers: Iterable[str] = (),
    protected_task_texts: Iterable[str] = (),
    web_search_allowed: bool = True,
) -> dict[str, Any]:
    blocked_domains = normalize_blocked_domains(blocked_domains)
    search_queries: set[str] = set()
    filter_required_queries: set[str] = set()
    visited_urls: set[str] = set()
    cited_urls: set[str] = set()
    visit_evidence: dict[str, set[str]] = {}
    web_search_event_count = 0

    for event in load_events(stdout_path):
        item = event.get("item") if isinstance(event.get("item"), dict) else event
        item_type = str(item.get("type", "")).lower()
        if item_type == "web_search":
            web_search_event_count += 1
            action = item.get("action") if isinstance(item.get("action"), dict) else {}
            queries = action.get("queries")
            if isinstance(queries, list) and queries:
                normalized_queries = {
                    str(query).strip() for query in queries if str(query).strip()
                }
                search_queries.update(normalized_queries)
                if str(action.get("type", "")).lower() == "search":
                    filter_required_queries.update(normalized_queries)
            else:
                normalized_queries = set()
                for candidate in [action.get("query"), item.get("query")]:
                    if isinstance(candidate, str) and candidate.strip():
                        normalized_queries.add(candidate.strip())
                search_queries.update(normalized_queries)
                if str(action.get("type", "")).lower() == "search":
                    filter_required_queries.update(normalized_queries)
            # Only URL-valued fields belonging to the action itself count as a
            # page open. Search-result URLs are not exposed by Codex JSONL and
            # must not be guessed from snippets.
            for data in iter_dicts(action):
                for key, value in data.items():
                    if key.lower() in {"url", "uri", "link"} and isinstance(value, str):
                        for url in urls_in_text(value):
                            visited_urls.add(url)
                            visit_evidence.setdefault(url, set()).add("web_search open")
        elif item_type == "command_execution":
            command = item.get("command")
            if isinstance(command, str) and re.search(
                r"(?:^|[;&|\s])(curl|wget|http|https)(?:\s|$)", command
            ):
                for url in urls_in_text(command):
                    visited_urls.add(url)
                    visit_evidence.setdefault(url, set()).add("command fetch")

    for path in deliverables:
        if path.is_file():
            cited_urls.update(
                urls_in_text(path.read_text(encoding="utf-8", errors="replace"))
            )

    reported = reported_sources(reported_sources_path) if reported_sources_path else {}
    used_urls = cited_urls | set(reported)
    all_urls = sorted(visited_urls | used_urls)
    policy_violations: list[dict[str, str]] = []
    for blocked_domain in blocked_domains:
        for query in sorted(filter_required_queries):
            if not negative_site_filter(query, blocked_domain):
                policy_violations.append(
                    {
                        "domain": blocked_domain,
                        "kind": "missing-negative-filter",
                        "evidence": query,
                    }
                )
            if positive_domain_reference(query, blocked_domain):
                policy_violations.append(
                    {
                        "domain": blocked_domain,
                        "kind": "positive-search-target",
                        "evidence": query,
                    }
                )
        for evidence_kind, urls in (
            ("opened-or-fetched-url", visited_urls),
            ("used-or-cited-url", used_urls),
        ):
            for url in sorted(urls):
                if host_matches_blocked_domain(urlsplit(url).netloc, blocked_domain):
                    policy_violations.append(
                        {
                            "domain": blocked_domain,
                            "kind": evidence_kind,
                            "evidence": url,
                        }
                    )
    leakage_flags = search_leakage_flags(
        filter_required_queries,
        forbidden_search_identifiers,
        protected_task_texts,
    )
    web_access_violations: list[dict[str, str]] = []
    if not web_search_allowed:
        if web_search_event_count:
            web_access_violations.append(
                {
                    "kind": "web-search-event",
                    "evidence": f"{web_search_event_count} web_search event(s)",
                }
            )
        for url in sorted(visited_urls):
            web_access_violations.append(
                {"kind": "explicit-network-fetch", "evidence": url}
            )
    sources = []
    for url in all_urls:
        sources.append(
            {
                "url": url,
                "domain": urlsplit(url).netloc,
                "visited": url in visited_urls,
                "used": url in used_urls,
                "cited_in_deliverable": url in cited_urls,
                "reported_title": reported.get(url, {}).get("title", ""),
                "reported_purpose": reported.get(url, {}).get("purpose", ""),
                "visit_evidence": sorted(visit_evidence.get(url, set())),
            }
        )
    return {
        "schema_version": "0.2",
        "method_note": (
            "Used means the URL appears in the selected deliverable or in Codex's required "
            ".codex-used-sources.json sidecar. Open/Fetch means Codex additionally recorded an "
            "explicit page-open action or HTTP fetch command. Search-result URLs are not "
            "invented from snippets and are not counted unless one of those records exists."
        ),
        "counts": {
            "search_queries": len(search_queries),
            "recorded_open_or_fetch_urls": len(visited_urls),
            "used_urls": len(used_urls),
            "cited_urls": len(cited_urls),
            "unique_used_source_urls": len(used_urls),
            "unique_used_source_domains": len(
                {urlsplit(url).netloc for url in used_urls}
            ),
            "unique_source_urls": len(all_urls),
            "unique_source_domains": len({urlsplit(url).netloc for url in all_urls}),
            "blocked_domain_violations": len(policy_violations),
            "search_leakage_flags": len(leakage_flags),
            "web_access_violations": len(web_access_violations),
        },
        "blocked_domain_policy": {
            "blocked_domains": blocked_domains,
            "passed": not policy_violations,
            "violations": policy_violations,
        },
        "web_access_policy": {
            "web_search_allowed": web_search_allowed,
            "passed": not web_access_violations,
            "violations": web_access_violations,
        },
        "search_leakage_audit": {
            "enforcement": "informational-only",
            "flagged": bool(leakage_flags),
            "flags": leakage_flags,
        },
        "search_queries": sorted(search_queries),
        "sources": sources,
    }


def render_task_markdown(report: dict[str, Any], task_id: str) -> str:
    counts = report["counts"]
    lines = [
        "# Quellen- und Webrecherche-Audit",
        "",
        f"**Fall:** `{task_id}`",
        "",
        "## Zählung",
        "",
        f"- Suchanfragen: **{counts['search_queries']}**",
        f"- Als verwendet belegte URLs: **{counts['used_urls']}**",
        f"- Explizit als Open/Fetch protokollierte URLs: **{counts['recorded_open_or_fetch_urls']}**",
        f"- In der Lösung zitierte URLs: **{counts['cited_urls']}**",
        f"- Eindeutige verwendete Quellen-URLs: **{counts['unique_used_source_urls']}**",
        f"- Eindeutige verwendete Domains: **{counts['unique_used_source_domains']}**",
        f"- Alle im Audit beobachteten URLs: **{counts['unique_source_urls']}**",
        f"- Verstöße gegen die Domain-Sperre: **{counts['blocked_domain_violations']}**",
        f"- Verstöße gegen den Webzugriffsmodus: **{counts['web_access_violations']}**",
        f"- Informativ markierte Suchanfragen: **{counts['search_leakage_flags']}**",
        "",
        "## Domain-Sperre",
        "",
        "- Gesperrte Domains: "
        + (
            ", ".join(
                f"`{domain}`"
                for domain in report["blocked_domain_policy"]["blocked_domains"]
            )
            or "_keine_"
        ),
        f"- Status: **{'bestanden' if report['blocked_domain_policy']['passed'] else 'KONTAMINIERT'}**",
        "- Webzugriffsmodus: "
        + (
            "erlaubt"
            if report["web_access_policy"]["web_search_allowed"]
            else "deaktiviert"
        ),
        f"- Webzugriffs-Audit: **{'bestanden' if report['web_access_policy']['passed'] else 'KONTAMINIERT'}**",
        "- Such-Leakage-Audit: **nur Hinweis; keine Verwerfung**",
        "",
        "## Quellen",
        "",
        "| Quelle | Domain | verwendet | Open/Fetch protokolliert | in Lösung zitiert | Zweck/Nachweis |",
        "|---|---|:---:|:---:|:---:|---|",
    ]
    if report["sources"]:
        for source in report["sources"]:
            lines.append(
                f"| [Link]({source['url']}) | `{source['domain']}` | "
                f"{'ja' if source['used'] else 'nein'} | "
                f"{'ja' if source['visited'] else 'nein'} | "
                f"{'ja' if source['cited_in_deliverable'] else 'nein'} | "
                f"{source['reported_purpose'] or ', '.join(source['visit_evidence']) or 'Deliverable'} |"
            )
    else:
        lines.append("| _Keine URL im Audit nachweisbar_ |  |  |  |  |  |")

    if report["blocked_domain_policy"]["violations"]:
        lines.extend(["", "### Verstöße", ""])
        for violation in report["blocked_domain_policy"]["violations"]:
            lines.append(
                f"- `{violation['kind']}` für `{violation['domain']}`: "
                f"{violation['evidence']}"
            )

    if report["web_access_policy"]["violations"]:
        lines.extend(["", "### Verstöße gegen den Webzugriffsmodus", ""])
        for violation in report["web_access_policy"]["violations"]:
            lines.append(f"- `{violation['kind']}`: {violation['evidence']}")

    if report["search_leakage_audit"]["flags"]:
        lines.extend(["", "### Informative Such-Leakage-Flags", ""])
        lines.append(
            "Diese Treffer sind Review-Hinweise. Sie kontaminieren oder verwerfen den Fall nicht."
        )
        lines.append("")
        for violation in report["search_leakage_audit"]["flags"]:
            lines.append(
                f"- `{violation['kind']}` (`{violation['match']}`): "
                f"{violation['evidence']}"
            )

    lines.extend(["", "## Suchanfragen", ""])
    if report["search_queries"]:
        lines.extend(f"- {query}" for query in report["search_queries"])
    else:
        lines.append("_Keine Suchanfrage im Eventstream aufgezeichnet._")
    lines.extend(
        [
            "",
            "## Methodische Grenze",
            "",
            report["method_note"],
            "",
        ]
    )
    return "\n".join(lines)


def write_task_report(
    task_run_dir: pathlib.Path,
    task_id: str | None = None,
    blocked_domains: Iterable[str] = (),
    web_search_allowed: bool = True,
) -> dict[str, Any]:
    metadata_path = task_run_dir / "metadata.json"
    task_id = task_id or task_run_dir.name
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        task_id = str(metadata.get("task_id", task_id))
    deliverables = sorted((task_run_dir / "submission").rglob("*"))
    deliverables = [path for path in deliverables if path.is_file()]
    source_task_dir_path = task_run_dir / "input_task_dir.txt"
    if source_task_dir_path.is_file():
        source_task_dir = pathlib.Path(
            source_task_dir_path.read_text(encoding="utf-8").strip()
        )
        identifiers, protected_texts = search_guard_material(source_task_dir)
    else:
        identifiers, protected_texts = [], []
    report = source_audit(
        task_run_dir / "stdout.jsonl",
        deliverables,
        task_run_dir / "work" / ".codex-used-sources.json",
        blocked_domains,
        identifiers,
        protected_texts,
        web_search_allowed,
    )
    report["task_id"] = task_id
    (task_run_dir / "sources.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (task_run_dir / "sources.md").write_text(
        render_task_markdown(report, task_id), encoding="utf-8"
    )
    return report


def write_run_summary(
    run_dir: pathlib.Path,
    blocked_domains: Iterable[str] | None = None,
    web_search_allowed: bool | None = None,
) -> dict[str, Any]:
    if blocked_domains is None or web_search_allowed is None:
        manifest_path = run_dir / "manifest.json"
        manifest = (
            json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest_path.is_file()
            else {}
        )
        if blocked_domains is None:
            blocked_domains = manifest.get("blocked_domains") or []
        if web_search_allowed is None:
            web_search_allowed = manifest.get("live_web_search", True)
    reports = []
    for task_dir in sorted((run_dir / "tasks").iterdir()):
        if task_dir.is_dir() and (task_dir / "stdout.jsonl").is_file():
            reports.append(
                write_task_report(
                    task_dir,
                    blocked_domains=blocked_domains,
                    web_search_allowed=web_search_allowed,
                )
            )

    url_cases: dict[str, set[str]] = {}
    domain_cases: dict[str, set[str]] = {}
    total_queries = 0
    contaminated_cases: list[str] = []
    for report in reports:
        task_id = report["task_id"]
        total_queries += report["counts"]["search_queries"]
        if (
            not report["blocked_domain_policy"]["passed"]
            or not report["web_access_policy"]["passed"]
        ):
            contaminated_cases.append(task_id)
        for source in report["sources"]:
            if not source["used"]:
                continue
            url_cases.setdefault(source["url"], set()).add(task_id)
            domain_cases.setdefault(source["domain"], set()).add(task_id)

    summary = {
        "schema_version": "0.2",
        "n_tasks": len(reports),
        "total_search_queries": total_queries,
        "unique_source_urls": len(url_cases),
        "unique_source_domains": len(domain_cases),
        "blocked_domains": normalize_blocked_domains(blocked_domains),
        "n_contaminated_tasks": len(contaminated_cases),
        "contaminated_tasks": sorted(contaminated_cases),
        "n_search_leakage_flagged_tasks": sum(
            bool(report["search_leakage_audit"]["flagged"]) for report in reports
        ),
        "search_leakage_flagged_tasks": sorted(
            report["task_id"]
            for report in reports
            if report["search_leakage_audit"]["flagged"]
        ),
        "sources": [
            {
                "url": url,
                "domain": urlsplit(url).netloc,
                "case_count": len(cases),
                "cases": sorted(cases),
            }
            for url, cases in sorted(url_cases.items())
        ],
        "domains": [
            {"domain": domain, "case_count": len(cases), "cases": sorted(cases)}
            for domain, cases in sorted(domain_cases.items())
        ],
    }
    (run_dir / "source-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Quellenübersicht des Codex-Runs",
        "",
        f"- Fälle mit Audit: **{summary['n_tasks']}**",
        f"- Suchanfragen insgesamt: **{summary['total_search_queries']}**",
        f"- Eindeutige Quellen-URLs: **{summary['unique_source_urls']}**",
        f"- Eindeutige Domains: **{summary['unique_source_domains']}**",
        f"- Durch Domain-Sperre kontaminierte Fälle: **{summary['n_contaminated_tasks']}**",
        f"- Fälle mit informativem Leakage-Flag: **{summary['n_search_leakage_flagged_tasks']}**",
        "",
        "## Quellen über alle Fälle",
        "",
        "| Quelle | Domain | Fälle |",
        "|---|---|---:|",
    ]
    for source in summary["sources"]:
        lines.append(
            f"| [Link]({source['url']}) | `{source['domain']}` | {source['case_count']} |"
        )
    if not summary["sources"]:
        lines.append("| _Keine URL im Audit nachweisbar_ |  | 0 |")
    (run_dir / "source-summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate source reports for an existing Codex run."
    )
    parser.add_argument("run_dir", type=pathlib.Path)
    parser.add_argument(
        "--blocked-domain",
        action="append",
        dest="blocked_domains",
        help="Domain to prohibit and audit. Repeat for multiple domains.",
    )
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    if not (run_dir / "tasks").is_dir():
        raise SystemExit(f"Not a Codex run directory: {run_dir}")
    summary = write_run_summary(run_dir, args.blocked_domains)
    print(
        f"Wrote source audit for {summary['n_tasks']} task(s): "
        f"{summary['unique_source_urls']} unique URL(s), "
        f"{summary['unique_source_domains']} domain(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
