/**
 * Transaction Flow Graph Component
 *
 * Visualizes transaction flow through resources using Cytoscape
 */

import { useEffect, useRef } from 'react';
import { Box } from '@mui/material';
import cytoscape from 'cytoscape';
import type { TransactionFlow } from '../../types';

interface TransactionFlowGraphProps {
  flow: TransactionFlow;
}

export default function TransactionFlowGraph({ flow }: TransactionFlowGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current || !flow) return;

    // Initialize Cytoscape
    const cy = cytoscape({
      container: containerRef.current,
      elements: [],
      style: [
        {
          selector: 'node',
          style: {
            shape: 'rectangle',
            'background-color': '#1976d2',
            label: 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap',
            'text-max-width': '46px',
            color: '#fff',
            'text-outline-color': '#1976d2',
            'text-outline-width': 2,
            width: 60,
            height: 60,
            'font-size': '9px',
            'font-weight': 'bold',
          },
        },
        {
          selector: 'node[status="error"]',
          style: {
            'background-color': '#d32f2f',
            'text-outline-color': '#d32f2f',
          },
        },
        {
          selector: 'node[status="warning"]',
          style: {
            'background-color': '#ed6c02',
            'text-outline-color': '#ed6c02',
          },
        },
        {
          selector: 'node[status="success"]',
          style: {
            'background-color': '#2e7d32',
            'text-outline-color': '#2e7d32',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 3,
            'line-color': '#90caf9',
            'target-arrow-color': '#90caf9',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: 'data(label)',
            'font-size': '9px',
            'text-rotation': 'autorotate',
            'text-margin-y': -10,
            color: '#666',
          },
        },
      ],
      layout: {
        name: 'breadthfirst',
        directed: true,
        spacingFactor: 1.5,
        padding: 30,
      },
    });

    cyRef.current = cy;

    // Add nodes
    flow.nodes.forEach((node) => {
      cy.add({
        group: 'nodes',
        data: {
          id: node.resource_id,
          label: node.resource_name,
          status: node.status,
          resource_type: node.resource_type,
          timestamp: node.timestamp,
          log_count: node.log_count,
          duration_ms: node.duration_ms,
        },
      });
    });

    // Add edges
    flow.edges.forEach((edge, index) => {
      const edgeLabel = edge.protocol || edge.duration_ms
        ? `${edge.protocol || ''}${edge.duration_ms ? ` ${edge.duration_ms.toFixed(0)}ms` : ''}`
        : '';

      cy.add({
        group: 'edges',
        data: {
          id: `edge-${index}`,
          source: edge.source_id,
          target: edge.target_id,
          label: edgeLabel,
          protocol: edge.protocol,
          duration_ms: edge.duration_ms,
        },
      });
    });

    // Apply layout
    cy.layout({
      name: 'breadthfirst',
      directed: true,
      spacingFactor: 1.5,
      padding: 30,
    } as cytoscape.LayoutOptions).run();

    // Add node click handler to show details
    cy.on('tap', 'node', (event) => {
      const node = event.target;
      const data = node.data();
      console.log('Node details:', data);
      // Could show a tooltip or details panel here
    });

    // Fit to viewport
    cy.fit(undefined, 50);

    // Cleanup
    return () => {
      cy.destroy();
    };
  }, [flow]);

  return (
    <Box
      ref={containerRef}
      sx={{
        width: '100%',
        height: '100%',
        minHeight: 400,
        bgcolor: '#fafafa',
      }}
    />
  );
}
