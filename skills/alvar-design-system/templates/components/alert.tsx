import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/**
 * Alert: inline callout with a soft status surface and matching border/icon.
 * Pass an `icon` (e.g. a lucide-react glyph) and optional `title`; body is
 * `children`. Status colour resolves through semantic tokens, so it flips with
 * the theme.
 */
const alertVariants = cva("flex gap-3 rounded-md border p-4 text-sm", {
  variants: {
    intent: {
      info: "bg-info-surface border-info/30 [&_svg]:text-info",
      success: "bg-success-surface border-success/30 [&_svg]:text-success",
      warning: "bg-warning-surface border-warning/35 [&_svg]:text-warning",
      danger: "bg-danger-surface border-danger/30 [&_svg]:text-danger",
    },
  },
  defaultVariants: { intent: "info" },
});

export interface AlertProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {
  icon?: React.ReactNode;
  title?: string;
}

export const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, intent, icon, title, children, ...props }, ref) => (
    <div
      ref={ref}
      role="alert"
      className={cn(alertVariants({ intent }), className)}
      {...props}
    >
      {icon && <span className="mt-0.5 shrink-0 [&_svg]:size-5">{icon}</span>}
      <div className="flex-1">
        {title && <p className="font-semibold">{title}</p>}
        {children && <div className="mt-0.5 text-muted-foreground">{children}</div>}
      </div>
    </div>
  ),
);
Alert.displayName = "Alert";

export { alertVariants };
