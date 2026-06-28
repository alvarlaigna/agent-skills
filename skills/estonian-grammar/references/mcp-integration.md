# estonian-mcp Integration

Use this reference when the `estonian-mcp` connector or local server is available.

Upstream: https://github.com/silly-geese/estonian-mcp by `silly-geese`.

The project is an offline MCP server wrapping EstNLTK, Vabamorf, EKI rules, Estonian WordNet, and fastText-derived related-word checks. It is especially useful because Estonian inflection, compounds, and object case are easy for general LLMs to hallucinate.

## Hard Rule

Never assert an Estonian lemma, case form, conjugation, spelling, or compound split without verification when a verifier is available.

## Tool Routing

Use these tools when available:

- `spell_check`: first pass for user-provided Estonian and generated drafts.
- `lemmatize`: dictionary forms, repetition analysis, vocabulary explanations.
- `analyze_morphology`: grammar claims, case forms, endings, ambiguity, compounds.
- `paradigm`: full declension/conjugation; do not recall paradigms from memory.
- `pos_tag`: part-of-speech checks.
- `tokenize`: sentence and word boundaries.
- `synonyms`: same-meaning alternatives from Estonian WordNet.
- `find_related_words`: adjacent concepts; inspect results because antonyms and inflections can appear.
- `classify_register`: formal/neutral/colloquial direction and mixed-register warnings.
- `check_style`: repetition, passive voice, sentence length, hedging.
- `check_redundancy`: pleonasm and doubled meanings.
- `check_object_case`: common object-case errors after negation and partitive-only verbs.
- `check_abbreviation_hyphenation`: `APIga` -> `API-ga`, `MCPst` -> `MCP-st`.
- `check_compound_familiarity`: calque and AI-coinage risk for compounds.
- `check_capitalization`: weekdays, months, nationalities, language/culture adjectives.
- `check_compounds`: common split-compound errors.
- `check_punctuation`: missing comma before common subordinating conjunctions.
- `check_hyphenation`: safe line breaks; use only for layout/typesetting tasks.
- `check_numbers`: decimal and thousands separator rules.
- `named_entities`: people, places, organizations in Estonian text.
- `syllabify`: syllables, quantity, accent; one word at a time.

## Recommended Pipelines

### Proofread

1. `spell_check`
2. `check_capitalization`, `check_compounds`, `check_punctuation`, `check_numbers`, `check_abbreviation_hyphenation`
3. `check_object_case` when sentences contain objects, negation, or verbs known to govern partitive
4. `check_redundancy` and `check_style` for polished copy
5. `analyze_morphology` for disputed words/forms

### Rewrite

1. `classify_register` on the original
2. Rewrite for target audience
3. `classify_register` on the rewrite
4. Run the proofread checks on the final text

### Vocabulary And Repetition

1. `lemmatize` to find repeated lemmas
2. `synonyms` for same-meaning replacements
3. `find_related_words` for broader ideation only
4. `analyze_morphology` to fit replacements into the original case/form

## Known Quirks

- Spell checking can accept morphologically plausible invented compounds; use compound familiarity and source lookup for unusual compounds.
- Proper nouns, brand names, and neologisms may be flagged as misspellings.
- Related-word results can include inflections, antonyms, or the wrong sense of a polysemous word.
- Register classification is heuristic. Treat it as a signal, not a verdict.
- Syllabification is per-word, not for whole sentences.

## Attribution Note

This skill does not vendor the upstream server code or data. It summarizes usage patterns and credits the upstream project. Preserve upstream attribution if adapting MCP-specific guidance.
