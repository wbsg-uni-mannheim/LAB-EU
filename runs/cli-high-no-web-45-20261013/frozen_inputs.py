"""Load the immutable inputs shared by the two CLI benchmark arms."""
import json
from pathlib import Path

from run_opencode_taskset import normalize_deliverables, validate_task_dir

PARENT = Path(__file__).resolve().parent


def load_taskset(path):
    path = Path(path).resolve()
    if path != PARENT / "taskset.jsonl":
        raise ValueError("This benchmark only accepts its frozen taskset")
    rows = []
    for line in path.read_text().splitlines():
        row = json.loads(line)
        task_dir = Path(row["task_dir"]).resolve()
        task_dir.relative_to(PARENT / "input-snapshot")
        validate_task_dir(task_dir)
        task = json.loads((task_dir / "task.json").read_text())
        rows.append({**row, "task_dir": task_dir, "task": task,
                     "deliverables": normalize_deliverables(task, task_dir),
                     "allow_network": False})
    if len(rows) != 45 or len({row["task_id"] for row in rows}) != 45:
        raise ValueError("Expected exactly 45 unique cases")
    return rows
