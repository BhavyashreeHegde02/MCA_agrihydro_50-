import Link from "next/link";
import {
  ArrowRight,
  Award,
  CheckCircle2,
  ChevronRight,
  Compass,
  Droplets,
  Info,
  Layers,
  Leaf,
  MapPin,
  ShieldCheck,
  Sparkles,
  Sprout,
  Tractor,
  Waves,
  Zap,
} from "lucide-react";

import { hasSession } from "@/lib/auth/session";
import { rscGetOptional } from "@/lib/api/rsc";
import { callBackend } from "@/lib/api/server";
import type { CropOut, UserOut } from "@/lib/api/types";
import { AgricultureMarquee } from "@/components/agro-illustrations/AgricultureMarquee";
import { HeroFarmScene } from "@/components/agro-illustrations/HeroFarmScene";
import { LocationJourneyStepper } from "@/components/agro-illustrations/LocationJourneyStepper";

export const metadata = {
  title: "Jalachakra (ಜಲಚಕ್ರ) — Intelligent Crop Water Requirement Prediction & Advisory System",
  description:
    "A research-backed, farmer-first agricultural water intelligence platform providing FAO-56 crop water demand, irrigation scheduling in pump litres, and actionable field advisories.",
};

export default async function LandingPage() {
  const loggedIn = await hasSession();
  const [user, crops] = await Promise.all([
    loggedIn ? rscGetOptional<UserOut>("/api/v1/auth/me") : Promise.resolve(null),
    callBackend<CropOut[]>({ path: "/api/v1/crops" })
      .then(({ data }) => data)
      .catch(() => null),
  ]);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col selection:bg-emerald-200 selection:text-emerald-900">
      {/* ---------------- 1. Running Agriculture Marquee ---------------- */}
      <AgricultureMarquee />

      {/* ---------------- 2. Academic Project Credentials Bar ---------------- */}
      <div className="bg-emerald-100/60 border-b border-emerald-200/80 px-4 py-2 text-xs text-emerald-950">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-primary text-white shadow-xs">
              <Award className="size-3" />
              
            </span>
            <span className="font-semibold text-emerald-900 hidden sm:inline">
              Physics-Guided Crop Water Requirement &amp; Climate-Resilient Farmer Decision Support System
            </span>
          </div>
          <div className="flex items-center gap-3 text-[11px] font-semibold text-emerald-800">
            <span>Karnataka District Benchmarks</span>
            <span>•</span>
            <span>FAO-56 Penman-Monteith</span>
          </div>
        </div>
      </div>

      {/* ---------------- 3. Navigation Bar ---------------- */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-emerald-200/80 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-18 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="size-11 rounded-2xl bg-gradient-to-tr from-primary via-emerald-600 to-teal-400 flex items-center justify-center text-white shadow-md shadow-emerald-900/10 transition-transform group-hover:scale-105">
              <Droplets className="size-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-xl tracking-tight text-emerald-950">
                  JALACHAKRA
                </span>
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                  ಜಲಚಕ್ರ
                </span>
              </div>
              <p className="text-xs text-emerald-800/80 font-medium leading-none mt-0.5">
                Predict Water · Grow Smarter
              </p>
            </div>
          </Link>

          <nav className="flex items-center gap-3">
            <Link
              href="/crops"
              className="hidden md:inline-flex items-center gap-1.5 px-3 py-2 text-sm font-semibold text-emerald-900 hover:text-primary transition-colors"
            >
              <Sprout className="size-4 text-emerald-600" />
              <span>Crop Guides</span>
            </Link>

            <Link
              href="/weather"
              className="hidden md:inline-flex items-center gap-1.5 px-3 py-2 text-sm font-semibold text-emerald-900 hover:text-primary transition-colors"
            >
              <span>Weather</span>
            </Link>

            {loggedIn && user ? (
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-white text-sm font-bold hover:bg-emerald-800 shadow-sm transition-all"
              >
                <span>Dashboard ({user.full_name.split(" ")[0]})</span>
                <ArrowRight className="size-4" />
              </Link>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="px-4 py-2 text-sm font-bold text-emerald-900 hover:text-primary transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-primary text-white text-sm font-bold hover:bg-emerald-800 shadow-sm transition-all"
                >
                  <Sprout className="size-4" />
                  <span>Register Farm</span>
                </Link>
              </div>
            )}
          </nav>
        </div>
      </header>

      {/* ---------------- 4. Immersive JALACHAKRA Hero Experience ---------------- */}
      <section className="relative overflow-hidden pt-8 pb-14 md:pt-14 md:pb-20 bg-gradient-to-b from-emerald-50/70 via-background to-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            {/* Left Hero Column */}
            <div className="lg:col-span-6 space-y-6 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 text-xs sm:text-sm font-bold shadow-xs">
                <Sparkles className="size-4 text-emerald-600" />
                <span>Agricultural Water Intelligence Platform</span>
              </div>

              <div className="space-y-2">
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-emerald-950 leading-[1.1]">
                  JALACHAKRA
                </h1>
                <p className="text-xl sm:text-2xl font-bold text-emerald-800">
                  Intelligent Water Decisions for Every Crop.
                </p>
              </div>

              <p className="text-base sm:text-lg text-emerald-900/80 leading-relaxed max-w-xl mx-auto lg:mx-0">
                Predict exact daily crop water requirement, credit incoming rainfall, and generate farmer-friendly pump schedules in litres—calibrated for Karnataka soils and climate.
              </p>

              {/* Research Badges */}
              <div className="flex flex-wrap items-center justify-center lg:justify-start gap-2 pt-1">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-emerald-200 text-xs font-bold text-emerald-900 shadow-xs">
                  <ShieldCheck className="size-3.5 text-emerald-600" />
                  Physics-Guided XGBoost
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-emerald-200 text-xs font-bold text-emerald-900 shadow-xs">
                  <Sprout className="size-3.5 text-emerald-600" />
                  Growth-Stage Aware (Kc)
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-emerald-200 text-xs font-bold text-emerald-900 shadow-xs">
                  <Waves className="size-3.5 text-sky-600" />
                  Rainfall-Credited
                </span>
              </div>

              {/* CTAs */}
              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-3.5 pt-3">
                <Link
                  href={loggedIn ? "/predict" : "/login"}
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-4 rounded-xl bg-primary text-white font-bold shadow-lg shadow-emerald-900/15 hover:bg-emerald-800 transition-all text-base group"
                >
                  <Droplets className="size-5" />
                  <span>Calculate Crop Water Need</span>
                  <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
                </Link>

                <Link
                  href="/login?demo=true"
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-4 rounded-xl border border-emerald-300 bg-white text-emerald-950 font-bold hover:bg-emerald-50 transition-colors text-base shadow-xs"
                >
                  <Zap className="size-4 text-amber-500 fill-amber-500" />
                  <span>1-Click Presentation Demo</span>
                </Link>
              </div>

              {/* Farmer Tip Subtext */}
              <p className="text-xs text-muted-foreground pt-1">
                Zero guesswork: Shows how many litres to pump today based on actual field area.
              </p>
            </div>

            {/* Right Hero Column: Living Farm Scene */}
            <div className="lg:col-span-6 flex justify-center">
              <HeroFarmScene />
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- 5. The Two Main User Intent Pathways (Dominant Cards) ---------------- */}
      <section className="py-14 bg-white border-y border-emerald-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100/80 px-3 py-1 rounded-full">
              Tailored Farmer Pathways
            </span>
            <h2 className="mt-3 text-3xl sm:text-4xl font-black tracking-tight text-foreground">
              What Would You Like to Do Today?
            </h2>
            <p className="mt-2 text-base text-muted-foreground">
              Whether you already have seedlings in the field or are planning next season&apos;s sowing, select your journey below.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Card 1: I KNOW MY CROP */}
            <div className="rounded-3xl border-2 border-emerald-300 bg-gradient-to-br from-emerald-50/60 via-white to-emerald-50/30 p-8 sm:p-9 relative overflow-hidden group hover:border-primary hover:shadow-xl hover:shadow-emerald-900/10 transition-all">
              <div className="absolute top-0 right-0 w-36 h-36 bg-gradient-to-bl from-emerald-200/50 to-transparent rounded-bl-full pointer-events-none" />

              <div className="flex items-center gap-4 mb-5">
                <div className="size-14 rounded-2xl bg-primary text-white flex items-center justify-center shadow-md shadow-emerald-900/15 group-hover:scale-105 transition-transform">
                  <Sprout className="size-7" />
                </div>
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">
                    Pathway 1 · Active Planting
                  </span>
                  <h3 className="text-2xl sm:text-3xl font-black text-foreground">
                    🌱 I KNOW MY CROP
                  </h3>
                </div>
              </div>

              <p className="text-base text-emerald-950/80 mb-6 leading-relaxed">
                Already know what you want to grow? Get a personalized crop-water requirement and irrigation recommendation tailored to your sowing date and growth stage.
              </p>

              <div className="space-y-3 mb-8 bg-white/80 rounded-2xl p-4 border border-emerald-200/70">
                <div className="flex items-center gap-2.5 text-sm font-semibold text-emerald-950">
                  <CheckCircle2 className="size-4.5 text-primary shrink-0" />
                  <span>Dynamic Kc curves across Initial, Vegetative, Flowering &amp; Maturity</span>
                </div>
                <div className="flex items-center gap-2.5 text-sm font-semibold text-emerald-950">
                  <CheckCircle2 className="size-4.5 text-primary shrink-0" />
                  <span>Automatic rainfall credit prevents waterlogging and electricity waste</span>
                </div>
                <div className="flex items-center gap-2.5 text-sm font-semibold text-emerald-950">
                  <CheckCircle2 className="size-4.5 text-primary shrink-0" />
                  <span>Gross irrigation output formatted directly into pump litres</span>
                </div>
              </div>

              <Link
                href="/predict"
                className="inline-flex items-center justify-center gap-2.5 w-full py-4 px-6 rounded-xl bg-primary text-white font-bold hover:bg-emerald-800 shadow-md shadow-emerald-900/10 transition-all text-base group/btn"
              >
                <span>Launch &quot;I Know My Crop&quot; Recommendation</span>
                <ArrowRight className="size-4 transition-transform group-hover/btn:translate-x-1" />
              </Link>
            </div>

            {/* Card 2: HELP ME CHOOSE */}
            <div className="rounded-3xl border-2 border-amber-300 bg-gradient-to-br from-amber-50/50 via-white to-emerald-50/20 p-8 sm:p-9 relative overflow-hidden group hover:border-amber-500 hover:shadow-xl hover:shadow-amber-900/10 transition-all">
              <div className="absolute top-0 right-0 w-36 h-36 bg-gradient-to-bl from-amber-200/50 to-transparent rounded-bl-full pointer-events-none" />

              <div className="flex items-center gap-4 mb-5">
                <div className="size-14 rounded-2xl bg-amber-500 text-white flex items-center justify-center shadow-md shadow-amber-900/15 group-hover:scale-105 transition-transform">
                  <Compass className="size-7" />
                </div>
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-amber-700">
                    Pathway 2 · Crop Matching
                  </span>
                  <h3 className="text-2xl sm:text-3xl font-black text-foreground">
                    🌾 HELP ME CHOOSE
                  </h3>
                </div>
              </div>

              <p className="text-base text-emerald-950/80 mb-6 leading-relaxed">
                Not sure which crop suits your conditions? Explore suitable crops based on your location, soil N-P-K, pH, and seasonal water availability.
              </p>

              <div className="space-y-3 mb-8 bg-white/80 rounded-2xl p-4 border border-amber-200/70">
                <div className="flex items-center gap-2.5 text-sm font-semibold text-emerald-950">
                  <CheckCircle2 className="size-4.5 text-amber-600 shrink-0" />
                  <span>Karnataka district soil benchmarks (Mandya, Belagavi, Mysuru, etc.)</span>
                </div>
                <div className="flex items-center gap-2.5 text-sm font-semibold text-emerald-950">
                  <CheckCircle2 className="size-4.5 text-amber-600 shrink-0" />
                  <span>Water feasibility check flags crops demanding more water than available</span>
                </div>
                <div className="flex items-center gap-2.5 text-sm font-semibold text-emerald-950">
                  <CheckCircle2 className="size-4.5 text-amber-600 shrink-0" />
                  <span>Distinguishes seasonal crops from multi-year perennials</span>
                </div>
              </div>

              <Link
                href="/help-me-choose"
                className="inline-flex items-center justify-center gap-2.5 w-full py-4 px-6 rounded-xl border-2 border-amber-400 bg-white text-amber-950 font-bold hover:bg-amber-50 shadow-sm transition-all text-base group/btn"
              >
                <span>Explore &quot;Help Me Choose&quot; Candidates</span>
                <ChevronRight className="size-4 transition-transform group-hover/btn:translate-x-1" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- 6. Location-First Stepper Experience ---------------- */}
      <section className="py-14 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <LocationJourneyStepper />
        </div>
      </section>

      {/* ---------------- 7. Supported Karnataka Crops ---------------- */}
      <section className="py-14 bg-white border-t border-emerald-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100/80 px-2.5 py-0.5 rounded-full">
                Regional Agronomic Library
              </span>
              <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-foreground mt-2">
                Supported Karnataka Crops
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                Calibrated crop models with FAO-56 crop coefficient curves and growth duration.
              </p>
            </div>
            <Link
              href="/crops"
              className="inline-flex items-center gap-1.5 text-sm font-bold text-primary hover:underline"
            >
              <span>View Full Stage Tables &amp; Kc Curves</span>
              <ArrowRight className="size-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {crops?.map((crop) => (
              <div
                key={crop.slug}
                className="bg-emerald-50/30 rounded-2xl p-5 border border-emerald-200/80 hover:border-primary/60 hover:bg-white hover:shadow-md transition-all group"
              >
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="size-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
                    <Sprout className="size-5" />
                  </div>
                  <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                    {crop.category ?? "Field Crop"}
                  </span>
                </div>

                <h3 className="font-extrabold text-lg text-foreground group-hover:text-primary transition-colors">
                  {crop.name}
                </h3>

                <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                  Stage-calibrated transpiration curve with USDA rainfall subtraction.
                </p>

                <div className="mt-4 pt-3 border-t border-emerald-100 flex items-center justify-between text-xs text-muted-foreground">
                  <span>Cycle Length:</span>
                  <strong className="text-emerald-950 font-bold">{crop.cycle_length_days} Days</strong>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs sm:text-sm text-amber-900 flex items-start gap-3">
            <Info className="size-5 shrink-0 text-amber-600 mt-0.5" />
            <div>
              <strong>Honest Agronomic Transparency:</strong> Non-calibrated crops (e.g. Sugarcane, Arecanut, Coffee) are marked <strong>UNDER DEVELOPMENT</strong>. Crop water requirements are only generated when verified lysimeter or FAO-56 curves exist.
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- 8. Academic Research Credentials & Physics Transparency ---------------- */}
      <section className="py-10 bg-background border-t border-emerald-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <details className="rounded-2xl border border-emerald-200 bg-white p-5 sm:p-6 group">
            <summary className="cursor-pointer text-base font-bold text-foreground flex items-center justify-between list-none">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="size-5 text-primary" />
                <span>About This MCA Research Project · Architecture &amp; Methodology</span>
              </div>
              <span className="text-xs text-primary font-bold group-open:rotate-180 transition-transform">
                ▼
              </span>
            </summary>

            <div className="mt-5 space-y-4 text-sm leading-relaxed text-muted-foreground border-t border-emerald-100 pt-4 max-w-4xl">
              <p>
                <strong>Jalachakra (ಜಲಚಕ್ರ)</strong> is an advanced agro-hydrological decision support system that unites farm geolocation, dynamic crop growth stage, localized weather, and physics-guided machine learning into an actionable recommendation engine.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <div className="p-3.5 rounded-xl bg-emerald-50/60 border border-emerald-200 text-xs">
                  <h4 className="font-bold text-foreground mb-1">1. FAO-56 Reference ET₀</h4>
                  <p>Penman-Monteith equation driven by temperature, radiation, relative humidity, and wind speed.</p>
                </div>
                <div className="p-3.5 rounded-xl bg-emerald-50/60 border border-emerald-200 text-xs">
                  <h4 className="font-bold text-foreground mb-1">2. Dynamic Kc Curves</h4>
                  <p>Piecewise linear interpolation over Initial, Crop Development, Mid-Season, and Late-Season stages.</p>
                </div>
                <div className="p-3.5 rounded-xl bg-emerald-50/60 border border-emerald-200 text-xs">
                  <h4 className="font-bold text-foreground mb-1">3. Irrigation in Litres</h4>
                  <p>Net irrigation adjusted for application efficiency (Ea) multiplied by farm area into pump discharge litres.</p>
                </div>
              </div>
            </div>
          </details>
        </div>
      </section>

      {/* ---------------- 9. Premium Footer ---------------- */}
      <footer className="mt-auto border-t border-emerald-200/90 bg-white py-12 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-sm text-muted-foreground">
          <div className="flex items-center gap-3">
            <div className="size-10 rounded-xl bg-primary text-white flex items-center justify-center font-bold shadow-sm">
              <Droplets className="size-5" />
            </div>
            <div>
              <p className="font-black text-foreground text-base">Jalachakra (ಜಲಚಕ್ರ)</p>
              <p className="text-xs text-muted-foreground">Intelligent Crop Water Requirement Prediction &amp; Advisory System</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-6 text-xs font-semibold text-emerald-950">
            <Link href="/dashboard" className="hover:text-primary transition-colors">Dashboard</Link>
            <Link href="/predict" className="hover:text-primary transition-colors">I Know My Crop</Link>
            <Link href="/help-me-choose" className="hover:text-primary transition-colors">Help Me Choose</Link>
            <Link href="/crops" className="hover:text-primary transition-colors">Crop Reference</Link>
            <Link href="/weather" className="hover:text-primary transition-colors">Local Weather</Link>
            <Link href="/login" className="hover:text-primary transition-colors">Farmer Login</Link>
          </div>

          <p className="text-xs text-muted-foreground text-center md:text-right">
          &copy;Real agronomic data &amp; transparent FAO-56 baselines.
          </p>
        </div>
      </footer>
    </div>
  );
}
