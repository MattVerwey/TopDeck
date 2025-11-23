/**
 * Live Topology Graph Component
 * 
 * Displays network topology with visual highlighting based on service health.
 * Uses Cytoscape.js for graph visualization with enhanced visuals.
 */

import { useEffect, useRef, useState } from 'react';
import { Box, Typography, Alert, Paper, Stack, Chip } from '@mui/material';
import { Circle as CircleIcon } from '@mui/icons-material';
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

// Color scheme for health statuses
const HEALTH_COLORS = {
  healthy: '#4caf50',      // Vibrant green for healthy/working
  degraded: '#ff9800',     // Orange for degraded
  failed: '#f44336',       // Red for errors/failed
  unknown: '#757575',      // Gray for unknown
};

const EDGE_COLORS = {
  healthy: '#66bb6a',      // Light green for healthy connections
  degraded: '#ffa726',     // Light orange for degraded connections
  failed: '#ef5350',       // Light red for failed connections
};

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
      // Cleanup existing instance if any
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }

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

      // Initialize Cytoscape with enhanced styling
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
                return HEALTH_COLORS[status as keyof typeof HEALTH_COLORS] || HEALTH_COLORS.unknown;
              },
              label: 'data(label)',
              'text-valign': 'center',
              'text-halign': 'center',
              color: '#ffffff',
              'text-outline-color': '#000000',
              'text-outline-width': 1,
              'font-size': '14px',
              'font-weight': 'bold',
              width: (ele: any) => {
                const anomalyCount = ele.data('anomaly_count');
                return anomalyCount > 0 ? 60 : 50;
              },
              height: (ele: any) => {
                const anomalyCount = ele.data('anomaly_count');
                return anomalyCount > 0 ? 60 : 50;
              },
              'border-width': (ele: any) => {
                const anomalyCount = ele.data('anomaly_count');
                return anomalyCount > 0 ? 4 : 2;
              },
              'border-color': (ele: any) => {
                const anomalyCount = ele.data('anomaly_count');
                return anomalyCount > 0 ? '#ff1744' : 'rgba(255, 255, 255, 0.5)';
              },
              'border-style': (ele: any) => {
                const anomalyCount = ele.data('anomaly_count');
                return anomalyCount > 0 ? 'dashed' : 'solid';
              },
              // Add shadow for depth
              'shadow-blur': 10,
              'shadow-color': '#000000',
              'shadow-opacity': 0.3,
              'shadow-offset-x': 2,
              'shadow-offset-y': 2,
            },
          },
          {
            selector: 'node:selected',
            style: {
              'border-width': 5,
              'border-color': '#2196f3',
              'border-opacity': 1,
            },
          },
          {
            selector: 'edge',
            style: {
              width: (ele: any) => {
                const status = ele.data('status');
                return status === 'failed' ? 4 : 3;
              },
              'line-color': (ele: any) => {
                const status = ele.data('status');
                if (status === 'failed') return EDGE_COLORS.failed;
                if (status === 'degraded') return EDGE_COLORS.degraded;
                return EDGE_COLORS.healthy;
              },
              'target-arrow-color': (ele: any) => {
                const status = ele.data('status');
                if (status === 'failed') return EDGE_COLORS.failed;
                if (status === 'degraded') return EDGE_COLORS.degraded;
                return EDGE_COLORS.healthy;
              },
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              opacity: (ele: any) => {
                const status = ele.data('status');
                return status === 'failed' ? 1.0 : 0.8;
              },
              'line-style': (ele: any) => {
                const status = ele.data('status');
                return status === 'failed' ? 'solid' : 'solid';
              },
            },
          },
        ],
        layout: {
          name: 'cose',
          animate: true,
          animationDuration: 500,
          fit: true,
          padding: 40,
          nodeRepulsion: 8000,
          idealEdgeLength: 100,
          edgeElasticity: 100,
        },
        minZoom: 0.3,
        maxZoom: 3,
      });

      // Add click handler
      cy.on('tap', 'node', (event) => {
        const node = event.target;
        const resourceId = node.data('id');
        onResourceClick(resourceId);
      });

      // Add hover effects
      cy.on('mouseover', 'node', (event) => {
        const node = event.target;
        node.style({
          'border-width': 5,
          'border-color': '#2196f3',
        });
      });

      cy.on('mouseout', 'node', (event) => {
        const node = event.target;
        const anomalyCount = node.data('anomaly_count');
        node.style({
          'border-width': anomalyCount > 0 ? 4 : 2,
          'border-color': anomalyCount > 0 ? '#ff1744' : 'rgba(255, 255, 255, 0.5)',
        });
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

  // Calculate status counts for legend
  const statusCounts = {
    healthy: services.filter(s => s.status === 'healthy').length,
    degraded: services.filter(s => s.status === 'degraded').length,
    failed: services.filter(s => s.status === 'failed').length,
    unknown: services.filter(s => s.status === 'unknown').length,
  };

  return (
    <Box sx={{ position: 'relative', width: '100%' }}>
      {/* Legend */}
      <Paper
        elevation={3}
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          zIndex: 1000,
          p: 2,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(10px)',
        }}
      >
        <Typography variant="subtitle2" sx={{ mb: 1, color: 'white', fontWeight: 'bold' }}>
          Service Health Status
        </Typography>
        <Stack spacing={1}>
          <Chip
            icon={<CircleIcon sx={{ color: HEALTH_COLORS.healthy }} />}
            label={`Healthy (${statusCounts.healthy})`}
            size="small"
            sx={{
              backgroundColor: 'rgba(76, 175, 80, 0.2)',
              color: 'white',
              justifyContent: 'flex-start',
            }}
          />
          <Chip
            icon={<CircleIcon sx={{ color: HEALTH_COLORS.degraded }} />}
            label={`Degraded (${statusCounts.degraded})`}
            size="small"
            sx={{
              backgroundColor: 'rgba(255, 152, 0, 0.2)',
              color: 'white',
              justifyContent: 'flex-start',
            }}
          />
          <Chip
            icon={<CircleIcon sx={{ color: HEALTH_COLORS.failed }} />}
            label={`Failed (${statusCounts.failed})`}
            size="small"
            sx={{
              backgroundColor: 'rgba(244, 67, 54, 0.2)',
              color: 'white',
              justifyContent: 'flex-start',
            }}
          />
        </Stack>
        <Typography variant="caption" sx={{ mt: 1, display: 'block', color: 'rgba(255, 255, 255, 0.7)' }}>
          Dashed border = Has anomalies
        </Typography>
      </Paper>

      {/* Graph Container */}
      <Box
        ref={containerRef}
        sx={{
          width: '100%',
          height: '600px',
          backgroundColor: '#1a1a1a',
          border: 2,
          borderColor: 'divider',
          borderRadius: 2,
          boxShadow: 3,
        }}
      />
    </Box>
  );
}
