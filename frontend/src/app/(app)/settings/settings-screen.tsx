"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { standardSchemaResolver } from "@hookform/resolvers/standard-schema";
import { CheckCircle2, LogOut } from "lucide-react";
import { toast } from "sonner";
import type { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { TextAreaField, TextField } from "@/components/ui/form-fields";
import { Notice } from "@/components/ui/notice";
import { SectionHeader } from "@/components/ui/section-header";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { auth } from "@/lib/api/client";
import { humanMessage } from "@/lib/api/errors";
import { useProfile, useUpdateProfile, useWeatherStatus } from "@/lib/api/queries";
import { useApiFormError } from "@/lib/use-api-form";
import { profileSchema } from "@/lib/validation/schemas";

type Input = z.input<typeof profileSchema>;
type Output = z.output<typeof profileSchema>;

const FIELD_NAMES = [
  "full_name",
  "phone",
  "state",
  "district",
  "taluk",
  "address",
] as const;

export function SettingsScreen() {
  const profile = useProfile();
  const weather = useWeatherStatus();

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-10">
      {/* Page Header */}
      <header className="rounded-3xl border border-emerald-200/90 bg-gradient-to-r from-emerald-50/70 via-white to-amber-50/30 p-6 sm:p-8 shadow-xs">
        <div className="flex items-center gap-3.5">
          <div className="size-14 rounded-2xl bg-emerald-700 text-white flex items-center justify-center font-bold shadow-md shadow-emerald-900/10 shrink-0">
            <CheckCircle2 className="size-7" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-100/80 px-2.5 py-0.5 rounded-full border border-emerald-300">
              Farmer Profile · ರೈತರ ವಿವರಗಳು
            </span>
            <h1 className="text-2xl sm:text-3xl font-black text-foreground mt-1 tracking-tight">
              Farmer Settings & Profile
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5 max-w-xl">
              Update your contact details, farm location, and view the capabilities available in this deployment of Jalachakra.
            </p>
          </div>
        </div>
      </header>

      {profile.isPending && <LoadingState label="Loading your profile…" />}

      {profile.isError && (
        <ErrorState
          message={humanMessage(profile.error)}
          onRetry={() => profile.refetch()}
        />
      )}

      {profile.isSuccess && <ProfileForm key={profile.dataUpdatedAt} />}

      <Card>
        <SectionHeader
          title="This deployment"
          description="What the service is actually able to do right now."
        />
        <CardContent className="pt-4">
          <dl className="grid gap-x-4 gap-y-2 text-sm sm:grid-cols-[minmax(0,12rem)_1fr]">
            <dt className="text-muted-foreground">Weather provider</dt>
            <dd className="text-foreground">
              {weather.isPending
                ? "checking…"
                : weather.data
                  ? `${weather.data.provider}${weather.data.configured ? "" : " (not configured)"}`
                  : "unknown"}
            </dd>
            {weather.data?.note && (
              <>
                <dt className="text-muted-foreground">Note</dt>
                <dd className="text-muted-foreground">{weather.data.note}</dd>
              </>
            )}
          </dl>
        </CardContent>
      </Card>

      <SignOutCard />
    </div>
  );
}

function ProfileForm() {
  const profile = useProfile();
  const update = useUpdateProfile();
  const [saved, setSaved] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<Input, unknown, Output>({
    resolver: standardSchemaResolver(profileSchema),
    defaultValues: {
      full_name: profile.data?.full_name ?? "",
      phone: profile.data?.phone ?? "",
      state: profile.data?.state ?? "",
      district: profile.data?.district ?? "",
      taluk: profile.data?.taluk ?? "",
      address: profile.data?.address ?? "",
    },
  });
  const { formError, report, clear } = useApiFormError<Input>(
    setError,
    FIELD_NAMES,
  );

  // The success message is transient, not a permanent banner: it confirms an
  // action rather than describing a state.
  useEffect(() => {
    if (!saved) return;
    const timer = setTimeout(() => setSaved(false), 4000);
    return () => clearTimeout(timer);
  }, [saved]);

  async function onSubmit(values: Output) {
    clear();
    try {
      const updated = await update.mutateAsync(values);
      reset({
        full_name: updated.full_name ?? "",
        phone: updated.phone ?? "",
        state: updated.state ?? "",
        district: updated.district ?? "",
        taluk: updated.taluk ?? "",
        address: updated.address ?? "",
      });
      setSaved(true);
      toast.success("Profile saved");
    } catch (error) {
      report(error);
    }
  }

  return (
    <Card>
      <SectionHeader
        title="Farmer profile"
        description="Used to label your farms. Only your name is required."
      />
      <CardContent className="pt-4">
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          {formError && (
            <Notice tone="danger" title="Could not save">
              {formError}
            </Notice>
          )}
          {saved && !formError && (
            <Notice tone="success" icon={CheckCircle2} title="Saved">
              Your profile has been updated.
            </Notice>
          )}

          <TextField
            label="Full name"
            autoComplete="name"
            error={errors.full_name?.message}
            required
            {...register("full_name")}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Phone"
              type="tel"
              autoComplete="tel"
              error={errors.phone?.message}
              {...register("phone")}
            />
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
              label="Taluk"
              error={errors.taluk?.message}
              {...register("taluk")}
            />
          </div>
          <TextAreaField
            label="Address"
            error={errors.address?.message}
            {...register("address")}
          />

          <Button
            type="submit"
            loading={isSubmitting}
            loadingText="Saving…"
            disabled={!isDirty}
          >
            Save changes
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function SignOutCard() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function signOut() {
    setBusy(true);
    try {
      await auth.logout();
    } finally {
      // Whatever the server said, this browser is done. A full refresh also
      // drops every cached query, so the next person to sign in on a shared
      // phone never sees the previous farmer's data.
      router.replace("/login");
      router.refresh();
    }
  }

  return (
    <Card>
      <SectionHeader
        title="Session"
        description="Signing out clears the session cookie on this device and empties the cached data."
      />
      <CardContent className="pt-4">
        <Button
          variant="destructive"
          onClick={signOut}
          loading={busy}
          loadingText="Signing out…"
        >
          <LogOut className="size-4" />
          Sign out
        </Button>
      </CardContent>
    </Card>
  );
}
