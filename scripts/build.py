#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    python = sys.executable
    if not root.exists():
        print("Unable to resolve repository root.")
        return 1

    sep = ";" if os.name == "nt" else ":"
    data_paths = [
        f"{root / 'app' / 'templates'}{sep}app/templates",
        f"{root / 'app' / 'static'}{sep}app/static",
    ]
    args = [
        python,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "Fetal MRI Calculator",
        *[f"--add-data={value}" for value in data_paths],
        str(root / "app" / "main.py"),
    ]

    print("Building cross-platform executable using PyInstaller...")
    subprocess.run(args, check=True)
    print("Build complete. Find the executable in the dist/ directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
