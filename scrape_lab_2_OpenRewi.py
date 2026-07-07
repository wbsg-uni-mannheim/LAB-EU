#!/usr/bin/env python3
"""
scrape_asyl.py -- OpenRewi "Fallbuch zum Asylrecht" -> LAB-EU task folders.

This book differs from the Verwaltungsrecht one:
  * each case = TWO wiki pages (Sachverhalt + Lösung), so two fetches per task
  * the index lists them as "<n>) Name: Sachverhalt | Lösung" (both are redirects)
  * cases are grouped under "§ N <Section>" bold labels -> folder layer
  * metadata lives in 'Behandelte Themen' / 'Schwierigkeitsgrad' / 'Autor*innen'
  * didactic 'Weiterführendes Wissen' / 'Hinweise zur Fallprüfung' boxes are
    <div class="collapsible PrettyTextBox"> -> kept as labelled blockquotes

Folder blueprint (per Hussain/Bizer):
    tasks/de/asylrecht/<section-slug>/fall-<n>-<case-slug>/
        task.json
        documents/
            sachverhalt.md
            metadata.md          (Schwierigkeitsgrad, Themen, Autor*innen, SV-link)
        evals/
            fallloesung-sut.md

    pip install requests beautifulsoup4 markdownify
    python scrape_asyl.py                 # default: case 1 only (known-good)
    python scrape_asyl.py --all           # every case on the index
    python scrape_asyl.py --list
"""

import argparse, json, re, sys, time, urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from markdownify import markdownify as md

API = "https://de.wikibooks.org/w/api.php"
BOOK = "OpenRewi/ Fallbuch zum Asylrecht mit aufenthaltsrechtlichen Bezügen"
OUT_ROOT = "out/tasks/de/asylrecht"
UA = {"User-Agent": "LAB-EU-asyl-scraper/0.1 (research; mannheim)"}
CLEAN = False                    # verbatim, per Aaron ("take the text exactly as is")

LICENSE_TMPL = (
    "Dieser Text steht unter der Lizenz CC BY-SA 4.0 "
    "(https://creativecommons.org/licenses/by-sa/4.0/deed.de). "
    "Er beruht auf dem Werk von {authors}, in: Mantel/Nachtigall/Wasnick (Hrsg.), "
    "Fallbuch Asylrecht. Mit Bezügen zum Aufenthaltsrecht, ebenfalls veröffentlicht "
    "unter der Lizenz CC BY-SA 4.0. Für Änderungen ist allein der/die Urheber*in "
    "dieser Überarbeitung verantwortlich."
)


# --------------------------------------------------------------------------- #
# Fetch
# --------------------------------------------------------------------------- #
def api_parse(page_title: str) -> BeautifulSoup:
    params = {"action": "parse", "page": page_title, "prop": "text",
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
    for b in body.find_all(["b", "strong"]):        # drop Randnummer-style pure-digit bold
        if re.fullmatch(r"\d+", b.get_text().strip()):
            b.decompose()
    return body


# --------------------------------------------------------------------------- #
# Index -> case list
# --------------------------------------------------------------------------- #
def list_cases():
    body = api_parse(BOOK)
    cases, section = [], None
    for el in body.descendants:
        if getattr(el, "name", None) == "b":
            m = re.match(r"§\s*\d+\s+(.+)", el.get_text(strip=True))
            if m:
                section = m.group(1).strip()
        if getattr(el, "name", None) == "li":
            links = {a.get_text(strip=True): a.get("href") for a in el.find_all("a")}
            sv, lo = links.get("Sachverhalt"), links.get("Lösung")
            if sv and lo:
                m = re.match(r"\s*(\d+[a-z]?)\)\s*(.+)", el.get_text(" ", strip=True))
                if not m:
                    continue
                num = m.group(1)
                name = re.sub(r"\s*:?\s*Sachverhalt\s*\|\s*L[oö]sung\s*$", "", m.group(2)).strip()
                cases.append({
                    "num": num, "name": name, "section": section,
                    "sv_title": _title(sv), "lo_title": _title(lo),
                })
    return cases


def _title(href):
    return urllib.parse.unquote(href.split("/wiki/")[-1]).replace("_", " ")


# --------------------------------------------------------------------------- #
# Footnotes  (same approach as scrape_lab: [^n] with links preserved)
# --------------------------------------------------------------------------- #
def extract_footnotes(body):
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


# --------------------------------------------------------------------------- #
# HTML -> markdown helpers
# --------------------------------------------------------------------------- #
def frag_md(node) -> str:
    raw = md(str(node), heading_style="atx", bullets="-", strip=["span"])
    raw = raw.replace("\\*", "*").replace("\\_", "_")
    raw = re.sub(r"[ \t]+\n", "\n", raw)
    return re.sub(r"\n{3,}", "\n\n", raw).strip()


def resolve_fn(t): return re.sub(r"@@FN(\d+)@@", r"[^\1]", t)


def slugify(s: str) -> str:
    s = s.lower()
    for k, v in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        s = s.replace(k, v)
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80].rsplit("-", 1)[0] if len(s) > 80 else s


