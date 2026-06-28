# Contributing

This is a personal collection, but suggestions and new skills are welcome.

## Proposing a skill

1. Open an issue describing the skill and when an agent should use it, so we can
   agree it fits before you spend time on it.
2. Copy `templates/SKILL.md` to `skills/<name>/SKILL.md`. The folder name must
   match the `name` field.
3. Write the skill. [docs/authoring.md](docs/authoring.md) covers what makes a
   good one.
4. Run the checks:

   ```
   python scripts/validate.py
   ```

   For a stricter check against the full standard, use `skills-ref validate
   skills/<name>` (see <https://agentskills.io>) and `claude plugin validate .`.
5. Open a pull request that links the issue.

## Writing style

Documentation here is plain and professional. Write in the third person, keep
sentences short, and say what a thing does and where it falls short. No badges,
no marketing language, no decorative emoji.
