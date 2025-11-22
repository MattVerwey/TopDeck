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
  CircularProgress,
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
  Error as ErrorIcon,
} from '@mui/icons-material';
import cytoscape from 'cytoscape';
import type { TopologyGraph as TopologyGraphType, Resource, RiskAssessment, TopologyFilterSettings } from '../../types';
import { useStore } from '../../store/useStore';
import apiClient from '../../services/api';
import { getRiskLevelFromScore } from '../../utils/riskUtils';
import { applyGroupingToElements } from '../../utils/topologyGrouping';


// Constants for node sizing and padding
const NODE_BASE_SIZE = 80; // Increased from 40 for better readability
const NODE_IMPORTANCE_MULTIPLIER = 15; // Increased from 10 for better visual distinction
const NODE_TEXT_PADDING = 24; // Increased padding for better text margins

// Helper function to calculate node size based on importance
const getNodeSize = (ele: cytoscape.NodeSingular): number => {
  return NODE_BASE_SIZE + ((ele.data('importance') as number) || 1) * NODE_IMPORTANCE_MULTIPLIER;
};

interface ServiceDependencyGraphProps {
  data: TopologyGraphType;
}

// Risk-based color scheme - prioritizes risk level over service type
const riskColors: Record<string, string> = {
  critical: '#d32f2f',  // Bright red
  high: '#f57c00',      // Orange
  medium: '#fbc02d',    // Yellow
  low: '#388e3c',       // Green
  unknown: '#607d8b',   // Gray
};

// Enhanced color scheme for service types (used when no risk data)
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
  storage_account: '#ff9800',
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

// Get color based on risk level first, then resource type or provider
const getNodeColor = (node: Resource, riskLevel?: string): string => {
  // Prioritize risk level for coloring
  if (riskLevel) {
    return riskColors[riskLevel.toLowerCase()] || riskColors.unknown;
  }
  
  // Fallback to service type colors
  const type = node.resource_type?.toLowerCase() || '';
  const provider = node.cloud_provider?.toLowerCase() || '';
  
  return serviceColors[type] || serviceColors[provider] || '#607d8b';
};

