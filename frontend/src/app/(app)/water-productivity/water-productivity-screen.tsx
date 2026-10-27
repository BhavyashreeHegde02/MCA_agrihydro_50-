"use client";

import Link from "next/link";
import { useState } from "react";
import { Database, Droplets, Info, Sprout } from "lucide-react";

import {
  EconomicProductivityChart,
  ProductivityRankChart,
  WaterValueScatter,
} from "@/components/charts/productivity-charts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SelectField } from "@/components/ui/form-fields";
import { Notice } from "@/components/ui/notice";
import { SectionHeader } from "@/components/ui/section-header";
import { Stat } from "@/components/ui/stat";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { humanMessage } from "@/lib/api/errors";
import {
  useFarms,
  useWaterCoverage,
  useWaterProductivity,
} from "@/lib/api/queries";
import type { WaterProductivityItem } from "@/lib/api/types";
import { LOCALE, formatNumber, humaniseSlug  } from "@/lib/format";

/**
 * Crop per drop.
 *
 * The screen the merged project exists for. The water engine knows what a crop
 * drinks; the district yield record knows what it produced; neither alone can
 * rank crops by what they return per unit of water. This shows that ranking,
 * with the terms behind it and the limits on the evidence stated on the page
 * rather than buried in a report.
 */
