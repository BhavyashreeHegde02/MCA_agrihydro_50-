"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { standardSchemaResolver } from "@hookform/resolvers/standard-schema";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  CloudRain,
  CloudSun,
  Droplets,
  Info,
  MapPin,
  PencilLine,
  RotateCcw,
  Sprout,
} from "lucide-react";
import { z } from "zod";

import { PredictionResult } from "@/components/prediction-result";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { Notice } from "@/components/ui/notice";
import { NumberField, TextField } from "@/components/ui/form-fields";
import { humanMessage } from "@/lib/api/errors";
import { useAllPlantings, usePredict, useWeatherStatus } from "@/lib/api/queries";
import type { PredictionOut, PredictionRequest } from "@/lib/api/types";
import { humaniseSlug, todayIso } from "@/lib/format";
import { useApiFormError } from "@/lib/use-api-form";
import { weatherSchema } from "@/lib/validation/schemas";

const optionalRain = z
  .union([z.string(), z.number(), z.null()])
  .transform((value) => (value === "" || value === null ? null : Number(value)))
  .refine((value) => value === null || (Number.isFinite(value) && value >= 0), {
    message: "Enter a number of millimetres, or leave blank.",
  })
  .default(null);

const rawWeather = z.object({
  temperature_mean_c: z.union([z.string(), z.number()]).default(""),
  temperature_min_c: z.union([z.string(), z.number()]).default(""),
  temperature_max_c: z.union([z.string(), z.number()]).default(""),
  humidity_pct: z.union([z.string(), z.number()]).default(""),
  rainfall_mm: z.union([z.string(), z.number()]).default(""),
  wind_speed_ms: z.union([z.string(), z.number()]).default(""),
  solar_radiation_mj_m2: z.union([z.string(), z.number()]).default(""),
});

const predictSchema = z
  .object({
    field_crop_id: z
      .union([z.string(), z.number()])
      .refine((value) => value !== "", { message: "Choose a planting." })
      .transform(Number)
      .refine((value) => Number.isFinite(value) && value > 0, {
        message: "Choose a planting.",
      }),
    prediction_date: z.iso.date("Enter a valid date."),
    rain_last_7_days_mm: optionalRain,
    rain_last_30_days_mm: optionalRain,
    forecast_rainfall_mm: optionalRain,
    weather_mode: z.enum(["provider", "manual"]),
    weather: rawWeather,
  })
  .transform((values, ctx) => {
    if (values.weather_mode === "provider") {
      return { ...values, weather: null as WeatherPayload | null };
    }
    const parsed = weatherSchema.safeParse(values.weather);
    if (!parsed.success) {
      for (const issue of parsed.error.issues) {
        ctx.addIssue({
          code: "custom",
          message: issue.message,
          path: ["weather", ...issue.path],
        });
      }
      return z.NEVER;
    }
    return { ...values, weather: parsed.data as WeatherPayload | null };
  });

type WeatherPayload = z.output<typeof weatherSchema>;
type Input = z.input<typeof predictSchema>;
type Output = z.output<typeof predictSchema>;

const STEPS = [
  { id: 1, title: "Farm & Field", icon: MapPin },
  { id: 2, title: "Crop & Stage", icon: Sprout },
  { id: 3, title: "Weather & Rain", icon: CloudRain },
  { id: 4, title: "Water Need", icon: Droplets },
];

const UNSUPPORTED_CROPS = [
  { name: "Sugarcane", kannada: "ಕಬ್ಬು", category: "Perennial / Long-term", reason: "Multi-year lysimeter curve calibration in progress" },
  { name: "Arecanut", kannada: "ಅಡಿಕೆ", category: "Perennial / Long-term", reason: "Canopy transpiration model under development" },
  { name: "Coffee", kannada: "ಕಾಫಿ", category: "Perennial / Long-term", reason: "Shade-crop microclimate baseline under development" },
];

