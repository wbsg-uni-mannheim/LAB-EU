You are solving one LAB-EU legal benchmark task in a fresh, ephemeral Codex CLI session.

Current date: 2026-08-06

This workspace contains only the task input. You may use every tool available in
this session, including live web search, to verify current law and authoritative
primary legal sources. Do not inspect local files outside this workspace and do
not look for hidden benchmark files, rubrics, gold solutions, or prior answers.

Task id:
case-038

Task title:
Juristische Fallbearbeitung

Work type:
draft

Task instructions:
Bearbeiten Sie den Fall gutachterlich. Erstellen Sie eine vollständige Falllösung auf Grundlage des Sachverhalts in documents/sachverhalt.md.

Available documents:
- documents/sachverhalt.md

Blocked research domains:
- zjs-online.com

Do not search, open, fetch, cite, or use information from any blocked domain.
Append every blocked domain to every web search as a negative filter in the
form `-site:blocked.example`. Ignore blocked-domain results that appear despite
the filter. Using or positively targeting a blocked domain invalidates the run.

You may research the facts of the case, including searches using distinctive
factual details. The harness may flag searches that resemble task identifiers,
solution searches, or copied task wording for later human review; those flags
are informational and do not invalidate the run. No domain allowlist applies.

Required deliverable:
fallloesung.md

Write the final answer as Markdown and save it as exactly "fallloesung.md" in
the workspace root. Your final response must contain the same complete legal
document, without a preamble, progress report, meta commentary, or closing
remarks, so it can be used as a fallback if the file write fails.

Before your final response, also save `.codex-used-sources.json` in the
workspace root. It must be valid JSON with this shape:
{"sources":[{"url":"https://...","title":"...","purpose":"..."}]}
Include every external webpage that you substantively relied on, but do not
include mere search-result pages or pages you discarded without using. This is
an audit sidecar and must not be mentioned in the legal deliverable.

Write in the same language as the task instructions and documents unless the
instructions require a different language. The deliverable must be complete
and self-contained. Use the legal reasoning style required by the task; for a
German case solution, use Gutachtenstil. Verify that cited provisions and any
time-sensitive legal claims are current. Where the supplied materials present
a question as settled by controlling high-court case law, follow that current
case-law path. Cite the provisions you rely on precisely.
