#!/usr/bin/env python3
"""
LAB-EU scraper -- Wikibooks "Verwaltungsrecht in der Klausur / Die Fälle"
=========================================================================

Turns one case page into the LAB-EU task layout:

    tasks/de/verwaltungsrecht/<slug>/
        task.json
        documents/
            sachverhalt.md
            auszug-<gesetz>.md      (one file per embedded law excerpt)
        evals/
            fallloesung-sut.md              (Gliederung + Vorschlag + Fußnoten)

Why HTML and not wikitext: the rendered HTML keeps the footnote links inside
<ol class="references">; the plain-text export drops them. We fetch the parsed
HTML through the MediaWiki API, recover the links from the reference list, and
re-attach them as markdown footnotes.

Heading levels in the Lösung are RE-DERIVED from the enumerator
(A. / I. / 1. / a) / aa) / (1)) instead of trusting the wiki's own levels,
because the wiki source mixes them up. This reproduces how Fall 5 was hand-built.

v1 -- run on ONE case, diff against the hand-built Fall 5, then batch.
The two OpenRewi books have a different layout and will need the section map tweaked.

    pip install requests beautifulsoup4 markdownify
    python scrape_lab.py                  # default: Fall 5 only (known-good)
    python scrape_lab.py --all            # every Fall on the index page
    python scrape_lab.py "<wiki page title>"   # one specific page
"""

import argparse
import json
import random
import re
import sys
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from markdownify import markdownify as md

API = "https://de.wikibooks.org/w/api.php"
INDEX_PAGE = "Verwaltungsrecht in der Klausur/ Die Fälle"
OUT_ROOT = "out/tasks/de/verwaltungsrecht"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "LAB-EU-scraper/0.1 (research; mannheim)"})

# Flip to True to auto-fix obvious source typos (missing §, doubled „„, etc.)
# and print every change. Default False = byte-faithful transcription.
CLEAN = False

# Match the hand-built ground-truth style: hints as > **Label:** blockquotes,
# and footnote links as "text (<url>)" instead of "[text](url)".
GT_STYLE = True

LICENSE = (
    "Dieser Text steht unter der Lizenz CC BY-SA 4.0 "
    "(https://creativecommons.org/licenses/by-sa/4.0/deed.de). "
    "Er beruht auf dem Werk von AUTOR*IN, in: Eisentraut, Fälle zum "
    "Verwaltungsrecht (DOI: 10.24921/2020.94115939), § ## Rn. ##, ebenfalls "
    "veröffentlicht unter der Lizenz CC BY-SA 4.0. Für Änderungen ist allein "
    "der/die Urheber*in dieser Überarbeitung verantwortlich."
)


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #
def api_parse(page_title: str) -> BeautifulSoup:
    params = {"action": "parse", "page": page_title, "prop": "text",
              "format": "json", "formatversion": "2", "redirects": "1"}
    for attempt in range(5):
        r = SESSION.get(API, params=params, timeout=30)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 0)) or (5 * (attempt + 1))
            print(f"     [429] rate-limited, waiting {wait}s (attempt {attempt+1}/5)")
            time.sleep(wait)
            continue
        r.raise_for_status()
        break
    else:
        raise RuntimeError("giving up after repeated 429s")
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("info", "API error"))
    soup = BeautifulSoup(data["parse"]["text"], "html.parser")
    body = soup.select_one(".mw-parser-output") or soup
    for sel in [".mw-editsection", "style", "link", ".navbox", ".noprint", "table.metadata"]:
        for el in body.select(sel):
            el.decompose()
    # Randnummern (margin paragraph numbers) render as pure-digit <b>/<strong>;
    # they are the only bold elements that are all digits, so drop just those.
    for b in body.find_all(["b", "strong"]):
        if re.fullmatch(r"\d+", b.get_text().strip()):
            b.decompose()
    # Header/footer navigation ("Zurück zu ... Weiter zu ... Inhaltsübersicht")
    for div in body.find_all("div"):
        t = div.get_text(" ", strip=True)
        if len(t) < 400 and re.search(r"Zurück zu|Weiter zu|Zur Inhaltsübersicht", t):
            div.decompose()
    return body


