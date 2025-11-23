/**
 * Traffic Pattern Chart Component
 * 
 * Visualizes traffic patterns between services
 */

import { Box, Paper, Typography } from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { TrafficPattern } from '../../types/diagnostics';

interface TrafficPatternChartProps {
  patterns: TrafficPattern[];
  onPatternClick: (pattern: TrafficPattern) => void;
}

export default function TrafficPatternChart({
  patterns,
  onPatternClick,
}: TrafficPatternChartProps) {
  if (patterns.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Typography variant="body1" color="textSecondary">
          No traffic patterns available
        </Typography>
      </Box>
    );
  }

  // Transform data for chart
  const chartData = patterns.map((pattern) => ({
    name: `${pattern.source_id} → ${pattern.target_id}`,
    'Request Rate': pattern.request_rate,
    'Error Rate %': pattern.error_rate * 100,
    'Latency (ms)': pattern.latency_p95 * 1000,
    is_abnormal: pattern.is_abnormal,
    pattern,
  }));

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Traffic Patterns
      </Typography>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          onClick={(data: any) => {
            if (
              data &&
              data.activePayload &&
              Array.isArray(data.activePayload) &&
              data.activePayload.length > 0 &&
              data.activePayload[0]?.payload?.pattern
            ) {
              onPatternClick(data.activePayload[0].payload.pattern);
            }
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          <Tooltip />
          <Legend />
          <Bar yAxisId="left" dataKey="Request Rate" fill="#8884d8">
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.is_abnormal ? '#f44336' : '#8884d8'} />
            ))}
          </Bar>
          <Bar yAxisId="right" dataKey="Error Rate %" fill="#ff7300" />
          <Bar yAxisId="right" dataKey="Latency (ms)" fill="#ffc658" />
        </BarChart>
      </ResponsiveContainer>
    </Paper>
  );
}
