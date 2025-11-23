/**
 * Error Detail Drawer Component
 * 
 * Displays detailed error information for a selected resource
 */

import { useEffect, useState } from 'react';
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Divider,
  Card,
  CardContent,
  Chip,
  Stack,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Close, TrendingUp, TrendingDown, Remove } from '@mui/icons-material';
import type { LiveDiagnosticsSnapshot } from '../../types/diagnostics';
import apiClient from '../../services/api';

interface ErrorDetailDrawerProps {
  open: boolean;
  onClose: () => void;
  resourceId: string;
  snapshot: LiveDiagnosticsSnapshot | null;
}

export default function ErrorDetailDrawer({
  open,
  onClose,
  resourceId,
  snapshot,
}: ErrorDetailDrawerProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [healthData, setHealthData] = useState<any>(null);

  useEffect(() => {
    if (open && resourceId) {
      loadHealthData();
    }
  }, [open, resourceId]);

  const loadHealthData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getServiceHealth(resourceId);
      setHealthData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load health data');
    } finally {
      setLoading(false);
    }
  };

  // Get service from snapshot
  const service = snapshot?.services.find((s) => s.resource_id === resourceId);
  const serviceAnomalies = snapshot?.anomalies.filter((a) => a.resource_id === resourceId) || [];

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUp color="error" />;
      case 'decreasing':
        return <TrendingDown color="success" />;
      default:
        return <Remove color="action" />;
    }
  };

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{ width: 500, p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">Service Details</Typography>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {service && (
          <>
            {/* Service Info */}
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {service.resource_name}
                </Typography>
                <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                  <Chip
                    label={service.status}
                    color={
                      service.status === 'healthy'
                        ? 'success'
                        : service.status === 'degraded'
                        ? 'warning'
                        : 'error'
                    }
                  />
                  <Chip label={service.resource_type} variant="outlined" />
                  <Chip
                    label={`Health: ${service.health_score.toFixed(1)}%`}
                    color={
                      service.health_score > 70
                        ? 'success'
                        : service.health_score > 50
                        ? 'warning'
                        : 'error'
                    }
                  />
                </Stack>
                <Typography variant="caption" color="textSecondary">
                  Last Updated: {new Date(service.last_updated).toLocaleString()}
                </Typography>
              </CardContent>
            </Card>

            {/* Metrics */}
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Current Metrics
                </Typography>
                <List dense>
                  {Object.entries(service.metrics).map(([key, value]) => (
                    <ListItem key={key}>
                      <ListItemText
                        primary={key}
                        secondary={typeof value === 'number' ? value.toFixed(2) : value}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>

            {/* Anomalies */}
            {serviceAnomalies.length > 0 && (
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Detected Anomalies ({serviceAnomalies.length})
                  </Typography>
                  <List>
                    {serviceAnomalies.map((anomaly) => (
                      <ListItem key={anomaly.alert_id}>
                        <ListItemText
                          primary={
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Chip
                                size="small"
                                label={anomaly.severity}
                                color={
                                  anomaly.severity === 'critical' || anomaly.severity === 'high'
                                    ? 'error'
                                    : anomaly.severity === 'medium'
                                    ? 'warning'
                                    : 'info'
                                }
                              />
                              <Typography variant="body2">{anomaly.metric_name}</Typography>
                            </Stack>
                          }
                          secondary={
                            <Box>
                              <Typography variant="caption" display="block">
                                {anomaly.message}
                              </Typography>
                              <Typography variant="caption" color="textSecondary" display="block">
                                Deviation: {anomaly.deviation_percentage.toFixed(1)}%
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            )}

            {/* System Anomalies */}
            {service.anomalies.length > 0 && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Anomalies
                  </Typography>
                  <List dense>
                    {service.anomalies.map((anomaly, index) => (
                      <ListItem key={index}>
                        <ListItemText primary={anomaly} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </Box>
    </Drawer>
  );
}
