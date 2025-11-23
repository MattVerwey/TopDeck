/**
 * Dashboard Builder Component
 * 
 * Allows users to create and customize dashboards with drag-and-drop widgets.
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Typography,
  Fab,
  Menu,
  MenuItem,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Save as SaveIcon,
  ViewModule as ViewModuleIcon,
} from '@mui/icons-material';
import { WidgetConfig } from './BaseWidget';
import {
  HealthGaugeWidget,
  TopFailingServicesWidget,
  AnomalyTimelineWidget,
  TrafficHeatmapWidget,
  CustomMetricWidget,
} from './widgets';

interface Dashboard {
  id?: string;
  name: string;
  description?: string;
  widgets: WidgetConfig[];
  layout_config: Record<string, any>;
}

interface DashboardBuilderProps {
  dashboardId?: string;
  onSave?: (dashboard: Dashboard) => void;
}

const WIDGET_TYPES = [
  {
    type: 'health_gauge',
    name: 'Health Score Gauge',
    description: 'Display overall system health',
    defaultConfig: {},
    defaultSize: { width: 4, height: 2 },
  },
  {
    type: 'top_failing_services',
    name: 'Top Failing Services',
    description: 'Show services with most errors',
    defaultConfig: { limit: 5 },
    defaultSize: { width: 4, height: 2 },
  },
  {
    type: 'anomaly_timeline',
    name: 'Anomaly Timeline',
    description: 'Recent anomalies timeline',
    defaultConfig: { hours: 24 },
    defaultSize: { width: 4, height: 2 },
  },
  {
    type: 'traffic_heatmap',
    name: 'Traffic Heatmap',
    description: 'Service traffic patterns',
    defaultConfig: { show_errors: true },
    defaultSize: { width: 12, height: 3 },
  },
  {
    type: 'custom_metric',
    name: 'Custom Metric Chart',
    description: 'Display custom metrics',
    defaultConfig: { metric: 'latency_p95', chart_type: 'line' },
    defaultSize: { width: 6, height: 2 },
  },
];

export default function DashboardBuilder({
  dashboardId,
  onSave,
}: DashboardBuilderProps) {
  const [dashboard, setDashboard] = useState<Dashboard>({
    name: 'New Dashboard',
    widgets: [],
    layout_config: { cols: 12, rowHeight: 80, margin: [10, 10] },
  });
  const [widgetMenuAnchor, setWidgetMenuAnchor] = useState<null | HTMLElement>(null);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  useEffect(() => {
    if (dashboardId) {
      loadDashboard(dashboardId);
    }
  }, [dashboardId]);

  const loadDashboard = async (id: string) => {
    try {
      setLoading(true);
      // const loadedDashboard = await apiClient.getDashboard(id);
      // setDashboard(loadedDashboard);
      // For now, just show a placeholder
      setSnackbar({
        open: true,
        message: 'Dashboard loaded (placeholder)',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to load dashboard',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAddWidget = (widgetType: typeof WIDGET_TYPES[0]) => {
    // Simple positioning: place widgets in a grid
    const newY = dashboard.widgets.length > 0
      ? Math.max(...dashboard.widgets.map(w => w.position.y + w.position.height))
      : 0;

    const newWidget: WidgetConfig = {
      id: `widget-${Date.now()}`,
      type: widgetType.type,
      title: widgetType.name,
      position: {
        x: 0,
        y: newY,
        width: widgetType.defaultSize.width,
        height: widgetType.defaultSize.height,
      },
      config: widgetType.defaultConfig,
      refresh_interval: 30,
    };

    setDashboard({
      ...dashboard,
      widgets: [...dashboard.widgets, newWidget],
    });

    setWidgetMenuAnchor(null);
  };

  const handleRemoveWidget = (widgetId: string) => {
    setDashboard({
      ...dashboard,
      widgets: dashboard.widgets.filter(w => w.id !== widgetId),
    });
  };

  const handleSaveDashboard = async () => {
    try {
      setLoading(true);
      
      // Call API to save dashboard
      // For now, just simulate a save
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSnackbar({
        open: true,
        message: `Dashboard "${dashboard.name}" saved successfully`,
        severity: 'success',
      });
      
      setSaveDialogOpen(false);
      
      if (onSave) {
        onSave(dashboard);
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to save dashboard',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const renderWidget = (widget: WidgetConfig) => {
    const commonProps = {
      config: widget,
      onRemove: () => handleRemoveWidget(widget.id),
    };

    switch (widget.type) {
      case 'health_gauge':
        return <HealthGaugeWidget {...commonProps} />;
      case 'top_failing_services':
        return <TopFailingServicesWidget {...commonProps} />;
      case 'anomaly_timeline':
        return <AnomalyTimelineWidget {...commonProps} />;
      case 'traffic_heatmap':
        return <TrafficHeatmapWidget {...commonProps} />;
      case 'custom_metric':
        return <CustomMetricWidget {...commonProps} />;
      default:
        return null;
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Typography variant="h5" fontWeight="medium">
          {dashboard.name}
        </Typography>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={() => setSaveDialogOpen(true)}
          disabled={loading}
        >
          Save Dashboard
        </Button>
      </Box>

      {/* Dashboard Grid */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <Grid container spacing={2}>
          {dashboard.widgets.map((widget) => (
            <Grid
              key={widget.id}
              item
              xs={12}
              md={widget.position.width}
              sx={{ height: `${widget.position.height * 100}px` }}
            >
              {renderWidget(widget)}
            </Grid>
          ))}
        </Grid>

        {dashboard.widgets.length === 0 && (
          <Box
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 2,
            }}
          >
            <ViewModuleIcon sx={{ fontSize: 64, color: 'text.disabled' }} />
            <Typography variant="h6" color="text.secondary">
              No widgets added yet
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Click the + button to add your first widget
            </Typography>
          </Box>
        )}
      </Box>

      {/* Add Widget Button */}
      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 24, right: 24 }}
        onClick={(e) => setWidgetMenuAnchor(e.currentTarget)}
      >
        <AddIcon />
      </Fab>

      {/* Widget Menu */}
      <Menu
        anchorEl={widgetMenuAnchor}
        open={Boolean(widgetMenuAnchor)}
        onClose={() => setWidgetMenuAnchor(null)}
      >
        {WIDGET_TYPES.map((widgetType) => (
          <MenuItem
            key={widgetType.type}
            onClick={() => handleAddWidget(widgetType)}
          >
            <Box>
              <Typography variant="body1">{widgetType.name}</Typography>
              <Typography variant="caption" color="text.secondary">
                {widgetType.description}
              </Typography>
            </Box>
          </MenuItem>
        ))}
      </Menu>

      {/* Save Dialog */}
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)}>
        <DialogTitle>Save Dashboard</DialogTitle>
        <DialogContent>
          <TextField
            label="Dashboard Name"
            fullWidth
            value={dashboard.name}
            onChange={(e) => setDashboard({ ...dashboard, name: e.target.value })}
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            label="Description (optional)"
            fullWidth
            multiline
            rows={3}
            value={dashboard.description || ''}
            onChange={(e) => setDashboard({ ...dashboard, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSaveDashboard}
            disabled={!dashboard.name || loading}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
