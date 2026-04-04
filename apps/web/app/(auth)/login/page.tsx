"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, LockKeyhole, Radar, ShieldCheck, Workflow } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { startTransition } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useRouter } from "next/navigation";

import { Logo } from "@/components/brand/logo";
import { FormField } from "@/components/forms/form-field";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { setAuthSession } from "@/lib/auth";
import { authWorkspaceUsers } from "@/lib/brand";
import { appConfig } from "@/lib/config";
import type { User } from "@/types/domain";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(8, "Password must be at least 8 characters.").max(128, "Password is too long."),
});

type LoginValues = z.infer<typeof loginSchema>;

type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

const accountDefaults: Record<string, string> = {
  "admin@example.com": "Admin123!",
  "analyst@example.com": "Analyst123!",
  "viewer@example.com": "Viewer123!",
};

const capabilities = [
  {
    icon: ShieldCheck,
    title: "Guardrail-first monitoring",
    text: "Ingest telemetry from Wazuh, Suricata, and lab-imported Nmap and Hydra results in a controlled defensive workflow.",
  },
  {
    icon: Radar,
    title: "Clear operational signal",
    text: "A dashboard-first experience that helps analysts interpret alert pressure and incident posture with clear operational context.",
  },
  {
    icon: Workflow,
    title: "End-to-end triage workflow",
    text: "Move from alert intake through triage, incident management, analytics, and reporting in one integrated workspace.",
  },
];

