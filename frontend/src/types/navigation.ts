export type NavItem = {
  label: string;
  path: string;
  description: string;
  icon:
    | "dashboard"
    | "alerts"
    | "incidents"
    | "logs"
    | "reports"
    | "integrations"
    | "settings";
};

export const navigationItems: NavItem[] = [
  { label: "Dashboard", path: "/dashboard", description: "SOC overview", icon: "dashboard" },
  { label: "Alerts", path: "/alerts", description: "Triage queue", icon: "alerts" },
  { label: "Incidents", path: "/incidents", description: "Case workflow", icon: "incidents" },
  { label: "Logs", path: "/logs", description: "Ingestion feed", icon: "logs" },
  { label: "Reports", path: "/reports", description: "Executive views", icon: "reports" },
  {
    label: "Integrations",
    path: "/integrations",
    description: "Source health",
    icon: "integrations",
  },
  { label: "Settings", path: "/settings", description: "Brand and config", icon: "settings" },
];
