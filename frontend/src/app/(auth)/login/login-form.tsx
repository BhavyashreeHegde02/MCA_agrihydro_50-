"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { standardSchemaResolver } from "@hookform/resolvers/standard-schema";
import { ArrowRight, Lock, Mail, Sprout, UserPlus, Zap } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Notice } from "@/components/ui/notice";
import { TextField } from "@/components/ui/form-fields";
import { auth } from "@/lib/api/client";
import { ApiError, humanMessage } from "@/lib/api/errors";
import { loginSchema, type LoginValues } from "@/lib/validation/schemas";
import { AuthFarmIllustration } from "@/components/agro-illustrations/AuthFarmIllustration";

export function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [formError, setFormError] = useState<string | null>(null);

  const rawNext = params.get("next");
  const next =
    rawNext && rawNext.startsWith("/") && !rawNext.startsWith("//")
      ? rawNext
      : "/dashboard";

  const expired = params.get("reason") === "expired";
  const isDemoParam = params.get("demo") === "true";

  const {
    register,
    handleSubmit,
    setValue,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({
    resolver: standardSchemaResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  // Automatically prefill if ?demo=true in URL
  useEffect(() => {
    if (isDemoParam) {
      setValue("email", "demo@jalachakra.example.com", { shouldValidate: true });
      setValue("password", "demo-password-123", { shouldValidate: true });
    }
  }, [isDemoParam, setValue]);

  function fillDemoCredentials() {
    setValue("email", "demo@jalachakra.example.com", { shouldValidate: true });
    setValue("password", "demo-password-123", { shouldValidate: true });
    setFormError(null);
  }

  async function onSubmit(values: LoginValues) {
    setFormError(null);
    try {
      await auth.login(values.email, values.password);
      router.replace(next);
      router.refresh();
    } catch (error) {
      if (error instanceof ApiError && error.isValidation) {
        for (const [field, problem] of Object.entries(error.fieldMap())) {
          if (field === "email" || field === "password") {
            setError(field, { message: problem });
          }
        }
        if (error.fields.length > 0) return;
      }
      setFormError(humanMessage(error));
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
      {/* LEFT 45%: Living Farm Illustration */}
      <div className="hidden lg:block lg:col-span-5">
        <AuthFarmIllustration
          headline="Welcome Back, Farmer 🌱"
          subheadline="Log in to monitor crop growth stages, check today's transpiration demand, and record irrigation applications."
        />
      </div>

      {/* RIGHT 55%: Clean White/Cream Login Card */}
      <div className="lg:col-span-7 flex flex-col justify-center">
        <Card className="border border-emerald-200/90 bg-white shadow-xl shadow-emerald-950/5 rounded-3xl overflow-hidden">
          <CardContent className="space-y-6 p-6 sm:p-9">
            {/* Header */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100/80 px-2.5 py-0.5 rounded-full">
                  ರೈತರ ಲಾಗಿನ್ · Farmer Access
                </span>
                <span className="text-xs font-semibold text-emerald-800">
                  Karnataka Agricultural Portal
                </span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-foreground tracking-tight">
                Welcome Back to Jalachakra 🌱
              </h2>
              <p className="text-sm text-muted-foreground">
                Let&apos;s make smarter, climate-resilient water decisions for your farm.
              </p>
            </div>

            {expired && (
              <Notice tone="warning" title="Your session ended">
                You were signed out because your session expired. Sign in again to continue.
              </Notice>
            )}

            {formError && (
              <Notice tone="danger" title="Could not sign in">
                {formError}
              </Notice>
            )}

            {/* 1-Click Demo Fill for Evaluators and Presentations */}
            <div className="rounded-2xl border border-amber-300 bg-gradient-to-r from-amber-50 to-emerald-50/50 p-4 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                  <Zap className="size-4 text-amber-500 fill-amber-500" />
                  Presentation &amp; Evaluation Demo
                </span>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={fillDemoCredentials}
                  className="text-xs h-8 border-amber-300 bg-white text-amber-950 hover:bg-amber-100 font-bold shadow-xs"
                >
                  Fill Demo Login
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Pre-seeded evaluator account connected with real Mandya field records and calibrated crop models.
              </p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
              <TextField
                label="Mobile Number or Email"
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
                label="Password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                error={errors.password?.message}
                required
                {...register("password")}
              />

              <div className="pt-2 space-y-3">
                <Button
                  type="submit"
                  size="lg"
                  className="w-full text-base font-bold bg-primary hover:bg-emerald-800 text-white rounded-xl shadow-md shadow-emerald-900/10 h-12"
                  loading={isSubmitting}
                  loadingText="Authenticating your farm…"
                >
                  <span>SIGN IN TO FARM</span>
                  <ArrowRight className="size-4 ml-1.5" />
                </Button>

                <Button
                  asChild
                  variant="outline"
                  size="lg"
                  className="w-full text-sm font-bold border-emerald-300 text-emerald-950 hover:bg-emerald-50 rounded-xl h-11"
                >
                  <Link href="/register">
                    <UserPlus className="size-4 mr-1.5 text-primary" />
                    CREATE NEW FARM ACCOUNT
                  </Link>
                </Button>
              </div>
            </form>

            <div className="pt-2 text-center text-xs text-muted-foreground border-t border-emerald-100">
              <Link href="/" className="hover:text-primary transition-colors font-medium">
                &larr; Back to Jalachakra Agriculture Overview
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
