"""Run the Claude arm using this comparison's immutable input snapshot."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import run_claude_taskset
from frozen_inputs import load_taskset

run_claude_taskset.load_taskset = load_taskset

if __name__ == "__main__":
    raise SystemExit(run_claude_taskset.main())
