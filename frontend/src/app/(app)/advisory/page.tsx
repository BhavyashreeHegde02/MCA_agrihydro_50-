import type { Metadata } from "next";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Droplets,
  Lightbulb,
  Sparkles,
  Sprout,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Notice } from "@/components/ui/notice";
import { AgroEmptyState } from "@/components/agro-illustrations/AgroEmptyState";
import { rscGet } from "@/lib/api/rsc";
import type { AdvisoryListResponse } from "@/lib/api/types";
import { formatDate, priorityTone, toneBadge } from "@/lib/format";

export const metadata: Metadata = { title: "Farmer Advisory — Jalachakra" };

export default async function AdvisoryPage() {
  const advisory = await rscGet<AdvisoryListResponse>("/api/v1/advisory", {
    limit: 50,
  });

  const items = advisory.advisories ?? [];
  const needsAction = items.filter((item) => item.action_required);
  const rest = items.filter((item) => !item.action_required);

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-10">
      {/* Header */}
      <header className="rounded-3xl border border-emerald-200/90 bg-gradient-to-r from-amber-50/70 via-white to-emerald-50/50 p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="size-14 rounded-2xl bg-amber-500 text-white flex items-center justify-center font-bold shadow-md shadow-amber-900/10 shrink-0">
              <Lightbulb className="size-7" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-amber-800 bg-amber-100/80 px-2.5 py-0.5 rounded-full border border-amber-300">
                Actionable Field Guidance · ಕೃಷಿ ಸಲಹೆಗಳು
              </span>
              <h1 className="text-2xl sm:text-3xl font-black text-foreground mt-1 tracking-tight">
                Farmer Advisory
              </h1>
              <p className="text-xs sm:text-sm text-muted-foreground mt-0.5 max-w-xl">
                What your daily predictions mean in plain instructions—written as field tasks, not raw statistical models.
              </p>
            </div>
          </div>

          {items.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              {needsAction.length > 0 && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-100 text-amber-900 text-xs font-bold border border-amber-300">
                  <AlertTriangle className="size-3.5 text-amber-600" />
                  <span>{needsAction.length} Action Needed</span>
                </div>
              )}
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-100 text-emerald-900 text-xs font-bold border border-emerald-300">
                <BookOpen className="size-3.5 text-primary" />
                <span>{rest.length} Informational</span>
              </div>
            </div>
          )}
        </div>
      </header>

      {items.length === 0 ? (
        <AgroEmptyState
          type="advisory"
          title="No Field Advisories Yet"
          description="Advisories are generated automatically whenever you calculate crop water requirements. Run a prediction to see immediate field guidance."
          actionHref="/predict"
          actionLabel="Calculate Crop Water Need"
        />
      ) : (
        <div className="space-y-8">
          {/* Urgent / Needs Action Section */}
          {needsAction.length > 0 && (
            <section className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="size-2.5 rounded-full bg-amber-500 animate-pulse" />
                <h2 className="text-lg font-black uppercase tracking-wider text-amber-900">
                  Needs Your Immediate Field Action ({needsAction.length})
                </h2>
              </div>

              <div className="space-y-3.5">
                {needsAction.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-3xl border-2 border-amber-300 bg-amber-50/40 p-5 sm:p-6 shadow-xs transition-all hover:shadow-md"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div className="flex items-start gap-3.5">
                        <div className="size-10 rounded-xl bg-amber-500 text-white flex items-center justify-center shrink-0 mt-0.5 shadow-xs font-bold">
                          <AlertTriangle className="size-5" />
                        </div>
                        <div>
                          <h3 className="font-bold text-base sm:text-lg text-foreground">
                            {item.headline}
                          </h3>
                          {item.detail && (
                            <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                              {item.detail}
                            </p>
                          )}
                        </div>
                      </div>
                      <Badge variant={toneBadge(priorityTone(item.priority))} className="shrink-0 text-xs font-bold self-start">
                        {item.priority}
                      </Badge>
                    </div>

                    <div className="mt-4 pt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground border-t border-amber-200/80">
                      <span className="flex items-center gap-1 font-bold text-foreground">
                        <Sprout className="size-3.5 text-primary" />
                        {item.crop}
                      </span>
                      <span>•</span>
                      <Link
                        href={`/predictions/${item.prediction_id}`}
                        className="text-primary hover:underline font-bold inline-flex items-center gap-1"
                      >
                        <span>Prediction Date: {formatDate(item.prediction_date)}</span>
                        <ArrowRight className="size-3" />
                      </Link>
                      <span>•</span>
                      <span className="capitalize">{item.advisory_type.replace(/_/g, " ")}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Informational Guidance Section */}
          {rest.length > 0 && (
            <section className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="size-2.5 rounded-full bg-primary" />
                <h2 className="text-lg font-black uppercase tracking-wider text-emerald-950">
                  Field Observations &amp; Soil Water Status ({rest.length})
                </h2>
              </div>

              <div className="space-y-3.5">
                {rest.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-3xl border border-emerald-200/90 bg-white p-5 sm:p-6 shadow-xs transition-all hover:border-emerald-300 hover:shadow-md"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div className="flex items-start gap-3.5">
                        <div className="size-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0 mt-0.5 font-bold">
                          <CheckCircle2 className="size-5 text-primary" />
                        </div>
                        <div>
                          <h3 className="font-bold text-base text-foreground">
                            {item.headline}
                          </h3>
                          {item.detail && (
                            <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                              {item.detail}
                            </p>
                          )}
                        </div>
                      </div>
                      <Badge variant={toneBadge(priorityTone(item.priority))} className="shrink-0 text-xs font-bold self-start">
                        {item.priority}
                      </Badge>
                    </div>

                    <div className="mt-4 pt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground border-t border-emerald-100">
                      <span className="flex items-center gap-1 font-bold text-foreground">
                        <Sprout className="size-3.5 text-primary" />
                        {item.crop}
                      </span>
                      <span>•</span>
                      <Link
                        href={`/predictions/${item.prediction_id}`}
                        className="text-primary hover:underline font-bold inline-flex items-center gap-1"
                      >
                        <span>Calculation: {formatDate(item.prediction_date)}</span>
                        <ArrowRight className="size-3" />
                      </Link>
                      <span>•</span>
                      <span className="capitalize">{item.advisory_type.replace(/_/g, " ")}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          <Notice tone="info" title="Scientific Transparency & Calibration">
            Every advisory item is produced against the FAO Penman-Monteith reference and your field&apos;s specific irrigation application efficiency. Select any date link to view full calculation lineage and model interval bounds.
          </Notice>
        </div>
      )}
    </div>
  );
}
