/**
 * Core type definitions for TopDeck UI
 */

export interface Resource {
  id: string;
  resource_type: string;
  name: string;
  cloud_provider: 'azure' | 'aws' | 'gcp';
  region?: string;
  properties: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

export interface Relationship {
  source_id: string;
  target_id: string;
  relationship_type: string;
  flow_type?: string;
  properties: Record<string, unknown>;
}

export interface TopologyGraph {
  nodes: Resource[];
  edges: Relationship[];
  metadata: {
    total_nodes: number;
    total_edges: number;
    filters?: {
      cloud_provider?: string;
      resource_type?: string;
      region?: string;
    };
  };
}

export interface ResourceDependencies {
  resource_id: string;
  resource_name: string;
  upstream: Resource[];
  downstream: Resource[];
  metadata: Record<string, unknown>;
}

export interface DataFlow {
  id: string;
  name: string;
  path: string[];
  flow_type: string;
  nodes: Resource[];
  edges: Relationship[];
  metadata: Record<string, unknown>;
}

export interface RiskAssessment {
  resource_id: string;
  resource_name?: string;
  resource_type?: string;
  risk_score: number;
  risk_level?: string;
  criticality: 'low' | 'medium' | 'high' | 'critical';
  criticality_score?: number;
  dependencies_count: number;
  dependents_count: number;
  blast_radius: number;
  single_point_of_failure: boolean;
  deployment_failure_rate?: number;
  time_since_last_change?: number;
  recommendations: string[];
  factors?: Record<string, unknown>;
  assessed_at?: string;
}

export interface ChangeImpact {
  service_id: string;
  affected_services: string[];
  performance_degradation: number;
  estimated_downtime: number;
  user_impact: 'low' | 'medium' | 'high';
  recommendations: string[];
}

export interface FilterOptions {
  cloud_provider?: string;
  resource_type?: string;
  region?: string;
  risk_level?: string;
  namespace?: string;
  cluster?: string;
}

export interface Integration {
  id: string;
  name: string;
  type: 'azure-devops' | 'github' | 'servicenow' | 'jira' | 'prometheus' | 'loki';
  enabled: boolean;
  configured: boolean;
  last_sync?: string;
}

export interface FlowNode {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  timestamp: string;
  duration_ms?: number;
  status: 'success' | 'error' | 'warning';
  log_count: number;
  metrics: Record<string, unknown>;
}

export interface FlowEdge {
  source_id: string;
  target_id: string;
  protocol?: string;
  duration_ms?: number;
  status_code?: number;
}

export interface TransactionFlow {
  transaction_id: string;
  start_time: string;
  end_time: string;
  total_duration_ms: number;
  nodes: FlowNode[];
  edges: FlowEdge[];
  status: 'success' | 'error' | 'partial';
  error_count: number;
  warning_count: number;
  source: string;
  metadata: Record<string, unknown>;
}

export type ViewMode = 'service' | 'cluster' | 'namespace' | 'network';

// Prediction types
export interface FailurePrediction {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  failure_probability: number;
  time_to_failure_hours: number | null;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  confidence: 'low' | 'medium' | 'high';
  contributing_factors: Array<{
    factor: string;
    importance: number;
    current_value: number | string | null;
    threshold: number | string | null;
    description: string;
  }>;
  recommendations: string[];
  predicted_at: string;
  model_version: string;
}

export interface PerformancePrediction {
  resource_id: string;
  resource_name: string;
  metric_name: string;
  current_value: number | null;
  baseline_value: number | null;
  predictions: Array<{
    timestamp: string;
    predicted_value: number;
    confidence_lower: number;
    confidence_upper: number;
  }>;
  degradation_risk: 'low' | 'medium' | 'high' | 'critical';
  confidence: 'low' | 'medium' | 'high';
  trend: string;
  seasonality_detected: boolean;
  anomalies_detected: boolean;
  recommendations: string[];
  predicted_at: string;
  prediction_horizon_hours: number;
  model_version: string;
}

export interface AnomalyDetection {
  resource_id: string;
  resource_name: string;
  anomalies: Array<{
    timestamp: string;
    metric_name: string;
    actual_value: number;
    expected_value: number;
    anomaly_score: number;
    deviation_percentage: number;
  }>;
  overall_anomaly_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  affected_metrics: string[];
  potential_causes: string[];
  similar_historical_incidents: string[];
  correlated_resources: string[];
  recommendations: string[];
  detected_at: string;
  detection_window_hours: number;
  model_version: string;
}
