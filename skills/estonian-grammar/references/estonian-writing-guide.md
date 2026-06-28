# Estonian Writing Guide

Use this reference for practical editing and naturalness checks. It is not a full grammar textbook; verify high-stakes claims with EKI, Sõnaveeb/ÕS, or `estonian-mcp`.

## Natural Estonian Defaults

- Prefer clear finite verbs over abstract nouns: `parandame teenust` often beats `teenuse parendamise teostamine`.
- Keep the main point early, but do not force English word order.
- Use concrete nouns and verbs instead of vague business words: `lahendus`, `kogemus`, `võimalus`, `tõhus`, `innovaatiline`.
- Avoid stacking genitives and nominalizations unless the genre requires it.
- Prefer one precise adjective to several empty intensifiers.

## Register

**Neutral standard Estonian** is the safest default for emails, product text, instructions, and explanations.

**Formal Estonian** should be precise, not bureaucratic. Avoid needless officialese:

- `käesolev`, `antud`, `teostama`, `läbi viima`, `vastavalt sellele`, `tulenevalt asjaolust`
- Prefer simpler alternatives: `see`, `korraldama`, `tegema`, `seetõttu`, `kuna`

**Friendly Estonian** can be warm without slang. Use direct address carefully and avoid fake enthusiasm.

**Marketing Estonian** should be specific. Replace generic hype with concrete benefit, action, or image.

## Cases And Government

Check case forms when they carry meaning:

- Negation often requires partitive object: `ma ei näe koera`, not `ma ei näe koer`.
- Many verbs govern a specific case or construction; verify rather than guessing.
- Whole/complete object vs partial/process object can change case and meaning.
- Place expressions may use internal or external locative cases depending on the noun and convention.

If a surface form has multiple possible analyses, state the ambiguity and use the sentence context.

## Compounds

Estonian compounds are productive, but AI often invents literal compounds from English. Watch for:

- direct calques from English,
- overly long compounds where a phrase is clearer,
- split compounds that should be written together,
- plausible but unfamiliar coinages.

When unsure, check Sõnaveeb/ÕS, EKI materials, or `check_compound_familiarity` if `estonian-mcp` is available.

## Capitalization

In running Estonian text, do not capitalize just because English would:

- weekdays and months are usually lowercase,
- languages and nationalities are usually lowercase when not part of a proper name,
- culture and region adjectives are often lowercase unless part of an official name.

Examples:

- `eesti keel`
- `esmaspäeval`
- `jaanuaris`
- `prantsuse kirjandus`

## Punctuation

Check commas before subordinate clauses and conjunctions such as `et`, `sest`, `kuna`, `kuigi`, `kuid`, `vaid`, `nagu`. Do not mechanically insert commas everywhere; verify the clause structure.

Avoid English-style comma habits in short Estonian sentences. Estonian comma rules are often more syntactic than rhythmic.

## Numbers And Abbreviations

- Decimal separator: `3,14`, not `3.14`.
- Thousands separator: `1 000 000`, not `1,000,000`.
- Use a hyphen before case endings on abbreviations: `API-ga`, `MCP-st`, `OÜ-le`.
- Keep units and symbols consistent with the target genre.

## Common AI-Sounding Estonian

Review and usually replace:

- `on oluline märkida, et`
- `tasub mainida, et`
- `antud kontekstis`
- `läbi selle`
- `parimad praktikad`
- `teeb mõtet`
- `võtab aega, et`
- `pakub võimalust`
- `innovaatiline lahendus`
- repeated `oluline`, `tõhus`, `lihtne`, `mugav`, `kaasaegne`

Better edits depend on context. Often the best fix is deleting the filler sentence.

## Final Polish Checklist

- Grammar and spelling are checked.
- Case forms are source-backed where uncertain.
- Compounds are idiomatic or intentionally coined.
- Register matches the audience.
- The text sounds like it was written in Estonian, not translated word by word.
- Corrections and style suggestions are separated when responding to the user.
