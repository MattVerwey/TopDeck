/**
 * Custom Metric Chart Widget
 * 
 * Displays a custom metric in a chart (line, area, or bar).
 */

import { useState, useEffect } from 'react';
import { Box, Typography } from '@mui/material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import BaseWidget, { WidgetConfig } from '../BaseWidget';
import apiClient from '../../../services/api';

interface MetricDataPoint {
  timestamp: string;
  value: number;
}

interface CustomMetricWidgetProps {
  config: WidgetConfig;
  onRemove?: () => void;
  onConfigure?: () => void;
}

export default function CustomMetricWidget({
  config,
  onRemove,
  onConfigure,
}: CustomMetricWidgetProps) {
  const [data, setData] = useState<MetricDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const metric = config.config?.metric || 'latency_p95';
  const chartType = config.config?.chart_type || 'line';
  const resourceId = config.config?.resource_id;

  const fetchMetricData = async () => {
    try {
      setLoading(true);
      setError(null);

      // In a real implementation, this would fetch historical metric data
      // For now, we'll generate sample data
      const now = Date.now();
      const sampleData: MetricDataPoint[] = [];
      
      for (let i = 23; i >= 0; i--) {
        const timestamp = new Date(now - i * 3600000).toISOString();
        const value = Math.random() * 100 + 50; // Random value between 50-150
        sampleData.push({ timestamp, value });
      }

      setData(sampleData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metric data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetricData();
  }, [metric, resourceId]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const renderChart = () => {
    const chartData = data.map(d => ({
      time: formatTime(d.timestamp),
      value: d.value,
    }));

    const commonProps = {
      data: chartData,
      margin: { top: 10, right: 30, left: 0, bottom: 0 },
    };

    switch (chartType) {
      case 'area':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="value" stroke="#8884d8" fill="#8884d8" />
            </AreaChart>
          </ResponsiveContainer>
        );
      
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        );
      
      default: // 'line'
        return (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <BaseWidget
      config={config}
      onRefresh={fetchMetricData}
      onRemove={onRemove}
      onConfigure={onConfigure}
      loading={loading}
      error={error}
    >
      {data.length === 0 ? (
        <Box
          sx={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography color="text.secondary">
            No data available
          </Typography>
        </Box>
      ) : (
        <Box sx={{ height: '100%', width: '100%' }}>
          {renderChart()}
        </Box>
      )}
    </BaseWidget>
  );
}
