/**
 * Custom Metric Chart Widget
 * 
 * Displays a custom metric in a chart (line, area, or bar).
 */

import { useState, useEffect, useCallback } from 'react';
import { Box, Typography, Chip, Stack } from '@mui/material';
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
  Legend,
  ResponsiveContainer,
} from 'recharts';
import BaseWidget from '../BaseWidget';
import type { WidgetConfig } from '../BaseWidget';

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

  const fetchMetricData = useCallback(async () => {
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
  }, [metric, resourceId]);

  useEffect(() => {
    fetchMetricData();
  }, [fetchMetricData]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  // Format value based on metric type
  const formatValue = (value: number) => {
    if (metric.includes('latency') || metric.includes('p95') || metric.includes('p99')) {
      return `${value.toFixed(2)}ms`;
    }
    if (metric.includes('cpu') || metric.includes('memory') || metric.includes('error_rate')) {
      return `${value.toFixed(1)}%`;
    }
    if (metric.includes('request_rate')) {
      return `${value.toFixed(2)} req/s`;
    }
    return value.toFixed(2);
  };

  // Get metric display name
  const getMetricLabel = () => {
    const labels: Record<string, string> = {
      'latency_p95': 'P95 Latency (ms)',
      'latency_p99': 'P99 Latency (ms)',
      'latency_p50': 'P50 Latency (ms)',
      'cpu_usage': 'CPU Usage (%)',
      'memory_usage': 'Memory Usage (%)',
      'request_rate': 'Request Rate (req/s)',
      'error_rate': 'Error Rate (%)',
    };
    return labels[metric] || metric;
  };

  // Custom tooltip with Grafana-style formatting
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <Box
          sx={{
            bgcolor: 'background.paper',
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            p: 1.5,
            boxShadow: 2,
          }}
        >
          <Typography variant="caption" color="text.secondary" display="block">
            {payload[0].payload.time}
          </Typography>
          <Typography variant="body2" fontWeight="medium" color="primary" sx={{ mt: 0.5 }}>
            {getMetricLabel()}: {formatValue(payload[0].value)}
          </Typography>
        </Box>
      );
    }
    return null;
  };

  // Calculate statistics for display
  const stats = data.length > 0 ? {
    current: data[data.length - 1].value,
    min: Math.min(...data.map(d => d.value)),
    max: Math.max(...data.map(d => d.value)),
    avg: data.reduce((sum, d) => sum + d.value, 0) / data.length,
  } : null;

  const renderChart = () => {
    const chartData = data.map(d => ({
      time: formatTime(d.timestamp),
      [getMetricLabel()]: d.value,
    }));

    const commonProps = {
      data: chartData,
      margin: { top: 5, right: 10, left: 0, bottom: 5 },
    };

    // Grafana-inspired color palette
    const colors = {
      primary: '#33b5e5',
      success: '#00e396',
      warning: '#feb019',
      error: '#ff4560',
    };

    const getColor = () => {
      if (metric.includes('error')) return colors.error;
      if (metric.includes('latency')) return colors.warning;
      if (metric.includes('cpu') || metric.includes('memory')) return colors.primary;
      return colors.success;
    };

    const chartColor = getColor();

    switch (chartType) {
      case 'area':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart {...commonProps}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={chartColor} stopOpacity={0.8}/>
                  <stop offset="95%" stopColor={chartColor} stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="time" 
                tick={{ fontSize: 11 }}
                stroke="rgba(255,255,255,0.5)"
              />
              <YAxis 
                tick={{ fontSize: 11 }}
                stroke="rgba(255,255,255,0.5)"
                tickFormatter={formatValue}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend 
                wrapperStyle={{ fontSize: '12px' }}
                iconType="line"
              />
              <Area 
                type="monotone" 
                dataKey={getMetricLabel()} 
                stroke={chartColor} 
                fill="url(#colorValue)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        );
      
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="time" 
                tick={{ fontSize: 11 }}
                stroke="rgba(255,255,255,0.5)"
              />
              <YAxis 
                tick={{ fontSize: 11 }}
                stroke="rgba(255,255,255,0.5)"
                tickFormatter={formatValue}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend 
                wrapperStyle={{ fontSize: '12px' }}
                iconType="rect"
              />
              <Bar 
                dataKey={getMetricLabel()} 
                fill={chartColor}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        );
      
      default: // 'line'
        return (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="time" 
                tick={{ fontSize: 11 }}
                stroke="rgba(255,255,255,0.5)"
              />
              <YAxis 
                tick={{ fontSize: 11 }}
                stroke="rgba(255,255,255,0.5)"
                tickFormatter={formatValue}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend 
                wrapperStyle={{ fontSize: '12px' }}
                iconType="line"
              />
              <Line 
                type="monotone" 
                dataKey={getMetricLabel()} 
                stroke={chartColor} 
                strokeWidth={2}
                dot={{ r: 2 }}
                activeDot={{ r: 4 }}
              />
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
        <Box sx={{ height: '100%', width: '100%', display: 'flex', flexDirection: 'column' }}>
          {/* Stats Summary - Grafana style */}
          {stats && (
            <Stack 
              direction="row" 
              spacing={1} 
              sx={{ 
                mb: 1, 
                pb: 1, 
                borderBottom: 1, 
                borderColor: 'divider' 
              }}
            >
              <Chip 
                label={`Current: ${formatValue(stats.current)}`}
                size="small"
                sx={{ bgcolor: 'primary.dark', fontSize: '0.75rem' }}
              />
              <Chip 
                label={`Avg: ${formatValue(stats.avg)}`}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.75rem' }}
              />
              <Chip 
                label={`Min: ${formatValue(stats.min)}`}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.75rem' }}
              />
              <Chip 
                label={`Max: ${formatValue(stats.max)}`}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.75rem' }}
              />
            </Stack>
          )}
          <Box sx={{ flex: 1, minHeight: 0 }}>
            {renderChart()}
          </Box>
        </Box>
      )}
    </BaseWidget>
  );
}
