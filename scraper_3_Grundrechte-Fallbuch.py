#!/usr/bin/env python3
"""
scrape_grundrechte.py -- OpenRewi Grundrechte-Fallbuch -> LAB-EU task folders.
(See original docstring for two-stage design rationale.)

    python scrape_grundrechte.py --stage1-only
    python scrape_grundrechte.py --build-only
    python scrape_grundrechte.py
"""

import argparse, json, re, time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from markdownify import markdownify as md

API = "https://de.wikibooks.org/w/api.php"
UA = {"User-Agent": "LAB-EU-scraper/1.0 (research; uni-mannheim)"}
RAW_DIR = "raw_grundrechte"
OUT_ROOT = "out/tasks/de/grundrechte-fallbuch"

# All 14 real cases. "Fall 8" main entry actually uses page "Fall_8a"; the
# plain "Fall_8" page is the separate "vereinfacht" variant under
# Zusatzmaterial -- confirmed from the book's own TOC, not guessed.
CASES = [
    {"num": "1",  "name": "Kunstfreiheit",                                             "sv": "Fall_1",  "lo": "Fall_1_Lösung"},
    {"num": "2",  "name": "Berufsfreiheit",                                             "sv": "Fall_2",  "lo": "Fall_2_Lösung"},
    {"num": "3",  "name": "Handlungsfreiheit",                                          "sv": "Fall_3",  "lo": "Fall_3_Lösung"},
    {"num": "4",  "name": "Recht auf Gesundheit",                                       "sv": "Fall_4",  "lo": "Fall_4_Lösung"},
    {"num": "5",  "name": "Meinungsfreiheit",                                           "sv": "Fall_5",  "lo": "Fall_5_Lösung"},
    {"num": "6",  "name": "Versammlungsfreiheit",                                       "sv": "Fall_6",  "lo": "Fall_6_Lösung"},
    {"num": "7",  "name": "Allg. Persönlichkeitsrecht",                                 "sv": "Fall_7",  "lo": "Fall_7_Lösung"},
    {"num": "8",  "name": "Eigentumsfreiheit",                                          "sv": "Fall_8a", "lo": "Fall_8a_Lösung"},
    {"num": "9",  "name": "Religionsfreiheit",                                          "sv": "Fall_9",  "lo": "Fall_9_Lösung"},
    {"num": "10", "name": "Gleichheitsrechte",                                          "sv": "Fall_10", "lo": "Fall_10_Lösung"},
    {"num": "3a", "name": "Crashkurs I – Prüfung Freiheitsgrundrecht",                  "sv": "Fall_3a", "lo": "Fall_3a_Lösung"},
    {"num": "3b", "name": "Crashkurs II – Zulässigkeit der Verfassungsbeschwerde, Sonderfälle", "sv": "Fall_3b", "lo": "Fall_3b_Lösung"},
    {"num": "8v", "name": "Eigentumsfreiheit vereinfacht",                              "sv": "Fall_8",  "lo": "Fall_8_Lösung"},
    {"num": "9a", "name": "Religionsfreiheit vereinfacht",                              "sv": "Fall_9a", "lo": "Fall_9a_Lösung"},
]

BOOK_PREFIX = "OpenRewi/_Grundrechte-Fallbuch/_"

LICENSE_TMPL = (
    "Dieser Text steht unter der Lizenz CC BY-SA 4.0 "
    "(https://creativecommons.org/licenses/by-sa/4.0/deed.de). "
    "Er beruht auf dem Werk von {authors}, in: Petras/Valentiner (Hrsg.), "
    "Grundrechte: Klausur- und Examensfälle, ebenfalls veröffentlicht unter der "
    "Lizenz CC BY-SA 4.0. Für Änderungen ist allein der/die Urheber*in dieser "
    "Überarbeitung verantwortlich."

)
# ---- known heading -> role maps (Stage 2 classification only) ---- #
FACTS_PREFIXES = ("sachverhalt", "ausgangsfall", "abwandlung")
QUESTION_HEADINGS = {"fallfrage", "fallfragen"}
NOTE_HEADINGS = {"bearbeitungshinweis", "hinweis zur bearbeitung", "hinweis"}
EXCERPT_PREFIXES = ("auszug",)
EXCERPT_EXACT = {"gesetz", "gesetze"}
SV_SKIP_HEADINGS = {"(preamble)", "fußnoten"}
LO_SKIP_BODY_HEADINGS = {"(preamble)", "fußnoten"} # metadata / footnotes handled separately


