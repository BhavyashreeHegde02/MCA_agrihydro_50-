"use client";

import { useState } from "react";
import Link from "next/link";
import { AlertCircle, ArrowRight, Sprout } from "lucide-react";

import { KcCurveChart } from "@/components/charts/water-charts";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Notice } from "@/components/ui/notice";
import { SectionHeader } from "@/components/ui/section-header";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { humanMessage } from "@/lib/api/errors";
import {
  useAllPlantings,
  useCrop,
  useCrops,
  useGrowthStages,
  useKcCurve,
} from "@/lib/api/queries";
import { cn } from "@/lib/utils";
import { humaniseSlug } from "@/lib/format";

const KANNADA_NAMES: Record<string, string> = {
  paddy: "ಭತ್ತ",
  maize: "ಮೆಕ್ಕೆಜೋಳ",
  wheat: "ಗೋಧಿ",
  finger_millet: "ರಾಗಿ",
  groundnut: "ಕಡಲೆಕಾಯಿ",
  cotton: "ಹತ್ತಿ",
  chickpea: "ಕಡಲೆ",
  cumin: "ಜೀರಿಗೆ",
};

const UNSUPPORTED_CROPS = [
  { name: "Sugarcane", kannada: "ಕಬ್ಬು", category: "Perennial / Long-term", reason: "12-18 month cycle; multi-station lysimeter calibration in progress" },
  { name: "Arecanut", kannada: "ಅಡಿಕೆ", category: "Perennial / Long-term", reason: "Canopy shade coefficient modeling under development" },
  { name: "Coffee (Arabica / Robusta)", kannada: "ಕಾಫಿ", category: "Perennial / Long-term", reason: "Western Ghats microclimate transpiration baseline pending" },
  { name: "Pomegranate", kannada: "ದಾಳಿಂಬೆ", category: "Perennial / Long-term", reason: "Bahar treatment water stress stages under development" },
];

