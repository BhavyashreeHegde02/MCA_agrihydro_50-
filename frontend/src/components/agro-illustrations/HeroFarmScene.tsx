"use client";

import { Droplets, Sparkles, Sprout, Sun, Wind } from "lucide-react";

export function HeroFarmScene({ className = "" }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`relative w-full aspect-[4/3] max-w-[560px] mx-auto rounded-3xl overflow-hidden border border-emerald-200/80 bg-gradient-to-b from-sky-100 via-emerald-50/50 to-emerald-100/60 shadow-xl shadow-emerald-900/5 select-none ${className}`}
    >
      <svg
        viewBox="0 0 800 600"
        className="w-full h-full object-cover"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Sky Gradient */}
          <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#dbeafe" />
            <stop offset="45%" stopColor="#fef3c7" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#e8f5e9" />
          </linearGradient>

          {/* Distant Hills Gradient */}
          <linearGradient id="hillGrad1" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#86efac" />
            <stop offset="100%" stopColor="#4ade80" />
          </linearGradient>

          {/* Near Hills Gradient */}
          <linearGradient id="hillGrad2" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#4ade80" />
            <stop offset="100%" stopColor="#22c55e" />
          </linearGradient>

          {/* Field Terrace Gradient */}
          <linearGradient id="terraceGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#2e7d32" />
            <stop offset="100%" stopColor="#1b5e20" />
          </linearGradient>

          {/* Water Channel Gradient */}
          <linearGradient id="waterStream" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="50%" stopColor="#0288d1" />
            <stop offset="100%" stopColor="#0369a1" />
          </linearGradient>

          {/* Soil Bed Gradient */}
          <linearGradient id="soilBed" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#a1887f" />
            <stop offset="100%" stopColor="#6d4c41" />
          </linearGradient>
        </defs>

        {/* 1. Sky & Sun */}
        <rect width="800" height="600" fill="url(#skyGrad)" />

        {/* Sun with pulsing corona */}
        <g className="animate-sun-pulse" style={{ transformOrigin: "670px 110px" }}>
          <circle cx="670" cy="110" r="50" fill="#fde68a" opacity="0.4" />
          <circle cx="670" cy="110" r="38" fill="#fef08a" opacity="0.7" />
          <circle cx="670" cy="110" r="26" fill="#f59e0b" />
          {/* Subtle Sun Rays */}
          <line x1="670" y1="40" x2="670" y2="25" stroke="#f59e0b" strokeWidth="3" strokeLinecap="round" opacity="0.6" />
          <line x1="670" y1="180" x2="670" y2="195" stroke="#f59e0b" strokeWidth="3" strokeLinecap="round" opacity="0.6" />
          <line x1="600" y1="110" x2="585" y2="110" stroke="#f59e0b" strokeWidth="3" strokeLinecap="round" opacity="0.6" />
          <line x1="740" y1="110" x2="755" y2="110" stroke="#f59e0b" strokeWidth="3" strokeLinecap="round" opacity="0.6" />
        </g>

        {/* 2. Soft Drifting Clouds */}
        <g className="animate-cloud-drift">
          {/* Cloud 1 */}
          <g fill="#ffffff" opacity="0.85">
            <ellipse cx="180" cy="95" rx="55" ry="22" />
            <ellipse cx="220" cy="85" rx="40" ry="24" />
            <ellipse cx="150" cy="100" rx="35" ry="18" />
          </g>
          {/* Cloud 2 */}
          <g fill="#ffffff" opacity="0.75">
            <ellipse cx="450" cy="130" rx="65" ry="24" />
            <ellipse cx="490" cy="120" rx="45" ry="26" />
            <ellipse cx="410" cy="135" rx="38" ry="18" />
          </g>
        </g>

        {/* 3. Distant Western Ghats / Karnataka Hills */}
        <path
          d="M0 290 Q 140 220 280 260 T 560 240 T 800 270 L 800 600 L 0 600 Z"
          fill="url(#hillGrad1)"
          opacity="0.65"
        />
        <path
          d="M0 320 Q 200 260 400 300 T 800 290 L 800 600 L 0 600 Z"
          fill="url(#hillGrad2)"
          opacity="0.8"
        />

        {/* Distant Palm / Coconut & Neem Trees */}
        <g fill="#2e7d32" opacity="0.9">
          {/* Palm 1 */}
          <path d="M 690 310 Q 692 260 690 230" stroke="#6d4c41" strokeWidth="4" fill="none" />
          <path d="M 690 230 Q 660 215 640 235 Q 675 228 690 230" />
          <path d="M 690 230 Q 720 215 740 235 Q 705 228 690 230" />
          <path d="M 690 230 Q 690 200 675 205 Q 688 220 690 230" />
          <path d="M 690 230 Q 705 200 705 205 Q 695 220 690 230" />

          {/* Palm 2 */}
          <path d="M 725 320 Q 728 275 725 245" stroke="#6d4c41" strokeWidth="3" fill="none" />
          <path d="M 725 245 Q 700 230 685 248 Q 712 242 725 245" />
          <path d="M 725 245 Q 750 230 765 248 Q 738 242 725 245" />

          {/* Round Neem / Peepal canopy */}
          <ellipse cx="110" cy="310" rx="35" ry="30" fill="#2e7d32" />
          <ellipse cx="140" cy="305" rx="30" ry="26" fill="#388e3c" />
          <rect x="120" y="325" width="8" height="25" fill="#5d4037" />
        </g>

        {/* 4. Terrace Farmland Layers & Soil */}
        <path
          d="M 0 350 Q 250 330 500 365 T 800 350 L 800 600 L 0 600 Z"
          fill="#43a047"
        />
        {/* Soil Bed Strip */}
        <path
          d="M 0 410 Q 300 395 600 420 T 800 410 L 800 450 Q 500 460 200 440 L 0 445 Z"
          fill="url(#soilBed)"
          opacity="0.85"
        />

        {/* 5. Main Agricultural Green Field with crop rows */}
        <path
          d="M 0 435 Q 260 410 520 440 T 800 430 L 800 600 L 0 600 Z"
          fill="url(#terraceGrad)"
        />

        {/* Irrigation Channel (Water Stream) with Animated Flow */}
        <path
          d="M 280 430 Q 320 470 380 520 T 450 600"
          stroke="#94a3b8"
          strokeWidth="32"
          fill="none"
          strokeLinecap="round"
          opacity="0.4"
        />
        <path
          d="M 280 430 Q 320 470 380 520 T 450 600"
          stroke="url(#waterStream)"
          strokeWidth="20"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d="M 280 430 Q 320 470 380 520 T 450 600"
          stroke="#e0f2fe"
          strokeWidth="4"
          fill="none"
          className="animate-water-flow"
        />

        {/* 6. Swaying Crop Rows (Paddy / Ragi / Maize) */}
        <g className="animate-crop-sway">
          {/* Row 1 - Left foreground */}
          {[60, 95, 130, 165, 200, 235].map((x, i) => (
            <g key={`crop-l-${i}`} transform={`translate(${x}, ${460 + (i % 2) * 15})`}>
              <path d="M 0 45 Q 8 15 2 0 Q -4 18 0 45" fill="#a5d6a7" />
              <path d="M 0 45 Q -10 22 -18 10 Q -6 26 0 45" fill="#81c784" />
              <path d="M 0 45 Q 12 25 22 12 Q 8 28 0 45" fill="#66bb6a" />
              <circle cx="2" cy="0" r="3.5" fill="#fde047" />
            </g>
          ))}

          {/* Row 2 - Right foreground */}
          {[480, 520, 560, 600, 640, 680, 720].map((x, i) => (
            <g key={`crop-r-${i}`} transform={`translate(${x}, ${470 + (i % 3) * 12})`}>
              <path d="M 0 50 Q 6 18 0 0 Q -5 20 0 50" fill="#a5d6a7" />
              <path d="M 0 50 Q -12 25 -20 12 Q -7 30 0 50" fill="#81c784" />
              <path d="M 0 50 Q 14 26 24 15 Q 9 32 0 50" fill="#66bb6a" />
              <circle cx="0" cy="0" r="3.5" fill="#fde047" />
            </g>
          ))}
        </g>

        {/* 7. Friendly Farmer Character Illustration */}
        <g transform="translate(200, 340)">
          {/* Shadow */}
          <ellipse cx="30" cy="180" rx="24" ry="7" fill="#1b3820" opacity="0.3" />

          {/* Legs & Dhoti/Pants */}
          <path d="M 20 125 L 18 175 L 26 175 L 28 135 L 36 175 L 44 175 L 40 125 Z" fill="#f1f5f9" />
          {/* Feet / Slippers */}
          <rect x="14" y="173" width="14" height="6" rx="2" fill="#78350f" />
          <rect x="34" y="173" width="14" height="6" rx="2" fill="#78350f" />

          {/* Kurta / Shirt (Natural Cotton) */}
          <path d="M 12 65 Q 30 60 48 65 L 46 128 L 14 128 Z" fill="#ecfdf5" stroke="#94a3b8" strokeWidth="0.8" />
          <path d="M 28 65 L 28 95" stroke="#cbd5e1" strokeWidth="1.5" />

          {/* Green Angavastram / Towel over shoulder */}
          <path d="M 12 70 Q 22 90 20 120 L 26 120 Q 28 85 24 67 Z" fill="#2e7d32" />

          {/* Arms holding tablet / crop leaf */}
          <path d="M 12 72 Q -2 95 10 110" stroke="#fbcfe8" strokeWidth="6" strokeLinecap="round" fill="none" />
          <path d="M 48 72 Q 58 92 42 108" stroke="#fbcfe8" strokeWidth="6" strokeLinecap="round" fill="none" />

          {/* Smart Device / Soil Moisture Sensor in hand */}
          <rect x="18" y="100" width="22" height="15" rx="3" fill="#0288d1" />
          <rect x="20" y="102" width="18" height="11" rx="1.5" fill="#38bdf8" />
          <circle cx="29" cy="107" r="2" fill="#ffffff" />

          {/* Neck & Head */}
          <rect x="26" y="52" width="8" height="14" fill="#fbcfe8" />
          <circle cx="30" cy="42" r="14" fill="#fbcfe8" />

          {/* Friendly Face / Smile */}
          <path d="M 27 45 Q 30 48 33 45" stroke="#831843" strokeWidth="1.2" fill="none" strokeLinecap="round" />
          {/* Eyes */}
          <circle cx="26" cy="40" r="1.5" fill="#1e293b" />
          <circle cx="34" cy="40" r="1.5" fill="#1e293b" />

          {/* Traditional Turban / Mysuru Peta style cloth */}
          <ellipse cx="30" cy="30" rx="18" ry="10" fill="#f59e0b" />
          <path d="M 14 34 Q 30 22 46 34 Q 30 38 14 34 Z" fill="#d97706" />
          <path d="M 42 30 Q 48 40 45 52" stroke="#d97706" strokeWidth="3" fill="none" strokeLinecap="round" />
        </g>

        {/* 8. Floating Water Droplets & Gentle Pollen Particles */}
        <g className="animate-particle-float">
          <circle cx="240" cy="410" r="3.5" fill="#38bdf8" opacity="0.8" />
          <circle cx="270" cy="390" r="2.5" fill="#0288d1" opacity="0.7" />
          <circle cx="360" cy="460" r="3" fill="#bae6fd" opacity="0.9" />
          <circle cx="410" cy="490" r="2" fill="#60a5fa" opacity="0.8" />
          {/* Sunlit golden pollen particles */}
          <circle cx="160" cy="350" r="2" fill="#fde047" opacity="0.8" />
          <circle cx="530" cy="390" r="2.5" fill="#fde047" opacity="0.75" />
          <circle cx="610" cy="340" r="2" fill="#facc15" opacity="0.85" />
        </g>
      </svg>

      {/* Floating Research Badge Overlay */}
      <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm border border-emerald-300/70 rounded-full px-3.5 py-1.5 flex items-center gap-2 shadow-sm text-xs font-semibold text-emerald-950">
        <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
        <span>Live Karnataka Agro-Hydrological Model</span>
      </div>

      <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur-sm border border-emerald-300/70 rounded-xl p-2.5 flex items-center gap-3 shadow-md">
        <div className="size-9 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold">
          <Droplets className="size-5" />
        </div>
        <div>
          <p className="text-[11px] font-bold text-emerald-900 leading-tight">Root Zone Transpiration</p>
          <p className="text-xs font-black text-emerald-700">Dynamic FAO-56 Kc Interpolation</p>
        </div>
      </div>
    </div>
  );
}
