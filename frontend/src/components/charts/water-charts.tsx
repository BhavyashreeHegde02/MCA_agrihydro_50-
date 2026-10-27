"use client";

import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  AXIS_STYLE,
  CHART_COLORS,
  ChartFrame,
  GRID_STROKE,
  UnitTooltip,
} from "@/components/charts/chart-frame";
import type {
  AnalyticsDailyPoint,
  AnalyticsStageTotal,
  KcCurvePoint,
  WeatherOut,
} from "@/lib/api/types";
import { LOCALE, formatDate, formatDepth, humaniseSlug } from "@/lib/format";

/** Trim an ISO date to "12 Sep" for an axis that has to fit on a phone. */
function shortDate(iso: string): string {
  const [datePart] = iso.split("T");
  const [, month, day] = datePart.split("-").map(Number);
  if (!month || !day) return iso;
  return new Date(2000, month - 1, day).toLocaleDateString(LOCALE, {
    day: "numeric",
    month: "short",
  });
}

// ---------------------------------------------------------------------------

/**
 * Demand over time against the physics reference.
 *
 * The conformal interval is drawn as a band behind the line, so the width of
 * what the model does not know is visible rather than stated in a footnote.
 * Recharts has no native interval band, so it is an Area of [lower, upper].
 */
export function DemandTrendChart({ series }: { series: AnalyticsDailyPoint[] }) {
  const data = series.map((point) => ({
    ...point,
    label: shortDate(point.date),
    band:
      point.lower !== null && point.upper !== null
        ? [point.lower, point.upper]
        : null,
  }));

  const hasInterval = data.some((point) => point.band !== null);
  const values = series.map((point) => point.cwr_mm_day);
  const mean = values.length
    ? values.reduce((sum, value) => sum + value, 0) / values.length
    : 0;

  const summary = series.length
    ? `${series.length} prediction${series.length === 1 ? "" : "s"} from ${formatDate(series[0].date)} to ${formatDate(series[series.length - 1].date)}. Crop demand ranges from ${formatDepth(Math.min(...values))} to ${formatDepth(Math.max(...values))} millimetres per day, averaging ${formatDepth(mean)}.`
    : "No predictions in this period.";

  return (
    <ChartFrame
      title="Crop water demand over time"
      summary={summary}
      caption={
        hasInterval
          ? "The shaded band is the 90% interval: the model expects the true value to fall inside it nine times in ten. The dashed line is what the FAO-56 calculation alone gives."
          : "The dashed line is what the FAO-56 calculation alone gives, for comparison."
      }
      height={300}
    >
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: -8 }}>
        <CartesianGrid stroke={GRID_STROKE} strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" tick={AXIS_STYLE} tickLine={false} axisLine={false} minTickGap={24} />
        <YAxis
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          width={48}
          label={{
            value: "mm/day",
            angle: -90,
            position: "insideLeft",
            style: { ...AXIS_STYLE, textAnchor: "middle" },
          }}
        />
        <Tooltip content={<UnitTooltip unit="mm/day" />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {hasInterval && (
          <Area
            dataKey="band"
            name="90% interval"
            stroke="none"
            fill={CHART_COLORS.demand}
            fillOpacity={0.16}
            isAnimationActive={false}
            connectNulls
          />
        )}
        <Line
          type="monotone"
          dataKey="baseline_mm_day"
          name="FAO-56 reference"
          stroke={CHART_COLORS.reference}
          strokeWidth={1.5}
          strokeDasharray="5 4"
          dot={false}
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="cwr_mm_day"
          name="Predicted demand"
          stroke={CHART_COLORS.demand}
          strokeWidth={2.5}
          dot={false}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ChartFrame>
  );
}

// ---------------------------------------------------------------------------

/**
 * What must be delivered, against what rainfall already supplied.
 *
 * Stacked, because the two together are the crop's supply: the point of the
 * chart is that rain reduces the bar above it.
 */
