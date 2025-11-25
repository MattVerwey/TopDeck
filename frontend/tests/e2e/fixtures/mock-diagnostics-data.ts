/**
 * Mock Diagnostics Data Fixtures
 *
 * Test fixtures for Live Diagnostics E2E tests
 */

export interface ServiceHealth {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  status: "healthy" | "degraded" | "failed";
  health_score: number;
  metrics: {
    cpu_usage: number;
    memory_usage: number;
    request_rate: number;
    error_rate: number;
    latency_p99: number;
  };
}

export interface Anomaly {
  id: string;
  resource_id: string;
  resource_name: string;
  anomaly_type: string;
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  detected_at: string;
  confidence: number;
}

export interface TrafficPattern {
  source_id: string;
  source_name: string;
  target_id: string;
  target_name: string;
  request_rate: number;
  error_rate: number;
  latency_avg: number;
  is_abnormal: boolean;
  deviation_score: number;
}

export interface FailingDependency {
  source_id: string;
  source_name: string;
  target_id: string;
  target_name: string;
  status: "degraded" | "failed";
  health_score: number;
  anomalies: string[];
}

export interface DiagnosticsSnapshot {
  timestamp: string;
  overall_health: "healthy" | "degraded" | "failed";
  services: ServiceHealth[];
  anomalies: Anomaly[];
  traffic_patterns: TrafficPattern[];
  failing_dependencies: FailingDependency[];
}

// Sample healthy service
export const healthyService: ServiceHealth = {
  resource_id: "service-001",
  resource_name: "api-gateway",
  resource_type: "service",
  status: "healthy",
  health_score: 95,
  metrics: {
    cpu_usage: 35,
    memory_usage: 45,
    request_rate: 1000,
    error_rate: 0.5,
    latency_p99: 120,
  },
};

// Sample degraded service
export const degradedService: ServiceHealth = {
  resource_id: "service-002",
  resource_name: "user-service",
  resource_type: "service",
  status: "degraded",
  health_score: 65,
  metrics: {
    cpu_usage: 75,
    memory_usage: 80,
    request_rate: 500,
    error_rate: 5.0,
    latency_p99: 800,
  },
};

// Sample failed service
export const failedService: ServiceHealth = {
  resource_id: "service-003",
  resource_name: "payment-service",
  resource_type: "service",
  status: "failed",
  health_score: 15,
  metrics: {
    cpu_usage: 10,
    memory_usage: 20,
    request_rate: 10,
    error_rate: 85.0,
    latency_p99: 5000,
  },
};

// Sample anomalies
export const sampleAnomalies: Anomaly[] = [
  {
    id: "anomaly-001",
    resource_id: "service-003",
    resource_name: "payment-service",
    anomaly_type: "high_error_rate",
    severity: "critical",
    message: "Error rate exceeded 80% threshold",
    detected_at: new Date().toISOString(),
    confidence: 0.95,
  },
  {
    id: "anomaly-002",
    resource_id: "service-002",
    resource_name: "user-service",
    anomaly_type: "high_latency",
    severity: "high",
    message: "P99 latency exceeded 500ms threshold",
    detected_at: new Date(Date.now() - 300000).toISOString(),
    confidence: 0.88,
  },
  {
    id: "anomaly-003",
    resource_id: "service-002",
    resource_name: "user-service",
    anomaly_type: "memory_pressure",
    severity: "medium",
    message: "Memory usage approaching limit",
    detected_at: new Date(Date.now() - 600000).toISOString(),
    confidence: 0.75,
  },
  {
    id: "anomaly-004",
    resource_id: "service-001",
    resource_name: "api-gateway",
    anomaly_type: "traffic_spike",
    severity: "low",
    message: "Unusual traffic pattern detected",
    detected_at: new Date(Date.now() - 900000).toISOString(),
    confidence: 0.65,
  },
];

// Sample traffic patterns
export const sampleTrafficPatterns: TrafficPattern[] = [
  {
    source_id: "service-001",
    source_name: "api-gateway",
    target_id: "service-002",
    target_name: "user-service",
    request_rate: 500,
    error_rate: 5.0,
    latency_avg: 200,
    is_abnormal: true,
    deviation_score: 2.5,
  },
  {
    source_id: "service-001",
    source_name: "api-gateway",
    target_id: "service-003",
    target_name: "payment-service",
    request_rate: 50,
    error_rate: 85.0,
    latency_avg: 3000,
    is_abnormal: true,
    deviation_score: 8.0,
  },
  {
    source_id: "service-002",
    source_name: "user-service",
    target_id: "db-001",
    target_name: "user-database",
    request_rate: 200,
    error_rate: 0.1,
    latency_avg: 15,
    is_abnormal: false,
    deviation_score: 0.2,
  },
];

// Sample failing dependencies
export const sampleFailingDependencies: FailingDependency[] = [
  {
    source_id: "service-001",
    source_name: "api-gateway",
    target_id: "service-003",
    target_name: "payment-service",
    status: "failed",
    health_score: 15,
    anomalies: ["anomaly-001"],
  },
  {
    source_id: "service-001",
    source_name: "api-gateway",
    target_id: "service-002",
    target_name: "user-service",
    status: "degraded",
    health_score: 65,
    anomalies: ["anomaly-002", "anomaly-003"],
  },
];

// Complete snapshot for healthy system
export const healthySnapshot: DiagnosticsSnapshot = {
  timestamp: new Date().toISOString(),
  overall_health: "healthy",
  services: [healthyService],
  anomalies: [],
  traffic_patterns: [
    {
      source_id: "service-001",
      source_name: "api-gateway",
      target_id: "db-001",
      target_name: "database",
      request_rate: 100,
      error_rate: 0.1,
      latency_avg: 10,
      is_abnormal: false,
      deviation_score: 0.1,
    },
  ],
  failing_dependencies: [],
};

// Complete snapshot with issues
export const degradedSnapshot: DiagnosticsSnapshot = {
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
