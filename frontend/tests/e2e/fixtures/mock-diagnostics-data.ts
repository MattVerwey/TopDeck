/**
 * Mock Diagnostics Data Fixtures
 *
 * Test fixtures for Live Diagnostics E2E tests
 * Types match the actual frontend types in src/types/diagnostics.ts
 */

export interface ServiceHealthStatus {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  status: "healthy" | "degraded" | "failed" | "unknown";
  health_score: number;
  anomalies: string[];
  metrics: Record<string, number>;
  last_updated: string;
}

export interface AnomalyAlert {
  alert_id: string;
  resource_id: string;
  resource_name: string;
  severity: "low" | "medium" | "high" | "critical";
  metric_name: string;
  current_value: number;
  expected_value: number;
  deviation_percentage: number;
  detected_at: string;
  message: string;
  potential_causes: string[];
}

export interface TrafficPattern {
  source_id: string;
  target_id: string;
  request_rate: number;
  error_rate: number;
  latency_p95: number;
  is_abnormal: boolean;
  anomaly_score: number;
  trend: "increasing" | "decreasing" | "stable";
}

export interface FailingDependency {
  source_id: string;
  source_name: string;
  target_id: string;
  target_name: string;
  status: "degraded" | "failed";
  health_score: number;
  anomalies: string[];
  error_details: {
    status: string;
    health_score: number;
    anomalies: string[];
    metrics: Record<string, number>;
    timestamp: string;
  };
}

export interface LiveDiagnosticsSnapshot {
  timestamp: string;
  overall_health: "healthy" | "degraded" | "critical";
  services: ServiceHealthStatus[];
  anomalies: AnomalyAlert[];
  traffic_patterns: TrafficPattern[];
  failing_dependencies: FailingDependency[];
}

// Sample healthy service
export const healthyService: ServiceHealthStatus = {
  resource_id: "service-001",
  resource_name: "api-gateway",
  resource_type: "service",
  status: "healthy",
  health_score: 95,
  anomalies: [],
  metrics: {
    cpu_usage: 35,
    memory_usage: 45,
    request_rate: 1000,
    error_rate: 0.5,
    latency_p99: 120,
  },
  last_updated: new Date().toISOString(),
};

// Sample degraded service
export const degradedService: ServiceHealthStatus = {
  resource_id: "service-002",
  resource_name: "user-service",
  resource_type: "service",
  status: "degraded",
  health_score: 65,
  anomalies: ["anomaly-002", "anomaly-003"],
  metrics: {
    cpu_usage: 75,
    memory_usage: 80,
    request_rate: 500,
    error_rate: 5.0,
    latency_p99: 800,
  },
  last_updated: new Date().toISOString(),
};

// Sample failed service
export const failedService: ServiceHealthStatus = {
  resource_id: "service-003",
  resource_name: "payment-service",
  resource_type: "service",
  status: "failed",
  health_score: 15,
  anomalies: ["anomaly-001"],
  metrics: {
    cpu_usage: 10,
    memory_usage: 20,
    request_rate: 10,
    error_rate: 85.0,
    latency_p99: 5000,
  },
  last_updated: new Date().toISOString(),
};

// Sample anomalies - matching AnomalyAlert interface
export const sampleAnomalies = [
  {
    alert_id: "anomaly-001",
    resource_id: "service-003",
    resource_name: "payment-service",
    severity: "critical" as const,
    metric_name: "error_rate",
    current_value: 85.0,
    expected_value: 5.0,
    deviation_percentage: 1600,
    message: "Error rate exceeded 80% threshold",
    detected_at: new Date().toISOString(),
    potential_causes: ["Database connection failure", "High traffic load"],
  },
  {
    alert_id: "anomaly-002",
    resource_id: "service-002",
    resource_name: "user-service",
    severity: "high" as const,
    metric_name: "latency_p99",
    current_value: 800,
    expected_value: 200,
    deviation_percentage: 300,
    message: "P99 latency exceeded 500ms threshold",
    detected_at: new Date(Date.now() - 300000).toISOString(),
    potential_causes: ["Database slow queries"],
  },
  {
    alert_id: "anomaly-003",
    resource_id: "service-002",
    resource_name: "user-service",
    severity: "medium" as const,
    metric_name: "memory_usage",
    current_value: 80,
    expected_value: 50,
    deviation_percentage: 60,
    message: "Memory usage approaching limit",
    detected_at: new Date(Date.now() - 600000).toISOString(),
    potential_causes: ["Memory leak"],
  },
  {
    alert_id: "anomaly-004",
    resource_id: "service-001",
    resource_name: "api-gateway",
    severity: "low" as const,
    metric_name: "request_rate",
    current_value: 1500,
    expected_value: 1000,
    deviation_percentage: 50,
    message: "Unusual traffic pattern detected",
    detected_at: new Date(Date.now() - 900000).toISOString(),
    potential_causes: [],
  },
];

