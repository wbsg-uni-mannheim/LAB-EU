"""Run Astra high on all 45 frozen cases, with external research disabled."""
import json
from pathlib import Path
import sys

PARENT = Path(__file__).resolve().parent
ROOT = PARENT.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_codex_taskset as harness  # noqa: E402
from frozen_inputs import load_taskset  # noqa: E402

original_build = harness.build_codex_command
original_manifest = harness.write_manifest
original_run_one = harness.run_one_task


def build(args, workspace, final_message):
    command = original_build(args, workspace, final_message)
    index = command.index("exec") + 1
    command[index:index] = [
        "--ignore-user-config", "--ignore-rules",
        "--config", 'web_search="disabled"',
        "--config", "sandbox_workspace_write.network_access=false",
        "--config", "project_doc_max_bytes=0",
        "--config", "features.apps=false",
        "--config", "features.multi_agent=false",
        "--config", "features.hooks=false",
        "--config", "features.browser_use=false",
        "--config", "features.browser_use_external=false",
        "--config", "features.computer_use=false",
        "--config", "features.in_app_browser=false",
        "--config", "plugins={}",
        "--config", "mcp_servers={}",
    ]
    return command


def augment(path):
    data = json.loads(path.read_text())
    data.update({"external_research_mode": "none",
                 "user_config_and_configured_tools_loaded": False,
                 "mcp_servers_enabled": False,
                 "protocol": str(PARENT / "protocol.json")})
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return data


def manifest(args, run_dir, *rest):
    original_manifest(args, run_dir, *rest)
    augment(run_dir / "manifest.json")


def run_one(args, row, run_dir):
    original_run_one(args, row, run_dir)
    return augment(run_dir / "tasks" / harness.safe_task_id(row["task_id"]) / "metadata.json")


if __name__ == "__main__":
    harness.load_taskset = load_taskset
    harness.build_codex_command = build
    harness.write_manifest = manifest
    harness.run_one_task = run_one
    extra = sys.argv[1:]
    sys.argv = [__file__, "--taskset", str(PARENT / "taskset.jsonl"),
                "--runs-dir", str(PARENT), "--run-name", "codex-astra-high",
                "--model", "gpt-6-astra", "--reasoning-effort", "high",
                "--tool-access", "workspace", "--timeout-seconds", "3600",
                "--parallel", "3", "--max-attempts", "1", "--no-web-search", *extra]
    raise SystemExit(harness.main())
