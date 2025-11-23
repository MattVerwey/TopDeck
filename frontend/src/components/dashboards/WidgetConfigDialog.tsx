/**
 * Widget Configuration Dialog Component
 * 
 * Provides a configuration UI for customizing individual dashboard widgets.
 */

import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Slider,
} from '@mui/material';
import type { WidgetConfig } from './BaseWidget';

interface WidgetConfigDialogProps {
  open: boolean;
  widget: WidgetConfig;
  onClose: () => void;
  onSave: (config: Record<string, any>) => void;
}

export default function WidgetConfigDialog({
  open,
  widget,
  onClose,
  onSave,
}: WidgetConfigDialogProps) {
  const [config, setConfig] = useState(widget.config);

  const handleSave = () => {
    onSave(config);
    onClose();
  };

  const renderConfigFields = () => {
    switch (widget.type) {
      case 'top_failing_services':
        return (
          <>
            <Box sx={{ mb: 3 }}>
              <Typography id="limit-slider" gutterBottom>
                Number of Services
              </Typography>
              <Slider
                value={config.limit || 5}
                onChange={(_, value) => setConfig({ ...config, limit: value })}
                aria-labelledby="limit-slider"
                valueLabelDisplay="auto"
                step={1}
                marks
                min={3}
                max={15}
              />
            </Box>
          </>
        );

      case 'anomaly_timeline':
        return (
          <>
            <TextField
              label="Time Window (hours)"
              type="number"
              fullWidth
              value={config.hours || 24}
              onChange={(e) => setConfig({ ...config, hours: parseInt(e.target.value) })}
              InputProps={{ inputProps: { min: 1, max: 168 } }}
              sx={{ mb: 2 }}
            />
          </>
        );

      case 'custom_metric':
        return (
          <>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Metric</InputLabel>
              <Select
                value={config.metric || 'latency_p95'}
                label="Metric"
                onChange={(e) => setConfig({ ...config, metric: e.target.value })}
              >
                <MenuItem value="latency_p95">Latency (P95)</MenuItem>
                <MenuItem value="latency_p99">Latency (P99)</MenuItem>
                <MenuItem value="error_rate">Error Rate</MenuItem>
                <MenuItem value="request_rate">Request Rate</MenuItem>
                <MenuItem value="cpu_usage">CPU Usage</MenuItem>
                <MenuItem value="memory_usage">Memory Usage</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Chart Type</InputLabel>
              <Select
                value={config.chart_type || 'line'}
                label="Chart Type"
                onChange={(e) => setConfig({ ...config, chart_type: e.target.value })}
              >
                <MenuItem value="line">Line</MenuItem>
                <MenuItem value="area">Area</MenuItem>
                <MenuItem value="bar">Bar</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Time Range (hours)"
              type="number"
              fullWidth
              value={config.time_range || 24}
              onChange={(e) => setConfig({ ...config, time_range: parseInt(e.target.value) })}
              InputProps={{ inputProps: { min: 1, max: 168 } }}
            />
          </>
        );

      case 'traffic_heatmap':
        return (
          <>
            <FormControl fullWidth>
              <InputLabel>Show Errors</InputLabel>
              <Select
                value={config.show_errors !== false ? 'yes' : 'no'}
                label="Show Errors"
                onChange={(e) => setConfig({ ...config, show_errors: e.target.value === 'yes' })}
              >
                <MenuItem value="yes">Yes</MenuItem>
                <MenuItem value="no">No</MenuItem>
              </Select>
            </FormControl>
          </>
        );

      default:
        return (
          <Typography color="text.secondary">
            No configuration options available for this widget type.
          </Typography>
        );
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Configure {widget.title}</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          {renderConfigFields()}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSave}>
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}
