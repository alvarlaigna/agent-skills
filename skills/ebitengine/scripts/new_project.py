#!/usr/bin/env python3
"""Scaffold an Ebitengine project from skill templates.

Run from anywhere. Templates live beside this script in ../templates/.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"

# Reject characters that would break the generated index.html title/status or Go source.
_UNSAFE_NAME = re.compile(r'[\x00-\x1f"\\`<>{}]')


def substitute(text: str, values: dict[str, str]) -> str:
    for key in ("{{PROJECT_NAME}}", "{{MODULE_PATH}}", "{{YEAR}}"):
        field = key.strip("{}").lower().replace("project_", "").replace("module_", "module")
        if key == "{{PROJECT_NAME}}":
            text = text.replace(key, values["name"])
        elif key == "{{MODULE_PATH}}":
            text = text.replace(key, values["module"])
        elif key == "{{YEAR}}":
            text = text.replace(key, values["year"])
    return text


def copy_templates(dst: Path, values: dict[str, str], force: bool) -> list[str]:
    written: list[str] = []
    for path in sorted(TEMPLATES.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(TEMPLATES)
        out = dst / rel
        if out.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing file: {out}")
        out.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in {".go", ".mod", ".html", ".gitkeep"} or path.name == ".gitignore":
            out.write_text(substitute(path.read_text(encoding="utf-8"), values), encoding="utf-8")
        else:
            out.write_bytes(path.read_bytes())
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold an Ebitengine project from skill templates.")
    parser.add_argument("--out", required=True, type=Path, help="Target project directory")
    parser.add_argument("--name", required=True, help="Window title / project display name")
    parser.add_argument("--module", default="example.com/my-game", help="Go module path")
    parser.add_argument("--force", action="store_true", help="Allow writing into a non-empty directory")
    args = parser.parse_args()

    out = args.out.resolve()
    if _UNSAFE_NAME.search(args.name):
        print(
            "error: --name may not contain quotes, backslashes, backticks, "
            "angle brackets, braces, or control characters",
            file=sys.stderr,
        )
        return 1
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", args.module):
        print("error: module path contains invalid characters", file=sys.stderr)
        return 1

    values = {
        "name": args.name,
        "module": args.module,
        "year": str(datetime.now().year),
    }

    try:
        ensure_empty_dir(out, args.force)
        written = copy_templates(out, values, args.force)
        print(f"Created Ebitengine project '{args.name}' at {out}")
        for path in written:
            print(f"  {path}")
        print("Next: cd to the project and run `go mod tidy` then `go test ./...`")
        return 0
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