# --------------------------------------------------------------------- #
# Stage 1
# --------------------------------------------------------------------- #
# Stage 1: fetch + structure (no interpretation)
def fetch_body(title):
    params = {"action": "parse", "page": title, "prop": "text",
              "format": "json", "formatversion": "2", "redirects": "1"}
    for attempt in range(5):
        r = requests.get(API, params=params, headers=UA, timeout=30)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 0)) or 5 * (attempt + 1)
            print(f"     [429] waiting {wait}s ({attempt+1}/5)"); time.sleep(wait); continue
        r.raise_for_status(); break
    else:
        raise RuntimeError("repeated 429s")
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("info", "API error"))
    soup = BeautifulSoup(data["parse"]["text"], "html.parser")
    body = soup.select_one(".mw-parser-output") or soup
    for sel in [".mw-editsection", "style", "link", ".navbox", ".noprint",
                ".mw-inputbox-centered", ".commentbox"]:
        for el in body.select(sel):
            el.decompose()
    for el in list(body.find_all(True)):
        if el.get_text(strip=True).startswith("Inhaltsverzeichnis des Buches"):
            el.decompose()
    return body


def extract_footnotes(body):
    """Replace <sup class=reference> with @@FNn@@ placeholders in place,
    return {n: definition_markdown}. Definitions list is removed from body."""
    definitions = {}
    for sup in body.select("sup.reference"):
        m = re.search(r"\d+", sup.get_text())
        if not m:
            sup.decompose(); continue
        sup.replace_with(NavigableString(f"@@FN{m.group(0)}@@"))
    ol = body.select_one("ol.references")
    if ol:
        for i, li in enumerate(ol.find_all("li", recursive=False), 1):
            n = str(i)
            mid = re.search(r"cite_note-(?:.*?-)?(\d+)$", li.get("id", ""))
            if mid:
                n = mid.group(1)
            span = li.select_one(".reference-text") or li
            for bl in span.select(".mw-cite-backlink"):
                bl.decompose()
            definitions[n] = re.sub(r"\s*\n\s*", " ", frag_md(span)).strip()
        ol.decompose()
    return definitions


def heading_info(el):
    if not isinstance(el, Tag):
        return None
    if re.fullmatch(r"h[1-6]", el.name or ""):
        return int(el.name[1]), re.sub(r"\s+", " ", el.get_text(" ", strip=True))
    if el.name in ("div", "section") and any(
        str(c).startswith("mw-heading") for c in (el.get("class") or [])
    ):
        h = el.find(re.compile(r"^h[1-6]$"))
        if h:
            return int(h.name[1]), re.sub(r"\s+", " ", h.get_text(" ", strip=True))
    return None


def structure_page(title):
    """Returns {title, footnotes: {n: md}, sections: [{level, heading, html:[frag,...]}]}
    -- footnotes resolved to @@FNn@@ inline, definitions kept separately.
    RAW html fragments are preserved per section; no markdown conversion,
    no classification happens here."""

    body = fetch_body(title)
    footnotes = extract_footnotes(body)
    sections = []
    current = {"level": 0, "heading": "(preamble)", "html": []}
    for el in body.children:
        if isinstance(el, Comment):
            continue
        hi = heading_info(el)
        if hi:
            sections.append(current)
            current = {"level": hi[0], "heading": hi[1], "html": []}
        else:
            frag = str(el).strip()
            if frag:
                current["html"].append(frag)
    sections.append(current)
    return {"title": title, "footnotes": footnotes, "sections": sections}


def write_readable_txt(data, out_path):
    """Human-readable companion to the JSON dump -- same section structure,
    HTML fragments rendered to plain text, for quick manual comparison."""

    lines = []
    for s in data["sections"]:
        lines.append(f"\n{'#' * max(s['level'], 1)} [{s['heading']}]")
        for frag in s["html"]:
            text = BeautifulSoup(frag, "html.parser").get_text(" ", strip=True)
            if text:
                lines.append(text)
    if data.get("footnotes"):
        lines.append("\n[Footnote definitions]")
        for n in sorted(data["footnotes"], key=lambda x: int(x)):
            lines.append(f"[{n}] {data['footnotes'][n]}")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


