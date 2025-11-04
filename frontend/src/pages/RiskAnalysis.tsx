/**
 * Risk Analysis page with risk heatmap and metrics
 */

import { useEffect, useState, useMemo, memo } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useStore } from '../store/useStore';
import RiskBreakdown from '../components/risk/RiskBreakdown';
import ResourceTester from '../components/risk/ResourceTester';
import ResourceQuery from '../components/risk/ResourceQuery';
import RemediationSuggestions from '../components/risk/RemediationSuggestions';
import PredictionAnalysis from '../components/risk/PredictionAnalysis';
import RiskDrilldownDialog from '../components/risk/RiskDrilldownDialog';
import DocLink from '../components/common/DocLink';
import apiClient from '../services/api';
import type { RiskAssessment } from '../types';
import { getRiskLevelFromScore } from '../utils/riskUtils';

interface RiskMetric {
  name: string;
  count: number;
  color: string;
}

// Memoized components for better performance
const MemoizedRiskCard = memo(({ 
  metric, 
  nodeCount, 
  onClick 
}: { 
  metric: RiskMetric; 
  nodeCount: number;
  onClick: () => void;
}) => (
  <Card
    sx={{
      background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
      borderLeft: `4px solid ${metric.color}`,
      cursor: 'pointer',
      transition: 'all 0.2s',
      '&:hover': {
        transform: 'translateY(-4px)',
        boxShadow: 4,
        borderLeftWidth: '6px',
      },
    }}
    onClick={onClick}
  >
    <CardContent>
      <Typography variant="h4" fontWeight={700}>
        {metric.count}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {metric.name} Risk
      </Typography>
      <LinearProgress
        variant="determinate"
        value={(metric.count / (nodeCount || 1)) * 100}
        sx={{ mt: 2, height: 6, borderRadius: 3 }}
      />
      <Typography variant="caption" color="primary" sx={{ mt: 1, display: 'block' }}>
        Click to view details
      </Typography>
    </CardContent>
  </Card>
));

MemoizedRiskCard.displayName = 'MemoizedRiskCard';

interface DefaultRisk {
  id: number;
  title: string;
  description: string;
  severity: string;
  affected: number;
}

