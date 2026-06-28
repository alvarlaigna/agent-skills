#!/usr/bin/env sh
# Install the skills in this repository into an agent's skills directory.
#
# Each skill is the same SKILL.md folder for every tool; only the destination
# differs. The --tool shortcuts point at each agent's personal skills directory
# as documented at the time of writing. Use --target for project scope or any
# tool not listed, and confirm paths against docs/compatibility.md.

set -eu

usage() {
  cat <<'EOF'
Install the skills in this repository into an agent's skills directory.

Usage:
  scripts/install.sh --tool <name> [--link]
  scripts/install.sh --target <dir> [--link]

Options:
  --tool <name>   claude | codex | gemini | grok (personal skills directory)
  --target <dir>  install into an explicit directory (any tool, any scope)
  --link          symlink skills instead of copying, so they track this repo
  -h, --help      show this help

See docs/compatibility.md for the per-tool directory table.
EOF
}

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
src="$repo_dir/skills"

tool=""
target=""
link=0

while [ $# -gt 0 ]; do
  case "$1" in
    --tool)
      tool="${2:-}"
      [ -n "$tool" ] || { echo "--tool needs a value" >&2; exit 1; }
      shift 2
      ;;
    --target)
      target="${2:-}"
      [ -n "$target" ] || { echo "--target needs a value" >&2; exit 1; }
      shift 2
      ;;
    --link) link=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [ -z "$target" ]; then
  case "$tool" in
    claude) target="$HOME/.claude/skills" ;;
    codex)  target="$HOME/.codex/skills" ;;
    gemini) target="$HOME/.gemini/skills" ;;
    grok)   target="$HOME/.grok/skills" ;;
    "")     echo "specify --tool <name> or --target <dir>" >&2; usage; exit 1 ;;
    *)      echo "unknown tool: $tool (use --target <dir>)" >&2; exit 1 ;;
  esac
fi

[ -d "$src" ] || { echo "no skills/ directory found at $src" >&2; exit 1; }

mkdir -p "$target"

count=0
for dir in "$src"/*/; do
  [ -d "$dir" ] || continue
  skill="${dir%/}"
  name=$(basename "$skill")
  dest="$target/$name"
  rm -rf "$dest"
  if [ "$link" -eq 1 ]; then
    ln -s "$skill" "$dest"
  else
    cp -R "$skill" "$dest"
  fi
  echo "installed $name -> $dest"
  count=$((count + 1))
done

echo "done: $count skill(s) into $target"
