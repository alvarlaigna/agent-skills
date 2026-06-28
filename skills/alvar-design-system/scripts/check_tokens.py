#!/usr/bin/env python3
"""Lint components for raw hex colours and primitive token references.

Components in the Alvar Design System reference SEMANTIC tokens only
(bg-primary, text-foreground, var(--color-...)). Raw hex values and primitive
tokens (--ember-500, --neutral-900, --navy-ink, ...) belong in tokens.css, not
in components, because only the semantic layer is remapped per theme.

    python check_tokens.py --dir src

Exits non-zero if any violation is found. tokens.css and globals.css are exempt
(that is where primitives are defined).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCAN_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".css"}
EXEMPT_NAMES = {"tokens.css", "globals.css"}

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
PRIMITIVE_RE = re.compile(
    r"--(?:ember|neutral|green|amber|red|blue)-\d{2,3}\b"
    r"|--(?:snow-white|classic-linen|navy-ink|ember-red)\b"
)


def scan_file(path: Path) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for token in HEX_RE.findall(line):
            hits.append((i, token))
        for token in PRIMITIVE_RE.findall(line):
            hits.append((i, token))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Flag raw hex and primitive tokens used inside components."
    )
    parser.add_argument("--dir", default="src", help="Directory to scan (default: src).")
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    if not root.exists():
        print(f"error: {root} does not exist")
        return 1

    total = 0
    files = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if path.name in EXEMPT_NAMES:
            continue
        hits = scan_file(path)
        if hits:
            files += 1
            rel = path.relative_to(root).as_posix()
            for line_no, token in hits:
                print(f"{rel}:{line_no}: {token}")
                total += 1

    if total:
        print(
            f"\n{total} violation(s) in {files} file(s). "
            f"Move each value into tokens.css and reference a semantic token."
        )
        return 1
    print("OK: components reference semantic tokens only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
