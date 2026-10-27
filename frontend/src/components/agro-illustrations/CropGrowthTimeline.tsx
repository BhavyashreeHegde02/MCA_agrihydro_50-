"use client";

import { CheckCircle2, ChevronRight, Droplets, Leaf, Sprout } from "lucide-react";
import { humaniseSlug } from "@/lib/format";

interface GrowthTimelineProps {
  currentStage: string;
  daysAfterSowing?: number | null;
  cropName?: string;
  cwrMmDay?: number | null;
  kcValue?: number | null;
  className?: string;
}

interface StageInfo {
  key: string;
  name: string;
  kannada: string;
  icon: string;
  desc: string;
  kcHint: string;
}

const STAGES: StageInfo[] = [
  {
    key: "initial",
    name: "Seedling / Initial",
    kannada: "ಮೊಳಕೆ ಹಂತ",
    icon: "🌱",
    desc: "Early germination & shallow root establishment.",
    kcHint: "Low water demand (Kc ~0.4 - 0.7)",
  },
  {
    key: "development",
    name: "Vegetative / Growth",
    kannada: "ಬೆಳವಣಿಗೆ ಹಂತ",
    icon: "🌿",
    desc: "Rapid leaf canopy expansion & active tiller formation.",
    kcHint: "Rising water demand (Kc ~0.7 - 1.0)",
  },
  {
    key: "mid_season",
    name: "Flowering / Mid-Season",
    kannada: "ಹೂವು & ಕಾಳು ಕಟ್ಟುವ ಹಂತ",
    icon: "🌼",
    desc: "Peak moisture sensitivity. High transpiration rate.",
    kcHint: "Peak demand (Kc ~1.05 - 1.25)",
  },
  {
    key: "late_season",
    name: "Maturity / Ripening",
    kannada: "ಕೊಯ್ಲು ಹಂತ",
    icon: "🌾",
    desc: "Grain filling, yellowing of foliage, pre-harvest dry down.",
    kcHint: "Tapering demand (Kc ~0.5 - 0.8)",
  },
];

function normalizeStage(stage: string): string {
  const s = stage.toLowerCase();
  if (s.includes("init") || s.includes("seed")) return "initial";
  if (s.includes("dev") || s.includes("veg")) return "development";
  if (s.includes("mid") || s.includes("flower") || s.includes("boot")) return "mid_season";
  if (s.includes("late") || s.includes("matur") || s.includes("harvest")) return "late_season";
  return "development";
}

export function CropGrowthTimeline({
  currentStage,
  daysAfterSowing,
  cropName = "Crop",
  cwrMmDay,
  kcValue,
  className = "",
}: GrowthTimelineProps) {
  const normalizedCurrent = normalizeStage(currentStage);
  const activeStageIndex = STAGES.findIndex((st) => st.key === normalizedCurrent);
  const currentIndex = activeStageIndex >= 0 ? activeStageIndex : 1;

  return (
    <div
      className={`rounded-3xl border border-emerald-200/90 bg-white p-6 sm:p-7 shadow-sm ${className}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-emerald-100">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100/80 px-2.5 py-0.5 rounded-full">
            Crop Lifecycle &amp; Kc Timeline
          </span>
          <h3 className="text-xl sm:text-2xl font-extrabold text-foreground mt-1">
            Growth Stage Journey: {cropName}
          </h3>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {daysAfterSowing !== null && daysAfterSowing !== undefined && (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs">
              <span className="text-muted-foreground">Crop Age:</span>{" "}
              <strong className="text-foreground font-black">{daysAfterSowing} Days</strong>
            </div>
          )}
          {kcValue !== null && kcValue !== undefined && (
            <div className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs">
              <span className="text-muted-foreground">Interpolated Kc:</span>{" "}
              <strong className="text-blue-900 font-black">{kcValue.toFixed(2)}</strong>
            </div>
          )}
        </div>
      </div>

      {/* Visual Timeline Steps */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-6">
        {STAGES.map((stage, idx) => {
          const isCurrent = idx === currentIndex;
          const isPassed = idx < currentIndex;

          return (
            <div
              key={stage.key}
              className={`relative rounded-2xl p-4 transition-all border ${
                isCurrent
                  ? "border-primary bg-gradient-to-b from-emerald-50/90 to-white shadow-md ring-2 ring-emerald-300"
                  : isPassed
                  ? "border-emerald-200 bg-emerald-50/40 text-muted-foreground"
                  : "border-emerald-100 bg-slate-50/50 text-muted-foreground opacity-75"
              }`}
            >
              {isCurrent && (
                <div className="absolute -top-2.5 left-4 bg-primary text-white text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full shadow-sm">
                  Active Stage
                </div>
              )}

              <div className="flex items-start justify-between mb-2">
                <span className="text-3xl" role="img" aria-label={stage.name}>
                  {stage.icon}
                </span>
                <span className="text-xs font-bold text-muted-foreground">
                  {stage.kannada}
                </span>
              </div>

              <h4 className="font-bold text-base text-foreground">
                {stage.name}
              </h4>

              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                {stage.desc}
              </p>

              <div className="mt-3 pt-2.5 border-t border-emerald-100 text-[11px] font-semibold text-emerald-800 flex items-center gap-1">
                <Droplets className="size-3 text-emerald-600 shrink-0" />
                <span>{stage.kcHint}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Current Stage Highlight Banner */}
      <div className="mt-6 rounded-2xl border border-primary/30 bg-gradient-to-r from-emerald-100/60 via-emerald-50/80 to-white p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="size-10 rounded-xl bg-primary text-white flex items-center justify-center font-bold shadow-sm">
            <Sprout className="size-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">
              Current Field Stage: <strong className="text-foreground font-bold">{humaniseSlug(currentStage)}</strong>
            </p>
            <p className="text-sm font-bold text-emerald-950">
              Crop is actively transpiring. Kc factor is dynamically adjusted for daily weather.
            </p>
          </div>
        </div>

        {cwrMmDay !== null && cwrMmDay !== undefined && (
          <div className="text-right shrink-0">
            <span className="text-[11px] text-muted-foreground block">Stage Water Demand</span>
            <span className="text-lg font-black text-primary tabular">{cwrMmDay.toFixed(1)} mm/day</span>
          </div>
        )}
      </div>
    </div>
  );
}
