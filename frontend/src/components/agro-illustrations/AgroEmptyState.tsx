"use client";

import { Droplets, Plus, Sprout, Waves } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

interface AgroEmptyStateProps {
  type?: "farms" | "crops" | "predictions" | "advisory" | "irrigation" | "general";
  title: string;
  description: string;
  actionHref?: string;
  actionLabel?: string;
  className?: string;
}

export function AgroEmptyState({
  type = "general",
  title,
  description,
  actionHref,
  actionLabel,
  className = "",
}: AgroEmptyStateProps) {
  return (
    <div
      className={`rounded-3xl border-2 border-dashed border-emerald-200/80 bg-gradient-to-b from-emerald-50/40 via-white to-amber-50/20 p-8 sm:p-12 text-center max-w-xl mx-auto shadow-sm ${className}`}
    >
      {/* Illustrated Field / Plant Graphic */}
      <div className="relative size-24 mx-auto mb-5 rounded-3xl bg-gradient-to-tr from-emerald-100 to-amber-100/60 border border-emerald-200 flex items-center justify-center shadow-inner">
        <svg viewBox="0 0 100 100" className="size-16" xmlns="http://www.w3.org/2000/svg">
          {/* Soil Mound */}
          <ellipse cx="50" cy="80" rx="35" ry="12" fill="#8d6e63" opacity="0.85" />
          <ellipse cx="50" cy="82" rx="25" ry="8" fill="#6d4c41" />
          {/* Sprouting Leaves */}
          <path d="M 50 78 Q 45 45 30 35 Q 40 38 48 55" fill="#66bb6a" stroke="#2e7d32" strokeWidth="1" />
          <path d="M 50 78 Q 55 42 70 32 Q 60 36 52 54" fill="#81c784" stroke="#2e7d32" strokeWidth="1" />
          <path d="M 50 78 L 50 30" stroke="#2e7d32" strokeWidth="2.5" strokeLinecap="round" />
          <circle cx="50" cy="26" r="4.5" fill="#fde047" />
          {/* Water Drop falling */}
          <path d="M 50 10 C 47 15 44 19 44 21 C 44 24 47 26 50 26 C 53 26 56 24 56 21 C 56 19 53 15 50 10 Z" fill="#38bdf8" />
        </svg>

        {/* Small floating sparkles badge */}
        <div className="absolute -top-1 -right-1 size-7 rounded-full bg-primary text-white flex items-center justify-center shadow-md">
          <Droplets className="size-3.5" />
        </div>
      </div>

      <h3 className="text-xl sm:text-2xl font-bold text-foreground">
        {title}
      </h3>

      <p className="mt-2 text-sm text-muted-foreground leading-relaxed max-w-md mx-auto">
        {description}
      </p>

      {actionHref && actionLabel && (
        <div className="mt-6">
          <Button asChild size="lg" className="rounded-xl px-6 font-semibold shadow-md">
            <Link href={actionHref}>
              <Plus className="size-4 mr-1.5" />
              {actionLabel}
            </Link>
          </Button>
        </div>
      )}
    </div>
  );
}
