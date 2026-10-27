"use client";

import Link from "next/link";
import { useState } from "react";
import { History } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SelectField, TextField } from "@/components/ui/form-fields";
import { SectionHeader } from "@/components/ui/section-header";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { humanMessage } from "@/lib/api/errors";
import { useAllPlantings, useHistory } from "@/lib/api/queries";
import { formatDate, formatDepth, humaniseSlug } from "@/lib/format";

export function HistoryScreen() {
  const [fieldCropId, setFieldCropId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const plantings = useAllPlantings(false);
  const history = useHistory({
    field_crop_id: fieldCropId ? Number(fieldCropId) : undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    limit: 200,
  });

  const filtered = Boolean(fieldCropId || startDate || endDate);

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      {/* Page Header */}
      <header className="rounded-3xl border border-emerald-200/90 bg-gradient-to-r from-emerald-50/70 via-white to-sky-50/30 p-6 sm:p-8 shadow-xs">
        <div className="flex items-center gap-3.5">
          <div className="size-14 rounded-2xl bg-primary text-white flex items-center justify-center font-bold shadow-md shadow-emerald-900/10 shrink-0">
            <History className="size-7" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-100/80 px-2.5 py-0.5 rounded-full border border-emerald-300">
              Water Decision Log · ನೀರಾವರಿ ಇತಿಹಾಸ
            </span>
            <h1 className="text-2xl sm:text-3xl font-black text-foreground mt-1 tracking-tight">
              Water Need History
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5 max-w-xl">
              Every prediction is stored with the weather and assumptions it used—so you can trace exactly why each calculation said what it said.
            </p>
          </div>
        </div>
      </header>

      <Card className="rounded-3xl border border-emerald-200/90 bg-white shadow-xs overflow-hidden">
        <SectionHeader title="Filter Predictions" divided={false} description="Narrow your history by crop planting or date range." />
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            <SelectField
              label="Planting"
              placeholder="All plantings"
              options={(plantings.data ?? []).map((planting) => ({
                value: String(planting.id),
                label: `${planting.crop_name} — ${planting.field_name}`,
              }))}
              value={fieldCropId}
              onChange={(event) => setFieldCropId(event.target.value)}
            />
            <TextField
              label="From"
              type="date"
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
            />
            <TextField
              label="To"
              type="date"
              value={endDate}
              onChange={(event) => setEndDate(event.target.value)}
            />
          </div>
          {filtered && (
            <Button
              variant="ghost"
              size="sm"
              className="mt-3"
              onClick={() => {
                setFieldCropId("");
                setStartDate("");
                setEndDate("");
              }}
            >
              Clear filters
            </Button>
          )}
        </CardContent>
      </Card>

      {history.isPending && <LoadingState label="Loading predictions…" />}

      {history.isError && (
        <ErrorState
          message={humanMessage(history.error)}
          onRetry={() => history.refetch()}
        />
      )}

      {history.isSuccess && history.data.length === 0 && (
        <Card className="rounded-3xl border border-emerald-200">
          <CardContent className="p-8">
            <EmptyState
              icon={History}
              title={filtered ? "Nothing matches those filters" : "No water predictions yet"}
              description={
                filtered
                  ? "Try widening the date range, or clear the filters to see everything."
                  : "Once you run a water prediction it is stored here with the exact weather and model inputs it used."
              }
              action={
                filtered ? (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setFieldCropId("");
                      setStartDate("");
                      setEndDate("");
                    }}
                  >
                    Clear filters
                  </Button>
                ) : (
                  <Button asChild>
                    <Link href="/predict">Make the first one</Link>
                  </Button>
                )
              }
            />
          </CardContent>
        </Card>
      )}

      {history.isSuccess && history.data.length > 0 && (
        <Card className="rounded-3xl border border-emerald-200/90 bg-white shadow-xs overflow-hidden">
          <SectionHeader
            title={`${history.data.length} Water Prediction${history.data.length === 1 ? "" : "s"} on Record`}
            description="Newest first. Click a date to view the full calculation breakdown and agronomic explanation."
          />
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-emerald-100 bg-emerald-50/80 text-left text-xs tracking-wide text-emerald-950 font-bold uppercase">
                  <tr>
                    <th scope="col" className="px-4 py-2.5 font-bold">Date</th>
                    <th scope="col" className="px-4 py-2.5 font-bold">Growth Stage</th>
                    <th scope="col" className="px-4 py-2.5 text-right font-bold">Kc</th>
                    <th scope="col" className="px-4 py-2.5 text-right font-bold">ET₀</th>
                    <th scope="col" className="px-4 py-2.5 text-right font-bold">Demand (ETc)</th>
                    <th scope="col" className="px-4 py-2.5 text-right font-bold">Net Irr.</th>
                    <th scope="col" className="px-4 py-2.5 text-right font-bold">Gross Irr.</th>
                    <th scope="col" className="px-4 py-2.5 font-bold">Source</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-emerald-100">
                  {history.data.map((row) => (
                    <tr key={row.id} className="hover:bg-emerald-50/40 transition-colors">
                      <td className="px-4 py-2.5">
                        <Link
                          href={`/predictions/${row.id}`}
                          className="font-medium text-primary underline underline-offset-2"
                        >
                          {formatDate(row.prediction_date)}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5 text-muted-foreground">
                        {humaniseSlug(row.growth_stage)}
                      </td>
                      <td className="tabular px-4 py-2.5 text-right">
                        {row.kc_value.toFixed(2)}
                      </td>
                      <td className="tabular px-4 py-2.5 text-right">
                        {formatDepth(row.et0_mm_day)}
                      </td>
                      <td className="tabular px-4 py-2.5 text-right font-medium">
                        {formatDepth(row.cwr_mm_day)}
                      </td>
                      <td className="tabular px-4 py-2.5 text-right">
                        {formatDepth(row.net_irrigation_mm)}
                      </td>
                      <td className="tabular px-4 py-2.5 text-right">
                        {formatDepth(row.gross_irrigation_mm)}
                      </td>
                      <td className="px-4 py-2.5">
                        <Badge
                          variant={
                            row.prediction_source === "ml_model" ? "info" : "secondary"
                          }
                        >
                          {row.prediction_source === "ml_model" ? "model" : "baseline"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="border-t border-emerald-100 bg-emerald-50/30 px-4 py-3 text-xs text-muted-foreground">
              <strong className="text-foreground">Column guide:</strong> ET₀ and demand (ETc) are daily mm; Net and Gross are single-application mm. Gross is always larger—no system delivers 100% of what it pumps. Gross ÷ field area = pump litres needed.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