def fetch_and_dump(case):
    """Stage 1 only: fetch from the API and write raw files. Always
    re-fetches (does not skip existing files) -- use this when you
    explicitly want fresh data."""

    Path(RAW_DIR).mkdir(exist_ok=True)
    sv_json = Path(RAW_DIR) / f"fall-{case['num']}-sv.json"
    lo_json = Path(RAW_DIR) / f"fall-{case['num']}-lo.json"
    sv_txt = Path(RAW_DIR) / f"fall-{case['num']}-sv.txt"
    lo_txt = Path(RAW_DIR) / f"fall-{case['num']}-lo.txt"

    sv_data = structure_page(BOOK_PREFIX + case["sv"])
    sv_json.write_text(json.dumps(sv_data, ensure_ascii=False, indent=2), "utf-8")
    write_readable_txt(sv_data, sv_txt)
    time.sleep(2)

    lo_data = structure_page(BOOK_PREFIX + case["lo"])
    lo_json.write_text(json.dumps(lo_data, ensure_ascii=False, indent=2), "utf-8")
    write_readable_txt(lo_data, lo_txt)
    time.sleep(2)

    print(f"[stage1] fall-{case['num']} dumped")
    return sv_data, lo_data


def load_raw(case):
    """Load previously-dumped raw JSON without fetching. Raises if missing."""

    sv_json = Path(RAW_DIR) / f"fall-{case['num']}-sv.json"
    lo_json = Path(RAW_DIR) / f"fall-{case['num']}-lo.json"
    if not sv_json.exists() or not lo_json.exists():
        raise FileNotFoundError(
            f"fall-{case['num']}: raw files missing in {RAW_DIR}/ -- "
            f"run with --stage1-only (or default mode) first."
        )
    return (json.loads(sv_json.read_text(encoding="utf-8")),
            json.loads(lo_json.read_text(encoding="utf-8")))


# --------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------- #
# Shared markdown helpers (ported from the Book 2 scraper)
def frag_md(node_or_html) -> str:
    raw = md(str(node_or_html), heading_style="atx", bullets="-", strip=["span"])
    raw = raw.replace("\\*", "*").replace("\\_", "_")
    raw = re.sub(r"[ \t]+\n", "\n", raw)
    return re.sub(r"\n{3,}", "\n\n", raw).strip()


def resolve_fn(t): return re.sub(r"@@FN(\d+)@@", r"[^\1]", t)


def strip_fn_placeholders(t): return re.sub(r"@@FN\d+@@", "", t)


def slugify(s: str) -> str:
    s = s.lower()
    for k, v in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        s = s.replace(k, v)
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80].rsplit("-", 1)[0] if len(s) > 80 else s


def render_boxes_as_quotes(html_fragments):
    """Given a list of raw HTML fragment strings for one section, convert
    any didactic box divs into labelled blockquotes, return combined md."""

    soup = BeautifulSoup("".join(html_fragments), "html.parser")
    for box in soup.select("div.PrettyTextBox, div.collapsible, div.Klappbox, div.klappbox"):
        title_el = box.select_one(".title")
        label = title_el.get_text(" ", strip=True) if title_el else "Hinweis"
        if title_el:
            title_el.decompose()
        inner = resolve_fn(frag_md(box))
        quoted = "\n".join(f"> {ln}" if ln.strip() else ">" for ln in inner.splitlines())
        box.replace_with(NavigableString(f"\n> **{label}:**\n{quoted}\n"))
    return resolve_fn(frag_md(soup))


def labelled_value(preamble_text, label):
    m = re.search(rf"{label}\s*:?\s*([^\n]+)", preamble_text)
    return m.group(1).strip() if m else ""

def clean_markdown_links(text: str) -> str:
    """Strip markdown link syntax and stray bold markers left over from
    frag_md() converting the preamble before labelled_value() extracts a
    field from it -- e.g. turns '** [Name](/wiki/...  "title")' into 'Name'."""
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'\*\*', '', text)
    return text.strip()

