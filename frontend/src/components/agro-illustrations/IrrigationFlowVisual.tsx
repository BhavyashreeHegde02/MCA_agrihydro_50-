"use client";

import {
  ArrowDown,
  CloudRain,
  Droplets,
  Layers,
  Sprout,
  Tractor,
  Waves,
} from "lucide-react";
import { formatDepth, formatLitres, formatPercent } from "@/lib/format";

interface IrrigationFlowProps {
  cwrMmDay: number;
  effectiveRainMm: number;
  netIrrigationMm: number;
  grossIrrigationMm: number;
  grossLitres?: number | null;
  efficiency?: number | null;
  className?: string;
}

export function IrrigationFlowVisual({
  cwrMmDay,
  effectiveRainMm,
  netIrrigationMm,
  grossIrrigationMm,
  grossLitres,
  efficiency = 0.85,
  className = "",
}: IrrigationFlowProps) {
  return (
    <div
      className={`rounded-3xl border border-emerald-200/90 bg-white p-6 sm:p-8 shadow-sm ${className}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-6 border-b border-emerald-100">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-sky-700 bg-sky-100/80 px-2.5 py-0.5 rounded-full">
            Water Balance Equation
          </span>
          <h3 className="text-xl sm:text-2xl font-extrabold text-foreground mt-1">
            Rain → Soil → Crop → Irrigation Flow
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Transparent physical accounting so you never pump water that rain has already provided.
          </p>
        </div>

        {grossLitres !== null && grossLitres !== undefined && grossLitres > 0 && (
          <div className="bg-primary/10 border border-primary/30 rounded-2xl px-4 py-2 text-right">
            <span className="text-[11px] font-bold text-primary uppercase block">
              Pump Schedule
            </span>
            <span className="text-xl font-black text-primary tabular">
              {formatLitres(grossLitres)} Litres
            </span>
          </div>
        )}
      </div>

      {/* Visual Flow Pipeline */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 pt-6 items-center">
        {/* Stage 1: Rain */}
        <div className="rounded-2xl border border-sky-200 bg-gradient-to-b from-sky-50 to-white p-4 text-center">
          <div className="size-11 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center mx-auto mb-2 font-bold">
            <CloudRain className="size-6" />
          </div>
          <span className="text-[11px] font-bold uppercase text-sky-900 block">
            1. Rainfall Credited
          </span>
          <div className="text-2xl font-black text-sky-700 my-1 tabular">
            {formatDepth(effectiveRainMm)} <span className="text-xs font-semibold">mm</span>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Effective rain entering root zone
          </p>
        </div>

        {/* Connector 1 */}
        <div className="hidden md:flex flex-col items-center text-emerald-400">
          <span className="text-[11px] font-black text-emerald-600 mb-1">SOIL RETENTION</span>
          <div className="w-full h-0.5 bg-emerald-200 relative">
            <div className="absolute right-0 -top-1 border-t-4 border-b-4 border-l-4 border-transparent border-l-emerald-400" />
          </div>
        </div>

        {/* Stage 2: Crop Demand */}
        <div className="rounded-2xl border border-emerald-200 bg-gradient-to-b from-emerald-50 to-white p-4 text-center">
          <div className="size-11 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto mb-2 font-bold">
            <Sprout className="size-6" />
          </div>
          <span className="text-[11px] font-bold uppercase text-emerald-900 block">
            2. Crop Water Need
          </span>
          <div className="text-2xl font-black text-emerald-800 my-1 tabular">
            {formatDepth(cwrMmDay)} <span className="text-xs font-semibold">mm/day</span>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Daily evapotranspiration (ETc)
          </p>
        </div>

        {/* Connector 2 */}
        <div className="hidden md:flex flex-col items-center text-emerald-400">
          <span className="text-[11px] font-black text-emerald-600 mb-1">NET DEFICIT</span>
          <div className="w-full h-0.5 bg-emerald-200 relative">
            <div className="absolute right-0 -top-1 border-t-4 border-b-4 border-l-4 border-transparent border-l-emerald-400" />
          </div>
        </div>

        {/* Stage 3: Irrigation To Apply */}
        <div className="rounded-2xl border-2 border-primary bg-gradient-to-b from-emerald-100/70 to-white p-4 text-center shadow-md">
          <div className="size-11 rounded-xl bg-primary text-white flex items-center justify-center mx-auto mb-2 font-bold">
            <Tractor className="size-6" />
          </div>
          <span className="text-[11px] font-black uppercase text-primary block">
            3. Irrigation To Pump
          </span>
          <div className="text-2xl font-black text-primary my-1 tabular">
            {formatDepth(grossIrrigationMm)} <span className="text-xs font-semibold">mm</span>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Adjusted for {formatPercent(efficiency ?? 0.85)} system efficiency
          </p>
        </div>
      </div>

      {/* Advisory Formula Explanation Box */}
      <div className="mt-6 rounded-2xl border border-emerald-200/80 bg-emerald-50/60 p-4 text-xs text-muted-foreground flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Waves className="size-4 text-primary shrink-0" />
          <span>
            <strong>Calculation Rule:</strong> Net Irrigation = Max(0, Crop Need ({formatDepth(cwrMmDay)} mm) − Effective Rain ({formatDepth(effectiveRainMm)} mm)) = <strong>{formatDepth(netIrrigationMm)} mm</strong>
          </span>
        </div>
        <span className="text-primary font-bold">
          Zero water waste guaranteed
        </span>
      </div>
    </div>
  );
}
