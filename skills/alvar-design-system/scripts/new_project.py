#!/usr/bin/env python3
"""Scaffold a new Vite + React + TypeScript app wired with the Alvar Design System.

Run from anywhere:

    python new_project.py --out ./my-app --name "My App"

Creates a runnable project: the foundation tokens, the layout primitives, the
core components, and a small demo App. Then:

    cd my-app && npm install && npm run dev
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"

# Reject characters that would break the generated index.html title or App.tsx JSX.
_UNSAFE_NAME = re.compile(r'[\x00-\x1f"\\`<>{}]')

# Design-system source folders copied into the new project's src/.
DS_DIRS = ("styles", "lib", "primitives", "components")

TEXT_SUFFIXES = {".json", ".ts", ".tsx", ".css", ".html", ".md", ".js", ".mjs"}


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "alvar-app"


def replace_placeholders(root: Path, name: str, slug: str) -> None:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            if "__APP_NAME__" in text or "__APP_SLUG__" in text:
                text = text.replace("__APP_NAME__", name).replace("__APP_SLUG__", slug)
                path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a new app with the Alvar Design System."
    )
    parser.add_argument("--out", required=True, help="Target directory for the new project.")
    parser.add_argument("--name", help="App name (default: the output folder name).")
    parser.add_argument(
        "--force", action="store_true", help="Write into a non-empty directory."
    )
    args = parser.parse_args()

    out = Path(args.out).resolve()
    name = args.name or out.name
    if _UNSAFE_NAME.search(name):
        print(
            "error: --name may not contain quotes, backslashes, backticks, "
            "angle brackets, braces, or control characters"
        )
        return 1
    slug = slugify(name)

    if out.exists() and any(out.iterdir()) and not args.force:
        print(f"error: {out} exists and is not empty (use --force to write anyway)")
        return 1

    project = TEMPLATES / "project"
    if not project.is_dir():
        print(f"error: templates not found at {project}")
        return 1

    # 1. Copy the project skeleton (root files + src/main.tsx, src/App.tsx).
    shutil.copytree(project, out, dirs_exist_ok=True)

    # 2. Copy the design-system source into src/.
    for d in DS_DIRS:
        src = TEMPLATES / d
        if src.is_dir():
            shutil.copytree(src, out / "src" / d, dirs_exist_ok=True)

    # 3. Fill in the project name.
    replace_placeholders(out, name, slug)

    print(f"Created {name} at {out}")
    print("\nNext steps:")
    print(f"  cd {out}")
    print("  npm install")
    print("  npm run dev")
    return 0


if __name__ == "__main__":
    sys.exit(main())
