"use client";

import { Droplets, Leaf, Sparkles, Sprout, Waves, Zap } from "lucide-react";

const MARQUEE_ITEMS = [
  { text: "SMART WATER MANAGEMENT", icon: Droplets },
  { text: "HEALTHY CROPS", icon: Sprout },
  { text: "SUSTAINABLE FARMING", icon: Leaf },
  { text: "AI WATER INTELLIGENCE", icon: Sparkles },
  { text: "RAINFALL-CREDITED IRRIGATION", icon: Waves },
  { text: "PREDICT WATER · GROW SMARTER", icon: Zap },
  { text: "JALACHAKRA (ಜಲಚಕ್ರ)", icon: Droplets },
  { text: "FAO-56 AGRONOMIC SCIENCE", icon: Sprout },
  { text: "PHYSICS-GUIDED PREDICTIONS", icon: Sparkles },
];

export function AgricultureMarquee({ className = "" }: { className?: string }) {
  return (
    <div
      aria-label="Agriculture highlights"
      className={`relative w-full overflow-hidden bg-emerald-50/80 border-y border-emerald-200/70 py-2.5 select-none ${className}`}
    >
      <div className="flex animate-marquee whitespace-nowrap">
        {/* Render twice for continuous seamless loop */}
        {[...MARQUEE_ITEMS, ...MARQUEE_ITEMS].map((item, idx) => {
          const Icon = item.icon;
          return (
            <div
              key={`${item.text}-${idx}`}
              className="inline-flex items-center gap-2 mx-5 text-xs font-bold tracking-wider text-emerald-900/90"
            >
              <span className="p-1 rounded-full bg-emerald-200/80 text-emerald-800">
                <Icon className="size-3" />
              </span>
              <span>{item.text}</span>
              <span className="text-emerald-400 font-black ml-3">•</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
