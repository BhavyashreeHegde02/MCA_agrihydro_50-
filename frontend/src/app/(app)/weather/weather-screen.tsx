"use client";

import Link from "next/link";
import { useState } from "react";
import {
  CloudOff,
  CloudRain,
  CloudSun,
  Droplets,
  MapPin,
  Thermometer,
  Wind,
} from "lucide-react";

import { WeatherForecastChart } from "@/components/charts/water-charts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SelectField } from "@/components/ui/form-fields";
import { Notice } from "@/components/ui/notice";
import { SectionHeader } from "@/components/ui/section-header";
import { Stat } from "@/components/ui/stat";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { ApiError, humanMessage } from "@/lib/api/errors";
import {
  useCurrentWeather,
  useFarms,
  useWeatherForecast,
  useWeatherStatus,
} from "@/lib/api/queries";
import { formatDate, formatDepth, formatNumber } from "@/lib/format";

export function WeatherScreen() {
  const status = useWeatherStatus();
  const farms = useFarms();
  // The chosen farm, or the first usable one. Derived rather than written into
  // state by an effect: an effect that calls setState on mount causes a second
  // render before anything is painted, and the fallback is a pure function of
  // data we already have.
  const [chosenFarmId, setChosenFarmId] = useState<string>("");

  // Farms without coordinates cannot be used: the backend refuses with
  // FARM_HAS_NO_COORDINATES rather than guessing a location.
  const locatable = (farms.data ?? []).filter(
    (farm) => farm.latitude !== null && farm.longitude !== null,
  );

  const farmId =
    chosenFarmId || (locatable.length > 0 ? String(locatable[0].id) : "");
  const configured = status.data?.configured === true;
  const selected = farmId ? Number(farmId) : undefined;
  const enabled = configured && selected !== undefined;

  const current = useCurrentWeather(
    { farmId: enabled ? selected : undefined },
    { enabled },
  );
  const forecast = useWeatherForecast(
    { farmId: enabled ? selected : undefined },
    7,
    { enabled },
  );

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      {/* ---- Page Header ---- */}
      <header className="rounded-3xl border border-emerald-200/90 bg-gradient-to-r from-sky-50/70 via-white to-emerald-50/40 p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="size-14 rounded-2xl bg-sky-500 text-white flex items-center justify-center font-bold shadow-md shadow-sky-900/10 shrink-0">
              <CloudSun className="size-7" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-sky-800 bg-sky-100/80 px-2.5 py-0.5 rounded-full border border-sky-200">
                Live Field Climate · ಹವಾಮಾನ ಡೇಟಾ
              </span>
              <h1 className="text-2xl sm:text-3xl font-black text-foreground mt-1 tracking-tight">
                Local Field Weather
              </h1>
              <p className="text-xs sm:text-sm text-muted-foreground mt-0.5 max-w-xl">
                Temperature and humidity drive reference evapotranspiration (ET₀). Rainfall reduces irrigation requirements directly—every credited millimetre saves pump energy.
              </p>
            </div>
          </div>

          <Link
            href="/predict"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-primary text-white text-xs font-bold shadow-md shadow-emerald-900/10 hover:bg-emerald-800 transition-all shrink-0"
          >
            <Droplets className="size-4" />
            <span>Use in Prediction</span>
          </Link>
        </div>
      </header>

      {/* ---- How Weather Feeds Predictions ---- */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-sky-200/80 bg-sky-50/50 p-4 flex items-start gap-3">
          <Thermometer className="size-5 text-sky-600 shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-bold text-sky-900">Temperature → ET₀</p>
            <p className="text-[11px] text-muted-foreground mt-0.5 leading-tight">
              Mean temp combined with solar radiation drives Penman-Monteith reference evapotranspiration.
            </p>
          </div>
        </div>
        <div className="rounded-2xl border border-emerald-200/80 bg-emerald-50/50 p-4 flex items-start gap-3">
          <CloudRain className="size-5 text-primary shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-bold text-emerald-900">Rainfall → Root Credit</p>
            <p className="text-[11px] text-muted-foreground mt-0.5 leading-tight">
              Recorded rainfall is credited to the soil root zone, directly reducing today&apos;s gross irrigation requirement.
            </p>
          </div>
        </div>
        <div className="rounded-2xl border border-amber-200/80 bg-amber-50/50 p-4 flex items-start gap-3">
          <Wind className="size-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-bold text-amber-900">Wind → Advection Loss</p>
            <p className="text-[11px] text-muted-foreground mt-0.5 leading-tight">
              Wind speed at 2 m height increases advective ET₀. Higher wind on dry days raises water demand.
            </p>
          </div>
        </div>
      </div>

      {status.isPending && <LoadingState label="Checking the weather service…" />}

      {status.isSuccess && !configured && (
        <Card className="rounded-3xl border border-emerald-200">
          <CardContent className="p-8">
            <EmptyState
              icon={CloudOff}
              title="No weather provider configured"
              description={
                status.data.note ??
                "This deployment has no live weather source. Weather readings must be entered manually when predicting. Setting WEATHER_PROVIDER on the backend enables this screen."
              }
              action={
                <Button asChild variant="outline" className="border-emerald-300 text-emerald-950 font-bold">
                  <Link href="/predict">Enter readings manually when predicting</Link>
                </Button>
              }
            />
          </CardContent>
        </Card>
      )}

      {configured && farms.isSuccess && locatable.length === 0 && (
        <Card className="rounded-3xl border border-emerald-200">
          <CardContent className="p-8">
            <EmptyState
              icon={MapPin}
              title="No farm has GPS coordinates"
              description="Live weather is fetched for a specific location. Add a latitude and longitude to one of your farms and it will appear here."
              action={
                <Button asChild className="bg-primary text-white font-bold hover:bg-emerald-800">
                  <Link href="/farms">Set up farm coordinates</Link>
                </Button>
              }
            />
          </CardContent>
        </Card>
      )}

      {configured && locatable.length > 0 && (
        <>
          {/* Farm Selector */}
          <div className="flex flex-wrap items-end gap-3 rounded-2xl border border-emerald-200/80 bg-white p-4 shadow-xs">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-800 mr-1">
              <MapPin className="size-3.5 text-primary" />
              <span>Farm Location</span>
            </div>
            <div className="max-w-xs flex-1">
              <SelectField
                label=""
                options={locatable.map((farm) => ({
                  value: String(farm.id),
                  label: `${farm.name} (${farm.latitude?.toFixed(4)}, ${farm.longitude?.toFixed(4)})`,
                }))}
                value={farmId}
                onChange={(event) => setChosenFarmId(event.target.value)}
              />
            </div>
            <Badge variant="info">
              <CloudSun className="size-3" />
              {status.data?.provider}
            </Badge>
          </div>

          {/* Today's Weather Card */}
          <Card className="border border-emerald-200/90 bg-white rounded-3xl shadow-xs overflow-hidden">
            <SectionHeader
              title="Today's Field Conditions"
              description="These are the exact readings that will be used if you select 'automatic weather provider' in your water prediction."
            />
            <CardContent className="pt-4 p-6 sm:p-7">
              {current.isPending && <LoadingState label="Fetching today's weather…" />}

              {current.isError && (
                <ErrorState
                  title={
                    current.error instanceof ApiError &&
                    current.error.status === 503
                      ? "The weather service did not respond"
                      : undefined
                  }
                  message={humanMessage(current.error)}
                  onRetry={() => current.refetch()}
                />
              )}

              {current.isSuccess && (
                <>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <Stat
                      label="Mean Temperature"
                      value={formatNumber(current.data.temperature_mean_c, 1)}
                      unit="°C"
                      hint={`${formatNumber(current.data.temperature_min_c, 1)} – ${formatNumber(current.data.temperature_max_c, 1)} °C today`}
                    />
                    <Stat
                      label="Relative Humidity"
                      value={formatNumber(current.data.humidity_pct, 0)}
                      unit="%"
                    />
                    <Stat
                      label="Today's Rainfall"
                      value={formatDepth(current.data.rainfall_mm)}
                      unit="mm"
                      tone={current.data.rainfall_mm > 0 ? "ok" : "neutral"}
                    />
                    <Stat
                      label="Wind at 2 m Height"
                      value={
                        current.data.wind_speed_ms !== null
                          ? formatNumber(current.data.wind_speed_ms, 1)
                          : "—"
                      }
                      unit={current.data.wind_speed_ms !== null ? "m/s" : undefined}
                      hint={
                        current.data.wind_speed_ms === null
                          ? "Not supplied; standard value assumed for ET₀"
                          : undefined
                      }
                    />
                  </div>

                  <div className="mt-4 pt-3 border-t border-emerald-100 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                    <span className="font-medium">{formatDate(current.data.date)}</span>
                    <span>·</span>
                    <span>Source: <strong className="text-foreground">{current.data.source}</strong></span>
                    <span>·</span>
                    <span>Provider: <strong className="text-foreground">{current.data.provider}</strong></span>
                    {current.data.solar_radiation_mj_m2 !== null ? (
                      <>
                        <span>·</span>
                        <span>Solar Radiation: <strong className="text-foreground">{formatNumber(current.data.solar_radiation_mj_m2, 1)} MJ/m²</strong></span>
                      </>
                    ) : (
                      <>
                        <span>·</span>
                        <span className="text-amber-700">Solar radiation estimated from temperature range</span>
                      </>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* 7-Day Forecast Card */}
          <Card className="border border-emerald-200/90 bg-white rounded-3xl shadow-xs overflow-hidden">
            <SectionHeader
              title="7-Day Karnataka Field Forecast"
              description="Plan irrigation scheduling ahead. Rainfall forecast reduces future gross irrigation requirements—save pump time proactively."
            />
            <CardContent className="pt-4 p-6 sm:p-7">
              {forecast.isPending && <LoadingState label="Loading 7-day field forecast…" />}

              {forecast.isError && (
                <ErrorState
                  message={humanMessage(forecast.error)}
                  onRetry={() => forecast.refetch()}
                />
              )}

              {forecast.isSuccess && forecast.data.length > 0 && (
                <div className="space-y-5">
                  <WeatherForecastChart days={forecast.data} />

                  <div className="overflow-x-auto rounded-2xl border border-emerald-100">
                    <table className="w-full text-sm">
                      <caption className="p-3 text-left text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50/50">
                        Daily Forecast Data
                      </caption>
                      <thead className="border-b border-emerald-100 bg-emerald-50/80 text-left text-xs tracking-wide text-emerald-950 font-bold uppercase">
                        <tr>
                          <th scope="col" className="px-3.5 py-2.5 font-bold">Date</th>
                          <th scope="col" className="px-3.5 py-2.5 text-right font-bold">Min °C</th>
                          <th scope="col" className="px-3.5 py-2.5 text-right font-bold">Max °C</th>
                          <th scope="col" className="px-3.5 py-2.5 text-right font-bold">Humidity</th>
                          <th scope="col" className="px-3.5 py-2.5 text-right font-bold">Rainfall</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-emerald-100">
                        {forecast.data.map((day) => (
                          <tr
                            key={day.date}
                            className="hover:bg-emerald-50/40 transition-colors"
                          >
                            <td className="px-3.5 py-2.5 font-medium text-foreground">{formatDate(day.date)}</td>
                            <td className="tabular px-3.5 py-2.5 text-right text-muted-foreground">
                              {formatNumber(day.temperature_min_c, 1)} °C
                            </td>
                            <td className="tabular px-3.5 py-2.5 text-right text-muted-foreground">
                              {formatNumber(day.temperature_max_c, 1)} °C
                            </td>
                            <td className="tabular px-3.5 py-2.5 text-right text-muted-foreground">
                              {formatNumber(day.humidity_pct, 0)}%
                            </td>
                            <td className="tabular px-3.5 py-2.5 text-right">
                              <span className={`font-bold ${day.rainfall_mm > 0 ? "text-sky-700" : "text-muted-foreground"}`}>
                                {formatDepth(day.rainfall_mm)} mm
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {forecast.isSuccess && forecast.data.length === 0 && (
                <EmptyState
                  title="No forecast data returned"
                  description="This can happen when the farm location is outside the provider's coverage area."
                />
              )}
            </CardContent>
          </Card>

          <Notice tone="warning" title="Research transparency: weather data provenance">
            The ML model was trained on a historical daily series whose location is not verified against live station data. Live readings shown here are tagged by source and are never mixed into training without a separate, deliberate calibration step.
          </Notice>
        </>
      )}
    </div>
  );
}
