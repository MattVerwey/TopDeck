/**
 * Dashboard Builder Component
 * 
 * Allows users to create and customize dashboards with drag-and-drop widgets.
 * Enhanced with react-grid-layout for true drag-and-drop positioning.
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
  Typography,
  Fab,
  Menu,
  MenuItem,
  Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Save as SaveIcon,
  ViewModule as ViewModuleIcon,
} from '@mui/icons-material';
import { Responsive, WidthProvider, Layout } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { WidgetConfig } from './BaseWidget';
import {
  HealthGaugeWidget,
  TopFailingServicesWidget,
  AnomalyTimelineWidget,
  TrafficHeatmapWidget,
  CustomMetricWidget,
} from './widgets';
import WidgetConfigDialog from './WidgetConfigDialog';
import apiClient from '../../services/api';

const ResponsiveGridLayout = WidthProvider(Responsive);

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
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState<WidgetConfig | null>(null);
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
      const loadedDashboard = await apiClient.getDashboard(id);
      setDashboard(loadedDashboard);
      setSnackbar({
        open: true,
        message: 'Dashboard loaded successfully',
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

  const handleConfigureWidget = (widget: WidgetConfig) => {
    setSelectedWidget(widget);
    setConfigDialogOpen(true);
  };

  const handleSaveWidgetConfig = (widgetId: string, newConfig: Record<string, any>) => {
    setDashboard({
      ...dashboard,
      widgets: dashboard.widgets.map(w =>
        w.id === widgetId ? { ...w, config: newConfig } : w
      ),
    });
    setConfigDialogOpen(false);
    setSelectedWidget(null);
  };

  const handleLayoutChange = (layout: Layout[]) => {
    // Update widget positions based on layout changes
    const updatedWidgets = dashboard.widgets.map(widget => {
      const layoutItem = layout.find(l => l.i === widget.id);
      if (layoutItem) {
        return {
          ...widget,
          position: {
            x: layoutItem.x,
            y: layoutItem.y,
            width: layoutItem.w,
            height: layoutItem.h,
          },
        };
      }
      return widget;
    });

    setDashboard({
      ...dashboard,
      widgets: updatedWidgets,
    });
  };

  const handleSaveDashboard = async () => {
    try {
      setLoading(true);
      
      // Call API to save dashboard
      if (dashboard.id) {
        await apiClient.updateDashboard(dashboard.id, dashboard);
      } else {
        await apiClient.createDashboard(dashboard);
      }
      
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
      onConfigure: () => handleConfigureWidget(widget),
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

      {/* Dashboard Grid with Drag-and-Drop */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {dashboard.widgets.length > 0 ? (
          <ResponsiveGridLayout
            className="layout"
            layouts={{ lg: dashboard.widgets.map(w => ({
              i: w.id,
              x: w.position.x,
              y: w.position.y,
              w: w.position.width,
              h: w.position.height,
              minW: 2,
              minH: 1,
            })) }}
            breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
            cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
            rowHeight={dashboard.layout_config.rowHeight || 80}
            margin={dashboard.layout_config.margin || [10, 10]}
            onLayoutChange={handleLayoutChange}
            isDraggable={!loading}
            isResizable={!loading}
            draggableHandle=".drag-handle"
          >
            {dashboard.widgets.map((widget) => (
              <div
                key={widget.id}
                style={{ height: '100%' }}
              >
                {renderWidget(widget)}
              </div>
            ))}
          </ResponsiveGridLayout>
        ) : (
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
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        message={snackbar.message}
        sx={{
          '& .MuiSnackbarContent-root': {
            backgroundColor: snackbar.severity === 'success' ? 'success.main' : 'error.main',
          },
        }}
      />

      {/* Widget Configuration Dialog */}
      {selectedWidget && (
        <WidgetConfigDialog
          open={configDialogOpen}
          widget={selectedWidget}
          onClose={() => {
            setConfigDialogOpen(false);
            setSelectedWidget(null);
          }}
          onSave={(config) => handleSaveWidgetConfig(selectedWidget.id, config)}
        />
      )}
    </Box>
  );
}