export default function LoginPage() {
  const router = useRouter();
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "admin@example.com", password: "Admin123!" },
  });

  const mutation = useMutation({
    mutationFn: (payload: LoginValues) => api.post<LoginResponse>("/auth/login", payload),
    onSuccess: (data) => {
      setAuthSession(data.user);
      startTransition(() => {
        router.push("/dashboard");
      });
    },
  });

  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--background)]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,122,26,0.18),transparent_24%),radial-gradient(circle_at_bottom_right,rgba(17,17,17,0.08),transparent_20%)]" />
      <div className="relative mx-auto grid min-h-screen max-w-[1600px] items-stretch gap-8 px-4 py-6 lg:grid-cols-[1.15fr_0.85fr] lg:px-8 lg:py-8">
        <section className="relative flex overflow-hidden rounded-[36px] border border-white/10 bg-[#111111] p-6 text-white shadow-[0_36px_80px_rgba(17,17,17,0.24)] lg:p-8">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,122,26,0.26),transparent_30%),linear-gradient(135deg,#171311_0%,#111111_55%,#0f0d0c_100%)]" />
          <div className="absolute right-[-60px] top-[120px] h-[240px] w-[240px] rounded-full bg-[rgba(255,122,26,0.18)] blur-3xl" />
          <div className="relative flex h-full w-full flex-col">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <Logo tone="light" size="large" />
              <span className="rounded-full border border-white/12 bg-white/[0.05] px-3 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-white/70">
                Defensive SOC platform
              </span>
            </div>

            <div className="mt-10 max-w-3xl space-y-5">
              <Badge tone="high">AI-assisted defensive operations</Badge>
              <h1 className="text-4xl font-semibold leading-[0.98] tracking-[-0.06em] text-white md:text-5xl xl:text-[4.1rem]">
                Build calm from noisy telemetry and keep every analyst decision grounded in evidence.
              </h1>
              <p className="max-w-2xl text-base leading-7 text-white/70">
                {appConfig.appName} brings SOC overview, live alert context, safe lab imports, explainable prioritization,
                and incident workflow into one disciplined defensive interface.
              </p>
            </div>

            <div className="mt-10 grid gap-4 md:grid-cols-3">
              {capabilities.map((item) => (
                <div key={item.title} className="rounded-[28px] border border-white/10 bg-white/[0.05] p-5 backdrop-blur-sm">
                  <div className="inline-flex rounded-2xl bg-[rgba(255,122,26,0.16)] p-3 text-[#FFB067]">
                    <item.icon className="h-5 w-5" />
                  </div>
                  <h2 className="mt-4 text-base font-semibold tracking-[-0.02em] text-white">{item.title}</h2>
                  <p className="mt-3 text-sm leading-6 text-white/68">{item.text}</p>
                </div>
              ))}
            </div>

            <div className="mt-auto grid gap-4 pt-8 lg:grid-cols-[1.1fr_0.9fr]">
              <div className="rounded-[28px] border border-white/10 bg-white/[0.05] p-5">
                <p className="text-[11px] uppercase tracking-[0.3em] text-[#ffb37f]">Operational readiness</p>
                <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-white">Operational visibility from the moment you sign in.</h2>
                <p className="mt-3 text-sm leading-6 text-white/68">
                  Telemetry integrations, explainable risk scoring, real-time alert feeds, and incident workflows
                  give analysts a unified surface for monitoring, triage, and response coordination.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
                {[
                  { label: "Roles", value: "3", detail: "Admin, Analyst, Viewer" },
                  { label: "Sources", value: "4", detail: "Wazuh, Suricata, Nmap, Hydra" },
                  { label: "Mode", value: "Safe", detail: "Controlled defensive ingestion" },
                ].map((item) => (
                  <div key={item.label} className="rounded-[24px] border border-white/10 bg-[#0f0d0c]/55 p-4">
                    <p className="text-[11px] uppercase tracking-[0.24em] text-white/42">{item.label}</p>
                    <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-white">{item.value}</p>
                    <p className="mt-2 text-sm text-white/62">{item.detail}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center">
          <Card className="w-full max-w-[560px] border-black/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(251,246,240,0.9))]">
            <CardContent className="space-y-8 px-6 py-8 sm:px-8">
              <div className="space-y-3">
                <Badge tone="medium">Secure access</Badge>
                <h2 className="text-3xl font-semibold tracking-[-0.05em] text-[#111111]">Enter the operations workspace</h2>
                <p className="text-sm leading-7 text-[#6d635a]">
                  Sign in with your credentials or choose a workspace account to enter the platform.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                {[
                  { label: "Operator roles", value: "3" },
                  { label: "Live dashboard", value: "Active" },
                  { label: "Policy mode", value: "Defensive" },
                ].map((item) => (
                  <div key={item.label} className="rounded-[22px] border border-black/8 bg-white/70 p-4">
                    <p className="text-[11px] uppercase tracking-[0.24em] text-[#8a7d72]">{item.label}</p>
                    <p className="mt-2 text-xl font-semibold tracking-[-0.04em] text-[#111111]">{item.value}</p>
                  </div>
                ))}
              </div>

              <form className="space-y-5" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
                <FormField label="Email" error={form.formState.errors.email?.message}>
                  <Input {...form.register("email")} autoComplete="email" placeholder="analyst@example.com" />
                </FormField>

                <FormField label="Password" hint="Choose a workspace account or enter your own credentials" error={form.formState.errors.password?.message}>
                  <Input
                    {...form.register("password")}
                    autoComplete="current-password"
                    type="password"
                    placeholder="Your password"
                  />
                </FormField>

                {mutation.error instanceof Error ? (
                  <div className="rounded-[20px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{mutation.error.message}</div>
                ) : null}

                <Button className="w-full justify-between" size="lg" type="submit" disabled={mutation.isPending}>
                  <span className="inline-flex items-center gap-2">
                    <LockKeyhole className="h-4 w-4" />
                    {mutation.isPending ? "Signing in..." : "Access AegisCore"}
                  </span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </form>

              <div className="rounded-[24px] border border-black/8 bg-white/65 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-[11px] uppercase tracking-[0.28em] text-[#8a7d72]">Workspace access</p>
                  <span className="text-xs text-[#8a7d72]">Role-based accounts</span>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {authWorkspaceUsers.map((email) => (
                    <button
                      key={email}
                      type="button"
                      className="rounded-full border border-black/10 bg-white px-3 py-2 text-sm font-medium text-[#111111] transition hover:border-[#FF7A1A] hover:text-[#FF7A1A]"
                      onClick={() => {
                        form.setValue("email", email, { shouldDirty: true });
                        form.setValue("password", accountDefaults[email] ?? "Admin123!", { shouldDirty: true });
                      }}
                    >
                      {email}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