def heading_info(el):
    if not isinstance(el, Tag):
        return None
    if re.fullmatch(r"h[1-6]", el.name or ""):
        return int(el.name[1]), el.get_text().strip()
    if el.name in ("div", "section") and any(str(c).startswith("mw-heading") for c in (el.get("class") or [])):
        h = el.find(re.compile(r"^h[1-6]$"))
        if h:
            return int(h.name[1]), h.get_text().strip()
    return None


def section_map(body):
    """Group top-level nodes under their h2 headings -> {title: [nodes]}."""
    out, title, nodes = [], None, []
    for el in body.children:
        hi = heading_info(el)
        if hi and hi[0] == 2:
            out.append((title, nodes)); title, nodes = hi[1], []
        else:
            nodes.append(el)
    out.append((title, nodes))
    return out


# --------------------------------------------------------------------------- #
# Didactic boxes -> labelled blockquotes
# --------------------------------------------------------------------------- #
def render_boxes_as_quotes(container):
    """Turn <div class='collapsible PrettyTextBox'> into a labelled blockquote,
    in place, so the surrounding markdown conversion keeps them clearly marked."""
    for box in container.select("div.PrettyTextBox, div.collapsible"):
        title_el = box.select_one(".title")
        label = title_el.get_text(" ", strip=True) if title_el else "Hinweis"
        if title_el:
            title_el.decompose()
        inner = resolve_fn(frag_md(box))
        quoted = "\n".join(f"> {ln}" if ln.strip() else ">" for ln in inner.splitlines())
        box.replace_with(NavigableString(f"\n> **{label}:**\n{quoted}\n"))


# --------------------------------------------------------------------------- #
# Metadata / instructions
# --------------------------------------------------------------------------- #
def detect_status(*bodies):
    """Return 'unfinished' if either page carries the OpenRewi Booksprint WIP banner."""
    for b in bodies:
        if b is None:
            continue
        if re.search(r"noch nicht fertig|laufenden Booksprint", b.get_text(" ")):
            return "unfinished"
    return "complete"


def labelled_value(body, label):
    m = re.search(rf"{label}\s*:?\s*([^\n]+)", body.get_text("\n"))
    return m.group(1).strip() if m else ""


def extract_tags(lo_body):
    val = labelled_value(lo_body, "Behandelte Themen")
    if not val:
        return []
    val = re.sub(r"\([^)]*\)", lambda m: m.group(0).replace(",", "\uE000"), val)  # shield commas in ()
    pieces = [p.strip().rstrip(".").replace("\uE000", ",") for p in re.split(r"[;,]", val) if p.strip()]
    return [p.replace(" ", "-") for p in pieces if len(p) <= 160]


def nodes_md(nodes):
    return resolve_fn(frag_md(BeautifulSoup("".join(str(n) for n in nodes), "html.parser")))


