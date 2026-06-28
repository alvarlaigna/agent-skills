# Design principles

How the Alvar Design System looks and why. Read this before making aesthetic
decisions; the rules below are what keep work on brand. The values that
implement them are in [tokens.md](tokens.md); the component patterns are in
[components.md](components.md).

## Contents

- [The brand in one line](#the-brand-in-one-line)
- [1. Space is structure](#1-space-is-structure)
- [2. Semantic monochromacy](#2-semantic-monochromacy)
- [3. Typography is the interface](#3-typography-is-the-interface)
- [4. Intent-driven, agentic components](#4-intent-driven-agentic-components)
- [5. Engineer the system with tokens](#5-engineer-the-system-with-tokens)
- [Brand voice](#brand-voice)
- [The necessity audit](#the-necessity-audit)

## The brand in one line

Warm, editorial, token-driven minimalism. A calm monochromatic canvas (Snow
White paper, Navy Ink text) where a single Ember Red accent and generous space
do the work that borders and color usually do. Premium and human, not flashy.

Aesthetic anchors: human-centric technology, refined minimalism, editorial
clarity, warm professional, digital craftsmanship.

## 1. Space is structure

Whitespace is a material, not leftover room. Use it to group and to separate.

- Define relationships by proximity, not chrome. Strip heavy borders, rules, and
  drop shadows; let spacing show what belongs together. This lowers the cognitive
  cost of parsing a screen.
- Scale space with the viewport, not breakpoints. Section rhythm uses the fluid
  `--space-section` and `--space-gutter` `clamp()` tokens, so layouts breathe
  across devices without media queries.
- Keep all spacing on the 4px grid (`--space-*`). A value off the scale is a bug.

## 2. Semantic monochromacy

The canvas is warm-neutral and quiet. Color earns its place.

- Reserve the Ember accent (`primary`) for the single most important action on a
  view, for AI/agentic affordances, and for critical feedback. If everything is
  accented, nothing is.
- Status hues (success, warning, danger, info) signal state only. They are tuned
  to sit beside the warm palette, and they surface as soft tints for callouts and
  badges (`--color-*-surface`).
- Default surfaces are paper and linen in light, ink in dark. Layer with
  `Card variant="elevated"` or `.glass` only when depth is genuinely needed; glass
  is for nav, modals, and side panels, used sparingly.

## 3. Typography is the interface

When the chrome is quiet, type carries the hierarchy.

- Two families: Space Grotesk for display (headings), Plus Jakarta Sans for body
  and UI. Mono is the system stack.
- Radical scale contrast. Pair large, confident headings (the fluid `--text-3xl`
  / `--text-4xl` `clamp()` steps) with calm, readable body at `--leading-normal`
  (1.6) and a `--measure` of 68ch.
- Headings are tight: display font, `-0.02em` tracking, weight 600.

## 4. Intent-driven, agentic components

Interfaces increasingly host agents, not just forms. Design for that.

- Contextual affordances: a natural-language or semantic-search field should look
  different from a deterministic input. The `Input intent="agentic"` variant is
  the reference, a soft primary ring that signals readiness.
- Progressive disclosure: show the core path first, reveal depth on demand.
  Prefer simplicity over cleverness.

## 5. Engineer the system with tokens

A design system is a dependency graph, not a picture.

- Behavioral tokens. Name variables for what they do
  (`--color-action-primary-hover`), not what they are (`--ember-600`). See
  [tokens.md](tokens.md).
- Primitive constraints on layout. Compose with `Stack`, `Cluster`, and `Grid`
  only. A one-off `flex flex-col gap-…` or a bespoke padding hack is a signal the
  primitive set is missing something; extend a primitive instead.

## Brand voice

Values: clarity over cleverness, ownership by design, inclusivity, technical
sovereignty. Tone: authoritative, pragmatic, transparent, forward-thinking. UI
copy is plain and short. Say what a control does.

## The necessity audit

Before shipping a screen, check:

1. Spacing is on the 4px grid; section rhythm is fluid, not pixel breakpoints.
2. Content is separated by space and type, not borders and backgrounds.
3. The Ember accent appears once, on the most important action.
4. Every token used is semantic, never a primitive or a raw hex.
5. The screen looks deliberate with real, messy data, not just the empty state.
6. If an element does not aid navigation, clarify data, or guide an action,
   remove it.
