#!/usr/bin/env python3
"""Simple script to run ruff with fixes."""

import subprocess
import sys


def main():
    # Run ruff check with fix
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "src", "tests", "--fix"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