export function IrrigationVersusRainChart({
  series,
}: {
  series: AnalyticsDailyPoint[];
}) {
  const data = series.map((point) => ({
    ...point,
    label: shortDate(point.date),
  }));

  const totalIrrigation = series.reduce(
    (sum, point) => sum + point.gross_irrigation_mm,
    0,
  );
  const totalRain = series.reduce(
    (sum, point) => sum + point.effective_rainfall_mm,
    0,
  );

  return (
    <ChartFrame
      title="Irrigation needed against usable rainfall"
      summary={`Across ${series.length} day${series.length === 1 ? "" : "s"}, ${formatDepth(totalIrrigation)} millimetres of gross irrigation was required and ${formatDepth(totalRain)} millimetres of rainfall was usable by the crop.`}
      caption="Effective rainfall is the part of the rain the crop can actually use; the rest runs off, evaporates or drains below the roots. Every millimetre of it is a millimetre you do not have to pump."
      height={280}
    >
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: -8 }}>
        <CartesianGrid stroke={GRID_STROKE} strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" tick={AXIS_STYLE} tickLine={false} axisLine={false} minTickGap={24} />
        <YAxis
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          width={48}
          label={{
            value: "mm",
            angle: -90,
            position: "insideLeft",
            style: { ...AXIS_STYLE, textAnchor: "middle" },
          }}
        />
        <Tooltip content={<UnitTooltip unit="mm" />} cursor={{ fill: "var(--muted)" }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar
          dataKey="effective_rainfall_mm"
          name="Usable rainfall"
          stackId="supply"
          fill={CHART_COLORS.rainfall}
          radius={[0, 0, 0, 0]}
          isAnimationActive={false}
        />
        <Bar
          dataKey="gross_irrigation_mm"
          name="Gross irrigation"
          stackId="supply"
          fill={CHART_COLORS.irrigation}
          radius={[3, 3, 0, 0]}
          isAnimationActive={false}
        />
      </BarChart>
    </ChartFrame>
  );
}

// ---------------------------------------------------------------------------

/** Total demand per growth stage — where the season's water actually goes. */
export function StageDemandChart({ stages }: { stages: AnalyticsStageTotal[] }) {
  const data = stages.map((stage) => ({
    ...stage,
    label: humaniseSlug(stage.growth_stage),
  }));

  const heaviest = [...stages].sort(
    (a, b) => b.mean_demand_mm_day - a.mean_demand_mm_day,
  )[0];

  return (
    <ChartFrame
      title="Average daily demand by growth stage"
      summary={
        heaviest
          ? `${humaniseSlug(heaviest.growth_stage)} is the thirstiest stage, averaging ${formatDepth(heaviest.mean_demand_mm_day)} millimetres per day across ${heaviest.days} day${heaviest.days === 1 ? "" : "s"}.`
          : "No predictions yet."
      }
      caption="The crop coefficient rises through the season and falls again as the crop matures, so the same weather produces different demand at different stages."
      height={240}
    >
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 16, bottom: 4, left: 8 }}
      >
        <CartesianGrid stroke={GRID_STROKE} strokeDasharray="3 3" horizontal={false} />
        <XAxis
          type="number"
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          label={{
            value: "mm/day",
            position: "insideBottom",
            offset: -2,
            style: AXIS_STYLE,
          }}
        />
        <YAxis
          type="category"
          dataKey="label"
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          width={96}
        />
        <Tooltip content={<UnitTooltip unit="mm/day" />} cursor={{ fill: "var(--muted)" }} />
        <Bar
          dataKey="mean_demand_mm_day"
          name="Mean daily demand"
          fill={CHART_COLORS.demand}
          radius={[0, 4, 4, 0]}
          isAnimationActive={false}
        />
      </BarChart>
    </ChartFrame>
  );
}

// ---------------------------------------------------------------------------

/**
 * The crop coefficient curve.
 *
 * This is the single most explanatory chart in the application: it is the whole
 * reason growth stage matters, drawn.
 */