def clean_mediawiki_artifacts(text: str) -> str:
    if not text:
        return text
    # Strip the NewPP limit report block. The trigger reason at the end
    # varies per page (page_view, diff-page, edit-page, etc.), so match
    # any single token there rather than hardcoding one value.
    newpp_pattern = re.compile(
        r'NewPP limit report.*?Rendering was triggered because: \S+\s*',
        re.DOTALL | re.IGNORECASE
    )
    text = newpp_pattern.sub('', text)
    # Collapse duplicate '## Fußnoten' headings
    text = re.sub(r'(?:##\s*Fußnoten\s*\n\s*)+', '## Fußnoten\n\n', text)
    # Strip excess blank spaces
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# --------------------------------------------------------------------------- #
# Build one case
# --------------------------------------------------------------------------- #

def _law_filename(txt):
    t = re.sub(r"^Auszug\s+", "", txt).strip()
    if not t.startswith("§"):
        return f"auszug-{slugify(re.sub(r'\\s*\\(.*$', '', t))}.md"
    after = re.sub(r"^§+\s*\d+[a-z]?\s*", "", t)
    for tok in after.split():
        if sum(c.isupper() for c in tok) >= 2:
            return f"auszug-{slugify(tok)}.md"
    return f"auszug-{slugify(after)}.md"


def _is_law_name(t):
    if t.strip().startswith("§"):
        return False
    return bool(re.search(r"Auszug|[Gg]esetz|[Vv]erordnung|[Ss]atzung|[Bb]edingungen|"
                          r"[Vv]ertrag|buch|\([A-ZÄÖÜ][A-Za-zÄÖÜ0-9]{1,15}\)", t))


def _para_header_text(el):
    if not isinstance(el, Tag) or el.name not in ("p", "dd", "div", "li"):
        return None
    txt = el.get_text(" ", strip=True)
    if not txt or len(txt) > 90:
        return None
    bolds = el.find_all(["b", "strong"])
    if not bolds:
        return None
    boldtxt = " ".join(b.get_text(" ", strip=True) for b in bolds)
    if txt.replace(" ", "") != boldtxt.replace(" ", ""):
        return None
    # a whole-bold "§ N Section" that is really the book NAV is NOT a statute
    if re.match(r"§\s*\d+\s+[A-ZÄÖÜ]", txt) and not re.search(r"[a-zäöü]", txt.split()[-1][:1] or "z"):
        pass
    if txt.startswith("Auszug") or _is_law_name(txt):
        return txt
    if re.match(r"^§+\s*\d", txt) and any(sum(c.isupper() for c in w) >= 2 for w in txt.split()):
        return txt
    return None


def _inline_statute(el):
    if not isinstance(el, Tag) or el.name not in ("p", "dd", "li"):
        return None
    b = el.find(["b", "strong"])
    if not b:
        return None
    btxt = b.get_text(" ", strip=True)
    ptxt = el.get_text(" ", strip=True)
    if not re.match(r"§+\s*\d", btxt):
        return None
    if not ptxt.startswith(btxt[:6]) or (len(ptxt) - len(btxt)) < 60:
        return None
    return _law_filename(btxt)


def split_excerpts(facts_nodes):
    """From Sachverhalt narrative nodes, return (clean_facts_md, {filename: excerpt_md}).
    Scoped to the facts only -- the book nav/Inhaltsverzeichnis is never passed in."""
    facts, order, chunks = [], [], {}
    current = None
    for el in facts_nodes:
        if not isinstance(el, Tag):
            continue
        chunk = resolve_fn(frag_md(BeautifulSoup(str(el), "html.parser")))
        if not chunk.strip():
            continue
        inl = _inline_statute(el)
        if inl:
            chunks.setdefault(inl, []); order.append(inl) if inl not in order else None
            chunks[inl].append(chunk); current = inl; continue
        hdr = _para_header_text(el)
        if hdr:
            fn = _law_filename(hdr)
            chunks.setdefault(fn, []); order.append(fn) if fn not in order else None
            chunks[fn].append(chunk); current = fn; continue
        if current:
            chunks[current].append(chunk)
        else:
            facts.append(chunk)
    excerpts = {fn: "\n\n".join(chunks[fn]).strip() for fn in order}
    return "\n\n".join(facts).strip(), excerpts

