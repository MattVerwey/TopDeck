/**
 * Traffic Heatmap Widget
 * 
 * Displays service-to-service traffic patterns in a heatmap view.
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import BaseWidget, { WidgetConfig } from '../BaseWidget';
import apiClient from '../../../services/api';

interface TrafficPattern {
  source_id: string;
  target_id: string;
  request_rate: number;
  error_rate: number;
  latency_p95: number;
  is_abnormal: boolean;
}

interface TrafficHeatmapWidgetProps {
  config: WidgetConfig;
  onRemove?: () => void;
  onConfigure?: () => void;
}

export default function TrafficHeatmapWidget({
  config,
  onRemove,
  onConfigure,
}: TrafficHeatmapWidgetProps) {
  const [patterns, setPatterns] = useState<TrafficPattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const showErrors = config.config?.show_errors !== false;

  const fetchTrafficPatterns = async () => {
    try {
      setLoading(true);
      setError(null);

      const patternsData = await apiClient.getLiveDiagnosticsTrafficPatterns(1, showErrors);
      setPatterns(patternsData?.slice(0, 10) || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch traffic patterns');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrafficPatterns();
  }, [showErrors]);

  const getErrorRateColor = (errorRate: number) => {
    if (errorRate < 1) return '#4caf50';
    if (errorRate < 5) return '#ff9800';
    return '#f44336';
  };

  return (
    <BaseWidget
      config={config}
      onRefresh={fetchTrafficPatterns}
      onRemove={onRemove}
      onConfigure={onConfigure}
      loading={loading}
      error={error}
    >
      {patterns.length === 0 ? (
        <Box
          sx={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography color="text.secondary">
            No traffic patterns found
          </Typography>
        </Box>
      ) : (
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Source</TableCell>
                <TableCell>Target</TableCell>
                <TableCell align="right">Req/s</TableCell>
                <TableCell align="right">Error %</TableCell>
                <TableCell align="right">P95 (ms)</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {patterns.map((pattern, index) => (
                <TableRow
                  key={`${pattern.source_id}-${pattern.target_id}`}
                  sx={{
                    '&:hover': { bgcolor: 'action.hover' },
                    bgcolor: pattern.is_abnormal ? 'error.light' : 'transparent',
                  }}
                >
                  <TableCell>{pattern.source_id}</TableCell>
                  <TableCell>{pattern.target_id}</TableCell>
                  <TableCell align="right">
                    {pattern.request_rate.toFixed(2)}
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ color: getErrorRateColor(pattern.error_rate) }}
                  >
                    {pattern.error_rate.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right">
                    {pattern.latency_p95.toFixed(0)}
                  </TableCell>
                  <TableCell>
                    {pattern.is_abnormal && (
                      <Chip
                        label="Abnormal"
                        size="small"
                        color="error"
                        variant="outlined"
                      />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </BaseWidget>
  );
}
