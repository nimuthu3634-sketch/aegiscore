import type { NmapImportItem } from "@/types/domain";

export const nmapDemoResults: NmapImportItem[] = [
  {
    host: "lab-admin-01",
    open_ports: [
      { port: 22, service_name: "ssh", protocol: "tcp", state: "open" },
      { port: 3389, service_name: "ms-wbt-server", protocol: "tcp", state: "open" },
      { port: 5985, service_name: "winrm", protocol: "tcp", state: "open" },
    ],
    service_names: ["ssh", "ms-wbt-server", "winrm"],
    scan_timestamp: "2026-03-15T08:15:00Z",
    scan_notes: "Authorized perimeter validation import from a scheduled hardening review.",
  },
  {
    host: "lab-db-01",
    open_ports: [
      { port: 22, service_name: "ssh", protocol: "tcp", state: "open" },
      { port: 5432, service_name: "postgresql", protocol: "tcp", state: "open" },
    ],
    service_names: ["ssh", "postgresql"],
    scan_timestamp: "2026-03-15T08:32:00Z",
    scan_notes: "Imported authorized lab scan output for database exposure review. No live scan is triggered by AegisCore.",
  },
  {
    host: "lab-web-02",
    open_ports: [
      { port: 80, service_name: "http", protocol: "tcp", state: "open" },
      { port: 443, service_name: "https", protocol: "tcp", state: "open" },
      { port: 8443, service_name: "https-alt", protocol: "tcp", state: "open" },
    ],
    service_names: ["http", "https", "https-alt"],
    scan_timestamp: "2026-03-15T08:48:00Z",
    scan_notes: "Authorized result import for web service baseline comparison.",
  },
];
