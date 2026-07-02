# Prompt Templates

Dieses Verzeichnis enthält die aktiven Prompt-Templates für LAB-EU. Die Templates sind bewusst vom Python-Code getrennt, damit juristische Reviewer Formulierungen prüfen und verbessern können, ohne Implementierungsdetails anfassen zu müssen.

Bitte Platzhalter in geschweiften Klammern wie `{task_title}` oder `{agent_output}` nicht entfernen oder umbenennen. Diese werden vom Code automatisch befüllt.

## Verzeichnisstruktur

- `rubric_generation/`: Prompts für die Erzeugung von Rubrics aus menschlichen Lösungen.
  - `atomize_solution.*`: Zerlegung der Lösung in prüfbare Antwort-Atome.
  - `generate_candidate_criteria.*`: Erzeugung des Kandidaten-Pools. Wird dreimal ausgeführt, je einmal pro Generator-Rolle.
  - `roles/`: Die drei Generator-Rollen (doctrine, fact_grounding, adversary), die an den Candidate-System-Prompt angehängt werden.
  - `prune_rubric.*`: Deduplizierung des Kandidaten-Pools zu einem atomaren Rubric.
  - `refine_rubric.*`: Reparatur von Kriterien, die die Musterlösung in der Kalibrierung nicht bestanden hat.
  - `tag_criteria.*`: Nicht bewertende Analyse-Tags pro Kriterium (Funktion nach Gutachtenstil-Schritten und Prüfungsstation), für Auswertungen nach juristischen Kategorien.
- `evaluation/`: Prompts für die Bewertung einer Agentenantwort gegen ein einzelnes Rubric-Kriterium (Evidenz-Zitate, Begründung, dann Verdikt).
- `harness/`: Prompts, die an den Solver für eine Benchmark-Aufgabe gehen.
  - `solve_task.txt`: Agenten-Harness (OpenCode) mit Datei-Workspace.
  - `solve_task_baseline.txt`: Einzelaufruf-Baseline ohne Agentenschleife; Dokumente werden direkt in den Prompt eingefügt.

## Review-Hinweise

- Inhaltliche Änderungen an den juristischen Bewertungsregeln gehören in die Prompt-Dateien, nicht in den Code.
- Die JSON-Feldnamen sollten auf Englisch bleiben, weil die Scripts diese Felder erwarten.
- Die Sprache der Rubrics soll der Sprache des Falls folgen, damit keine Übersetzungsunschärfe entsteht.
