"use client";

import Link from "next/link";
import { useState } from "react";
import {
  ArrowRight,
  Beaker,
  ChevronDown,
  ChevronUp,
  CloudRain,
  Droplets,
  Gauge,
  Info,
  Layers,
  Leaf,
  Lightbulb,
  ShieldCheck,
  Sparkles,
  Sprout,
  Tractor,
  Waves,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";
import type { PredictionOut } from "@/lib/api/types";
import {
  formatDate,
  formatDepth,
  formatLitres,
  formatPercent,
  humaniseSlug,
  priorityTone,
  toneBadge,
} from "@/lib/format";
import { WaterGaugeVisual } from "@/components/agro-illustrations/WaterGaugeVisual";
import { CropGrowthTimeline } from "@/components/agro-illustrations/CropGrowthTimeline";
import { IrrigationFlowVisual } from "@/components/agro-illustrations/IrrigationFlowVisual";

interface WaterNeed {
  band?: string;
  description?: string;
  value_mm_day?: number;
  thresholds_mm_day?: Record<string, string>;
  note?: string;
}

interface AdvisoryItem {
  advisory_type?: string;
  headline?: string;
  detail?: string;
  priority?: string;
  action_required?: boolean;
}

export function PredictionResult({
  prediction,
  showExplanationLink = true,
}: {
  prediction: PredictionOut;
  showExplanationLink?: boolean;
}) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const need = (prediction.water_need ?? {}) as WaterNeed;
  const advisories = (prediction.advisories ?? []) as AdvisoryItem[];
  const interval = prediction.interval;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* ---------------- 1. Main Water Need Central Visualization ---------------- */}
      <WaterGaugeVisual
        cwrMmDay={prediction.cwr_mm_day}
        expectedMinMm={interval?.lower_mm_day}
        expectedMaxMm={interval?.upper_mm_day}
        cropName={prediction.crop_name}
        nominalCoverage={interval?.nominal_coverage}
        grossLitres={prediction.gross_irrigation_litres}
      />

      {/* ---------------- 2. Growth Stage Visual Timeline ---------------- */}
      <CropGrowthTimeline
        currentStage={prediction.growth_stage}
        daysAfterSowing={prediction.days_after_sowing}
        cropName={prediction.crop_name}
        cwrMmDay={prediction.cwr_mm_day}
        kcValue={prediction.kc_value}
      />

      {/* ---------------- 3. Irrigation Flow & Water Balance ---------------- */}
      <IrrigationFlowVisual
        cwrMmDay={prediction.cwr_mm_day}
        effectiveRainMm={prediction.effective_rainfall_mm ?? 0}
        netIrrigationMm={prediction.net_irrigation_mm ?? Math.max(0, prediction.cwr_mm_day - (prediction.effective_rainfall_mm ?? 0))}
        grossIrrigationMm={prediction.gross_irrigation_mm}
        grossLitres={prediction.gross_irrigation_litres}
        efficiency={prediction.application_efficiency}
      />

      {/* ---------------- 4. Actionable Farmer Advisory Cards ---------------- */}
      {advisories.length > 0 && (
        <Card className="rounded-3xl border border-emerald-200/90 bg-white p-6 sm:p-7 shadow-xs">
          <div className="flex items-center justify-between pb-4 border-b border-emerald-100 mb-5">
            <div className="flex items-center gap-2.5">
              <div className="size-10 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center font-bold">
                <Lightbulb className="size-5" />
              </div>
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-amber-700">
                  Field Action Plan
                </span>
                <h3 className="text-xl font-black text-foreground">
                  Actionable Farmer Advisories
                </h3>
              </div>
            </div>
            <span className="text-xs text-muted-foreground font-semibold">
              {advisories.length} recommendations generated
            </span>
          </div>

          <div className="space-y-3.5">
            {advisories.map((advisory, index) => {
              const priority = (advisory.priority ?? "medium").toLowerCase();
              const isHigh = priority === "high" || priority === "urgent";
              return (
                <div
                  key={`${advisory.advisory_type ?? "advice"}-${index}`}
                  className={`rounded-2xl border p-4 sm:p-5 transition-all ${
                    isHigh
                      ? "border-amber-300 bg-amber-50/60"
                      : "border-emerald-200/80 bg-emerald-50/30"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3.5">
                      <div
                        className={`size-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
                          isHigh
                            ? "bg-amber-500 text-white font-bold"
                            : "bg-primary text-white"
                        }`}
                      >
                        <Droplets className="size-4.5" />
                      </div>
                      <div>
                        <h4 className="font-bold text-base text-foreground">
                          {advisory.headline}
                        </h4>
                        {advisory.detail && (
                          <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                            {advisory.detail}
                          </p>
                        )}
                      </div>
                    </div>
                    {advisory.priority && (
                      <Badge variant={toneBadge(priorityTone(advisory.priority))} className="shrink-0 text-xs">
                        {advisory.priority}
                      </Badge>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* ---------------- 5. Expandable Academic & Scientific Details (For Panel Members) ---------------- */}
      <Card className="rounded-3xl border border-emerald-200/90 bg-white overflow-hidden shadow-xs">
        <button
          type="button"
          onClick={() => setDetailsOpen(!detailsOpen)}
          className="w-full flex items-center justify-between p-6 text-left hover:bg-emerald-50/50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="size-10 rounded-2xl bg-emerald-100 text-primary flex items-center justify-center font-bold">
              <Beaker className="size-5" />
            </div>
            <div>
              <span className="block text-base sm:text-lg font-black text-foreground">
                View Technical Details &amp; Scientific Lineage
              </span>
              <span className="text-xs text-muted-foreground font-medium">
                FAO-56 reference values, Kc interpolation formula, and ML model metadata for review
              </span>
            </div>
          </div>
          <span className="flex items-center gap-1.5 text-xs font-bold text-primary bg-emerald-100/80 px-3 py-1.5 rounded-xl border border-emerald-300">
            {detailsOpen ? "Hide Technical Details" : "Expand Technical Details"}
            {detailsOpen ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
          </span>
        </button>

        {detailsOpen && (
          <CardContent className="border-t border-emerald-100 pt-6 space-y-6 bg-emerald-50/20 p-6 sm:p-7">
            {/* Scientific Badges */}
            <div className="flex flex-wrap gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-emerald-200 text-xs font-bold text-emerald-950">
                <ShieldCheck className="size-3.5 text-emerald-600" />
                Physics-Guided Prediction
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-emerald-200 text-xs font-bold text-emerald-950">
                <Sprout className="size-3.5 text-emerald-600" />
                Growth-Stage Aware (FAO-56)
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-emerald-200 text-xs font-bold text-emerald-950">
                <Waves className="size-3.5 text-sky-600" />
                Rainfall-Aware Irrigation
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-emerald-200 text-xs font-bold text-emerald-950">
                <Droplets className="size-3.5 text-blue-600" />
                Uncertainty-Aware Water Estimation
              </span>
            </div>

            {/* Core Agronomic Metrics Grid */}
            <div className="grid gap-3.5 sm:grid-cols-3">
              <div className="p-4 rounded-2xl border border-emerald-200 bg-white shadow-xs">
                <span className="text-xs text-muted-foreground font-semibold block">
                  Reference Evapotranspiration (ET₀)
                </span>
                <span className="text-2xl font-black text-foreground tabular mt-1 block">
                  {formatDepth(prediction.et0_mm_day)} mm/day
                </span>
                <span className="text-[11px] text-muted-foreground mt-1 block">
                  FAO Penman-Monteith grass reference
                </span>
              </div>

              <div className="p-4 rounded-2xl border border-emerald-200 bg-white shadow-xs">
                <span className="text-xs text-muted-foreground font-semibold block">
                  Interpolated Crop Coefficient (Kc)
                </span>
                <span className="text-2xl font-black text-foreground tabular mt-1 block">
                  {prediction.kc_value.toFixed(4)}
                </span>
                <span className="text-[11px] text-muted-foreground mt-1 block">
                  Linear interpolation for {humaniseSlug(prediction.growth_stage)}
                </span>
              </div>

              <div className="p-4 rounded-2xl border border-emerald-200 bg-white shadow-xs">
                <span className="text-xs text-muted-foreground font-semibold block">
                  Agronomic Baseline ETc
                </span>
                <span className="text-2xl font-black text-foreground tabular mt-1 block">
                  {formatDepth(prediction.cwr_baseline_mm_day)} mm/day
                </span>
                <span className="text-[11px] text-muted-foreground mt-1 block">
                  ETc = Kc × ET₀ reference baseline
                </span>
              </div>
            </div>

            {/* Model & Source Information */}
            <div className="rounded-2xl border border-emerald-200 bg-white p-5 text-sm text-muted-foreground space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-foreground">Model Lineage &amp; Uncertainty</span>
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                  {prediction.prediction_source === "ml_model" ? "ML Model + FAO Baseline" : "Physical Agricultural Baseline"}
                </span>
              </div>
              {interval && interval.lower_mm_day !== null && interval.upper_mm_day !== null && (
                <p className="text-xs leading-relaxed pt-1">
                  Expected uncertainty interval: <strong>{formatDepth(interval.lower_mm_day)}–{formatDepth(interval.upper_mm_day)} mm/day</strong>
                  {interval.nominal_coverage !== null && ` at ${formatPercent(interval.nominal_coverage)} nominal coverage.`}
                  {interval.note ? ` Note: ${interval.note}` : ""}
                </p>
              )}
            </div>

            {/* Formal Equations Reference Box */}
            <div className="p-5 rounded-2xl border border-emerald-200 bg-white text-xs space-y-2.5">
              <h4 className="font-bold text-foreground text-sm">Hydrological Formulas Applied</h4>
              <p className="text-muted-foreground">
                <strong>Crop Water Demand:</strong>{" "}
                <code className="bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded font-mono text-emerald-950">ETc = Kc × ET₀</code>
              </p>
              <p className="text-muted-foreground">
                <strong>Net Irrigation Requirement:</strong>{" "}
                <code className="bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded font-mono text-emerald-950">Inet = max(0, ETc − Peff)</code>{" "}
                where Peff is effective rainfall credited via USDA-SCS method.
              </p>
              <p className="text-muted-foreground">
                <strong>Gross Irrigation to Deliver:</strong>{" "}
                <code className="bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded font-mono text-emerald-950">Igross = Inet / Ea</code>{" "}
                where application efficiency Ea = {formatPercent(prediction.application_efficiency)}.
              </p>
              <p className="text-muted-foreground">
                <strong>Pump Volume in Litres:</strong>{" "}
                <code className="bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded font-mono text-emerald-950">V = Igross × Area(ha) × 10,000 L/mm/ha</code>.
              </p>
            </div>

            {showExplanationLink && prediction.id && (
              <div className="flex justify-end pt-2">
                <Link
                  href={`/predictions/${prediction.id}`}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline"
                >
                  <span>Open Full Feature Lineage &amp; Model Audit Lineage</span>
                  <ArrowRight className="size-3.5" />
                </Link>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    </div>
  );
}
