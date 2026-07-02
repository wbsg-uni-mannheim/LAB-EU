#!/usr/bin/env python3
"""Judge all submissions in a LAB-EU harness run directory."""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Judge a LAB-EU OpenCode run.")
    parser.add_argument("run_dir", type=pathlib.Path, help="Run directory containing manifest.json and tasks/.")
    parser.add_argument("--judge-model", default="gpt-5.5")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def task_metadata_paths(run_dir: pathlib.Path) -> list[pathlib.Path]:
    tasks_dir = run_dir / "tasks"
    if not tasks_dir.is_dir():
        raise SystemExit(f"Missing tasks directory: {tasks_dir}")
    return sorted(tasks_dir.glob("*/metadata.json"))


def judge_one(args: argparse.Namespace, metadata_path: pathlib.Path) -> tuple[pathlib.Path, int]:
    metadata = load_json(metadata_path)
    task_dir = pathlib.Path(metadata["source_task_dir"])
    submission_dir = metadata_path.parent / "submission"
    if not task_dir.exists():
        raise RuntimeError(f"Missing source task dir for {metadata_path}: {task_dir}")
    if not submission_dir.is_dir():
        raise RuntimeError(f"Missing submission dir for {metadata_path}: {submission_dir}")

    command = [
        args.python,
        "-m",
        "evaluation.run",
        str(task_dir),
        str(submission_dir),
        "--judge-model",
        args.judge_model,
    ]

    if args.dry_run:
        print(" ".join(command))
        return metadata_path, 0

    stdout_path = metadata_path.parent / "judge.stdout.log"
    stderr_path = metadata_path.parent / "judge.stderr.log"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        result = subprocess.run(command, cwd=REPO_ROOT, stdout=stdout, stderr=stderr, check=False)

    submission_scores = submission_dir / "scores.json"
    task_scores = metadata_path.parent / "scores.json"
    if submission_scores.exists():
        shutil.copy2(submission_scores, task_scores)

    return metadata_path, result.returncode


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir if args.run_dir.is_absolute() else REPO_ROOT / args.run_dir
    if not (run_dir / "manifest.json").exists():
        raise SystemExit(f"Missing run manifest: {run_dir / 'manifest.json'}")

    paths = task_metadata_paths(run_dir)
    if not paths:
        raise SystemExit(f"No task metadata found under {run_dir / 'tasks'}")

    failures = 0
    max_workers = max(1, args.parallel)
    if max_workers == 1:
        for path in paths:
            _path, code = judge_one(args, path)
            failures += int(code != 0)
            print(f"{path.parent.name}: judge_exit={code}")
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_path = {pool.submit(judge_one, args, path): path for path in paths}
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    _path, code = future.result()
                except Exception as exc:  # noqa: BLE001
                    failures += 1
                    print(f"{path.parent.name}: judge failed: {exc}", file=sys.stderr)
                    continue
                failures += int(code != 0)
                print(f"{path.parent.name}: judge_exit={code}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
