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
 * Helper to set up API mocks for the diagnostics endpoints
 * Also mocks WebSocket to fail immediately and trigger polling fallback
 */
async function setupApiMocks(page: Page) {
  // Speed up timers and mock WebSocket to fail immediately
  await page.addInitScript(() => {
    // Speed up setTimeout to reduce reconnection delays
    const originalSetTimeout = window.setTimeout;
    window.setTimeout = ((fn: TimerHandler, delay?: number, ...args: unknown[]) => {
      // Reduce all delays to max 50ms to speed up reconnection
      const newDelay = Math.min(delay || 0, 50);
      return originalSetTimeout(fn, newDelay, ...args);
    }) as typeof window.setTimeout;
    
    // Override WebSocket to fail and trigger polling fallback
    (window as unknown as { WebSocket: unknown }).WebSocket = class MockWebSocket {
      onopen: (() => void) | null = null;
      onclose: ((event: CloseEvent) => void) | null = null;
      onerror: ((event: Event) => void) | null = null;
      onmessage: ((event: MessageEvent) => void) | null = null;
      readyState = 3; // CLOSED
      static OPEN = 1;
      static CLOSED = 3;
      static CONNECTING = 0;
      static CLOSING = 2;
      OPEN = 1;
      CLOSED = 3;
      CONNECTING = 0;
      CLOSING = 2;

      constructor(_url: string) {
        // Trigger close immediately
        originalSetTimeout(() => {
          if (this.onclose) {
            this.onclose(new CloseEvent("close", { code: 1006, reason: "Connection failed" }));
          }
        }, 10);
      }

      send() {
        // No-op
      }

      close() {
        // No-op
      }
    };
  });

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

    // Wait for the connection status to appear (either WebSocket or Polling)
    const connectionChip = page.locator('[class*="MuiChip"]').filter({
      hasText: /(WebSocket|Polling)/,
    });
    await expect(connectionChip).toBeVisible({ timeout: 10000 });
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

    // Check that anomaly content is visible
    const tabPanel = page.locator('[id="diagnostics-tabpanel-1"]');
    await expect(tabPanel).toBeVisible();
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

    // Navigate to Anomalies tab
    await page.getByRole("tab", { name: /Anomalies/i }).click();
  });

  test("should display list of anomalies", async ({ page }) => {
    // Check that anomalies from mock data are displayed
    await expect(page.getByText("high_error_rate")).toBeVisible();
    await expect(page.getByText("high_latency")).toBeVisible();
    await expect(page.getByText("memory_pressure")).toBeVisible();
  });

  test("should show anomaly severity badges", async ({ page }) => {
    // Check for severity chips
    await expect(page.getByText("critical")).toBeVisible();
    await expect(page.getByText("high")).toBeVisible();
    await expect(page.getByText("medium")).toBeVisible();
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

    // Navigate to Failing Dependencies tab
    await page.getByRole("tab", { name: /Failing Dependencies/i }).click();
  });

  test("should display failing dependencies list", async ({ page }) => {
    // Check that dependency relationships are shown
    await expect(page.getByText(/api-gateway.*→.*payment-service/)).toBeVisible();
    await expect(page.getByText(/api-gateway.*→.*user-service/)).toBeVisible();
  });

  test("should show dependency status", async ({ page }) => {
    // Check for status indicators
    await expect(page.getByText("failed")).toBeVisible();
    await expect(page.getByText("degraded")).toBeVisible();
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
    // Speed up timers and mock WebSocket to fail
    await page.addInitScript(() => {
      const originalSetTimeout = window.setTimeout;
      window.setTimeout = ((fn: TimerHandler, delay?: number, ...args: unknown[]) => {
        const newDelay = Math.min(delay || 0, 50);
        return originalSetTimeout(fn, newDelay, ...args);
      }) as typeof window.setTimeout;
      
      (window as unknown as { WebSocket: unknown }).WebSocket = class MockWebSocket {
        onopen: (() => void) | null = null;
        onclose: ((event: CloseEvent) => void) | null = null;
        onerror: ((event: Event) => void) | null = null;
        onmessage: ((event: MessageEvent) => void) | null = null;
        readyState = 3;
        static OPEN = 1;
        static CLOSED = 3;
        static CONNECTING = 0;
        static CLOSING = 2;
        OPEN = 1;
        CLOSED = 3;
        CONNECTING = 0;
        CLOSING = 2;

        constructor(_url: string) {
          originalSetTimeout(() => {
            if (this.onclose) {
              this.onclose(new CloseEvent("close", { code: 1006, reason: "Connection failed" }));
            }
          }, 10);
        }

        send() {}
        close() {}
      };
    });

    // Mock API to return error
    await page.route("**/**/api/v1/live-diagnostics/snapshot*", async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Internal server error" }),
      });
    });

    await page.goto("/live-diagnostics");

    // Should show error message (graceful degradation)
    await page.waitForTimeout(2000);

    // Page should not crash - either shows error or loading state
    await expect(page).toHaveURL("/live-diagnostics");

    // Should show the error alert
    await expect(page.getByRole("alert")).toBeVisible({ timeout: 5000 });
  });

  test("should show loading state while fetching data", async ({ page }) => {
    // Speed up timers and mock WebSocket to fail
    await page.addInitScript(() => {
      const originalSetTimeout = window.setTimeout;
      window.setTimeout = ((fn: TimerHandler, delay?: number, ...args: unknown[]) => {
        const newDelay = Math.min(delay || 0, 50);
        return originalSetTimeout(fn, newDelay, ...args);
      }) as typeof window.setTimeout;
      
      (window as unknown as { WebSocket: unknown }).WebSocket = class MockWebSocket {
        onopen: (() => void) | null = null;
        onclose: ((event: CloseEvent) => void) | null = null;
        onerror: ((event: Event) => void) | null = null;
        onmessage: ((event: MessageEvent) => void) | null = null;
        readyState = 3;
        static OPEN = 1;
        static CLOSED = 3;
        static CONNECTING = 0;
        static CLOSING = 2;
        OPEN = 1;
        CLOSED = 3;
        CONNECTING = 0;
        CLOSING = 2;

        constructor(_url: string) {
          originalSetTimeout(() => {
            if (this.onclose) {
              this.onclose(new CloseEvent("close", { code: 1006, reason: "Connection failed" }));
            }
          }, 10);
        }

        send() {}
        close() {}
      };
    });

    // Delay the API response to show loading state
    await page.route("**/**/api/v1/live-diagnostics/snapshot*", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockSnapshotResponse),
      });
    });

    await page.goto("/live-diagnostics");

    // Should show loading indicator initially (before data loads)
    const loadingIndicator = page.locator('[role="progressbar"]');
    await expect(loadingIndicator).toBeVisible({ timeout: 1000 });

    // After loading, data should be visible
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 15000 });
  });
});

test.describe("Service Click Interaction", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await page.goto("/live-diagnostics");
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });
  });

  test("should open error detail drawer when clicking failing dependency", async ({
    page,
  }) => {
    // Navigate to Failing Dependencies tab
    await page.getByRole("tab", { name: /Failing Dependencies/i }).click();

    // Click on a failing dependency
    const dependencyItem = page.locator("li").filter({
      hasText: /api-gateway.*→.*payment-service/,
    });
    await dependencyItem.click();

    // Drawer should open (MUI Drawer component)
    const drawer = page.locator('[class*="MuiDrawer"]');
    await expect(drawer).toBeVisible({ timeout: 5000 });
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

  test("should have proper tab panel IDs", async ({ page }) => {
    await page.goto("/live-diagnostics");
    await expect(page.getByText("Total Services")).toBeVisible({ timeout: 10000 });

    // Tab panels should have proper IDs matching aria-labelledby
    const tab = page.getByRole("tab", { name: /Topology/i });
    await expect(tab).toHaveAttribute("id", "diagnostics-tab-0");
    await expect(tab).toHaveAttribute("aria-controls", "diagnostics-tabpanel-0");
  });
});