export function CropsScreen() {
  const crops = useCrops();
  const plantings = useAllPlantings(true);
  const [chosenCropId, setChosenCropId] = useState<number | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<"all" | "seasonal" | "perennial">("all");

  const selectedId = chosenCropId ?? crops.data?.[0]?.id ?? 0;
  const detail = useCrop(selectedId);
  const stages = useGrowthStages(selectedId);
  const curve = useKcCurve(selectedId);

  const planting = plantings.data?.find(
    (candidate) => candidate.crop_id === selectedId,
  );

  // Filter crops by category
  const filteredCrops = (crops.data ?? []).filter((crop) => {
    const isPerennial = crop.slug === "cotton";
    if (categoryFilter === "seasonal") return !isPerennial;
    if (categoryFilter === "perennial") return isPerennial;
    return true;
  });

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      <header className="pb-4 border-b border-emerald-200">
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold uppercase tracking-wider">
            FAO-56 Agronomic Reference · ಬೆಳೆ ಮಾರ್ಗದರ್ಶಿ
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-foreground mt-1">
          Crop Reference &amp; Growth-Stage Curves
        </h1>
        <p className="mt-1 text-sm text-muted-foreground max-w-2xl">
          Stage-by-stage crop coefficient curves ($K_c$) calibrated for Karnataka agroclimatic zones. Unsupported crops are declared under development to preserve research integrity.
        </p>
      </header>

      {/* Category Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="inline-flex rounded-xl border border-emerald-200 bg-emerald-50/60 p-1 text-xs font-semibold">
          <button
            type="button"
            onClick={() => setCategoryFilter("all")}
            className={`px-3.5 py-1.5 rounded-lg transition-colors ${
              categoryFilter === "all" ? "bg-white text-emerald-950 font-bold shadow-xs" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            All Calibrated Crops ({crops.data?.length ?? 8})
          </button>
          <button
            type="button"
            onClick={() => setCategoryFilter("seasonal")}
            className={`px-3.5 py-1.5 rounded-lg transition-colors ${
              categoryFilter === "seasonal" ? "bg-white text-emerald-950 font-bold shadow-xs" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Seasonal / Short-term (7)
          </button>
          <button
            type="button"
            onClick={() => setCategoryFilter("perennial")}
            className={`px-3.5 py-1.5 rounded-lg transition-colors ${
              categoryFilter === "perennial" ? "bg-white text-emerald-950 font-bold shadow-xs" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Perennial / Long-term (1)
          </button>
        </div>

        <Link
          href="/predict"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline"
        >
          <span>Use in Calculation Wizard &rarr;</span>
        </Link>
      </div>

      {crops.isPending && <LoadingState label="Loading calibrated crops…" />}

      {crops.isError && (
        <ErrorState
          message={humanMessage(crops.error)}
          onRetry={() => crops.refetch()}
        />
      )}

      {crops.isSuccess && crops.data.length === 0 && (
        <Card className="rounded-3xl border border-emerald-200">
          <CardContent className="p-8">
            <EmptyState
              icon={Sprout}
              title="No crops in the reference"
              description="The crop reference is seeded when the backend starts. If this is empty, seeding did not run."
            />
          </CardContent>
        </Card>
      )}

      {crops.isSuccess && crops.data.length > 0 && (
        <>
          {/* Crop Selection Pill Buttons */}
          <div
            role="tablist"
            aria-label="Crops"
            className="flex flex-wrap gap-2"
          >
            {filteredCrops.map((crop) => {
              const active = crop.id === selectedId;
              const kannada = KANNADA_NAMES[crop.slug] || "";
              return (
                <button
                  key={crop.id}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => setChosenCropId(crop.id)}
                  className={cn(
                    "h-11 rounded-2xl border px-4 text-sm font-bold transition-all flex items-center gap-2",
                    active
                      ? "border-primary bg-primary text-white shadow-md shadow-emerald-950/10"
                      : "border-emerald-200 bg-white text-emerald-950 hover:bg-emerald-50",
                  )}
                >
                  <span>{crop.name}</span>
                  {kannada && (
                    <span className={cn(
                      "text-xs px-2 py-0.5 rounded-full font-medium",
                      active ? "bg-white/20 text-white" : "bg-emerald-100 text-emerald-800"
                    )}>
                      {kannada}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {detail.isError && (
            <ErrorState
              message={humanMessage(detail.error)}
              onRetry={() => detail.refetch()}
            />
          )}

          {detail.isSuccess && (
            <Card className="border border-emerald-200/90 bg-white rounded-3xl shadow-xs overflow-hidden">
              <SectionHeader
                title={`${detail.data.name} ${KANNADA_NAMES[detail.data.slug] ? `(${KANNADA_NAMES[detail.data.slug]})` : ""}`}
                description={`${detail.data.cycle_length_days} day total cycle · ${detail.data.category ? humaniseSlug(detail.data.category) : "Crop"}`}
                action={
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="ok">Active CWR Model</Badge>
                    {planting && (
                      <Badge variant="info">
                        Active in {planting.field_name} · Day {planting.days_after_sowing}
                      </Badge>
                    )}
                  </div>
                }
              />
              <CardContent className="space-y-6 pt-4 p-6 sm:p-7">
                {curve.isPending && <LoadingState label="Loading continuous Kc curve…" />}

                {curve.isSuccess && curve.data.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span className="font-bold text-foreground">
                        FAO-56 Daily Crop Coefficient ($K_c$) Timeline
                      </span>
                      <span>Continuous interpolation across development stages</span>
                    </div>
                    <KcCurveChart
                      points={curve.data}
                      cropName={detail.data.name}
                      currentDay={planting?.days_after_sowing}
                    />
                  </div>
                )}

                {stages.isSuccess && stages.data.length > 0 && (
                  <div className="overflow-x-auto rounded-2xl border border-emerald-100">
                    <table className="w-full text-sm">
                      <caption className="p-3 text-left text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50/50">
                        The 4 Canonical FAO-56 Growth Stages
                      </caption>
                      <thead className="border-b border-emerald-100 bg-emerald-50/80 text-left text-xs tracking-wide text-emerald-950 font-bold uppercase">
                        <tr>
                          <th scope="col" className="px-3.5 py-2.5 font-bold">Growth Stage</th>
                          <th scope="col" className="px-3.5 py-2.5 text-right font-bold">Days After Sowing</th>
                          <th scope="col" className="px-3.5 py-2.5 text-right font-bold">Anchor Kc</th>
                          <th scope="col" className="px-3.5 py-2.5 font-bold">Agronomic Basis</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-emerald-100">
                        {stages.data.map((stage) => {
                          const current =
                            planting !== undefined &&
                            planting.days_after_sowing >= stage.start_day &&
                            planting.days_after_sowing <= stage.end_day;
                          return (
                            <tr
                              key={stage.id}
                              className={cn(current && "bg-emerald-50/70 font-semibold")}
                            >
                              <td className="px-3.5 py-2.5 text-foreground flex items-center gap-2">
                                <span>{humaniseSlug(stage.stage_name)}</span>
                                {current && (
                                  <span className="text-[10px] px-2 py-0.2 rounded-full bg-primary text-white font-bold">
                                    Current
                                  </span>
                                )}
                              </td>
                              <td className="tabular px-3.5 py-2.5 text-right text-muted-foreground">
                                Days {stage.start_day}–{stage.end_day}
                              </td>
                              <td className="tabular px-3.5 py-2.5 text-right font-bold text-foreground">
                                {stage.kc_value !== null && stage.kc_value !== undefined
                                  ? stage.kc_value.toFixed(2)
                                  : "Interpolated"}
                              </td>
                              <td className="px-3.5 py-2.5 text-xs text-muted-foreground">
                                {stage.kc_basis ?? "—"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}

                <Notice tone="info" title="What Kc means in simple farmer terms">
                  When {detail.data.name} is in its mid-season stage, it transpires about {curve.data?.length ? Math.max(...curve.data.map((p) => p.kc)).toFixed(2) : "1.1"} times what standard grass would transpire on the same day. Multiplying reference $ET_0$ by $K_c$ produces today&apos;s crop water need ($ET_c$).
                </Notice>

                {detail.data.reference_source && (
                  <p className="text-xs text-muted-foreground">
                    Research Reference Source: <strong>{detail.data.reference_source}</strong>
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Unsupported Crops Section */}
          <div className="rounded-3xl border border-dashed border-amber-300 bg-amber-50/30 p-6 space-y-4">
            <div className="flex items-center gap-2.5">
              <AlertCircle className="size-5 text-amber-600 shrink-0" />
              <div>
                <h3 className="font-bold text-base text-foreground">
                  Crops Currently Under Research Development
                </h3>
                <p className="text-xs text-muted-foreground">
                  The following crops are grown in Karnataka but do not yet have published lysimeter-validated four-stage curves in our dataset. Jalachakra displays &quot;UNDER DEVELOPMENT&quot; rather than generating fake or fabricated estimates.
                </p>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 pt-1">
              {UNSUPPORTED_CROPS.map((uc) => (
                <div key={uc.name} className="p-4 rounded-2xl border border-amber-200 bg-white space-y-1.5 shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-foreground">{uc.name}</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                      UNDER DEV
                    </span>
                  </div>
                  <span className="text-xs text-primary font-bold block">{uc.kannada}</span>
                  <p className="text-[11px] text-muted-foreground leading-tight">{uc.reason}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
