/**
 * Top Failing Services Widget
 * 
 * Displays a list of services with the most errors or lowest health scores.
 */

import { useState, useEffect } from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Typography,
  Box,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  CheckCircle as HealthyIcon,
} from '@mui/icons-material';
import BaseWidget, { WidgetConfig } from '../BaseWidget';
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

  const limit = config.config?.limit || 5;
  const sortBy = config.config?.sort_by || 'health_score';

  const fetchServices = async () => {
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
  };

  useEffect(() => {
    fetchServices();
  }, [limit, sortBy]);

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
            <ListItem
              key={service.resource_id}
              sx={{
                borderBottom: index < services.length - 1 ? 1 : 0,
                borderColor: 'divider',
                '&:hover': {
                  bgcolor: 'action.hover',
                },
              }}
            >
              <ListItemIcon>
                {getStatusIcon(service.health_score)}
              </ListItemIcon>
              <ListItemText
                primary={
                  <Typography variant="body1" fontWeight="medium">
                    {service.resource_name}
                  </Typography>
                }
                secondary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                    <Chip
                      label={`Health: ${service.health_score.toFixed(0)}%`}
                      size="small"
                      color={getStatusColor(service.health_score)}
                      variant="outlined"
                    />
                    {service.anomaly_count > 0 && (
                      <Chip
                        label={`${service.anomaly_count} anomalies`}
                        size="small"
                        color="error"
                        variant="outlined"
                      />
                    )}
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>
      )}
    </BaseWidget>
  );
}
