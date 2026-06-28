import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Stack: vertical rhythm primitive.
 * Lays children out in a column with a single, token-based gap.
 * Prefer this over ad-hoc margins to keep spacing on the 4px grid.
 */
const gapMap = {
  0: "gap-0",
  1: "gap-1",
  2: "gap-2",
  3: "gap-3",
  4: "gap-4",
  6: "gap-6",
  8: "gap-8",
  12: "gap-12",
  16: "gap-16",
} as const;

const alignMap = {
  start: "items-start",
  center: "items-center",
  end: "items-end",
  stretch: "items-stretch",
} as const;

export interface StackProps extends React.HTMLAttributes<HTMLDivElement> {
  gap?: keyof typeof gapMap;
  align?: keyof typeof alignMap;
  asChild?: never;
}

export const Stack = React.forwardRef<HTMLDivElement, StackProps>(
  ({ className, gap = 4, align = "stretch", ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex flex-col", gapMap[gap], alignMap[align], className)}
      {...props}
    />
  ),
);
Stack.displayName = "Stack";