// Helper to get node's risk level from risk assessments
const getNodeRiskLevel = (nodeId: string, riskMap: Map<string, RiskAssessment>): string | undefined => {
  const risk = riskMap.get(nodeId);
  if (!risk) return undefined;
  
  return risk.risk_level?.toLowerCase() ||
    (risk.risk_score !== undefined && risk.risk_score !== null && !Number.isNaN(risk.risk_score)
      ? getRiskLevelFromScore(risk.risk_score).toLowerCase()
      : 'unknown');
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
  const { setSelectedResource, filterSettings } = useStore();
  const [selectedNode, setSelectedNode] = useState<Resource | null>(null);
  const [graphStats, setGraphStats] = useState({
    nodes: 0,
    edges: 0,
    providers: new Set<string>(),
    types: new Set<string>(),
  });
  const [riskAssessments, setRiskAssessments] = useState<Map<string, RiskAssessment>>(new Map());
  const [loadingRisks, setLoadingRisks] = useState(false);
  const [riskStats, setRiskStats] = useState({
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    unknown: 0,
  });

  // Load risk assessments for all nodes
  useEffect(() => {
    if (!data || data.nodes.length === 0) return;

    const loadRiskAssessments = async () => {
      setLoadingRisks(true);
      try {
        // Try bulk endpoint first
        let allRisks: RiskAssessment[] = [];
        try {
          allRisks = await apiClient.getAllRisks();
          console.log(`Loaded ${allRisks.length} risk assessments via bulk endpoint`);
        } catch (bulkError) {
          // Log bulk endpoint failure and fallback to individual requests
          console.warn('Bulk risk endpoint failed, falling back to individual requests:', bulkError);
          
          // Batch requests in chunks of 10 to avoid overwhelming the server
          const BATCH_SIZE = 10;
          const allRisksBatch: (RiskAssessment | null)[] = [];
          for (let i = 0; i < data.nodes.length; i += BATCH_SIZE) {
            const chunk = data.nodes.slice(i, i + BATCH_SIZE);
            const chunkRisks = await Promise.all(
              chunk.map(node =>
                apiClient.getRiskAssessment(node.id).catch(err => {
                  console.debug(`Failed to fetch risk for ${node.id}:`, err);
                  return null;
                })
              )
            );
            allRisksBatch.push(...chunkRisks);
          }
          allRisks = allRisksBatch.filter((r): r is RiskAssessment => r !== null);
          console.log(`Loaded ${allRisks.length}/${data.nodes.length} risk assessments via batched individual requests`);
        }

        // Create a map of resource_id to risk assessment
        const riskMap = new Map<string, RiskAssessment>();
        const stats = { critical: 0, high: 0, medium: 0, low: 0, unknown: 0 };
        
        allRisks.forEach(risk => {
          riskMap.set(risk.resource_id, risk);
          const level = risk.risk_level?.toLowerCase() ||
            (risk.risk_score !== undefined && risk.risk_score !== null && !Number.isNaN(risk.risk_score)
              ? getRiskLevelFromScore(risk.risk_score).toLowerCase()
              : 'unknown');
          if (level === 'critical') stats.critical++;
          else if (level === 'high') stats.high++;
          else if (level === 'medium') stats.medium++;
          else if (level === 'low') stats.low++;
          else stats.unknown++;
        });

        setRiskAssessments(riskMap);
        setRiskStats(stats);
      } catch (error) {
        console.error('Failed to load risk assessments:', error);
      } finally {
        setLoadingRisks(false);
      }
    };

    loadRiskAssessments();
  }, [data]);

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

    // Convert data to Cytoscape format with enhanced metadata including risk
    const elements = [
      ...data.nodes.map((node) => {
        const risk = riskAssessments.get(node.id);
        const riskLevel = risk
          ? (
              risk.risk_level?.toLowerCase() ||
              (
                risk.risk_score !== undefined &&
                risk.risk_score !== null &&
                !Number.isNaN(risk.risk_score)
                  ? getRiskLevelFromScore(risk.risk_score)
                  : 'unknown'
              )
            )
          : 'unknown';
        
        return {
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
            // Risk data
            riskLevel,
            riskScore: risk?.risk_score,
            blastRadius: risk?.blast_radius,
            spof: risk?.single_point_of_failure || false,
          },
        };
      }),
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

    // Apply grouping if enabled
    const finalElements = filterSettings.showGrouping && filterSettings.groupBy
      ? applyGroupingToElements(elements, filterSettings.groupBy, data.nodes)
      : elements;

    // Initialize Cytoscape with enhanced styling
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: finalElements,
      style: [
        // Group node styling
        {
          selector: '.group-node',
          style: {
            shape: 'roundrectangle',
            'background-color': '#1e293b',
            'background-opacity': 0.1,
            'border-width': 2,
            'border-color': '#475569',
            'border-style': 'dashed',
            label: 'data(label)',
            'text-valign': 'top',
            'text-halign': 'center',
            'text-margin-y': 10,
            'font-size': '14px',
            'font-weight': 700,
            color: '#cbd5e1',
            'padding': 20,
          } as cytoscape.Css.Node,
        },
        {
          selector: 'node',
          style: {
            shape: 'roundrectangle',
            'background-color': (ele: cytoscape.NodeSingular) => {
              const nodeData = ele.data() as Resource & { riskLevel?: string };
              return getNodeColor(nodeData, nodeData.riskLevel);
            },
            label: 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap',
            // Text width calculated as node width minus padding for readability
            'text-max-width': (ele: cytoscape.NodeSingular) => `${getNodeSize(ele) - NODE_TEXT_PADDING}px`,
            color: '#fff',
            'font-size': '11px', // Increased from 9px for better readability
            'font-weight': 600, // Increased from 500 for better visibility
            'text-outline-width': 1, // Add text outline for better contrast
            'text-outline-color': '#000',
            width: getNodeSize,
            height: getNodeSize,
            'border-width': 3,
            'border-color': '#1e293b',
            'overlay-opacity': 0,
          } as cytoscape.Css.Node,
        },
        {
          selector: 'node[?spof]',
          style: {
            'border-width': 5,
            'border-color': '#ff1744', // Bright red border for SPOF
            'border-style': 'double',
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
            width: 2, // Reduced from 3 to declutter
            'line-color': '#64748b',
            'target-arrow-color': '#64748b',
            'target-arrow-shape': 'triangle',
            'curve-style': 'unbundled-bezier', // Changed from 'bezier' for better edge routing
            'control-point-distances': [20, -20], // Add control points for better curve
            'control-point-weights': [0.25, 0.75],
            'arrow-scale': 1.3, // Reduced from 1.5
            label: 'data(label)',
            'font-size': '9px', // Reduced from 10px to declutter
            'font-weight': 500,
            color: '#cbd5e1',
            'text-rotation': 'autorotate',
            'text-margin-y': -12,
            'text-background-opacity': 0.9,
            'text-background-color': '#0f172a',
            'text-background-padding': '4px',
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
        nodeRepulsion: 20000, // Increased from 12000 for better spacing
        idealEdgeLength: 150, // Increased from 120 for more spread
        edgeElasticity: 80, // Reduced from 100 for less bouncing
        nestingFactor: 5,
        gravity: 60, // Reduced from 80 for looser clustering
        numIter: 1500, // Increased from 1000 for better convergence
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
  }, [data, setSelectedResource, riskAssessments, filterSettings]);

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
            {!loadingRisks && riskAssessments.size > 0 && (
              <Grid size={{ xs: 12 }}>
                <Divider sx={{ my: 1 }} />
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Risk Distribution
                </Typography>
                <Stack spacing={0.5}>
                  {riskStats.critical > 0 && (
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <Box sx={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: riskColors.critical }} />
                        <Typography variant="caption">Critical</Typography>
                      </Box>
                      <Typography variant="caption" fontWeight={600}>{riskStats.critical}</Typography>
                    </Box>
                  )}
                  {riskStats.high > 0 && (
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <Box sx={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: riskColors.high }} />
                        <Typography variant="caption">High</Typography>
                      </Box>
                      <Typography variant="caption" fontWeight={600}>{riskStats.high}</Typography>
                    </Box>
                  )}
                  {riskStats.medium > 0 && (
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <Box sx={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: riskColors.medium }} />
                        <Typography variant="caption">Medium</Typography>
                      </Box>
                      <Typography variant="caption" fontWeight={600}>{riskStats.medium}</Typography>
                    </Box>
                  )}
                  {riskStats.low > 0 && (
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <Box sx={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: riskColors.low }} />
                        <Typography variant="caption">Low</Typography>
                      </Box>
                      <Typography variant="caption" fontWeight={600}>{riskStats.low}</Typography>
                    </Box>
                  )}
                </Stack>
              </Grid>
            )}
            {loadingRisks && (
              <Grid size={{ xs: 12 }}>
                <Box display="flex" alignItems="center" gap={1} justifyContent="center" py={1}>
                  <CircularProgress size={16} />
                  <Typography variant="caption" color="text.secondary">
                    Loading risks...
                  </Typography>
                </Box>
              </Grid>
            )}
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
                        backgroundColor: getNodeColor(selectedNode, getNodeRiskLevel(selectedNode.id, riskAssessments)),
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
                  <Stack direction="row" spacing={1}>
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
                    {(() => {
                      const riskLevel = getNodeRiskLevel(selectedNode.id, riskAssessments);
                      if (riskLevel) {
                        const riskIcon = riskLevel === 'critical' ? <ErrorIcon /> :
                                       riskLevel === 'high' ? <Warning /> :
                                       riskLevel === 'medium' ? <Info /> :
                                       <CheckCircle />;
                        return (
                          <Chip
                            icon={riskIcon}
                            label={`${riskLevel.toUpperCase()} Risk`}
                            sx={{
                              backgroundColor: riskColors[riskLevel],
                              color: '#fff',
                              fontWeight: 600,
                            }}
                          />
                        );
                      }
                      return null;
                    })()}
                  </Stack>
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
                    backgroundColor: getNodeColor(selectedNode, getNodeRiskLevel(selectedNode.id, riskAssessments)),
                    color: '#fff',
                    fontWeight: 500,
                  }}
                />
              </Grid>

              {/* Risk Metrics */}
              {(() => {
                const risk = riskAssessments.get(selectedNode.id);
                if (risk) {
                  return (
                    <>
                      <Grid size={{ xs: 12 }}>
                        <Divider />
                      </Grid>
                      <Grid size={{ xs: 12 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Risk Metrics
                        </Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap" gap={0.5}>
                          {risk.risk_score !== undefined && risk.risk_score !== null && (
                            <Chip
                              label={`Risk Score: ${risk.risk_score.toFixed(1)}`}
                              size="small"
                              variant="outlined"
                              color={
                                risk.risk_score >= 75 ? 'error' :
                                risk.risk_score >= 50 ? 'warning' :
                                risk.risk_score >= 25 ? 'info' : 'success'
                              }
                            />
                          )}
                          {risk.blast_radius !== undefined && risk.blast_radius !== null && (
                            <Chip
                              label={`Blast Radius: ${risk.blast_radius}`}
                              size="small"
                              variant="outlined"
                              color={risk.blast_radius > 10 ? 'warning' : 'info'}
                            />
                          )}
                          {risk.dependencies_count !== undefined && (
                            <Chip
                              label={`Dependencies: ${risk.dependencies_count}`}
                              size="small"
                              variant="outlined"
                            />
                          )}
                          {risk.dependents_count !== undefined && (
                            <Chip
                              label={`Dependents: ${risk.dependents_count}`}
                              size="small"
                              variant="outlined"
                              color={risk.dependents_count > 5 ? 'warning' : 'info'}
                            />
                          )}
                          {risk.single_point_of_failure && (
                            <Chip
                              label="SPOF"
                              size="small"
                              color="error"
                              variant="filled"
                            />
                          )}
                        </Stack>
                      </Grid>
                    </>
                  );
                }
                return null;
              })()}

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
          minWidth: 200,
          maxWidth: 220,
          opacity: 0.95,
        }}
      >
        <CardContent>
          <Typography variant="body2" fontWeight={600} gutterBottom>
            Risk Levels
          </Typography>
          <Stack spacing={0.5} mb={2}>
            {[
              { label: 'Critical Risk', color: riskColors.critical },
              { label: 'High Risk', color: riskColors.high },
              { label: 'Medium Risk', color: riskColors.medium },
              { label: 'Low Risk', color: riskColors.low },
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
          <Divider sx={{ my: 1 }} />
          <Typography variant="body2" fontWeight={600} gutterBottom>
            Resource Types
          </Typography>
          <Stack spacing={0.5}>
            {[
              { label: 'Pods', color: serviceColors.pod },
              { label: 'Services', color: serviceColors.service },
              { label: 'Deployments', color: serviceColors.deployment },
              { label: 'Databases', color: serviceColors.database },
              { label: 'Storage Accounts', color: serviceColors.storage_account },
              { label: 'Cache/Redis', color: serviceColors.cache },
              { label: 'Load Balancers', color: serviceColors.load_balancer },
              { label: 'App Gateways', color: serviceColors.application_gateway },
              { label: 'Service Bus', color: serviceColors.servicebus_namespace },
              { label: 'AKS Clusters', color: serviceColors.aks_cluster },
              { label: 'App Services', color: serviceColors.app_service },
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
          <Divider sx={{ my: 1 }} />
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 16,
                height: 16,
                borderRadius: '4px',
                border: '3px double #ff1744',
                backgroundColor: 'transparent',
              }}
            />
            <Typography variant="caption">Single Point of Failure</Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
