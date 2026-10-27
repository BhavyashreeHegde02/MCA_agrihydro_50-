"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { standardSchemaResolver } from "@hookform/resolvers/standard-schema";
import { ArrowLeft, Droplets, FlaskConical, Plus, Sprout } from "lucide-react";
import type { z } from "zod";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";
import { Stat } from "@/components/ui/stat";
import { FormDialog } from "@/components/ui/form-dialog";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/ui/states";
import { Notice } from "@/components/ui/notice";
import {
  NumberField,
  SelectField,
  TextAreaField,
  TextField,
} from "@/components/ui/form-fields";
import { humanMessage } from "@/lib/api/errors";
import {
  useAddSoil,
  useCreatePlanting,
  useCrops,
  useFields,
  usePlantings,
  useSoil,
} from "@/lib/api/queries";
import {
  formatArea,
  formatDate,
  formatNumber,
  formatPercent,
  humaniseSlug,
  todayIso,
} from "@/lib/format";
import { useApiFormError } from "@/lib/use-api-form";
import { plantingSchema, soilSchema } from "@/lib/validation/schemas";

export function FieldDetailScreen({
  farmId,
  fieldId,
}: {
  farmId: number;
  fieldId: number;
}) {
  const [planting, setPlanting] = useState(false);
  const [sampling, setSampling] = useState(false);

  const fields = useFields(farmId);
  const field = fields.data?.find((candidate) => candidate.id === fieldId);
  const plantings = usePlantings(fieldId);
  const soil = useSoil(fieldId);

  return (
    <div className="space-y-6">
      <Link
        href={`/farms/${farmId}`}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-primary"
      >
        <ArrowLeft className="size-4" />
        Back to the farm
      </Link>

      {fields.isPending && <LoadingState label="Loading the field…" />}

      {fields.isError && (
        <ErrorState
          message={humanMessage(fields.error)}
          onRetry={() => fields.refetch()}
        />
      )}

      {fields.isSuccess && !field && (
        <Notice tone="warning" title="Field not found">
          No field with id {fieldId} belongs to this farm. It may have been
          removed.
        </Notice>
      )}

      {field && (
        <>
          <header>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              {field.name}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {formatArea(field.area_ha)} ha
              {field.soil_type && ` · ${humaniseSlug(field.soil_type)}`}
            </p>
          </header>

          <section className="grid gap-3 sm:grid-cols-3">
            <Stat label="Area" value={formatArea(field.area_ha)} unit="ha" />
            <Stat
              label="Irrigation method"
              value={
                field.irrigation_method
                  ? humaniseSlug(field.irrigation_method)
                  : "Not set"
              }
            />
            <Stat
              label="Application efficiency"
              value={
                field.irrigation_efficiency !== null &&
                field.irrigation_efficiency !== undefined
                  ? formatPercent(field.irrigation_efficiency)
                  : "Default"
              }
              hint="Sets how much more must be delivered than the crop needs"
            />
          </section>

          <Card>
            <SectionHeader
              title="Plantings"
              description="A prediction is made for a planting, because the crop coefficient depends on how far through its cycle the crop is."
              action={
                <Button size="sm" onClick={() => setPlanting(true)}>
                  <Plus className="size-4" />
                  Plant a crop
                </Button>
              }
            />
            <CardContent>
              {plantings.isPending && <LoadingState label="Loading plantings…" />}

              {plantings.isError && (
                <ErrorState
                  message={humanMessage(plantings.error)}
                  onRetry={() => plantings.refetch()}
                />
              )}

              {plantings.isSuccess && plantings.data.length === 0 && (
                <EmptyState
                  icon={Sprout}
                  title="Nothing planted here yet"
                  description="Record the crop and its sowing date. The growth stage and crop coefficient are then worked out for you on any given day."
                  action={
                    <Button onClick={() => setPlanting(true)}>
                      <Plus className="size-4" />
                      Plant a crop
                    </Button>
                  }
                />
              )}

              {plantings.isSuccess && plantings.data.length > 0 && (
                <ul className="divide-y divide-border">
                  {plantings.data.map((crop) => (
                    <li
                      key={crop.id}
                      className="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
                    >
                      <div className="min-w-0">
                        <p className="flex items-center gap-2 font-medium text-foreground">
                          {crop.crop_name}
                          <Badge
                            variant={crop.status === "active" ? "ok" : "secondary"}
                          >
                            {crop.status}
                          </Badge>
                        </p>
                        <p className="mt-0.5 text-sm text-muted-foreground">
                          Sown {formatDate(crop.sowing_date)} · day{" "}
                          {crop.days_after_sowing} of {crop.cycle_length_days} ·{" "}
                          {humaniseSlug(crop.current_stage)}
                          {crop.current_kc !== null &&
                            crop.current_kc !== undefined &&
                            ` · Kc ${crop.current_kc.toFixed(2)}`}
                        </p>
                      </div>
                      <Link
                        href={`/predict?fieldCropId=${crop.id}`}
                        className="rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground"
                      >
                        Predict water need
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <SectionHeader
              title="Soil samples"
              description="Recorded for the agronomic record and crop suitability. Soil chemistry does not enter the water balance."
              action={
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setSampling(true)}
                >
                  <Plus className="size-4" />
                  Add reading
                </Button>
              }
            />
            <CardContent className="p-0">
              {soil.isPending && (
                <div className="p-4">
                  <LoadingState label="Loading soil readings…" />
                </div>
              )}

              {soil.isError && (
                <div className="p-4">
                  <ErrorState
                    message={humanMessage(soil.error)}
                    onRetry={() => soil.refetch()}
                  />
                </div>
              )}

              {soil.isSuccess && soil.data.length === 0 && (
                <div className="p-4">
                  <EmptyState
                    icon={FlaskConical}
                    title="No soil readings"
                    description="Add what you know. Every measurement is optional on its own — pH alone is a useful record."
                    action={
                      <Button
                        variant="secondary"
                        onClick={() => setSampling(true)}
                      >
                        Add a reading
                      </Button>
                    }
                  />
                </div>
              )}

              {soil.isSuccess && soil.data.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
                      <tr>
                        <th scope="col" className="px-4 py-2.5 font-semibold">Sampled</th>
                        <th scope="col" className="px-4 py-2.5 text-right font-semibold">pH</th>
                        <th scope="col" className="px-4 py-2.5 text-right font-semibold">N</th>
                        <th scope="col" className="px-4 py-2.5 text-right font-semibold">P</th>
                        <th scope="col" className="px-4 py-2.5 text-right font-semibold">K</th>
                        <th scope="col" className="px-4 py-2.5 text-right font-semibold">Organic %</th>
                        <th scope="col" className="px-4 py-2.5 font-semibold">Texture</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {soil.data.map((sample) => (
                        <tr key={sample.id}>
                          <td className="px-4 py-2.5">
                            {formatDate(sample.sample_date)}
                          </td>
                          <td className="tabular px-4 py-2.5 text-right">
                            {formatNumber(sample.ph_level, 1)}
                          </td>
                          <td className="tabular px-4 py-2.5 text-right">
                            {formatNumber(sample.nitrogen, 0)}
                          </td>
                          <td className="tabular px-4 py-2.5 text-right">
                            {formatNumber(sample.phosphorus, 0)}
                          </td>
                          <td className="tabular px-4 py-2.5 text-right">
                            {formatNumber(sample.potassium, 0)}
                          </td>
                          <td className="tabular px-4 py-2.5 text-right">
                            {formatNumber(sample.organic_matter, 1)}
                          </td>
                          <td className="px-4 py-2.5 text-muted-foreground">
                            {sample.texture ?? "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      <PlantCropDialog
        fieldId={fieldId}
        open={planting}
        onClose={() => setPlanting(false)}
      />
      <SoilDialog
        fieldId={fieldId}
        open={sampling}
        onClose={() => setSampling(false)}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------

type PlantInput = z.input<typeof plantingSchema>;
type PlantOutput = z.output<typeof plantingSchema>;

function PlantCropDialog({
  fieldId,
  open,
  onClose,
}: {
  fieldId: number;
  open: boolean;
  onClose: () => void;
}) {
  const crops = useCrops();
  const createPlanting = useCreatePlanting(fieldId);
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<PlantInput, unknown, PlantOutput>({
    resolver: standardSchemaResolver(plantingSchema),
    defaultValues: {
      crop_id: "",
      sowing_date: todayIso(),
      planting_area_ha: "",
      notes: "",
    },
  });
  const { formError, report, clear } = useApiFormError<PlantInput>(setError, [
    "crop_id",
    "sowing_date",
    "planting_area_ha",
    "notes",
  ]);

  async function onSubmit(values: PlantOutput) {
    clear();
    try {
      await createPlanting.mutateAsync(values);
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
      title="Plant a crop"
      description="The sowing date is what places the crop on its growth-stage curve."
    >
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {formError && (
          <Notice tone="danger" title="Could not save">
            {formError}
          </Notice>
        )}

        {crops.isError && (
          <Notice tone="danger" title="Could not load crops">
            {humanMessage(crops.error)}
          </Notice>
        )}

        <SelectField
          label="Crop"
          placeholder={crops.isPending ? "Loading crops…" : "Choose a crop"}
          disabled={crops.isPending || crops.isError}
          options={(crops.data ?? []).map((crop) => ({
            value: String(crop.id),
            label: crop.name,
          }))}
          error={errors.crop_id?.message}
          required
          {...register("crop_id")}
        />
        <TextField
          label="Sowing date"
          type="date"
          error={errors.sowing_date?.message}
          required
          {...register("sowing_date")}
        />
        <NumberField
          label="Planted area"
          unit="hectares"
          hint="Leave blank to use the whole field."
          error={errors.planting_area_ha?.message}
          {...register("planting_area_ha")}
        />
        <TextAreaField
          label="Notes"
          error={errors.notes?.message}
          {...register("notes")}
        />

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="secondary" onClick={close}>
            Cancel
          </Button>
          <Button type="submit" loading={isSubmitting} loadingText="Saving…">
            <Sprout className="size-4" />
            Save planting
          </Button>
        </div>
      </form>
    </FormDialog>
  );
}

// ---------------------------------------------------------------------------

type SoilInput = z.input<typeof soilSchema>;
type SoilOutput = z.output<typeof soilSchema>;

function SoilDialog({
  fieldId,
  open,
  onClose,
}: {
  fieldId: number;
  open: boolean;
  onClose: () => void;
}) {
  const addSoil = useAddSoil(fieldId);
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<SoilInput, unknown, SoilOutput>({
    resolver: standardSchemaResolver(soilSchema),
    defaultValues: {
      sample_date: todayIso(),
      ph_level: "",
      nitrogen: "",
      phosphorus: "",
      potassium: "",
      organic_matter: "",
      texture: "",
    },
  });
  const { formError, report, clear } = useApiFormError<SoilInput>(setError, [
    "sample_date",
    "ph_level",
    "nitrogen",
    "phosphorus",
    "potassium",
    "organic_matter",
    "texture",
  ]);

  async function onSubmit(values: SoilOutput) {
    clear();
    try {
      await addSoil.mutateAsync(values);
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
      title="Add a soil reading"
      description="Enter what you have. Anything left blank is recorded as not measured, not as zero."
    >
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {formError && (
          <Notice tone="danger" title="Could not save">
            {formError}
          </Notice>
        )}

        <TextField
          label="Sample date"
          type="date"
          error={errors.sample_date?.message}
          {...register("sample_date")}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <NumberField
            label="pH"
            unit="0–14"
            error={errors.ph_level?.message}
            {...register("ph_level")}
          />
          <NumberField
            label="Organic matter"
            unit="%"
            error={errors.organic_matter?.message}
            {...register("organic_matter")}
          />
          <NumberField
            label="Nitrogen"
            unit="kg/ha"
            error={errors.nitrogen?.message}
            {...register("nitrogen")}
          />
          <NumberField
            label="Phosphorus"
            unit="kg/ha"
            error={errors.phosphorus?.message}
            {...register("phosphorus")}
          />
          <NumberField
            label="Potassium"
            unit="kg/ha"
            error={errors.potassium?.message}
            {...register("potassium")}
          />
          <TextField
            label="Texture"
            error={errors.texture?.message}
            {...register("texture")}
          />
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="secondary" onClick={close}>
            Cancel
          </Button>
          <Button type="submit" loading={isSubmitting} loadingText="Saving…">
            <Droplets className="size-4" />
            Save reading
          </Button>
        </div>
      </form>
    </FormDialog>
  );
}
