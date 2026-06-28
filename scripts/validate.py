#!/usr/bin/env python3
"""Validate the skills and Claude plugin manifests in this repository.

A small, dependency-free check for the most common mistakes. For the full Agent
Skills standard, use `skills-ref validate` (https://agentskills.io). For the
plugin and marketplace manifests, use `claude plugin validate .`.

Run from anywhere:

    python scripts/validate.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
PLUGIN_DIR = ROOT / ".claude-plugin"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED_WORDS = ("anthropic", "claude")

# Marketplace names Anthropic reserves for official use.
RESERVED_MARKETPLACES = {
    "claude-code-marketplace", "claude-code-plugins", "claude-plugins-official",
    "claude-plugins-community", "claude-community", "anthropic-marketplace",
    "anthropic-plugins", "agent-skills", "anthropic-agent-skills",
    "knowledge-work-plugins", "life-sciences", "claude-for-legal",
    "claude-for-financial-services", "financial-services-plugins",
}

errors: list[str] = []
warnings: list[str] = []


def parse_frontmatter(text: str):
    """Return top-level key/value pairs from leading YAML frontmatter.

    Intentionally minimal: reads unindented `key: value` lines and ignores
    nested blocks. Enough for the checks below, not a full YAML parser.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if not line or line[0] in (" ", "\t", "#"):
            continue  # nested key, blank line, or comment
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[key.strip()] = value
    return None  # no closing delimiter


def check_skill(skill_md: Path) -> None:
    rel = skill_md.relative_to(ROOT).as_posix()
    folder = skill_md.parent.name
    text = skill_md.read_text(encoding="utf-8")

    fields = parse_frontmatter(text)
    if fields is None:
        errors.append(f"{rel}: missing or unterminated YAML frontmatter")
        return

    name = fields.get("name")
    if not name:
        errors.append(f"{rel}: frontmatter is missing `name`")
    else:
        if not NAME_RE.match(name):
            errors.append(f"{rel}: name '{name}' must be lowercase letters, "
                          f"numbers, and single hyphens")
        if len(name) > 64:
            errors.append(f"{rel}: name '{name}' exceeds 64 characters")
        if name != folder:
            errors.append(f"{rel}: name '{name}' must match the folder "
                          f"'{folder}'")
        if any(word in name for word in RESERVED_WORDS):
            errors.append(f"{rel}: name '{name}' must not contain "
                          f"{RESERVED_WORDS}")

    description = fields.get("description")
    if not description:
        errors.append(f"{rel}: frontmatter is missing `description`")
    elif len(description) > 1024:
        errors.append(f"{rel}: description is {len(description)} characters "
                      f"(max 1024)")

    body = text.split("---", 2)[-1]
    body_lines = body.count("\n")
    if body_lines > 500:
        warnings.append(f"{rel}: body is {body_lines} lines; consider moving "
                        f"detail into references/ (recommended under 500)")

    skill_dir = skill_md.parent
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if "\\" in target:
            warnings.append(f"{rel}: link target '{target}' uses a backslash; "
                            f"use forward slashes")
            continue
        clean = target.split("#", 1)[0].strip()
        if not clean or clean.startswith(("http://", "https://", "mailto:")):
            continue
        if not (skill_dir / clean).exists():
            errors.append(f"{rel}: link target '{target}' does not exist")


def check_skills() -> None:
    if not SKILLS_DIR.is_dir():
        warnings.append("skills/ directory not found")
        return
    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    if not skill_files:
        warnings.append("skills/ contains no skills yet")
    for skill_md in skill_files:
        check_skill(skill_md)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.relative_to(ROOT).as_posix()}: invalid JSON "
                      f"({exc})")
        return None


def check_marketplace() -> None:
    path = PLUGIN_DIR / "marketplace.json"
    if not path.is_file():
        warnings.append(".claude-plugin/marketplace.json not found; skipping")
        return
    data = load_json(path)
    if data is None:
        return
    rel = path.relative_to(ROOT).as_posix()
    for field in ("name", "owner", "plugins"):
        if field not in data:
            errors.append(f"{rel}: missing required field `{field}`")
    if data.get("name") in RESERVED_MARKETPLACES:
        errors.append(f"{rel}: marketplace name '{data['name']}' is reserved by "
                      f"Anthropic; choose another")
    for i, plugin in enumerate(data.get("plugins", [])):
        for field in ("name", "source"):
            if field not in plugin:
                errors.append(f"{rel}: plugins[{i}] missing required field "
                              f"`{field}`")


def check_plugin() -> None:
    path = PLUGIN_DIR / "plugin.json"
    if not path.is_file():
        return
    data = load_json(path)
    if data is None:
        return
    if "name" not in data:
        errors.append(f"{path.relative_to(ROOT).as_posix()}: missing required "
                      f"field `name`")


def main() -> int:
    check_skills()
    check_marketplace()
    check_plugin()

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"OK: no errors, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
