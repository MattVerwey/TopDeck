/**
 * Interactive topology graph visualization using Cytoscape.js
 */

import { useEffect, useRef, useState } from 'react';
import { Box, Paper, Typography, Chip, Button, Stack } from '@mui/material';
import { Timeline } from '@mui/icons-material';
import cytoscape from 'cytoscape';
import type { TopologyGraph as TopologyGraphType, ViewMode } from '../../types';
import { useStore } from '../../store/useStore';
import TransactionFlowDialog from './TransactionFlowDialog';

interface TopologyGraphProps {
  data: TopologyGraphType;
  viewMode: ViewMode;
}

const colorMap: Record<string, string> = {
  azure: '#0078d4',
  aws: '#ff9900',
  gcp: '#4285f4',
  pod: '#4caf50',
  service: '#2196f3',
  database: '#9c27b0',
  storage: '#ff9800',
  load_balancer: '#f44336',
  gateway: '#00bcd4',
};

export default function TopologyGraph({ data, viewMode }: TopologyGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const { setSelectedResource } = useStore();
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [flowDialogOpen, setFlowDialogOpen] = useState(false);

  useEffect(() => {
    if (!containerRef.current || !data) return;

    // Convert data to Cytoscape format
    const elements = [
      ...data.nodes.map((node) => ({
        data: {
          ...node,
          id: node.id,
          label: node.name,
          type: node.resource_type,
          provider: node.cloud_provider,
        },
      })),
      ...data.edges.map((edge, idx) => ({
        data: {
          ...edge,
          id: `edge-${idx}`,
          source: edge.source_id,
          target: edge.target_id,
          label: edge.relationship_type,
        },
      })),
    ];

    // Initialize Cytoscape
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            shape: 'rectangle',
            'background-color': (ele: any) =>
              colorMap[ele.data('provider')] || colorMap[ele.data('type')] || '#2196f3',
            label: 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap',
            'text-max-width': '36px',
            color: '#fff',
            'font-size': '10px',
            width: 50,
            height: 50,
            'border-width': 2,
            'border-color': '#fff',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#f50057',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#666',
            'target-arrow-color': '#666',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: 'data(label)',
            'font-size': '10px',
            color: '#999',
            'text-rotation': 'autorotate',
          },
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#f50057',
            'target-arrow-color': '#f50057',
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: true,
        animationDuration: 500,
        nodeRepulsion: 8000,
        idealEdgeLength: 100,
        edgeElasticity: 100,
        nestingFactor: 5,
      },
      minZoom: 0.1,
      maxZoom: 3,
    });

    // Add event handlers
    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeData = node.data();
      setSelectedNode(nodeData);
      setSelectedResource(nodeData);
    });

    // Fit to view
    cyRef.current.fit(undefined, 50);

    return () => {
      cyRef.current?.destroy();
    };
  }, [data, viewMode]);

  return (
    <Box sx={{ position: 'relative', height: '100%', width: '100%' }}>
      {/* Graph Container */}
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          backgroundColor: '#0a1929',
        }}
      />

      {/* Stats Overlay */}
      <Paper
        sx={{
          position: 'absolute',
          top: 16,
          left: 16,
          p: 2,
          opacity: 0.95,
        }}
      >
        <Typography variant="body2" gutterBottom>
          <strong>Nodes:</strong> {data.nodes.length}
        </Typography>
        <Typography variant="body2" gutterBottom>
          <strong>Edges:</strong> {data.edges.length}
        </Typography>
        <Typography variant="body2">
          <strong>View:</strong> {viewMode}
        </Typography>
      </Paper>

      {/* Legend */}
      <Paper
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          p: 2,
          opacity: 0.95,
        }}
      >
        <Typography variant="body2" gutterBottom fontWeight={600}>
          Cloud Providers
        </Typography>
        <Box display="flex" flexDirection="column" gap={0.5}>
          {Object.entries(colorMap)
            .filter(([key]) => ['azure', 'aws', 'gcp'].includes(key))
            .map(([key, color]) => (
              <Chip
                key={key}
                label={key.toUpperCase()}
                size="small"
                sx={{
                  backgroundColor: color,
                  color: '#fff',
                  fontWeight: 500,
                }}
              />
            ))}
        </Box>
      </Paper>

      {/* Selected Node Info */}
      {selectedNode && (
        <Paper
          sx={{
            position: 'absolute',
            bottom: 16,
            left: 16,
            right: 16,
            p: 2,
            opacity: 0.95,
          }}
        >
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedNode.name}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {selectedNode.resource_type} • {selectedNode.cloud_provider.toUpperCase()}
              </Typography>
              <Typography variant="body2">
                Region: {selectedNode.region || 'N/A'}
              </Typography>
            </Box>
            {selectedNode.resource_type === 'pod' && (
              <Button
                variant="contained"
                size="small"
                startIcon={<Timeline />}
                onClick={() => setFlowDialogOpen(true)}
              >
                Visualize Flow
              </Button>
            )}
          </Stack>
        </Paper>
      )}

      {/* Transaction Flow Dialog */}
      {selectedNode && selectedNode.resource_type === 'pod' && (
        <TransactionFlowDialog
          open={flowDialogOpen}
          onClose={() => setFlowDialogOpen(false)}
          resourceId={selectedNode.id}
          resourceName={selectedNode.name}
        />
      )}
    </Box>
  );
}
