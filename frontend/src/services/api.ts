/**
 * API client for TopDeck backend
 */

import axios from 'axios';
import type { AxiosInstance } from 'axios';
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

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Topology API
  async getTopology(filters?: {
    cloud_provider?: string;
    resource_type?: string;
    region?: string;
  }): Promise<TopologyGraph> {
    const { data } = await this.client.get('/api/v1/topology', { params: filters });
    return data;
  }

  async getResourceDependencies(resourceId: string): Promise<ResourceDependencies> {
    const { data } = await this.client.get(`/api/v1/topology/resources/${resourceId}/dependencies`);
    return data;
  }

  async getDataFlows(filters?: {
    flow_type?: string;
    start_resource_type?: string;
  }): Promise<DataFlow[]> {
    const { data } = await this.client.get('/api/v1/topology/flows', { params: filters });
    return data;
  }

  // Risk Analysis API
  async getRiskAssessment(resourceId: string): Promise<RiskAssessment> {
    const { data } = await this.client.get(`/api/v1/risk/resources/${resourceId}`);
    return data;
  }

  async getAllRisks(): Promise<RiskAssessment[]> {
    try {
      const { data } = await this.client.get('/api/v1/risk/all');
      return data;
    } catch {
      // Fallback to empty array if endpoint doesn't exist
      return [];
    }
  }

  async getChangeImpact(serviceId: string, changeType: string): Promise<ChangeImpact> {
    const { data } = await this.client.post(`/api/v1/risk/impact`, {
      service_id: serviceId,
      change_type: changeType,
    });
    return data;
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
    const { data } = await this.client.get(`/api/v1/risk/blast-radius/${resourceId}`);
    return data;
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

  // Health check
  async checkHealth() {
    const { data } = await this.client.get('/health');
    return data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;
