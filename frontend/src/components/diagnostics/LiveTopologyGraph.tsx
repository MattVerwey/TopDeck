/**
 * Live Topology Graph Component
 * 
 * Displays network topology with visual highlighting based on service health.
 * Uses Cytoscape.js for graph visualization.
 */

import { useEffect, useRef, useState } from 'react';
import { Box, Typography, Alert } from '@mui/material';
import cytoscape from 'cytoscape';
import type {
  ServiceHealthStatus,
  AnomalyAlert,
  FailingDependency,
} from '../../types/diagnostics';

interface LiveTopologyGraphProps {
  services: ServiceHealthStatus[];
  anomalies: AnomalyAlert[];
  failingDependencies: FailingDependency[];
  onResourceClick: (resourceId: string) => void;
}

export default function LiveTopologyGraph({
  services,
  anomalies,
  failingDependencies,
  onResourceClick,
}: LiveTopologyGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current || services.length === 0) return;

    try {
      // Create node-to-status map
      const statusMap = new Map<string, ServiceHealthStatus>();
      services.forEach((service) => {
        statusMap.set(service.resource_id, service);
      });

      // Create anomaly map for quick lookup
      const anomalyMap = new Map<string, number>();
      anomalies.forEach((anomaly) => {
        const count = anomalyMap.get(anomaly.resource_id) || 0;
        anomalyMap.set(anomaly.resource_id, count + 1);
      });

      // Build nodes
      const nodes = services.map((service) => ({
        data: {
          id: service.resource_id,
          label: service.resource_name,
          status: service.status,
          health_score: service.health_score,
          anomaly_count: anomalyMap.get(service.resource_id) || 0,
        },
      }));

      // Build edges from failing dependencies
      const edges = failingDependencies.map((dep, index) => ({
        data: {
          id: `edge-${index}`,
          source: dep.source_id,
          target: dep.target_id,
          status: dep.status,
        },
      }));

      // Initialize Cytoscape
      const cy = cytoscape({
        container: containerRef.current,
        elements: {
          nodes,
          edges,
        },
        style: [
          {
            selector: 'node',
            style: {
              'background-color': (ele: any) => {
                const status = ele.data('status');
                switch (status) {
                  case 'healthy':
                    return '#4caf50'; // green
                  case 'degraded':
                    return '#ff9800'; // orange
                  case 'failed':
                    return '#f44336'; // red
                  default:
                    return '#9e9e9e'; // gray
                }
              },
              label: 'data(label)',
              'text-valign': 'center',
              'text-halign': 'center',
              color: '#fff',
              'font-size': '12px',
              width: (ele: any) => {
                const anomalyCount = ele.data('anomaly_count');
                return anomalyCount > 0 ? 50 : 40;
              },
              height: (ele: any) => {
                const anomalyCount = ele.data('anomaly_count');
                return anomalyCount > 0 ? 50 : 40;
              },
              'border-width': (ele: any) => {
                const anomalyCount = ele.data('anomaly_count');
                return anomalyCount > 0 ? 3 : 2;
              },
              'border-color': (ele: any) => {
                const anomalyCount = ele.data('anomaly_count');
                return anomalyCount > 0 ? '#ff5722' : '#fff';
              },
            },
          },
          {
            selector: 'edge',
            style: {
              width: 2,
              'line-color': (ele: any) => {
                const status = ele.data('status');
                return status === 'failed' ? '#f44336' : '#ff9800';
              },
              'target-arrow-color': (ele: any) => {
                const status = ele.data('status');
                return status === 'failed' ? '#f44336' : '#ff9800';
              },
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
            },
          },
        ],
        layout: {
          name: 'cose',
          animate: true,
          animationDuration: 500,
          fit: true,
          padding: 30,
        },
        minZoom: 0.5,
        maxZoom: 3,
      });

      // Add click handler
      cy.on('tap', 'node', (event) => {
        const node = event.target;
        const resourceId = node.data('id');
        onResourceClick(resourceId);
      });

      cyRef.current = cy;

      return () => {
        cy.destroy();
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to render topology graph');
    }
  }, [services, anomalies, failingDependencies, onResourceClick]);

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (services.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Typography variant="body1" color="textSecondary">
          No services to display
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      ref={containerRef}
      sx={{
        width: '100%',
        height: '600px',
        backgroundColor: 'background.paper',
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
      }}
    />
  );
}
