# Authoring skills

A skill teaches an agent something it does not already do well. The best skills
are short, specific, and tested. This is the practical version; the full standard
is at <https://agentskills.io>.

## Frontmatter

Every `SKILL.md` starts with YAML frontmatter. Two fields matter most:

- **`name`**: lowercase letters, numbers, and hyphens; 64 characters or fewer;
  must match the skill's folder name.
- **`description`**: what the skill does and when to use it; 1024 characters or
  fewer.

Optional fields include `license`, `compatibility` (environment requirements),
and `metadata` (a map for things like `version`).

## Write the description for discovery

The agent reads the description to decide whether to use the skill, often
choosing among many. Make it earn that choice.

- Write in the third person: "Extracts text from PDFs", not "I can help with
  PDFs".
- State both halves: what it does, and when to reach for it.
- Include the words a user would actually say: file types, tool names, the
  phrasing of the request.

Good: `Extracts text and tables from PDF files and fills forms. Use when the user
mentions a PDF, a form, or document extraction.`

Weak: `Helps with documents.`

## Keep the body lean

The model is already capable. Add only what it does not know: your conventions,
the exact steps, the failure modes. Cut anything that explains a concept the
model already understands.

- Aim for under 500 lines. Move detail into `references/`.
- Prefer concrete examples over description.
- Use one term for one thing throughout.
- Avoid dates and "as of" notes; if you must keep superseded guidance, put it in
  an "old patterns" section.
- Use forward slashes in paths, always.

## Use progressive disclosure

Put the overview and the common path in `SKILL.md`. Move long reference material,
large examples, and rarely needed detail into sibling files:

```
my-skill/
├── SKILL.md          # overview and the common case
├── references/
│   └── reference.md  # detail, read only when needed
└── scripts/
    └── helper.py     # executed, not read into context
```

Link to these files from `SKILL.md`, and keep references one level deep so the
agent reads whole files rather than chasing a chain. Give files longer than about
100 lines a short table of contents.

## Prefer scripts for fragile work

If an operation must run a fixed way, ship a script and tell the agent to run it.
A script is more reliable than regenerated code, and only its output enters the
context. Say plainly whether the agent should run a file or read it.

## Add a gotchas section

The mistakes an agent tends to make are the highest-value thing you can write
down. Collect them as you watch real runs, and keep them specific.

## Test before sharing

Run the skill on real requests in a fresh session. Check two things separately:
that the agent picks the skill when it should, and that the result is what you
wanted when it does. If it does not trigger, the description usually needs the
words the user actually used.

## Checklist

- [ ] `name` matches the folder; `description` says what and when.
- [ ] Body is under 500 lines; detail is in `references/`.
- [ ] Examples are concrete; terminology is consistent.
- [ ] References are one level deep; paths use forward slashes.
- [ ] Gotchas captured from real use.
- [ ] `python scripts/validate.py` passes.
