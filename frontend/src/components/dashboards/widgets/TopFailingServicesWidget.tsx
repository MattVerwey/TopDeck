/**
 * Top Failing Services Widget
 * 
 * Displays a list of services with the most errors or lowest health scores.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Typography,
  Box,
  Collapse,
  IconButton,
  Stack,
  LinearProgress,
  Divider,
  Grid,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  CheckCircle as HealthyIcon,
  ExpandMore as ExpandMoreIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
} from '@mui/icons-material';
import BaseWidget from '../BaseWidget';
import type { WidgetConfig } from '../BaseWidget';
import apiClient from '../../../services/api';

interface ServiceHealth {
  resource_id: string;
  resource_name: string;
  health_score: number;
  status: string;
  anomaly_count: number;
}

interface TopFailingServicesWidgetProps {
  config: WidgetConfig;
  onRemove?: () => void;
  onConfigure?: () => void;
}

export default function TopFailingServicesWidget({
  config,
  onRemove,
  onConfigure,
}: TopFailingServicesWidgetProps) {
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedService, setExpandedService] = useState<string | null>(null);

  const limit = config.config?.limit || 5;
  const sortBy = config.config?.sort_by || 'health_score';

  const fetchServices = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch live diagnostics snapshot
      const snapshot = await apiClient.getLiveDiagnosticsSnapshot(1);
      
      // Map services to health data
      const servicesData: ServiceHealth[] = (snapshot.services || []).map(s => ({
        resource_id: s.resource_id,
        resource_name: s.resource_name,
        health_score: s.health_score || 0,
        status: s.status,
        anomaly_count: s.anomalies?.length || 0,
      }));

      // Sort based on config
      let sorted = [...servicesData];
      if (sortBy === 'health_score') {
        sorted.sort((a, b) => a.health_score - b.health_score); // Lowest first
      } else if (sortBy === 'error_count') {
        sorted.sort((a, b) => b.anomaly_count - a.anomaly_count); // Highest first
      }

      // Take top N
      setServices(sorted.slice(0, limit));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch services');
    } finally {
      setLoading(false);
    }
  }, [limit, sortBy]);

  useEffect(() => {
    fetchServices();
  }, [fetchServices]);

  const getStatusIcon = (healthScore: number) => {
    if (healthScore >= 70) {
      return <HealthyIcon sx={{ color: '#4caf50' }} />;
    } else if (healthScore >= 50) {
      return <WarningIcon sx={{ color: '#ff9800' }} />;
    } else {
      return <ErrorIcon sx={{ color: '#f44336' }} />;
    }
  };

  const getStatusColor = (healthScore: number): 'success' | 'warning' | 'error' => {
    if (healthScore >= 70) return 'success';
    else if (healthScore >= 50) return 'warning';
    else return 'error';
  };

  const handleServiceClick = (serviceId: string) => {
    setExpandedService(expandedService === serviceId ? null : serviceId);
  };

  const renderServiceDetails = (service: ServiceHealth) => (
    <Box sx={{ p: 2, bgcolor: 'background.default' }}>
      <Stack spacing={2}>
        <Box>
          <Typography variant="caption" color="text.secondary" gutterBottom>
            Health Score Breakdown
          </Typography>
          <LinearProgress
            variant="determinate"
            value={service.health_score}
            color={getStatusColor(service.health_score)}
            sx={{ height: 8, borderRadius: 4, mt: 1 }}
          />
          <Typography variant="caption" sx={{ mt: 0.5, display: 'block' }}>
            {service.health_score.toFixed(1)}% - {service.status}
          </Typography>
        </Box>
        <Divider />
        {/* Note: Using sample data - will be replaced with real metrics from API */}
        <Grid container spacing={1}>
          <Grid size={{ xs: 6 }}>
            <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
              <SpeedIcon color="primary" sx={{ fontSize: 20 }} />
              <Typography variant="caption" display="block" color="text.secondary">
                Response Time
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {Math.floor(Math.random() * 500) + 50}ms
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 6 }}>
            <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
              <MemoryIcon color="warning" sx={{ fontSize: 20 }} />
              <Typography variant="caption" display="block" color="text.secondary">
                Memory
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {Math.floor(Math.random() * 40) + 60}%
              </Typography>
            </Box>
          </Grid>
        </Grid>
        {service.anomaly_count > 0 && (
          <Box sx={{ bgcolor: 'error.dark', p: 1, borderRadius: 1 }}>
            <Typography variant="caption" fontWeight="bold">
              ⚠️ {service.anomaly_count} Active Anomalies
            </Typography>
          </Box>
        )}
      </Stack>
    </Box>
  );

  return (
    <BaseWidget
      config={config}
      onRefresh={fetchServices}
      onRemove={onRemove}
      onConfigure={onConfigure}
      loading={loading}
      error={error}
    >
      {services.length === 0 ? (
        <Box
          sx={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography color="text.secondary">
            No services found
          </Typography>
        </Box>
      ) : (
        <List sx={{ p: 0 }}>
          {services.map((service, index) => (
            <Box key={service.resource_id}>
              <ListItem
                sx={{
                  borderBottom: index < services.length - 1 ? 1 : 0,
                  borderColor: 'divider',
                  '&:hover': {
                    bgcolor: 'action.hover',
                  },
                  cursor: 'pointer',
                  flexDirection: 'column',
                  alignItems: 'stretch',
                }}
                onClick={() => handleServiceClick(service.resource_id)}
              >
                <Box sx={{ display: 'flex', width: '100%', alignItems: 'center' }}>
                  <ListItemIcon>
                    {getStatusIcon(service.health_score)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1" fontWeight="medium">
                          {service.resource_name}
                        </Typography>
                        <Chip
                          label={`${service.health_score.toFixed(0)}%`}
                          size="small"
                          color={getStatusColor(service.health_score)}
                          sx={{ fontWeight: 'bold', minWidth: 50 }}
                        />
                      </Box>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        {service.anomaly_count > 0 && (
                          <Chip
                            label={`${service.anomaly_count} anomalies`}
                            size="small"
                            color="error"
                            variant="outlined"
                          />
                        )}
                        <Typography variant="caption" color="text.secondary">
                          Status: {service.status}
                        </Typography>
                      </Box>
                    }
                  />
                  <IconButton
                    size="small"
                    sx={{
                      transform: expandedService === service.resource_id ? 'rotate(180deg)' : 'rotate(0deg)',
                      transition: 'transform 0.3s',
                    }}
                  >
                    <ExpandMoreIcon />
                  </IconButton>
                </Box>
                <Collapse in={expandedService === service.resource_id} timeout="auto" unmountOnExit>
                  {renderServiceDetails(service)}
                </Collapse>
              </ListItem>
            </Box>
          ))}
        </List>
      )}
    </BaseWidget>
  );
}
