# Tokens

The token contract is the heart of the system. Getting it right is what keeps
theming from breaking components. The file is `templates/styles/tokens.css`;
this document explains its structure and lists the values.

## Contents

- [Two layers](#two-layers)
- [The rule for changing a themeable value](#the-rule-for-changing-a-themeable-value)
- [Color primitives](#color-primitives)
- [Semantic color](#semantic-color)
- [Spacing](#spacing)
- [Radius](#radius)
- [Typography](#typography)
- [Elevation and glass](#elevation-and-glass)
- [Motion](#motion)
- [Z-index](#z-index)

## Two layers

1. Primitives: raw brand values named for what they are (`--ember-500`,
   `--neutral-900`, `--space-4`). Never reference these in a component.
2. Semantic tokens: behavioral, named for what they do
   (`--color-action-primary-hover`, `--color-background`). Components reference
   only these, through Tailwind utilities (`bg-primary`) or arbitrary values
   (`bg-[var(--color-overlay)]`).

`.dark` remaps only the semantic layer; primitives never change. `globals.css`
wires the semantic layer to Tailwind utilities via `@theme inline`.

## The rule for changing a themeable value

Three steps, in order:

1. Add or pick a primitive (e.g. `--ember-500`).
2. Map a semantic token to it in `:root` and again in `.dark`.
3. Expose the semantic token as a utility in the `@theme inline` block of
   `globals.css`.

Skipping the `.dark` step is the usual cause of "it looks wrong in dark mode".

## Color primitives

Brand anchors: Snow White `#fdfbf7`, Classic Linen `#f1ece2`, Navy Ink
`#1a2a3a`, Ember Red `#d95d39`.

Warm neutral ramp (paper to ink):

| Token | Hex | Token | Hex |
|---|---|---|---|
| --neutral-50 | #fdfbf7 | --neutral-500 | #7e7464 |
| --neutral-100 | #f1ece2 | --neutral-600 | #585347 |
| --neutral-200 | #e6ddcd | --neutral-700 | #3a4651 |
| --neutral-300 | #d3c8b4 | --neutral-800 | #283744 |
| --neutral-400 | #aca08a | --neutral-900 | #1a2a3a |
| | | --neutral-950 | #111c26 |

Ember accent ramp: 50 `#fbeee9`, 100 `#f6d8cd`, 200 `#efb6a0`, 300 `#e89073`,
400 `#e1744f`, 500 `#d95d39`, 600 `#c24a2a`, 700 `#a03b22`, 800 `#7d2f1d`, 900
`#5e251a`.

Functional hues: green 500 `#3f8f6b` / 600 `#347458`; amber 500 `#c98a2e` / 600
`#a87122`; red 500 `#c4452c` / 600 `#a4361f`; blue 500 `#3a6ea5` / 600 `#2f5985`.

## Semantic color

Components use these names. Each has a value in `:root` (light) and, where it
changes, in `.dark`.

- Surfaces and text: `--color-background`, `--color-surface`,
  `--color-surface-raised`, `--color-foreground`, `--color-muted`,
  `--color-muted-foreground`, `--color-border`, `--color-input`, `--color-ring`.
- Primary action (Ember): `--color-action-primary`, `-hover`, `-active`,
  `-foreground`. Secondary: `--color-action-secondary`, `-hover`, `-foreground`.
- Feedback: `--color-success`, `--color-warning`, `--color-danger` (+ `-hover`),
  `--color-info`, each with a `-foreground`.
- Soft tints for callouts and badges: `--color-info-surface`,
  `--color-success-surface`, `--color-warning-surface`, `--color-danger-surface`
  (built with `color-mix()` over the raised surface, so they follow the theme).
- Utility: `--color-focus-ring` (decoupled from `--color-ring`),
  `--color-overlay` (the modal scrim).

Tailwind exposes these as `bg-*`, `text-*`, `border-*`, `ring-*` with short
names: `primary`, `secondary`, `success`, `warning`, `danger`, `info`,
`background`, `surface`, `surface-raised`, `foreground`, `muted`,
`muted-foreground`, `border`, `input`, `ring`, and the `*-surface` tints.

## Spacing

4px baseline grid. `--space-0` through `--space-32`: `0, 1px, 0.25rem, 0.5rem,
0.75rem, 1rem, 1.25rem, 1.5rem, 2rem, 2.5rem, 3rem, 4rem, 5rem, 6rem, 8rem`.

Fluid section rhythm: `--space-section: clamp(4rem, 10vw, 9rem)` and
`--space-gutter: clamp(1rem, 5vw, 3rem)`. Use these for page and section padding
instead of breakpoints.

## Radius

`--radius-sm` 0.375rem, `--radius-md` 0.625rem, `--radius-lg` 0.875rem,
`--radius-xl` 1.25rem, `--radius-full` 9999px. Tailwind:
`rounded-sm|md|lg|xl|full`.

## Typography

Families: `--font-display` Space Grotesk, `--font-sans` Plus Jakarta Sans,
`--font-mono` system mono. Tailwind: `font-display|sans|mono`.

Fluid scale (Tailwind `text-xs` through `text-4xl`):

| Token | Value |
|---|---|
| --text-xs | 0.75rem |
| --text-sm | 0.875rem |
| --text-base | 1rem |
| --text-lg | 1.125rem |
| --text-xl | clamp(1.25rem, 1.1rem + 0.6vw, 1.5rem) |
| --text-2xl | clamp(1.5rem, 1.2rem + 1.4vw, 2.1rem) |
| --text-3xl | clamp(2rem, 1.5rem + 2.4vw, 3.2rem) |
| --text-4xl | clamp(2.75rem, 1.9rem + 4vw, 5rem) |

Line height: `--leading-tight` 1.1, `--leading-snug` 1.3, `--leading-normal` 1.6
(body minimum), `--leading-relaxed` 1.75. Reading width `--measure` 68ch.

## Elevation and glass

Soft, low-contrast shadows: `--shadow-xs|sm|md|lg` (Tailwind `shadow-*`). Prefer
whitespace over shadow; reach for elevation only when layering is real.

Glass (opt-in `.glass` utility, layered surfaces only): `--glass-bg`,
`--glass-border`, `--glass-blur` (16px). Both background and border flip in
`.dark`.

## Motion

Durations: `--duration-fast` 120ms, `--duration-base` 200ms, `--duration-slow`
360ms. Easing: `--ease-standard` `cubic-bezier(0.2, 0, 0, 1)`, `--ease-emphasized`
`cubic-bezier(0.3, 0, 0, 1.2)` (slight overshoot, for entrances). Reference in
classes as `duration-[var(--duration-base)]` and `ease-[var(--ease-standard)]`.
All motion is suppressed under `prefers-reduced-motion`.

## Z-index

`--z-base` 0, `--z-dropdown` 20, `--z-sticky` 30, `--z-overlay` 60, `--z-toast`
70. Use `z-[var(--z-overlay)]` rather than ad-hoc values so layers stay ordered.
