"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { standardSchemaResolver } from "@hookform/resolvers/standard-schema";
import { ChevronRight, LocateFixed, Map, MapPin, Plus, Tractor } from "lucide-react";
import type { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FormDialog } from "@/components/ui/form-dialog";
import { AgroEmptyState } from "@/components/agro-illustrations/AgroEmptyState";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { Notice } from "@/components/ui/notice";
import { NumberField, TextField } from "@/components/ui/form-fields";
import { useCreateFarm, useFarms } from "@/lib/api/queries";
import { humanMessage } from "@/lib/api/errors";
import { formatArea } from "@/lib/format";
import { useApiFormError } from "@/lib/use-api-form";
import { farmSchema } from "@/lib/validation/schemas";

type Input = z.input<typeof farmSchema>;
type Output = z.output<typeof farmSchema>;

const FIELD_NAMES = [
  "name",
  "total_area_ha",
  "state",
  "district",
  "taluk",
  "latitude",
  "longitude",
] as const;

export function FarmsScreen() {
  const [creating, setCreating] = useState(false);
  const farms = useFarms();

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-emerald-200">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold uppercase tracking-wider">
              Farm Management · ನನ್ನ ಕೃಷಿ ಭೂಮಿ
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-foreground mt-1">
            My Farm &amp; Field Locations
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Add your location first. Coordinates enable localized Open-Meteo and IMD weather; district details can be saved without them.
          </p>
        </div>
        <Button
          onClick={() => setCreating(true)}
          className="bg-primary hover:bg-emerald-800 text-white font-bold rounded-xl shadow-md shrink-0 flex items-center gap-1.5"
        >
          <Plus className="size-4" />
          <span>Add New Farm</span>
        </Button>
      </header>

      {farms.isPending && <LoadingState label="Loading your farms…" />}

      {farms.isError && (
        <ErrorState
          message={humanMessage(farms.error)}
          onRetry={() => farms.refetch()}
        />
      )}

      {farms.isSuccess && farms.data.length === 0 && (
        <AgroEmptyState
          type="farms"
          title="Your Field is Waiting for Its First Water Plan"
          description="Register your farm plot to connect local Karnataka weather normals, map soil texture, and calculate daily transpiration demand."
          actionLabel="Add Your Farm Now"
          actionHref="#"
        />
      )}

      {farms.isSuccess && farms.data.length > 0 && (
        <ul className="grid gap-4 sm:grid-cols-2">
          {farms.data.map((farm) => (
            <li key={farm.id}>
              <Link
                href={`/farms/${farm.id}`}
                className="flex h-full flex-col justify-between rounded-3xl border border-emerald-200/90 bg-white p-5 sm:p-6 shadow-xs transition-all hover:border-primary hover:shadow-md group"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="size-11 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
                        <Tractor className="size-5.5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-black text-lg text-foreground group-hover:text-primary transition-colors">
                          {farm.name}
                        </h3>
                        <p className="text-xs text-muted-foreground">
                          {farm.district ? `${farm.district}` : "Karnataka Region"}
                          {farm.taluk ? `, ${farm.taluk}` : ""}
                        </p>
                      </div>
                    </div>
                    <span className="text-xs font-black px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                      {formatArea(farm.total_area_ha)} ha
                    </span>
                  </div>

                  <p className="text-xs text-muted-foreground pt-1">
                    {farm.latitude !== null && farm.longitude !== null
                      ? `GPS: ${farm.latitude.toFixed(4)}° N, ${farm.longitude.toFixed(4)}° E`
                      : "District coordinates active · Precise GPS optional"}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-emerald-100 flex items-center justify-between text-xs font-bold text-primary">
                  <span>View Fields &amp; Active Plantings</span>
                  <ChevronRight className="size-4 transition-transform group-hover:translate-x-1" />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}

      <CreateFarmDialog open={creating} onClose={() => setCreating(false)} />
    </div>
  );
}

function CreateFarmDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
  }) {
  const createFarm = useCreateFarm();
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Input, unknown, Output>({
    resolver: standardSchemaResolver(farmSchema),
    defaultValues: {
      name: "",
      total_area_ha: "",
      state: "Karnataka",
      district: "Mandya",
      taluk: "",
      latitude: "",
      longitude: "",
    },
  });
  const { formError, report, clear } = useApiFormError<Input>(
    setError,
    FIELD_NAMES,
  );
  const [gpsAccuracy, setGpsAccuracy] = useState<number | null>(null);
  const [gpsError, setGpsError] = useState<string | null>(null);
  const [gpsLoading, setGpsLoading] = useState(false);

  function useGpsLocation() {
    setGpsError(null);
    setGpsAccuracy(null);
    if (!navigator.geolocation) {
      setGpsError("GPS is not available in this browser. Enter the location manually.");
      return;
    }
    setGpsLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setValue("latitude", position.coords.latitude.toFixed(6), { shouldValidate: true });
        setValue("longitude", position.coords.longitude.toFixed(6), { shouldValidate: true });
        setGpsAccuracy(position.coords.accuracy);
        setGpsLoading(false);
      },
      (error) => {
        setGpsError(
          error.code === error.PERMISSION_DENIED
            ? "Location permission was not granted. Enter the location manually."
            : "Could not get a GPS reading. Enter the location manually.",
        );
        setGpsLoading(false);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 },
    );
  }

  async function onSubmit(values: Output) {
    clear();
    try {
      await createFarm.mutateAsync(values);
      reset();
      onClose();
    } catch (error) {
      report(error);
    }
  }

  function close() {
    reset();
    clear();
    onClose();
  }

  return (
    <FormDialog
      open={open}
      onClose={close}
      title="Add a New Farm"
      description="Only the farm name and total area in hectares are required."
    >
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {formError && (
          <Notice tone="danger" title="Could not save">
            {formError}
          </Notice>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <TextField
            label="State"
            error={errors.state?.message}
            {...register("state")}
          />
          <TextField
            label="District"
            error={errors.district?.message}
            {...register("district")}
          />
          <TextField
            label="Taluk / Village"
            error={errors.taluk?.message}
            {...register("taluk")}
          />
        </div>

        <fieldset className="space-y-3 rounded-2xl border border-emerald-200 bg-emerald-50/40 p-4">
          <legend className="px-1 text-xs font-bold uppercase tracking-wider text-emerald-900">
            Coordinates (Optional)
          </legend>
          <p className="text-xs text-muted-foreground">
            Capture field GPS or enter coordinates manually for hyper-local weather predictions.
          </p>
          <Button
            type="button"
            variant="secondary"
            onClick={useGpsLocation}
            loading={gpsLoading}
            loadingText="Reading device GPS…"
            className="border border-emerald-200 bg-white hover:bg-emerald-50 text-xs font-bold text-emerald-950"
          >
            <LocateFixed className="size-4 text-primary" />
            Capture GPS Coordinates
          </Button>
          {gpsError && <p role="alert" className="text-xs text-destructive">{gpsError}</p>}
          {gpsAccuracy !== null && (
            <p className="text-xs text-emerald-800 font-semibold">
              GPS reading captured. Estimated accuracy: ±{Math.round(gpsAccuracy)} m.
            </p>
          )}
          <div className="grid gap-3 sm:grid-cols-2 pt-1">
            <NumberField
              label="Latitude"
              unit="degrees"
              error={errors.latitude?.message}
              {...register("latitude", { onChange: () => setGpsAccuracy(null) })}
            />
            <NumberField
              label="Longitude"
              unit="degrees"
              error={errors.longitude?.message}
              {...register("longitude", { onChange: () => setGpsAccuracy(null) })}
            />
          </div>
        </fieldset>

        <TextField
          label="Farm Name"
          placeholder="e.g. Kaveri Basin Plot 1"
          error={errors.name?.message}
          required
          {...register("name")}
        />
        <NumberField
          label="Total Area"
          unit="hectares"
          placeholder="1.5"
          hint="Total farmland area. Sub-fields must fit within this."
          error={errors.total_area_ha?.message}
          required
          {...register("total_area_ha")}
        />

        <div className="flex justify-end gap-2.5 pt-2">
          <Button variant="secondary" onClick={close} className="rounded-xl font-bold">
            Cancel
          </Button>
          <Button
            type="submit"
            loading={isSubmitting}
            loadingText="Saving Farm…"
            className="bg-primary hover:bg-emerald-800 text-white font-bold rounded-xl shadow-md"
          >
            Save Farm
          </Button>
        </div>
      </form>
    </FormDialog>
  );
}
