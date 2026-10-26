"""Write generation progress and a final artifact audit; never score answers."""
import datetime
import hashlib
import json
from pathlib import Path
import time

PARENT = Path(__file__).resolve().parent
ARMS = {"codex": "codex-astra-high", "claude": "claude-opus-5.5-high"}


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def summarize():
    summary = {"updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "grading": "not run; deferred by user", "arms": {}}
    for name, directory in ARMS.items():
        base = PARENT / directory
        status = read_json(PARENT / f"{name}-status.json")
        completed = []
        for path in sorted(base.rglob("metadata.json")):
            meta = read_json(path)
            if not meta:
                continue
            deliverables = []
            for expected in meta.get("expected_deliverables", []):
                output = path.parent / "submission" / expected
                if output.is_file():
                    content = output.read_bytes()
                    deliverables.append({"path": str(output.relative_to(PARENT)),
                                         "bytes": len(content),
                                         "words": len(content.decode(errors="replace").split()),
                                         "sha256": hashlib.sha256(content).hexdigest()})
            violations = meta.get("policy_violations", []) + meta.get("web_access_policy", {}).get("violations", [])
            artifact_ok = bool(deliverables) and all(item["bytes"] > 0 for item in deliverables)
            successful = meta.get("exit_code") == 0 and artifact_ok and not violations
            completed.append({"task_id": meta["task_id"], "successful": successful,
                              "exit_code": meta.get("exit_code"), "violations": violations,
                              "deliverables": deliverables})
        summary["arms"][name] = {
            "process_status": status.get("status", "starting"),
            "expected": 45, "started": len(list(base.rglob("stdout.jsonl"))),
            "completed": len(completed), "successful": sum(x["successful"] for x in completed),
            "failed": sum(not x["successful"] for x in completed), "cases": completed,
        }
    terminal = all(arm["process_status"] in {"completed", "failed"} for arm in summary["arms"].values())
    summary["status"] = ("completed" if all(arm["successful"] == 45 for arm in summary["arms"].values())
                         else "needs_attention") if terminal else "running"
    if terminal:
        hashes = read_json(PARENT / "source-hashes.json")
        summary["input_snapshot_mismatches"] = [name for name, expected in hashes.items()
            if not (PARENT / name).is_file() or hashlib.sha256((PARENT / name).read_bytes()).hexdigest() != expected]
        if summary["input_snapshot_mismatches"]:
            summary["status"] = "needs_attention"
    return summary, terminal


if __name__ == "__main__":
    while True:
        result, finished = summarize()
        temporary = PARENT / "generation-summary.tmp.json"
        temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(PARENT / "generation-summary.json")
        if finished:
            break
        time.sleep(15)
