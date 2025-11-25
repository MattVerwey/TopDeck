/**
 * Live Diagnostics End-to-End Tests
 *
 * Tests for the Live Diagnostics feature including:
 * - Loading the diagnostics panel
 * - Viewing service health
 * - Filtering anomalies
 * - Navigating between tabs
 * - Testing connection status indicators
 */

import { test, expect, Page } from "@playwright/test";
import {
  mockSnapshotResponse,
  mockHealthResponse,
  mockAnomaliesResponse,
} from "./fixtures/mock-diagnostics-data";

/**
 * Common WebSocket mock init script that speeds up timers and mocks WebSocket
 * to fail immediately, triggering polling fallback
 */
const webSocketMockScript = `
  // Speed up setTimeout to reduce reconnection delays
  const originalSetTimeout = window.setTimeout;
  window.setTimeout = (fn, delay, ...args) => {
    const newDelay = Math.min(delay || 0, 50);
    return originalSetTimeout(fn, newDelay, ...args);
  };
  
  // Override WebSocket to fail and trigger polling fallback
  window.WebSocket = class MockWebSocket {
    constructor(url) {
      this.readyState = 3;
      originalSetTimeout(() => {
        if (this.onclose) {
          this.onclose(new CloseEvent("close", { code: 1006, reason: "Connection failed" }));
        }
      }, 10);
    }
    send() {}
    close() {}
  };
  window.WebSocket.OPEN = 1;
  window.WebSocket.CLOSED = 3;
  window.WebSocket.CONNECTING = 0;
  window.WebSocket.CLOSING = 2;
`;

/**
 * Helper to set up API mocks for the diagnostics endpoints
 * Also mocks WebSocket to fail immediately and trigger polling fallback
 */
async function setupApiMocks(page: Page) {
  // Speed up timers and mock WebSocket to fail immediately
  await page.addInitScript(webSocketMockScript);

  // Mock all requests to API endpoints (both localhost:8000 and current host)
  await page.route("**/**/api/v1/live-diagnostics/snapshot*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockSnapshotResponse),
    });
  });

  // Mock the health endpoint
  await page.route("**/**/api/v1/live-diagnostics/health*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockHealthResponse),
    });
  });

  // Mock the anomalies endpoint
  await page.route("**/**/api/v1/live-diagnostics/anomalies*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockAnomaliesResponse),
    });
  });
}

test.describe("Live Diagnostics Panel", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
  });

  test("should load the diagnostics panel", async ({ page }) => {
    await page.goto("/live-diagnostics");

    // Check the page title is present
    await expect(page.getByRole("heading", { name: "Live Diagnostics" })).toBeVisible();

    // Check that summary cards are displayed (may need loading time)
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Active Anomalies")).toBeVisible();
    // Use first() to handle multiple matches (card label + tab)
    await expect(page.getByText("Failing Dependencies").first()).toBeVisible();
    await expect(page.getByText("Abnormal Traffic")).toBeVisible();
  });

  test("should display service count correctly", async ({ page }) => {
    await page.goto("/live-diagnostics");

    // Wait for data to load
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });

    // Should show 3 services from mock data
    const serviceCard = page.locator("text=Total Services").locator("..");
    await expect(serviceCard.getByRole("heading", { level: 4 })).toContainText("3");
  });

  test("should display anomaly count correctly", async ({ page }) => {
    await page.goto("/live-diagnostics");

    await expect(page.getByText("Active Anomalies")).toBeVisible({ timeout: 10000 });

    // Should show 4 anomalies from mock data
    const anomalyCard = page.locator("text=Active Anomalies").locator("..");
    await expect(anomalyCard.getByRole("heading", { level: 4 })).toContainText("4");

    // Check critical count
    await expect(anomalyCard.getByText("1 critical")).toBeVisible();
  });

  test("should display overall system health status", async ({ page }) => {
    await page.goto("/live-diagnostics");

    // Wait for the health status chip to appear
    await expect(page.getByText(/System: degraded/i)).toBeVisible({ timeout: 10000 });
  });

  test("should display connection status indicator", async ({ page }) => {
    await page.goto("/live-diagnostics");

    // Wait for data to load first
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });
    
    // The connection status chip should show Polling after WebSocket fallback
    // Use getByLabel for more specific targeting
    const connectionChip = page.getByLabel("Connection: Polling (Fallback)");
    await expect(connectionChip).toBeVisible({ timeout: 5000 });
  });

  test("should have a working refresh button", async ({ page }) => {
    await page.goto("/live-diagnostics");

    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });

    // Find and click the refresh button
    const refreshButton = page.getByRole("button", { name: /Refresh/i });
    await expect(refreshButton).toBeVisible();
    await refreshButton.click();

    // Should still show data after refresh
    await expect(page.getByText("Total Services")).toBeVisible();
  });
});