// Sample traffic patterns - matching TrafficPattern interface
export const sampleTrafficPatterns: TrafficPattern[] = [
  {
    source_id: "service-001",
    target_id: "service-002",
    request_rate: 500,
    error_rate: 5.0,
    latency_p95: 200,
    is_abnormal: true,
    anomaly_score: 0.75,
    trend: "increasing",
  },
  {
    source_id: "service-001",
    target_id: "service-003",
    request_rate: 50,
    error_rate: 85.0,
    latency_p95: 3000,
    is_abnormal: true,
    anomaly_score: 0.95,
    trend: "decreasing",
  },
  {
    source_id: "service-002",
    target_id: "db-001",
    request_rate: 200,
    error_rate: 0.1,
    latency_p95: 15,
    is_abnormal: false,
    anomaly_score: 0.1,
    trend: "stable",
  },
];

// Sample failing dependencies - matching FailingDependency interface
export const sampleFailingDependencies: FailingDependency[] = [
  {
    source_id: "service-001",
    source_name: "api-gateway",
    target_id: "service-003",
    target_name: "payment-service",
    status: "failed",
    health_score: 15,
    anomalies: ["anomaly-001"],
    error_details: {
      status: "failed",
      health_score: 15,
      anomalies: ["anomaly-001"],
      metrics: { error_rate: 85.0, latency_p99: 5000 },
      timestamp: new Date().toISOString(),
    },
  },
  {
    source_id: "service-001",
    source_name: "api-gateway",
    target_id: "service-002",
    target_name: "user-service",
    status: "degraded",
    health_score: 65,
    anomalies: ["anomaly-002", "anomaly-003"],
    error_details: {
      status: "degraded",
      health_score: 65,
      anomalies: ["anomaly-002", "anomaly-003"],
      metrics: { error_rate: 5.0, latency_p99: 800 },
      timestamp: new Date().toISOString(),
    },
  },
];

// Complete snapshot for healthy system
export const healthySnapshot: LiveDiagnosticsSnapshot = {
  timestamp: new Date().toISOString(),
  overall_health: "healthy",
  services: [healthyService],
  anomalies: [],
  traffic_patterns: [
    {
      source_id: "service-001",
      target_id: "db-001",
      request_rate: 100,
      error_rate: 0.1,
      latency_p95: 10,
      is_abnormal: false,
      anomaly_score: 0.05,
      trend: "stable",
    },
  ],
  failing_dependencies: [],
};

// Complete snapshot with issues
export const degradedSnapshot: LiveDiagnosticsSnapshot = {
  timestamp: new Date().toISOString(),
  overall_health: "degraded",
  services: [healthyService, degradedService, failedService],
  anomalies: sampleAnomalies,
  traffic_patterns: sampleTrafficPatterns,
  failing_dependencies: sampleFailingDependencies,
};

// API response mocks
export const mockSnapshotResponse = degradedSnapshot;

export const mockHealthResponse = {
  prometheus: "healthy",
  neo4j: "healthy",
  overall: "healthy",
};

export const mockAnomaliesResponse = sampleAnomalies;

export const mockTrafficPatternsResponse = sampleTrafficPatterns;

export const mockFailingDependenciesResponse = sampleFailingDependencies;

// WebSocket mock events
export const mockWebSocketEvents = {
  connected: {
    type: "connected",
    connection_id: "test-connection-123",
    timestamp: new Date().toISOString(),
  },
  snapshotUpdate: {
    type: "snapshot_update",
    data: mockSnapshotResponse,
    timestamp: new Date().toISOString(),
  },
  anomalyDetected: {
    type: "anomaly_detected",
    data: sampleAnomalies[0],
    timestamp: new Date().toISOString(),
  },
  healthChanged: {
    type: "health_changed",
    data: {
      resource_id: "service-003",
      old_status: "degraded",
      new_status: "failed",
    },
    timestamp: new Date().toISOString(),
  },
};

// Error responses
export const mockErrorResponses = {
  notFound: {
    detail: "Resource not found",
  },
  serverError: {
    detail: "Internal server error",
  },
  serviceUnavailable: {
    detail: "Service temporarily unavailable",
  },
};
