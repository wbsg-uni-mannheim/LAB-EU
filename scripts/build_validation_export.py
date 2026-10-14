#!/usr/bin/env python3
"""Build the jurist validation export for de-core-45.

Writes one review packet per case (Markdown and Word) with the current rubric
text, the final per-criterion verdicts of the six study arms and the model
answers, plus a stratified random sample of content criteria as an Excel
workbook for the rubric validation.

Verdicts come from the published August 4 scores (Luna and Terra, Gemini as
tie-breaker). Criteria whose text changed after that judging show the judged
wording next to the current one. No API calls.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

REPO_ROOT = Path(__file__).resolve().parents[1]
TASKSET = REPO_ROOT / "studies" / "de-core-45" / "taskset.jsonl"
JUDGED_COMMIT = "1f5be8a"  # task/rubric snapshot of the August 4 judging
SEED = 20261007
EXPORT_DATE = "7. Oktober 2026"

ARMS = (
    ("Sol", "Agent", "agent-gpt-5.6-sol-high/20260730T221733Z"),
    ("Sol", "Baseline", "baseline-gpt-5.6-sol-high/20260730T221734Z"),
    ("Terra", "Agent", "agent-gpt-5.6-terra-high/20260730T221733Z"),
    ("Terra", "Baseline", "baseline-gpt-5.6-terra-high/20260730T221744Z"),
    ("DeepSeek", "Agent", "agent-deepseek-v4-pro-medium/20260730T214602Z"),
    ("DeepSeek", "Baseline", "baseline-deepseek-v4-pro/20260730T221734Z"),
)
AREAS = {
    "oeffentliches-recht": "Öffentliches Recht",
    "strafrecht": "Strafrecht",
    "zivilrecht": "Zivilrecht",
}
FUNCTIONS = {
    "legal_basis": "Rechtsgrundlage",
    "rule_statement": "Obersatz/Definition",
    "application": "Subsumtion",
    "argumentation": "Argumentation",
    "conclusion": "Ergebnis",
    "structure": "Aufbau",
    "form_citation": "Zitierweise",
}

# Whole case: the stored solver prompts still ask about M, the task asks about H.
EXCLUDED_TASKS = {
    "de/oeffentliches-recht/verwaltungsrecht/anfechtungsklage/fall-02-anfechtungsklage-bei-nebenbestimmungen":
        "Eingabeproblem: Die gespeicherten Aufgabenstellungen der Läufe fragen nach M, die aktuelle Aufgabe nach H.",
}
# Single criteria: the judge did not see the KCanG excerpt (file not found).
EXCLUDED_CRITERIA = {
    ("de/zivilrecht/schuldrecht/fortgeschrittenenklausur-wertpapier-werkstatt-und-weed", cid):
        "Quelle fehlte beim Bewerten: Der KCanG-Auszug war für den Judge nicht auffindbar."
    for cid in ("C-032", "C-033")
}


@dataclass
class Case:
    task_id: str
    task_dir: Path
    number: str
    packet_dir: str
    task: dict
    rubric: dict
    judged: dict[str, str]
    scores: dict[str, dict] = field(default_factory=dict)  # arm label -> scores.json
    submissions: dict[str, str] = field(default_factory=dict)

    @property
    def area(self) -> str:
        return AREAS[self.task_id.split("/")[1]]

    @property
    def title(self) -> str:
        return self.task["title"]


def arm_label(arm: tuple[str, str, str]) -> str:
    return f"{arm[0]} · {arm[1]}"


def stars(n: int | None) -> str:
    return "★" * int(n or 0)


def git_show(path: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "show", f"{JUDGED_COMMIT}:{path}"], cwd=REPO_ROOT, text=True
        )
    except subprocess.CalledProcessError:
        return None


def load_cases(runs_root: Path, packet_map: Path) -> list[Case]:
    mapping = {}
    for line in packet_map.read_text().splitlines():
        packet_dir, number, task_id = line.split("\t")
        mapping[task_id.strip()] = (number, packet_dir)
    cases = []
    for line in TASKSET.read_text().splitlines():
        entry = json.loads(line)
        task_dir = REPO_ROOT / entry["task_dir"]
        rubric = json.loads((task_dir / "evals" / "rubric.json").read_text())
        old = json.loads(git_show(f"{entry['task_dir']}/evals/rubric.json") or "{}")
        judged = {c["id"]: c["match_criteria"] for c in old.get("criteria", [])}
        number, packet_dir = mapping[entry["task_id"]]
        case = Case(
            entry["task_id"], task_dir, number, packet_dir,
            json.loads((task_dir / "task.json").read_text()), rubric, judged,
        )
        run_name = entry["task_id"].replace("/", "__")
        for arm in ARMS:
            task_run = runs_root / arm[2] / "tasks" / run_name
            if (task_run / "scores.json").exists():
                case.scores[arm_label(arm)] = json.loads((task_run / "scores.json").read_text())
                parts = [p.read_text() for p in sorted((task_run / "submission").glob("*.md"))]
                case.submissions[arm_label(arm)] = "\n\n".join(parts)
        cases.append(case)
    return sorted(cases, key=lambda c: c.number)


def verdicts(case: Case) -> dict[str, dict[str, dict]]:
    """criterion id -> arm label -> final content result."""
    out: dict[str, dict[str, dict]] = {}
    for arm, score in case.scores.items():
        for result in score["criteria_results"]:
            out.setdefault(result["id"], {})[arm] = result
    return out


def changed(case: Case, crit: dict) -> bool:
    old = case.judged.get(crit["id"])
    return old is not None and old != crit["match_criteria"]


def embed(text: str, by: int, prefix: str) -> str:
    """Demote headings and give footnotes a section prefix so they stay unique."""
    def repl(m: re.Match) -> str:
        return "#" * min(6, len(m.group(1)) + by) + " "
    text = re.sub(r"^(#{1,6})\s+", repl, text.strip(), flags=re.M)
    return re.sub(r"\[\^([^\]]+)\]", rf"[^{prefix}-\1]", text)


def mark(result: dict | None) -> str:
    if result is None:
        return "–"
    return "✓" if result["verdict"] == "pass" else "✗"


def vote_summary(result: dict) -> str:
    names = {"luna": "Luna", "terra": "Terra", "gemini-3.6-flash": "Gemini"}
    parts = []
    for vote in result.get("votes", []):
        name = names.get(vote["judge"]["name"], vote["judge"]["name"])
        parts.append(f"{name}: {'erfüllt' if vote['verdict'] == 'pass' else 'nicht erfüllt'}")
    return ", ".join(parts)


def packet_markdown(case: Case) -> str:
    crits = case.rubric["criteria"]
    by_crit = verdicts(case)
    source = case.task.get("source", {})
    lines = [
        f"# Prüfpaket {case.number}: {case.title}",
        "",
        f"{case.area} · Rubrikstand {EXPORT_DATE} · Urteile vom 4. August 2026",
        "",
        f"**Aufgabe:** {case.task['instructions']}",
        "",
    ]
    if source.get("fundstelle"):
        lines += [f"**Fundstelle:** {source['fundstelle']}", ""]
    if source.get("autoren"):
        lines += [f"**Autor:innen:** {source['autoren']}", ""]
    lines += [f"**Task-ID:** {case.task_id}", ""]
    if case.task_id in EXCLUDED_TASKS:
        lines += [f"> **Nicht Teil der Validierung.** {EXCLUDED_TASKS[case.task_id]}", ""]
    n_changed = sum(changed(case, c) for c in crits)
    lines += [
        "## Ergebnisübersicht",
        "",
        "Anteil erfüllter Kriterien, Inhalt und Gutachtenstil getrennt. Bewertet haben "
        "Luna und Terra, bei Uneinigkeit entschied Gemini.",
        "",
        "| Modell | Methode | Inhalt | Gutachtenstil | Tie-breaks |",
        "|---|---|---|---|---|",
    ]
    for arm in ARMS:
        score = case.scores.get(arm_label(arm))
        if score is None:
            lines.append(f"| {arm[0]} | {arm[1]} | keine Abgabe | – | – |")
            continue
        c = score["criteria_results"]
        s = score["style_results"]
        cp = sum(r["verdict"] == "pass" for r in c)
        sp = sum(r["verdict"] == "pass" for r in s)
        lines.append(
            f"| {arm[0]} | {arm[1]} | {round(100 * cp / len(c))} % ({cp}/{len(c)}) | "
            f"{round(100 * sp / len(s)) if s else 0} % ({sp}/{len(s)}) | {score.get('n_tiebreaks', 0)} |"
        )
    lines.append("")
    if n_changed:
        what = "Ein Kriterium wurde" if n_changed == 1 else f"{n_changed} Kriterien wurden"
        lines += [
            f"> {what} nach der Bewertung neu gefasst. Die Urteile beziehen sich dort auf die "
            "frühere Fassung, die jeweils mit angegeben ist.",
            "",
        ]

    lines += ["## 1. Sachverhalt", ""]
    docs = sorted((case.task_dir / "documents").glob("*.md"), key=lambda p: p.name != "sachverhalt.md")
    for doc in docs:
        if doc.name != "sachverhalt.md":
            lines += [f"### Anlage: {doc.stem}", ""]
        lines += [embed(doc.read_text(), 2, f"sv{doc.stem}"), ""]

    lines += ["## 2. Musterlösung", "", embed((case.task_dir / "evals" / "loesung.md").read_text(), 2, "ml"), ""]

    arm_labels = [arm_label(a) for a in ARMS]
    lines += [
        "## 3. Bewertungsrubrik",
        "",
        f"Die Rubrik enthält {len(crits)} binäre Kriterien. Ein Kriterium gilt nur dann als erfüllt, "
        "wenn die ERFÜLLT-Bedingung vorliegt und keine NICHT-ERFÜLLT-Bedingung greift. "
        "Gewichtung: ★★★ ergebnistragend, ★★ wichtig, ★ Detail.",
        "",
    ]
    for crit in crits:
        tags = crit.get("analysis_tags") or {}
        station = " › ".join(p for p in tags.get("station_path") or [] if p)
        func = FUNCTIONS.get(tags.get("function"), tags.get("function") or "–")
        row = by_crit.get(crit["id"], {})
        lines += [
            f"### {crit['id']} · {crit['title']}",
            "",
            f"Gewichtung: {stars(crit.get('criticality'))} | Funktion: {func} | Prüfungsstation: {station or '–'}",
            "",
            crit["match_criteria"],
            "",
        ]
        if changed(case, crit):
            lines += [f"> **Bewertet wurde die frühere Fassung:** {case.judged[crit['id']]}", ""]
        if (case.task_id, crit["id"]) in EXCLUDED_CRITERIA:
            lines += [f"> **Nicht Teil der Validierung.** {EXCLUDED_CRITERIA[(case.task_id, crit['id'])]}", ""]
        lines += [
            "Urteile: " + " | ".join(f"{a.replace(' · ', ' ')} {mark(row.get(a))}" for a in arm_labels),
            "",
        ]

    lines += [
        "## 4. Urteilsübersicht",
        "",
        "✓ erfüllt, ✗ nicht erfüllt, – keine Abgabe. Ag = Agent, Ba = Baseline.",
        "",
        "| Kriterium | Gew. | Sol Ag | Sol Ba | Terra Ag | Terra Ba | DS Ag | DS Ba |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for crit in crits:
        row = by_crit.get(crit["id"], {})
        flag = " (neu gefasst)" if changed(case, crit) else ""
        lines.append(
            f"| {crit['id']} {crit['title']}{flag} | {stars(crit.get('criticality'))} | "
            + " | ".join(mark(row.get(a)) for a in arm_labels) + " |"
        )
    lines.append("")

    lines += ["## 5. Modellantworten", "", "Die Antworten sind unverändert aus den Läufen übernommen.", ""]
    for i, arm in enumerate(ARMS, 1):
        label = arm_label(arm)
        lines += [f"### 5.{i} {label}", ""]
        if label not in case.scores:
            lines += ["Keine Abgabe (Inhaltsfilter des Anbieters).", ""]
            continue
        fails = [r for r in case.scores[label]["criteria_results"] if r["verdict"] != "pass"]
        lines += ["#### Nicht erfüllte Kriterien mit Begründung des Judges", ""]
        if not fails:
            lines += ["Alle Kriterien erfüllt.", ""]
        for r in fails:
            tb = " (Tie-break)" if r.get("tiebreak_used") else ""
            lines += [f"- **{r['id']} · {r['title']}**{tb}: {r.get('reasoning') or '–'}"]
        lines += ["", "#### Falllösung", "", embed(case.submissions[label], 4, f"a{i}"), ""]
    return "\n".join(lines)


def solve_class(row: dict[str, dict]) -> tuple[int, int, str]:
    n = len(row)
    k = sum(r["verdict"] == "pass" for r in row.values())
    cls = "nie gelöst" if k == 0 else "immer gelöst" if k == n else "teilweise gelöst"
    return k, n, cls


def population(cases: list[Case]) -> tuple[list[dict], list[dict]]:
    pool, excluded = [], []
    for case in cases:
        by_crit = verdicts(case)
        for crit in case.rubric["criteria"]:
            k, n, cls = solve_class(by_crit[crit["id"]])
            item = {"case": case, "crit": crit, "row": by_crit[crit["id"]], "k": k, "n": n, "cls": cls}
            reason = EXCLUDED_TASKS.get(case.task_id) or EXCLUDED_CRITERIA.get((case.task_id, crit["id"]))
            if reason:
                excluded.append({**item, "reason": reason})
            else:
                pool.append(item)
    return pool, excluded


def stratified(pool: list[dict], n: int, rng: random.Random) -> list[dict]:
    """Proportional allocation over legal area x weight, largest remainder."""
    groups: dict[tuple[str, int], list[dict]] = {}
    for item in pool:
        groups.setdefault((item["case"].area, item["crit"].get("criticality") or 0), []).append(item)
    quotas = {a: n * len(g) / len(pool) for a, g in groups.items()}
    alloc = {a: math.floor(q) for a, q in quotas.items()}
    for a in sorted(quotas, key=lambda a: quotas[a] - alloc[a], reverse=True)[: n - sum(alloc.values())]:
        alloc[a] += 1
    picked = [item for a in sorted(groups) for item in rng.sample(groups[a], alloc[a])]
    rng.shuffle(picked)
    return picked


def ci_halfwidth(n: int, N: int, p: float = 0.9) -> float:
    return 1.96 * math.sqrt(p * (1 - p) / n) * math.sqrt((N - n) / (N - 1))


HEADER_FILL = PatternFill("solid", fgColor="DDDDDD")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")


def write_sheet(ws, headers: list[str], rows: list[list], widths: list[int], input_cols: int = 0) -> None:
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for row in rows:
        ws.append(row)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = w
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    if input_cols:
        for col in range(len(headers) - input_cols + 1, len(headers) + 1):
            for r in range(1, ws.max_row + 1):
                ws.cell(r, col).fill = INPUT_FILL
    ws.freeze_panes = "A2"


def build_workbook(cases: list[Case], out: Path, n_part1: int, n_total: int) -> dict:
    rng = random.Random(SEED)
    pool, excluded = population(cases)
    part1 = stratified(pool, n_part1, rng)
    taken = {id(x) for x in part1}
    part2 = stratified([x for x in pool if id(x) not in taken], n_total - n_part1, rng)
    sample = [(1, x) for x in part1] + [(2, x) for x in part2]

    wb = Workbook()
    guide = wb.active
    guide.title = "Anleitung"
    N = len(pool)
    text = [
        "Validierung der Rubriken: Stichprobe",
        "",
        f"Die Stichprobe umfasst {n_total} zufällig gezogene Inhaltskriterien aus {N} Kriterien der 45 Fälle. "
        "Gezogen wurde ohne Blick auf Fehler, geschichtet nach Rechtsgebiet und Gewichtung. "
        f"Teil 1 (Nr. 1 bis {n_part1}) ist für sich bereits eine vollständige Stichprobe. Teil 2 erweitert sie.",
        "",
        "Pro Zeile sind zwei Fragen zu beantworten (gelbe Spalten):",
        "1. Kriterium juristisch korrekt? ja = richtig, fallbezogen und fair prüfbar. teilweise = im Kern richtig, "
        "aber zu eng, zu weit oder unklar formuliert. nein = rechtlich falsch oder für den Fall unpassend.",
        "2. Urteil des Judges korrekt? Passt ERFÜLLT bzw. NICHT ERFÜLLT zur gezeigten Antwort und zum Kriteriumstext?",
        "Die Anmerkung ist frei. Bei teilweise oder nein bitte kurz begründen.",
        "",
        "Zu jeder Zeile wird die Antwort eines zufällig gewählten Laufs gezeigt, mit Urteil, Begründung und "
        "Belegstellen des Judges. Die vollständige Antwort steht im Prüfpaket des Falls (Ordner 45 Fälle, Abschnitt 5).",
        "",
        "Wurde ein Kriterium nach der Bewertung neu gefasst, steht in Spalte J die bewertete Fassung. "
        "Zu prüfen ist diese Fassung, die neue steht in Spalte K.",
        "",
        "Nicht Teil der Stichprobe: der Fall Anfechtungsklage bei Nebenbestimmungen (Eingabeproblem), zwei Kriterien "
        "von Wertpapier, Werkstatt und Weed (Quelle fehlte beim Bewerten) und die 15 Fälle des Zweiten Staatsexamens. "
        "Siehe Blatt Ausgeschlossen.",
        "",
        f"Zufallsstartwert: {SEED}. Bewertung vom 4. August 2026 (Luna und Terra, bei Uneinigkeit Gemini).",
    ]
    for line in text:
        guide.append([line])
    guide.column_dimensions["A"].width = 130
    for row in guide.iter_rows():
        row[0].alignment = Alignment(wrap_text=True, vertical="top")
    guide["A1"].font = Font(bold=True, size=14)

    ws = wb.create_sheet("Stichprobe")
    headers = [
        "Nr", "Teil", "Rechtsgebiet", "Prüfpaket", "Kriterium", "Titel", "Gewichtung", "Funktion",
        "Prüfungsstation", "Kriteriumstext (bewertete Fassung)", "Neue Fassung (falls geändert)",
        "Gelöst von", "Lösungsklasse", "Gezeigte Antwort", "Urteil", "Stimmen", "Begründung des Judges",
        "Belegstellen aus der Antwort",
        "Kriterium juristisch korrekt?", "Urteil korrekt?", "Anmerkung",
    ]
    rows = []
    for nr, (part, item) in enumerate(sample, 1):
        case, crit, row = item["case"], item["crit"], item["row"]
        arm = rng.choice(sorted(row))
        result = row[arm]
        tags = crit.get("analysis_tags") or {}
        is_changed = changed(case, crit)
        rows.append([
            nr, part, case.area, f"{case.number} {case.title}", crit["id"], crit["title"],
            stars(crit.get("criticality")), FUNCTIONS.get(tags.get("function"), tags.get("function") or ""),
            " › ".join(p for p in tags.get("station_path") or [] if p),
            case.judged[crit["id"]] if is_changed else crit["match_criteria"],
            crit["match_criteria"] if is_changed else "",
            f"{item['k']}/{item['n']}", item["cls"], arm,
            "erfüllt" if result["verdict"] == "pass" else "nicht erfüllt",
            vote_summary(result), result.get("reasoning") or "",
            "\n".join(f"„{e}“" for e in result.get("evidence") or []),
            "", "", "",
        ])
    write_sheet(ws, headers, rows,
                [5, 5, 14, 28, 9, 28, 8, 12, 30, 60, 30, 8, 14, 16, 12, 24, 50, 50, 14, 14, 40], input_cols=3)
    ws.auto_filter.ref = ws.dimensions
    for col, options in (("S", '"ja,teilweise,nein"'), ("T", '"ja,nein,unklar"')):
        dv = DataValidation(type="list", formula1=options, allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{len(rows) + 1}")

    dist = wb.create_sheet("Verteilung")
    classes = ["nie gelöst", "teilweise gelöst", "immer gelöst"]
    s1 = [x for p, x in sample if p == 1]
    s_all = [x for _, x in sample]

    def share(items: list[dict], key, value) -> str:
        c = sum(key(x) == value for x in items)
        return f"{c} ({100 * c / len(items):.1f} %)".replace(".", ",")

    drows = [["Lösungsklasse (über die sechs Läufe)", "", "", ""]]
    for cls in classes:
        drows.append([cls, share(pool, lambda x: x["cls"], cls), share(s1, lambda x: x["cls"], cls),
                      share(s_all, lambda x: x["cls"], cls)])
    drows.append(["Rechtsgebiet", "", "", ""])
    for area in AREAS.values():
        drows.append([area, share(pool, lambda x: x["case"].area, area), share(s1, lambda x: x["case"].area, area),
                      share(s_all, lambda x: x["case"].area, area)])
    drows.append(["Gewichtung", "", "", ""])
    for crit in (3, 2, 1):
        key = lambda x: x["crit"].get("criticality")  # noqa: E731
        drows.append([stars(crit), share(pool, key, crit), share(s1, key, crit), share(s_all, key, crit)])
    drows += [
        ["", "", "", ""],
        ["Genauigkeit (95-%-Konfidenzintervall bei 90 % Zustimmung, mit Endlichkeitskorrektur)", "", "", ""],
        [f"Teil 1 (n = {n_part1})", "", f"± {100 * ci_halfwidth(n_part1, N):.1f} Prozentpunkte".replace(".", ","), ""],
        [f"Teil 1 und 2 (n = {n_total})", "", "", f"± {100 * ci_halfwidth(n_total, N):.1f} Prozentpunkte".replace(".", ",")],
    ]
    write_sheet(dist, ["Merkmal", f"Grundgesamtheit (N = {N})", f"Teil 1 (n = {n_part1})",
                       f"Teil 1 und 2 (n = {n_total})"], drows, [60, 24, 24, 24])
    for row in dist.iter_rows(min_row=2):
        if row[1].value == "" and row[0].value:
            row[0].font = Font(bold=True)

    exc = wb.create_sheet("Ausgeschlossen")
    erows = [[x["case"].title, x["crit"]["id"], x["crit"]["title"], x["reason"]] for x in excluded]
    erows.append(["15 Fälle Zweites Staatsexamen", "alle", "", "Nicht Teil dieses Benchmarks (Lizenz offen)."])
    write_sheet(exc, ["Fall", "Kriterium", "Titel", "Grund"], erows, [45, 10, 45, 70])

    wb.save(out)
    return {
        "population": N, "excluded": len(excluded),
        "pool": Counter(x["cls"] for x in pool), "part1": Counter(x["cls"] for x in s1),
        "all": Counter(x["cls"] for x in s_all),
        "changed_in_sample": sum(changed(x["case"], x["crit"]) for x in s_all),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", type=Path, default=REPO_ROOT / "runs",
                        help="Directory with the six published study arms")
    parser.add_argument("--packet-map", type=Path,
                        default=REPO_ROOT / "studies" / "de-core-45" / "validation" / "packet_map.tsv",
                        help="TSV: packet folder, packet number, task id")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--part1", type=int, default=100)
    parser.add_argument("--total", type=int, default=250)
    parser.add_argument("--no-docx", action="store_true")
    args = parser.parse_args()

    cases = load_cases(args.runs_root, args.packet_map)
    for case in cases:
        target = args.output_dir / case.packet_dir
        target.mkdir(parents=True, exist_ok=True)
        md = target / "Pruefpaket.md"
        md.write_text(packet_markdown(case))
        if not args.no_docx:
            subprocess.run(["pandoc", str(md), "-o", str(target / "Pruefpaket.docx")], check=True)
    stats = build_workbook(cases, args.output_dir / "00_Validierung_Stichprobe.xlsx", args.part1, args.total)
    print(json.dumps({k: dict(v) if isinstance(v, Counter) else v for k, v in stats.items()},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