test.describe("Tab Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto("/live-diagnostics");
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });
  });

  test("should navigate to Topology tab", async ({ page }) => {
    const topologyTab = page.getByRole("tab", { name: /Topology/i });
    await expect(topologyTab).toBeVisible();

    // Topology tab should be selected by default
    await expect(topologyTab).toHaveAttribute("aria-selected", "true");
  });

  test("should navigate to Anomalies tab", async ({ page }) => {
    const anomaliesTab = page.getByRole("tab", { name: /Anomalies/i });
    await anomaliesTab.click();

    // Check tab is selected
    await expect(anomaliesTab).toHaveAttribute("aria-selected", "true");
  });

  test("should navigate to Traffic Patterns tab", async ({ page }) => {
    const trafficTab = page.getByRole("tab", { name: /Traffic Patterns/i });
    await trafficTab.click();

    await expect(trafficTab).toHaveAttribute("aria-selected", "true");

    // Check that traffic pattern content is visible
    const tabPanel = page.locator('[id="diagnostics-tabpanel-2"]');
    await expect(tabPanel).toBeVisible();
  });

  test("should navigate to Failing Dependencies tab", async ({ page }) => {
    const dependenciesTab = page.getByRole("tab", { name: /Failing Dependencies/i });
    await dependenciesTab.click();

    await expect(dependenciesTab).toHaveAttribute("aria-selected", "true");

    // Check that failing dependencies content is visible
    const tabPanel = page.locator('[id="diagnostics-tabpanel-3"]');
    await expect(tabPanel).toBeVisible();
  });
});

test.describe("Anomalies View", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto("/live-diagnostics");
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });

    // Navigate to Anomalies tab and wait for content
    await page.getByRole("tab", { name: /Anomalies/i }).click();
    await expect(page.getByRole("tab", { name: /Anomalies/i })).toHaveAttribute("aria-selected", "true");
  });

  test("should display list of anomalies", async ({ page }) => {
    // Check that anomaly metric names from mock data are displayed
    await expect(page.getByText("error_rate").first()).toBeVisible();
    await expect(page.getByText("latency_p99").first()).toBeVisible();
  });

  test("should show anomaly severity badges", async ({ page }) => {
    // Check for severity chips - use first() to handle multiple matches
    await expect(page.getByText("critical").first()).toBeVisible();
    await expect(page.getByText("high").first()).toBeVisible();
  });

  test("should show anomaly messages", async ({ page }) => {
    await expect(page.getByText("Error rate exceeded 80% threshold")).toBeVisible();
    await expect(page.getByText("P99 latency exceeded 500ms threshold")).toBeVisible();
  });
});

test.describe("Failing Dependencies View", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto("/live-diagnostics");
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });

    // Navigate to Failing Dependencies tab and wait for content
    await page.getByRole("tab", { name: /Failing Dependencies/i }).click();
    await expect(page.getByRole("tab", { name: /Failing Dependencies/i })).toHaveAttribute("aria-selected", "true");
  });

  test("should display failing dependencies list", async ({ page }) => {
    // Check that dependency relationships are shown
    await expect(page.getByText(/api-gateway.*→.*payment-service/)).toBeVisible();
    await expect(page.getByText(/api-gateway.*→.*user-service/)).toBeVisible();
  });

  test("should show dependency status", async ({ page }) => {
    // Check for status indicators - use first() to handle multiple matches
    await expect(page.getByText("failed").first()).toBeVisible();
    await expect(page.getByText("degraded").first()).toBeVisible();
  });

  test("should show health score for dependencies", async ({ page }) => {
    await expect(page.getByText(/Health: 15\.0%/)).toBeVisible();
    await expect(page.getByText(/Health: 65\.0%/)).toBeVisible();
  });
});

