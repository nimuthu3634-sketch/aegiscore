"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ShieldCheck, Waves } from "lucide-react";
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
import { appConfig } from "@/lib/config";
import type { User } from "@/types/domain";
import { authDemoUsers } from "@aegiscore/config";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(8, "Password must be at least 8 characters."),
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

export default function LoginPage() {
  const router = useRouter();
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "admin@example.com", password: "Admin123!" },
  });

  const mutation = useMutation({
    mutationFn: (payload: LoginValues) => api.post<LoginResponse>("/auth/login", payload),
    onSuccess: (data) => {
      setAuthSession(data.access_token, data.user);
      startTransition(() => {
        router.push("/dashboard");
      });
    },
  });

  return (
    <div className="relative min-h-screen overflow-hidden bg-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,122,26,0.12),transparent_24%),radial-gradient(circle_at_bottom_right,rgba(17,17,17,0.06),transparent_24%),linear-gradient(180deg,#ffffff_0%,#f7f7f7_100%)]" />
      <div className="relative mx-auto grid min-h-screen max-w-7xl items-center gap-10 px-4 py-10 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
        <div className="space-y-8">
          <Logo />
          <div className="space-y-5">
            <Badge tone="medium">AI-assisted defensive operations</Badge>
            <h1 className="max-w-3xl text-5xl font-semibold leading-[1.02] tracking-[-0.05em] text-[#111111]">
              See alert pressure clearly, explain risk decisions, and keep incident response disciplined.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-[#5f5f5f]">
              {appConfig.appName} combines SOC overview, live alerting, telemetry imports, explainable prioritization, and
              analyst workflow in one clean defensive workspace.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                icon: ShieldCheck,
                title: "Lab-safe integrations",
                text: "Wazuh and Suricata telemetry plus import-only Nmap and Hydra results.",
              },
              {
                icon: Waves,
                title: "Live operations signal",
                text: "Realtime alert updates keep the dashboard and analyst views current.",
              },
              {
                icon: ShieldCheck,
                title: "Explainable scoring",
                text: "Every risk score is backed by visible factors and recommendation context.",
              },
            ].map((item) => (
              <Card key={item.title} className="bg-white/80 backdrop-blur">
                <CardContent className="space-y-4">
                  <div className="inline-flex rounded-2xl bg-[#fff4eb] p-3 text-[#FF7A1A]">
                    <item.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-[#111111]">{item.title}</h2>
                    <p className="mt-2 text-sm leading-6 text-[#676767]">{item.text}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        <Card className="border-white/70 bg-white/90 backdrop-blur">
          <CardContent className="space-y-6 py-8">
            <div className="space-y-2">
              <p className="text-xs uppercase tracking-[0.3em] text-[#8f8f8f]">Secure sign in</p>
              <h2 className="text-2xl font-semibold tracking-[-0.03em] text-[#111111]">Enter the operations workspace</h2>
              <p className="text-sm leading-6 text-[#676767]">
                Use one of the seeded roles below or sign in with your own API-backed account.
              </p>
            </div>

            <form className="space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
              <FormField label="Email" error={form.formState.errors.email?.message}>
                <Input {...form.register("email")} autoComplete="email" placeholder="analyst@example.com" />
              </FormField>
              <FormField label="Password" error={form.formState.errors.password?.message}>
                <Input {...form.register("password")} autoComplete="current-password" type="password" placeholder="Your password" />
              </FormField>

              {mutation.error instanceof Error ? (
                <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{mutation.error.message}</div>
              ) : null}

              <Button className="w-full" size="lg" type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "Signing in..." : "Access AegisCore"}
              </Button>
            </form>

            <div className="rounded-[1.5rem] border bg-[#fafafa] p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Seeded accounts</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {authDemoUsers.map((email) => (
                  <button
                    key={email}
                    type="button"
                    className="rounded-full border bg-white px-3 py-1.5 text-sm text-[#111111] transition hover:border-[#FF7A1A] hover:text-[#FF7A1A]"
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
      </div>
    </div>
  );
}
