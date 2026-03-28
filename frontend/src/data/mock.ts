import type { SettingsItem } from "@/types/domain";

export const brandingSettings: SettingsItem[] = [
  {
    label: "Primary Accent",
    value: "#FF7A1A",
    description: "Buttons, chart accents, active navigation, and status highlights.",
  },
  {
    label: "Sidebar Surface",
    value: "#1A1A1A",
    description: "Dark operational shell used for the main left navigation.",
  },
  {
    label: "Workspace Background",
    value: "#F3F3F3",
    description: "Light content surface that keeps dense dashboard data readable.",
  },
];

export const accountSettings: SettingsItem[] = [
  {
    label: "Display Name",
    value: "Admin Console",
    description: "Placeholder account profile for the current operating session.",
  },
  {
    label: "Role",
    value: "Admin",
    description: "Role-based access placeholder until backend JWT wiring is connected.",
  },
  {
    label: "Workspace",
    value: "AegisCore SOC",
    description: "Current team environment for cybersecurity operations monitoring.",
  },
];

export const systemConfig: SettingsItem[] = [
  {
    label: "API Mode",
    value: "Connected",
    description: "The dashboard, analytics, incidents, alerts, and integrations pages use live backend data.",
  },
  {
    label: "Realtime Feed",
    value: "WebSocket enabled",
    description: "Live alert notifications and dashboard refreshes are available through the backend stream.",
  },
  {
    label: "Analytics Focus",
    value: "Explainable ML",
    description: "The anomaly workspace is tailored to presentation-friendly, explainable outputs.",
  },
];
