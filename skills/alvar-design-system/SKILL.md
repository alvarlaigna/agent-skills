---
name: alvar-design-system
description: Build frontends in the Alvar Design System, a warm, editorial, token-driven UI style on React 19, TypeScript, Tailwind v4, Radix, and class-variance-authority. Use when creating or restyling a UI, web app, component, or design system in this style; when setting up design tokens, theming, light/dark mode, or a shadcn-style component library; or when the user mentions the Alvar design system, the brand palette (Ember Red, Navy Ink, Snow White), or wants a spacious, minimalist frontend. Scaffolds a new Vite project, adds the foundation to an existing one, and reviews UI against the principles.
license: MIT
---

# Alvar Design System

A spacious, editorial, token-driven UI system: a warm monochromatic canvas (Snow
White paper, Navy Ink text) with a single Ember Red accent, fluid space and type,
and accessibility built in. The stack is React 19 + TypeScript + Tailwind v4
(CSS-first) + Radix + class-variance-authority. Use it to build a new frontend in
this style, restyle an existing one, or review UI against the principles.

This skill ships the foundation (design tokens, the `cn()` helper, and the Stack
/ Cluster / Grid layout primitives) and six reference components (button, card,
input, badge, alert, dialog). They demonstrate every pattern; build the rest the
same way.

## Core principles

Apply these on every screen. The full version is in
[references/principles.md](references/principles.md).

1. Space is structure. Separate with whitespace and proximity, not borders and
   shadows. Spacing stays on the 4px grid; section rhythm is fluid (`clamp()`),
   not breakpoints.
2. Semantic monochromacy. The canvas is warm-neutral. The Ember accent
   (`primary`) appears once, on the most important action, agentic affordances, or
   critical feedback.
3. Typography carries hierarchy. Space Grotesk display, Plus Jakarta Sans body,
   radical scale contrast, body at `leading-normal` and a 68ch measure.
4. Two-layer tokens. Components reference semantic tokens only, never a primitive
   or a raw hex.
5. Layout from primitives only. Compose with Stack, Cluster, Grid; extend a
   primitive rather than writing a one-off flex or padding.
6. Accessibility is a requirement: WCAG AA, visible focus,
   `prefers-reduced-motion`, Radix for overlays.

## Reading documentation

Read the bundled references when you need detail:

- [references/principles.md](references/principles.md): the design philosophy and
  aesthetic rules, plus a pre-ship necessity audit.
- [references/tokens.md](references/tokens.md): the two-layer token model, the full
  token values, and the rule for adding or changing a themeable value.
- [references/components.md](references/components.md): the canonical component
  shape, the primitives, the six components, and how to build a new one.
- [references/setup.md](references/setup.md): installing into projects, Tailwind v4
  wiring, fonts, dark mode, accessibility, and the token linter.

## Templates and scripts

Use the bundled scaffolding instead of regenerating files from memory.

- Run `scripts/new_project.py` to scaffold a runnable Vite + React + TS app wired
  with the system.
  - Example: `python scripts/new_project.py --out ./my-app --name "My App"`
  - Then `cd my-app && npm install && npm run dev`.
- Run `scripts/add_to_project.py` to add the foundation to an existing repo.
  - Example: `python scripts/add_to_project.py --dir . --base src --with-components`
  - It copies the files and prints the deps to install and the wiring to do.
- Run `scripts/check_tokens.py --dir src` to verify components use semantic tokens
  only (flags raw hex and primitives; exits non-zero on a hit).
- Read files under `templates/` when you need the exact source: the token contract
  is [templates/styles/tokens.css](templates/styles/tokens.css) and the Tailwind
  wiring is [templates/styles/globals.css](templates/styles/globals.css).

Run the scripts; do not read their source into context unless debugging the skill.

## Default workflow

1. Decide: new project (`new_project.py`) or existing (`add_to_project.py`).
2. Import `globals.css` once at the app root; confirm the `@/` alias and the
   Tailwind v4 plugin are set up (see references/setup.md).
3. Lay out with Stack / Cluster / Grid. Keep spacing on the 4px grid; use the
   fluid `--space-section` / `--space-gutter` for page rhythm.
4. Build UI from the shipped components. Add a new one by mirroring `button.tsx`
   (CVA, forwardRef, displayName, `cn()`), using semantic tokens only.
5. Run `scripts/check_tokens.py`; fix any hit.
6. Verify accessibility: keyboard, visible focus, contrast, `aria-label` on
   icon-only controls.

## Must-follow rules

- Components reference semantic tokens only (`bg-primary`,
  `bg-[var(--color-overlay)]`). Never a primitive (`--ember-500`) or a raw hex.
- To add a themeable value: add a primitive, map a semantic token in `:root` and
  `.dark`, then expose it in `@theme inline`. All three, in that order.
- Dark mode is the `.dark` class on an ancestor, not a media query.
- The Ember accent earns its place: one primary action per view.
- Compose layout from primitives; do not invent local flex or padding.

## Gotchas

- Tailwind v4 is CSS-first. There is no `tailwind.config.js`; theming lives in
  `tokens.css` and `globals.css` via `@theme inline` and `@custom-variant dark`.
- Reference non-color tokens with arbitrary utilities: `z-[var(--z-overlay)]`,
  `duration-[var(--duration-base)]`, `ease-[var(--ease-standard)]`,
  `animate-[dialog-in_0.26s_var(--ease-emphasized)]`.
- Status surface tints use `color-mix()`, so they adapt to light and dark on their
  own. Do not hard-code tinted backgrounds.
- The `@source inline(...)` safelist in `globals.css` keeps semantic utilities in
  the compiled CSS. If you rename a semantic token, update the safelist too.
- Dialog needs `@radix-ui/react-dialog` and `lucide-react`. `add_to_project.py`
  prints these when you include components.