def is_fallfrage_heading(t):
    """True if a Sachverhalt-page h2 heading is a question section --
    Fallfrage, Fallfragen, Fallfrage Abwandlung, Zusatzfrage, etc.
    Substring match on "frage" rather than a prefix check: confirmed across
    all 58 cases that no non-question heading (Sachverhalt, Abwandlung,
    Fussnoten, Hinweis, Bearbeiter*innenvermerk, Ausgangsfall) contains
    "frage", so this is safe and also catches fall-2's "Zusatzfrage",
    which a startswith("Fallfrage") check would miss.
    NOTE: fall-8 (Dublin-Roulette Teil 1) uses a single combined heading
    "Sachverhalt: Kurzfaelle mit Fragen und Abwandlungen" for the whole page
    instead of separate Sachverhalt/Fallfragen/Abwandlung sections. This
    check will also match that heading (it contains "Fragen"), but that
    alone does not fix that case -- its Sachverhalt extraction also fails
    since section_map never sees a section titled exactly "Sachverhalt".
    See MANUAL_REVIEW below -- it's flagged in the report, not silently
    "fixed" by this heading check."""
    return bool(t) and "frage" in t.lower()


# Cases whose page structure doesn't fit the standard
# Sachverhalt / Fallfragen / Abwandlung split -- flagged in report.md/report.csv
# only, not written into task.json, so task.json stays purely data-driven and
# these don't need to be remembered to "unflag" later if the source changes.
MANUAL_REVIEW = {
    "8": "Single combined heading 'Sachverhalt: Kurzfaelle mit Fragen und "
         "Abwandlungen' bundles multiple lettered mini-cases (A./B./C...); "
         "standard Sachverhalt/Fallfragen extraction does not apply. Needs "
         "hand-fixing, like Fall 5 in the Verwaltungsrecht book. Also marked "
         "'70% Work in Progress' in the source itself.",
}

