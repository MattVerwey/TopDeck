/**
 * Error Detail Drawer Component
 * 
 * Displays detailed error information for a selected resource,
 * including recent error logs from Loki.
 */

import { useEffect, useState, useCallback } from 'react';
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import { Close, ExpandMore, Error as ErrorIcon } from '@mui/icons-material';
import type { LiveDiagnosticsSnapshot } from '../../types/diagnostics';

interface ErrorDetailDrawerProps {
  open: boolean;
  onClose: () => void;
  resourceId: string;
  snapshot: LiveDiagnosticsSnapshot | null;
}

interface ErrorLog {
  timestamp: string;
  message: string;
  level: string;
  labels: Record<string, string>;
}

export default function ErrorDetailDrawer({
  open,
  onClose,
  resourceId,
  snapshot,
}: ErrorDetailDrawerProps) {
  const [errorLogs, setErrorLogs] = useState<ErrorLog[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [logsError, setLogsError] = useState<string | null>(null);

  // Get service from snapshot
  const service = snapshot?.services.find((s) => s.resource_id === resourceId);
  const serviceAnomalies = snapshot?.anomalies.filter((a) => a.resource_id === resourceId) || [];

  // Fetch error logs when drawer opens
  useEffect(() => {
    if (open && resourceId) {
      fetchErrorLogs();
    }
  }, [open, resourceId]);

  const fetchErrorLogs = useCallback(async () => {
    setLoadingLogs(true);
    setLogsError(null);
    
    try {
      const response = await fetch(
        `/api/v1/live-diagnostics/services/${resourceId}/error-logs?limit=10&duration_hours=1`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to fetch error logs: ${response.statusText}`);
      }
      
      const data = await response.json();
      setErrorLogs(data.error_logs || []);
    } catch (error) {
      console.error('Error fetching logs:', error);
      setLogsError(error instanceof Error ? error.message : 'Failed to fetch error logs');
      setErrorLogs([]);
    } finally {
      setLoadingLogs(false);
    }
  }, [resourceId]);

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{ width: 550, p: 3, maxHeight: '100vh', overflowY: 'auto' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">Service Details</Typography>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>

        <Divider sx={{ mb: 2 }} />

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

            {/* Recent Error Logs */}
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <ErrorIcon sx={{ mr: 1, color: 'error.main' }} />
                  <Typography variant="h6">
                    Recent Error Logs (Last 10)
                  </Typography>
                </Box>
                
                {loadingLogs && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                    <CircularProgress size={24} />
                  </Box>
                )}
                
                {logsError && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    {logsError}
                  </Alert>
                )}
                
                {!loadingLogs && !logsError && errorLogs.length === 0 && (
                  <Alert severity="info">
                    No error logs found in the last hour
                  </Alert>
                )}
                
                {!loadingLogs && errorLogs.length > 0 && (
                  <List dense>
                    {errorLogs.map((log, index) => (
                      <Accordion key={index} sx={{ mb: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                          <Stack direction="row" spacing={1} alignItems="center" sx={{ width: '100%' }}>
                            <Chip
                              size="small"
                              label={log.level.toUpperCase()}
                              color="error"
                              sx={{ minWidth: 60 }}
                            />
                            <Typography variant="caption" color="textSecondary">
                              {new Date(log.timestamp).toLocaleString()}
                            </Typography>
                          </Stack>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Typography
                            variant="body2"
                            sx={{
                              fontFamily: 'monospace',
                              fontSize: '0.75rem',
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word',
                              p: 1,
                              backgroundColor: 'rgba(0, 0, 0, 0.05)',
                              borderRadius: 1,
                            }}
                          >
                            {log.message}
                          </Typography>
                          {Object.keys(log.labels).length > 0 && (
                            <Box sx={{ mt: 1 }}>
                              <Typography variant="caption" color="textSecondary">
                                Labels:
                              </Typography>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                                {Object.entries(log.labels).map(([key, value]) => (
                                  <Chip
                                    key={key}
                                    size="small"
                                    label={`${key}: ${value}`}
                                    variant="outlined"
                                  />
                                ))}
                              </Box>
                            </Box>
                          )}
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </List>
                )}
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
