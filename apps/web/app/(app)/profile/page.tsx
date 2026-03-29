"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { FormField } from "@/components/forms/form-field";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { passwordPolicyHint, strongPasswordSchema } from "@/lib/validation";
import { useAuth } from "@/hooks/use-auth";
import type { User } from "@/types/domain";

const profileSchema = z.object({
  full_name: z.string().trim().min(2, "Full name is required."),
  password: strongPasswordSchema("Password").optional().or(z.literal("")),
});

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const { data: user, isLoading, isError, refetch } = useAuth();

  const form = useForm<z.infer<typeof profileSchema>>({
    resolver: zodResolver(profileSchema),
    defaultValues: { full_name: "", password: "" },
  });

  useEffect(() => {
    if (user) {
      form.reset({ full_name: user.full_name, password: "" });
    }
  }, [form, user]);

  const mutation = useMutation({
    mutationFn: (values: z.infer<typeof profileSchema>) =>
      api.patch<User>("/auth/profile", {
        full_name: values.full_name,
        password: values.password || undefined,
      }),
    onSuccess: (updatedUser) => {
      form.reset({ full_name: updatedUser.full_name, password: "" });
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });

  if (isLoading) {
    return <LoadingState lines={6} />;
  }

  if (isError || !user) {
    return <ErrorState description="Profile details could not be loaded for this session." onRetry={() => refetch()} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Personal workspace"
        title="Profile"
        description="Manage your display name, rotate your password, and review the account identity currently used for AegisCore access."
        actions={<Badge tone={user.role === "Admin" ? "critical" : user.role === "Analyst" ? "high" : "medium"}>{user.role}</Badge>}
      />

      <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Identity summary</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-[1.25rem] border bg-white p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Email</p>
                <p className="mt-3 font-semibold text-[#111111]">{user.email}</p>
              </div>
              <div className="rounded-[1.25rem] border bg-white p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Role</p>
                <div className="mt-3">
                  <Badge tone={user.role === "Admin" ? "critical" : user.role === "Analyst" ? "high" : "medium"}>{user.role}</Badge>
                </div>
              </div>
              <div className="rounded-[1.25rem] border bg-white p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Last login</p>
                <p className="mt-3 font-semibold text-[#111111]">{formatDate(user.last_login_at)}</p>
              </div>
              <div className="rounded-[1.25rem] border bg-white p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Created</p>
                <p className="mt-3 font-semibold text-[#111111]">{formatDate(user.created_at)}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Account guidance</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm leading-6 text-[#5f5f5f]">
              <div className="rounded-[1.25rem] border bg-white p-4">Profile changes update the authenticated session used across alerts, incidents, reports, and realtime notification channels.</div>
              <div className="rounded-[1.25rem] border bg-white p-4">Password changes are applied immediately and the new credentials are required for the next login.</div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Update profile</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
              <FormField label="Full name" error={form.formState.errors.full_name?.message}>
                <Input {...form.register("full_name")} placeholder="Your display name" />
              </FormField>
              <FormField label="Email address" hint="Read only">
                <Input value={user.email} disabled />
              </FormField>
              <FormField
                label="New password"
                hint={`Leave blank to keep the current password. ${passwordPolicyHint}`}
                error={form.formState.errors.password?.message}
              >
                <Input {...form.register("password")} type="password" placeholder="Enter a new password" />
              </FormField>
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "Saving profile..." : "Save profile changes"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
