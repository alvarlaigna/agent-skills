#!/usr/bin/env python3
"""Add the Alvar Design System foundation to an existing project.

Copies the tokens, the cn() helper, and the layout primitives (and optionally
the core components) into an existing repo, then prints the wiring steps. It
does not touch package.json or your build config.

    python add_to_project.py --dir . --base src --with-components
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"

FOUNDATION = ("styles", "lib", "primitives")


def copy_dir(src: Path, dst: Path, force: bool) -> list[str]:
    copied: list[str] = []
    for item in src.rglob("*"):
        if not item.is_file():
            continue
        target = dst / item.relative_to(src)
        if target.exists() and not force:
            print(f"  skip (exists): {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        copied.append(str(target))
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add the Alvar Design System to an existing project."
    )
    parser.add_argument("--dir", default=".", help="Project root (default: current directory).")
    parser.add_argument("--base", default="src", help="Source base inside the project (default: src).")
    parser.add_argument(
        "--with-components", action="store_true", help="Also copy the core components."
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite files that already exist."
    )
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory")
        return 1
    base = root / args.base

    dirs = list(FOUNDATION) + (["components"] if args.with_components else [])
    copied: list[str] = []
    for d in dirs:
        src = TEMPLATES / d
        if src.is_dir():
            copied += copy_dir(src, base / d, args.force)

    print(f"\nCopied {len(copied)} file(s) into {base}")
    print("\nFinish wiring it up:")
    deps = "clsx tailwind-merge class-variance-authority"
    if args.with_components:
        deps += " @radix-ui/react-dialog lucide-react"
    print(f"  1. npm install {deps}")
    print("     npm install -D tailwindcss @tailwindcss/vite   # if not already on Tailwind v4")
    print('  2. Import the stylesheet once at your app root:  import "@/styles/globals.css"')
    print('  3. Map the "@/" alias to your source base in vite.config and tsconfig paths.')
    print("  4. Toggle dark mode by adding/removing the `dark` class on <html>.")
    print("  5. Check components reference semantic tokens only:")
    print(f"       python {Path(__file__).parent / 'check_tokens.py'} --dir {args.base}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
