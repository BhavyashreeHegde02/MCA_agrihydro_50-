"use client";

import { useState } from "react";
import {
  CloudSun,
  Droplets,
  Layers,
  Leaf,
  Lightbulb,
  MapPin,
  Sprout,
  Tractor,
} from "lucide-react";

interface StepItem {
  id: number;
  label: string;
  question: string;
  detail: string;
  badge: string;
  icon: React.ComponentType<{ className?: string }>;
  accentColor: string;
  bgColor: string;
  borderColor: string;
}

const STEPS: StepItem[] = [
  {
    id: 1,
    label: "Location",
    question: "Where is your farm?",
    detail: "District & taluk coordinates load localized Karnataka IMD rainfall normals, historical ET₀ and soil characteristics.",
    badge: "Step 1",
    icon: MapPin,
    accentColor: "text-amber-700",
    bgColor: "bg-amber-100/80",
    borderColor: "border-amber-300",
  },
  {
    id: 2,
    label: "Crop",
    question: "What are you growing?",
    detail: "Choose from calibrated regional crops (Paddy, Ragi, Maize, Groundnut) or explore matched candidates.",
    badge: "Step 2",
    icon: Sprout,
    accentColor: "text-emerald-700",
    bgColor: "bg-emerald-100/80",
    borderColor: "border-emerald-300",
  },
  {
    id: 3,
    label: "Growth Stage",
    question: "How old is the crop?",
    detail: "Sowing date calculates days after sowing, mapping into Initial, Vegetative, Flowering or Maturity with exact Kc coefficients.",
    badge: "Step 3",
    icon: Leaf,
    accentColor: "text-green-700",
    bgColor: "bg-green-100/80",
    borderColor: "border-green-300",
  },
  {
    id: 4,
    label: "Weather",
    question: "Current field conditions",
    detail: "Incorporates solar radiation, ambient temperature, relative humidity, wind speed, and recent 7-day rainfall.",
    badge: "Step 4",
    icon: CloudSun,
    accentColor: "text-sky-700",
    bgColor: "bg-sky-100/80",
    borderColor: "border-sky-300",
  },
  {
    id: 5,
    label: "Water Need",
    question: "Daily crop requirement",
    detail: "Physics-guided evapotranspiration (ETc = Kc × ET₀) produces expected daily demand in millimetres per day.",
    badge: "Step 5",
    icon: Droplets,
    accentColor: "text-blue-700",
    bgColor: "bg-blue-100/80",
    borderColor: "border-blue-300",
  },
  {
    id: 6,
    label: "Irrigation",
    question: "How much to pump?",
    detail: "Effective rainfall is subtracted from demand and adjusted for irrigation system efficiency (drip 90%, flood 60%).",
    badge: "Step 6",
    icon: Tractor,
    accentColor: "text-teal-700",
    bgColor: "bg-teal-100/80",
    borderColor: "border-teal-300",
  },
  {
    id: 7,
    label: "Advisory",
    question: "Actionable decision",
    detail: "Converts millimetres into exact pump volume in litres with weather-aware advice for immediate field action.",
    badge: "Step 7",
    icon: Lightbulb,
    accentColor: "text-amber-800",
    bgColor: "bg-amber-100/80",
    borderColor: "border-amber-300",
  },
];

export function LocationJourneyStepper({ className = "" }: { className?: string }) {
  const [activeStep, setActiveStep] = useState<number>(1);
  const current = STEPS[activeStep - 1];

  return (
    <div className={`rounded-3xl border border-emerald-200/90 bg-white p-6 sm:p-8 shadow-sm ${className}`}>
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-3 pb-6 border-b border-emerald-100">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100/80 px-2.5 py-1 rounded-full">
            Farmer Intelligence Pathway
          </span>
          <h3 className="text-2xl sm:text-3xl font-extrabold text-foreground mt-2">
            The Location-First Water Journey
          </h3>
          <p className="text-sm text-muted-foreground mt-1 max-w-xl">
            From the soil of your Karnataka district to precise irrigation pump litres in 7 intelligent steps.
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
          <Layers className="size-3.5 text-emerald-600" />
          <span>Click any step to inspect</span>
        </div>
      </div>

      {/* Stepper Timeline Navigation */}
      <div className="pt-6 overflow-x-auto pb-4 scrollbar-none">
        <div className="flex items-center justify-between min-w-[700px] relative px-4">
          {/* Background Connecting Line */}
          <div className="absolute top-5 left-8 right-8 h-1 bg-emerald-100 -z-0" />
          {/* Active Progress Line */}
          <div
            className="absolute top-5 left-8 h-1 bg-gradient-to-r from-emerald-500 to-primary transition-all duration-300 -z-0"
            style={{ width: `${((activeStep - 1) / (STEPS.length - 1)) * 92}%` }}
          />

          {STEPS.map((step) => {
            const Icon = step.icon;
            const isCurrent = step.id === activeStep;
            const isCompleted = step.id < activeStep;

            return (
              <button
                type="button"
                key={step.id}
                onClick={() => setActiveStep(step.id)}
                className="relative z-10 flex flex-col items-center group cursor-pointer focus:outline-none"
              >
                <div
                  className={`size-11 rounded-2xl flex items-center justify-center font-bold transition-all shadow-sm ${
                    isCurrent
                      ? "bg-primary text-primary-foreground scale-110 ring-4 ring-emerald-200 shadow-md"
                      : isCompleted
                      ? "bg-emerald-600 text-white"
                      : "bg-emerald-50 border border-emerald-200 text-emerald-800 hover:bg-emerald-100"
                  }`}
                >
                  <Icon className="size-5" />
                </div>
                <span
                  className={`mt-2 text-xs font-bold text-center whitespace-nowrap transition-colors ${
                    isCurrent ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                  }`}
                >
                  {step.label}
                </span>
                <span className="text-[10px] text-muted-foreground font-medium">
                  {step.badge}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Interactive Detail Card */}
      <div className="mt-4 rounded-2xl border border-emerald-200/80 bg-gradient-to-br from-emerald-50/70 via-white to-amber-50/40 p-5 sm:p-6 transition-all shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className={`size-14 rounded-2xl ${current.bgColor} ${current.borderColor} border flex items-center justify-center shrink-0 shadow-sm`}>
              <current.icon className={`size-7 ${current.accentColor}`} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">
                  {current.badge}
                </span>
                <span className="text-xs text-muted-foreground">•</span>
                <span className="text-xs font-semibold text-muted-foreground">{current.label} Phase</span>
              </div>
              <h4 className="text-xl font-bold text-foreground mt-0.5">
                {current.question}
              </h4>
              <p className="text-sm text-muted-foreground mt-1 leading-relaxed max-w-2xl">
                {current.detail}
              </p>
            </div>
          </div>

          <div className="flex sm:flex-col gap-2 shrink-0">
            <button
              type="button"
              disabled={activeStep === 1}
              onClick={() => setActiveStep((prev) => Math.max(1, prev - 1))}
              className="px-3.5 py-1.5 rounded-lg border border-emerald-200 bg-white text-xs font-semibold text-emerald-900 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-emerald-50"
            >
              &larr; Previous Step
            </button>
            <button
              type="button"
              disabled={activeStep === STEPS.length}
              onClick={() => setActiveStep((prev) => Math.min(STEPS.length, prev + 1))}
              className="px-3.5 py-1.5 rounded-lg bg-primary text-xs font-semibold text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-primary/90"
            >
              Next Step &rarr;
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