export function PredictScreen() {
  const params = useSearchParams();
  const preselected = params.get("fieldCropId");

  const [currentStep, setCurrentStep] = useState(1);

  const plantings = useAllPlantings(true);
  const weatherStatus = useWeatherStatus();
  const predict = usePredict();
  const [result, setResult] = useState<PredictionOut | null>(null);

  const providerReady = weatherStatus.data?.configured === true;

  const {
    register,
    handleSubmit,
    control,
    setValue,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Input, unknown, Output>({
    resolver: standardSchemaResolver(predictSchema),
    defaultValues: {
      field_crop_id: preselected ?? "",
      prediction_date: todayIso(),
      rain_last_7_days_mm: "",
      rain_last_30_days_mm: "",
      forecast_rainfall_mm: "",
      weather_mode: "manual",
      weather: {
        temperature_mean_c: "",
        temperature_min_c: "",
        temperature_max_c: "",
        humidity_pct: "",
        rainfall_mm: "",
        wind_speed_ms: "",
        solar_radiation_mj_m2: "",
      },
    } as Input,
  });

  const { formError, report, clear } = useApiFormError<Input>(setError, [
    "field_crop_id",
    "prediction_date",
  ]);

  const mode = useWatch({ control, name: "weather_mode" });
  const selectedId = useWatch({ control, name: "field_crop_id" });

  const selected = plantings.data?.find(
    (planting) => String(planting.id) === String(selectedId),
  );

  // If preselected planting ID arrived from URL or list
  useEffect(() => {
    if (preselected && plantings.data?.length) {
      setValue("field_crop_id", preselected);
    } else if (!selectedId && plantings.data?.length) {
      setValue("field_crop_id", String(plantings.data[0].id));
    }
  }, [preselected, plantings.data, selectedId, setValue]);

  useEffect(() => {
    if (providerReady) setValue("weather_mode", "provider");
  }, [providerReady, setValue]);

  async function onSubmit(values: Output) {
    clear();
    const body: PredictionRequest = {
      field_crop_id: values.field_crop_id,
      prediction_date: values.prediction_date,
      rain_last_7_days_mm: values.rain_last_7_days_mm,
      rain_last_30_days_mm: values.rain_last_30_days_mm,
      forecast_rainfall_mm: values.forecast_rainfall_mm,
      use_weather_provider: values.weather_mode === "provider",
      weather: values.weather
        ? {
            temperature_mean_c: values.weather.temperature_mean_c,
            temperature_min_c: values.weather.temperature_min_c,
            temperature_max_c: values.weather.temperature_max_c,
            humidity_pct: values.weather.humidity_pct,
            rainfall_mm: values.weather.rainfall_mm ?? 0,
            wind_speed_ms: values.weather.wind_speed_ms,
            solar_radiation_mj_m2: values.weather.solar_radiation_mj_m2,
          }
        : null,
      persist: true,
    };

    try {
      const prediction = await predict.mutateAsync(body);
      setResult(prediction);
      setCurrentStep(4);
    } catch (error) {
      setResult(null);
      report(error);
    }
  }

  function handleReset() {
    setResult(null);
    setCurrentStep(1);
    clear();
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* ---------------- Wizard Title & Story Header ---------------- */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-emerald-200">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold uppercase tracking-wider border border-emerald-300">
              Pathway 1 · ನಾನು ಬೆಳೆದ ಬೆಳೆ
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-foreground mt-1">
            “I KNOW MY CROP” — Step-by-Step Water Wizard
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Guided farmer workflow: Location &rarr; Crop &rarr; Growth Stage &rarr; Weather &rarr; Water Need &rarr; Advisory.
          </p>
        </div>

        {result && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleReset}
            className="flex items-center gap-1.5 self-start sm:self-auto border-emerald-300 text-emerald-950 font-bold hover:bg-emerald-50"
          >
            <RotateCcw className="size-4 text-primary" />
            <span>New Calculation</span>
          </Button>
        )}
      </header>

      {/* ---------------- Step Progress Indicator ---------------- */}
      <nav aria-label="Wizard Steps" className="grid grid-cols-4 gap-2 text-center">
        {STEPS.map((s) => {
          const Icon = s.icon;
          const isActive = currentStep === s.id;
          const isDone = currentStep > s.id;
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => {
                if (s.id <= (result ? 4 : 3)) setCurrentStep(s.id);
              }}
              className={`flex flex-col sm:flex-row items-center justify-center gap-1.5 p-3 rounded-2xl border transition-all text-xs font-bold ${
                isActive
                  ? "border-primary bg-primary text-white shadow-md shadow-emerald-950/10"
                  : isDone
                  ? "border-emerald-300 bg-emerald-50 text-emerald-900"
                  : "border-emerald-200/80 bg-white text-muted-foreground hover:bg-emerald-50/50"
              }`}
            >
              <Icon className="size-4 shrink-0" />
              <span>{s.title}</span>
            </button>
          );
        })}
      </nav>

      {/* ---------------- Loading & Error States ---------------- */}
      {plantings.isPending && <LoadingState label="Loading your farm fields and plantings…" />}

      {plantings.isError && (
        <ErrorState
          message={humanMessage(plantings.error)}
          onRetry={() => plantings.refetch()}
        />
      )}

      {plantings.isSuccess && plantings.data.length === 0 && (
        <Card className="rounded-3xl border border-emerald-200">
          <CardContent className="p-8">
            <EmptyState
              icon={Sprout}
              title="No plantings recorded yet"
              description="To calculate exact stage-aware water needs, Jalachakra needs a crop planted in a field with a sowing date."
              action={
                <Link
                  href="/farms"
                  className="rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-white shadow-sm hover:bg-emerald-800"
                >
                  Set up a farm &amp; planting
                </Link>
              }
            />
          </CardContent>
        </Card>
      )}

      {/* ---------------- The Guided Form & Wizard Steps ---------------- */}
      {plantings.isSuccess && plantings.data.length > 0 && (
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-6">
          {formError && (
            <Notice tone="danger" title="Could not complete calculation">
              {formError}
            </Notice>
          )}

          {/* ---------------- STEP 1: Farm Location & Field ---------------- */}
          {currentStep === 1 && (
            <Card className="border border-emerald-200/90 bg-white rounded-3xl shadow-xs overflow-hidden">
              <SectionHeader
                title="Step 1: Choose Your Farm & Field"
                description="Where is this crop growing? Soil and location determine percolation and local reference evapotranspiration."
              />
              <CardContent className="space-y-6 p-6 sm:p-7">
                <div className="space-y-3">
                  <label className="text-sm font-bold text-foreground block">
                    Select Your Active Planting
                  </label>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {plantings.data.map((p) => {
                      const isChosen = String(p.id) === String(selectedId);
                      return (
                        <div
                          key={p.id}
                          onClick={() => setValue("field_crop_id", String(p.id))}
                          className={`cursor-pointer rounded-2xl border-2 p-4 transition-all relative ${
                            isChosen
                              ? "border-primary bg-emerald-50/70 shadow-sm"
                              : "border-emerald-200 bg-white hover:border-emerald-300 hover:bg-emerald-50/30"
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <h3 className="font-bold text-base text-foreground">
                                {p.crop_name}
                              </h3>
                              <p className="text-xs text-muted-foreground mt-0.5">
                                Field: <strong className="text-foreground">{p.field_name}</strong>
                              </p>
                            </div>
                            {isChosen && (
                              <CheckCircle2 className="size-5 text-primary shrink-0" />
                            )}
                          </div>

                          <div className="mt-3 pt-3 border-t border-emerald-100 flex items-center justify-between text-xs text-muted-foreground">
                            <span>Sown: <strong className="text-foreground">{p.sowing_date}</strong></span>
                            <span>Cycle: <strong className="text-foreground">{p.cycle_length_days}d</strong></span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  {errors.field_crop_id && (
                    <p className="text-xs text-destructive">{errors.field_crop_id.message}</p>
                  )}
                </div>

                {selected && (
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-4 space-y-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 block">
                      Field Agronomic Profile
                    </span>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                      <div>
                        <span className="text-muted-foreground block">Crop Name:</span>
                        <strong className="text-foreground">{selected.crop_name}</strong>
                      </div>
                      <div>
                        <span className="text-muted-foreground block">Sowing Date:</span>
                        <strong className="text-foreground">{selected.sowing_date}</strong>
                      </div>
                      <div>
                        <span className="text-muted-foreground block">Growth Stage:</span>
                        <strong className="text-foreground">{humaniseSlug(selected.current_stage)}</strong>
                      </div>
                      <div>
                        <span className="text-muted-foreground block">Current Kc:</span>
                        <strong className="text-foreground">{selected.current_kc?.toFixed(2) ?? "—"}</strong>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex justify-end pt-2">
                  <Button
                    type="button"
                    size="lg"
                    onClick={() => setCurrentStep(2)}
                    className="flex items-center gap-2 bg-primary hover:bg-emerald-800 text-white font-bold rounded-xl shadow-md"
                  >
                    <span>Proceed to Crop &amp; Stage</span>
                    <ArrowRight className="size-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ---------------- STEP 2: Crop Category & Stage Context ---------------- */}
          {currentStep === 2 && (
            <Card className="border border-emerald-200/90 bg-white rounded-3xl shadow-xs overflow-hidden">
              <SectionHeader
                title="Step 2: Crop Category & Agronomic Stage"
                description="Review crop category, growth cycle timing, and FAO-56 stage progression."
              />
              <CardContent className="space-y-6 p-6 sm:p-7">
                {selected && (
                  <div className="rounded-2xl border-2 border-emerald-300 bg-emerald-50/60 p-5 space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <span className="text-xs font-bold uppercase tracking-wider text-emerald-800">
                          Selected Active Crop
                        </span>
                        <h3 className="text-xl font-black text-foreground mt-0.5">
                          {selected.crop_name}
                        </h3>
                        <p className="text-xs text-muted-foreground">
                          Planted in {selected.field_name} · Day {selected.days_after_sowing} of {selected.cycle_length_days}
                        </p>
                      </div>
                      <span className="px-3 py-1 rounded-full bg-emerald-100 border border-emerald-300 text-emerald-800 text-xs font-bold self-start sm:self-auto">
                        Active CWR Calibrated Model
                      </span>
                    </div>

                    <div className="pt-2">
                      <div className="flex justify-between text-xs text-muted-foreground mb-1 font-semibold">
                        <span>Current Stage: <strong className="text-foreground">{humaniseSlug(selected.current_stage)}</strong></span>
                        <span>{Math.round(selected.progress_pct)}% Complete</span>
                      </div>
                      <div className="h-3 rounded-full bg-emerald-100 overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all"
                          style={{ width: `${Math.min(100, Math.max(0, selected.progress_pct))}%` }}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Date selection for the prediction */}
                <div className="grid gap-4 sm:grid-cols-2">
                  <TextField
                    label="Prediction Target Date"
                    type="date"
                    error={errors.prediction_date?.message}
                    required
                    {...register("prediction_date")}
                  />
                  <div className="text-xs text-muted-foreground p-3.5 rounded-2xl bg-emerald-50/40 border border-emerald-200 flex items-center">
                    <Info className="size-4 shrink-0 text-primary mr-2" />
                    <span>Defaults to today. You can simulate previous days or future dates in the crop cycle.</span>
                  </div>
                </div>

                {/* Unsupported Crops Warning Section */}
                <div className="pt-2 space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    Perennial / Long-Term Crops Status
                  </h4>
                  <div className="grid gap-2.5 sm:grid-cols-3 text-xs">
                    {UNSUPPORTED_CROPS.map((uc) => (
                      <div key={uc.name} className="p-3.5 rounded-2xl border border-dashed border-amber-300 bg-amber-50/40 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-foreground">{uc.name} ({uc.kannada})</span>
                          <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-amber-100 text-amber-700">
                            UNDER DEV
                          </span>
                        </div>
                        <p className="text-[11px] text-muted-foreground leading-tight">{uc.reason}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex justify-between pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setCurrentStep(1)}
                    className="flex items-center gap-1.5 border-emerald-300 text-emerald-950 font-bold"
                  >
                    <ArrowLeft className="size-4" />
                    <span>Back</span>
                  </Button>
                  <Button
                    type="button"
                    onClick={() => setCurrentStep(3)}
                    className="flex items-center gap-2 bg-primary hover:bg-emerald-800 text-white font-bold rounded-xl"
                  >
                    <span>Proceed to Weather &amp; Rain</span>
                    <ArrowRight className="size-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ---------------- STEP 3: Weather & Rainfall ---------------- */}
          {currentStep === 3 && (
            <Card className="border border-emerald-200/90 bg-white rounded-3xl shadow-xs overflow-hidden">
              <SectionHeader
                title="Step 3: Weather & Rainfall Context"
                description="Recent rainfall is credited to the soil reservoir so you don't over-pump or leach nutrients."
              />
              <CardContent className="space-y-6 p-6 sm:p-7">
                {/* Weather Mode Selector */}
                <div className="space-y-3">
                  <label className="text-sm font-bold text-foreground block">
                    Choose Weather Data Source
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <label
                      className={`cursor-pointer rounded-2xl border-2 p-4 transition-all flex items-start gap-3.5 ${
                        mode === "provider"
                          ? "border-primary bg-emerald-50/70"
                          : "border-emerald-200 bg-white hover:bg-emerald-50/30"
                      }`}
                    >
                      <input
                        type="radio"
                        value="provider"
                        className="sr-only"
                        {...register("weather_mode")}
                      />
                      <CloudSun className="size-5 text-primary shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold text-sm text-foreground block">
                          Automatic Weather Provider
                        </span>
                        <span className="text-xs text-muted-foreground block mt-0.5">
                          {providerReady
                            ? "Connected to Open-Meteo & Karnataka IMD daily station data."
                            : "Using district meteorological normals."}
                        </span>
                      </div>
                    </label>

                    <label
                      className={`cursor-pointer rounded-2xl border-2 p-4 transition-all flex items-start gap-3.5 ${
                        mode === "manual"
                          ? "border-primary bg-emerald-50/70"
                          : "border-emerald-200 bg-white hover:bg-emerald-50/30"
                      }`}
                    >
                      <input
                        type="radio"
                        value="manual"
                        className="sr-only"
                        {...register("weather_mode")}
                      />
                      <PencilLine className="size-5 text-primary shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold text-sm text-foreground block">
                          Enter Farm Weather Readings
                        </span>
                        <span className="text-xs text-muted-foreground block mt-0.5">
                          Type in rain gauge or thermometer readings from your field.
                        </span>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Rainfall History Fields (Both Modes) */}
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50/30 p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <CloudRain className="size-4 text-primary" />
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-900">
                      Recent Soil Moisture &amp; Rain Credit
                    </span>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-3">
                    <NumberField
                      label="Rain in Last 7 Days (mm)"
                      placeholder="0"
                      hint="Reduces immediate irrigation need"
                      error={errors.rain_last_7_days_mm?.message}
                      {...register("rain_last_7_days_mm")}
                    />
                    <NumberField
                      label="Rain in Last 30 Days (mm)"
                      placeholder="0"
                      hint="Deep root zone moisture balance"
                      error={errors.rain_last_30_days_mm?.message}
                      {...register("rain_last_30_days_mm")}
                    />
                    <NumberField
                      label="Forecast Rain (mm)"
                      placeholder="0"
                      hint="Expected rain in next 24-48 hours"
                      error={errors.forecast_rainfall_mm?.message}
                      {...register("forecast_rainfall_mm")}
                    />
                  </div>
                </div>

                {/* Manual Weather Block */}
                {mode === "manual" && (
                  <div className="rounded-2xl border border-emerald-200 p-4 space-y-4 bg-white">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground block">
                      Today&apos;s Field Weather Readings
                    </span>
                    <div className="grid gap-4 sm:grid-cols-3">
                      <NumberField
                        label="Today's Rainfall (mm)"
                        placeholder="0"
                        error={errors.weather?.rainfall_mm?.message}
                        {...register("weather.rainfall_mm")}
                      />
                      <NumberField
                        label="Mean Temperature (°C)"
                        placeholder="28.5"
                        error={errors.weather?.temperature_mean_c?.message}
                        {...register("weather.temperature_mean_c")}
                      />
                      <NumberField
                        label="Relative Humidity (%)"
                        placeholder="65"
                        error={errors.weather?.humidity_pct?.message}
                        {...register("weather.humidity_pct")}
                      />
                    </div>
                  </div>
                )}

                <div className="flex justify-between pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setCurrentStep(2)}
                    className="flex items-center gap-1.5 border-emerald-300 text-emerald-950 font-bold"
                  >
                    <ArrowLeft className="size-4" />
                    <span>Back</span>
                  </Button>
                  <Button
                    type="submit"
                    size="lg"
                    loading={isSubmitting}
                    loadingText="Computing FAO-56 Demand…"
                    className="flex items-center gap-2 font-bold bg-primary hover:bg-emerald-800 text-white rounded-xl shadow-md"
                  >
                    <Droplets className="size-5" />
                    <span>Calculate Crop Water Need &rarr;</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ---------------- STEP 4: Water Need & Advisory Result ---------------- */}
          {currentStep === 4 && result && (
            <div className="space-y-6">
              <PredictionResult prediction={result} />

              <div className="flex justify-between pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setCurrentStep(3)}
                  className="flex items-center gap-1.5 border-emerald-300 text-emerald-950 font-bold"
                >
                  <ArrowLeft className="size-4" />
                  <span>Adjust Weather Inputs</span>
                </Button>
                <Button
                  type="button"
                  onClick={handleReset}
                  className="flex items-center gap-2 bg-primary hover:bg-emerald-800 text-white font-bold rounded-xl"
                >
                  <RotateCcw className="size-4" />
                  <span>Start Another Crop Calculation</span>
                </Button>
              </div>
            </div>
          )}
        </form>
      )}
    </div>
  );
}