export default function RiskAnalysis() {
  const { topology, setLoading, setError, loading, error } = useStore();
  const [riskData, setRiskData] = useState<RiskMetric[]>([]);
  const [defaultRisks, setDefaultRisks] = useState<DefaultRisk[]>([]);
  const [activeTab, setActiveTab] = useState(0);
  const [drilldownOpen, setDrilldownOpen] = useState(false);
  const [selectedRiskLevel, setSelectedRiskLevel] = useState<'critical' | 'high' | 'medium' | 'low'>('critical');

  useEffect(() => {
    loadRiskData();
  }, [topology]);

  const loadRiskData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Load topology if not available
      let currentTopology = topology;
      if (!currentTopology) {
        try {
          console.log('Loading topology for risk analysis...');
          currentTopology = await apiClient.getTopology();
          useStore.getState().setTopology(currentTopology);
        } catch (err) {
          console.warn('Failed to load topology, using empty state:', err);
          // If topology loading fails, use empty state
          currentTopology = {
            nodes: [],
            edges: [],
            metadata: { total_nodes: 0, total_edges: 0 },
          };
        }
      }

      const nodeCount = currentTopology?.nodes.length || 0;
      
      // Fetch real risk assessments from API
      let allRisks: RiskAssessment[] = [];
      if (currentTopology?.nodes && currentTopology.nodes.length > 0) {
        try {
          console.log(`Fetching risk assessments for ${currentTopology.nodes.length} resources...`);
          // Try to fetch all risks for each resource
          const riskPromises = currentTopology.nodes.map(node => 
            apiClient.getRiskAssessment(node.id).catch(err => {
              console.warn('Failed to fetch risk for resource', node.id, err);
              return null;
            })
          );
          const risks = await Promise.all(riskPromises);
          allRisks = risks.filter((r): r is RiskAssessment => r !== null);
          console.log(`Successfully fetched ${allRisks.length} risk assessments`);
        } catch (err) {
          // Catch unexpected errors during Promise.all operation
          console.warn('Unexpected error fetching risk assessments:', err);
        }
      }

      // Calculate risk distribution from actual data
      const riskCounts = {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
      };

      allRisks.forEach(risk => {
        const level = risk.risk_level?.toLowerCase() || getRiskLevelFromScore(risk.risk_score);
        if (level === 'critical') riskCounts.critical++;
        else if (level === 'high') riskCounts.high++;
        else if (level === 'medium') riskCounts.medium++;
        else riskCounts.low++;
      });

      // If no API data but we have nodes, use estimates based on topology
      // These percentages provide reasonable defaults based on typical risk distribution:
      // - 5% critical: high-impact resources (databases, core services)
      // - 15% high: important but not critical resources
      // - 30% medium: standard resources with some dependencies
      // - Remainder: low-risk resources
      // Only use estimates if we actually have resources in topology
      if (allRisks.length === 0 && nodeCount > 0) {
        console.log('No risk assessments available, using estimates based on topology');
        const CRITICAL_PERCENTAGE = 0.05;
        const HIGH_PERCENTAGE = 0.15;
        const MEDIUM_PERCENTAGE = 0.30;

        riskCounts.critical = Math.floor(nodeCount * CRITICAL_PERCENTAGE);
        riskCounts.high = Math.floor(nodeCount * HIGH_PERCENTAGE);
        riskCounts.medium = Math.floor(nodeCount * MEDIUM_PERCENTAGE);
        riskCounts.low = nodeCount - riskCounts.critical - riskCounts.high - riskCounts.medium;
      }

      const riskMetrics: RiskMetric[] = [
        { name: 'Critical', count: riskCounts.critical, color: '#f44336' },
        { name: 'High', count: riskCounts.high, color: '#ff9800' },
        { name: 'Medium', count: riskCounts.medium, color: '#ffeb3b' },
        { name: 'Low', count: riskCounts.low, color: '#4caf50' },
      ];

      setRiskData(riskMetrics);

      // Identify real risks from assessments
      const spofResources = allRisks.filter(r => r.single_point_of_failure);
      const highDependencyResources = allRisks.filter(r => r.dependents_count > 10);
      const highBlastRadiusResources = allRisks.filter(r => r.blast_radius > 20);

      const defaultRisksData: DefaultRisk[] = [];
      
      if (spofResources.length > 0) {
        const totalAffected = spofResources.reduce((sum, r) => sum + r.dependents_count, 0);
        defaultRisksData.push({
          id: 1,
          title: 'Single Point of Failure Detected',
          description: `${spofResources.length} resource${spofResources.length > 1 ? 's have' : ' has'} no redundancy: ${spofResources.slice(0, 2).map(r => r.resource_name || r.resource_id).join(', ')}${spofResources.length > 2 ? '...' : ''}`,
          severity: 'critical',
          affected: totalAffected,
        });
      }

      if (highDependencyResources.length > 0) {
        const maxDeps = Math.max(...highDependencyResources.map(r => r.dependents_count));
        const resource = highDependencyResources.find(r => r.dependents_count === maxDeps);
        defaultRisksData.push({
          id: 2,
          title: 'High Dependency Count',
          description: `${resource?.resource_name || 'Resource'} has ${maxDeps} dependent services`,
          severity: 'high',
          affected: maxDeps,
        });
      }

      if (highBlastRadiusResources.length > 0) {
        const maxBlast = Math.max(...highBlastRadiusResources.map(r => r.blast_radius));
        const resource = highBlastRadiusResources.find(r => r.blast_radius === maxBlast);
        defaultRisksData.push({
          id: 3,
          title: 'Large Blast Radius',
          description: `${resource?.resource_name || 'Resource'} affects ${maxBlast} resources if it fails`,
          severity: 'high',
          affected: maxBlast,
        });
      }

      // Add fallback risks if no real risks found
      if (defaultRisksData.length === 0) {
        if (nodeCount === 0) {
          defaultRisksData.push({
            id: 1,
            title: 'No Resources Discovered',
            description: 'No resources found in topology. Run resource discovery to populate the system.',
            severity: 'info',
            affected: 0,
          });
        } else if (allRisks.length === 0) {
          defaultRisksData.push({
            id: 1,
            title: 'Risk Analysis Unavailable',
            description: `Found ${nodeCount} resources but could not fetch risk assessments. Check API connectivity.`,
            severity: 'info',
            affected: 0,
          });
        } else {
          defaultRisksData.push({
            id: 1,
            title: 'No Critical Risks Detected',
            description: 'No significant risks found. All resources appear healthy.',
            severity: 'info',
            affected: 0,
          });
        }
      }

      setDefaultRisks(defaultRisksData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load risk data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleRiskCardClick = (riskLevel: 'critical' | 'high' | 'medium' | 'low') => {
    setSelectedRiskLevel(riskLevel);
    setDrilldownOpen(true);
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'high':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      default:
        return 'success';
    }
  };

  // Memoize node count for performance
  const nodeCount = useMemo(() => topology?.nodes.length || 5, [topology?.nodes.length]);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4" fontWeight={600}>
          Risk Analysis
        </Typography>
        <DocLink href="docs/ENHANCED_RISK_ANALYSIS.md" text="Risk Analysis Guide" />
      </Box>

      {/* Tabs for different sections */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant="fullWidth"
        >
          <Tab label="Overview" />
          <Tab label="Prediction Analysis" />
          <Tab label="Remediation Suggestions" />
          <Tab label="Resource Testing" />
          <Tab label="Query Assistant" />
          <Tab label="Risk Breakdown" />
        </Tabs>
      </Paper>

      {/* Overview Tab */}
      {activeTab === 0 && (
        <>
          {loading && (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
              <CircularProgress />
            </Box>
          )}

          {error && <Alert severity="error">{error}</Alert>}

          {!loading && !error && (
            <>
              {/* Risk Distribution */}
              <Grid container spacing={3} sx={{ mb: 4 }}>
                {riskData.map((metric) => (
                  <Grid size={{ xs: 12, sm: 6, md: 3 }} key={metric.name}>
                    <MemoizedRiskCard 
                      metric={metric} 
                      nodeCount={nodeCount}
                      onClick={() => handleRiskCardClick(metric.name.toLowerCase() as 'critical' | 'high' | 'medium' | 'low')}
                    />
                  </Grid>
                ))}
              </Grid>

              {/* Risk Chart */}
              <Paper sx={{ p: 3, mb: 4 }}>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Risk Distribution
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={riskData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="name" stroke="#999" />
                    <YAxis stroke="#999" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#132f4c',
                        border: '1px solid #2196f3',
                        borderRadius: 4,
                      }}
                    />
                    <Legend />
                    <Bar dataKey="count" fill="#2196f3" name="Resources" />
                  </BarChart>
                </ResponsiveContainer>
              </Paper>

              {/* Default Risks Detected */}
              <Paper sx={{ p: 3, mb: 4 }}>
                <Typography variant="h6" gutterBottom fontWeight={600}>
                  Default Risks Detected
                </Typography>
                <Grid container spacing={2}>
                  {defaultRisks.map((risk) => (
                    <Grid size={{ xs: 12 }} key={risk.id}>
                      <Card 
                        sx={{ 
                          background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
                          border: '1px solid',
                          borderColor: 'divider',
                          transition: 'all 0.2s',
                          '&:hover': {
                            borderColor: risk.severity === 'critical' ? 'error.main' : 
                                       risk.severity === 'high' ? 'warning.main' : 'info.main',
                            boxShadow: 3,
                          }
                        }}
                      >
                        <CardContent sx={{ p: 3 }}>
                          <Box display="flex" alignItems="flex-start" gap={2}>
                            <Box
                              sx={{
                                p: 1.5,
                                borderRadius: 2,
                                bgcolor: risk.severity === 'critical' ? 'error.light' :
                                        risk.severity === 'high' ? 'warning.light' :
                                        'info.light',
                                opacity: 0.35,
                              }}
                            >
                              {getSeverityIcon(risk.severity)}
                            </Box>
                            <Box flex={1}>
                              <Box display="flex" alignItems="center" gap={1} mb={1} flexWrap="wrap">
                                <Typography variant="h6" fontWeight={600}>
                                  {risk.title}
                                </Typography>
                                <Chip
                                  label={risk.severity.toUpperCase()}
                                  size="small"
                                  color={getSeverityColor(risk.severity) as 'error' | 'warning' | 'info' | 'success'}
                                  sx={{ fontWeight: 600 }}
                                />
                              </Box>
                              <Typography variant="body2" color="text.secondary" paragraph sx={{ mb: 2 }}>
                                {risk.description}
                              </Typography>
                              <Box display="flex" alignItems="center" gap={2}>
                                <Chip
                                  label={risk.affected === 0 ? 'No services affected' : `${risk.affected} service${risk.affected !== 1 ? 's' : ''} affected`}
                                  size="small"
                                  variant="outlined"
                                  color="primary"
                                />
                              </Box>
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Paper>
            </>
          )}
        </>
      )}

      {/* Prediction Analysis Tab */}
      {activeTab === 1 && <PredictionAnalysis />}

      {/* Remediation Suggestions Tab */}
      {activeTab === 2 && <RemediationSuggestions />}

      {/* Resource Testing Tab */}
      {activeTab === 3 && <ResourceTester />}

      {/* Query Assistant Tab */}
      {activeTab === 4 && <ResourceQuery />}

      {/* Risk Breakdown Tab */}
      {activeTab === 5 && <RiskBreakdown />}

      {/* Drilldown Dialog */}
      <RiskDrilldownDialog
        open={drilldownOpen}
        onClose={() => setDrilldownOpen(false)}
        riskLevel={selectedRiskLevel}
      />
    </Box>
  );
}
