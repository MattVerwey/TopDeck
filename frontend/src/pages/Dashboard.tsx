/**
 * Main dashboard page with overview metrics and topology preview
 * Enhanced to show comprehensive risk overview and analytics
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Tooltip,
} from '@mui/material';
import {
  Cloud as CloudIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Security as SecurityIcon,
  ShowChart as ShowChartIcon,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip } from 'recharts';
import { useStore } from '../store/useStore';
import type { TopologyGraph, RiskAssessment } from '../types';
import apiClient from '../services/api';
import DocLink from '../components/common/DocLink';
import { mockTopologyData } from '../utils/mockTopologyData';

interface DashboardMetric {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  link: string;
  description?: string;
}

interface RecentChange {
  id: string;
  title: string;
  type: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high';
}

interface TopRisk {
  id: string;
  resource: string;
  riskScore: number;
  reason: string;
}

type SPOFResource = {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  dependents_count: number;
  blast_radius: number;
  risk_score: number;
  recommendations: string[];
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { setTopology, setLoading, setError, loading } = useStore();
  const [metrics, setMetrics] = useState<DashboardMetric[]>([]);
  const [recentChanges, setRecentChanges] = useState<RecentChange[]>([]);
  const [topRisks, setTopRisks] = useState<TopRisk[]>([]);
  const [spofResources, setSpofResources] = useState<SPOFResource[]>([]);
  const [allRisks, setAllRisks] = useState<RiskAssessment[]>([]);
  const [riskDistribution, setRiskDistribution] = useState<{ name: string; value: number; color: string }[]>([]);
  const [usingMockData, setUsingMockData] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Try to load topology data from API
      const topology = await apiClient.getTopology();
      setTopology(topology);
      setUsingMockData(false);

      // Calculate metrics from API data
      calculateMetrics(topology);
      
      // Load other dashboard data
      await Promise.all([
        loadRecentChanges(),
        loadTopRisks(),
        loadSPOFResources(),
      ]);
    } catch (err: unknown) {
      const error = err as { message?: string };
      console.warn('API unavailable, using mock data:', error.message || 'Unknown error');
      // Fallback to mock data when API is unavailable
      setTopology(mockTopologyData);
      setUsingMockData(true);
      
      // Calculate metrics from mock data
      calculateMetrics(mockTopologyData);
      
      // Load mock recent changes and risks
      loadMockRecentChanges();
      loadMockTopRisks();
      loadMockSPOFResources();
      
      setError(null); // Clear error since we have fallback data
    } finally {
      setLoading(false);
    }
  };

  const calculateMetrics = (topology: TopologyGraph) => {
    const totalResources = topology.nodes.length;
    
    // Calculate degraded/unhealthy resources
    const degradedCount = topology.nodes.filter(
      (node) => node.properties?.health_status === 'degraded' || node.properties?.health_status === 'unhealthy'
    ).length;
    
    // Calculate SPOFs (resources with high importance and many connections)
    const spofCount = topology.nodes.filter(
      (node) => (node.metadata?.importance as number || 0) >= 3
    ).length;
    
    // Calculate healthy percentage
    const healthyPercent = totalResources > 0 
      ? Math.round(((totalResources - degradedCount) / totalResources) * 100)
      : 100;

    setMetrics([
      {
        label: 'Total Resources',
        value: totalResources,
        icon: <CloudIcon fontSize="large" />,
        color: '#2196f3',
        link: '/topology',
        description: 'Total discovered resources',
      },
      {
        label: 'High Risk',
        value: degradedCount,
        icon: <WarningIcon fontSize="large" />,
        color: '#ff9800',
        link: '/risk',
        description: 'Resources with high risk score',
      },
      {
        label: 'SPOFs',
        value: spofCount,
        icon: <ErrorIcon fontSize="large" />,
        color: '#f44336',
        link: '/risk',
        description: 'Single Points of Failure',
      },
      {
        label: 'Healthy',
        value: healthyPercent,
        icon: <CheckIcon fontSize="large" />,
        color: '#4caf50',
        link: '/topology',
        description: 'Percentage of healthy resources',
      },
    ]);
  };

  const loadRecentChanges = async () => {
    try {
      const changes = await apiClient.getChangeCalendar();
      const recent = changes.slice(0, 5).map(change => ({
        id: change.id,
        title: change.title,
        type: change.change_type,
        timestamp: change.scheduled_start,
        severity: change.risk_level as 'low' | 'medium' | 'high',
      }));
      setRecentChanges(recent);
    } catch {
      // If API fails, keep empty or use mock data
      loadMockRecentChanges();
    }
  };

  const loadTopRisks = async () => {
    try {
      const risks = await apiClient.getAllRisks();
      setAllRisks(risks);
      
      // Calculate risk distribution
      const critical = risks.filter(r => r.risk_score >= 80).length;
      const high = risks.filter(r => r.risk_score >= 60 && r.risk_score < 80).length;
      const medium = risks.filter(r => r.risk_score >= 40 && r.risk_score < 60).length;
      const low = risks.filter(r => r.risk_score < 40).length;
      
      setRiskDistribution([
        { name: 'Critical', value: critical, color: '#f44336' },
        { name: 'High', value: high, color: '#ff9800' },
        { name: 'Medium', value: medium, color: '#ffc107' },
        { name: 'Low', value: low, color: '#4caf50' },
      ]);
      
      const topRisks = risks
        .sort((a, b) => b.risk_score - a.risk_score)
        .slice(0, 5)
        .map(risk => ({
          id: risk.resource_id,
          resource: risk.resource_name || risk.resource_id,
          riskScore: risk.risk_score,
          reason: risk.single_point_of_failure ? 'Single Point of Failure' : `${risk.dependencies_count} dependencies`,
        }));
      setTopRisks(topRisks);
    } catch {
      // If API fails, use mock data
      loadMockTopRisks();
    }
  };

  const loadSPOFResources = async () => {
    try {
      const spofs = await apiClient.getSinglePointsOfFailure();
      setSpofResources(spofs);
    } catch {
      // If API fails, use mock data
      loadMockSPOFResources();
    }
  };

  const loadMockRecentChanges = () => {
    setRecentChanges([
      {
        id: '1',
        title: 'AKS Cluster Scale Up',
        type: 'scale',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        severity: 'low',
      },
      {
        id: '2',
        title: 'API Service Deployment',
        type: 'deployment',
        timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        severity: 'medium',
      },
      {
        id: '3',
        title: 'Database Maintenance',
        type: 'maintenance',
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        severity: 'high',
      },
    ]);
  };

  const loadMockTopRisks = () => {
    const mockRisks = [
      {
        resource_id: 'sql-db-1',
        resource_name: 'SQL-Primary',
        resource_type: 'database',
        risk_score: 85,
        single_point_of_failure: true,
        dependencies_count: 5,
        dependents_count: 12,
        blast_radius: 15,
      },
      {
        resource_id: 'app-gateway-1',
        resource_name: 'AppGateway-Prod',
        resource_type: 'network',
        risk_score: 78,
        single_point_of_failure: false,
        dependencies_count: 12,
        dependents_count: 8,
        blast_radius: 10,
      },
      {
        resource_id: 'aks-cluster-1',
        resource_name: 'AKS-Prod-Cluster',
        resource_type: 'kubernetes',
        risk_score: 72,
        single_point_of_failure: false,
        dependencies_count: 8,
        dependents_count: 15,
        blast_radius: 20,
      },
      {
        resource_id: 'redis-cache-1',
        resource_name: 'Redis-Cache',
        resource_type: 'cache',
        risk_score: 65,
        single_point_of_failure: true,
        dependencies_count: 3,
        dependents_count: 18,
        blast_radius: 22,
      },
      {
        resource_id: 'api-service-1',
        resource_name: 'API-Service-Main',
        resource_type: 'service',
        risk_score: 58,
        single_point_of_failure: false,
        dependencies_count: 10,
        dependents_count: 5,
        blast_radius: 8,
      },
    ] as RiskAssessment[];
    
    // Set allRisks for the table
    setAllRisks(mockRisks);
    
    setTopRisks(mockRisks.slice(0, 3).map(r => ({
      id: r.resource_id,
      resource: r.resource_name || r.resource_id,
      riskScore: r.risk_score,
      reason: r.single_point_of_failure ? 'Single Point of Failure' : `${r.dependencies_count} dependencies`,
    })));
    
    setRiskDistribution([
      { name: 'Critical', value: 3, color: '#f44336' },
      { name: 'High', value: 5, color: '#ff9800' },
      { name: 'Medium', value: 8, color: '#ffc107' },
      { name: 'Low', value: 12, color: '#4caf50' },
    ]);
  };

  const loadMockSPOFResources = () => {
    setSpofResources([
      {
        resource_id: 'sql-db-1',
        resource_name: 'SQL-Primary',
        resource_type: 'database',
        dependents_count: 12,
        blast_radius: 15,
        risk_score: 85,
        recommendations: ['Set up read replicas', 'Configure automatic failover', 'Implement circuit breaker pattern'],
      },
      {
        resource_id: 'app-gateway-1',
        resource_name: 'AppGateway-Prod',
        resource_type: 'network',
        dependents_count: 8,
        blast_radius: 10,
        risk_score: 78,
        recommendations: ['Deploy multiple instances', 'Configure geo-redundancy'],
      },
    ]);
  };

  const handleMetricClick = (link: string) => {
    navigate(link);
  };

  const handleRiskClick = (resourceId: string) => {
    navigate(`/risk?resource=${resourceId}`);
  };

  const handleChangeClick = (changeId: string) => {
    navigate(`/impact?change=${changeId}`);
  };

  const getSeverityColor = (severity: 'low' | 'medium' | 'high'): 'error' | 'warning' | 'success' => {
    switch (severity) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      default:
        return 'success';
    }
  };

  const getRiskColor = (score: number) => {
    if (score >= 80) return '#f44336'; // Critical - red
    if (score >= 60) return '#ff9800'; // High - orange
    if (score >= 40) return '#ffc107'; // Medium - yellow
    return '#4caf50'; // Low - green
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box>
          <Typography variant="h4" fontWeight={600}>
            Risk Dashboard & Overview
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Real-time infrastructure risk analysis and monitoring
          </Typography>
          {usingMockData && (
            <Chip 
              label="Demo Mode" 
              size="small" 
              color="info" 
              sx={{ mt: 1 }}
            />
          )}
        </Box>
        <DocLink href="README.md" text="Getting Started" />
      </Box>

      {/* Metrics Cards - Now Clickable */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {metrics.map((metric) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={metric.label}>
            <Tooltip title={metric.description || metric.label}>
              <Card
                onClick={() => handleMetricClick(metric.link)}
                sx={{
                  background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
                  borderLeft: `4px solid ${metric.color}`,
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: `0 8px 16px rgba(0,0,0,0.3)`,
                  },
                }}
              >
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography variant="h3" fontWeight={700}>
                        {metric.label === 'Healthy' ? `${metric.value}%` : metric.value}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {metric.label}
                      </Typography>
                    </Box>
                    <Box sx={{ color: metric.color }}>{metric.icon}</Box>
                  </Box>
                </CardContent>
              </Card>
            </Tooltip>
          </Grid>
        ))}
      </Grid>

      {/* Recent Changes & Top Risks - Now with Data */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, minHeight: 250 }}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <TrendingUpIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Recent Changes
              </Typography>
            </Box>
            {recentChanges.length > 0 ? (
              <List sx={{ py: 0 }}>
                {recentChanges.map((change) => (
                  <ListItem
                    key={change.id}
                    onClick={() => handleChangeClick(change.id)}
                    sx={{
                      cursor: 'pointer',
                      borderRadius: 1,
                      mb: 1,
                      '&:hover': {
                        bgcolor: 'rgba(33, 150, 243, 0.08)',
                      },
                    }}
                  >
                    <ListItemText
                      primary={
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="body1">{change.title}</Typography>
                          <Chip
                            label={change.type}
                            size="small"
                            color={getSeverityColor(change.severity)}
                            sx={{ ml: 1 }}
                          />
                        </Box>
                      }
                      secondary={formatTimestamp(change.timestamp)}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No recent changes detected
              </Typography>
            )}
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, minHeight: 250 }}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <AssessmentIcon color="warning" />
              <Typography variant="h6" fontWeight={600}>
                Top Risks
              </Typography>
            </Box>
            {topRisks.length > 0 ? (
              <List sx={{ py: 0 }}>
                {topRisks.map((risk) => (
                  <ListItem
                    key={risk.id}
                    onClick={() => handleRiskClick(risk.id)}
                    sx={{
                      cursor: 'pointer',
                      borderRadius: 1,
                      mb: 1,
                      '&:hover': {
                        bgcolor: 'rgba(255, 152, 0, 0.08)',
                      },
                    }}
                  >
                    <ListItemText
                      primary={
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="body1">{risk.resource}</Typography>
                          <Typography
                            variant="h6"
                            fontWeight={700}
                            sx={{ color: getRiskColor(risk.riskScore) }}
                          >
                            {risk.riskScore}
                          </Typography>
                        </Box>
                      }
                      secondary={risk.reason}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Risk analysis in progress...
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Risk Distribution and SPOF Analysis */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, minHeight: 350 }}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <ShowChartIcon color="warning" />
              <Typography variant="h6" fontWeight={600}>
                Risk Distribution
              </Typography>
            </Box>
            {riskDistribution.length > 0 ? (
              <Box>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={riskDistribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {riskDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
                <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
                  Total: {riskDistribution.reduce((sum, item) => sum + item.value, 0)} resources analyzed
                </Typography>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Loading risk distribution...
              </Typography>
            )}
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, minHeight: 350 }}>
            <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
              <Box display="flex" alignItems="center" gap={1}>
                <SecurityIcon color="error" />
                <Typography variant="h6" fontWeight={600}>
                  Single Points of Failure
                </Typography>
              </Box>
              <Chip 
                label={`${spofResources.length} Critical`}
                color="error"
                size="small"
              />
            </Box>
            {spofResources.length > 0 ? (
              <List sx={{ py: 0, maxHeight: 280, overflow: 'auto' }}>
                {spofResources.slice(0, 3).map((spof) => (
                  <ListItem
                    key={spof.resource_id}
                    onClick={() => handleRiskClick(spof.resource_id)}
                    sx={{
                      cursor: 'pointer',
                      borderRadius: 1,
                      mb: 1,
                      bgcolor: 'rgba(244, 67, 54, 0.05)',
                      '&:hover': {
                        bgcolor: 'rgba(244, 67, 54, 0.12)',
                      },
                    }}
                  >
                    <ListItemText
                      primary={
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="body1" fontWeight={600}>
                            {spof.resource_name}
                          </Typography>
                          <Chip
                            label={spof.resource_type}
                            size="small"
                            sx={{ ml: 1 }}
                          />
                        </Box>
                      }
                      secondary={
                        <Box sx={{ mt: 0.5 }}>
                          <Typography variant="body2" color="text.secondary">
                            {spof.dependents_count} dependents • Blast radius: {spof.blast_radius}
                          </Typography>
                          <Typography variant="caption" color="error.main">
                            Risk Score: {spof.risk_score}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No single points of failure detected
              </Typography>
            )}
            {spofResources.length > 3 && (
              <Button
                fullWidth
                onClick={() => navigate('/risk')}
                sx={{ mt: 2 }}
              >
                View All SPOFs ({spofResources.length})
              </Button>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Most Risky Resources Table */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <AssessmentIcon color="warning" />
            <Typography variant="h6" fontWeight={600}>
              Most Risky Resources
            </Typography>
          </Box>
          <Button
            variant="outlined"
            size="small"
            onClick={() => navigate('/risk')}
          >
            View All
          </Button>
        </Box>
        {allRisks.length > 0 ? (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Resource</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell align="center">Risk Score</TableCell>
                  <TableCell align="center">Dependencies</TableCell>
                  <TableCell align="center">Dependents</TableCell>
                  <TableCell align="center">Blast Radius</TableCell>
                  <TableCell align="center">SPOF</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {allRisks
                  .sort((a, b) => b.risk_score - a.risk_score)
                  .slice(0, 10)
                  .map((risk) => (
                    <TableRow
                      key={risk.resource_id}
                      onClick={() => handleRiskClick(risk.resource_id)}
                      sx={{
                        cursor: 'pointer',
                        '&:hover': {
                          bgcolor: 'rgba(255, 152, 0, 0.08)',
                        },
                      }}
                    >
                      <TableCell>
                        <Tooltip title={risk.resource_id}>
                          <Typography variant="body2" fontWeight={600}>
                            {risk.resource_name || risk.resource_id}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Chip label={risk.resource_type || 'N/A'} size="small" />
                      </TableCell>
                      <TableCell align="center">
                        <Typography
                          variant="body2"
                          fontWeight={700}
                          sx={{ color: getRiskColor(risk.risk_score) }}
                        >
                          {(risk.risk_score || 0).toFixed(0)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">{risk.dependencies_count}</TableCell>
                      <TableCell align="center">{risk.dependents_count}</TableCell>
                      <TableCell align="center">{risk.blast_radius}</TableCell>
                      <TableCell align="center">
                        {risk.single_point_of_failure && (
                          <ErrorIcon color="error" fontSize="small" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Typography variant="body2" color="text.secondary">
            Loading risk data...
          </Typography>
        )}
      </Paper>

      {/* Topology Preview - Clickable */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Network Topology
        </Typography>
        <Box
          onClick={() => navigate('/topology')}
          sx={{
            height: 400,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: '#0a1929',
            borderRadius: 1,
            cursor: 'pointer',
            transition: 'background-color 0.2s',
            '&:hover': {
              bgcolor: '#0d2136',
            },
          }}
        >
          <CloudIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
          <Typography variant="body1" color="text.secondary" align="center">
            Click to view interactive topology visualization
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
            {metrics[0]?.value || 0} resources discovered
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
}