def list_cases():
    """Return [(page_title, display_title)] for every 'Fall N' on the index page."""
    body = api_parse(INDEX_PAGE)
    cases = []
    seen = set()
    for a in body.select("a[href]"):
        href = a.get("href", "")
        if not re.search(r"/_?Fall_\d+", href):
            continue
        path = urllib.parse.unquote(href.split("/wiki/")[-1])
        page_title = path.replace("_", " ")
        if page_title in seen:
            continue
        seen.add(page_title)
        display = a.get_text().strip()                 # "Fall 5: ..."
        cases.append((page_title, display))
    # sort by Fall number
    cases.sort(key=lambda c: int(re.search(r"Fall (\d+)", c[0]).group(1)))
    return cases


# --------------------------------------------------------------------------- #
# Footnotes
# --------------------------------------------------------------------------- #
def extract_footnotes(body: BeautifulSoup) -> dict:
    """Inline <sup.reference> -> @@FNn@@ tokens; references <ol> -> {n: md}."""
    definitions = {}
    for sup in body.select("sup.reference"):
        m = re.search(r"\d+", sup.get_text())
        if not m:
            sup.decompose(); continue
        sup.replace_with(NavigableString(f"@@FN{m.group(0)}@@"))

    ol = body.select_one("ol.references")
    if ol:
        for i, li in enumerate(ol.find_all("li", recursive=False), start=1):
            n = str(i)
            mid = re.search(r"cite_note-(?:.*?-)?(\d+)$", li.get("id", ""))
            if mid:
                n = mid.group(1)
            span = li.select_one(".reference-text") or li
            for bl in span.select(".mw-cite-backlink"):
                bl.decompose()
            definitions[n] = re.sub(r"\s*\n\s*", " ", frag_to_md(span)).strip()
        ol.decompose()
    return definitions


