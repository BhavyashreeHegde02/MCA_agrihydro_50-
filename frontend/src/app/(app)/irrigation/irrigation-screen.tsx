"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { standardSchemaResolver } from "@hookform/resolvers/standard-schema";
import { Droplets, Plus, Waves } from "lucide-react";
import { toast } from "sonner";
import type { z } from "zod";

import { IrrigationBreakdown } from "@/components/irrigation-breakdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FormDialog } from "@/components/ui/form-dialog";
import {
  NumberField,
  SelectField,
  TextAreaField,
  TextField,
} from "@/components/ui/form-fields";
import { Notice } from "@/components/ui/notice";
import { SectionHeader } from "@/components/ui/section-header";
import { Stat } from "@/components/ui/stat";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { humanMessage } from "@/lib/api/errors";
import {
  useAllPlantings,
  useHistory,
  useIrrigationRecords,
  useLogIrrigation,
  usePrediction,
} from "@/lib/api/queries";
import {
  IRRIGATION_METHODS,
  irrigationRecordSchema,
} from "@/lib/validation/schemas";
import {
  formatDate,
  formatDepth,
  formatLitres,
  formatPercent,
  humaniseSlug,
  todayIso,
} from "@/lib/format";
import { useApiFormError } from "@/lib/use-api-form";

/**
 * Irrigation: what to apply, and what was applied.
 *
 * The requirement half is driven by the most recent stored prediction for the
 * selected planting — this screen never recalculates demand in the browser,
 * because a second implementation of the water balance would be a second thing
 * that can disagree with the backend.
 */
