import {
  AlertTriangle,
  CheckCircle2,
  Info,
  XCircle,
  type LucideIcon,
} from "lucide-react";

import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";

export type NoticeTone = "info" | "success" | "warning" | "danger";

const ICONS: Record<NoticeTone, LucideIcon> = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: XCircle,
};

/**
 * shadcn's Alert with the icon and the live-region behaviour already decided.
 *
 * Two things are handled here rather than at each call site. The icon is
 * derived from the tone, so a warning can never be shown with a tick beside it.
 * And only a failure interrupts a screen reader — shadcn's Alert hard-codes
 * `role="alert"`, which would make an informational note talk over whatever the
 * farmer is in the middle of doing, so anything that is not a danger is
 * downgraded to a polite status.
 */
export function Notice({
  tone = "info",
  title,
  children,
  icon,
  className,
}: {
  tone?: NoticeTone;
  title?: string;
  children?: React.ReactNode;
  icon?: LucideIcon;
  className?: string;
}) {
  const Icon = icon ?? ICONS[tone];
  return (
    <Alert
      variant={tone}
      className={className}
      {...(tone === "danger"
        ? { role: "alert" as const }
        : { role: "status" as const, "aria-live": "polite" as const })}
    >
      <Icon />
      {title && <AlertTitle>{title}</AlertTitle>}
      {children && <AlertDescription>{children}</AlertDescription>}
    </Alert>
  );
}
