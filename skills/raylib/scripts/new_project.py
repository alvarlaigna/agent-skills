#!/usr/bin/env python3
"""Scaffold a raylib project from skill templates.

Run from anywhere. Templates live beside this script in ../templates/.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"

PLACEHOLDERS = {
    "{{PROJECT_NAME}}": "name",
    "{{MODULE_PATH}}": "module",
    "{{YEAR}}": "year",
}


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip()).strip("_").lower()
    return slug or "my_game"


def substitute(text: str, values: dict[str, str]) -> str:
    for key, field in PLACEHOLDERS.items():
        text = text.replace(key, values.get(field, values["name"]))
    return text


def copy_tree(src: Path, dst: Path, values: dict[str, str], force: bool) -> list[str]:
    written: list[str] = []
    for path in sorted(src.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(src)
        out = dst / rel
        if out.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing file: {out}")
        out.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in {".c", ".cpp", ".h", ".go", ".mod", ".txt", ".html", ".md"} or path.name in {
            "Makefile", ".gitignore", "CMakeLists.txt"
        }:
            out.write_text(substitute(path.read_text(encoding="utf-8"), values), encoding="utf-8")
        else:
            shutil.copy2(path, out)
        written.append(str(out))
    return written


def ensure_empty_dir(path: Path, force: bool) -> None:
    if not path.exists():
        path.mkdir(parents=True)
        return
    if any(path.iterdir()) and not force:
        raise FileExistsError(
            f"Output directory is not empty: {path}\nUse --force to write anyway."
        )


def template_set(lang: str, layout: str) -> Path:
    if layout == "single":
        if lang == "c":
            return TEMPLATES / "c"
        if lang == "cpp":
            return TEMPLATES / "cpp"
        if lang == "go":
            return TEMPLATES / "go"
    if layout == "multi" and lang == "c":
        return TEMPLATES / "multi-file"
    raise ValueError(f"Unsupported combination: lang={lang}, layout={layout}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a raylib project from skill templates.")
    parser.add_argument("--out", required=True, type=Path, help="Target project directory")
    parser.add_argument("--name", required=True, help="Window title / project display name")
    parser.add_argument("--lang", choices=["c", "cpp", "go"], default="c")
    parser.add_argument("--layout", choices=["single", "multi"], default="single")
    parser.add_argument("--module", default="example.com/my-game", help="Go module path (go only)")
    parser.add_argument("--force", action="store_true", help="Allow writing into a non-empty directory")
    args = parser.parse_args()

    out: Path = args.out.resolve()
    values = {
        "name": args.name,
        "module": args.module,
        "year": str(datetime.now().year),
    }

    try:
        src = template_set(args.lang, args.layout)
        if not src.is_dir():
            print(f"error: template directory not found: {src}", file=sys.stderr)
            return 1
        ensure_empty_dir(out, args.force)
        written = copy_tree(src, out, values, args.force)

        # Always include web shell and gitignore for C/C++ layouts.
        if args.lang in {"c", "cpp"}:
            web_dst = out / "web"
            web_dst.mkdir(parents=True, exist_ok=True)
            shell_src = TEMPLATES / "web" / "minshell.html"
            shell_dst = web_dst / "minshell.html"
            shell_dst.write_text(
                substitute(shell_src.read_text(encoding="utf-8"), values), encoding="utf-8"
            )
            written.append(str(shell_dst))
            gi_src = TEMPLATES / ".gitignore"
            gi_dst = out / ".gitignore"
            if not gi_dst.exists() or args.force:
                gi_dst.write_text(gi_src.read_text(encoding="utf-8"), encoding="utf-8")
                written.append(str(gi_dst))
            resources = out / "resources"
            resources.mkdir(exist_ok=True)
            placeholder = resources / ".gitkeep"
            if not placeholder.exists():
                placeholder.write_text("", encoding="utf-8")
                written.append(str(placeholder))

        print(f"Created raylib project '{args.name}' at {out}")
        for path in written:
            print(f"  {path}")
        return 0
    except (FileExistsError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
