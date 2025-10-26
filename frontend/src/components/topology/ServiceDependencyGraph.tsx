/**
 * Enhanced Service Dependency Graph with modern UI and improved visualization
 * Shows service dependencies with clear directional arrows and detailed service information
 */

import { useEffect, useRef, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Stack,
  IconButton,
  Tooltip,
  Divider,
  Button,
} from '@mui/material';
import {
  ZoomIn,
  ZoomOut,
  CenterFocusStrong,
  Timeline,
  Storage,
  Cloud,
  AccountTree,
  Info,
  Warning,
  CheckCircle,
} from '@mui/icons-material';
import cytoscape from 'cytoscape';
import type { TopologyGraph as TopologyGraphType, Resource } from '../../types';
import { useStore } from '../../store/useStore';

interface ServiceDependencyGraphProps {
  data: TopologyGraphType;
}

// Enhanced color scheme for service types
const serviceColors: Record<string, string> = {
  // Core services
  pod: '#4caf50',
  service: '#2196f3',
  deployment: '#00bcd4',
  
  // Data layer
  database: '#9c27b0',
  sql_database: '#7b1fa2',
  cosmosdb: '#6a1b9a',
  storage: '#ff9800',
  cache: '#f44336',
  
  // Messaging (Service Bus)
  servicebus_namespace: '#8b5cf6',
  servicebus_topic: '#a78bfa',
  servicebus_queue: '#c4b5fd',
  servicebus_subscription: '#ddd6fe',
  
  // Network layer
  load_balancer: '#e91e63',
  application_gateway: '#ec407a',
  gateway: '#00bcd4',
  
  // Compute
  aks_cluster: '#3f51b5',
  app_service: '#1976d2',
  function_app: '#0288d1',
  
  // Cloud providers
  azure: '#0078d4',
  aws: '#ff9900',
  gcp: '#4285f4',
};

// Get color based on resource type or provider
const getNodeColor = (node: Resource): string => {
  const type = node.resource_type?.toLowerCase() || '';
  const provider = node.cloud_provider?.toLowerCase() || '';
  
  return serviceColors[type] || serviceColors[provider] || '#607d8b';
};

// Relationship type to description mapping
const relationshipLabels: Record<string, string> = {
  depends_on: 'depends on',
  deployed_to: 'deployed to',
  connects_to: 'connects to',
  routes_to: 'routes to',
  stores_in: 'stores in',
  accesses: 'accesses',
  uses: 'uses',
  publishes_to: 'publishes to',
  subscribes_from: 'subscribes from',
  contains: 'contains',
};