export function IrrigationScreen() {
  const [chosenFieldCropId, setChosenFieldCropId] = useState("");
  const [logging, setLogging] = useState(false);

  const plantings = useAllPlantings(true);

  // The chosen planting, or the first active one. Derived rather than written
  // by an effect, which would render twice before painting.
  const fieldCropId =
    chosenFieldCropId ||
    (plantings.data && plantings.data.length > 0
      ? String(plantings.data[0].id)
      : "");
  const selectedId = fieldCropId ? Number(fieldCropId) : undefined;
  const planting = plantings.data?.find(
    (candidate) => candidate.id === selectedId,
  );

  const history = useHistory(
    { field_crop_id: selectedId, limit: 1 },
    { enabled: selectedId !== undefined },
  );
  const latestId = history.data?.[0]?.id ?? 0;
  const latest = usePrediction(latestId, { enabled: latestId > 0 });
  const records = useIrrigationRecords(selectedId);

  const noPlantings = plantings.isSuccess && plantings.data.length === 0;

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      {/* Page Header */}
      <header className="rounded-3xl border border-emerald-200/90 bg-gradient-to-r from-sky-50/70 via-white to-emerald-50/40 p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="size-14 rounded-2xl bg-sky-500 text-white flex items-center justify-center font-bold shadow-md shadow-sky-900/10 shrink-0">
              <Waves className="size-7" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-sky-800 bg-sky-100/80 px-2.5 py-0.5 rounded-full border border-sky-200">
                Pump Scheduling · ನೀರಾವರಿ ವೇಳಾಪಟ್ಟಿ
              </span>
              <h1 className="text-2xl sm:text-3xl font-black text-foreground mt-1 tracking-tight">
                Irrigation Scheduling
              </h1>
              <p className="text-xs sm:text-sm text-muted-foreground mt-0.5 max-w-xl">
                How much to apply, why that figure, and a field log of what was actually applied. Calibrated to your crop&apos;s current growth stage.
              </p>
            </div>
          </div>
          {!noPlantings && (
            <Button
              onClick={() => setLogging(true)}
              disabled={!selectedId}
              className="bg-primary text-white font-bold hover:bg-emerald-800 shadow-md shadow-emerald-900/10 shrink-0"
            >
              <Plus className="size-4" />
              Log an Application
            </Button>
          )}
        </div>
      </header>

      {plantings.isPending && <LoadingState label="Loading your plantings…" />}

      {plantings.isError && (
        <ErrorState
          message={humanMessage(plantings.error)}
          onRetry={() => plantings.refetch()}
        />
      )}

      {noPlantings && (
        <Card>
          <CardContent>
            <EmptyState
              icon={Waves}
              title="No active plantings"
              description="Irrigation advice is for a specific crop in a specific field. Add a planting first."
              action={
                <Button asChild>
                  <Link href="/farms">Set up a farm and field</Link>
                </Button>
              }
            />
          </CardContent>
        </Card>
      )}

      {plantings.isSuccess && plantings.data.length > 0 && (
        <>
          <div className="max-w-sm">
            <SelectField
              label="Planting"
              options={plantings.data.map((item) => ({
                value: String(item.id),
                label: `${item.crop_name} — ${item.field_name}`,
              }))}
              value={fieldCropId}
              onChange={(event) => setChosenFieldCropId(event.target.value)}
            />
          </div>

          {history.isPending && <LoadingState label="Finding the latest prediction…" />}

          {history.isSuccess && history.data.length === 0 && (
            <Card>
              <CardContent>
                <EmptyState
                  icon={Droplets}
                  title="No prediction for this planting yet"
                  description="The irrigation requirement is derived from a prediction. Make one and the full calculation will appear here."
                  action={
                    <Button asChild>
                      <Link href={`/predict?fieldCropId=${selectedId}`}>
                        Predict water demand
                      </Link>
                    </Button>
                  }
                />
              </CardContent>
            </Card>
          )}

          {latest.isSuccess && (
            <>
              <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <Stat
                  label="Crop demand"
                  value={formatDepth(latest.data.cwr_mm_day)}
                  unit="mm/day"
                  hint="What the crop will transpire"
                />
                <Stat
                  label="Net requirement"
                  value={formatDepth(latest.data.net_irrigation_mm)}
                  unit="mm"
                  hint="Must reach the root zone"
                />
                <Stat
                  label="Apply this much"
                  value={formatDepth(latest.data.gross_irrigation_mm)}
                  unit="mm"
                  tone="primary"
                  hint={`At ${formatPercent(latest.data.application_efficiency)} efficiency`}
                />
                <Stat
                  label="At the pump"
                  value={
                    latest.data.gross_irrigation_litres !== null
                      ? formatLitres(latest.data.gross_irrigation_litres)
                      : "—"
                  }
                  unit={
                    latest.data.gross_irrigation_litres !== null ? "litres" : undefined
                  }
                />
              </section>

              <Card>
                <SectionHeader
                  title="Why that figure"
                  description={`From the prediction for ${formatDate(latest.data.prediction_date)} — ${humaniseSlug(latest.data.growth_stage)}, day ${latest.data.days_after_sowing}.`}
                  action={
                    <Button asChild variant="outline" size="sm">
                      <Link href={`/predictions/${latest.data.id}`}>
                        Full detail
                      </Link>
                    </Button>
                  }
                />
                <CardContent className="pt-4">
                  <IrrigationBreakdown
                    inputs={{
                      et0MmDay: latest.data.et0_mm_day,
                      kc: latest.data.kc_value,
                      cwrMmDay: latest.data.cwr_mm_day,
                      effectiveRainfallMm: latest.data.effective_rainfall_mm,
                      netIrrigationMm: latest.data.net_irrigation_mm,
                      grossIrrigationMm: latest.data.gross_irrigation_mm,
                      applicationEfficiency: latest.data.application_efficiency,
                      grossIrrigationLitres: latest.data.gross_irrigation_litres,
                      areaHa: planting?.planting_area_ha ?? null,
                    }}
                  />
                </CardContent>
              </Card>

              <Notice tone="warning" title="This is advice, not an instruction">
                The figure assumes the weather used in that prediction and the
                efficiency recorded for your field. If it rained since, or your
                system is not performing as assumed, the number will be wrong in
                a direction you can judge better than the model can. Check the
                soil before you irrigate.
              </Notice>
            </>
          )}

          <Card>
            <SectionHeader
              title="Applications you have recorded"
              description="Your own record of water applied. Analytics compares it with what was required."
            />
            <CardContent className="p-0">
              {records.isPending && (
                <div className="p-4">
                  <LoadingState label="Loading records…" />
                </div>
              )}

              {records.isError && (
                <div className="p-4">
                  <ErrorState
                    message={humanMessage(records.error)}
                    onRetry={() => records.refetch()}
                  />
                </div>
              )}

              {records.isSuccess && records.data.length === 0 && (
                <div className="p-4">
                  <EmptyState
                    icon={Droplets}
                    title="Nothing logged yet"
                    description="Recording what you applied is what lets the analytics screen compare requirement against practice."
                    action={
                      <Button onClick={() => setLogging(true)} disabled={!selectedId}>
                        Log an application
                      </Button>
                    }
                  />
                </div>
              )}

              {records.isSuccess && records.data.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b text-left text-xs tracking-wide text-muted-foreground uppercase">
                      <tr>
                        <th scope="col" className="px-4 py-2.5 font-semibold">Date</th>
                        <th scope="col" className="px-4 py-2.5 font-semibold">Method</th>
                        <th scope="col" className="px-4 py-2.5 text-right font-semibold">Applied</th>
                        <th scope="col" className="px-4 py-2.5 text-right font-semibold">Duration</th>
                        <th scope="col" className="px-4 py-2.5 font-semibold">Notes</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {records.data.map((record) => (
                        <tr key={record.id}>
                          <td className="px-4 py-2.5">
                            {formatDate(record.irrigation_date)}
                          </td>
                          <td className="px-4 py-2.5 text-muted-foreground">
                            {record.method ? humaniseSlug(record.method) : "—"}
                          </td>
                          <td className="tabular px-4 py-2.5 text-right font-medium">
                            {formatDepth(record.water_applied_mm)} mm
                          </td>
                          <td className="tabular px-4 py-2.5 text-right">
                            {record.duration_hours !== null &&
                            record.duration_hours !== undefined
                              ? `${record.duration_hours} h`
                              : "—"}
                          </td>
                          <td className="px-4 py-2.5 text-muted-foreground">
                            {record.notes ?? "—"}
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

      {selectedId !== undefined && (
        <LogIrrigationDialog
          fieldCropId={selectedId}
          open={logging}
          onClose={() => setLogging(false)}
          suggestedMm={latest.data?.gross_irrigation_mm}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

type LogInput = z.input<typeof irrigationRecordSchema>;
type LogOutput = z.output<typeof irrigationRecordSchema>;

function LogIrrigationDialog({
  fieldCropId,
  open,
  onClose,
  suggestedMm,
}: {
  fieldCropId: number;
  open: boolean;
  onClose: () => void;
  suggestedMm?: number;
}) {
  const log = useLogIrrigation();
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LogInput, unknown, LogOutput>({
    resolver: standardSchemaResolver(irrigationRecordSchema),
    defaultValues: {
      irrigation_date: todayIso(),
      water_applied_mm: "",
      method: "",
      duration_hours: "",
      application_efficiency: "",
      notes: "",
    },
  });
  const { formError, report, clear } = useApiFormError<LogInput>(setError, [
    "irrigation_date",
    "water_applied_mm",
    "method",
    "duration_hours",
    "application_efficiency",
    "notes",
  ]);

  async function onSubmit(values: LogOutput) {
    clear();
    try {
      await log.mutateAsync({ field_crop_id: fieldCropId, ...values });
      toast.success("Irrigation recorded");
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
      title="Log an irrigation"
      description="Record what you actually applied, not what was recommended."
    >
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {formError && (
          <Notice tone="danger" title="Could not save">
            {formError}
          </Notice>
        )}

        <TextField
          label="Date"
          type="date"
          error={errors.irrigation_date?.message}
          required
          {...register("irrigation_date")}
        />
        <NumberField
          label="Water applied"
          unit="mm"
          hint={
            suggestedMm !== undefined
              ? `The latest prediction called for ${formatDepth(suggestedMm)} mm.`
              : undefined
          }
          error={errors.water_applied_mm?.message}
          required
          {...register("water_applied_mm")}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <SelectField
            label="Method"
            placeholder="Not specified"
            options={IRRIGATION_METHODS.map((method) => ({
              value: method,
              label: humaniseSlug(method),
            }))}
            error={errors.method?.message}
            {...register("method")}
          />
          <NumberField
            label="Duration"
            unit="hours"
            error={errors.duration_hours?.message}
            {...register("duration_hours")}
          />
        </div>
        <TextAreaField
          label="Notes"
          error={errors.notes?.message}
          {...register("notes")}
        />

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="outline" onClick={close}>
            Cancel
          </Button>
          <Button type="submit" loading={isSubmitting} loadingText="Saving…">
            <Droplets className="size-4" />
            Save record
          </Button>
        </div>
      </form>
    </FormDialog>
  );
}
