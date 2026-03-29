"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { Incident, PageResult } from "@/types/domain";

function downloadText(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function ReportsPage() {
  const [incidentId, setIncidentId] = useState("");
  const { data: incidents } = useQuery({
    queryKey: ["reports-incidents"],
    queryFn: () => api.get<PageResult<Incident>>("/incidents"),
  });

  return (
    <AppShell title="Reports and Export">
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>CSV exports</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={async () => downloadText("alerts.csv", await api.get<string>("/reports/alerts.csv"), "text/csv")}>
              Download alerts CSV
            </Button>
            <Button variant="outline" onClick={async () => downloadText("dashboard.csv", await api.get<string>("/reports/dashboard.csv"), "text/csv")}>
              Download dashboard summary CSV
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Printable incident summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              list="incident-options"
              value={incidentId}
              onChange={(event) => setIncidentId(event.target.value)}
              placeholder="Paste or choose an incident id"
            />
            <datalist id="incident-options">
              {incidents?.items.map((incident) => (
                <option key={incident.id} value={incident.id}>
                  {incident.reference}
                </option>
              ))}
            </datalist>
            <Button
              onClick={async () =>
                downloadText(`incident-${incidentId}.txt`, await api.get<string>(`/reports/incidents/${incidentId}/summary`), "text/plain")
              }
              disabled={!incidentId}
            >
              Download summary
            </Button>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
