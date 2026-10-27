import { cn } from "@/lib/utils";

export type StatTone = "neutral" | "ok" | "warn" | "danger" | "primary";

const TONE_TEXT: Record<StatTone, string> = {
  neutral: "text-foreground",
  ok: "text-ok",
  warn: "text-warn",
  danger: "text-danger",
  primary: "text-primary",
};

/**
 * One number, with its unit and its meaning.
 *
 * The unit is a separate element and never folded into the value string. This
 * application reports millimetres per day, millimetres, litres, hectares and
 * percentages side by side, and a figure shown without its unit here is not
 * information — it is a chance to irrigate by the wrong quantity.
 */
export function Stat({
  label,
  value,
  unit,
  hint,
  tone = "neutral",
  className,
}: {
  label: string;
  value: React.ReactNode;
  unit?: string;
  hint?: React.ReactNode;
  tone?: StatTone;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl bg-card px-4 py-3 ring-1 ring-foreground/10",
        className,
      )}
    >
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
        {label}
      </p>
      <p className="mt-1 flex items-baseline gap-1.5">
        <span className={cn("tabular text-2xl font-semibold", TONE_TEXT[tone])}>
          {value}
        </span>
        {unit && (
          <span className="text-sm text-muted-foreground">{unit}</span>
        )}
      </p>
      {hint && (
        <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
      )}
    </div>
  );
}
