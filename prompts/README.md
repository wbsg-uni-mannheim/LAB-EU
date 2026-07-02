# Prompt Templates

Dieses Verzeichnis enthält die aktiven Prompt-Templates für LAB-EU. Die Templates sind bewusst vom Python-Code getrennt, damit juristische Reviewer Formulierungen prüfen und verbessern können, ohne Implementierungsdetails anfassen zu müssen.

Bitte Platzhalter in geschweiften Klammern wie `{task_title}` oder `{agent_output}` nicht entfernen oder umbenennen. Diese werden vom Code automatisch befüllt.

## Verzeichnisstruktur

- `rubric_generation/`: Prompts für die Erzeugung von Rubrics aus menschlichen Lösungen.
- `evaluation/`: Prompts für die Bewertung einer Agentenantwort gegen ein einzelnes Rubric-Kriterium.
- `harness/`: Prompts, die an den Solver-Agenten für eine Benchmark-Aufgabe gehen.

## Review-Hinweise

- Inhaltliche Änderungen an den juristischen Bewertungsregeln gehören in die Prompt-Dateien, nicht in den Code.
- Die JSON-Feldnamen sollten auf Englisch bleiben, weil die Scripts diese Felder erwarten.
- Die Sprache der Rubrics soll der Sprache des Falls folgen, damit keine Übersetzungsunschärfe entsteht.
