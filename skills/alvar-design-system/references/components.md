# Components

Patterns for building and using components. The shipped set is the foundation
plus six reference components (button, card, input, badge, alert, dialog) in
`templates/components/`. The rest of the source system (switch, avatar, progress,
skeleton, spinner, tabs, accordion, tooltip, toast) follows the same patterns;
build them as needed.

## Contents

- [Canonical component shape](#canonical-component-shape)
- [Layout primitives](#layout-primitives)
- [The shipped components](#the-shipped-components)
- [Radix and data-state animation](#radix-and-data-state-animation)
- [Building a new component](#building-a-new-component)
- [Composition example](#composition-example)

## Canonical component shape

Every component: `forwardRef`, a `displayName`, variants via
`class-variance-authority` (CVA), classes merged with `cn()` from `@/lib/utils`.
One family per file, lowercase filename, exported from `components/index.ts`.
`button.tsx` is the reference implementation.

```tsx
const buttonVariants = cva(["/* base classes */"], {
  variants: { variant: { primary: "bg-primary text-primary-foreground …" } },
  defaultVariants: { variant: "primary", size: "md" },
});

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, type = "button", ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  ),
);
Button.displayName = "Button";
```

Use semantic-token utilities only (`bg-primary`, `text-foreground`,
`bg-[var(--color-overlay)]`). Never a primitive or a raw hex. Run
`scripts/check_tokens.py` to enforce it.

## Layout primitives

Compose layout from these three; do not write one-off flex or padding.

- `Stack` (`primitives/stack.tsx`): vertical rhythm. Props `gap`
  (0,1,2,3,4,6,8,12,16) and `align` (start|center|end|stretch). Default `gap=4`,
  `align=stretch`.
- `Cluster` (`primitives/cluster.tsx`): horizontal group that wraps. Props `gap`
  (1,2,3,4,6) and `justify` (start|center|end|between). For tag lists, button
  rows, toolbars, metadata.
- `Grid` (`primitives/grid.tsx`): auto-fit bento. Props `min` (minimum column
  width, e.g. "16rem") and `gap` (2,4,6,8). Wraps fluidly with no breakpoints.

## The shipped components

- Button (`button.tsx`): `variant` = primary | secondary | outline | ghost | link
  | danger; `size` = sm | md | lg | icon. Primary carries the Ember accent.
- Card (`card.tsx`): `variant` = flat | outline | elevated | glass; `padding` =
  none | sm | md | lg. Sub-parts `CardTitle`, `CardDescription`.
- Input (`input.tsx`): `intent` = default | agentic. The agentic variant marks
  natural-language fields with a soft primary ring.
- Badge (`badge.tsx`): `variant` = neutral | primary | success | danger | soft |
  outline. Compact status pill.
- Alert (`alert.tsx`): `intent` = info | success | warning | danger. Takes an
  `icon` and optional `title`; soft status surface, theme-aware.
- Dialog (`dialog.tsx`): Radix-based modal. Parts `Dialog`, `DialogTrigger`,
  `DialogContent`, `DialogTitle`, `DialogDescription`, `DialogFooter`,
  `DialogClose`. Blurred scrim, emphasized entrance.

## Radix and data-state animation

Headless components use Radix primitives for behavior and accessibility, styled
with semantic tokens. Animate on Radix state with arbitrary utilities and the
keyframes defined in `globals.css`:

```tsx
"data-[state=open]:animate-[dialog-in_0.26s_var(--ease-emphasized)]"
"data-[state=closed]:animate-[dialog-out_0.18s_ease]"
```

Keyframes available: `overlay-in/out`, `dialog-in/out`, `toast-in/out`,
`tooltip-in`, `accordion-down/up`, `shimmer`, `indeterminate`.

## Building a new component

1. Create `components/<name>.tsx`. For interactive or overlay behavior, start
   from the matching Radix primitive (`@radix-ui/react-*`).
2. Define variants with CVA and a sensible default. Use semantic tokens only.
3. `forwardRef`, set `displayName`, merge classes with `cn()`.
4. Wire focus: `focus-visible:outline-none focus-visible:ring-2
   focus-visible:ring-ring focus-visible:ring-offset-2
   focus-visible:ring-offset-background`.
5. Export from `components/index.ts`.
6. Run `scripts/check_tokens.py --dir <your-src>`; fix any hit.

## Composition example

```tsx
<Card>
  <Stack gap={4}>
    <CardTitle>Project</CardTitle>
    <CardDescription>A short, plain summary.</CardDescription>
    <Cluster gap={2}>
      <Badge variant="soft">Agentic AI</Badge>
      <Badge variant="outline">GovTech</Badge>
    </Cluster>
    <Cluster gap={3} justify="end">
      <Button variant="ghost">Details</Button>
      <Button>Open</Button>
    </Cluster>
  </Stack>
</Card>
```
