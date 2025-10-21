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

interface RiskMetric {
  name: string;
  count: number;
  color: string;
}

// Memoized components for better performance
const MemoizedRiskCard = memo(({ metric, nodeCount }: { metric: RiskMetric; nodeCount: number }) => (
  <Card
    sx={{
      background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
      borderLeft: `4px solid ${metric.color}`,
    }}
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

  useEffect(() => {
    loadRiskData();
  }, [topology]);

  const loadRiskData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Create mock topology if not available
      if (!topology) {
        const mockTopology = {
          nodes: [
            { id: '1', name: 'API Gateway', resource_type: 'gateway', cloud_provider: 'azure' as const, properties: {}, metadata: {} },
            { id: '2', name: 'Database Primary', resource_type: 'database', cloud_provider: 'azure' as const, properties: {}, metadata: {} },
            { id: '3', name: 'Cache Service', resource_type: 'cache', cloud_provider: 'aws' as const, properties: {}, metadata: {} },
            { id: '4', name: 'Auth Service', resource_type: 'service', cloud_provider: 'azure' as const, properties: {}, metadata: {} },
            { id: '5', name: 'Storage Account', resource_type: 'storage', cloud_provider: 'gcp' as const, properties: {}, metadata: {} },
          ],
          edges: [],
          metadata: { total_nodes: 5, total_edges: 0 },
        };
        useStore.getState().setTopology(mockTopology);
      }

      const nodeCount = topology?.nodes.length || 5;
      
      // Simulate risk calculation based on topology
      const riskMetrics: RiskMetric[] = [
        { name: 'Critical', count: 3, color: '#f44336' },
        { name: 'High', count: 12, color: '#ff9800' },
        { name: 'Medium', count: 25, color: '#ff9800' },
        { name: 'Low', count: Math.max(nodeCount - 40, 10), color: '#4caf50' },
      ];

      setRiskData(riskMetrics);

      // Default risks detected
      const defaultRisksData = [
        {
          id: 1,
          title: 'Single Point of Failure Detected',
          description: 'Database instance has no redundancy',
          severity: 'critical',
          affected: 15,
        },
        {
          id: 2,
          title: 'High Dependency Count',
          description: 'API Gateway has 25+ dependent services',
          severity: 'high',
          affected: 25,
        },
        {
          id: 3,
          title: 'No Backup Configuration',
          description: 'Storage account missing backup policy',
          severity: 'medium',
          affected: 5,
        },
      ];

      setDefaultRisks(defaultRisksData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load risk data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
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
      <Typography variant="h4" gutterBottom fontWeight={600}>
        Risk Analysis
      </Typography>

      {/* Tabs for different sections */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant="fullWidth"
        >
          <Tab label="Overview" />
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
                    <MemoizedRiskCard metric={metric} nodeCount={nodeCount} />
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
                      <Card sx={{ background: '#132f4c' }}>
                        <CardContent>
                          <Box display="flex" alignItems="flex-start" gap={2}>
                            {getSeverityIcon(risk.severity)}
                            <Box flex={1}>
                              <Box display="flex" alignItems="center" gap={1} mb={1}>
                                <Typography variant="h6">{risk.title}</Typography>
                                <Chip
                                  label={risk.severity.toUpperCase()}
                                  size="small"
                                  color={getSeverityColor(risk.severity) as 'error' | 'warning' | 'info' | 'success'}
                                />
                              </Box>
                              <Typography variant="body2" color="text.secondary" paragraph>
                                {risk.description}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {risk.affected} services affected
                              </Typography>
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

      {/* Remediation Suggestions Tab */}
      {activeTab === 1 && <RemediationSuggestions />}

      {/* Resource Testing Tab */}
      {activeTab === 2 && <ResourceTester />}

      {/* Query Assistant Tab */}
      {activeTab === 3 && <ResourceQuery />}

      {/* Risk Breakdown Tab */}
      {activeTab === 4 && <RiskBreakdown />}
    </Box>
  );
}
