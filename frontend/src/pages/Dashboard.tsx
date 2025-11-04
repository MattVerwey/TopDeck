/**
 * Main dashboard page with overview metrics and topology preview
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
} from '@mui/material';
import {
  Cloud as CloudIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { useStore } from '../store/useStore';
import type { TopologyGraph } from '../types';
import apiClient from '../services/api';
import DocLink from '../components/common/DocLink';
import { mockTopologyData } from '../utils/mockTopologyData';

interface DashboardMetric {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  link: string;
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

export default function Dashboard() {
  const navigate = useNavigate();
  const { setTopology, setLoading, setError, loading } = useStore();
  const [metrics, setMetrics] = useState<DashboardMetric[]>([]);
  const [recentChanges, setRecentChanges] = useState<RecentChange[]>([]);
  const [topRisks, setTopRisks] = useState<TopRisk[]>([]);
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
      await loadRecentChanges();
      await loadTopRisks();
    } catch (err: any) {
      console.warn('API unavailable, using mock data:', err.message);
      // Fallback to mock data when API is unavailable
      setTopology(mockTopologyData);
      setUsingMockData(true);
      
      // Calculate metrics from mock data
      calculateMetrics(mockTopologyData);
      
      // Load mock recent changes and risks
      loadMockRecentChanges();
      loadMockTopRisks();
      
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
      },
      {
        label: 'High Risk',
        value: degradedCount,
        icon: <WarningIcon fontSize="large" />,
        color: '#ff9800',
        link: '/risk',
      },
      {
        label: 'SPOFs',
        value: spofCount,
        icon: <ErrorIcon fontSize="large" />,
        color: '#f44336',
        link: '/risk',
      },
      {
        label: 'Healthy',
        value: healthyPercent,
        icon: <CheckIcon fontSize="large" />,
        color: '#4caf50',
        link: '/topology',
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
    setTopRisks([
      {
        id: 'sql-db-1',
        resource: 'SQL-Primary',
        riskScore: 85,
        reason: 'Single Point of Failure',
      },
      {
        id: 'app-gateway-1',
        resource: 'AppGateway-Prod',
        riskScore: 78,
        reason: 'Critical path component',
      },
      {
        id: 'aks-cluster-1',
        resource: 'AKS-Prod-Cluster',
        riskScore: 72,
        reason: '8 dependent services',
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

  const getSeverityColor = (severity: string) => {
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
    if (score >= 80) return '#f44336';
    if (score >= 60) return '#ff9800';
    return '#4caf50';
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
            Dashboard Overview
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