def build_case(case):
    sv_body = api_parse(case["sv_title"])
    lo_body = api_parse(case["lo_title"])

    sv_fn = extract_footnotes(sv_body)
    lo_fn = extract_footnotes(lo_body)

    # -- Sachverhalt page sections (peel out any reproduced statutes) --
    sachverhalt_blocks, excerpts = [], {}
    for key in ("Sachverhalt", "Abwandlung"):
        for t, n in section_map(sv_body):
            if t == key:
                clean_facts, exc = split_excerpts([x for x in n if isinstance(x, Tag)])
                sachverhalt_blocks.append(f"## {key}\n\n{clean_facts}".strip())
                excerpts.update(exc)
    sachverhalt = "\n\n".join(b for b in sachverhalt_blocks if b).strip()

    # instructions = Fallfragen + Bearbeitungshinweis
    instr_parts = []
    for t, n in section_map(sv_body):
        if is_fallfrage_heading(t): #changed to fallfrage to catch both Fallfragen and fallfragen keywords
            # a Fallfragen section may run into the Bearbeitungshinweis; strip it here
            frag = nodes_md(n)
            frag = re.sub(r"\n?\**Bearbeitungshinweis\b.*", "", frag, flags=re.S).strip()
            instr_parts.append(frag)
    hinweis = re.search(r"(Bearbeitungshinweis\s*:?.*?)(?:\n\s*\n|\Z)",
                        sv_body.get_text("\n"), re.S)
    if hinweis:
        instr_parts.append("Bearbeitungshinweis: " +
                           re.sub(r"^\**Bearbeitungshinweis\s*:?\s*", "",
                                  re.sub(r"\s+", " ", hinweis.group(1)).strip()))
    # de-dup while preserving order
    seen, uniq = set(), []
    for p in instr_parts:
        p = p.strip()
        if p and p not in seen:
            seen.add(p); uniq.append(p)
    instructions = "\n\n".join(uniq).strip()

    # -- Lösung page: didactic boxes -> quotes, then Gutachten body --
    render_boxes_as_quotes(lo_body)
    loesung_parts = ["# Lösungsvorschlag", ""]
    started = False          # skip the leading metadata block until the first real heading
    META_RE = re.compile(r"^(Autor(innen|\*innen|en)?|Behandelte Themen|"
                         r"Zugrundeliegender Sachverhalt|Schwierigkeitsgrad)\s*:", re.I)
    for el in lo_body.children:
        hi = heading_info(el)
        if hi:
            started = True
            lvl = min(hi[0], 6)
            loesung_parts.append(f"{'#'*lvl} {resolve_fn(hi[1])}")
        else:
            frag = resolve_fn(frag_md(BeautifulSoup(str(el), "html.parser")))
            if not frag.strip():
                continue
            if not started:                              # still in the metadata preamble
                continue
            if "Inhaltsverzeichnis des Buches" in frag:
                continue
            loesung_parts.append(frag)
    # footnotes (merge both pages; Lösung has most)
    all_fn = {**sv_fn, **lo_fn}
    if all_fn:
        loesung_parts += ["", "## Fußnoten", ""]
        for n in sorted(all_fn, key=lambda x: int(x)):
            loesung_parts.append(f"[^{n}]: {all_fn[n]}")
    loesung = "\n\n".join(loesung_parts).strip() + "\n"

    loesung = clean_mediawiki_artifacts(loesung) + "\n"

    # -- metadata.md --
    authors = labelled_value(lo_body, "Autor(?:[*:]?in(?:nen)?|en)?") or labelled_value(sv_body, "Autor(?:[*:]?in(?:nen)?|en)?")
    difficulty = labelled_value(lo_body, "Schwierigkeitsgrad") or labelled_value(sv_body, "Schwierigkeitsgrad")
    themen = labelled_value(lo_body, "Behandelte Themen")
    metadata = (f"# Metadaten\n\n"
                f"**Fall:** {case['num']}) {case['name']}\n\n"
                f"**Autor*innen:** {authors}\n\n"
                f"**Schwierigkeitsgrad:** {difficulty}\n\n"
                f"**Behandelte Themen:** {themen}\n\n"
                f"**Abschnitt:** {case['section']}\n")

    tags = extract_tags(lo_body)
    status = detect_status(sv_body, lo_body)
    task = {
        "title": case["name"],
        "work_type": "draft",
        "tags": tags,
        "instructions": instructions,
        "deliverables": "fallloesung-sut.md",
        "license": LICENSE_TMPL.format(authors=authors or "AUTOR*IN"),
        "status": status,
    }
    return {"sachverhalt": sachverhalt, "metadata": metadata, "loesung": loesung,
            "task": task, "excerpts": excerpts,
            "n_footnotes": len(all_fn), "n_tags": len(tags), "n_excerpts": len(excerpts), "status": status}


