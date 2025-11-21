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
  storage_account: '#ff9800',
  load_balancer: '#f44336',
  gateway: '#00bcd4',
};

// Node sizing constants - increased for better readability
const NODE_WIDTH = 80;
const NODE_HEIGHT = 80;
const NODE_BORDER_WIDTH = 3;
// Text max width derived from node width minus padding
const NODE_TEXT_PADDING = 24;
const NODE_TEXT_MAX_WIDTH = NODE_WIDTH - NODE_TEXT_PADDING;

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
            shape: 'roundrectangle',
            'background-color': (ele: any) =>
              colorMap[ele.data('provider')] || colorMap[ele.data('type')] || '#2196f3',
            label: 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap',
            'text-max-width': `${NODE_TEXT_MAX_WIDTH}px`,
            color: '#fff',
            'font-size': '11px', // Increased from 9px
            'font-weight': 600, // Added for better visibility
            'text-outline-width': 1, // Add text outline for better contrast
            'text-outline-color': '#000',
            width: NODE_WIDTH,
            height: NODE_HEIGHT,
            'border-width': NODE_BORDER_WIDTH,
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
            'line-color': '#64748b',
            'target-arrow-color': '#64748b',
            'target-arrow-shape': 'triangle',
            'curve-style': 'unbundled-bezier',
            'control-point-distances': [20, -20],
            'control-point-weights': [0.25, 0.75],
            label: 'data(label)',
            'font-size': '9px',
            color: '#cbd5e1',
            'font-weight': 500,
            'text-rotation': 'autorotate',
            'text-margin-y': -12,
            'text-background-opacity': 0.9,
            'text-background-color': '#0a1929',
            'text-background-padding': '4px',
            'text-background-shape': 'roundrectangle',
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
        animationDuration: 800,
        animationEasing: 'ease-in-out-cubic',
        nodeRepulsion: 16000, // Increased for better spacing
        idealEdgeLength: 140, // Increased for more spread
        edgeElasticity: 80,
        nestingFactor: 5,
        gravity: 60,
        numIter: 1500,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
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
          maxWidth: 200,
        }}
      >
        <Typography variant="body2" gutterBottom fontWeight={600}>
          Cloud Providers
        </Typography>
        <Box display="flex" flexDirection="column" gap={0.5} mb={2}>
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
        <Typography variant="body2" gutterBottom fontWeight={600}>
          Resource Types
        </Typography>
        <Box display="flex" flexDirection="column" gap={0.5}>
          {[
            { key: 'pod', label: 'Pods', color: colorMap.pod },
            { key: 'service', label: 'Services', color: colorMap.service },
            { key: 'database', label: 'Databases', color: colorMap.database },
            { key: 'storage', label: 'Storage', color: colorMap.storage },
            { key: 'load_balancer', label: 'Load Balancers', color: colorMap.load_balancer },
            { key: 'gateway', label: 'Gateways', color: colorMap.gateway },
          ].map((item) => (
            <Chip
              key={item.key}
              label={item.label}
              size="small"
              sx={{
                backgroundColor: item.color,
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