export function WaterProductivityScreen() {
  const [scope, setScope] = useState("Karnataka");
  const farms = useFarms();
  const coverage = useWaterCoverage();

  const state = scope === "__all__" ? undefined : scope;
  const productivity = useWaterProductivity({ state });

  const crops = productivity.data?.crops ?? [];
  const leader = crops[0];
  const economicLeader = [...crops]
    .filter((c) => c.ewp_etc_rs_per_m3 != null)
    .sort((a, b) => (b.ewp_etc_rs_per_m3 ?? 0) - (a.ewp_etc_rs_per_m3 ?? 0))[0];

  // Every state that appears among the farmer's own farms, plus Karnataka,
  // which is the region the yield record covers most densely.
  const states = Array.from(
    new Set(
      [
        "Karnataka",
        ...(farms.data ?? []).map((farm) => farm.state).filter(Boolean),
      ] as string[],
    ),
  );

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Crop per drop
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          How much each crop returns for the water it consumes. This is the one
          question neither half of this system can answer alone — it needs the
          FAO-56 water requirement and the district yield record together.
        </p>
      </header>

      <div className="max-w-xs">
        <SelectField
          label="Region"
          hint="Narrows the yield median. Fewer observations, more local."
          options={[
            { value: "__all__", label: "All states" },
            ...states.map((s) => ({ value: s, label: s })),
          ]}
          value={scope}
          onChange={(event) => setScope(event.target.value)}
        />
      </div>

      {productivity.isPending && <LoadingState label="Joining water to yield…" />}

      {productivity.isError && (
        <ErrorState
          message={humanMessage(productivity.error)}
          onRetry={() => productivity.refetch()}
        />
      )}

      {productivity.isSuccess && crops.length === 0 && (
        <Card>
          <CardContent>
            <EmptyState
              icon={Sprout}
              title="No crop has enough history here"
              description="A median needs observations behind it. Try a wider region, or all states."
              action={
                <Button variant="outline" onClick={() => setScope("__all__")}>
                  Show all states
                </Button>
              }
            />
          </CardContent>
        </Card>
      )}

      {productivity.isSuccess && crops.length > 0 && (
        <>
          {productivity.data.fell_back_to_state && (
            <Notice tone="warning" title="Showing the state figure">
              {productivity.data.requested_district} had too little yield
              history to produce a median of its own, so this is the figure for{" "}
              {productivity.data.region}.
            </Notice>
          )}

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Stat
              label="Most crop per drop"
              value={humaniseSlug(leader.crop)}
              tone="primary"
              hint={`${leader.wp_etc_kg_per_m3.toFixed(3)} kg per m³`}
            />
            {economicLeader && (
              <Stat
                label="Most value per drop"
                value={humaniseSlug(economicLeader.crop)}
                tone="ok"
                hint={`₹${economicLeader.ewp_etc_rs_per_m3?.toFixed(2)} per m³`}
              />
            )}
            <Stat
              label="Crops ranked"
              value={crops.length}
              hint={productivity.data.region ?? undefined}
            />
            <Stat
              label="Observations"
              value={crops
                .reduce((sum, crop) => sum + crop.observations, 0)
                .toLocaleString(LOCALE)}
              hint="District-years behind the medians"
            />
          </section>

          {economicLeader && leader.crop !== economicLeader.crop && (
            <Notice tone="info" icon={Info} title="The two rankings disagree">
              <strong>{humaniseSlug(leader.crop)}</strong> turns water into the
              most food — {leader.wp_etc_kg_per_m3.toFixed(3)} kg per cubic
              metre. <strong>{humaniseSlug(economicLeader.crop)}</strong> turns
              it into the most income — ₹
              {economicLeader.ewp_etc_rs_per_m3?.toFixed(2)} per cubic metre.
              They are different questions. If you are growing to eat, follow
              the first; if you are growing to sell, follow the second.
            </Notice>
          )}

          <Card>
            <SectionHeader
              title="Ranked by water"
              description="Both productivities, because they answer different questions."
            />
            <CardContent className="pt-4">
              <ProductivityRankChart crops={crops} />
            </CardContent>
          </Card>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card>
              <SectionHeader
                title="Ranked by value"
                description="At the minimum support price for 2026-27."
              />
              <CardContent className="pt-4">
                <EconomicProductivityChart crops={crops} />
              </CardContent>
            </Card>

            <Card>
              <SectionHeader
                title="The trade-off"
                description="Water demanded against income returned."
              />
              <CardContent className="pt-4">
                <WaterValueScatter crops={crops} />
              </CardContent>
            </Card>
          </div>

          <Card>
            <SectionHeader
              title="Every figure"
              description="The terms behind each ranking, so they can be checked."
              action={
                <Button asChild variant="outline" size="sm">
                  <Link href="/water-budget">
                    <Droplets className="size-4" />
                    Plan a budget
                  </Link>
                </Button>
              }
            />
            <CardContent className="p-0">
              <ProductivityTable crops={crops} />
            </CardContent>
          </Card>

          <Card>
            <SectionHeader
              title="What these numbers are, and are not"
              description="Read this before quoting any of them."
            />
            <CardContent className="space-y-3 pt-4">
              <p className="text-sm text-muted-foreground">
                {productivity.data.interpretation}
              </p>
              <ul className="list-inside list-disc space-y-1.5 text-sm text-muted-foreground">
                {productivity.data.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
              <Notice tone="warning" title="Use the ranking, not the value">
                Because the water and yield terms come from different sources
                and are not observations of the same fields, the order these
                crops fall in is far more defensible than the numbers
                themselves. Treat them as a comparison, not a measurement.
              </Notice>
              {coverage.isSuccess && (
                <details className="rounded-lg border">
                  <summary className="cursor-pointer px-3.5 py-2.5 text-sm font-medium text-foreground">
                    <Database className="mr-1.5 inline size-4" />
                    Where the evidence comes from
                  </summary>
                  <dl className="space-y-2 border-t px-3.5 py-3 text-sm">
                    {Object.entries(coverage.data).map(([name, source]) => (
                      <div key={name}>
                        <dt className="flex items-center gap-2 font-medium text-foreground">
                          {humaniseSlug(name)}
                          <Badge variant={source.available ? "ok" : "danger"}>
                            {source.available
                              ? `${source.rows.toLocaleString(LOCALE)} rows`
                              : "unavailable"}
                          </Badge>
                        </dt>
                        <dd className="mt-0.5 text-muted-foreground">
                          {source.detail}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </details>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function ProductivityTable({ crops }: { crops: WaterProductivityItem[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b text-left text-xs tracking-wide text-muted-foreground uppercase">
          <tr>
            <th scope="col" className="px-4 py-2.5 font-semibold">Crop</th>
            <th scope="col" className="px-4 py-2.5 text-right font-semibold">Yield</th>
            <th scope="col" className="px-4 py-2.5 text-right font-semibold">Season water</th>
            <th scope="col" className="px-4 py-2.5 text-right font-semibold">kg / m³</th>
            <th scope="col" className="px-4 py-2.5 text-right font-semibold">₹ / m³</th>
            <th scope="col" className="px-4 py-2.5 text-right font-semibold">₹ / ha</th>
            <th scope="col" className="px-4 py-2.5 text-right font-semibold">Obs.</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {crops.map((crop) => (
            <tr key={crop.crop} className="hover:bg-muted">
              <td className="px-4 py-2.5 font-medium text-foreground">
                {humaniseSlug(crop.crop)}
              </td>
              <td className="tabular px-4 py-2.5 text-right">
                {formatNumber(crop.yield_kg_ha, 0)} kg/ha
                <span className="block text-xs text-muted-foreground">
                  {formatNumber(crop.yield_p25_kg_ha, 0)}–
                  {formatNumber(crop.yield_p75_kg_ha, 0)}
                </span>
              </td>
              <td className="tabular px-4 py-2.5 text-right">
                {formatNumber(crop.etc_mm, 0)} mm
                <span className="block text-xs text-muted-foreground">
                  {formatNumber(crop.gross_irrigation_mm, 0)} gross
                </span>
              </td>
              <td className="tabular px-4 py-2.5 text-right font-medium">
                {crop.wp_etc_kg_per_m3.toFixed(3)}
                <span className="block text-xs text-muted-foreground">
                  {crop.wp_applied_kg_per_m3.toFixed(3)} pumped
                </span>
              </td>
              <td className="tabular px-4 py-2.5 text-right font-medium">
                {crop.ewp_etc_rs_per_m3 != null
                  ? `₹${crop.ewp_etc_rs_per_m3.toFixed(2)}`
                  : "—"}
              </td>
              <td className="tabular px-4 py-2.5 text-right">
                {crop.revenue_msp_rs_ha != null
                  ? `₹${crop.revenue_msp_rs_ha.toLocaleString(LOCALE)}`
                  : "—"}
              </td>
              <td className="tabular px-4 py-2.5 text-right text-muted-foreground">
                {crop.observations}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="border-t px-4 py-2.5 text-xs text-muted-foreground">
        Yield is the district median with its interquartile range beneath.
        Season water is crop evapotranspiration with gross irrigation beneath —
        the larger figure, because no system delivers everything it pumps.
        Value uses the minimum support price, an annual figure, not a market
        snapshot.
      </p>
    </div>
  );
}
