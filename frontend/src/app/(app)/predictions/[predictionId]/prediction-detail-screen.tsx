"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { standardSchemaResolver } from "@hookform/resolvers/standard-schema";
import { ArrowLeft, Brain, Calculator, Droplets } from "lucide-react";
import type { z } from "zod";

import { IrrigationBreakdown } from "@/components/irrigation-breakdown";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { NumberField } from "@/components/ui/form-fields";
import { Notice } from "@/components/ui/notice";
import { SectionHeader } from "@/components/ui/section-header";
import { Stat } from "@/components/ui/stat";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { humanMessage } from "@/lib/api/errors";
import {
  useCalculateIrrigation,
  useExplanation,
  usePrediction,
} from "@/lib/api/queries";
import type {
  BaselineComparison,
  ExplanationContributor,
  IrrigationCalculationOut,
} from "@/lib/api/types";
import {
  formatDate,
  formatDepth,
  formatLitres,
  formatPercent,
  humaniseSlug,
  priorityTone,
  toneBadge,
} from "@/lib/format";
import { useApiFormError } from "@/lib/use-api-form";
import { irrigationCalcSchema } from "@/lib/validation/schemas";

export function PredictionDetailScreen({
  predictionId,
}: {
  predictionId: number;
}) {
  const prediction = usePrediction(predictionId);
  const explanation = useExplanation(predictionId);

  return (
    <div className="space-y-6">
      <Link
        href="/predictions"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-primary"
      >
        <ArrowLeft className="size-4" />
        All predictions
      </Link>

      {prediction.isPending && <LoadingState label="Loading the prediction…" />}

      {prediction.isError && (
        <ErrorState
          message={humanMessage(prediction.error)}
          onRetry={() => prediction.refetch()}
        />
      )}

      {prediction.isSuccess && (
        <>
          <header className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">
                {prediction.data.crop_name ?? "Prediction"} —{" "}
                {formatDate(prediction.data.prediction_date)}
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                {humaniseSlug(prediction.data.growth_stage)}, day{" "}
                {prediction.data.days_after_sowing} after sowing, Kc{" "}
                {prediction.data.kc_value.toFixed(2)}
              </p>
            </div>
            <Badge
              variant={
                prediction.data.prediction_source === "ml_model"
                  ? "info"
                  : "secondary"
              }
            >
              {prediction.data.prediction_source === "ml_model"
                ? "ML model"
                : "Physics baseline"}
            </Badge>
          </header>

          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Stat
              label="ET₀ reference"
              value={formatDepth(prediction.data.et0_mm_day)}
              unit="mm/day"
            />
            <Stat
              label="Crop demand"
              value={formatDepth(prediction.data.cwr_mm_day)}
              unit="mm/day"
              tone="primary"
            />
            <Stat
              label="Net irrigation"
              value={formatDepth(prediction.data.net_irrigation_mm)}
              unit="mm"
              hint="Must reach the roots"
            />
            <Stat
              label="Gross irrigation"
              value={formatDepth(prediction.data.gross_irrigation_mm)}
              unit="mm"
              hint={`Must be delivered · ${formatPercent(prediction.data.application_efficiency)} efficient`}
            />
          </section>

          {prediction.data.cwr_lower_mm_day !== null &&
            prediction.data.cwr_upper_mm_day !== null && (
              <Notice tone="info" title="Uncertainty range">
                The model puts the true demand between{" "}
                <strong>
                  {formatDepth(prediction.data.cwr_lower_mm_day)} and{" "}
                  {formatDepth(prediction.data.cwr_upper_mm_day)} mm/day
                </strong>
                {prediction.data.interval_coverage !== null &&
                  `, with ${formatPercent(prediction.data.interval_coverage)} coverage`}
                . That interval was calibrated on held-out data and its coverage
                was measured, not assumed.
              </Notice>
            )}

          <Tabs defaultValue="calculation">
            <TabsList>
              <TabsTrigger value="calculation">
                <Calculator className="size-4" />
                Calculation
              </TabsTrigger>
              <TabsTrigger value="explanation">
                <Brain className="size-4" />
                Why this number
              </TabsTrigger>
              <TabsTrigger value="recalculate">
                <Droplets className="size-4" />
                Try other assumptions
              </TabsTrigger>
            </TabsList>

            <TabsContent value="calculation" className="mt-4">
              <Card>
                <SectionHeader
                  title="From weather to water"
                  description="Each step with its arithmetic, so the final figure can be checked rather than trusted."
                />
                <CardContent className="pt-4">
                  <IrrigationBreakdown
                    inputs={{
                      et0MmDay: prediction.data.et0_mm_day,
                      kc: prediction.data.kc_value,
                      cwrMmDay: prediction.data.cwr_mm_day,
                      effectiveRainfallMm: prediction.data.effective_rainfall_mm,
                      netIrrigationMm: prediction.data.net_irrigation_mm,
                      grossIrrigationMm: prediction.data.gross_irrigation_mm,
                      applicationEfficiency:
                        prediction.data.application_efficiency,
                      grossIrrigationLitres:
                        prediction.data.gross_irrigation_litres,
                    }}
                  />
                </CardContent>
              </Card>

              {prediction.data.advisories.length > 0 && (
                <Card className="mt-6">
                  <SectionHeader title="What to do" />
                  <CardContent className="pt-4">
                    <ul className="space-y-3">
                      {prediction.data.advisories.map((advisory, index) => (
                        <li
                          key={`${advisory.advisory_type}-${index}`}
                          className="rounded-lg border p-3"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <p className="font-medium text-foreground">
                              {advisory.headline}
                            </p>
                            <Badge variant={toneBadge(priorityTone(advisory.priority))}>
                              {advisory.priority}
                            </Badge>
                          </div>
                          <p className="mt-1 text-sm text-muted-foreground">
                            {advisory.detail}
                          </p>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="explanation" className="mt-4">
              <ExplanationPanel
                predictionId={predictionId}
                query={explanation}
              />
            </TabsContent>

            <TabsContent value="recalculate" className="mt-4">
              <RecalculatePanel
                predictionId={predictionId}
                currentEfficiency={prediction.data.application_efficiency}
              />
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

function ExplanationPanel({
  predictionId,
  query,
}: {
  predictionId: number;
  query: ReturnType<typeof useExplanation>;
}) {
  if (query.isPending) return <LoadingState label="Loading the explanation…" />;
  if (query.isError) {
    return (
      <ErrorState
        message={humanMessage(query.error)}
        onRetry={() => query.refetch()}
      />
    );
  }

  const data = query.data;
  const comparison = data.baseline_comparison as BaselineComparison | null;
  const contributors = (data.contributors ??
    []) as unknown as ExplanationContributor[];

  return (
    <div className="space-y-6">
      {comparison && (
        <Card>
          <SectionHeader
            title="Against the physics reference"
            description="The FAO-56 calculation is recomputed on every request, whether or not a model is used."
          />
          <CardContent className="space-y-3 pt-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <Stat
                label="Reference"
                value={formatDepth(comparison.baseline_cwr_mm_day)}
                unit="mm/day"
              />
              <Stat
                label="Served"
                value={formatDepth(comparison.served_cwr_mm_day)}
                unit="mm/day"
                tone="primary"
              />
              <Stat
                label="Difference"
                value={formatDepth(comparison.difference_mm_day)}
                unit="mm/day"
                tone={
                  Math.abs(comparison.difference_mm_day) > 1 ? "warn" : "ok"
                }
              />
            </div>
            <p className="text-sm text-muted-foreground">{comparison.note}</p>
          </CardContent>
        </Card>
      )}

      {!data.available ? (
        <Notice tone="info" title="No model explanation for this prediction">
          {data.reason ??
            "This prediction did not come from a trained model, so there is no learned behaviour to explain."}
        </Notice>
      ) : (
        <Card>
          <SectionHeader
            title="What the model relies on"
            description={data.method ?? undefined}
          />
          <CardContent className="space-y-4 pt-4">
            <ul className="space-y-2.5">
              {contributors.map((contributor) => (
                <li key={contributor.feature}>
                  <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                    <p className="font-medium text-foreground">
                      {contributor.meaning}
                    </p>
                    <p className="tabular text-sm text-muted-foreground">
                      today: <strong className="text-foreground">
                        {contributor.value_today === null
                          ? "—"
                          : String(contributor.value_today)}
                      </strong>
                    </p>
                  </div>
                  <div className="mt-1.5 flex items-center gap-2">
                    <div
                      className="h-2 flex-1 overflow-hidden rounded-full bg-muted"
                      role="img"
                      aria-label={`${formatPercent(contributor.relative_importance)} of the model's reliance`}
                    >
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{
                          width: `${Math.min(100, contributor.relative_importance * 100)}%`,
                        }}
                      />
                    </div>
                    <span className="tabular w-12 text-right text-xs text-muted-foreground">
                      {formatPercent(contributor.relative_importance)}
                    </span>
                  </div>
                </li>
              ))}
            </ul>

            {data.note && (
              <Notice tone="warning" title="Read this carefully">
                {data.note}
              </Notice>
            )}
          </CardContent>
        </Card>
      )}

      <p className="text-xs text-muted-foreground">
        Prediction #{predictionId}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------

type CalcInput = z.input<typeof irrigationCalcSchema>;
type CalcOutput = z.output<typeof irrigationCalcSchema>;

function RecalculatePanel({
  predictionId,
  currentEfficiency,
}: {
  predictionId: number;
  currentEfficiency: number;
}) {
  const calculate = useCalculateIrrigation();
  const [result, setResult] = useState<IrrigationCalculationOut | null>(null);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<CalcInput, unknown, CalcOutput>({
    resolver: standardSchemaResolver(irrigationCalcSchema),
    defaultValues: {
      irrigation_efficiency: "",
      forecast_rainfall_mm: "",
      area_ha: "",
    },
  });
  const { formError, report, clear } = useApiFormError<CalcInput>(setError, [
    "irrigation_efficiency",
    "forecast_rainfall_mm",
    "area_ha",
  ]);

  async function onSubmit(values: CalcOutput) {
    clear();
    try {
      const response = await calculate.mutateAsync({
        prediction_id: predictionId,
        ...values,
      });
      setResult(response);
    } catch (error) {
      setResult(null);
      report(error);
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <SectionHeader
          title="What if the assumptions were different?"
          description="The crop's demand does not change — but what you must deliver does, if rain is coming or your system is less efficient than assumed."
        />
        <CardContent className="pt-4">
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            {formError && (
              <Notice tone="danger" title="Could not recalculate">
                {formError}
              </Notice>
            )}
            <div className="grid gap-4 sm:grid-cols-3">
              <NumberField
                label="Application efficiency"
                unit="0 to 1"
                hint={`Currently ${formatPercent(currentEfficiency)}`}
                error={errors.irrigation_efficiency?.message}
                {...register("irrigation_efficiency")}
              />
              <NumberField
                label="Rain expected"
                unit="mm"
                hint="Credited against what you apply"
                error={errors.forecast_rainfall_mm?.message}
                {...register("forecast_rainfall_mm")}
              />
              <NumberField
                label="Area"
                unit="hectares"
                hint="For the litre figure"
                error={errors.area_ha?.message}
                {...register("area_ha")}
              />
            </div>
            <Button type="submit" loading={isSubmitting} loadingText="Calculating…">
              <Calculator className="size-4" />
              Recalculate
            </Button>
          </form>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <SectionHeader
            title="Under those assumptions"
            description="Recomputed by the backend from the stored prediction, not adjusted in the browser."
          />
          <CardContent className="space-y-4 pt-4">
            <IrrigationBreakdown
              inputs={{
                // ET0 and Kc are deliberately absent: this endpoint
                // recalculates irrigation from the stored demand, so the
                // derivation steps would only restate what the prediction
                // above already established.
                cwrMmDay: result.cwr_mm_day,
                effectiveRainfallMm: result.effective_rainfall_mm,
                forecastRainfallMm: result.forecast_rainfall_mm,
                netIrrigationMm: result.net_irrigation_mm,
                grossIrrigationMm: result.gross_irrigation_mm,
                applicationEfficiency: result.application_efficiency,
                grossIrrigationLitres: result.gross_irrigation_litres,
              }}
            />
            {result.assumptions.length > 0 && (
              <div>
                <p className="mb-1.5 text-sm font-medium text-foreground">
                  Assumptions used
                </p>
                <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                  {result.assumptions.map((assumption, index) => (
                    <li key={index}>{String(assumption)}</li>
                  ))}
                </ul>
              </div>
            )}
            {result.gross_irrigation_litres !== null &&
              result.gross_irrigation_litres !== undefined && (
                <Notice tone="success" title="At the pump">
                  {formatLitres(result.gross_irrigation_litres)} litres.
                </Notice>
              )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
