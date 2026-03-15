export const wazuhDemoAlerts = [
  {
    id: "wazuh-demo-001",
    timestamp: "2026-03-15T16:10:00Z",
    agent: {
      id: "001",
      name: "lab-web-03",
    },
    manager: {
      name: "wazuh-manager",
    },
    rule: {
      id: 5710,
      level: 10,
      description: "sshd: multiple authentication failures detected",
      groups: ["authentication_failed", "sshd", "pci_dss_10.2.4"],
    },
    full_log: "sshd[21432]: Failed password for invalid user root from 10.0.0.54 port 49302 ssh2",
    data: {
      srcip: "10.0.0.54",
      user: "root",
    },
  },
  {
    id: "wazuh-demo-002",
    timestamp: "2026-03-15T15:42:00Z",
    agent: {
      id: "002",
      name: "endpoint-lab-11",
    },
    manager: {
      name: "wazuh-manager",
    },
    rule: {
      id: 5503,
      level: 7,
      description: "Integrity checksum changed for monitored configuration file",
      groups: ["syscheck", "configuration"],
    },
    full_log: "File '/etc/sudoers' checksum changed on monitored endpoint.",
    syscheck: {
      path: "/etc/sudoers",
      event: "modified",
    },
  },
  {
    id: "wazuh-demo-003",
    timestamp: "2026-03-15T14:56:00Z",
    agent: {
      id: "003",
      name: "endpoint-lab-12",
    },
    manager: {
      name: "wazuh-manager",
    },
    rule: {
      id: 31103,
      level: 13,
      description: "Malware quarantine action reported by endpoint tooling",
      groups: ["malware", "windows", "defender"],
    },
    full_log: "Windows Defender quarantined Trojan:Script/Wacatac.B!ml on classroom endpoint.",
    data: {
      file: "C:\\Users\\Student\\Downloads\\payload.exe",
      action: "quarantined",
    },
  },
];
