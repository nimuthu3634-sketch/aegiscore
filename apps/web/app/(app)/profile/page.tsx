"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";

export default function ProfilePage() {
  const { data: user } = useAuth();
  const queryClient = useQueryClient();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (user?.full_name) {
      setFullName(user.full_name);
    }
  }, [user?.full_name]);

  const mutation = useMutation({
    mutationFn: () => api.patch("/auth/profile", { full_name: fullName, password: password || undefined }),
    onSuccess: () => {
      setPassword("");
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    },
  });

  return (
    <AppShell title="Profile">
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>My profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Full name</label>
            <Input value={fullName} onChange={(event) => setFullName(event.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Email</label>
            <Input value={user?.email ?? ""} disabled />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">New password</label>
            <Input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </div>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
            Save profile
          </Button>
        </CardContent>
      </Card>
    </AppShell>
  );
}
