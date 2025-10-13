/**
 * Core type definitions for TopDeck UI
 */

export interface Resource {
  id: string;
  resource_type: string;
  name: string;
  cloud_provider: 'azure' | 'aws' | 'gcp';
  region?: string;
  properties: Record<string, any>;
  metadata: Record<string, any>;
}

export interface Relationship {
  source_id: string;
  target_id: string;
  relationship_type: string;
  flow_type?: string;
  properties: Record<string, any>;
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
  metadata: Record<string, any>;
}

export interface DataFlow {
  id: string;
  name: string;
  path: string[];
  flow_type: string;
  nodes: Resource[];
  edges: Relationship[];
  metadata: Record<string, any>;
}

export interface RiskAssessment {
  resource_id: string;
  risk_score: number;
  criticality: 'low' | 'medium' | 'high' | 'critical';
  dependencies_count: number;
  dependents_count: number;
  blast_radius: number;
  single_point_of_failure: boolean;
  recommendations: string[];
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
  metrics: Record<string, any>;
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
  metadata: Record<string, any>;
}

export type ViewMode = 'service' | 'cluster' | 'namespace' | 'network';
