export type NavItem = {
  label: string;
  path: string;
  description: string;
};

export const navigationItems: NavItem[] = [
  { label: "Dashboard", path: "/dashboard", description: "SOC overview" },
  { label: "Alerts", path: "/alerts", description: "Triage queue" },
  { label: "Incidents", path: "/incidents", description: "Case workflow" },
  { label: "Reports", path: "/reports", description: "Presentation outputs" },
  { label: "Integrations", path: "/integrations", description: "Data sources" },
  { label: "Settings", path: "/settings", description: "Roles and config" }
];
