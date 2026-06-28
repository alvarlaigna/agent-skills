# Setup

Install the system into a project and wire Tailwind v4, fonts, dark mode, and
accessibility. The token values are in [tokens.md](tokens.md).

## Contents

- [New project](#new-project)
- [Existing project](#existing-project)
- [Tailwind v4 wiring](#tailwind-v4-wiring)
- [Fonts](#fonts)
- [Dark mode](#dark-mode)
- [Accessibility baseline](#accessibility-baseline)
- [Linting tokens](#linting-tokens)
- [Storybook (optional)](#storybook-optional)

## New project

```bash
python scripts/new_project.py --out ./my-app --name "My App"
cd my-app
npm install
npm run dev
```

Produces a Vite + React 19 + TypeScript app with the foundation, primitives, core
components, and a demo `App.tsx`. The `@/` alias maps to `src/`.

## Existing project

```bash
python scripts/add_to_project.py --dir . --base src --with-components
```

Copies `styles/`, `lib/`, `primitives/` (and `components/` with the flag) into
your source base, then prints the remaining steps:

1. Install deps: `clsx tailwind-merge class-variance-authority` (and
   `@radix-ui/react-dialog lucide-react` for Dialog), plus Tailwind v4
   (`tailwindcss @tailwindcss/vite`) if you are not already on it.
2. Import the stylesheet once at the app root: `import "@/styles/globals.css"`.
3. Map the `@/` alias to your source base in the bundler and tsconfig paths.
4. Toggle dark mode with the `dark` class on `<html>`.

## Tailwind v4 wiring

Tailwind v4 is CSS-first. There is no `tailwind.config.js`. Everything lives in
two CSS files:

- `tokens.css`: primitives and semantic tokens (`:root` and `.dark`).
- `globals.css`: `@import "tailwindcss"`, the token import, the fonts import,
  `@custom-variant dark`, the `@theme inline` block that turns semantic tokens
  into utilities, the base layer, and the component keyframes.

Use the Vite plugin (`@tailwindcss/vite`) as in the scaffold's `vite.config.ts`.
The `@source inline(...)` lines safelist the semantic utilities so the palette
exists in compiled CSS even where local components do not use every class.

## Fonts

`globals.css` imports Space Grotesk and Plus Jakarta Sans from Google Fonts. To
self-host, install the fontsource packages and replace the `@import url(...)` line
with local imports; keep the `--font-display` and `--font-sans` token names.

## Dark mode

Class strategy, not media query. Add or remove `dark` on the root element:

```ts
document.documentElement.classList.toggle("dark", isDark);
```

Only semantic tokens flip; primitives stay fixed. To follow the OS on first load,
read `window.matchMedia("(prefers-color-scheme: dark)").matches` and set the
class. Persist the user's choice yourself (for example in localStorage).

## Accessibility baseline

This is a requirement, not a finishing touch. The system ships:

- Visible, branded focus on `:focus-visible` (2px ring at 2px offset), applied
  consistently across interactive components.
- `prefers-reduced-motion`: animation and transition collapse to near zero.
- Radix primitives for overlay and disclosure components, which handle focus
  trapping, escape, and ARIA.

Hold work to WCAG AA: sufficient contrast, semantic HTML and landmarks, keyboard
operability, and labels on icon-only controls (`aria-label`).

## Linting tokens

The one mechanical rule the system enforces: components reference semantic tokens
only.

```bash
python scripts/check_tokens.py --dir src
```

It flags raw hex and primitive tokens (`--ember-500`, `--navy-ink`, and so on) in
component source and exits non-zero. `tokens.css` and `globals.css` are exempt.

## Storybook (optional)

The source system is developed in Storybook with the a11y addon as the spec. This
skill does not scaffold Storybook. If you want per-component docs and a11y checks,
add `@storybook/react-vite` and the a11y addon, and title stories under
`Foundations/`, `Primitives/`, and `Components/`.
