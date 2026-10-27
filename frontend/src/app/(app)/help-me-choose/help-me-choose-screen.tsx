"use client";

import Link from "next/link";
import { useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Compass,
  Droplets,
  Info,
  MapPin,
  ShieldCheck,
  Sparkles,
  Sprout,
  Waves,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";
import { LoadingState } from "@/components/ui/states";
import { Notice } from "@/components/ui/notice";
import { api } from "@/lib/api/client";
import { humanMessage } from "@/lib/api/errors";
import type { CropRecommendationOut } from "@/lib/api/types";
import { formatDepth, formatPercent } from "@/lib/format";

// Real Karnataka District Benchmarks from datasets/processed/
interface DistrictProfile {
  name: string;
  rainfall_mm: number;
  n: number;
  p: number;
  k: number;
  ph: number;
  temp_c: number;
  humidity_pct: number;
}

const DISTRICT_PROFILES: Record<string, DistrictProfile> = {
  Mandya: { name: "Mandya", rainfall_mm: 655, n: 65, p: 48, k: 52, ph: 6.8, temp_c: 28.5, humidity_pct: 65 },
  "Bengaluru Rural": { name: "Bengaluru Rural", rainfall_mm: 751, n: 58, p: 42, k: 45, ph: 6.5, temp_c: 26.5, humidity_pct: 68 },
  "Bengaluru Urban": { name: "Bengaluru Urban", rainfall_mm: 751, n: 55, p: 40, k: 44, ph: 6.4, temp_c: 26.0, humidity_pct: 67 },
  Belagavi: { name: "Belagavi", rainfall_mm: 844, n: 72, p: 55, k: 60, ph: 7.2, temp_c: 27.0, humidity_pct: 70 },
  Mysuru: { name: "Mysuru", rainfall_mm: 739, n: 62, p: 45, k: 48, ph: 6.7, temp_c: 27.5, humidity_pct: 66 },
  Shivamogga: { name: "Shivamogga", rainfall_mm: 2682, n: 50, p: 35, k: 40, ph: 6.2, temp_c: 25.5, humidity_pct: 82 },
  Dharwad: { name: "Dharwad", rainfall_mm: 787, n: 68, p: 52, k: 56, ph: 7.4, temp_c: 28.0, humidity_pct: 64 },
  Ballari: { name: "Ballari", rainfall_mm: 606, n: 75, p: 50, k: 65, ph: 7.8, temp_c: 31.0, humidity_pct: 55 },
  Chitradurga: { name: "Chitradurga", rainfall_mm: 507, n: 60, p: 40, k: 50, ph: 7.5, temp_c: 29.5, humidity_pct: 58 },
  Raichur: { name: "Raichur", rainfall_mm: 658, n: 70, p: 48, k: 62, ph: 7.9, temp_c: 32.0, humidity_pct: 54 },
  Tumakuru: { name: "Tumakuru", rainfall_mm: 589, n: 56, p: 38, k: 46, ph: 6.6, temp_c: 28.0, humidity_pct: 62 },
  Hassan: { name: "Hassan", rainfall_mm: 1147, n: 52, p: 36, k: 42, ph: 6.3, temp_c: 25.0, humidity_pct: 75 },
  Kalaburagi: { name: "Kalaburagi", rainfall_mm: 842, n: 74, p: 54, k: 58, ph: 7.8, temp_c: 31.5, humidity_pct: 58 },
};

const KANADA_NAMES: Record<string, string> = {
  paddy: "ಭತ್ತ",
  rice: "ಭತ್ತ",
  maize: "ಮೆಕ್ಕೆಜೋಳ",
  wheat: "ಗೋಧಿ",
  finger_millet: "ರಾಗಿ",
  ragi: "ರಾಗಿ",
  groundnut: "ಕಡಲೆಕಾಯಿ",
  cotton: "ಹತ್ತಿ",
  chickpea: "ಕಡಲೆ",
  cumin: "ಜೀರಿಗೆ",
  sugarcane: "ಕಬ್ಬು",
  arecanut: "ಅಡಿಕೆ",
  coffee: "ಕಾಫಿ",
};

export function HelpMeChooseScreen() {
  const [selectedDistrict, setSelectedDistrict] = useState("Mandya");
  const [categoryFilter, setCategoryFilter] = useState<"all" | "seasonal" | "perennial">("all");
  const [season, setSeason] = useState<"kharif" | "rabi" | "summer" | "annual">("kharif");
  const [waterCapacity, setWaterCapacity] = useState<"assured" | "moderate" | "rainfed">("moderate");

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CropRecommendationOut | null>(null);

  const district = DISTRICT_PROFILES[selectedDistrict] || DISTRICT_PROFILES["Mandya"];

  // Available water mm corresponding to capacity level
  const availableWaterMm =
    waterCapacity === "assured" ? 900 : waterCapacity === "moderate" ? 450 : 250;

  async function handleEvaluate() {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<CropRecommendationOut>("recommendations/crops", {
        nitrogen: district.n,
        phosphorus: district.p,
        potassium: district.k,
        ph: district.ph,
        temperature_c: district.temp_c,
        humidity_pct: district.humidity_pct,
        rainfall_mm: district.rainfall_mm / 4, // Seasonal allocation
        available_water_mm: availableWaterMm,
        top_n: 10,
      });
      setResult(response);
    } catch (err) {
      setError(humanMessage(err));
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  }

  // Filter recommendations by Seasonal vs Perennial
  const filteredRecs = (result?.recommendations ?? []).filter((item) => {
    const isPerennial = ["cotton", "mango", "banana", "apple", "orange", "papaya", "coconut"].includes(
      item.crop.toLowerCase(),
    );
    if (categoryFilter === "seasonal") return !isPerennial;
    if (categoryFilter === "perennial") return isPerennial;
    return true;
  });

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* ---------------- Header ---------------- */}
      <header className="pb-4 border-b border-emerald-200">
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-100 border border-amber-300 text-amber-900 font-bold uppercase tracking-wider">
            Pathway 2 · ಬೆಳೆ ಆಯ್ಕೆ ಮಾರ್ಗದರ್ಶಕ
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-foreground mt-1">
          “HELP ME CHOOSE” — Regional Crop &amp; Water Suitability
        </h1>
        <p className="mt-1 text-sm text-muted-foreground max-w-3xl">
          Evidence-based candidate crops using actual Karnataka soil nutrients, IMD rainfall normals, and transparent water feasibility trade-offs. No unsupported &quot;best crop&quot; promises.
        </p>
      </header>

      {/* ---------------- 1. Location-First District & Soil Context ---------------- */}
      <Card className="border border-emerald-200/90 bg-white rounded-3xl shadow-xs overflow-hidden">
        <SectionHeader
          title="1. Where is your farm? (Location, Soil & Climate)"
          description="Select your Karnataka district to pull verified soil nutrients and historical rainfall averages."
        />
        <CardContent className="space-y-6 p-6 sm:p-7">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-1.5 sm:col-span-2">
              <label htmlFor="district-choice" className="text-sm font-bold text-foreground flex items-center gap-1.5">
                <MapPin className="size-4 text-primary" />
                <span>Karnataka District</span>
              </label>
              <select
                id="district-choice"
                value={selectedDistrict}
                onChange={(e) => {
                  setSelectedDistrict(e.target.value);
                  setResult(null);
                }}
                className="w-full h-11 rounded-xl border border-emerald-200 bg-white px-3.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-primary"
              >
                {Object.keys(DISTRICT_PROFILES).map((d) => (
                  <option key={d} value={d}>
                    {d} District
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="season-choice" className="text-sm font-bold text-foreground">
                Target Season
              </label>
              <select
                id="season-choice"
                value={season}
                onChange={(e) => setSeason(e.target.value as "kharif" | "rabi" | "summer" | "annual")}
                className="w-full h-11 rounded-xl border border-emerald-200 bg-white px-3.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-primary"
              >
                <option value="kharif">Kharif (Monsoon: Jun-Oct)</option>
                <option value="rabi">Rabi (Winter: Oct-Mar)</option>
                <option value="summer">Summer (Mar-Jun)</option>
                <option value="annual">Year-Round / Perennial</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="water-capacity" className="text-sm font-bold text-foreground">
                Irrigation Supply
              </label>
              <select
                id="water-capacity"
                value={waterCapacity}
                onChange={(e) => setWaterCapacity(e.target.value as "assured" | "moderate" | "rainfed")}
                className="w-full h-11 rounded-xl border border-emerald-200 bg-white px-3.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-primary"
              >
                <option value="assured">Assured (Canal / High Borewell &gt;600mm)</option>
                <option value="moderate">Moderate (Standard Borewell ~450mm)</option>
                <option value="rainfed">Scarce / Rainfed (~250mm)</option>
              </select>
            </div>
          </div>

          {/* Regional Soil and Climate Snapshot from project datasets */}
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-4 space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
              <Sparkles className="size-3.5 text-primary" />
              <span>Project Dataset Normals for {district.name}</span>
            </span>

            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5 text-xs pt-1">
              <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-xs">
                <span className="text-muted-foreground block text-[11px]">Normal Rain</span>
                <strong className="text-foreground text-sm font-bold">{district.rainfall_mm} mm/yr</strong>
              </div>
              <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-xs">
                <span className="text-muted-foreground block text-[11px]">Soil Nitrogen</span>
                <strong className="text-foreground text-sm font-bold">{district.n} kg/ha</strong>
              </div>
              <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-xs">
                <span className="text-muted-foreground block text-[11px]">Phosphorus</span>
                <strong className="text-foreground text-sm font-bold">{district.p} kg/ha</strong>
              </div>
              <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-xs">
                <span className="text-muted-foreground block text-[11px]">Potassium</span>
                <strong className="text-foreground text-sm font-bold">{district.k} kg/ha</strong>
              </div>
              <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-xs">
                <span className="text-muted-foreground block text-[11px]">Soil pH</span>
                <strong className="text-foreground text-sm font-bold">{district.ph}</strong>
              </div>
              <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-xs">
                <span className="text-muted-foreground block text-[11px]">Mean Temp</span>
                <strong className="text-foreground text-sm font-bold">{district.temp_c} °C</strong>
              </div>
              <div className="bg-white p-3 rounded-xl border border-emerald-100 shadow-xs">
                <span className="text-muted-foreground block text-[11px]">Humidity</span>
                <strong className="text-foreground text-sm font-bold">{district.humidity_pct}%</strong>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-1">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Info className="size-4 text-primary shrink-0" />
              <span>
                Available water cap set to <strong className="text-foreground font-bold">{availableWaterMm} mm</strong> for feasibility assessment.
              </span>
            </div>

            <Button
              type="button"
              size="lg"
              onClick={handleEvaluate}
              loading={isLoading}
              loadingText="Analyzing Regional Suitability…"
              className="w-full sm:w-auto font-bold flex items-center gap-2 bg-primary hover:bg-emerald-800 text-white rounded-xl shadow-md"
            >
              <Compass className="size-4" />
              <span>Evaluate Candidate Crops &rarr;</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ---------------- 2. Evaluation Results ---------------- */}
      {error && (
        <Notice tone="danger" title="Could not evaluate crops">
          {error}
        </Notice>
      )}

      {isLoading && <LoadingState label="Fitting Random Forest model on 2,200 regional suitability records…" />}

      {result && (
        <div className="space-y-6">
          {/* Category Filter Tabs */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-muted-foreground uppercase">Filter Category:</span>
              <div className="inline-flex rounded-xl border border-emerald-200 bg-emerald-50/60 p-1 text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setCategoryFilter("all")}
                  className={`px-3 py-1.5 rounded-lg transition-colors ${
                    categoryFilter === "all" ? "bg-white text-emerald-950 font-bold shadow-xs" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  All ({result.recommendations.length})
                </button>
                <button
                  type="button"
                  onClick={() => setCategoryFilter("seasonal")}
                  className={`px-3 py-1.5 rounded-lg transition-colors ${
                    categoryFilter === "seasonal" ? "bg-white text-emerald-950 font-bold shadow-xs" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Seasonal / Short-term
                </button>
                <button
                  type="button"
                  onClick={() => setCategoryFilter("perennial")}
                  className={`px-3 py-1.5 rounded-lg transition-colors ${
                    categoryFilter === "perennial" ? "bg-white text-emerald-950 font-bold shadow-xs" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Perennial / Long-term
                </button>
              </div>
            </div>

            <span className="text-xs font-semibold text-emerald-800">
              Showing {filteredRecs.length} candidate crops for {district.name}
            </span>
          </div>

          {/* Candidate Crop Cards */}
          <div className="space-y-4">
            {filteredRecs.map((item) => {
              const kannada = KANADA_NAMES[item.crop.toLowerCase()] || "";
              const hasCwr = item.estimated_season_demand_mm !== null;
              const isFeasible = item.water_feasible === true;
              const hasDeficit = item.water_feasible === false;

              return (
                <div
                  key={item.crop}
                  className={`rounded-3xl border-2 p-6 bg-white transition-all ${
                    isFeasible
                      ? "border-emerald-300 hover:border-primary shadow-xs"
                      : hasDeficit
                      ? "border-amber-300 hover:border-amber-500 bg-amber-50/20"
                      : "border-emerald-100 hover:border-emerald-200"
                  }`}
                >
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    {/* Crop Title & Suitability */}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                          Rank #{item.suitability_rank}
                        </span>
                        <h3 className="text-xl font-black text-foreground capitalize">
                          {item.crop}
                        </h3>
                        {kannada && (
                          <span className="text-xs font-bold text-primary px-2 py-0.5 rounded-full bg-primary/10">
                            {kannada}
                          </span>
                        )}
                        {hasCwr ? (
                          <Badge variant="ok">CWR Active</Badge>
                        ) : (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300">
                            UNDER DEVELOPMENT
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-muted-foreground">
                        Agronomic Suitability: <strong className="text-foreground font-bold">{formatPercent(item.suitability_score)}</strong> match with {district.name} soil &amp; climate.
                      </p>
                    </div>

                    {/* Water Feasibility Status Badge */}
                    <div className="flex flex-wrap items-center gap-3">
                      {hasCwr ? (
                        <div className="text-left sm:text-right">
                          <span className="text-xs text-muted-foreground block">
                            Seasonal Water Need
                          </span>
                          <span className="text-base font-black text-foreground tabular">
                            ~{formatDepth(item.estimated_season_demand_mm)} mm
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground italic">
                          Water demand under calibration
                        </span>
                      )}

                      <div className="h-8 w-px bg-emerald-100 hidden sm:block" />

                      {isFeasible ? (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-100 text-emerald-800 text-xs font-bold border border-emerald-300">
                          <CheckCircle2 className="size-4 text-primary" />
                          <span>Water Feasible</span>
                        </div>
                      ) : hasDeficit ? (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-100 text-amber-900 text-xs font-bold border border-amber-300">
                          <AlertTriangle className="size-4 text-amber-600" />
                          <span>Water Shortfall ({formatDepth(Math.abs(item.water_balance_mm ?? 0))} mm)</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-muted text-muted-foreground text-xs font-semibold">
                          <Info className="size-4" />
                          <span>No Curve in Database</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Reasons & Caveats */}
                  <div className="mt-4 pt-3.5 border-t border-emerald-100 grid gap-3 sm:grid-cols-2 text-xs">
                    <div>
                      <strong className="text-foreground block mb-1 font-bold">Agronomic Evidence:</strong>
                      <ul className="space-y-0.5 text-muted-foreground list-disc list-inside">
                        {item.reasons.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <strong className="text-foreground block mb-1 font-bold">Transparent Limitations:</strong>
                      <ul className="space-y-0.5 text-muted-foreground list-disc list-inside">
                        {item.caveats.map((c, i) => (
                          <li key={i}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Action Link if Supported */}
                  {hasCwr && (
                    <div className="mt-3.5 pt-2 flex justify-end">
                      <Link
                        href={`/predict`}
                        className="inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline"
                      >
                        <span>Calculate Daily Stage Schedule for this Crop</span>
                        <ArrowRight className="size-3.5" />
                      </Link>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Research Transparency Box */}
          <div className="rounded-3xl border border-emerald-200 bg-white p-6 text-xs text-muted-foreground space-y-2.5 shadow-xs">
            <h4 className="font-bold text-foreground text-sm flex items-center gap-2">
              <ShieldCheck className="size-4 text-primary" />
              <span>Academic Transparency &amp; Modeling Disclosure</span>
            </h4>
            <p className="leading-relaxed">
              Candidate rankings are generated by a multi-class Random Forest classifier trained on 2,200 ICAR/UAS regional suitability samples. Water feasibility compares seasonal demand against your declared supply ({availableWaterMm} mm).
            </p>
            <p className="leading-relaxed">
              Crops marked <strong>UNDER DEVELOPMENT</strong> belong to the broader suitability training set but do not yet possess calibrated FAO-56 four-stage crop coefficient curves ($K_c$). Jalachakra explicitly marks these crops to prevent fabricated agricultural advice.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
