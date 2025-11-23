/**
 * Health Score Gauge Widget
 * 
 * Displays overall system health score as a circular gauge.
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  Box, 
  Typography, 
  LinearProgress, 
  Card,
  CardContent,
  Grid,
  Divider,
  Stack,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import BaseWidget, { WidgetConfig } from '../BaseWidget';
import apiClient from '../../../services/api';

interface HealthScoreData {
  score: number;
  status: 'excellent' | 'good' | 'degraded' | 'critical';
  trend?: 'improving' | 'stable' | 'degrading';
  services_count: number;
  anomaly_count: number;
}

interface HealthGaugeWidgetProps {
  config: WidgetConfig;
  onRemove?: () => void;
  onConfigure?: () => void;
}

export default function HealthGaugeWidget({
  config,
  onRemove,
  onConfigure,
}: HealthGaugeWidgetProps) {
  const [healthData, setHealthData] = useState<HealthScoreData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const fetchHealthScore = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch live diagnostics snapshot
      const snapshot = await apiClient.getLiveDiagnosticsSnapshot(1);
      
      // Calculate overall health score
      const services = snapshot.services || [];
      const totalScore = services.reduce((sum, s) => sum + (s.health_score || 0), 0);
      const avgScore = services.length > 0 ? totalScore / services.length : 100;
      
      // Determine status based on score
      let status: 'excellent' | 'good' | 'degraded' | 'critical';
      if (avgScore >= 90) status = 'excellent';
      else if (avgScore >= 70) status = 'good';
      else if (avgScore >= 50) status = 'degraded';
      else status = 'critical';

      setHealthData({
        score: avgScore,
        status,
        services_count: services.length,
        anomaly_count: snapshot.anomalies?.length || 0,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health score');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealthScore();
  }, [fetchHealthScore]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return '#4caf50';
      case 'good': return '#8bc34a';
      case 'degraded': return '#ff9800';
      case 'critical': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'excellent':
      case 'good':
        return <HealthyIcon sx={{ fontSize: 48, color: getStatusColor(status) }} />;
      case 'degraded':
        return <WarningIcon sx={{ fontSize: 48, color: getStatusColor(status) }} />;
      case 'critical':
        return <ErrorIcon sx={{ fontSize: 48, color: getStatusColor(status) }} />;
      default:
        return null;
    }
  };

  return (
    <BaseWidget
      config={config}
      onRefresh={fetchHealthScore}
      onRemove={onRemove}
      onConfigure={onConfigure}
      loading={loading}
      error={error}
    >
      {healthData && (
        <Box
          sx={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Main Health Display */}
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              flex: expanded ? 0 : 1,
              transition: 'flex 0.3s',
            }}
          >
            {/* Health Icon */}
            <Box sx={{ mb: 2, position: 'relative' }}>
              {getStatusIcon(healthData.status)}
              {/* Circular progress ring */}
              <Box
                sx={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: 80,
                  height: 80,
                  borderRadius: '50%',
                  border: 4,
                  borderColor: getStatusColor(healthData.status),
                  opacity: 0.3,
                }}
              />
            </Box>

            {/* Health Score */}
            <Typography 
              variant="h2" 
              fontWeight="bold" 
              sx={{ 
                mb: 1,
                background: `linear-gradient(45deg, ${getStatusColor(healthData.status)}, ${getStatusColor(healthData.status)}CC)`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              {healthData.score.toFixed(0)}
            </Typography>
            <Typography
              variant="h6"
              color="text.secondary"
              sx={{ mb: 2, textTransform: 'uppercase', letterSpacing: 1 }}
            >
              {healthData.status}
            </Typography>

            {/* Progress Bar */}
            <Box sx={{ width: '100%', mb: 2, px: 2 }}>
              <LinearProgress
                variant="determinate"
                value={healthData.score}
                sx={{
                  height: 12,
                  borderRadius: 6,
                  bgcolor: 'rgba(0, 0, 0, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: getStatusColor(healthData.status),
                    borderRadius: 6,
                    background: `linear-gradient(90deg, ${getStatusColor(healthData.status)}, ${getStatusColor(healthData.status)}DD)`,
                  },
                }}
              />
            </Box>

            {/* Quick Stats */}
            <Grid container spacing={2} sx={{ px: 2 }}>
              <Grid item xs={6}>
                <Card sx={{ bgcolor: 'background.default' }}>
                  <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                    <Typography variant="h4" fontWeight="bold" color="primary">
                      {healthData.services_count}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Services
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card sx={{ bgcolor: 'background.default' }}>
                  <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                    <Typography
                      variant="h4"
                      fontWeight="bold"
                      color={healthData.anomaly_count > 0 ? 'error.main' : 'success.main'}
                    >
                      {healthData.anomaly_count}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Anomalies
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>

          {/* Expandable Details Section */}
          <Box sx={{ mt: 2 }}>
            <Divider sx={{ mb: 1 }} />
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
              }}
              onClick={() => setExpanded(!expanded)}
            >
              <Typography variant="caption" color="text.secondary">
                {expanded ? 'Hide' : 'Show'} Details
              </Typography>
              <IconButton
                size="small"
                sx={{
                  transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s',
                }}
              >
                <ExpandMoreIcon fontSize="small" />
              </IconButton>
            </Box>

            <Collapse in={expanded}>
              <Box sx={{ p: 2, bgcolor: 'background.default', borderRadius: 1, mt: 1 }}>
                <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                  Health Metrics Breakdown
                </Typography>
                <Stack spacing={1.5} sx={{ mt: 2 }}>
                  {/* Note: Using sample data - will be replaced with real metrics from API */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption">CPU Usage</Typography>
                      <Typography variant="caption" fontWeight="bold">
                        {Math.random() > 0.5 ? '45%' : '78%'}
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={Math.random() * 100} 
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption">Memory Usage</Typography>
                      <Typography variant="caption" fontWeight="bold">
                        {Math.random() > 0.5 ? '62%' : '89%'}
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={Math.random() * 100} 
                      color="warning"
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption">Error Rate</Typography>
                      <Typography variant="caption" fontWeight="bold">
                        {healthData.anomaly_count > 0 ? '3.2%' : '0.1%'}
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={healthData.anomaly_count > 0 ? 32 : 1} 
                      color={healthData.anomaly_count > 0 ? 'error' : 'success'}
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>
                  <Divider sx={{ my: 1 }} />
                  <Stack direction="row" spacing={1}>
                    <Box
                      sx={{
                        flex: 1,
                        p: 1,
                        bgcolor: 'success.dark',
                        borderRadius: 1,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 0.5,
                      }}
                    >
                      <TrendingUpIcon fontSize="small" />
                      <Typography variant="caption">Uptime 99.9%</Typography>
                    </Box>
                    <Box
                      sx={{
                        flex: 1,
                        p: 1,
                        bgcolor: 'primary.dark',
                        borderRadius: 1,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 0.5,
                      }}
                    >
                      <TrendingDownIcon fontSize="small" />
                      <Typography variant="caption">Latency -15%</Typography>
                    </Box>
                  </Stack>
                </Stack>
              </Box>
            </Collapse>
          </Box>
        </Box>
      )}
    </BaseWidget>
  );
}
