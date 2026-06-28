import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Grid: responsive auto-fit grid for bento layouts and card collections.
 * `min` sets the minimum column width; columns fill the row and wrap fluidly
 * with no manual breakpoints (the Fluid Void).
 */
const gapMap = {
  2: "gap-2",
  4: "gap-4",
  6: "gap-6",
  8: "gap-8",
} as const;

export interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Minimum column width before wrapping, e.g. "16rem". */
  min?: string;
  gap?: keyof typeof gapMap;
}

export const Grid = React.forwardRef<HTMLDivElement, GridProps>(
  ({ className, min = "16rem", gap = 4, style, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("grid", gapMap[gap], className)}
      style={{
        gridTemplateColumns: `repeat(auto-fit, minmax(min(${min}, 100%), 1fr))`,
        ...style,
      }}
      {...props}
    />
  ),
);
Grid.displayName = "Grid";
