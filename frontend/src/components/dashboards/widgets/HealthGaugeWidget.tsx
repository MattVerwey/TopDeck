/**
 * Health Score Gauge Widget
 * 
 * Displays overall system health score as a circular gauge.
 */

import { useState, useEffect } from 'react';
import { Box, Typography, LinearProgress } from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
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

  const fetchHealthScore = async () => {
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
  };

  useEffect(() => {
    fetchHealthScore();
  }, []);

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
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {/* Health Icon */}
          <Box sx={{ mb: 2 }}>
            {getStatusIcon(healthData.status)}
          </Box>

          {/* Health Score */}
          <Typography variant="h3" fontWeight="bold" sx={{ mb: 1 }}>
            {healthData.score.toFixed(1)}
          </Typography>
          <Typography
            variant="h6"
            color="text.secondary"
            sx={{ mb: 3, textTransform: 'capitalize' }}
          >
            {healthData.status}
          </Typography>

          {/* Progress Bar */}
          <Box sx={{ width: '100%', mb: 3 }}>
            <LinearProgress
              variant="determinate"
              value={healthData.score}
              sx={{
                height: 10,
                borderRadius: 5,
                bgcolor: 'rgba(0, 0, 0, 0.1)',
                '& .MuiLinearProgress-bar': {
                  bgcolor: getStatusColor(healthData.status),
                  borderRadius: 5,
                },
              }}
            />
          </Box>

          {/* Stats */}
          <Box
            sx={{
              display: 'flex',
              gap: 4,
              justifyContent: 'center',
              width: '100%',
            }}
          >
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h5" fontWeight="bold">
                {healthData.services_count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Services
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography
                variant="h5"
                fontWeight="bold"
                color={healthData.anomaly_count > 0 ? 'error.main' : 'text.primary'}
              >
                {healthData.anomaly_count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Anomalies
              </Typography>
            </Box>
          </Box>
        </Box>
      )}
    </BaseWidget>
  );
}
