#!/usr/bin/env python3
"""Start the LAB-EU Lawyer Workbench on the local loopback interface."""

from __future__ import annotations

import argparse
import pathlib
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from workbench import create_app  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local LAB-EU Lawyer Workbench.")
    parser.add_argument("--port", type=int, default=5050)
    args = parser.parse_args()
    create_app().run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
