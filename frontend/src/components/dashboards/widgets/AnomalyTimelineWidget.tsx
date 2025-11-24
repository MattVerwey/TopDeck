/**
 * Anomaly Timeline Widget
 * 
 * Displays recent anomalies in a timeline view.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
} from '@mui/lab';
import {
  Typography,
  Box,
  Chip,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import BaseWidget from '../BaseWidget';
import type { WidgetConfig } from '../BaseWidget';
import apiClient from '../../../services/api';

interface Anomaly {
  alert_id: string;
  resource_name: string;
  severity: string;
  metric_name: string;
  detected_at: string;
  message: string;
}

interface AnomalyTimelineWidgetProps {
  config: WidgetConfig;
  onRemove?: () => void;
  onConfigure?: () => void;
}

export default function AnomalyTimelineWidget({
  config,
  onRemove,
  onConfigure,
}: AnomalyTimelineWidgetProps) {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const hours = config.config?.hours || 24;
  const severityFilter = config.config?.severity_filter || 'all';

  const fetchAnomalies = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch anomalies from live diagnostics
      const anomalyData = await apiClient.getLiveDiagnosticsAnomalies(
        hours,
        severityFilter !== 'all' ? severityFilter : undefined,
        20 // Limit to 20 most recent
      );

      setAnomalies(anomalyData || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch anomalies');
    } finally {
      setLoading(false);
    }
  }, [hours, severityFilter]);

  useEffect(() => {
    fetchAnomalies();
  }, [fetchAnomalies]);

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'high':
        return <ErrorIcon />;
      case 'medium':
      case 'warning':
        return <WarningIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'high':
        return 'error';
      case 'medium':
      case 'warning':
        return 'warning';
      default:
        return 'info';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'just now';
  };

  return (
    <BaseWidget
      config={config}
      onRefresh={fetchAnomalies}
      onRemove={onRemove}
      onConfigure={onConfigure}
      loading={loading}
      error={error}
    >
      {anomalies.length === 0 ? (
        <Box
          sx={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography color="text.secondary">
            No anomalies detected
          </Typography>
        </Box>
      ) : (
        <Timeline position="right" sx={{ p: 0, m: 0 }}>
          {anomalies.map((anomaly, index) => (
            <TimelineItem key={anomaly.alert_id}>
              <TimelineOppositeContent sx={{ flex: 0.2, py: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {formatTime(anomaly.detected_at)}
                </Typography>
              </TimelineOppositeContent>
              <TimelineSeparator>
                <TimelineDot color={getSeverityColor(anomaly.severity)}>
                  {getSeverityIcon(anomaly.severity)}
                </TimelineDot>
                {index < anomalies.length - 1 && <TimelineConnector />}
              </TimelineSeparator>
              <TimelineContent sx={{ py: 1 }}>
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography variant="body2" fontWeight="medium">
                      {anomaly.resource_name}
                    </Typography>
                    <Chip
                      label={anomaly.severity}
                      size="small"
                      color={getSeverityColor(anomaly.severity)}
                      sx={{ height: 20 }}
                    />
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {anomaly.metric_name}: {anomaly.message}
                  </Typography>
                </Box>
              </TimelineContent>
            </TimelineItem>
          ))}
        </Timeline>
      )}
    </BaseWidget>
  );
}
