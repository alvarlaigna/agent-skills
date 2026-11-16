#!/usr/bin/env python3
"""Write agent rule files and Git settings into an Unreal project.

    python init_agent_files.py --project ./MyGame
    python init_agent_files.py --project ./MyGame --only AGENTS.md CLAUDE.md

Copies from ../templates/: AGENTS.md, CLAUDE.md, .gitignore, .gitattributes (Git LFS).
Fills in the project name and engine association. Refuses to overwrite an
existing file unless --force. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
FILES = {  # template name -> file name in the project
    "AGENTS.md.template": "AGENTS.md",
    "CLAUDE.md.template": "CLAUDE.md",
    "gitignore": ".gitignore",
    "gitattributes": ".gitattributes",
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".", help="project folder containing the .uproject")
    ap.add_argument("--only", nargs="+", choices=list(FILES.values()), help="write only these files")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    a = ap.parse_args(argv)

    project = Path(a.project).resolve()
    uprojects = sorted(project.glob("*.uproject"))
    if len(uprojects) != 1:
        print(f"error: expected one .uproject in {project}, found {len(uprojects)}", file=sys.stderr)
        return 2
    up = uprojects[0]
    try:
        assoc = json.loads(up.read_text(encoding="utf-8-sig")).get("EngineAssociation", "") or "source build"
    except json.JSONDecodeError:
        assoc = "unknown"
    values = {"{{PROJECT_NAME}}": up.stem, "{{ENGINE_ASSOCIATION}}": str(assoc)}

    wrote, skipped = [], []
    for template, target in FILES.items():
        if a.only and target not in a.only:
            continue
        dst = project / target
        if dst.exists() and not a.force:
            skipped.append(target)
            continue
        text = (TEMPLATES / template).read_text(encoding="utf-8")
        for key, value in values.items():
            text = text.replace(key, value)
        dst.write_text(text, encoding="utf-8", newline="\n")
        wrote.append(target)

    for f in wrote:
        print(f"wrote   {project / f}")
    for f in skipped:
        print(f"skipped {project / f} (exists; merge by hand or use --force)")
    if ".gitattributes" in wrote:
        print("next: run `git lfs install` once on each machine before committing assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
