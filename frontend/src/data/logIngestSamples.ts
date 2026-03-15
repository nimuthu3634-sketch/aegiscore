import type { LogIngestPayload } from "@/types/domain";

export const logIngestSamples: LogIngestPayload[] = [
  {
    source: "lab-web-02",
    source_tool: "wazuh",
    timestamp: "2026-03-15T15:25:00Z",
    raw_log: {
      host: "lab-web-02",
      message: "Multiple SSH login failures detected from 10.0.0.35",
      user: "ops_admin",
      source_ip: "10.0.0.35",
      severity: "high",
    },
  },
  {
    source_tool: "suricata",
    raw_log: {
      timestamp: "2026-03-15T14:48:00Z",
      sensor: "sensor-north-01",
      message: "Suspicious outbound DNS volume exceeded the expected baseline.",
      src_ip: "10.10.22.12",
      dest_ip: "1.1.1.1",
      severity: "medium",
    },
  },
  {
    source_tool: "nmap",
    raw_log: {
      timestamp: "2026-03-15T13:32:00Z",
      asset: "lab-gateway-03",
      message: "Imported Nmap lab result identified tcp/8080 open.",
      port: 8080,
      service: "http-proxy",
      severity: "medium",
    },
  },
  {
    source_tool: "hydra",
    raw_log: {
      timestamp: "2026-03-15T12:58:00Z",
      asset: "simulation-node-02",
      message: "Imported Hydra assessment result recorded repeated successful matches for managed credentials.",
      username: "test_user",
      attempts: 9,
      severity: "high",
    },
  },
];
