"use client";

import { useMutation } from "@tanstack/react-query";
import { Shield } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { setAuthSession } from "@/lib/auth";
import type { User } from "@/types/domain";

type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("Admin123!");
  const [error, setError] = useState("");

  const mutation = useMutation({
    mutationFn: (payload: { email: string; password: string }) => api.post<LoginResponse>("/auth/login", payload),
    onSuccess: (data) => {
      setAuthSession(data.access_token, data.user);
      router.push("/dashboard");
    },
    onError: (issue: Error) => setError(issue.message),
  });

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="grid w-full max-w-5xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-[2rem] bg-[#111111] p-8 text-white shadow-panel">
          <div className="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/80">
            <Shield className="h-4 w-4 text-[#ff7a1a]" />
            AI-assisted defensive SOC
          </div>
          <h1 className="mt-8 max-w-xl text-4xl font-semibold leading-tight">
            Triage alerts faster, keep incidents coherent, and explain every risk decision.
          </h1>
          <p className="mt-4 max-w-xl text-base text-white/70">
            AegisCore brings together defensive telemetry, analyst workflows, live updates, and explainable scoring for
            small and medium organizations.
          </p>
          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            {[
              ["Live alerts", "Realtime websocket updates"],
              ["Explainable AI", "Transparent scoring factors"],
              ["Defensive integrations", "Wazuh, Suricata, Nmap import, Hydra import"],
            ].map(([title, text]) => (
              <div key={title} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="font-semibold">{title}</p>
                <p className="mt-2 text-sm text-white/65">{text}</p>
              </div>
            ))}
          </div>
        </div>
        <Card className="self-center">
          <CardHeader>
            <CardTitle>Sign in to AegisCore</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Email</label>
              <Input value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Password</label>
              <Input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>
            {error ? <p className="text-sm text-red-600">{error}</p> : null}
            <Button className="w-full" onClick={() => mutation.mutate({ email, password })} disabled={mutation.isPending}>
              {mutation.isPending ? "Signing in..." : "Enter workspace"}
            </Button>
            <div className="rounded-2xl border bg-[#fff8f1] p-4 text-sm text-[var(--muted)]">
              Default demo accounts are seeded by the backend: `admin@example.com`, `analyst@example.com`, and
              `viewer@example.com`.
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
