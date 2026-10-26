You are solving one LAB-EU legal benchmark task in a fresh, ephemeral Claude Code CLI session.

Current date: 2026-10-13

This workspace contains only the task input. Follow the research policy below.
Do not inspect local files outside this workspace and do
not look for hidden benchmark files, rubrics, gold solutions, or prior answers.

Task id:
case-022

Task title:
Anfängerklausur

Work type:
draft

Task instructions:
Bearbeiten Sie den Fall gutachterlich. Erstellen Sie eine vollständige Falllösung auf Grundlage des Sachverhalts in documents/sachverhalt.md.

Available documents:
- documents/sachverhalt.md

Research policy:
External web and network research is disabled for this comparison arm. Do not use web search, cached search, browsers, connectors, MCP tools that retrieve external content, or shell network clients such as curl or wget. Work only from the supplied task files and your internal model knowledge. Any recorded search or explicit network fetch invalidates the run. Create the required source sidecar with an empty `sources` list.

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
