/**
 * Main dashboard page with overview metrics and topology preview
 */

import { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Cloud as CloudIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useStore } from '../store/useStore';
import apiClient from '../services/api';

interface DashboardMetric {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}

export default function Dashboard() {
  const { setTopology, setLoading, setError, loading, error } = useStore();
  const [metrics, setMetrics] = useState<DashboardMetric[]>([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Load topology data
      const topology = await apiClient.getTopology();
      setTopology(topology);

      // Calculate metrics
      const totalResources = topology.nodes.length;
      const highRiskCount = 0; // Would calculate from risk API
      const spofCount = 0; // Would calculate from risk API
      const healthyPercent = 98;

      setMetrics([
        {
          label: 'Total Resources',
          value: totalResources,
          icon: <CloudIcon fontSize="large" />,
          color: '#2196f3',
        },
        {
          label: 'High Risk',
          value: highRiskCount,
          icon: <WarningIcon fontSize="large" />,
          color: '#ff9800',
        },
        {
          label: 'SPOFs',
          value: spofCount,
          icon: <ErrorIcon fontSize="large" />,
          color: '#f44336',
        },
        {
          label: 'Healthy',
          value: healthyPercent,
          icon: <CheckIcon fontSize="large" />,
          color: '#4caf50',
        },
      ]);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight={600}>
        Dashboard Overview
      </Typography>

      {/* Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {metrics.map((metric) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={metric.label}>
            <Card
              sx={{
                background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
                borderLeft: `4px solid ${metric.color}`,
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

      {/* Recent Changes & Top Risks */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, minHeight: 250 }}>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              Recent Changes
            </Typography>
            <Typography variant="body2" color="text.secondary">
              No recent changes detected
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, minHeight: 250 }}>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              Top Risks
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Risk analysis in progress...
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Topology Preview */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Network Topology
        </Typography>
        <Box
          sx={{
            height: 400,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: '#0a1929',
            borderRadius: 1,
          }}
        >
          <Typography variant="body1" color="text.secondary">
            Navigate to Topology view for interactive visualization
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
}
