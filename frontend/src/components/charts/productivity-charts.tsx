"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Legend,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import {
  AXIS_STYLE,
  CHART_COLORS,
  ChartFrame,
  GRID_STROKE,
  UnitTooltip,
} from "@/components/charts/chart-frame";
import type { WaterProductivityItem } from "@/lib/api/types";
import { humaniseSlug } from "@/lib/format";

/** Crop labels read better than slugs on an axis. */
function label(crop: string): string {
  return humaniseSlug(crop);
}

/**
 * Crops ranked by what they return per unit of water.
 *
 * Both productivities are drawn together rather than in separate charts,
 * because the gap between them *is* the irrigation system's loss and is the
 * thing worth seeing. A crop whose two bars are far apart is one where
 * improving delivery would pay.
 */
export function ProductivityRankChart({
  crops,
}: {
  crops: WaterProductivityItem[];
}) {
  const data = crops.map((crop) => ({
    ...crop,
    label: label(crop.crop),
  }));

  const best = crops[0];
  const worst = crops[crops.length - 1];

  return (
    <ChartFrame
      title="Crop per drop"
      summary={
        best && worst
          ? `${label(best.crop)} returns ${best.wp_etc_kg_per_m3.toFixed(3)} kilograms per cubic metre transpired, the highest of ${crops.length} crops. ${label(worst.crop)} returns ${worst.wp_etc_kg_per_m3.toFixed(3)}, the lowest.`
          : "No crops to rank."
      }
      caption="The upper bar is what the plant achieves per cubic metre it transpires. The lower bar is what you achieve per cubic metre pumped, after irrigation losses. A wide gap means delivery is where the water goes."
      height={Math.max(240, crops.length * 52)}
    >
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 40, bottom: 16, left: 8 }}
        barGap={2}
      >
        <CartesianGrid stroke={GRID_STROKE} strokeDasharray="3 3" horizontal={false} />
        <XAxis
          type="number"
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          label={{
            value: "kg per m³",
            position: "insideBottom",
            offset: -6,
            style: AXIS_STYLE,
          }}
        />
        <YAxis
          type="category"
          dataKey="label"
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          width={104}
        />
        <Tooltip content={<UnitTooltip unit="kg/m³" />} cursor={{ fill: "var(--muted)" }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar
          dataKey="wp_etc_kg_per_m3"
          name="Per m³ transpired"
          fill={CHART_COLORS.demand}
          radius={[0, 4, 4, 0]}
          isAnimationActive={false}
        >
          <LabelList
            dataKey="wp_etc_kg_per_m3"
            position="right"
            // Recharts types this as RenderableText, which can be undefined.
            formatter={(value: unknown) =>
              typeof value === "number" ? value.toFixed(2) : ""
            }
            style={{ ...AXIS_STYLE, fontSize: 11 }}
          />
        </Bar>
        <Bar
          dataKey="wp_applied_kg_per_m3"
          name="Per m³ pumped"
          fill={CHART_COLORS.irrigation}
          radius={[0, 4, 4, 0]}
          isAnimationActive={false}
        />
      </BarChart>
    </ChartFrame>
  );
}

// ---------------------------------------------------------------------------

/**
 * Value per cubic metre.
 *
 * Kept as its own chart rather than a third bar on the one above, because it
 * is measured in different units and routinely disagrees with the physical
 * ranking — a crop can be the most efficient converter of water into biomass
 * and still not be the most efficient converter of water into income.
 */
