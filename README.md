# agent-skills

A small, curated set of agent skills, written once in the open
[Agent Skills](https://agentskills.io) standard so the same files work across
Claude Code, Codex, Gemini, Grok, and other agents.

## What this is

A skill is a folder with a `SKILL.md` file: a short note on when to use it and
the instructions to follow when it runs. Agents read the note up front and the
rest only when a task needs it, so a skill costs almost nothing until it is used.

This is a personal collection by [Alvar Laigna](https://alvarlaigna.com). The
list stays short and the documentation plain. The same `SKILL.md` is the source
of truth for every tool.

## Install

### Claude Code (marketplace)

```
/plugin marketplace add alvarlaigna/agent-skills
/plugin install agent-skills@alvarlaigna-skills
```

Skills installed this way are namespaced, for example `/agent-skills:raylib`.

### Claude Code (manual)

Copy a skill into your personal skills directory:

```
cp -r skills/ebitengine ~/.claude/skills/
```

It is then available as `/ebitengine`.

### Other tools

Copy or symlink the skills into another agent's directory:

```
scripts/install.sh --tool gemini                 # copy into ~/.gemini/skills
scripts/install.sh --target ./.agents/skills --link
```

On Windows, use `scripts/install.ps1`. See
[docs/compatibility.md](docs/compatibility.md) for where each tool expects
skills.

## Skills

| Skill | What it does |
|-------|--------------|
| [`alvar-design-system`](skills/alvar-design-system/) | Build frontends in the Alvar Design System: a warm, editorial, token-driven React UI on Tailwind v4. |
| [`ebitengine`](skills/ebitengine/) | Build, test, and ship Go games and tools with Ebitengine/Ebiten. |
| [`estonian-grammar`](skills/estonian-grammar/) | Write, proofread, and rewrite natural Estonian, with case-form and register guidance. |
| [`raylib`](skills/raylib/) | Build 2D and 3D games with raylib in C, C++, or Go. |

## Add your own

1. Copy [`templates/SKILL.md`](templates/SKILL.md) to `skills/<name>/SKILL.md`.
2. Read [docs/authoring.md](docs/authoring.md).
3. Run `python scripts/validate.py`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the rest.

## How it works

Each skill follows the Agent Skills standard: a `SKILL.md` with `name` and
`description` in YAML frontmatter, then Markdown instructions. Longer material
lives in a `references/` folder beside it and loads only when needed. Claude Code
supports the standard natively, as do a growing number of other agents.

## License

[MIT](LICENSE).
