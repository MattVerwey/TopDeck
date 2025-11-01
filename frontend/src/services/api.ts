/**
 * API client for TopDeck backend
 */

import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import type {
  TopologyGraph,
  ResourceDependencies,
  DataFlow,
  RiskAssessment,
  ChangeImpact,
  Integration,
  TransactionFlow,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Error response structure from the API
 */
interface ErrorResponse {
  error?: {
    message?: string;
    code?: string;
  };
}

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  statusCode?: number;
  requestId?: string;
  code?: string;

  constructor(
    message: string,
    statusCode?: number,
    requestId?: string,
    code?: string,
  ) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.requestId = requestId;
    this.code = code;
  }
}

/**
 * Retry configuration
 */
interface RetryConfig {
  maxRetries: number;
  retryDelay: number;
  retryableStatuses: number[];
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  retryDelay: 1000, // 1 second
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

/**
 * Sleep utility for retry delays
 */
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

class ApiClient {
  private client: AxiosInstance;
  private retryConfig: RetryConfig;

  constructor(retryConfig: Partial<RetryConfig> = {}) {
    this.retryConfig = { ...DEFAULT_RETRY_CONFIG, ...retryConfig };
    
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        const requestId = error.response?.headers['x-request-id'];
        const errorData = error.response?.data;
        
        throw new ApiError(
          errorData?.error?.message || error.message || 'An error occurred',
          error.response?.status,
          requestId,
          errorData?.error?.code,
        );
      }
    );
  }

  /**
   * Make a request with automatic retry logic
   */
  private async requestWithRetry<T>(
    requestFn: () => Promise<T>,
    retries = 0,
  ): Promise<T> {
    try {
      return await requestFn();
    } catch (error) {
      if (error instanceof ApiError && retries < this.retryConfig.maxRetries) {
        // Check if status is retryable
        if (
          error.statusCode &&
          this.retryConfig.retryableStatuses.includes(error.statusCode)
        ) {
          // Calculate delay with exponential backoff
          const delay = this.retryConfig.retryDelay * Math.pow(2, retries);
          
          console.warn(
            `Request failed with ${error.statusCode}. Retrying in ${delay}ms... (attempt ${retries + 1}/${this.retryConfig.maxRetries})`
          );
          
          await sleep(delay);
          return this.requestWithRetry(requestFn, retries + 1);
        }
      }
      
      throw error;
    }
  }

  // Topology API
  async getTopology(filters?: {
    cloud_provider?: string;
    resource_type?: string;
    region?: string;
  }): Promise<TopologyGraph> {
    return this.requestWithRetry(async () => {
      const { data } = await this.client.get('/api/v1/topology', { params: filters });
      return data;
    });
  }

  async getResourceDependencies(resourceId: string): Promise<ResourceDependencies> {
    return this.requestWithRetry(async () => {
      const { data } = await this.client.get(`/api/v1/topology/resources/${resourceId}/dependencies`);
      return data;
    });
  }

  async getDataFlows(filters?: {
    flow_type?: string;
    start_resource_type?: string;
  }): Promise<DataFlow[]> {
    return this.requestWithRetry(async () => {
      const { data } = await this.client.get('/api/v1/topology/flows', { params: filters });
      return data;
    });
  }

  // Risk Analysis API
  async getRiskAssessment(resourceId: string): Promise<RiskAssessment> {
    return this.requestWithRetry(async () => {
      const { data } = await this.client.get(`/api/v1/risk/resources/${resourceId}`);
      return data;
    });
  }

  async getAllRisks(): Promise<RiskAssessment[]> {
    try {
      return await this.requestWithRetry(async () => {
        const { data } = await this.client.get('/api/v1/risk/all');
        return data;
      });
    } catch {
      // Fallback to empty array if endpoint doesn't exist
      return [];
    }
  }

  async getChangeImpact(serviceId: string, changeType: string): Promise<ChangeImpact> {
    return this.requestWithRetry(async () => {
      const { data } = await this.client.post(`/api/v1/risk/impact`, {
        service_id: serviceId,
        change_type: changeType,
      });
      return data;
    });
  }

  async getBlastRadius(resourceId: string): Promise<{
    resource_id: string;
    resource_name: string;
    directly_affected: { id: string; name: string; type?: string }[];
    indirectly_affected: { id: string; name: string; type?: string }[];
    total_affected: number;
    user_impact: string;
    estimated_downtime_seconds: number;
    critical_path: string[];
    affected_services: Record<string, unknown>;
  }> {
    return this.requestWithRetry(async () => {
      const { data } = await this.client.get(`/api/v1/risk/blast-radius/${resourceId}`);
      return data;
    });
  }

  async getComprehensiveRiskAnalysis(
    resourceId: string,
    projectPath?: string,
    currentLoad: number = 0.7
  ): Promise<{
    resource_id: string;
    combined_risk_score: number;
    standard_assessment: RiskAssessment;
    degraded_performance_scenario: {
      resource_id: string;
      resource_name: string;
      failure_type: string;
      outcomes: Array<{
        outcome_type: string;
        probability: number;
        duration_seconds: number;
        affected_percentage: number;
        user_impact_description: string;
        technical_details: string;
      }>;
      overall_impact: string;
      mitigation_strategies: string[];
      monitoring_recommendations: string[];
    };
    intermittent_failure_scenario: {
      resource_id: string;
      resource_name: string;
      failure_type: string;
      outcomes: Array<{
        outcome_type: string;
        probability: number;
        duration_seconds: number;
        affected_percentage: number;
        user_impact_description: string;
        technical_details: string;
      }>;
      overall_impact: string;
      mitigation_strategies: string[];
      monitoring_recommendations: string[];
    };
    dependency_vulnerabilities: Array<{
      package_name: string;
      current_version: string;
      vulnerability_id: string;
      severity: string;
      description: string;
      fixed_version?: string;
      exploit_available: boolean;
      affected_resources: string[];
    }>;
    vulnerability_risk_score: number;
    all_recommendations: string[];
  }> {
    return this.requestWithRetry(async () => {
      const params: Record<string, string | number | boolean> = { current_load: currentLoad };
      if (projectPath) {
        params.project_path = projectPath;
      }
      const { data } = await this.client.get(
        `/api/v1/risk/resources/${resourceId}/comprehensive`,
        { params }
      );
      return data;
    });
  }

  // Monitoring API
  async getResourceMetrics(resourceId: string, duration_hours: number = 24) {
    const { data } = await this.client.get(`/api/v1/monitoring/resources/${resourceId}/metrics`, {
      params: { duration_hours },
    });
    return data;
  }

  async getFlowBottlenecks(flowPath: string[]) {
    const { data } = await this.client.get(`/api/v1/monitoring/flows/bottlenecks`, {
      params: { flow_path: flowPath },
    });
    return data;
  }

  async getResourceCorrelationIds(
    resourceId: string,
    durationHours: number = 1
  ): Promise<string[]> {
    const { data } = await this.client.get(
      `/api/v1/monitoring/resources/${resourceId}/correlation-ids`,
      {
        params: { duration_hours: durationHours },
      }
    );
    return data;
  }

  async traceTransactionFlow(
    correlationId: string,
    durationHours: number = 1,
    source: string = 'auto',
    enrich: boolean = true
  ): Promise<TransactionFlow> {
    const { data } = await this.client.get(
      `/api/v1/monitoring/flows/trace/${correlationId}`,
      {
        params: {
          duration_hours: durationHours,
          source,
          enrich,
        },
      }
    );
    return data;
  }

  // Integrations
  async getIntegrations(): Promise<Integration[]> {
    const { data } = await this.client.get('/api/v1/integrations');
    return data;
  }

  async updateIntegration(id: string, config: Record<string, unknown>): Promise<Integration> {
    const { data } = await this.client.put(`/api/v1/integrations/${id}`, config);
    return data;
  }

  // Change Management API
  async createChangeRequest(changeData: {
    title: string;
    description: string;
    change_type: string;
    affected_resources?: string[];
    scheduled_start?: string;
    scheduled_end?: string;
    requester?: string;
  }): Promise<{
    id: string;
    title: string;
    description: string;
    change_type: string;
    status: string;
    risk_level: string;
    affected_resources: string[];
    affected_services_count: number;
    estimated_downtime_seconds: number;
    created_at: string;
    updated_at: string;
  }> {
    return this.requestWithRetry(async () => {
      const { data } = await this.client.post('/api/v1/changes', changeData);
      return data;
    });
  }

  async assessChangeImpact(
    changeId: string,
    resourceId?: string
  ): Promise<{
    change_id: string;
    directly_affected_resources: Array<{
      resource_id: string;
      name: string;
      type: string;
      risk_score: number;
      blast_radius: number;
    }>;
    indirectly_affected_resources: Array<{
      resource_id: string;
      name: string;
      type: string;
    }>;
    total_affected_count: number;
    overall_risk_score: number;
    performance_degradation_pct: number;
    estimated_downtime_seconds: number;
    user_impact_level: string;
    critical_path_affected: boolean;
    recommended_window: string;
    rollback_plan_required: boolean;
    approval_required: boolean;
    breakdown: Record<string, unknown>;
    recommendations: string[];
    assessed_at: string;
  }> {
    return this.requestWithRetry(async () => {
      const params = resourceId ? { resource_id: resourceId } : {};
      const { data } = await this.client.post(`/api/v1/changes/${changeId}/assess`, null, {
        params,
      });
      return data;
    });
  }

  async getChangeCalendar(
    startDate?: string,
    endDate?: string
  ): Promise<Array<{
    id: string;
    title: string;
    change_type: string;
    status: string;
    risk_level: string;
    scheduled_start: string;
    scheduled_end?: string;
    requester?: string;
  }>> {
    return this.requestWithRetry(async () => {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      const { data } = await this.client.get('/api/v1/changes/calendar', { params });
      return data;
    });
  }

  async getChangeTypes(): Promise<string[]> {
    return this.requestWithRetry(async () => {
      const { data } = await this.client.get('/api/v1/changes/types');
      return data;
    });
  }

  // Prediction API
  async getFailurePrediction(
    resourceId: string,
    resourceName?: string,
    resourceType?: string
  ): Promise<{
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
  }> {
    return this.requestWithRetry(async () => {
      const params: Record<string, string> = {};
      if (resourceName) params.resource_name = resourceName;
      if (resourceType) params.resource_type = resourceType;
      const { data } = await this.client.get(
        `/api/v1/prediction/resources/${resourceId}/failure-risk`,
        { params }
      );
      return data;
    });
  }

  async getPerformancePrediction(
    resourceId: string,
    resourceName?: string,
    metricName: string = 'latency_p95',
    horizonHours: number = 24
  ): Promise<{
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
  }> {
    return this.requestWithRetry(async () => {
      const params: Record<string, string | number> = {
        metric_name: metricName,
        horizon_hours: horizonHours,
      };
      if (resourceName) params.resource_name = resourceName;
      const { data } = await this.client.get(
        `/api/v1/prediction/resources/${resourceId}/performance`,
        { params }
      );
      return data;
    });
  }

  async getAnomalyDetection(
    resourceId: string,
    resourceName?: string,
    windowHours: number = 24
  ): Promise<{
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
  }> {
    return this.requestWithRetry(async () => {
      const params: Record<string, string | number> = {
        window_hours: windowHours,
      };
      if (resourceName) params.resource_name = resourceName;
      const { data } = await this.client.get(
        `/api/v1/prediction/resources/${resourceId}/anomalies`,
        { params }
      );
      return data;
    });
  }

  async getPredictionHealth(): Promise<{
    status: string;
    models: Record<string, unknown>;
    features: Record<string, boolean>;
  }> {
    return this.requestWithRetry(async () => {
      const { data } = await this.client.get('/api/v1/prediction/health');
      return data;
    });
  }

  // Health check
  async checkHealth() {
    const { data } = await this.client.get('/health');
    return data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;
