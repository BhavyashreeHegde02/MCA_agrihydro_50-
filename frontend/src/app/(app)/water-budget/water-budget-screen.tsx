"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { standardSchemaResolver } from "@hookform/resolvers/standard-schema";
import { Calculator, CheckCircle2, Droplets, XCircle } from "lucide-react";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { NumberField, SelectField } from "@/components/ui/form-fields";
import { Notice } from "@/components/ui/notice";
import { SectionHeader } from "@/components/ui/section-header";
import { Stat } from "@/components/ui/stat";
import { LoadingState } from "@/components/ui/states";
import { useFarms, useWaterBudget } from "@/lib/api/queries";
import type { WaterBudgetResponse } from "@/lib/api/types";
import { LOCALE, humaniseSlug  } from "@/lib/format";
import { useApiFormError } from "@/lib/use-api-form";
import { cn } from "@/lib/utils";

/**
 * A number typed into a box, coerced without turning an empty box into a zero.
 */
const positiveNumber = (message: string, max: number) =>
  z
    .union([z.string(), z.number()])
    .refine((value) => value !== "" && value !== null, { message })
    .transform(Number)
    .refine((value) => Number.isFinite(value) && value > 0, { message })
    .refine((value) => value <= max, {
      message: `That is larger than this tool is meant for.`,
    });

/**
 * Litres, not cubic metres, at the point of entry.
 *
 * A farmer knows their borewell in litres per hour and their tank in litres.
 * Asking for cubic metres would push a units conversion onto them at exactly
 * the moment they are most likely to get it wrong by a factor of a thousand.
 * The conversion happens here, once, and the screen shows both.
 */
const budgetSchema = z.object({
  available_litres: positiveNumber("Enter the water you expect to have.", 1e10),
  plot_area_ha: positiveNumber("Enter the area you want to grow on.", 100_000),
  farm_id: z.union([z.string(), z.number(), z.null()]).default(null),
});

type Input = z.input<typeof budgetSchema>;
type Output = z.output<typeof budgetSchema>;

const LITRES_PER_M3 = 1000;

export function WaterBudgetScreen() {
  const farms = useFarms();
  const budget = useWaterBudget();
  const [result, setResult] = useState<WaterBudgetResponse | null>(null);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Input, unknown, Output>({
    resolver: standardSchemaResolver(budgetSchema),
    defaultValues: {
      available_litres: "",
      plot_area_ha: "",
      farm_id: "",
    },
  });
  const { formError, report, clear } = useApiFormError<Input>(setError, [
    "available_litres",
    "plot_area_ha",
  ]);

  async function onSubmit(values: Output) {
    clear();
    try {
      const response = await budget.mutateAsync({
        available_water_m3: values.available_litres / LITRES_PER_M3,
        plot_area_ha: values.plot_area_ha,
        farm_id: values.farm_id ? Number(values.farm_id) : null,
      });
      setResult(response);
    } catch (error) {
      setResult(null);
      report(error);
    }
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      {/* Page Header */}
      <header className="rounded-3xl border border-emerald-200/90 bg-gradient-to-r from-sky-50/70 via-white to-emerald-50/40 p-6 sm:p-8 shadow-xs">
        <div className="flex items-center gap-3.5">
          <div className="size-14 rounded-2xl bg-sky-600 text-white flex items-center justify-center font-bold shadow-md shadow-sky-900/10 shrink-0">
            <Calculator className="size-7" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-sky-800 bg-sky-100/80 px-2.5 py-0.5 rounded-full border border-sky-200">
              Seasonal Planning · ನೀರು ಬಜೆಟ್
            </span>
            <h1 className="text-2xl sm:text-3xl font-black text-foreground mt-1 tracking-tight">
              Water Budget Planner
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5 max-w-xl">
              Know your seasonal water supply? This tool identifies which crops your available water will actually see through full maturity—and what each crop returns per litre invested.
            </p>
          </div>
        </div>
      </header>

      <Card className="rounded-3xl border border-emerald-200/90 bg-white shadow-xs overflow-hidden">
        <SectionHeader
          title="Your Available Water This Season"
          description="Enter the total water you expect to have for the whole season, not per day."
        />
        <CardContent className="pt-4">
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            {formError && (
              <Notice tone="danger" title="Could not work that out">
                {formError}
              </Notice>
            )}

            <div className="grid gap-4 sm:grid-cols-3">
              <NumberField
                label="Water available"
                unit="litres"
                hint="A borewell at 5,000 L/hour for 3 hours a day over 100 days is 1,500,000."
                error={errors.available_litres?.message}
                required
                {...register("available_litres")}
              />
              <NumberField
                label="Area to grow"
                unit="hectares"
                error={errors.plot_area_ha?.message}
                required
                {...register("plot_area_ha")}
              />
              <SelectField
                label="Farm"
                placeholder="Not linked"
                hint="Takes the district from a farm you own."
                options={(farms.data ?? []).map((farm) => ({
                  value: String(farm.id),
                  label: farm.name,
                }))}
                error={undefined}
                {...register("farm_id")}
              />
            </div>

            <Button type="submit" size="lg" loading={isSubmitting} loadingText="Working it out…">
              <Calculator className="size-4" />
              What can I grow?
            </Button>
          </form>
        </CardContent>
      </Card>

      {budget.isPending && isSubmitting && <LoadingState label="Assessing crops…" />}

      {result && <BudgetResult result={result} />}
    </div>
  );
}

