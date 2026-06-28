# Tool compatibility

These skills are written in the [Agent Skills](https://agentskills.io) standard:
a `SKILL.md` file in a folder. Several agents read that format directly and
differ only in where they look for it. Others use their own format; for those,
copy the instructions across by hand for now.

The directories below are each tool's personal (user-level) skills location.
Support and exact paths change as tools evolve, so confirm against the linked
docs and use `scripts/install.sh --target <dir>` for anything not listed or for
project-level installs.

## Reads SKILL.md

| Tool | Skills directory | Install |
|------|------------------|---------|
| Claude Code | `~/.claude/skills/` (or a plugin) | marketplace, or `install.sh --tool claude` |
| OpenAI Codex | `~/.codex/skills/` | `install.sh --tool codex` |
| Gemini CLI | `~/.gemini/skills/` | `install.sh --tool gemini` |
| Grok | `~/.grok/skills/` | `install.sh --tool grok` |

Project scope works the same way: install into the repo's `.claude/skills/`,
`.agents/skills/`, or equivalent with `--target`.

Docs: [Claude Code](https://code.claude.com/docs/en/skills) ·
[Codex](https://developers.openai.com/codex) ·
[Gemini CLI](https://geminicli.com) ·
[Grok](https://x.ai).

## Uses its own format

These tools do not read `SKILL.md`; they use a rules or context file. Until this
repository ships converters, adapt a skill by copying its instructions into the
tool's format.

| Tool | Format | Location |
|------|--------|----------|
| Cursor | rules (`.mdc`) | `.cursor/rules/` |
| Windsurf | rules | `.windsurf/rules/` |
| Aider | conventions | `CONVENTIONS.md` |
| GitHub Copilot | instructions | `.github/copilot-instructions.md` |

Many of these also read a shared `AGENTS.md` for always-on guidance, which is a
reasonable place to paste a skill's core instructions.
