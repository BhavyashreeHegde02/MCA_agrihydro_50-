"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { standardSchemaResolver } from "@hookform/resolvers/standard-schema";
import { ArrowRight, Check, Droplets, MapPin, ShieldCheck, Sprout, User } from "lucide-react";
import type { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Notice } from "@/components/ui/notice";
import { TextField } from "@/components/ui/form-fields";
import { auth } from "@/lib/api/client";
import { ApiError, humanMessage } from "@/lib/api/errors";
import { PASSWORD_MIN, registerSchema } from "@/lib/validation/schemas";
import { AuthFarmIllustration } from "@/components/agro-illustrations/AuthFarmIllustration";

type Input = z.input<typeof registerSchema>;
type Output = z.output<typeof registerSchema>;

const KARNATAKA_DISTRICTS = [
  "Bagalkot",
  "Ballari",
  "Belagavi",
  "Bengaluru Rural",
  "Bengaluru Urban",
  "Bidar",
  "Chamarajanagar",
  "Chikkaballapura",
  "Chikkamagaluru",
  "Chitradurga",
  "Dakshina Kannada",
  "Davanagere",
  "Dharwad",
  "Gadag",
  "Hassan",
  "Haveri",
  "Kalaburagi",
  "Kodagu",
  "Kolar",
  "Koppal",
  "Mandya",
  "Mysuru",
  "Raichur",
  "Ramanagara",
  "Shivamogga",
  "Tumakuru",
  "Udupi",
  "Uttara Kannada",
  "Vijayapura",
  "Yadgir",
];

const NAMED_FIELDS = new Set<keyof Input>([
  "full_name",
  "email",
  "password",
  "phone",
  "state",
  "district",
  "taluk",
]);