def clean_mediawiki_artifacts(text: str) -> str:
    if not text:
        return text
    newpp_pattern = re.compile(
        r'NewPP limit report.*?Rendering was triggered because: \S+\s*',
        re.DOTALL | re.IGNORECASE
    )
    text = newpp_pattern.sub('', text)
    text = re.sub(r'(?:##\s*Fußnoten\s*\n\s*)+', '## Fußnoten\n\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def detect_status(sv_data, lo_data):
    for data in (sv_data, lo_data):
        blob = " ".join("".join(s["html"]) for s in data["sections"])
        if re.search(r"noch nicht fertig|laufenden Booksprint", blob):
            return "unfinished"
    return "complete"


def extract_tags(themen: str):
    """Split 'Behandelte Themen' on ; and , while shielding commas that sit
    inside parentheses (e.g. 'X (Y, Z)' must stay one tag, not split into
    two). This is the fix for the fall-9 / fall-56 fused/split-tag bugs
    found in Book 2."""

    if not themen:
        return []
    shielded = re.sub(r"\([^)]*\)", lambda m: m.group(0).replace(",", "\uE000"), themen)
    pieces = [p.strip().rstrip(".").replace("\uE000", ",")
              for p in re.split(r"[;,]", shielded) if p.strip()]
    return [p.replace(" ", "-") for p in pieces if len(p) <= 160]


def excerpt_filename(heading_text: str) -> str:
    t = strip_fn_placeholders(heading_text).strip()
    t = re.sub(r"^Auszug\s+(aus\s+)?(dem\s+)?", "", t, flags=re.I).strip()
    t = re.sub(r"[()]", "", t)  # keep parenthetical abbreviations (e.g. "KSG"), just drop the brackets
    return f"auszug-{slugify(t)}.md"


# --------------------------------------------------------------------- #
# Stage 2: classify + build
# --------------------------------------------------------------------- #

def build_case(case, sv_data, lo_data):
    unclassified_notes = []

    sv_preamble = " ".join(sv_data["sections"][0]["html"])
    sv_preamble_text = frag_md(BeautifulSoup(sv_preamble, "html.parser")) if sv_preamble else ""
    lo_preamble = " ".join(lo_data["sections"][0]["html"])
    lo_preamble_text = frag_md(BeautifulSoup(lo_preamble, "html.parser")) if lo_preamble else ""

    authors = (labelled_value(lo_preamble_text, "Autor(?:[*:]?in(?:nen)?|en)?") or
               labelled_value(sv_preamble_text, "Autor(?:[*:]?in(?:nen)?|en)?"))
    authors = clean_markdown_links(authors)
    difficulty = (labelled_value(lo_preamble_text, "Schwierigkeitsgrad") or
                  labelled_value(sv_preamble_text, "Schwierigkeitsgrad"))
    difficulty = clean_markdown_links(difficulty)
    themen = labelled_value(lo_preamble_text, "Behandelte Themen")
    themen = clean_markdown_links(themen)

    facts_parts, question_parts = [], []
    excerpts = {}

    for s in sv_data["sections"]:
        raw_heading = s["heading"].strip()
        key = strip_fn_placeholders(raw_heading).strip().lower()
        if key in SV_SKIP_HEADINGS:
            continue
        heading_clean = resolve_fn(raw_heading)
        content_md = render_boxes_as_quotes(s["html"])
        if not content_md.strip():
            continue

        if any(key.startswith(p) for p in FACTS_PREFIXES):
            facts_parts.append(f"## {heading_clean}\n\n{content_md}")
        elif key in QUESTION_HEADINGS:
            question_parts.append(f"### {heading_clean}\n\n{content_md}")
        elif key in NOTE_HEADINGS:
            question_parts.append(f"**{heading_clean}:** {content_md}")
        elif key in EXCERPT_EXACT or any(key.startswith(p) for p in EXCERPT_PREFIXES):
            fname = excerpt_filename(raw_heading)
            if fname not in excerpts:
                excerpts[fname] = f"## {heading_clean}\n\n{content_md}"
            else:
                excerpts[fname] = excerpts[fname] + "\n\n" + content_md
        else:
            unclassified_notes.append(f"SV heading '{heading_clean}' (level {s['level']})")
            facts_parts.append(f"## [UNCLASSIFIED: {heading_clean}]\n\n{content_md}")

    sachverhalt = "\n\n".join(facts_parts).strip()
    instructions = "\n\n".join(question_parts).strip()

    # --- Lösung page: everything after preamble is body, in order --- #
    loesung_parts = ["# Lösungsvorschlag", ""]
    for s in lo_data["sections"]:
        key = strip_fn_placeholders(s["heading"]).strip().lower()
        if key in LO_SKIP_BODY_HEADINGS:
            continue
        content_md = render_boxes_as_quotes(s["html"])
        loesung_parts.append(f"{'#' * min(max(s['level'],2),6)} {resolve_fn(s['heading'])}")
        if content_md.strip():
            loesung_parts.append(content_md)

    # Footnotes: namespace by source page before merging, so identical
    # numbers from SV and LO pages (each restarts at 1) never collide and
    # silently overwrite each other.
    # remap @@FNn@@ placeholders in the already-resolved text: since
    # resolve_fn() ran per-section above using bare @@FNn@@, and SV/LO
    # placeholders were never disambiguated at the source, we instead
    # keep LO's own numbering authoritative for the Lösung body (matches
    # every footnote actually cited there) and separately append SV's
    # footnote definitions -- if any -- to sachverhalt.md so SV-page
    # citations aren't left dangling with no definition anywhere.

    if lo_data["footnotes"]:
        loesung_parts += ["", "## Fußnoten", ""]
        for n in sorted(lo_data["footnotes"], key=lambda x: int(x)):
            loesung_parts.append(f"[^{n}]: {lo_data['footnotes'][n]}")
    loesung = clean_mediawiki_artifacts("\n\n".join(loesung_parts).strip()) + "\n"

    if sv_data["footnotes"]:
        sv_fn_block = ["", "## Fußnoten (Sachverhalt)", ""]
        for n in sorted(sv_data["footnotes"], key=lambda x: int(x)):
            sv_fn_block.append(f"[^{n}]: {sv_data['footnotes'][n]}")
        sachverhalt = sachverhalt + "\n\n" + "\n\n".join(sv_fn_block)

    metadata = (f"# Metadaten\n\n"
                f"**Fall:** {case['num']}) {case['name']}\n\n"
                f"**Autor*innen:** {authors}\n\n"
                f"**Schwierigkeitsgrad:** {difficulty}\n\n"
                f"**Behandelte Themen:** {themen}\n\n")

    status = detect_status(sv_data, lo_data)
    task = {
        "title": case["name"],
        "work_type": "draft",
        "tags": extract_tags(themen),
        "instructions": instructions,
        "deliverables": "fallloesung-sut.md",
        "license": LICENSE_TMPL.format(authors=authors or "AUTOR*IN"),
        "status": status,
    }
    return {"sachverhalt": sachverhalt, "metadata": metadata, "loesung": loesung,
            "task": task, "status": status, "unclassified": unclassified_notes,
            "excerpts": excerpts}


def write_case(case, built, out_root=OUT_ROOT):
    case_slug = f"fall-{case['num']}-{slugify(case['name'])}"
    base = Path(out_root) / case_slug
    (base / "documents").mkdir(parents=True, exist_ok=True)
    (base / "evals").mkdir(parents=True, exist_ok=True)
    (base / "task.json").write_text(json.dumps(built["task"], ensure_ascii=False, indent=2), "utf-8")
    (base / "documents" / "sachverhalt.md").write_text(f"{built['sachverhalt']}\n", "utf-8")
    (base / "documents" / "metadata.md").write_text(built["metadata"], "utf-8")
    (base / "evals" / "fallloesung-sut.md").write_text(built["loesung"], "utf-8")
    for fname, content in built["excerpts"].items():
        (base / "documents" / fname).write_text(content + "\n", "utf-8")

    flag = "  [UNFINISHED]" if built["status"] == "unfinished" else ""
    warn = f"  [UNCLASSIFIED: {len(built['unclassified'])}]" if built["unclassified"] else ""
    exc = f"  [excerpts: {len(built['excerpts'])}]" if built["excerpts"] else ""
    print(f"[stage2] fall-{case['num']} -> {base}{flag}{warn}{exc}")
    for note in built["unclassified"]:
        print(f"          !! {note}")


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--stage1-only", action="store_true",
                       help="Fetch + dump raw files only. No build.")
    mode.add_argument("--build-only", action="store_true",
                       help="Build final files from existing raw_grundrechte/ files. No fetching.")
    args = ap.parse_args()

    for case in CASES:
        if args.stage1_only:
            fetch_and_dump(case)
        elif args.build_only:
            sv_data, lo_data = load_raw(case)
            built = build_case(case, sv_data, lo_data)
            write_case(case, built)
        else:
            sv_data, lo_data = fetch_and_dump(case)
            built = build_case(case, sv_data, lo_data)
            write_case(case, built)


if __name__ == "__main__":
    main()