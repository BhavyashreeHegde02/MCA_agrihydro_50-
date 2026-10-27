"use client";

/**
 * The irrigation calculation, shown as a chain rather than as one number.
 *
 * A farmer told only "apply 5.4 mm" has no way to judge whether that is
 * reasonable, and no way to notice when an assumption behind it is wrong for
 * their field. Each step names what it does, shows its arithmetic, and states
 * its unit, so the figure can be argued with.
 */

import { ArrowDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { formatDepth, formatLitres, formatPercent } from "@/lib/format";

export interface BreakdownInputs {
  /** Omitted when the caller is recalculating from a stored demand. */
  et0MmDay?: number | null;
  /** Omitted for the same reason as et0MmDay. */
  kc?: number | null;
  cwrMmDay: number;
  rainfallMm?: number | null;
  effectiveRainfallMm: number;
  forecastRainfallMm?: number | null;
  netIrrigationMm: number;
  grossIrrigationMm: number;
  applicationEfficiency: number;
  grossIrrigationLitres?: number | null;
  areaHa?: number | null;
}

interface Step {
  label: string;
  formula: string;
  result: string;
  explanation: string;
  emphasis?: boolean;
}

export function IrrigationBreakdown({
  inputs,
  className,
}: {
  inputs: BreakdownInputs;
  className?: string;
}) {
  const rainCredit =
    inputs.forecastRainfallMm && inputs.forecastRainfallMm > 0
      ? inputs.effectiveRainfallMm + inputs.forecastRainfallMm
      : inputs.effectiveRainfallMm;

  // The first two steps explain where the demand came from. The recalculation
  // endpoint starts from a demand that is already stored, so they are dropped
  // there rather than shown with placeholder values.
  const showsDerivation =
    typeof inputs.et0MmDay === "number" &&
    Number.isFinite(inputs.et0MmDay) &&
    typeof inputs.kc === "number" &&
    Number.isFinite(inputs.kc);

  const derivation: Step[] = showsDerivation
    ? [
        {
          label: "Reference evapotranspiration",
          formula: "ET₀ from the day's weather (FAO-56 Penman-Monteith)",
          result: `${formatDepth(inputs.et0MmDay)} mm/day`,
          explanation:
            "How much water a short, well-watered grass surface would lose today. It depends only on the weather, not on your crop — it is the common yardstick every crop is measured against.",
        },
        {
          label: "Crop coefficient",
          formula: "Kc for this crop at this growth stage",
          result: inputs.kc!.toFixed(2),
          explanation:
            "How thirsty this crop is compared with that reference grass, right now. It changes through the season: small seedlings use less than the reference, a full canopy uses more.",
        },
      ]
    : [];

  const steps: Step[] = [
    ...derivation,
    {
      label: "Crop water requirement",
      formula: showsDerivation
        ? `ETc = ET₀ × Kc = ${formatDepth(inputs.et0MmDay)} × ${inputs.kc!.toFixed(2)}`
        : "ETc, as established by the stored prediction",
      result: `${formatDepth(inputs.cwrMmDay)} mm/day`,
      explanation:
        "What the crop will actually lose today through its leaves and the soil surface. This is demand — it is not yet the amount you need to apply.",
      emphasis: true,
    },
    {
      label: "Usable rainfall",
      formula:
        inputs.rainfallMm !== null && inputs.rainfallMm !== undefined
          ? `effective rainfall from ${formatDepth(inputs.rainfallMm)} mm of rain`
          : "effective rainfall",
      result: `${formatDepth(inputs.effectiveRainfallMm)} mm`,
      explanation:
        "Not all rain reaches the roots. Some is caught on leaves and evaporates, some runs off, some drains below the root zone. Only the remainder counts against what you need to apply.",
    },
    {
      label: "Net irrigation requirement",
      formula: `${formatDepth(inputs.cwrMmDay)} − ${formatDepth(rainCredit)} = ${formatDepth(inputs.netIrrigationMm)}`,
      result: `${formatDepth(inputs.netIrrigationMm)} mm`,
      explanation:
        "The depth of water that has to arrive at the roots. If rain covered the whole requirement this would be zero, and you would not irrigate at all today.",
    },
    {
      label: "Application efficiency",
      formula: "how much of what you deliver actually reaches the root zone",
      result: formatPercent(inputs.applicationEfficiency),
      explanation: `Your irrigation method loses about ${formatPercent(1 - inputs.applicationEfficiency)} of what is delivered. Drip loses least; flood loses most. This is why the next figure is larger than the one above.`,
    },
    {
      label: "Gross irrigation — what to apply",
      formula: `${formatDepth(inputs.netIrrigationMm)} ÷ ${inputs.applicationEfficiency.toFixed(2)} = ${formatDepth(inputs.grossIrrigationMm)}`,
      result: `${formatDepth(inputs.grossIrrigationMm)} mm`,
      explanation:
        "The depth to deliver so that the net requirement arrives. This is the number to act on.",
      emphasis: true,
    },
  ];

  if (
    inputs.grossIrrigationLitres !== null &&
    inputs.grossIrrigationLitres !== undefined
  ) {
    steps.push({
      label: "In litres",
      formula:
        inputs.areaHa != null
          ? `${formatDepth(inputs.grossIrrigationMm)} mm × ${inputs.areaHa} ha × 10,000`
          : "depth × area × 10,000",
      result: `${formatLitres(inputs.grossIrrigationLitres)} L`,
      explanation:
        "One millimetre spread over one hectare is ten thousand litres. This is the same figure as above, in the units a pump is measured in.",
      emphasis: true,
    });
  }

  return (
    <ol className={cn("space-y-0", className)}>
      {steps.map((step, index) => (
        <li key={step.label}>
          <div
            className={cn(
              "rounded-lg border p-3.5",
              step.emphasis
                ? "border-primary/30 bg-info-surface"
                : "border-border bg-card",
            )}
          >
            <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
              <p className="font-medium text-foreground">
                <span className="mr-1.5 text-muted-foreground tabular">
                  {index + 1}.
                </span>
                {step.label}
              </p>
              <p
                className={cn(
                  "tabular font-semibold",
                  step.emphasis ? "text-primary text-lg" : "text-foreground",
                )}
              >
                {step.result}
              </p>
            </div>
            <p className="tabular mt-1 font-mono text-xs text-muted-foreground">
              {step.formula}
            </p>
            <p className="mt-1.5 text-sm text-muted-foreground">
              {step.explanation}
            </p>
          </div>
          {index < steps.length - 1 && (
            <div className="flex justify-center py-1">
              <ArrowDown aria-hidden className="size-4 text-muted-foreground" />
            </div>
          )}
        </li>
      ))}
    </ol>
  );
}