export default function ServiceDependencyGraph({ data }: ServiceDependencyGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const { setSelectedResource } = useStore();
  const [selectedNode, setSelectedNode] = useState<Resource | null>(null);
  const [graphStats, setGraphStats] = useState({
    nodes: 0,
    edges: 0,
    providers: new Set<string>(),
    types: new Set<string>(),
  });

  useEffect(() => {
    if (!containerRef.current || !data) return;

    // Calculate graph statistics
    const providers = new Set(data.nodes.map(n => n.cloud_provider));
    const types = new Set(data.nodes.map(n => n.resource_type));
    setGraphStats({
      nodes: data.nodes.length,
      edges: data.edges.length,
      providers,
      types,
    });

    // Convert data to Cytoscape format with enhanced metadata
    const elements = [
      ...data.nodes.map((node) => ({
        data: {
          ...node,
          id: node.id,
          label: node.name,
          type: node.resource_type,
          provider: node.cloud_provider,
          region: node.region || 'N/A',
          // Add properties for better visualization
          importance: node.metadata?.importance || 1,
          health: node.properties?.health_status || 'unknown',
        },
      })),
      ...data.edges.map((edge, idx) => ({
        data: {
          ...edge,
          id: `edge-${idx}`,
          source: edge.source_id,
          target: edge.target_id,
          label: relationshipLabels[edge.relationship_type] || edge.relationship_type,
          relType: edge.relationship_type,
        },
      })),
    ];

    // Initialize Cytoscape with enhanced styling
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            shape: 'rectangle',
            'background-color': (ele: cytoscape.NodeSingular) =>
              getNodeColor(ele.data() as Resource),
            label: 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap',
            'text-max-width': (ele: cytoscape.NodeSingular) => `${(40 + ((ele.data('importance') as number) || 1) * 10) - 16}px`,
            color: '#fff',
            'font-size': '10px',
            'font-weight': 500,
            width: (ele: cytoscape.NodeSingular) => 40 + ((ele.data('importance') as number) || 1) * 10,
            height: (ele: cytoscape.NodeSingular) => 40 + ((ele.data('importance') as number) || 1) * 10,
            'border-width': 3,
            'border-color': '#1e293b',
            'overlay-opacity': 0,
          } as cytoscape.Css.Node,
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 5,
            'border-color': '#fbbf24',
          } as cytoscape.Css.Node,
        },
        {
          selector: 'node:active',
          style: {
            'border-color': '#60a5fa',
          } as cytoscape.Css.Node,
        },
        {
          selector: 'edge',
          style: {
            width: 3,
            'line-color': '#475569',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 1.5,
            label: 'data(label)',
            'font-size': '10px',
            'font-weight': 500,
            color: '#94a3b8',
            'text-rotation': 'autorotate',
            'text-margin-y': -10,
            'text-background-opacity': 0.8,
            'text-background-color': '#0f172a',
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            'overlay-opacity': 0,
          },
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#fbbf24',
            'target-arrow-color': '#fbbf24',
            width: 4,
          },
        },
        {
          selector: 'edge:active',
          style: {
            'line-color': '#60a5fa',
            'target-arrow-color': '#60a5fa',
          } as cytoscape.Css.Edge,
        },
      ],
      layout: {
        name: 'cose',
        animate: true,
        animationDuration: 800,
        animationEasing: 'ease-in-out-cubic',
        nodeRepulsion: 12000,
        idealEdgeLength: 120,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
      },
      minZoom: 0.1,
      maxZoom: 4,
      wheelSensitivity: 0.2,
    });

    // Add event handlers
    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeData = node.data() as Resource;
      setSelectedNode(nodeData);
      setSelectedResource(nodeData);
      
      // Highlight connected edges and nodes
      cyRef.current?.$('node').removeClass('highlighted');
      cyRef.current?.$('edge').removeClass('highlighted');
      
      node.addClass('highlighted');
      node.connectedEdges().addClass('highlighted');
      node.connectedEdges().connectedNodes().addClass('highlighted');
    });

    cyRef.current.on('tap', (evt) => {
      if (evt.target === cyRef.current) {
        // Clicked on background - clear selection
        setSelectedNode(null);
        cyRef.current?.$('.highlighted').removeClass('highlighted');
      }
    });

    // Fit to view with padding
    cyRef.current.fit(undefined, 80);

    return () => {
      cyRef.current?.destroy();
    };
  }, [data, setSelectedResource]);

  // Zoom controls
  const handleZoomIn = () => {
    const zoom = cyRef.current?.zoom() || 1;
    cyRef.current?.zoom({
      level: zoom * 1.2,
      renderedPosition: { x: window.innerWidth / 2, y: window.innerHeight / 2 },
    });
  };

  const handleZoomOut = () => {
    const zoom = cyRef.current?.zoom() || 1;
    cyRef.current?.zoom({
      level: zoom / 1.2,
      renderedPosition: { x: window.innerWidth / 2, y: window.innerHeight / 2 },
    });
  };

  const handleCenter = () => {
    cyRef.current?.fit(undefined, 80);
  };

  // Get health status icon and color
  const getHealthStatus = (status: string | undefined) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'running':
        return { icon: <CheckCircle />, color: '#4caf50', text: 'Healthy' };
      case 'degraded':
      case 'warning':
        return { icon: <Warning />, color: '#ff9800', text: 'Degraded' };
      case 'unhealthy':
      case 'error':
        return { icon: <Warning />, color: '#f44336', text: 'Unhealthy' };
      default:
        return { icon: <Info />, color: '#607d8b', text: 'Unknown' };
    }
  };

  const health = selectedNode ? getHealthStatus((selectedNode.properties?.health_status as string) || 'unknown') : null;

  return (
    <Box sx={{ position: 'relative', height: '100%', width: '100%' }}>
      {/* Graph Container */}
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          backgroundColor: '#0f172a',
          borderRadius: '8px',
        }}
      />

      {/* Zoom Controls */}
      <Paper
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          p: 1,
          opacity: 0.95,
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
        }}
      >
        <Tooltip title="Zoom In" placement="left">
          <IconButton onClick={handleZoomIn} size="small">
            <ZoomIn />
          </IconButton>
        </Tooltip>
        <Tooltip title="Zoom Out" placement="left">
          <IconButton onClick={handleZoomOut} size="small">
            <ZoomOut />
          </IconButton>
        </Tooltip>
        <Tooltip title="Fit to Screen" placement="left">
          <IconButton onClick={handleCenter} size="small">
            <CenterFocusStrong />
          </IconButton>
        </Tooltip>
      </Paper>

      {/* Stats Card */}
      <Card
        sx={{
          position: 'absolute',
          top: 16,
          left: 16,
          minWidth: 240,
          opacity: 0.95,
        }}
      >
        <CardContent>
          <Typography variant="h6" gutterBottom fontWeight={600}>
            Dependency Graph
          </Typography>
          <Divider sx={{ my: 1 }} />
          <Grid container spacing={2}>
            <Grid size={{ xs: 6 }}>
              <Typography variant="body2" color="text.secondary">
                Services
              </Typography>
              <Typography variant="h5" fontWeight={600}>
                {graphStats.nodes}
              </Typography>
            </Grid>
            <Grid size={{ xs: 6 }}>
              <Typography variant="body2" color="text.secondary">
                Dependencies
              </Typography>
              <Typography variant="h5" fontWeight={600}>
                {graphStats.edges}
              </Typography>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Cloud Providers
              </Typography>
              <Stack direction="row" spacing={0.5} flexWrap="wrap" gap={0.5}>
                {Array.from(graphStats.providers).map((provider) => (
                  <Chip
                    key={provider}
                    label={provider.toUpperCase()}
                    size="small"
                    sx={{
                      backgroundColor: serviceColors[provider] || '#607d8b',
                      color: '#fff',
                      fontWeight: 500,
                      fontSize: '0.7rem',
                    }}
                  />
                ))}
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Selected Service Details Panel */}
      {selectedNode && (
        <Card
          sx={{
            position: 'absolute',
            bottom: 16,
            left: 16,
            right: 16,
            maxWidth: 800,
            mx: 'auto',
            opacity: 0.97,
          }}
        >
          <CardContent>
            <Grid container spacing={3}>
              {/* Service Header */}
              <Grid size={{ xs: 12 }}>
                <Stack direction="row" alignItems="center" spacing={2} justifyContent="space-between">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        borderRadius: '8px',
                        backgroundColor: getNodeColor(selectedNode),
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      {selectedNode.resource_type?.includes('database') ? (
                        <Storage sx={{ color: '#fff' }} />
                      ) : selectedNode.resource_type === 'pod' ? (
                        <AccountTree sx={{ color: '#fff' }} />
                      ) : (
                        <Cloud sx={{ color: '#fff' }} />
                      )}
                    </Box>
                    <Box>
                      <Typography variant="h6" fontWeight={600}>
                        {selectedNode.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {selectedNode.resource_type} • {selectedNode.cloud_provider.toUpperCase()}
                      </Typography>
                    </Box>
                  </Box>
                  {health && (
                    <Chip
                      icon={health.icon}
                      label={health.text}
                      sx={{
                        backgroundColor: health.color,
                        color: '#fff',
                        fontWeight: 600,
                      }}
                    />
                  )}
                </Stack>
              </Grid>

              <Grid size={{ xs: 12 }}>
                <Divider />
              </Grid>

              {/* Service Details */}
              <Grid size={{ xs: 12, md: 4 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Region
                </Typography>
                <Typography variant="body1" fontWeight={500}>
                  {selectedNode.region || 'N/A'}
                </Typography>
              </Grid>

              <Grid size={{ xs: 12, md: 4 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Resource ID
                </Typography>
                <Typography
                  variant="body1"
                  fontWeight={500}
                  sx={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {selectedNode.id.split('/').pop() || selectedNode.id}
                </Typography>
              </Grid>

              <Grid size={{ xs: 12, md: 4 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Type
                </Typography>
                <Chip
                  label={selectedNode.resource_type}
                  size="small"
                  sx={{
                    backgroundColor: getNodeColor(selectedNode),
                    color: '#fff',
                    fontWeight: 500,
                  }}
                />
              </Grid>

              {/* Additional Properties */}
              {Object.keys(selectedNode.properties || {}).length > 0 && (
                <Grid size={{ xs: 12 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Properties
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" gap={0.5}>
                    {Object.entries(selectedNode.properties || {})
                      .slice(0, 5)
                      .map(([key, value]) => (
                        <Chip
                          key={key}
                          label={`${key}: ${String(value).substring(0, 20)}`}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                  </Stack>
                </Grid>
              )}

              {/* Actions */}
              <Grid size={{ xs: 12 }}>
                <Stack direction="row" spacing={2}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Timeline />}
                    onClick={() => {
                      // This could navigate to a detailed view
                      console.log('View dependencies for:', selectedNode.id);
                    }}
                  >
                    View Dependencies
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Info />}
                    onClick={() => {
                      // This could show more details
                      console.log('View details for:', selectedNode.id);
                    }}
                  >
                    More Details
                  </Button>
                </Stack>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Legend */}
      <Card
        sx={{
          position: 'absolute',
          top: 200,
          right: 16,
          minWidth: 180,
          opacity: 0.95,
        }}
      >
        <CardContent>
          <Typography variant="body2" fontWeight={600} gutterBottom>
            Service Types
          </Typography>
          <Stack spacing={0.5}>
            {[
              { label: 'Services', color: serviceColors.service },
              { label: 'Databases', color: serviceColors.database },
              { label: 'Load Balancers', color: serviceColors.load_balancer },
              { label: 'Storage', color: serviceColors.storage },
            ].map((item) => (
              <Box key={item.label} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box
                  sx={{
                    width: 16,
                    height: 16,
                    borderRadius: '4px',
                    backgroundColor: item.color,
                  }}
                />
                <Typography variant="caption">{item.label}</Typography>
              </Box>
            ))}
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
