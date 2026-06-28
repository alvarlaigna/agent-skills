import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/**
 * Input: single-line text field.
 * The `intent="agentic"` variant visually differentiates natural-language /
 * semantic-search inputs from deterministic fields (contextual affordances).
 */
const inputVariants = cva(
  [
    "flex h-10 w-full rounded-md bg-surface-raised px-3 py-2 text-sm text-foreground",
    "placeholder:text-muted-foreground",
    "transition-[border-color,box-shadow] duration-[var(--duration-base)] ease-[var(--ease-standard)]",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
    "disabled:cursor-not-allowed disabled:opacity-50",
  ],
  {
    variants: {
      intent: {
        default: "border border-input",
        agentic:
          "border border-primary/40 shadow-[0_0_0_3px_color-mix(in_oklab,var(--color-action-primary)_12%,transparent)] focus-visible:border-primary",
      },
    },
    defaultVariants: {
      intent: "default",
    },
  },
);

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement>,
    VariantProps<typeof inputVariants> {}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, intent, type = "text", ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn(inputVariants({ intent }), className)}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export { inputVariants };
