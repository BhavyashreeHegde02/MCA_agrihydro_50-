import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Clock3,
  CloudRain,
  Compass,
  Droplets,
  History,
  Info,
  Leaf,
  Lightbulb,
  MapPin,
  Plus,
  ShieldCheck,
  Sparkles,
  Sprout,
  Tractor,
  Waves,
  Zap,
} from "lucide-react";

import { rscGet, rscGetOptional } from "@/lib/api/rsc";
import type {
  AdvisoryListResponse,
  AnalyticsDailyPoint,
  AnalyticsOut,
  FarmOut,
  FieldCropDetail,
  PredictionSummary,
  UserOut,
} from "@/lib/api/types";
import { formatArea, formatDate, formatDepth, humaniseSlug } from "@/lib/format";

export const metadata: Metadata = {
  title: "Farmer Dashboard",
  description: "Your Karnataka farm overview, daily crop water demand, and actionable irrigation advice.",
};

export default async function DashboardPage() {
  const [farms, plantings, advisory, history, analytics, farmer] =
    await Promise.all([
      rscGet<FarmOut[]>("/api/v1/farms"),
      rscGet<FieldCropDetail[]>("/api/v1/field-crops", { active_only: true }),
      rscGetOptional<AdvisoryListResponse>("/api/v1/advisory", { limit: 3 }),
      rscGetOptional<PredictionSummary[]>("/api/v1/predictions/history", { limit: 5 }),
      rscGetOptional<AnalyticsOut>("/api/v1/analytics/cwr"),
      rscGet<UserOut>("/api/v1/auth/me"),
    ]);

  const farm = farms[0];
  const planting = plantings[0];
  const latest = history?.[0];
  const latestRain = (analytics?.daily_series as unknown as AnalyticsDailyPoint[] | undefined)
    ?.find((point) => point.date === latest?.prediction_date)?.effective_rainfall_mm;
  const advisories = advisory?.advisories ?? [];
  const area = farms.reduce((total, item) => total + (item.total_area_ha ?? 0), 0);

  // Time-aware greeting
  const greeting = "Good morning";

  return (
    <div className="mx-auto max-w-6xl space-y-8 pb-12">
      {/* ---------------- 1. Storytelling Welcome Banner ---------------- */}
      <section className="relative overflow-hidden rounded-3xl border border-emerald-200/90 bg-gradient-to-r from-emerald-100/70 via-emerald-50/50 to-white p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-white/80 border border-emerald-300 px-3 py-0.5 rounded-full shadow-xs">
                🌾 Farmer Dashboard · ರೈತರ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್
              </span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-foreground tracking-tight">
              {greeting}, {farmer.full_name.split(" ")[0]} 🌱
            </h1>
            <p className="text-base text-emerald-950/80 max-w-xl font-medium">
              &ldquo;Let&apos;s make today&apos;s water decision smarter.&rdquo; Review active plantings, check transpiration demand, and avoid unnecessary pump hours.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 shrink-0">
            <Link
              href="/predict"
              className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-primary hover:bg-emerald-800 text-white font-bold shadow-md shadow-emerald-900/10 transition-all text-sm group"
            >
              <Droplets className="size-4.5" />
              <span>Check Water Need</span>
              <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>
        </div>

        {/* Subtle decorative farm scene horizon curve */}
        <div className="absolute right-0 bottom-0 pointer-events-none opacity-20 -mr-10 -mb-10">
          <svg width="240" height="140" viewBox="0 0 240 140" fill="none">
            <circle cx="120" cy="140" r="100" fill="#2e7d32" />
          </svg>
        </div>
      </section>

      {/* ---------------- 2. Farm Location Snapshot ---------------- */}
      <section aria-labelledby="farm-location-heading" className="rounded-3xl border border-emerald-200/90 bg-white p-6 sm:p-7 shadow-xs">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3.5">
            <div className="size-12 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center shrink-0 shadow-xs">
              <MapPin className="size-6 text-amber-600" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-amber-700">
                Farm Geolocation
              </span>
              <h2 id="farm-location-heading" className="text-xl sm:text-2xl font-black text-foreground mt-0.5">
                {farm ? farm.name : "Where is your farm?"}
              </h2>
              {farm ? (
                <p className="text-sm text-muted-foreground mt-1">
                  <strong className="text-foreground">{farm.district ?? "Karnataka"}</strong>
                  {farm.taluk ? `, ${farm.taluk}` : ""}
                  {area > 0 ? ` · ${formatArea(area)} ha total area` : ""}
                </p>
              ) : (
                <p className="text-sm text-muted-foreground mt-1">
                  Add your farm coordinates to localize IMD rainfall normals, historical ET₀ and soil water capacity.
                </p>
              )}
            </div>
          </div>

          <Link
            href={farm ? `/farms/${farm.id}` : "/farms"}
            className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-emerald-300 bg-emerald-50/50 hover:bg-emerald-100 px-4 py-2.5 text-xs font-bold text-emerald-950 transition-colors shadow-xs shrink-0"
          >
            {farm ? <MapPin className="size-3.5 text-primary" /> : <Plus className="size-3.5 text-primary" />}
            <span>{farm ? "Manage Farm Location" : "Add Farm Location"}</span>
            <ChevronRight className="size-3.5 text-muted-foreground" />
          </Link>
        </div>
      </section>

      {/* ---------------- 3. The Two Core Decision Pathways ---------------- */}
      <section aria-labelledby="journeys-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">
              Guided Workflows
            </span>
            <h2 id="journeys-heading" className="text-xl sm:text-2xl font-black text-foreground mt-0.5">
              Choose Your Agricultural Goal
            </h2>
          </div>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          {/* Journey 1 */}
          <Link
            href="/predict"
            className="group flex min-h-48 flex-col justify-between rounded-3xl border-2 border-emerald-300/80 bg-gradient-to-br from-emerald-50/70 via-white to-emerald-50/40 p-6 transition-all hover:border-primary hover:shadow-md"
          >
            <div>
              <div className="size-11 rounded-2xl bg-primary text-white flex items-center justify-center font-bold mb-3 shadow-xs">
                <Sprout className="size-5" />
              </div>
              <h3 className="text-xl font-black text-foreground">
                🌱 I Know My Crop
              </h3>
              <p className="mt-1.5 text-sm text-muted-foreground leading-relaxed max-w-md">
                Already planted? Select your crop and growth stage to compute exact daily evapotranspiration and irrigation pump litres.
              </p>
            </div>
            <span className="mt-5 inline-flex items-center gap-2 text-xs font-bold text-primary">
              <span>Start Stage-Aware Calculation</span>
              <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-1" />
            </span>
          </Link>

          {/* Journey 2 */}
          <Link
            href="/help-me-choose"
            className="group flex min-h-48 flex-col justify-between rounded-3xl border-2 border-amber-300/80 bg-gradient-to-br from-amber-50/60 via-white to-amber-50/30 p-6 transition-all hover:border-amber-500 hover:shadow-md"
          >
            <div>
              <div className="size-11 rounded-2xl bg-amber-500 text-white flex items-center justify-center font-bold mb-3 shadow-xs">
                <Compass className="size-5" />
              </div>
              <h3 className="text-xl font-black text-foreground">
                🌾 Help Me Choose
              </h3>
              <p className="mt-1.5 text-sm text-muted-foreground leading-relaxed max-w-md">
                Explore candidate crops matching your district&apos;s soil N-P-K, pH, IMD rainfall normals, and available water capacity.
              </p>
            </div>
            <span className="mt-5 inline-flex items-center gap-2 text-xs font-bold text-amber-800">
              <span>Explore Crop Match Candidates</span>
              <ChevronRight className="size-3.5 transition-transform group-hover:translate-x-1" />
            </span>
          </Link>
        </div>
      </section>

      {/* ---------------- 4. Active Planting & Today's Water Status ---------------- */}
      <section aria-labelledby="active-crop-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">
              Field Status
            </span>
            <h2 id="active-crop-heading" className="text-xl sm:text-2xl font-black text-foreground mt-0.5">
              Active Crop &amp; Today&apos;s Water Status
            </h2>
          </div>
          <Link href="/crops" className="text-xs font-bold text-primary hover:underline flex items-center gap-1">
            <span>Crop Guides</span>
            <ArrowRight className="size-3.5" />
          </Link>
        </div>

        {planting ? (
          <div className="rounded-3xl border border-emerald-200/90 bg-white p-6 sm:p-7 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="size-12 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
                  <Sprout className="size-6" />
                </div>
                <div>
                  <h3 className="text-xl font-black text-foreground">
                    {planting.crop_name}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Field: <strong className="text-foreground">{planting.field_name}</strong> · Growth Stage:{" "}
                    <strong className="text-primary">{humaniseSlug(planting.current_stage)}</strong>
                  </p>
                </div>
              </div>

              <Link
                href={`/predict?fieldCropId=${planting.id}`}
                className="inline-flex items-center gap-1.5 text-xs font-bold px-4 py-2 rounded-xl bg-primary text-white hover:bg-emerald-800 transition-colors shadow-xs"
              >
                <Droplets className="size-3.5" />
                <span>Calculate Water Need</span>
              </Link>
            </div>

            {/* Growth Stage Progress Bar */}
            <div className="space-y-2 pt-2 border-t border-emerald-100">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-muted-foreground">Growing Season Progress</span>
                <span className="font-bold text-foreground">
                  Day {planting.days_after_sowing} of {planting.cycle_length_days} ({Math.round(planting.progress_pct)}%)
                </span>
              </div>
              <div className="h-3 w-full rounded-full bg-emerald-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-700"
                  style={{ width: `${Math.min(100, Math.max(5, planting.progress_pct))}%` }}
                />
              </div>
            </div>

            {/* Today's Water Indicators (if latest prediction exists) */}
            {latest ? (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 pt-2">
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-4">
                  <span className="text-[11px] font-bold uppercase text-emerald-900 block">
                    Daily Crop Demand (ETc)
                  </span>
                  <div className="text-2xl font-black text-foreground mt-1 tabular">
                    {formatDepth(latest.cwr_mm_day)}{" "}
                    <span className="text-xs font-bold text-muted-foreground">mm/day</span>
                  </div>
                  <span className="text-[11px] text-muted-foreground block mt-0.5">
                    Transpiration requirement
                  </span>
                </div>

                <div className="rounded-2xl border border-sky-200 bg-sky-50/50 p-4">
                  <span className="text-[11px] font-bold uppercase text-sky-900 block">
                    Rainfall Credited
                  </span>
                  <div className="text-2xl font-black text-sky-700 mt-1 tabular">
                    {latestRain !== undefined ? formatDepth(latestRain) : "0.0"}{" "}
                    <span className="text-xs font-bold text-muted-foreground">mm</span>
                  </div>
                  <span className="text-[11px] text-muted-foreground block mt-0.5">
                    Natural root zone credit
                  </span>
                </div>

                <div className="rounded-2xl border-2 border-primary/40 bg-primary/5 p-4">
                  <span className="text-[11px] font-black uppercase text-primary block">
                    Irrigation to Apply
                  </span>
                  <div className="text-2xl font-black text-primary mt-1 tabular">
                    {formatDepth(latest.gross_irrigation_mm)}{" "}
                    <span className="text-xs font-bold text-primary">mm</span>
                  </div>
                  <span className="text-[11px] text-muted-foreground block mt-0.5">
                    Net deficit divided by system Ea
                  </span>
                </div>
              </div>
            ) : (
              <div className="rounded-2xl bg-emerald-50/80 border border-emerald-200 p-4 text-center">
                <p className="text-xs text-muted-foreground">
                  No prediction calculated for this active planting yet.
                </p>
                <Link
                  href={`/predict?fieldCropId=${planting.id}`}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline mt-1.5"
                >
                  <Droplets className="size-3.5" />
                  <span>Run Today&apos;s Water Prediction</span>
                </Link>
              </div>
            )}

            {/* Expandable Technical Calculation Details */}
            {latest && (
              <details className="pt-2 border-t border-emerald-100 text-xs text-muted-foreground group">
                <summary className="cursor-pointer font-bold text-primary flex items-center justify-between list-none">
                  <span>View Technical Details (ET₀, Kc, Physical Model)</span>
                  <span className="group-open:rotate-180 transition-transform">▼</span>
                </summary>
                <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-emerald-50/40 p-3.5 rounded-xl border border-emerald-100">
                  <div>
                    <span className="text-muted-foreground block">Reference ET₀:</span>
                    <strong className="text-foreground">{formatDepth(latest.et0_mm_day)} mm/day</strong>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Calculation Source:</span>
                    <strong className="text-foreground">{latest.prediction_source === "ml_model" ? "XGBoost + Baseline" : "FAO-56 Baseline"}</strong>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Prediction Date:</span>
                    <strong className="text-foreground">{formatDate(latest.prediction_date)}</strong>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Rainfall Benefit:</span>
                    <strong className="text-foreground">{latestRain !== undefined ? `${formatDepth(latestRain)} mm` : "N/A"}</strong>
                  </div>
                </div>
              </details>
            )}
          </div>
        ) : (
          <div className="rounded-3xl border-2 border-dashed border-emerald-200 bg-white p-8 text-center space-y-3">
            <div className="size-12 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center mx-auto font-bold">
              <Sprout className="size-6" />
            </div>
            <h3 className="text-lg font-bold text-foreground">
              No active planting recorded yet
            </h3>
            <p className="text-xs text-muted-foreground max-w-md mx-auto">
              Add a field and record what you are growing to follow its growth stage and receive daily water guidance.
            </p>
            <Link
              href={farm ? `/farms/${farm.id}` : "/farms"}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:bg-emerald-800 transition-colors shadow-xs"
            >
              <Plus className="size-3.5" />
              <span>Add Field Planting</span>
            </Link>
          </div>
        )}
      </section>

      {/* ---------------- 5. Irrigation Advisory & Recent History Grid ---------------- */}
      <section className="grid gap-6 lg:grid-cols-2">
        {/* Advisories */}
        <div className="rounded-3xl border border-emerald-200/90 bg-white p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-emerald-100">
              <div className="flex items-center gap-2">
                <div className="size-8 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center">
                  <Lightbulb className="size-4" />
                </div>
                <div>
                  <h3 className="font-black text-base text-foreground">Farmer Advisory</h3>
                  <p className="text-[11px] text-muted-foreground">Actionable instructions for your fields</p>
                </div>
              </div>
              <Link href="/advisory" className="text-xs font-bold text-primary hover:underline">
                View All
              </Link>
            </div>

            {advisories.length > 0 ? (
              <div className="space-y-3 mt-4">
                {advisories.slice(0, 3).map((item, index) => (
                  <div
                    key={`${item.prediction_id}-${index}`}
                    className="p-3.5 rounded-2xl border border-emerald-200/80 bg-emerald-50/30 space-y-1"
                  >
                    <p className="text-sm font-bold text-foreground">{item.headline}</p>
                    {item.detail && <p className="text-xs text-muted-foreground leading-relaxed">{item.detail}</p>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground py-6 text-center">
                Run a water prediction for your crop to generate actionable advisories.
              </p>
            )}
          </div>

          <Link
            href="/irrigation"
            className="mt-4 pt-3 border-t border-emerald-100 inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline"
          >
            <span>Open Irrigation Scheduling</span>
            <ArrowRight className="size-3.5" />
          </Link>
        </div>

        {/* Recent History */}
        <div className="rounded-3xl border border-emerald-200/90 bg-white p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-emerald-100">
              <div className="flex items-center gap-2">
                <div className="size-8 rounded-xl bg-blue-100 text-blue-800 flex items-center justify-center">
                  <History className="size-4" />
                </div>
                <div>
                  <h3 className="font-black text-base text-foreground">Recent Water Checks</h3>
                  <p className="text-[11px] text-muted-foreground">Recent predictions and irrigation advice</p>
                </div>
              </div>
              <Link href="/predictions" className="text-xs font-bold text-primary hover:underline">
                View All
              </Link>
            </div>

            {history && history.length > 0 ? (
              <div className="space-y-2.5 mt-4">
                {history.slice(0, 3).map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-3 rounded-2xl border border-emerald-100 bg-white hover:bg-emerald-50/50 transition-colors"
                  >
                    <div>
                      <p className="text-xs font-bold text-foreground">{humaniseSlug(item.growth_stage)}</p>
                      <p className="text-[11px] text-muted-foreground">{formatDate(item.prediction_date)}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-black text-primary tabular">{formatDepth(item.gross_irrigation_mm)} mm</span>
                      <span className="text-[10px] text-muted-foreground block">to apply</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground py-6 text-center">
                Your completed water checks will be listed here.
              </p>
            )}
          </div>

          <Link
            href="/predictions"
            className="mt-4 pt-3 border-t border-emerald-100 inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline"
          >
            <span>See Full Water History Lineage</span>
            <ArrowRight className="size-3.5" />
          </Link>
        </div>
      </section>

      {/* ---------------- 6. Farmer Tip of the Day ---------------- */}
      <section className="rounded-3xl border border-amber-300 bg-gradient-to-r from-amber-50/80 via-white to-emerald-50/40 p-5 sm:p-6 shadow-xs">
        <div className="flex items-start gap-4">
          <div className="size-11 rounded-2xl bg-amber-500 text-white flex items-center justify-center shrink-0 shadow-xs font-bold">
            <Sparkles className="size-5" />
          </div>
          <div className="space-y-1">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-900">
              Karnataka Farmer Agronomic Tip
            </span>
            <p className="text-sm font-bold text-foreground">
              Early Morning Irrigation Saves Up to 25% of Pumping Energy
            </p>
            <p className="text-xs text-muted-foreground leading-relaxed max-w-3xl">
              Applying water between 6:00 AM and 8:30 AM minimizes solar evaporative losses and prevents leaf scorching. Drip systems deliver water directly to the active root depth without weed canopy interception.
            </p>
          </div>
        </div>
      </section>

      {/* ---------------- 7. Farm Shortcuts Navigation ---------------- */}
      <nav aria-label="Farm shortcuts" className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { href: "/farms", label: "My Farm & Fields", icon: Tractor },
          { href: "/predict", label: "Predict Water Need", icon: Droplets },
          { href: "/irrigation", label: "Irrigation Scheduling", icon: Waves },
          { href: "/predictions", label: "Water History", icon: Clock3 },
          { href: "/weather", label: "Local Field Weather", icon: MapPin },
          { href: "/advisory", label: "Farmer Advisory", icon: Sprout },
          { href: "/water-budget", label: "Water Budget", icon: BarChart3 },
          { href: "/help-me-choose", label: "Help Me Choose", icon: CircleHelp },
        ].map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className="flex min-h-12 items-center gap-2.5 rounded-2xl border border-emerald-200/90 bg-white px-3.5 py-3 text-xs font-bold text-foreground transition-all hover:border-primary hover:bg-emerald-50/50 shadow-xs"
          >
            <Icon className="size-4 shrink-0 text-primary" />
            <span className="truncate">{label}</span>
          </Link>
        ))}
      </nav>
    </div>
  );
}