export function RegisterForm() {
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    control,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Input, unknown, Output>({
    resolver: standardSchemaResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      confirm_password: "",
      phone: "",
      state: "Karnataka",
      district: "Mandya",
      taluk: "",
    },
    mode: "onChange",
  });

  const watchPassword = useWatch({ control, name: "password" }) || "";
  const watchConfirm = useWatch({ control, name: "confirm_password" }) || "";
  const watchPhone = useWatch({ control, name: "phone" }) || "";

  // Password requirement checks
  const hasMinLength = watchPassword.length >= PASSWORD_MIN;
  const hasUpper = /[A-Z]/.test(watchPassword);
  const hasLower = /[a-z]/.test(watchPassword);
  const hasNumber = /\d/.test(watchPassword);
  const hasSpecial = /[^A-Za-z\d]/.test(watchPassword);
  const isMatch = watchPassword && watchConfirm && watchPassword === watchConfirm;

  // Phone check
  const phoneDigitsOnly = watchPhone.replace(/\D/g, "");
  const isValidPhone = /^[6-9]\d{9}$/.test(watchPhone);

  async function onSubmit(values: Output) {
    setFormError(null);
    try {
      const { confirm_password, ...payload } = values;
      void confirm_password;
      await auth.register(payload);
      router.replace("/dashboard");
      router.refresh();
    } catch (error) {
      if (error instanceof ApiError) {
        let attached = false;
        for (const [field, problem] of Object.entries(error.fieldMap())) {
          if (NAMED_FIELDS.has(field as keyof Input)) {
            setError(field as keyof Input, { message: problem });
            attached = true;
          }
        }
        if (error.code === "EMAIL_ALREADY_REGISTERED" || error.isConflict) {
          setError("email", { message: "An account already uses this email." });
          attached = true;
        }
        if (attached) return;
      }
      setFormError(humanMessage(error));
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
      {/* LEFT 45%: Living Farm Illustration */}
      <div className="hidden lg:block lg:col-span-5">
        <AuthFarmIllustration
          headline="Start Your Smart Farming Journey 🌾"
          subheadline="Register your Karnataka farm to unlock FAO-56 crop water demand, localized soil N-P-K benchmarks, and rainfall-credited irrigation schedules."
        />
      </div>

      {/* RIGHT 55%: Clean White/Cream Registration Card */}
      <div className="lg:col-span-7 flex flex-col justify-center">
        <Card className="border border-emerald-200/90 bg-white shadow-xl shadow-emerald-950/5 rounded-3xl overflow-hidden">
          <CardContent className="space-y-6 p-6 sm:p-9">
            {/* Header */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100/80 px-2.5 py-0.5 rounded-full">
                  ಹೊಸ ರೈತರ ನೋಂದಣಿ · Farmer Registration
                </span>
                <span className="text-xs font-semibold text-emerald-800">
                  Karnataka Agriculture
                </span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-foreground tracking-tight">
                Start Your Smart Farming Journey 🌾
              </h2>
              <p className="text-sm text-muted-foreground">
                Set up your farm profile to calculate exact crop water needs in minutes.
              </p>
            </div>

            {/* Subtle Progress Stepper */}
            <div className="grid grid-cols-4 gap-2 py-1 text-center border-y border-emerald-100">
              <div className="text-xs font-bold text-primary flex items-center justify-center gap-1">
                <span className="size-5 rounded-full bg-primary text-white text-[10px] flex items-center justify-center font-bold">1</span>
                <span className="hidden sm:inline">Details</span>
              </div>
              <div className="text-xs font-bold text-emerald-800 flex items-center justify-center gap-1">
                <span className="size-5 rounded-full bg-emerald-200 text-emerald-900 text-[10px] flex items-center justify-center font-bold">2</span>
                <span className="hidden sm:inline">Farm</span>
              </div>
              <div className="text-xs font-semibold text-muted-foreground flex items-center justify-center gap-1">
                <span className="size-5 rounded-full bg-muted text-muted-foreground text-[10px] flex items-center justify-center">3</span>
                <span className="hidden sm:inline">Crop</span>
              </div>
              <div className="text-xs font-semibold text-muted-foreground flex items-center justify-center gap-1">
                <span className="size-5 rounded-full bg-muted text-muted-foreground text-[10px] flex items-center justify-center">4</span>
                <span className="hidden sm:inline">Water</span>
              </div>
            </div>

            {formError && (
              <Notice tone="danger" title="Could not register">
                {formError}
              </Notice>
            )}

            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
              <TextField
                label="Full Farmer Name"
                autoComplete="name"
                placeholder="e.g. Ramesh Gowda"
                error={errors.full_name?.message}
                required
                {...register("full_name")}
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <TextField
                  label="Email Address"
                  type="email"
                  autoComplete="email"
                  autoCapitalize="none"
                  spellCheck={false}
                  placeholder="farmer@example.com"
                  error={errors.email?.message}
                  required
                  {...register("email")}
                />

                <TextField
                  label="Mobile Number"
                  type="tel"
                  inputMode="numeric"
                  autoComplete="tel"
                  placeholder="9876543210"
                  hint={
                    watchPhone
                      ? `${phoneDigitsOnly.length}/10 digits · ${
                          isValidPhone ? "✓ Valid Indian mobile" : "10 digits (6-9)"
                        }`
                      : "10-digit mobile number"
                  }
                  error={errors.phone?.message}
                  required
                  {...register("phone")}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <TextField
                  label="Password"
                  type="password"
                  autoComplete="new-password"
                  placeholder="••••••••"
                  error={errors.password?.message}
                  required
                  {...register("password")}
                />

                <TextField
                  label="Confirm Password"
                  type="password"
                  autoComplete="new-password"
                  placeholder="••••••••"
                  error={errors.confirm_password?.message}
                  required
                  {...register("confirm_password")}
                />
              </div>

              {/* Password checks indicator */}
              <div className="rounded-xl bg-emerald-50/70 p-3 text-xs text-muted-foreground border border-emerald-200/80 space-y-1">
                <div className="grid grid-cols-2 gap-1.5">
                  <span className={`flex items-center gap-1.5 ${hasMinLength ? "text-emerald-700 font-bold" : ""}`}>
                    {hasMinLength ? <Check className="size-3 text-emerald-600" /> : <span className="size-1.5 rounded-full bg-slate-300" />}
                    At least 8 chars
                  </span>
                  <span className={`flex items-center gap-1.5 ${hasUpper ? "text-emerald-700 font-bold" : ""}`}>
                    {hasUpper ? <Check className="size-3 text-emerald-600" /> : <span className="size-1.5 rounded-full bg-slate-300" />}
                    1 Uppercase (A-Z)
                  </span>
                  <span className={`flex items-center gap-1.5 ${hasLower ? "text-emerald-700 font-bold" : ""}`}>
                    {hasLower ? <Check className="size-3 text-emerald-600" /> : <span className="size-1.5 rounded-full bg-slate-300" />}
                    1 Lowercase (a-z)
                  </span>
                  <span className={`flex items-center gap-1.5 ${hasNumber && hasSpecial ? "text-emerald-700 font-bold" : ""}`}>
                    {hasNumber && hasSpecial ? <Check className="size-3 text-emerald-600" /> : <span className="size-1.5 rounded-full bg-slate-300" />}
                    1 Number &amp; Symbol
                  </span>
                </div>
              </div>

              {/* Farm Location Selection */}
              <div className="pt-2 border-t border-emerald-100 space-y-3">
                <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-800">
                  <MapPin className="size-3.5 text-primary" />
                  <span>Farm Location (Karnataka Region)</span>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <label htmlFor="district-select" className="text-sm font-semibold text-foreground">
                      District
                    </label>
                    <select
                      id="district-select"
                      {...register("district")}
                      className="w-full h-11 rounded-xl border border-emerald-200 bg-white px-3.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-primary"
                    >
                      {KARNATAKA_DISTRICTS.map((d) => (
                        <option key={d} value={d}>
                          {d}
                        </option>
                      ))}
                    </select>
                    {errors.district && (
                      <p className="text-xs text-destructive">{errors.district.message}</p>
                    )}
                  </div>

                  <TextField
                    label="Taluk / Village"
                    placeholder="e.g. Maddur / Pandavapura"
                    error={errors.taluk?.message}
                    {...register("taluk")}
                  />
                </div>
              </div>

              <Button
                type="submit"
                size="lg"
                className="w-full text-base font-bold bg-primary hover:bg-emerald-800 text-white rounded-xl shadow-md shadow-emerald-900/10 h-12 mt-2"
                loading={isSubmitting}
                loadingText="Registering Farm Profile…"
              >
                <span>CREATE FARM ACCOUNT</span>
                <ArrowRight className="size-4 ml-1.5" />
              </Button>
            </form>

            <p className="text-center text-xs text-muted-foreground border-t border-emerald-100 pt-3">
              Already registered your farm?{" "}
              <Link
                href="/login"
                className="font-bold text-primary hover:underline underline-offset-2"
              >
                Sign In Here
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
