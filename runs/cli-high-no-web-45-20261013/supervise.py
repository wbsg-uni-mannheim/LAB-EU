"""Record a durable completion marker for a foreground benchmark command."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


if __name__ == "__main__":
    status_file = Path(sys.argv[1]).resolve()
    command = sys.argv[2:]
    state = {"supervisor_pid": os.getpid(), "command": command, "started_at": now(),
             "status": "running"}
    status_file.write_text(json.dumps(state, indent=2) + "\n")
    try:
        child = subprocess.Popen(command)
        state["runner_pid"] = child.pid
        status_file.write_text(json.dumps(state, indent=2) + "\n")
        state["exit_code"] = child.wait()
        state["status"] = "completed" if state["exit_code"] == 0 else "failed"
    except Exception as exc:
        state.update(status="failed", error=str(exc))
    state["ended_at"] = now()
    status_file.write_text(json.dumps(state, indent=2) + "\n")
