#!/usr/bin/env python3
"""Soll-Ist-Abgleich der Phase-H-Negativmutanten gegen expectations.json.

Vergleicht je Mutant die Content-Verdicts mit dem Positivlauf desselben Falls:
- must_fail-Kriterien müssen im Mutanten scheitern;
- must_not_fail-Kriterien dürfen nicht scheitern (Folgesanktions-Check);
- weitere neue Fails werden als "erwartet" eingestuft, wenn sie ausschließlich
  auf die mutierte bzw. fehlende Datei beschränkt sind, sonst als "sachfremd".
"""

from __future__ import annotations

import json
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent
NEG = BASE / "negativpruefung"
POS = BASE / "positivpruefung"
RUBRICS = {
    "allesch": "tasks/de/oeffentliches-recht/referendariat/Allesch-BayVBl-2024/evals/rubric.second-exam-pilot-v1.json",
    "kaess": "tasks/de/oeffentliches-recht/referendariat/Kaess-BayVBl-2026/evals/rubric.second-exam-pilot-v1.json",
    "koehl": "tasks/de/oeffentliches-recht/referendariat/Köhl-BayVBl-2025/evals/rubric.second-exam-pilot-v1.json",
    "oertel": "tasks/de/oeffentliches-recht/referendariat/Oertel-BayVBl-2025_104ff_137ff/evals/rubric.second-exam-v1.json",
    "schoemig": "tasks/de/oeffentliches-recht/referendariat/Schömig-BayVBl-2026/evals/rubric.second-exam-v1.json",
    "decker": "tasks/de/oeffentliches-recht/referendariat/Decker-BayVBl-2024/evals/rubric.second-exam-v1.json",
    "gregor": "tasks/de/oeffentliches-recht/referendariat/Gregor-BayVBl-2024/evals/rubric.second-exam-v1.json",
    "hasl-kleiber": "tasks/de/oeffentliches-recht/referendariat/Hasl-Kleiber-BayVBl-2024/evals/rubric.second-exam-v1.json",
    "kaess-ex2": "tasks/de/oeffentliches-recht/referendariat/Kaess-BayVBl-2024_ex2/evals/rubric.second-exam-v1.json",
    "koehl-2024": "tasks/de/oeffentliches-recht/referendariat/Köhl_BayVBl-2024/evals/rubric.second-exam-v1.json",
    "oertel-537": "tasks/de/oeffentliches-recht/referendariat/Oertel-BayVBl-2025_537ff_572ff/evals/rubric.second-exam-v1.json",
    "possart": "tasks/de/oeffentliches-recht/referendariat/Possart-BayVBl-2025_392ff_426ff/evals/rubric.second-exam-v1.json",
    "wolff": "tasks/de/oeffentliches-recht/referendariat/Wolff-BayVBl-2026/evals/rubric.second-exam-v1.json",
    "weber": "tasks/de/oeffentliches-recht/referendariat/Weber-BayVBl-2025/evals/rubric.second-exam-v1.json",
    "zoellner": "tasks/de/oeffentliches-recht/referendariat/Zöllner-BayVBl-2025/evals/rubric.second-exam-v1.json",
}
MUTATED_FILES = {
    "allesch-m1-hilfsgutachten-fehlt": {"hilfsgutachten-sut.md"},
    "allesch-m2-ossram-in-falscher-datei": {"mandantenschreiben-sut.md", "hilfsgutachten-sut.md"},
    "allesch-m3-ohne-antraege": {"klageerwiderung-sut.md"},
    "allesch-m4-mandantenschreiben-als-gutachten": {"mandantenschreiben-sut.md"},
    "kaess-m5-hilfsgutachten-fehlt": {"hilfsgutachten-sut.md"},
    "kaess-m6-ohne-zulassungsantrag": {"schriftsatz-an-das-gericht-sut.md"},
    "koehl-m7-tenor-widerspruch": {"urteil-sut.md"},
    "koehl-m8-begruendung-fehlt": {"urteil-sut.md"},
    "oertel-m9-tenor-widerspruch": {"beschluss-des-bayerischen-verwaltungsgerichts-augsburg-sut.md"},
    "oertel-m10-hilfsgutachten-fehlt": {"hilfsgutachten-sut.md"},
    "schoemig-m11-tenor-widerspruch": {"urteil-sut.md"},
    "schoemig-m12-hilfsgutachten-fehlt": {"hilfsgutachten-sut.md"},
    "decker-m13-tenor-widerspruch": {"urteil-sut.md"},
    "decker-m14-hilfsgutachten-fehlt": {"hilfsgutachten-sut.md"},
    "gregor-m15-tenor-widerspruch": {
        "entscheidung-des-bayerischen-verwaltungsgerichts-muenchen-sut.md"
    },
    "gregor-m16-hilfsgutachten-fehlt": {"hilfsgutachten-sut.md"},
    "hasl-kleiber-m17-ohne-antraege": {"schriftsatz-sut.md"},
    "hasl-kleiber-m18-bauherr-in-falscher-datei": {
        "schriftsatz-sut.md",
        "mandantenschreiben-sut.md",
    },
    "kaess-ex2-m19-tenor-widerspruch": {
        "entscheidung-des-bayerischen-verwaltungsgerichts-regensburg-sut.md"
    },
    "kaess-ex2-m20-hilfsgutachten-fehlt": {"hilfsgutachten-sut.md"},
    "koehl-2024-m21-ohne-verweisung": {
        "entscheidung-des-bayerischen-verwaltungsgerichtshofs-sut.md"
    },
    "koehl-2024-m22-hilfsgutachten-fehlt": {"hilfsgutachten-sut.md"},
    "oertel-537-m23-tenor-widerspruch": {
        "urteil-des-bayerischen-verwaltungsgerichts-augsburg-sut.md"
    },
    "oertel-537-m24-hilfsgutachten-fehlt": {"hilfsgutachten-sut.md"},
    "possart-m25-tenor-widerspruch": {"entscheidung-sut.md"},
    "possart-m26-hilfsgutachten-fehlt": {"hilfsgutachten-sut.md"},
    "wolff-m27-tenor-widerspruch": {"gutachten-sut.md"},
    "wolff-m28-hilfsgutachten-fehlt": {"hilfsgutachten-sut.md"},
    "weber-m29-ohne-antrag": {"schriftsatz-sut.md"},
    "weber-m30-hilfsgutachten-fehlt": {"hilfsgutachten-sut.md"},
    "zoellner-m31-ohne-antrag": {"eilantrag-fraktionsausschluss-sut.md"},
    "zoellner-m32-als-gutachten": {"eilantrag-fraktionsausschluss-sut.md"},
}


