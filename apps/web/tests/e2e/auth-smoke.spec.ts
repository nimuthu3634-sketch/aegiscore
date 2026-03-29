import { expect, type Page, test } from "@playwright/test";

type Role = "Admin" | "Analyst" | "Viewer";

async function setSessionCookies(page: Page, role: Role) {
  await page.context().addCookies([
    {
      name: "auth_token",
      value: "session-token",
      url: "http://127.0.0.1:3000",
      httpOnly: true,
      sameSite: "Lax",
    },
    {
      name: "auth_role",
      value: role,
      url: "http://127.0.0.1:3000",
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);
}

async function mockAuthenticatedApp(page: Page, role: Role) {
  await setSessionCookies(page, role);

  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({
      json: {
        id: "user-1",
        email: role === "Viewer" ? "viewer@example.com" : "admin@example.com",
        full_name: role === "Viewer" ? "Viewer User" : "Admin User",
        role,
        is_active: true,
        last_login_at: "2026-03-29T02:00:00Z",
        created_at: "2026-03-29T00:00:00Z",
      },
    });
  });

  await page.route("**/api/v1/dashboard/summary", async (route) => {
    await route.fulfill({
      json: {
        kpis: {
          total_assets: 12,
          open_alerts: 8,
          open_incidents: 2,
          ingestion_today: 144,
          average_risk_score: 72.4,
        },
        severity_breakdown: { critical: 2, high: 3, medium: 2, low: 1 },
        integration_health: { Wazuh: "healthy", Suricata: "healthy" },
        alert_trend: [{ label: "2026-03-29", critical: 2, high: 3, medium: 2, low: 1 }],
        risky_assets: [
          {
            id: "asset-1",
            hostname: "finance-db-01",
            ip_address: "10.0.0.5",
            criticality: 5,
            risk_score: 88,
            risk_summary: "3 active alerts across telemetry sources.",
            created_at: "2026-03-29T00:00:00Z",
          },
        ],
        recent_activity: [
          {
            id: "alert-1",
            timestamp: "2026-03-29T04:00:00Z",
            title: "Repeated SSH authentication failures",
            kind: "alert",
            summary: "High alert from wazuh",
          },
        ],
      },
    });
  });

  await page.route("**/api/v1/alerts**", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            id: "alert-1",
            title: "Repeated SSH authentication failures",
            source: "wazuh",
            source_type: "endpoint-telemetry",
            severity: "high",
            status: "open",
            risk_score: 82,
            explainability: [],
            recommendations: [],
            tags: ["ssh", "authentication"],
            incident_ids: [],
            comments: [],
            response_recommendations: [],
            occurred_at: "2026-03-29T04:00:00Z",
            detected_at: "2026-03-29T04:00:00Z",
            created_at: "2026-03-29T04:00:00Z",
            updated_at: "2026-03-29T04:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 40,
      },
    });
  });

  await page.route("**/api/v1/incidents**", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            id: "incident-1",
            reference: "INC-001",
            title: "Credential abuse investigation",
            status: "open",
            priority: "P2",
            opened_at: "2026-03-29T04:05:00Z",
            evidence: [],
            timeline_events: [],
            linked_alerts: [],
          },
        ],
        total: 1,
        page: 1,
        page_size: 40,
      },
    });
  });

  await page.route("**/api/v1/integrations**", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            id: "integration-1",
            name: "Wazuh",
            slug: "wazuh",
            type: "wazuh",
            health_status: "healthy",
            enabled: true,
            description: "Endpoint telemetry",
            last_synced_at: "2026-03-29T04:00:00Z",
            runs: [],
          },
        ],
        total: 1,
        page: 1,
        page_size: 8,
      },
    });
  });
}

test("unauthenticated users are redirected to login", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByText("Secure sign in")).toBeVisible();
});

test("authenticated admin sessions can load the dashboard shell", async ({ page }) => {
  await mockAuthenticatedApp(page, "Admin");
  await page.goto("/dashboard");

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByText("SOC dashboard")).toBeVisible();
  await expect(page.getByText("Open alerts")).toBeVisible();
  await expect(page.getByText("Integration health")).toBeVisible();
});

test("non-admin sessions are blocked from admin routes", async ({ page }) => {
  await mockAuthenticatedApp(page, "Viewer");
  await page.goto("/admin");

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByText("SOC dashboard")).toBeVisible();
});
