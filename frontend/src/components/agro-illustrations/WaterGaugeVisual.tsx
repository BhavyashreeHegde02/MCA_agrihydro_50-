"use client";

import { Droplets, Sparkles, TrendingUp, Waves, Zap } from "lucide-react";
import { formatDepth, formatPercent } from "@/lib/format";

interface WaterGaugeProps {
  cwrMmDay: number;
  expectedMinMm?: number | null;
  expectedMaxMm?: number | null;
  cropName?: string;
  nominalCoverage?: number | null;
  grossLitres?: number | null;
  className?: string;
}

export function WaterGaugeVisual({
  cwrMmDay,
  expectedMinMm,
  expectedMaxMm,
  cropName = "Crop",
  nominalCoverage,
  grossLitres,
  className = "",
}: WaterGaugeProps) {
  // Normalize water level between 1mm (min) and 10mm (max) for gauge display (30% to 85% fill)
  const clampedCwr = Math.max(1, Math.min(10, cwrMmDay));
  const fillPercentage = Math.round(25 + ((clampedCwr - 1) / 9) * 60);

  // Demand band assessment
  const demandLevel =
    cwrMmDay < 3.5 ? "Low Demand" : cwrMmDay < 6.5 ? "Moderate Demand" : "High Peak Demand";
  const demandBadgeColor =
    cwrMmDay < 3.5
      ? "bg-emerald-100 text-emerald-800 border-emerald-300"
      : cwrMmDay < 6.5
      ? "bg-blue-100 text-blue-800 border-blue-300"
      : "bg-amber-100 text-amber-800 border-amber-300";

  return (
    <div
      className={`relative overflow-hidden rounded-3xl border border-emerald-200/90 bg-gradient-to-b from-white via-emerald-50/30 to-sky-50/50 p-6 sm:p-8 shadow-sm ${className}`}
    >
      <div className="flex flex-col md:flex-row items-center justify-between gap-8">
        {/* Left / Center: The Animated Circular Water Gauge */}
        <div className="flex flex-col items-center shrink-0">
          <div className="relative size-56 sm:size-64 rounded-full border-4 border-emerald-200/80 bg-emerald-50/40 p-2 shadow-inner shadow-emerald-900/5 flex items-center justify-center">
            {/* Outer Rotating Ripple Ring */}
            <div className="absolute inset-0 rounded-full border-2 border-dashed border-sky-300/60 animate-spin" style={{ animationDuration: "40s" }} />

            {/* Inner Water Reservoir Container */}
            <div className="relative size-full rounded-full overflow-hidden bg-gradient-to-b from-sky-50 to-emerald-50/70 border border-emerald-200 flex flex-col justify-end">
              {/* Animated Fluid Water Fill */}
              <div
                className="w-full bg-gradient-to-t from-sky-500 via-sky-400 to-sky-300 transition-all duration-1000 ease-out relative"
                style={{ height: `${fillPercentage}%` }}
              >
                {/* Surface Wave Ribbon */}
                <div className="absolute -top-3 left-0 right-0 h-4 bg-sky-300/80 rounded-[50%] blur-[0.5px] animate-pulse" />
                <div className="absolute -top-1.5 left-0 right-0 h-3 bg-sky-200/60 rounded-[50%]" />

                {/* Subsurface Water Bubbles */}
                <div className="absolute bottom-2 left-6 size-2 rounded-full bg-white/60 animate-particle-float" />
                <div className="absolute bottom-5 right-8 size-2.5 rounded-full bg-white/70 animate-particle-float" style={{ animationDelay: "1.5s" }} />
              </div>

              {/* Water Need Content Overlay (Floating in center of circle) */}
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center z-10 px-4">
                <div className="size-8 rounded-full bg-white/90 text-sky-600 flex items-center justify-center shadow-sm mb-1">
                  <Droplets className="size-4.5" />
                </div>

                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-950/80">
                  WATER NEED
                </span>

                <div className="flex items-baseline justify-center gap-1 my-0.5">
                  <span className="text-4xl sm:text-5xl font-black tracking-tight text-foreground tabular">
                    {formatDepth(cwrMmDay)}
                  </span>
                  <span className="text-sm font-bold text-muted-foreground">mm/day</span>
                </div>

                <p className="text-[11px] font-semibold text-emerald-900/90 leading-tight">
                  Estimated Crop Water Need
                </p>

                <span className={`mt-2 text-[10px] font-bold px-2 py-0.5 rounded-full border ${demandBadgeColor}`}>
                  {demandLevel}
                </span>
              </div>
            </div>
          </div>

          <p className="text-xs text-muted-foreground text-center mt-3 font-medium">
            Daily evapotranspiration for <strong className="text-foreground">{cropName}</strong>
          </p>
        </div>

        {/* Right: Farmer-Friendly Interpretation & Uncertainty Range */}
        <div className="flex-1 space-y-5 w-full">
          {/* Plain Farmer Language Box */}
          <div className="rounded-2xl border border-emerald-200 bg-white p-5 shadow-sm">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1.5">
              <Sparkles className="size-3.5" />
              <span>What this means for your field</span>
            </span>
            <p className="text-lg font-bold text-foreground mt-1.5 leading-snug">
              Your crop may need about{" "}
              <span className="text-primary underline decoration-emerald-300 decoration-2 underline-offset-4">
                {formatDepth(cwrMmDay)} mm
              </span>{" "}
              of water today.
            </p>
            <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
              Calculated using localized solar energy, humidity, and active root depth. Subtracted from soil reservoir to prevent over-irrigation.
            </p>
          </div>

          {/* Uncertainty Range Bar (Simplified & Farmer-Friendly) */}
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-foreground block">
                  Expected Water Need Range
                </span>
                <span className="text-[11px] text-muted-foreground">
                  Likely daily variation due to weather fluctuations
                </span>
              </div>
              {nominalCoverage !== null && nominalCoverage !== undefined && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-white border border-emerald-200 text-emerald-800">
                  {formatPercent(nominalCoverage)} confidence band
                </span>
              )}
            </div>

            {expectedMinMm !== null &&
            expectedMinMm !== undefined &&
            expectedMaxMm !== null &&
            expectedMaxMm !== undefined ? (
              <div className="space-y-2">
                <div className="relative pt-3 pb-1">
                  {/* Range Track */}
                  <div className="h-3 w-full rounded-full bg-emerald-200/70 overflow-hidden relative">
                    <div
                      className="absolute top-0 bottom-0 bg-primary/70 rounded-full"
                      style={{
                        left: "20%",
                        width: "60%",
                      }}
                    />
                  </div>
                  {/* Center Dot for Expected Value */}
                  <div
                    className="absolute top-1.5 size-6 rounded-full bg-white border-2 border-primary shadow-md flex items-center justify-center text-[10px] font-bold text-primary"
                    style={{ left: "calc(50% - 12px)" }}
                  >
                    ●
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-muted-foreground">
                    Low: <strong className="text-foreground">{formatDepth(expectedMinMm)} mm</strong>
                  </span>
                  <span className="text-primary font-black">
                    Expected: {formatDepth(cwrMmDay)} mm
                  </span>
                  <span className="text-muted-foreground">
                    High: <strong className="text-foreground">{formatDepth(expectedMaxMm)} mm</strong>
                  </span>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between text-xs pt-1">
                <span className="text-muted-foreground">Expected estimate:</span>
                <span className="font-bold text-foreground">{formatDepth(cwrMmDay)} mm/day</span>
              </div>
            )}
          </div>

          {/* Quick Litres Summary if available */}
          {grossLitres !== null && grossLitres !== undefined && grossLitres > 0 && (
            <div className="rounded-xl border border-sky-200 bg-sky-50/70 p-3.5 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div className="size-8 rounded-lg bg-sky-500 text-white flex items-center justify-center font-bold">
                  <Waves className="size-4" />
                </div>
                <div>
                  <span className="text-[11px] font-bold uppercase text-sky-900 block">
                    Equivalent Pump Delivery
                  </span>
                  <span className="text-xs text-sky-800">
                    Gross volume to distribute across the planted area
                  </span>
                </div>
              </div>
              <span className="text-lg font-black text-sky-900 tabular">
                {Math.round(grossLitres).toLocaleString()} L
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
