"use client";

import { Droplets, Sparkles, Sprout, Sun } from "lucide-react";

export function AuthFarmIllustration({
  headline = "Smarter Water for Every Field",
  subheadline = "Predict water demand, protect against drought, and optimize pumping.",
}: {
  headline?: string;
  subheadline?: string;
}) {
  return (
    <div className="relative h-full w-full rounded-3xl overflow-hidden border border-emerald-200/90 bg-gradient-to-b from-sky-100 via-emerald-50/50 to-emerald-100/70 p-8 flex flex-col justify-between shadow-lg shadow-emerald-950/5 select-none min-h-[480px]">
      {/* Background Living SVG Scene */}
      <svg
        viewBox="0 0 500 500"
        className="absolute inset-0 w-full h-full object-cover pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="authSky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#bae6fd" />
            <stop offset="50%" stopColor="#fef3c7" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#dcfce7" />
          </linearGradient>

          <linearGradient id="authHill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#86efac" />
            <stop offset="100%" stopColor="#4ade80" />
          </linearGradient>

          <linearGradient id="authField" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2e7d32" />
            <stop offset="100%" stopColor="#1b5e20" />
          </linearGradient>

          <linearGradient id="authWater" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="100%" stopColor="#0288d1" />
          </linearGradient>
        </defs>

        <rect width="500" height="500" fill="url(#authSky)" />

        {/* Golden Sun with Pulse */}
        <g className="animate-sun-pulse" style={{ transformOrigin: "420px 90px" }}>
          <circle cx="420" cy="90" r="42" fill="#fde68a" opacity="0.5" />
          <circle cx="420" cy="90" r="28" fill="#f59e0b" />
        </g>

        {/* Clouds */}
        <g className="animate-cloud-drift">
          <ellipse cx="120" cy="80" rx="45" ry="18" fill="#ffffff" opacity="0.9" />
          <ellipse cx="150" cy="72" rx="30" ry="20" fill="#ffffff" opacity="0.9" />
        </g>

        {/* Karnataka Hills */}
        <path d="M0 250 Q 150 190 300 230 T 500 220 L 500 500 L 0 500 Z" fill="url(#authHill)" opacity="0.75" />
        <path d="M0 280 Q 200 230 350 270 T 500 260 L 500 500 L 0 500 Z" fill="#22c55e" opacity="0.8" />

        {/* Trees */}
        <ellipse cx="80" cy="270" rx="30" ry="25" fill="#15803d" />
        <rect x="76" y="285" width="8" height="20" fill="#78350f" />
        <ellipse cx="115" cy="265" rx="25" ry="22" fill="#166534" />
        <rect x="112" y="280" width="6" height="20" fill="#78350f" />

        {/* Main Field Terrace */}
        <path d="M0 320 Q 200 290 380 330 T 500 320 L 500 500 L 0 500 Z" fill="url(#authField)" />

        {/* Flowing Irrigation Stream */}
        <path
          d="M 180 320 Q 220 370 270 420 T 320 500"
          stroke="url(#authWater)"
          strokeWidth="18"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d="M 180 320 Q 220 370 270 420 T 320 500"
          stroke="#ffffff"
          strokeWidth="3.5"
          fill="none"
          className="animate-water-flow"
        />

        {/* Swaying Crops */}
        <g className="animate-crop-sway">
          {[40, 80, 120, 360, 400, 440].map((x, i) => (
            <g key={`crop-${x}`} transform={`translate(${x}, 380)`}>
              <path d="M 0 35 Q 6 12 0 0 Q -5 14 0 35" fill="#a5d6a7" />
              <path d="M 0 35 Q -10 18 -16 8 Q -6 22 0 35" fill="#81c784" />
              <path d="M 0 35 Q 12 18 18 10 Q 7 24 0 35" fill="#66bb6a" />
              <circle cx="0" cy="0" r="2.5" fill="#fde047" />
            </g>
          ))}
        </g>

        {/* Farmer Silhouette in Field */}
        <g transform="translate(140, 255)">
          <ellipse cx="20" cy="115" rx="16" ry="5" fill="#14532d" opacity="0.4" />
          <path d="M 12 80 L 10 110 L 16 110 L 18 85 L 24 110 L 30 110 L 26 80 Z" fill="#ffffff" />
          <path d="M 8 40 Q 20 36 32 40 L 30 82 L 10 82 Z" fill="#ecfdf5" />
          <path d="M 8 45 Q 15 60 14 80 L 18 80 Q 19 55 16 42 Z" fill="#2e7d32" />
          <circle cx="20" cy="24" r="10" fill="#fbcfe8" />
          <ellipse cx="20" cy="16" rx="13" ry="7" fill="#f59e0b" />
          <path d="M 28 16 Q 34 25 32 35" stroke="#d97706" strokeWidth="2.5" fill="none" />
        </g>
      </svg>

      {/* Foreground Brand Content */}
      <div className="relative z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/90 backdrop-blur-sm border border-emerald-300 text-xs font-bold text-emerald-900 shadow-sm mb-4">
          <Droplets className="size-3.5 text-primary" />
          <span>Jalachakra · ಜಲಚಕ್ರ</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-black text-emerald-950 leading-tight">
          {headline}
        </h2>
        <p className="text-xs sm:text-sm text-emerald-900/85 mt-2 leading-relaxed max-w-sm">
          {subheadline}
        </p>
      </div>

      {/* Bottom Highlights Card */}
      <div className="relative z-10 bg-white/90 backdrop-blur-md border border-emerald-300/80 rounded-2xl p-4 shadow-sm space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-emerald-900">
          <Sparkles className="size-4 text-emerald-600" />
          <span>Research-Backed Farm Intelligence</span>
        </div>
        <p className="text-xs text-muted-foreground leading-normal">
          FAO Penman-Monteith reference ET₀ with localized Karnataka soil physics &amp; crop coefficient tracking.
        </p>
      </div>
    </div>
  );
}