export function EconomicProductivityChart({
  crops,
}: {
  crops: WaterProductivityItem[];
}) {
  const priced = crops
    .filter((crop) => crop.ewp_etc_rs_per_m3 !== null)
    .map((crop) => ({ ...crop, label: label(crop.crop) }))
    .sort(
      (a, b) => (b.ewp_etc_rs_per_m3 ?? 0) - (a.ewp_etc_rs_per_m3 ?? 0),
    );

  if (priced.length === 0) {
    return null;
  }

  const physicalBest = [...crops].sort(
    (a, b) => b.wp_etc_kg_per_m3 - a.wp_etc_kg_per_m3,
  )[0];
  const economicBest = priced[0];
  const disagree = physicalBest && economicBest.crop !== physicalBest.crop;

  return (
    <ChartFrame
      title="Value per drop"
      summary={`${economicBest.label} returns ₹${economicBest.ewp_etc_rs_per_m3?.toFixed(2)} per cubic metre at its support price, the highest of ${priced.length} crops.${disagree ? ` This differs from the physical ranking, where ${label(physicalBest.crop)} leads.` : ""}`}
      caption={
        disagree
          ? `Note that this disagrees with the chart above. ${label(physicalBest.crop)} converts water into the most kilograms; ${economicBest.label} converts it into the most rupees. Which one matters depends on whether you are feeding a household or selling a crop.`
          : "Valued at the minimum support price, which is an annual published figure rather than a market snapshot."
      }
      height={Math.max(220, priced.length * 44)}
    >
      <BarChart
        data={priced}
        layout="vertical"
        margin={{ top: 4, right: 48, bottom: 16, left: 8 }}
      >
        <CartesianGrid stroke={GRID_STROKE} strokeDasharray="3 3" horizontal={false} />
        <XAxis
          type="number"
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          label={{
            value: "₹ per m³",
            position: "insideBottom",
            offset: -6,
            style: AXIS_STYLE,
          }}
        />
        <YAxis
          type="category"
          dataKey="label"
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          width={104}
        />
        <Tooltip content={<UnitTooltip unit="₹/m³" />} cursor={{ fill: "var(--muted)" }} />
        <Bar
          dataKey="ewp_etc_rs_per_m3"
          name="Value per m³"
          radius={[0, 4, 4, 0]}
          isAnimationActive={false}
        >
          {priced.map((crop, index) => (
            <Cell
              key={crop.crop}
              // The leader is highlighted; the rest share one colour so the
              // chart reads as a ranking rather than a categorical palette.
              fill={index === 0 ? CHART_COLORS.rainfall : CHART_COLORS.demand}
            />
          ))}
          <LabelList
            dataKey="ewp_etc_rs_per_m3"
            position="right"
            formatter={(value: unknown) =>
              typeof value === "number" ? `₹${value.toFixed(1)}` : ""
            }
            style={{ ...AXIS_STYLE, fontSize: 11 }}
          />
        </Bar>
      </BarChart>
    </ChartFrame>
  );
}

// ---------------------------------------------------------------------------

/**
 * Water demand against value returned.
 *
 * The quadrant a crop sits in is the decision: bottom-right is a crop that
 * drinks little and returns much, top-left is the reverse. Plotting them
 * against each other makes that visible in a way two ranked lists do not.
 */
export function WaterValueScatter({
  crops,
}: {
  crops: WaterProductivityItem[];
}) {
  const priced = crops.filter((crop) => crop.revenue_msp_rs_ha !== null);
  if (priced.length < 2) return null;

  const data = priced.map((crop) => ({
    x: crop.etc_mm,
    y: (crop.revenue_msp_rs_ha ?? 0) / 1000,
    z: crop.wp_etc_kg_per_m3 * 100,
    label: label(crop.crop),
  }));

  const thrifty = [...priced].sort((a, b) => a.etc_mm - b.etc_mm)[0];
  const richest = [...priced].sort(
    (a, b) => (b.revenue_msp_rs_ha ?? 0) - (a.revenue_msp_rs_ha ?? 0),
  )[0];

  return (
    <ChartFrame
      title="Water needed against value returned"
      summary={`${label(thrifty.crop)} needs the least water at ${thrifty.etc_mm.toFixed(0)} millimetres a season. ${label(richest.crop)} returns the most per hectare at ₹${((richest.revenue_msp_rs_ha ?? 0) / 1000).toFixed(0)} thousand.`}
      caption="Lower and further right is better: less water for more income. Bubble size is kilograms per cubic metre, so a large bubble low on the chart is the crop to look at first."
      height={320}
    >
      <ScatterChart margin={{ top: 12, right: 24, bottom: 20, left: 4 }}>
        <CartesianGrid stroke={GRID_STROKE} strokeDasharray="3 3" />
        <XAxis
          type="number"
          dataKey="x"
          name="Season water"
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          label={{
            value: "season water (mm)",
            position: "insideBottom",
            offset: -8,
            style: AXIS_STYLE,
          }}
        />
        <YAxis
          type="number"
          dataKey="y"
          name="Value"
          tick={AXIS_STYLE}
          tickLine={false}
          axisLine={false}
          width={56}
          label={{
            value: "₹ thousand / ha",
            angle: -90,
            position: "insideLeft",
            style: { ...AXIS_STYLE, textAnchor: "middle" },
          }}
        />
        <ZAxis type="number" dataKey="z" range={[80, 620]} name="kg/m³ ×100" />
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const point = payload[0].payload as (typeof data)[number];
            return (
              <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
                <p className="font-medium text-popover-foreground">{point.label}</p>
                <p className="tabular mt-1 text-muted-foreground">
                  {point.x.toFixed(0)} mm · ₹{point.y.toFixed(0)}k/ha ·{" "}
                  {(point.z / 100).toFixed(2)} kg/m³
                </p>
              </div>
            );
          }}
        />
        <Scatter data={data} fill={CHART_COLORS.demand} isAnimationActive={false}>
          <LabelList
            dataKey="label"
            position="top"
            style={{ ...AXIS_STYLE, fontSize: 11 }}
          />
        </Scatter>
      </ScatterChart>
    </ChartFrame>
  );
}