def content_fails(scores: dict) -> dict[str, dict]:
    return {
        r["id"]: r
        for r in scores["criteria_results"]
        if r.get("verdict") != "pass"
    }


def main() -> int:
    repo = BASE.parents[1]
    expectations = json.loads((NEG / "expectations.json").read_text(encoding="utf-8"))
    rubric_deliverables: dict[str, dict[str, list[str]]] = {}
    for fall, task_dir in RUBRICS.items():
        rubric = json.loads((repo / task_dir).read_text(encoding="utf-8"))
        rubric_deliverables[fall] = {
            c["id"]: [str(n) for n in (c.get("deliverables") or [])] for c in rubric["criteria"]
        }

    overall_ok = True
    for mutant, expectation in expectations.items():
        # Longest match first, so "hasl-kleiber-m17-..." maps to "hasl-kleiber", not "hasl".
        fall = next(
            (name for name in sorted(RUBRICS, key=len, reverse=True) if mutant.startswith(name)),
            "",
        )
        if not fall:
            print(f"## {mutant}: kein Fall zugeordnet")
            overall_ok = False
            continue
        scores_path = NEG / mutant / "submission" / "scores.json"
        if not scores_path.exists():
            print(f"## {mutant}: scores.json fehlt (Lauf unvollständig?)")
            overall_ok = False
            continue
        mutant_scores = json.loads(scores_path.read_text(encoding="utf-8"))
        pos_path = POS / fall / "submission" / "scores.json"
        if not pos_path.exists():
            pos_path = POS / fall / "submission" / "scores.committee.json"
        positive_scores = json.loads(pos_path.read_text(encoding="utf-8"))
        mutant_fails = content_fails(mutant_scores)
        positive_fails = set(content_fails(positive_scores))
        new_fails = {cid: r for cid, r in mutant_fails.items() if cid not in positive_fails}

        technical = sorted(
            cid for cid, r in new_fails.items() if r.get("resolution") == "unresolved"
        )
        must_fail = set(expectation["must_fail"])
        must_not = set(expectation.get("must_not_fail") or [])
        missed = sorted(must_fail - set(mutant_fails))
        violated = sorted(must_not & set(mutant_fails))

        deliv = rubric_deliverables[fall]
        mutated = MUTATED_FILES[mutant]
        substance_loss = set(expectation.get("expected_substance_loss") or [])
        collateral = []
        expected_extra = []
        for cid in sorted(set(new_fails) - must_fail - set(technical)):
            if cid not in deliv:
                continue  # Kriterium wurde nach dem Mutantenlauf aus der Rubrik entfernt
            files = deliv.get(cid) or []
            if (files and set(files) <= mutated) or cid in substance_loss:
                expected_extra.append(cid)
            else:
                collateral.append(cid)

        status = "OK" if not missed and not violated and not collateral else "PRÜFEN"
        if status != "OK":
            overall_ok = False
        print(f"## {mutant}: {status}")
        print(f"   Mutation: {expectation['mutation']}")
        print(f"   Muss-Fails erwischt: {sorted(must_fail & set(mutant_fails))}")
        if missed:
            print(f"   VERFEHLT (muss failen, tat es nicht): {missed}")
        if violated:
            print(f"   FOLGESANKTION (must_not_fail gescheitert): {violated}")
        if expected_extra:
            print(f"   Weitere erwartete Fails (nur mutierte Datei): {expected_extra}")
        if collateral:
            print(f"   SACHFREMDE Fails: {collateral}")
        if technical:
            print(f"   Technische Fails (unresolved): {technical}")
    print()
    print("GESAMT:", "alle Mutanten wie erwartet" if overall_ok else "Abweichungen vorhanden – siehe PRÜFEN")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
