/**
 * TypeScript types for Live Diagnostics
 */

export interface ServiceHealthStatus {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  status: 'healthy' | 'degraded' | 'failed' | 'unknown';
  health_score: number; // 0-100
  anomalies: string[];
  metrics: Record<string, number>;
  last_updated: string; // ISO datetime
}

export interface AnomalyAlert {
  alert_id: string;
  resource_id: string;
  resource_name: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  metric_name: string;
  current_value: number;
  expected_value: number;
  deviation_percentage: number;
  detected_at: string; // ISO datetime
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
  anomaly_score: number; // 0-1
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface FailingDependency {
  source_id: string;
  source_name: string;
  target_id: string;
  target_name: string;
  status: 'degraded' | 'failed';
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
  timestamp: string; // ISO datetime
  overall_health: 'healthy' | 'degraded' | 'critical';
  services: ServiceHealthStatus[];
  anomalies: AnomalyAlert[];
  traffic_patterns: TrafficPattern[];
  failing_dependencies: FailingDependency[];
}
