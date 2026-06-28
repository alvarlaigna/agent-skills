---
name: estonian-grammar
description: Write, proofread, rewrite, translate, and explain high-quality Estonian. Use when the user writes or edits Estonian text, asks whether Estonian sounds natural, needs grammar or case-form guidance, wants register-aware Estonian copy, or wants to avoid AI-sounding Estonian. Uses EKI, Sõnaveeb/ÕS, EKI teatmik, and estonian-mcp when available.
---

# Estonian Grammar

Use this skill for Estonian drafting, proofreading, rewriting, grammar explanation, translation polishing, and naturalness checks.

Core rule: do not invent Estonian spellings, lemmas, case forms, conjugations, or compound splits. Verify with `estonian-mcp` tools when available; otherwise use Sõnaveeb/ÕS, EKI teatmik, or EKI search and mark uncertainty where a source is not checked.

## Default Workflow

1. Identify the task: proofread, rewrite, translate/polish, explain grammar, or draft new Estonian.
2. Determine the intended audience and register from context. If unclear, default to natural neutral standard Estonian.
3. Check factual language questions against authoritative sources:
   - Read [authoritative sources](references/authoritative-sources.md) when using EKI, Sõnaveeb, ÕS, or EKI teatmik.
   - Read [MCP integration](references/mcp-integration.md) when `estonian-mcp` tools are available.
   - Read [writing guide](references/estonian-writing-guide.md) when working on style, grammar, or common AI mistakes.
4. Edit for correctness first, then naturalness, then tone. Do not let marketing polish break grammar.
5. Before finalizing Estonian you produce, check spelling, capitalization, compounds, punctuation, numbers, abbreviation hyphenation, and suspicious calques through available tools or references.
6. When reporting changes, separate mandatory corrections from style suggestions.

## Source Priority

Use this order when sources disagree or confidence matters:

1. EKI and Sõnaveeb/ÕS for written standard, word forms, spelling, and norming.
2. EKI teatmik for orthography, punctuation, capitalization, abbreviations, names, numbers, and language advice.
3. `estonian-mcp` for repeatable automated checks and morphology/tooling workflows.
4. Native-style judgment and corpus-like reasoning only after source-backed checks.

ÕS 2025 is the basis of the written standard from 2026; prefer it where available.

## Task Patterns

### Proofread Estonian

Use [proofread report](templates/proofread-report.md) for substantial edits.

Check in this order:

1. Spelling and obvious typos.
2. Inflection and case agreement, especially object case, partitive after negation, and government after verbs/adpositions.
3. Compounds, capitalization, punctuation, abbreviations, and number formatting.
4. Register consistency and sentence rhythm.
5. Natural wording: remove literal translations, officialese, empty intensifiers, and AI-like filler.

Do not silently rewrite the user's intent. For uncertain grammar choices, explain the tradeoff and give the safer option.

### Rewrite For Tone

Use [rewrite brief](templates/rewrite-brief.md) for multi-paragraph or client-facing work.

Preserve the facts, names, terminology, and level of directness unless the user asks otherwise. Verify the output did not drift from the requested register:

- `ametlik`: clear, precise, not bureaucratic.
- `neutraalne`: everyday standard written Estonian.
- `sõbralik`: warmer, still grammatical and not childish.
- `turunduslik`: vivid but concrete; avoid empty hype.
- `kõnekeelne`: only when requested or context clearly calls for it.

### Translate Or Polish Into Estonian

Translate meaning, not syntax. English source order often creates stiff Estonian. Prefer natural Estonian clause order, idiomatic verbs, and native compounds.

Check especially:

- English calques such as `võtab aega`, `teeb mõtet`, `parim praktika`, `mõtteliin`.
- Overuse of `oluline`, `võimaldab`, `pakub`, `lahendus`, `kogemus`, `tõhus`.
- Nominalizations where a verb would sound better.
- Unnecessary possessives copied from English.

### Explain Grammar

When answering grammar questions, cite the checked form or source. If a word form is ambiguous, say so. Estonian surface forms can represent multiple cases or numbers.

For learners, explain:

- lemma and part of speech,
- case/form and why it fits the sentence,
- literal role in the phrase,
- natural translation,
- one short example if useful.

## Anti-Slop Rules

- Do not produce Estonian that only mirrors English syntax.
- Do not use formal bureaucratic vocabulary to make weak content sound professional.
- Do not invent compounds because they look plausible. Estonian allows compounds productively, but not every plausible compound is idiomatic.
- Do not over-capitalize weekdays, months, languages, nationalities, or culture adjectives in mid-sentence.
- Do not write abbreviation endings without the hyphen: prefer `API-ga`, `MCP-st`, `OÜ-le`.
- Do not use decimal points or comma thousands separators in Estonian numbers: prefer `3,14` and `1 000 000`.
- Do not claim a form is correct from memory when a verifier is available.
- Do not mention tool mechanics inside polished user-facing copy.

## Local Advisory Script

For quick deterministic checks when no MCP is available, run:

```bash
python scripts/check_estonian_text.py input.txt
```

or:

```bash
echo "Tekst" | python scripts/check_estonian_text.py
```

The script is advisory only. It catches common AI-writing and formatting risks; it is not a grammar oracle and does not replace EKI, Sõnaveeb/ÕS, or `estonian-mcp`.

## Attribution

This skill is inspired by and designed to work well with [`silly-geese/estonian-mcp`](https://github.com/silly-geese/estonian-mcp). See [attribution](ATTRIBUTION.md) before redistributing or extending MCP-derived material.
