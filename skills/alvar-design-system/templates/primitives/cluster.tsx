import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Cluster: horizontal group of items that wraps gracefully.
 * Use for tag lists, button rows, metadata, toolbars.
 */
const gapMap = {
  1: "gap-1",
  2: "gap-2",
  3: "gap-3",
  4: "gap-4",
  6: "gap-6",
} as const;

const justifyMap = {
  start: "justify-start",
  center: "justify-center",
  end: "justify-end",
  between: "justify-between",
} as const;

export interface ClusterProps extends React.HTMLAttributes<HTMLDivElement> {
  gap?: keyof typeof gapMap;
  justify?: keyof typeof justifyMap;
}

export const Cluster = React.forwardRef<HTMLDivElement, ClusterProps>(
  ({ className, gap = 2, justify = "start", ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flex-wrap items-center",
        gapMap[gap],
        justifyMap[justify],
        className,
      )}
      {...props}
    />
  ),
);
Cluster.displayName = "Cluster";