export function KcCurveChart({
  points,
  currentDay,
  cropName,
}: {
  points: KcCurvePoint[];
  currentDay?: number;
  cropName: string;
}) {
  const peak = points.reduce(
    (best, point) => (point.kc > best.kc ? point : best),
    points[0] ?? { kc: 0, days_after_sowing: 0, stage: "" },
  );

  return (
    <ChartFrame
      title={`Crop coefficient through the season — ${cropName}`}
      summary={`The crop coefficient runs from ${points[0]?.kc.toFixed(2) ?? "—"} at sowing to a peak of ${peak.kc.toFixed(2)} around day ${peak.days_after_sowing}, then falls as the crop matures.`}
      caption="Kc multiplies the reference evapotranspiration to give this crop's own demand. A Kc of 1.2 means the crop uses twenty per cent more water than the reference grass surface would on the same day."
      height={260}
    >
      <LineChart data={points} margin={{ top: 8, right: 12, bottom: 4, left: -8 }}>
        <CartesianGrid stroke={GRID_STROKE} strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="days_after_sowing"
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          // The curve is sampled every few days, and one tick per sample is a
          // solid band of unreadable numbers on a phone.
          interval="preserveStartEnd"
          minTickGap={40}
          label={{
            value: "days after sowing",
            position: "insideBottom",
            offset: -2,
            style: AXIS_STYLE,
          }}
        />
        <YAxis
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          width={44}
          domain={[0, "auto"]}
          label={{
            value: "Kc",
            angle: -90,
            position: "insideLeft",
            style: { ...AXIS_STYLE, textAnchor: "middle" },
          }}
        />
        <Tooltip content={<UnitTooltip unit="" />} />
        {currentDay !== undefined && (
          <ReferenceLine
            x={currentDay}
            stroke={CHART_COLORS.deficit}
            strokeWidth={2}
            label={{
              value: "today",
              position: "top",
              style: { ...AXIS_STYLE, fill: CHART_COLORS.deficit },
            }}
          />
        )}
        <Line
          type="monotone"
          dataKey="kc"
          name="Crop coefficient"
          stroke={CHART_COLORS.demand}
          strokeWidth={2.5}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ChartFrame>
  );
}

// ---------------------------------------------------------------------------

/** Temperature range and rainfall for a forecast window. */
export function WeatherForecastChart({ days }: { days: WeatherOut[] }) {
  const data = days.map((day) => ({
    label: shortDate(day.date),
    min: day.temperature_min_c,
    max: day.temperature_max_c,
    rain: day.rainfall_mm,
  }));

  const totalRain = days.reduce((sum, day) => sum + day.rainfall_mm, 0);

  return (
    <ChartFrame
      title="Temperature and rainfall"
      summary={`Over ${days.length} days, temperatures run from ${formatDepth(Math.min(...days.map((d) => d.temperature_min_c)))} to ${formatDepth(Math.max(...days.map((d) => d.temperature_max_c)))} degrees, with ${formatDepth(totalRain)} millimetres of rain in total.`}
      caption="Temperature drives reference evapotranspiration; rainfall reduces what you have to apply. Both feed the prediction directly."
      height={260}
    >
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: -8 }}>
        <CartesianGrid stroke={GRID_STROKE} strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" tick={AXIS_STYLE} tickLine={false} axisLine={false} minTickGap={16} />
        <YAxis
          yAxisId="temp"
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          width={44}
          label={{
            value: "°C",
            angle: -90,
            position: "insideLeft",
            style: { ...AXIS_STYLE, textAnchor: "middle" },
          }}
        />
        <YAxis
          yAxisId="rain"
          orientation="right"
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          width={44}
          label={{
            value: "mm",
            angle: 90,
            position: "insideRight",
            style: { ...AXIS_STYLE, textAnchor: "middle" },
          }}
        />
        <Tooltip content={<UnitTooltip unit="" />} cursor={{ fill: "var(--muted)" }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar
          yAxisId="rain"
          dataKey="rain"
          name="Rain (mm)"
          fill={CHART_COLORS.rainfall}
          radius={[3, 3, 0, 0]}
          isAnimationActive={false}
        />
        <Line
          yAxisId="temp"
          type="monotone"
          dataKey="max"
          name="Max (°C)"
          stroke={CHART_COLORS.deficit}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
        <Line
          yAxisId="temp"
          type="monotone"
          dataKey="min"
          name="Min (°C)"
          stroke={CHART_COLORS.demand}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ChartFrame>
  );
}