# --------------------------------------------------------------------------- #
# HTML -> Markdown helpers
# --------------------------------------------------------------------------- #
def frag_to_md(node) -> str:
    raw = md(str(node), heading_style="atx", bullets="-", strip=["span"])
    raw = raw.replace("\\*", "*").replace("\\_", "_")   # undo gender-star escaping
    raw = re.sub(r"[ \t]+\n", "\n", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def resolve_fn(text: str) -> str:
    return re.sub(r"@@FN(\d+)@@", r"[^\1]", text)


def gt_footnote_links(text: str) -> str:
    """[text](url) -> text (<url>), moving a trailing period outside the link."""
    return re.sub(r"\[([^\]]+?)\]\((https?://[^)\s]+)\)", r"\1 (<\2>)", text)


def gt_hints(text: str) -> str:
    """Standalone *Lösungshinweis: ...* -> > **Lösungshinweis:** ...; strip inline italics."""
    out = []
    for ln in text.split("\n"):
        m = re.match(r"^\*(L\u00f6sungshinweis|Aufbauhinweis|Bearbeitungshinweis):\s*(.+?)\*(\[\^\d+\])?\s*$", ln)
        if m:
            out.append(f"> **{m.group(1)}:** {m.group(2)}{m.group(3) or ''}")
        else:
            out.append(ln)
    text = "\n".join(out)
    # strip italics ONLY inside parentheses, e.g. (*a.A. vertretbar*) -> (a.A. vertretbar);
    # this leaves gender-stars like Leser*innen untouched.
    return re.sub(r"\(\*([^*\n]+?)\*\)", r"(\1)", text)


def maybe_clean(text: str) -> str:
    if not CLEAN:
        return text
    changes = []
    def sub(pat, repl, label, s):
        new, k = re.subn(pat, repl, s)
        if k: changes.append(f"{label} x{k}")
        return new
    text = sub(r"„„", "„", "doubled-open-quote", text)
    text = sub(r"(?<!§)(?<!§ )\bWerturteilte\b", "Werturteile", "Werturteilte", text)
    text = sub(r"(?<![§\d])\bNach 7 I TMG\b", "Nach § 7 I TMG", "missing-§", text)
    if changes:
        print("   [clean]", "; ".join(changes))
    return text


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #
def clean_heading(t: str) -> str:
    """Strip the leftover wiki '= ... =' markup some headings carry."""
    return re.sub(r"^\s*=+\s*|\s*=+\s*$", "", t).strip()


def split_sections(body: BeautifulSoup):
    """
    Group top-level nodes under their preceding top-level heading.
    The 'top level' is auto-detected as the heading level of 'Sachverhalt'
    (h1 on current Wikibooks, but this adapts if that ever changes).
    Returns [(title, nodes)].
    """
    main_level = 2
    for h in body.find_all(re.compile(r"^h[1-6]$")):
        if "sachverhalt" in h.get_text().strip().lower():
            main_level = int(h.name[1])
            break
    out, title, nodes = [], None, []
    for el in body.children:
        hi = heading_info(el)
        if hi and hi[0] == main_level:
            out.append((title, nodes))
            title, nodes = hi[1], []
        else:
            nodes.append(el)
    out.append((title, nodes))
    return out


def nodes_html(nodes) -> str:
    return "".join(str(n) for n in nodes)


def heading_info(el):
    """
    Return (level:int, text:str) if `el` is a heading, else None.
    Handles MediaWiki 1.43+ where headings are wrapped as
    <div class="mw-heading mw-heading2"><h2>...</h2></div>, plus the old bare <hN>.
    """
    if not isinstance(el, Tag):
        return None
    if re.fullmatch(r"h[1-6]", el.name or ""):
        return int(el.name[1]), el.get_text().strip()
    cls = el.get("class") or []
    if el.name in ("div", "section") and any(str(c).startswith("mw-heading") for c in cls):
        h = el.find(re.compile(r"^h[1-6]$"))
        if h:
            return int(h.name[1]), h.get_text().strip()
    return None


# --------------------------------------------------------------------------- #
# Enumerator -> heading level (Bizer's hierarchy)
# --------------------------------------------------------------------------- #
ENUM = [
    (re.compile(r"^[A-H]\.\s"),     "## "),
    (re.compile(r"^[IVX]+\.\s"),    "### "),
    (re.compile(r"^\d+\.\s"),       "#### "),
    (re.compile(r"^[a-h]\)\s"),     "##### "),
    (re.compile(r"^[a-h]{2}\)\s"),  "###### "),
    (re.compile(r"^\(\d+\)\s"),     "BOLD"),
]


def relevel(line: str):
    t = line.strip()
    # check 2-letter aa) before 1-letter a)
    for pat, pre in [ENUM[0], ENUM[1], ENUM[2], ENUM[4], ENUM[3], ENUM[5]]:
        if pat.match(t):
            return pre
    return None


# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #
def _para_header_text(el):
    """If el is a standalone fully-bold paragraph that looks like a law/excerpt
    header, return its text; else None. This is what separates real excerpt
    headers from bold emphasis inside prose."""
    if not isinstance(el, Tag) or el.name not in ("p", "dd", "div", "li"):
        return None
    txt = el.get_text(" ", strip=True)
    if not txt or len(txt) > 90:
        return None
    bolds = el.find_all(["b", "strong"])
    if not bolds:
        return None
    boldtxt = " ".join(b.get_text(" ", strip=True) for b in bolds)
    if txt.replace(" ", "") != boldtxt.replace(" ", ""):      # not WHOLLY bold -> emphasis, skip
        return None
    if _is_section_header(txt) or _is_law_name(txt) or txt.startswith("Auszug"):
        return txt
    return None


def _is_section_header(t):
    return bool(re.match(r"^§+\s*\d", t.strip()))


def _is_law_name(t):
    if t.strip().startswith("§"):
        return False

    return bool(re.search(
        r"Auszug|"
        r"Art\.\s*\d+|"
        r"[Gg]esetz|[Vv]erordnung|[Ss]atzung|[Oo]rdnung\b|"
        r"[Bb]edingungen|[Vv]ertrag|buch|"
        r"\([A-ZÄÖÜ][A-Za-zÄÖÜ0-9]{1,15}\)",
        t
    ))


def _law_key(txt, is_section):
    """A stable key identifying which law a header belongs to."""
    mp = re.search(r"\(([A-ZÄÖÜ][A-Za-zÄÖÜ0-9]{1,15})\)", txt)   # (LFGB), (RStV)
    if mp:
        return mp.group(1)
    for m in re.finditer(r"\b([A-ZÄÖÜ][A-Za-zÄÖÜ]{1,12})\b", txt):   # WaffG, HSOG
        if sum(c.isupper() for c in m.group(1)) >= 2:
            return m.group(1)
    if is_section:
        return None                       # plain "§ 40 Title" -> current law
    return re.sub(r"^Auszug\s+", "", txt).strip()[:40]


def _law_filename(txt):
    """Filename for an excerpt. Keeps the full spelled-out law name (matching the
    hand-built Fall 5, e.g. 'rundfunkstaatsvertrag'), but for a bare section
    header like '§ 20 HGO Teilnahme ...' uses just the abbreviation ('hgo').
    Always drops the section title, and slugify() caps the length."""
    t = re.sub(r"^Auszug\s+", "", txt).strip()
    if not t.startswith("§"):
        name = re.sub(r"\s*\(.*$", "", t).strip()        # drop "(ABBR) ..." + section title
        return f"auszug-{slugify(name)}.md"
    m = re.match(r"§+\s*\d+\w*\s+([A-ZÄÖÜ][A-Za-zÄÖÜ]{1,12})", t)
    if m and sum(c.isupper() for c in m.group(1)) >= 2:   # real abbreviation (HGO, WaffG)
        return f"auszug-{slugify(m.group(1))}.md"
    name = re.sub(r"^§+\s*\d+\w*\s*", "", t).strip()
    return f"auszug-{slugify(name)}.md"


def build_sachverhalt(nodes):
    facts, order, chunks = [], [], {}
    current_key = None
    current_file = None
    in_excerpt = False

    for el in nodes:
        if not isinstance(el, Tag):
            continue
        md_chunk = resolve_fn(frag_to_md(BeautifulSoup(str(el), "html.parser")))
        if not md_chunk.strip():
            continue
        htext = _para_header_text(el)
        if htext is not None:
            is_sec = _is_section_header(htext)
            key = _law_key(htext, is_sec)
            # a section with no law-key of its own continues the current document
            if is_sec and key is None and current_file is not None:
                chunks[current_file].append(md_chunk)
                in_excerpt = True
                continue
            # otherwise this header starts (or switches to) a document
            if key != current_key or current_file is None:
                current_key = key
                current_file = _law_filename(htext)
                if current_file not in chunks:
                    chunks[current_file] = []
                    order.append(current_file)
            chunks[current_file].append(md_chunk)
            in_excerpt = True
        else:
            if in_excerpt and current_file:
                chunks[current_file].append(md_chunk)
            else:
                facts.append(md_chunk)

    body_block = maybe_clean("\n\n".join(facts).strip())
    excerpts = {fn: maybe_clean("\n\n".join(chunks[fn]).strip()) for fn in order}
    instructions = extract_instructions(body_block)
    sachverhalt = strip_question(body_block)
    return sachverhalt, instructions, excerpts


# HINT_LABEL: processing notes that follow the task question (e.g. "Bearbeitungshinweis: assume X").
# NOTE_LABEL: editor/author vermerk lines — used as fallback task source ONLY when no question or
#             imperative is found (e.g. Fall 9: "Bearbeiter*innenvermerk: Erstellen Sie ein Gutachten").
#             In Falls 7/8 these lines are hints, not tasks, so they must not override a real question.
HINT_LABEL = r"(?:Bearbeitungshinweis|Bearbeitungsvermerk)"
NOTE_LABEL = r"(?:Bearbeiter\*?innenvermerk|Bearbeitervermerk|Aufgabe|Frage(?:\s*\d+)?)"

# All imperative verbs that signal a task line ending in ! or embedded in a sentence.
INSTR_VERB = (
    r"(?:Erstellen|Fertigen|Pr\u00fcfen|Begutachten|Beurteilen|Bewerten|Verfassen"
    r"|Er\u00f6rtern|Untersuchen|Bearbeiten|Analysieren|L\u00f6sen|Pr\u00fcfen)\s+Sie"
)


def _label_blocks(block, label):
    """Extract all paragraphs starting with a given label pattern."""
    out = []
    for m in re.finditer(rf"(?m)^[*_#\s]*(?:{label})\s*:(.+?)(?:\n\s*\n|\Z)", block, flags=re.S):
        seg = re.sub(r"\*\*|__", "", re.sub(r"\s+", " ", m.group(0))).strip()
        out.append(seg)
    return out


def extract_instructions(block: str) -> str:
    """
    Priority order:
      1. Lines ending in ?  (explicit question, e.g. "Hat die Klage Aussicht auf Erfolg?")
      2. Imperative verb lines (e.g. "Beurteilen Sie…!", "Bewerten Sie…!")
      3. HINT_LABEL blocks (Bearbeitungshinweis / Bearbeitungsvermerk)
      4. NOTE_LABEL blocks as fallback only (Bearbeiter*innenvermerk, Aufgabe, Frage) —
         used when 1+2 are both empty, so Fall 9's vermerk becomes the task.
    """
    def clean(l):
        return re.sub(r"\*\*|__", "", l.strip().strip("#").strip()).strip()

    lines = [clean(l) for l in block.splitlines() if l.strip()]
    hints = _label_blocks(block, HINT_LABEL)
    notes = _label_blocks(block, NOTE_LABEL)

    hint_text = " ".join(hints)
    note_text = " ".join(notes)

    # 1. Question lines (end in ?) that aren't already in hint/note text
    questions = [l for l in lines if l.endswith("?") and l not in hint_text and l not in note_text]

    # 2. Imperative verb lines (end in ! or part of a sentence) not already captured
    captured_so_far = " ".join(questions) + " " + hint_text + " " + note_text
    verbs = [l for l in lines
             if re.search(INSTR_VERB, l)
             and l not in captured_so_far
             and not any(l in h for h in hints + notes)]

    # If we have a real question or imperative, use it + hints (not the note/vermerk).
    # If we have nothing, fall back to the note (Fall 9 case).
    # When a real question/imperative exists, include notes as trailing assumptions
    # (same role as Bearbeitungshinweis). Fall 9 has no question/verb, so the note
    # IS the task — it goes first.
    if questions or verbs:
        parts = questions + verbs + hints + notes
    else:
        parts = notes + hints

    seen, out = set(), []
    for p in parts:
        if p and p not in seen:
            seen.add(p); out.append(p)
    out += [clean(l) for l in block.splitlines() if "frage" in l.lower() and clean(l) not in out]        
    return " ".join(out).strip()


def strip_question(block: str) -> str:
    """Remove the task prompt lines from the Sachverhalt body."""
    block = re.sub(r"(?m)^[*_#\s]*.*\?[*_\s]*$", "", block)           # question lines
    block = re.sub(rf"(?ms)^[*_#\s]*(?:{HINT_LABEL}|{NOTE_LABEL})\s*:.*?(?:\n\s*\n|\Z)", "", block)
    block = re.sub(rf"(?m)^[*_#\s]*(?:{INSTR_VERB}).*$", "", block)   # bare imperative lines
    return re.sub(r"\n{3,}", "\n\n", block).strip()


def build_loesung(gliederung_nodes, vorschlag_nodes, footnotes) -> str:
    out = ["# Lösungsgliederung", ""]

    # Gliederung: relevel each line into the heading skeleton.
    gtext = resolve_fn(frag_to_md(BeautifulSoup(nodes_html(gliederung_nodes), "html.parser")))
    for line in gtext.splitlines():
        s = re.sub(r"^[:\-*\s]+", "", line.strip()).strip()
        if not s:
            continue
        pre = relevel(s)
        if pre == "BOLD":
            out += [f"**{s}**", ""]
        elif pre:
            out += [f"{pre}{s}", ""]
        else:
            out += [s, ""]

    out += ["# Lösungsvorschlag", ""]
    soup = BeautifulSoup(nodes_html(vorschlag_nodes), "html.parser")
    for el in soup.children:
        hi = heading_info(el)
        if hi:
            t = clean_heading(hi[1])
            pre = relevel(t)
            if pre == "BOLD":
                out += [f"**{t}**", ""]
            elif pre:
                out += [f"{pre}{t}", ""]
            else:
                out += [t, ""]                      # non-enumerator heading -> plain
        else:
            frag = maybe_clean(resolve_fn(frag_to_md(BeautifulSoup(str(el), "html.parser"))))
            if frag.strip():
                out += [frag, ""]

    out += ["## Fußnoten", ""]
    for n in sorted(footnotes, key=lambda x: int(x)):
        out += [f"[^{n}]: {maybe_clean(footnotes[n])}", ""]
    result = "\n".join(out).strip() + "\n"
    if GT_STYLE:
        result = gt_hints(gt_footnote_links(result))
    return result


def build_task_json(title, tags, instructions, license):
    return {"title": title, "work_type": "draft", "tags": tags,
            "instructions": instructions, "deliverables": "fallloesung-sut.md",
            "license": license}


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #
def extract_title(body, display_title, page_title):
    if display_title:
        return re.sub(r"^Fall\s*\d+:\s*", "", display_title).strip()
    # The case title is bold text ("Fall 5: ..."); the "Zurück zu Fall 4: ..."
    # back-link is an <a>. Prefer a bold element, then any NON-link occurrence.
    for b in body.find_all(["b", "strong"]):
        m = re.match(r"\s*Fall\s*\d+:\s*(.+)", b.get_text())
        if m:
            return m.group(1).strip()
    for node in body.find_all(string=re.compile(r"Fall\s*\d+:")):
        if node.find_parent("a"):            # skip navigation links
            continue
        m = re.search(r"Fall\s*\d+:\s*(.+)", node)
        if m:
            return m.group(1).strip()
    return page_title.split("/")[-1].strip()


def extract_license(body) -> str:
    """Build the rights statement from the page's own author + CC line.
    Falls back to the placeholder LICENSE if the author can't be found."""
    txt = body.get_text("\n")
    m = re.search(r"Autor(?:in)?\s+der\s+Ursprungsfassung\s+ist\s+([^\n]+)", txt)
    author = m.group(1).strip() if m else None
    # tidy trailing footnote-ish artifacts, keep the name
    if author:
        author = re.sub(r"\[.*$", "", author).strip().rstrip(".")
    if not author:
        return LICENSE                       # keep placeholder -> fill by hand
    return (
        f"Dieser Text steht unter der Lizenz CC BY-SA 4.0 "
        f"(https://creativecommons.org/licenses/by-sa/4.0/deed.de). "
        f"Er beruht auf dem Werk von {author}, in: Eisentraut, F\u00e4lle zum "
        f"Verwaltungsrecht (DOI: 10.24921/2020.94115939), ebenfalls "
        f"ver\u00f6ffentlicht unter der Lizenz CC BY-SA 4.0. F\u00fcr \u00c4nderungen ist allein "
        f"der/die Urheber*in dieser \u00dcberarbeitung verantwortlich."
    )


def extract_tags(body) -> list:
    """Return clean tags from a delimited Lernziele/Schwerpunkte list.
    Returns [] when the line is missing (Pattern C) or is prose (Pattern B,
    e.g. Fall 9) -- those cases are meant to be filled by the LLM tag step."""
    m = re.search(r"(?:Lernziele/Schwerpunkte|Schwerpunkte/Lernziele)\s*:\s*([^\n]+)",
                  body.get_text("\n"))
    if not m:
        return []                                   # Pattern C: no metadata line
    content = m.group(1).replace("\xa0", " ").strip()

    # Prose rather than a list -> hand to the LLM step.
    if re.search(r"Kernpunkte sind|nachvollziehbare Argument|^\s*Der Fall\b", content):
        return []

    pieces = [p.strip() for p in re.split(r"[;,]", content) if p.strip()]
    tags = []
    for p in pieces:
        if len(p) > 90:                              # a run-on clause, not a tag
            continue
        p = re.sub(r"-\s+", "-", p).replace(" ", "-")
        tags.append(p)
    return tags

def slugify(s: str) -> str:
    s = s.lower()
    for k, v in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        s = s.replace(k, v)
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > 80:                       # keep paths under Windows' 260-char limit
        s = s[:80].rsplit("-", 1)[0]
    return s


# --------------------------------------------------------------------------- ##
# Orchestration
# --------------------------------------------------------------------------- #
def scrape_case(page_title, display_title="", out_root=OUT_ROOT, force=False, fall_number=None):
    body = api_parse(page_title)
    footnotes = extract_footnotes(body)
    title = extract_title(body, display_title, page_title)
    tags = extract_tags(body)

    sec = {}
    for sect_title, nodes in split_sections(body):
        if not sect_title:
            continue
        k = sect_title.lower()
        if "sachverhalt" in k:   sec["sachverhalt"] = nodes
        elif "gliederung" in k:  sec["gliederung"] = nodes
        elif "vorschlag" in k:   sec["vorschlag"] = nodes

    sachverhalt, instructions, excerpts = build_sachverhalt(sec.get("sachverhalt", []))
    loesung = build_loesung(sec.get("gliederung", []), sec.get("vorschlag", []), footnotes)

    # Fall 13 and similar cases have no explicit question in the Sachverhalt.
    # Fall back to a generic instruction derived from the case title so the
    # task.json instructions field is never left blank.
    if not instructions.strip():
        instructions = f"Prüfen Sie gutachterlich die Erfolgsaussichten. Gegenstand: {title}."
        print(f"     [warn] no instructions found -- using title-derived fallback")

    task = build_task_json(title, tags, instructions, extract_license(body))

    missing = [s for s in ("sachverhalt", "gliederung", "vorschlag") if not sec.get(s)]
    if missing:
        print(f"     [warn] sections not found: {missing} "
              f"(found: {[t for t, _ in split_sections(body) if t]})")

    # Prepend zero-padded fall number prefix if available (e.g. fall-05-)
    title_slug = slugify(title)
    if fall_number is not None:
        folder_name = f"fall-{int(fall_number):02d}-{title_slug}"
    else:
        folder_name = title_slug
    base = Path(out_root) / folder_name
    if (base / "task.json").exists() and not force:
        print(f"[skip] {base} already exists -- pass --force to overwrite")
        return base
    (base / "documents").mkdir(parents=True, exist_ok=True)
    (base / "evals").mkdir(parents=True, exist_ok=True)
    (base / "task.json").write_text(json.dumps(task, ensure_ascii=False, indent=2), "utf-8")
    (base / "documents" / "sachverhalt.md").write_text(sachverhalt + "\n", "utf-8")
    for fname, content in excerpts.items():
        (base / "documents" / fname).write_text(content + "\n", "utf-8")
    (base / "evals" / "fallloesung-sut.md").write_text(loesung, "utf-8")

    print(f"[ok] {title}")
    print(f"     dir:       {base}")
    print(f"     tags:      {len(tags)} -> {tags}")
    print(f"     excerpts:  {list(excerpts)}")
    print(f"     footnotes: {len(footnotes)}")
    return {
        "title": title,
        "slug": folder_name,
        "work_type": task["work_type"], #will probably later make an LLM determine this
        "n_tags": len(tags), #will probably later make an LLM determine this (tags themselves not the number)
        "n_excerpts": len(excerpts),
        "excerpts": list(excerpts),
        "n_footnotes": len(footnotes),
        "instructions": instructions,
        "warnings": "; ".join(missing) if missing else "",
    }


def write_report(rows, out_dir):
    """Write report.md + report.csv summarizing every scraped case."""
    import csv
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    md = Path(out_dir) / "report.md"
    lines = ["# LAB-EU scrape report", "",
             f"{len(rows)} case(s). Review `work_type` and any warnings before pushing.", "",
             "| # | Title | work_type | tags | excerpts | footnotes | warnings |",
             "|---|-------|-----------|-----:|---------:|----------:|----------|"]
    for i, r in enumerate(rows, 1):
        warn = r["warnings"] or "-"
        lines.append(f"| {i} | {r['title'][:60]} | {r['work_type']} | "
                     f"{r['n_tags']} | {r['n_excerpts']} | {r['n_footnotes']} | {warn} |")
    lines += ["", "## Instructions (check each to confirm work_type)", ""]
    for i, r in enumerate(rows, 1):
        lines += [f"**{i}. {r['title']}**  (`{r['work_type']}`)",
                  "", f"> {r['instructions']}", "",
                  f"excerpts: {', '.join(r['excerpts']) or '(none)'}",
                  f"warnings: {r['warnings'] or '(none)'}", "", "---", ""]
    md.write_text("\n".join(lines), encoding="utf-8")

    csvp = Path(out_dir) / "report.csv"
    with open(csvp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["#","title","slug","work_type","n_tags","n_excerpts","n_footnotes","warnings","instructions"])
        for i, r in enumerate(rows, 1):
            w.writerow([i, r["title"], r["slug"], r["work_type"], r["n_tags"],
                        r["n_excerpts"], r["n_footnotes"], r["warnings"], r["instructions"]])
    print(f"\n[report] {md}\n[report] {csvp}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*", help="specific wiki page titles")
    ap.add_argument("--all", action="store_true", help="scrape every Fall on the index")
    ap.add_argument("--list", action="store_true", help="just list the cases")
    ap.add_argument("--out", default="out", help="output root folder (default: ./out)")
    ap.add_argument("--force", action="store_true", help="overwrite existing task.json")
    args = ap.parse_args()
    out_root = f"{args.out}/tasks/de/verwaltungsrecht"

    if args.list:
        for pt, dt in list_cases():
            print(f"{pt}\n    -> {slugify(re.sub(r'^Fall.*?:.s*','',dt))}")
        return
    if args.all:
        targets = list_cases()
        if not targets:
            print("[warn] index scan found no cases; falling back to Fall 1-16 by name")
            targets = [(f"Verwaltungsrecht in der Klausur/ Die Fälle / Fall {n}", "")
                       for n in range(1, 17)]
        print(f"[info] {len(targets)} case(s) to scrape")
    elif args.pages:
        targets = [(p, "") for p in args.pages]
    else:
        targets = [("Verwaltungsrecht in der Klausur/ Die Fälle / Fall 5", "")]

    rows = []
    for pt, dt in targets:
        try:
            # Extract Fall number from page title if present (e.g. "... / Fall 5" -> 5)
            fn_match = re.search(r"Fall\s*(\d+)", pt)
            fall_num = int(fn_match.group(1)) if fn_match else None
            info = scrape_case(pt, dt, out_root=out_root, force=args.force, fall_number=fall_num)
            if isinstance(info, dict):
                rows.append(info)
            time.sleep(2 + random.uniform(0, 2))   # 2-4s with jitter, polite to API
        except Exception as e:
            print(f"[FAIL] {pt}: {e}")
    if rows:
        write_report(rows, args.out)


if __name__ == "__main__":
    main()