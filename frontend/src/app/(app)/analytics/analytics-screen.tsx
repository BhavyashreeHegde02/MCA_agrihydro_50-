"use client";

import Link from "next/link";
import { useState } from "react";
import { BarChart3, Info } from "lucide-react";

import {
  DemandTrendChart,
  IrrigationVersusRainChart,
  StageDemandChart,
} from "@/components/charts/water-charts";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SelectField } from "@/components/ui/form-fields";
import { Notice } from "@/components/ui/notice";
import { SectionHeader } from "@/components/ui/section-header";
import { Stat } from "@/components/ui/stat";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { api } from "@/lib/api/client";
import { humanMessage } from "@/lib/api/errors";
import { keys, useAllPlantings } from "@/lib/api/queries";
import type {
  AnalyticsDailyPoint,
  AnalyticsOut,
  AnalyticsStageTotal,
} from "@/lib/api/types";
import { formatDate, formatDepth } from "@/lib/format";
import { useQuery } from "@tanstack/react-query";

export function AnalyticsScreen() {
  const [fieldCropId, setFieldCropId] = useState<string>("");
  const plantings = useAllPlantings(false);

  const params = fieldCropId ? { field_crop_id: Number(fieldCropId) } : {};
  const analytics = useQuery({
    queryKey: keys.analytics(params),
    queryFn: () => api.get<AnalyticsOut>("analytics/cwr", { query: params }),
  });

  // The backend types these two as `list[dict[str, Any]]`, so OpenAPI gives
  // them no shape. The element types are written by hand in types.ts from the
  // handler source; the cast through unknown is what acknowledges that.
  const series = (analytics.data?.daily_series ??
    []) as unknown as AnalyticsDailyPoint[];
  const stages = (analytics.data?.by_growth_stage ??
    []) as unknown as AnalyticsStageTotal[];
  const balance = analytics.data?.balance_mm ?? 0;

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      {/* Page Header */}
      <header className="rounded-3xl border border-emerald-200/90 bg-gradient-to-r from-emerald-50/70 via-white to-sky-50/30 p-6 sm:p-8 shadow-xs">
        <div className="flex items-center gap-3.5">
          <div className="size-14 rounded-2xl bg-emerald-700 text-white flex items-center justify-center font-bold shadow-md shadow-emerald-900/10 shrink-0">
            <BarChart3 className="size-7" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-100/80 px-2.5 py-0.5 rounded-full border border-emerald-300">
              Research & Analytics · ಸಂಶೋಧನಾ ವಿಶ್ಲೇಷಣೆ
            </span>
            <h1 className="text-2xl sm:text-3xl font-black text-foreground mt-1 tracking-tight">
              Crop Water Analytics
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5 max-w-xl">
              What your crops have needed, how rainfall has credited the root zone, and how demand compares to what was actually applied—trended across the full growing season.
            </p>
          </div>
        </div>
      </header>

      {plantings.isSuccess && plantings.data.length > 0 && (
        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-emerald-200/80 bg-white p-4 shadow-xs">
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-800">Filter by Planting</span>
          <div className="max-w-xs flex-1">
            <SelectField
              label=""
              placeholder="All plantings"
              options={plantings.data.map((planting) => ({
                value: String(planting.id),
                label: `${planting.crop_name} — ${planting.field_name}`,
              }))}
              value={fieldCropId}
              onChange={(event) => setFieldCropId(event.target.value)}
            />
          </div>
        </div>
      )}

      {analytics.isPending && <LoadingState label="Loading analytics…" />}

      {analytics.isError && (
        <ErrorState
          message={humanMessage(analytics.error)}
          onRetry={() => analytics.refetch()}
        />
      )}

      {analytics.isSuccess && analytics.data.predictions === 0 && (
        <Card>
          <CardContent>
            <EmptyState
              icon={BarChart3}
              title="Nothing to analyse yet"
              description="Analytics are built from stored predictions. Make a few and the trends will appear here."
              action={
                <Button asChild>
                  <Link href="/predict">Predict water demand</Link>
                </Button>
              }
            />
          </CardContent>
        </Card>
      )}

      {analytics.isSuccess && analytics.data.predictions > 0 && (
        <>
          <section
            aria-label="Totals"
            className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
          >
            <Stat
              label="Predictions"
              value={analytics.data.predictions}
              hint={
                analytics.data.period_start && analytics.data.period_end
                  ? `${formatDate(analytics.data.period_start)} – ${formatDate(analytics.data.period_end)}`
                  : undefined
              }
            />
            <Stat
              label="Total demand"
              value={formatDepth(analytics.data.total_predicted_demand_mm)}
              unit="mm"
              tone="primary"
              hint="Summed crop transpiration"
            />
            <Stat
              label="Gross irrigation needed"
              value={formatDepth(analytics.data.total_gross_irrigation_mm)}
              unit="mm"
              hint="What should have been delivered"
            />
            <Stat
              label="Water you applied"
              value={formatDepth(analytics.data.total_water_applied_mm)}
              unit="mm"
              tone={
                Math.abs(balance) < 5 ? "ok" : balance > 0 ? "warn" : "danger"
              }
              hint={
                balance > 0
                  ? `${formatDepth(balance)} mm more than needed`
                  : balance < 0
                    ? `${formatDepth(Math.abs(balance))} mm less than needed`
                    : "Matches the requirement"
              }
            />
          </section>

          <Notice tone="info" icon={Info} title="How to read the balance">
            {analytics.data.note}
          </Notice>

          <Card>
            <SectionHeader
              title="Demand over time"
              description="Predicted demand against the FAO-56 reference, with the model's uncertainty."
            />
            <CardContent className="pt-4">
              <DemandTrendChart series={series} />
            </CardContent>
          </Card>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card>
              <SectionHeader
                title="Supply"
                description="Where the crop's water came from."
              />
              <CardContent className="pt-4">
                <IrrigationVersusRainChart series={series} />
              </CardContent>
            </Card>

            <Card>
              <SectionHeader
                title="By growth stage"
                description="Why the same weather produces different demand."
              />
              <CardContent className="pt-4">
                {stages.length > 0 ? (
                  <StageDemandChart stages={stages} />
                ) : (
                  <EmptyState
                    title="Not enough stages yet"
                    description="Predictions have so far only covered one growth stage."
                  />
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <SectionHeader
              title="Stage totals"
              description="The same figures as the chart, exactly."
            />
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b text-left text-xs tracking-wide text-muted-foreground uppercase">
                    <tr>
                      <th scope="col" className="px-4 py-2.5 font-semibold">Stage</th>
                      <th scope="col" className="px-4 py-2.5 text-right font-semibold">Days</th>
                      <th scope="col" className="px-4 py-2.5 text-right font-semibold">Mean demand</th>
                      <th scope="col" className="px-4 py-2.5 text-right font-semibold">Total demand</th>
                      <th scope="col" className="px-4 py-2.5 text-right font-semibold">Gross irrigation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {stages.map((stage) => (
                      <tr key={stage.growth_stage}>
                        <td className="px-4 py-2.5 font-medium text-foreground">
                          {stage.growth_stage.replace(/_/g, " ")}
                        </td>
                        <td className="tabular px-4 py-2.5 text-right">{stage.days}</td>
                        <td className="tabular px-4 py-2.5 text-right">
                          {formatDepth(stage.mean_demand_mm_day)} mm/day
                        </td>
                        <td className="tabular px-4 py-2.5 text-right">
                          {formatDepth(stage.total_demand_mm)} mm
                        </td>
                        <td className="tabular px-4 py-2.5 text-right">
                          {formatDepth(stage.total_gross_irrigation_mm)} mm
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