function BudgetResult({ result }: { result: WaterBudgetResponse }) {
  const options = result.options ?? [];
  const feasible = options.filter((option) => option.feasible);
  const best = options[0];

  if (options.length === 0) {
    return (
      <Notice tone="warning" title="Nothing to rank">
        {result.note}
      </Notice>
    );
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Your budget"
          value={(result.available_water_m3 * LITRES_PER_M3).toLocaleString(LOCALE)}
          unit="litres"
          hint={`${result.available_water_m3.toLocaleString(LOCALE)} m³ over ${result.plot_area_ha} ha`}
        />
        <Stat
          label="Crops that fit"
          value={`${result.feasible_count} of ${options.length}`}
          tone={result.feasible_count > 0 ? "ok" : "danger"}
          hint="Finish the whole plot on this water"
        />
        {best && (
          <>
            <Stat
              label="Best return"
              value={humaniseSlug(best.crop)}
              tone="primary"
              hint={
                best.expected_value_rs
                  ? `₹${best.expected_value_rs.toLocaleString(LOCALE)} expected`
                  : undefined
              }
            />
            <Stat
              label="On this water"
              value={best.expected_yield_kg.toLocaleString(LOCALE)}
              unit="kg"
              hint={`Over ${best.irrigable_area_ha} ha`}
            />
          </>
        )}
      </section>

      {feasible.length === 0 && (
        <Notice tone="danger" title="This budget will not finish the plot">
          No crop can be watered across the whole {result.plot_area_ha} ha on
          this volume. The options below show the area each one *can* finish —
          growing a smaller area properly is usually better than under-watering
          all of it.
        </Notice>
      )}

      <Card>
        <SectionHeader
          title="What this water will grow"
          description={result.note}
        />
        <CardContent className="space-y-3 pt-4">
          {options.map((option) => (
            <div
              key={option.crop}
              className={cn(
                "rounded-lg border p-3.5",
                option.feasible ? "border-ok/30 bg-ok-surface" : "border-border",
              )}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <p className="flex items-center gap-2 font-medium text-foreground">
                  {option.feasible ? (
                    <CheckCircle2 aria-hidden className="size-4 text-ok" />
                  ) : (
                    <XCircle aria-hidden className="size-4 text-muted-foreground" />
                  )}
                  {humaniseSlug(option.crop)}
                  <Badge variant={option.feasible ? "ok" : "secondary"}>
                    {option.feasible
                      ? "fits"
                      : `${Math.round(option.coverage * 100)}% of the plot`}
                  </Badge>
                </p>
                {option.expected_value_rs != null && (
                  <p className="tabular font-semibold text-foreground">
                    ₹{option.expected_value_rs.toLocaleString(LOCALE)}
                  </p>
                )}
              </div>

              {/* How far the budget stretches, drawn. */}
              <div
                className="mt-2.5 h-2 w-full overflow-hidden rounded-full bg-muted"
                role="img"
                aria-label={`${Math.round(option.coverage * 100)} per cent of the plot`}
              >
                <div
                  className={cn(
                    "h-full rounded-full",
                    option.feasible ? "bg-ok" : "bg-warn",
                  )}
                  style={{ width: `${Math.min(100, option.coverage * 100)}%` }}
                />
              </div>

              <dl className="mt-2.5 grid gap-x-4 gap-y-1 text-sm sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <dt className="text-xs text-muted-foreground">Water needed</dt>
                  <dd className="tabular text-foreground">
                    {(option.water_needed_m3 * LITRES_PER_M3).toLocaleString(LOCALE)} L
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Area it reaches</dt>
                  <dd className="tabular text-foreground">
                    {option.irrigable_area_ha} of {result.plot_area_ha} ha
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Expected harvest</dt>
                  <dd className="tabular text-foreground">
                    {option.expected_yield_kg.toLocaleString(LOCALE)} kg
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Per m³ pumped</dt>
                  <dd className="tabular text-foreground">
                    {option.wp_applied_kg_per_m3.toFixed(3)} kg
                    {option.ewp_applied_rs_per_m3 != null &&
                      ` · ₹${option.ewp_applied_rs_per_m3.toFixed(2)}`}
                  </dd>
                </div>
              </dl>
            </div>
          ))}
        </CardContent>
      </Card>

      <Notice tone="warning" icon={Droplets} title="This is a planning figure">
        Water needed is gross irrigation for a full season, so it already
        includes what your system loses on the way to the root zone. It assumes
        the crop gets no useful rain, which makes it the pessimistic case — any
        rain that falls reduces it. Check the prediction screen during the
        season for the day-to-day figure.
      </Notice>

      {(result.limitations ?? []).length > 0 && (
        <Card>
          <SectionHeader title="What this rests on" />
          <CardContent className="pt-4">
            <ul className="list-inside list-disc space-y-1.5 text-sm text-muted-foreground">
              {(result.limitations ?? []).map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