test.describe("Traffic Patterns View", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto("/live-diagnostics");
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });

    // Navigate to Traffic Patterns tab
    await page.getByRole("tab", { name: /Traffic Patterns/i }).click();
  });

  test("should display traffic pattern chart area", async ({ page }) => {
    // Traffic patterns tab should be visible
    const tabPanel = page.locator('[id="diagnostics-tabpanel-2"]');
    await expect(tabPanel).toBeVisible();
  });
});

test.describe("Error Handling", () => {
  test("should handle API errors gracefully", async ({ page }) => {
    // Use the common WebSocket mock script
    await page.addInitScript(webSocketMockScript);

    // Mock API to return error
    await page.route("**/**/api/v1/live-diagnostics/snapshot*", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Internal server error" }),
      });
    });

    await page.goto("/live-diagnostics");

    // Page should not crash - either shows error or loading state
    await expect(page).toHaveURL("/live-diagnostics");

    // Should show the error alert
    await expect(page.getByRole("alert")).toBeVisible({ timeout: 5000 });
  });

  test("should show loading state while fetching data", async ({ page }) => {
    // Use the common WebSocket mock script
    await page.addInitScript(webSocketMockScript);

    // Delay the API response to show loading state (use shorter delay for efficiency)
    await page.route("**/**/api/v1/live-diagnostics/snapshot*", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockSnapshotResponse),
      });
    });

    await page.goto("/live-diagnostics");

    // Should show loading indicator initially (before data loads)
    const loadingIndicator = page.locator('[role="progressbar"]');
    await expect(loadingIndicator).toBeVisible({ timeout: 500 });

    // After loading, data should be visible
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Service Click Interaction", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto("/live-diagnostics");
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });
  });

  test("should allow clicking on failing dependency items", async ({
    page,
  }) => {
    // Navigate to Failing Dependencies tab and wait for it to be selected
    await page.getByRole("tab", { name: /Failing Dependencies/i }).click();
    await expect(page.getByRole("tab", { name: /Failing Dependencies/i })).toHaveAttribute("aria-selected", "true");

    // Click on a failing dependency - check that click is possible
    const dependencyItem = page.locator("li").filter({
      hasText: /api-gateway.*→.*payment-service/,
    });
    await expect(dependencyItem).toBeVisible();
    
    // Clicking should not throw an error
    await dependencyItem.click();
  });
});

test.describe("Accessibility", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
  });

  test("should have proper ARIA labels for tabs", async ({ page }) => {
    await page.goto("/live-diagnostics");
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });

    // Check tabs have proper aria attributes
    const tabs = page.getByRole("tab");
    await expect(tabs).toHaveCount(4);

    // Each tab should have aria-selected attribute
    for (const tab of await tabs.all()) {
      await expect(tab).toHaveAttribute("aria-selected");
    }
  });

  test("should have proper heading structure", async ({ page }) => {
    await page.goto("/live-diagnostics");
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });

    // Main heading should be h1
    const mainHeading = page.getByRole("heading", { name: "Live Diagnostics", level: 1 });
    await expect(mainHeading).toBeVisible();
  });

  test("tabs should have proper accessibility attributes", async ({ page }) => {
    await page.goto("/live-diagnostics");
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });

    // Tabs should have role="tab" and one should be selected
    const selectedTab = page.getByRole("tab", { selected: true });
    await expect(selectedTab).toBeVisible();
    
    // Clicking a different tab should change the selected state
    const anomaliesTab = page.getByRole("tab", { name: /Anomalies/i });
    await anomaliesTab.click();
    await expect(anomaliesTab).toHaveAttribute("aria-selected", "true");
  });
});
