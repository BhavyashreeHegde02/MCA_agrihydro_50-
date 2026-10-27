"use client";

/**
 * Shared chart scaffolding.
 *
 * Recharts renders into a measured container, so every chart needs a
 * ResponsiveContainer and an explicit height. Beyond that, three decisions are
 * made here once rather than per chart:
 *
 *   - colours come from the CSS custom properties, so charts follow the theme
 *     into dark mode instead of keeping light-mode hex values;
 *   - every chart is described in text underneath, because a farmer reading on
 *     a phone in sunlight often cannot resolve a thin line, and a screen reader
 *     cannot read an SVG at all;
 *   - axis labels always carry their unit.
 */

import { ResponsiveContainer } from "recharts";

import { cn } from "@/lib/utils";

/** The five categorical chart slots defined in globals.css. */
export const CHART_COLORS = {
  demand: "var(--chart-1)",
  rainfall: "var(--chart-2)",
  irrigation: "var(--chart-3)",
  reference: "var(--chart-4)",
  deficit: "var(--chart-5)",
} as const;

export const AXIS_STYLE = {
  fontSize: 12,
  fill: "var(--muted-foreground)",
} as const;

export const GRID_STROKE = "var(--border)";

export function ChartFrame({
  title,
  caption,
  summary,
  height = 280,
  children,
  className,
}: {
  title: string;
  /** One line under the chart saying how to read it. */
  caption?: string;
  /**
   * A sentence stating what the chart shows in numbers. This is the chart's
   * accessible alternative, not decoration — it must say the same thing.
   */
  summary: string;
  height?: number;
  children: React.ReactElement;
  className?: string;
}) {
  return (
    <figure className={cn("space-y-2", className)}>
      <figcaption className="text-sm font-medium text-foreground">
        {title}
      </figcaption>
      <div
        style={{ height }}
        role="img"
        aria-label={`${title}. ${summary}`}
        className="w-full"
      >
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </div>
      {caption && (
        <p className="text-xs text-muted-foreground">{caption}</p>
      )}
      {/* Repeated as text so the figures are readable and selectable. */}
      <p className="sr-only">{summary}</p>
    </figure>
  );
}

/**
 * A tooltip that names the unit on every row.
 *
 * Recharts' default prints a bare number. In this application the same chart
 * can carry millimetres per day and millimetres, and an unlabelled figure is
 * how someone applies the wrong amount of water.
 */
export function UnitTooltip({
  active,
  payload,
  label,
  unit,
}: {
  active?: boolean;
  payload?: Array<{ name?: string; value?: number | string; color?: string }>;
  label?: string | number;
  unit: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
      <p className="mb-1 font-medium text-popover-foreground">{label}</p>
      <ul className="space-y-0.5">
        {payload
          .filter((entry) => entry.value !== null && entry.value !== undefined)
          .map((entry, index) => (
            <li
              key={`${entry.name}-${index}`}
              className="flex items-center gap-1.5 text-muted-foreground"
            >
              <span
                aria-hidden
                className="size-2 shrink-0 rounded-full"
                style={{ background: entry.color }}
              />
              <span>{entry.name}</span>
              <span className="tabular ml-auto pl-3 font-medium text-popover-foreground">
                {typeof entry.value === "number"
                  ? entry.value.toFixed(2)
                  : entry.value}{" "}
                {unit}
              </span>
            </li>
          ))}
      </ul>
    </div>
  );
}
