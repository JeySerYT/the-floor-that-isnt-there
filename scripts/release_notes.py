#!/usr/bin/env python3
"""Печатает заметки релиза из CHANGELOG.md для указанной версии."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def extract(changelog: str, version: str) -> str:
    heading = re.search(rf"^## {re.escape(version)}\s*$", changelog, re.MULTILINE)
    if heading is None:
        raise SystemExit(f"версия {version} не найдена в CHANGELOG.md")
    rest = changelog[heading.end():]
    next_heading = re.search(r"^## ", rest, re.MULTILINE)
    section = rest[: next_heading.start()] if next_heading else rest
    lines = section.strip().splitlines()
    if lines and lines[0].startswith("*") and lines[0].endswith("*"):
        lines = lines[1:]
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="версия без префикса v, например 0.5.0-alpha.1")
    parser.add_argument("--changelog", type=Path, default=ROOT / "CHANGELOG.md")
    args = parser.parse_args()
    changelog = args.changelog.read_text(encoding="utf-8")
    print(extract(changelog, args.version), end="")


if __name__ == "__main__":
    main()