def scrape_case(case, out_root=OUT_ROOT, force=False):
    sec_slug = slugify(case["section"] or "sonstige")
    case_slug = f"fall-{case['num']}-{slugify(case['name'])}"
    base = Path(out_root) / sec_slug / case_slug
    if (base / "task.json").exists() and not force:
        print(f"[skip] {base} exists"); return None

    built = build_case(case)
    (base / "documents").mkdir(parents=True, exist_ok=True)
    (base / "evals").mkdir(parents=True, exist_ok=True)
    (base / "task.json").write_text(json.dumps(built["task"], ensure_ascii=False, indent=2), "utf-8")
    (base / "documents" / "sachverhalt.md").write_text(built["sachverhalt"] + "\n", "utf-8")
    for fname, content in built["excerpts"].items():
        (base / "documents" / fname).write_text(content + "\n", "utf-8")
    (base / "documents" / "metadata.md").write_text(built["metadata"], "utf-8")
    (base / "evals" / "fallloesung-sut.md").write_text(built["loesung"], "utf-8")

    print(f"[ok] fall-{case['num']} {case['name'][:40]}")
    print(f"     dir: {base}")
    flag = "  [UNFINISHED]" if built["status"] == "unfinished" else ""
    print(f"     tags: {built['n_tags']} | excerpts: {built['n_excerpts']} | footnotes: {built['n_footnotes']}{flag}")
    return {"num": case["num"], "name": case["name"], "section": case["section"],
            "slug": case_slug, "n_tags": built["n_tags"],
            "n_excerpts": built["n_excerpts"], "n_footnotes": built["n_footnotes"],
            "status": built["status"], "instructions": built["task"]["instructions"][:200]}



def write_report(rows, out_dir):
    import csv
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    md_lines = ["# LAB-EU Asylrecht scrape report", "",
                f"{len(rows)} case(s). Review UNFINISHED cases and thin instructions before pushing.", "",
                "| # | Fall | status | section | tags | excerpts | footnotes |",
                "|---|------|--------|---------|-----:|---------:|----------:|"]
    for r in rows:
        md_lines.append(f"| {r['num']} | {r['name'][:38]} | {r['status']} | "
                        f"{slugify(r['section'] or '')[:24]} | {r['n_tags']} | "
                        f"{r['n_excerpts']} | {r['n_footnotes']} |")
    unfinished = [r for r in rows if r["status"] == "unfinished"]
    if unfinished:
        md_lines += ["", "## \u26a0 Unfinished cases", ""]
        md_lines += [f"- fall-{r['num']} {r['name']}" for r in unfinished]
    review = [r for r in rows if r["num"] in MANUAL_REVIEW]
    if review:
        md_lines += ["", "## \U0001f6a9 Manual review needed", "",
                     "These cases' page structure doesn't fit the standard "
                     "Sachverhalt/Fallfragen/Abwandlung split -- check the "
                     "output by hand before trusting it.", ""]
        md_lines += [f"- fall-{r['num']} {r['name']}: {MANUAL_REVIEW[r['num']]}"
                     for r in review]
    md_lines += ["", "## Instructions preview (check phrasing/thin cases)", ""]
    for r in rows:
        md_lines += [f"**{r['num']}) {r['name']}**  (`{r['status']}`)", "",
                     f"> {r['instructions']}", "", "---", ""]
    (Path(out_dir) / "report.md").write_text("\n".join(md_lines), "utf-8")

    with open(Path(out_dir) / "report.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["num","name","status","section","n_tags","n_excerpts",
                    "n_footnotes","manual_review","instructions"])
        for r in rows:
            w.writerow([r["num"], r["name"], r["status"], r["section"],
                        r["n_tags"], r["n_excerpts"], r["n_footnotes"],
                        MANUAL_REVIEW.get(r["num"], ""), r["instructions"]])
    print(f"\n[report] {Path(out_dir)/'report.md'}\n[report] {Path(out_dir)/'report.csv'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out", default="out")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cases = list_cases()
    print(f"[info] {len(cases)} cases on index")
    if args.list:
        for c in cases:
            print(f"  {c['num']:>3}) {c['name'][:45]:45s} [{slugify(c['section'] or '')}]")
        return
    targets = cases if args.all else cases[:1]
    out_root = f"{args.out}/tasks/de/asylrecht"
    rows = []
    for c in targets:
        try:
            info = scrape_case(c, out_root=out_root, force=args.force)
            if isinstance(info, dict):
                rows.append(info)
            time.sleep(2)
        except Exception as e:
            print(f"[FAIL] fall-{c['num']}: {e}")
    if rows:
        write_report(rows, args.out)


if __name__ == "__main__":
    main()