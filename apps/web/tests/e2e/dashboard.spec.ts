import { test, expect } from "@playwright/test";

test("user can sign in and load the dashboard", async ({ page }) => {
  await page.route("**/api/v1/auth/login", async (route) => {
    await route.fulfill({
      json: {
        access_token: "token-123",
        token_type: "bearer",
        user: {
          id: "user-1",
          email: "admin@example.com",
          full_name: "Admin User",
          role: "Admin",
          is_active: true,
          created_at: "2026-03-29T00:00:00Z",
        },
      },
    });
  });

  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({
      json: {
        id: "user-1",
        email: "admin@example.com",
        full_name: "Admin User",
        role: "Admin",
        is_active: true,
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

  await page.goto("/login");
  await page.getByRole("button", { name: "Enter workspace" }).click();

  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByText("SOC Overview")).toBeVisible();
  await expect(page.getByText("Open alerts")).toBeVisible();
});
