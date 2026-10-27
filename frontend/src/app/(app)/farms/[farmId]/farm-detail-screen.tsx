"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { standardSchemaResolver } from "@hookform/resolvers/standard-schema";
import { ArrowLeft, ChevronRight, LandPlot, Plus } from "lucide-react";
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
import { NumberField, SelectField, TextField } from "@/components/ui/form-fields";
import { humanMessage } from "@/lib/api/errors";
import { useCreateField, useFarm, useFields } from "@/lib/api/queries";
import { formatArea, formatPercent, humaniseSlug } from "@/lib/format";
import { useApiFormError } from "@/lib/use-api-form";
import { IRRIGATION_METHODS, fieldSchema } from "@/lib/validation/schemas";

type Input = z.input<typeof fieldSchema>;
type Output = z.output<typeof fieldSchema>;

const FIELD_NAMES = [
  "name",
  "area_ha",
  "soil_type",
  "irrigation_method",
  "irrigation_efficiency",
] as const;

export function FarmDetailScreen({ farmId }: { farmId: number }) {
  const [creating, setCreating] = useState(false);
  const farm = useFarm(farmId);
  const fields = useFields(farmId);

  const usedArea = (fields.data ?? []).reduce(
    (sum, field) => sum + field.area_ha,
    0,
  );
  const remaining = (farm.data?.total_area_ha ?? 0) - usedArea;

  return (
    <div className="space-y-6">
      <Link
        href="/farms"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-primary"
      >
        <ArrowLeft className="size-4" />
        All farms
      </Link>

      {farm.isPending && <LoadingState label="Loading the farm…" />}

      {farm.isError && (
        <ErrorState
          message={humanMessage(farm.error)}
          onRetry={() => farm.refetch()}
        />
      )}

      {farm.isSuccess && (
        <>
          <header className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">
                {farm.data.name}
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                {[farm.data.taluk, farm.data.district, farm.data.state]
                  .filter(Boolean)
                  .join(", ") || "No location recorded"}
              </p>
            </div>
            <Button onClick={() => setCreating(true)}>
              <Plus className="size-4" />
              Add field
            </Button>
          </header>

          <section className="grid gap-3 sm:grid-cols-3">
            <Stat
              label="Total area"
              value={formatArea(farm.data.total_area_ha)}
              unit="ha"
            />
            <Stat label="Fields" value={fields.data?.length ?? "—"} />
            <Stat
              label="Unallocated"
              value={fields.isSuccess ? formatArea(remaining) : "—"}
              unit="ha"
              tone={remaining < 0 ? "danger" : "neutral"}
              hint={
                remaining < 0
                  ? "Fields exceed the farm area"
                  : "Area not yet assigned to a field"
              }
            />
          </section>

          <Card>
            <SectionHeader
              title="Fields"
              description="Irrigation method sets the application efficiency, which is what makes gross irrigation larger than the crop's demand."
            />
            <CardContent>
              {fields.isPending && <LoadingState label="Loading fields…" />}

              {fields.isError && (
                <ErrorState
                  message={humanMessage(fields.error)}
                  onRetry={() => fields.refetch()}
                />
              )}

              {fields.isSuccess && fields.data.length === 0 && (
                <EmptyState
                  icon={LandPlot}
                  title="No fields in this farm"
                  description="A field is the unit a crop is planted in and a prediction is made for."
                  action={
                    <Button onClick={() => setCreating(true)}>
                      <Plus className="size-4" />
                      Add the first field
                    </Button>
                  }
                />
              )}

              {fields.isSuccess && fields.data.length > 0 && (
                <ul className="divide-y divide-border">
                  {fields.data.map((field) => (
                    <li key={field.id}>
                      <Link
                        // Nested under the farm because the backend has no
                        // GET /fields/{id}: the field is read from the farm's
                        // field list, so the farm id has to be in the URL.
                        href={`/farms/${farmId}/fields/${field.id}`}
                        className="-mx-2 flex items-center justify-between gap-3 rounded-lg px-2 py-3 hover:bg-muted"
                      >
                        <div className="min-w-0">
                          <p className="truncate font-medium text-foreground">
                            {field.name}
                          </p>
                          <p className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
                            <span>{formatArea(field.area_ha)} ha</span>
                            {field.soil_type && (
                              <span>· {humaniseSlug(field.soil_type)}</span>
                            )}
                            {field.irrigation_method && (
                              <Badge variant="info">
                                {humaniseSlug(field.irrigation_method)}
                              </Badge>
                            )}
                            {field.irrigation_efficiency !== null &&
                              field.irrigation_efficiency !== undefined && (
                                <span className="text-muted-foreground">
                                  {formatPercent(field.irrigation_efficiency)}{" "}
                                  efficient
                                </span>
                              )}
                          </p>
                        </div>
                        <ChevronRight
                          aria-hidden
                          className="size-5 shrink-0 text-muted-foreground"
                        />
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </>
      )}

      <CreateFieldDialog
        farmId={farmId}
        open={creating}
        onClose={() => setCreating(false)}
      />
    </div>
  );
}

function CreateFieldDialog({
  farmId,
  open,
  onClose,
}: {
  farmId: number;
  open: boolean;
  onClose: () => void;
}) {
  const createField = useCreateField(farmId);
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Input, unknown, Output>({
    resolver: standardSchemaResolver(fieldSchema),
    defaultValues: {
      name: "",
      area_ha: "",
      soil_type: "",
      irrigation_method: "",
      irrigation_efficiency: "",
    },
  });
  const { formError, report, clear } = useApiFormError<Input>(
    setError,
    FIELD_NAMES,
  );

  async function onSubmit(values: Output) {
    clear();
    try {
      await createField.mutateAsync(values);
      reset();
      onClose();
    } catch (error) {
      // The backend rejects a field larger than its farm with
      // AREA_EXCEEDS_FARM, which is about this input specifically.
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
      title="Add a field"
      description="The field must fit inside the farm's total area."
    >
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {formError && (
          <Notice tone="danger" title="Could not save">
            {formError}
          </Notice>
        )}

        <TextField
          label="Field name"
          error={errors.name?.message}
          required
          {...register("name")}
        />
        <NumberField
          label="Area"
          unit="hectares"
          error={errors.area_ha?.message}
          required
          {...register("area_ha")}
        />
        <TextField
          label="Soil type"
          hint="For example: clay loam, sandy loam, black cotton."
          error={errors.soil_type?.message}
          {...register("soil_type")}
        />
        <SelectField
          label="Irrigation method"
          placeholder="Not specified"
          options={IRRIGATION_METHODS.map((method) => ({
            value: method,
            label: humaniseSlug(method),
          }))}
          error={errors.irrigation_method?.message}
          {...register("irrigation_method")}
        />
        <NumberField
          label="Application efficiency"
          unit="0 to 1"
          hint="Leave blank to use the standard figure for the method you chose. Drip delivers more of what is pumped than flood does."
          error={errors.irrigation_efficiency?.message}
          {...register("irrigation_efficiency")}
        />

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="secondary" onClick={close}>
            Cancel
          </Button>
          <Button type="submit" loading={isSubmitting} loadingText="Saving…">
            Save field
          </Button>
        </div>
      </form>
    </FormDialog>
  );
}
