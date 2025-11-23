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
  IconButton,
  Collapse,
  Stack,
  LinearProgress,
} from '@mui/material';
import {
  KeyboardArrowDown as ExpandIcon,
  KeyboardArrowUp as CollapseIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
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
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

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

  const getLatencyColor = (latency: number) => {
    if (latency < 100) return '#4caf50';
    if (latency < 500) return '#ff9800';
    return '#f44336';
  };

  const handleRowClick = (index: number) => {
    setExpandedRow(expandedRow === index ? null : index);
  };

  const renderExpandedDetails = (pattern: TrafficPattern) => (
    <Box sx={{ p: 2, bgcolor: 'background.default' }}>
      <Typography variant="subtitle2" gutterBottom>
        Traffic Details
      </Typography>
      <Stack spacing={1}>
        <Box>
          <Typography variant="caption" color="text.secondary">
            Request Rate Trend
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={Math.min(pattern.request_rate * 10, 100)} 
            sx={{ height: 8, borderRadius: 1, mt: 0.5 }}
          />
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary">
            Error Budget
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={100 - pattern.error_rate} 
            color={pattern.error_rate < 1 ? 'success' : 'error'}
            sx={{ height: 8, borderRadius: 1, mt: 0.5 }}
          />
        </Box>
        <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
          <Chip 
            icon={pattern.error_rate < 5 ? <TrendingDownIcon /> : <TrendingUpIcon />}
            label={`Error Trend: ${pattern.error_rate < 5 ? 'Improving' : 'Degrading'}`}
            size="small"
            color={pattern.error_rate < 5 ? 'success' : 'error'}
            variant="outlined"
          />
        </Stack>
      </Stack>
    </Box>
  );

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
              <TableRow sx={{ bgcolor: 'background.default' }}>
                <TableCell sx={{ width: 40 }}></TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Source</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>Target</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                  Req/s
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                  Error Rate
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                  P95 Latency
                </TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {patterns.map((pattern, index) => (
                <>
                  <TableRow
                    key={`${pattern.source_id}-${pattern.target_id}`}
                    onClick={() => handleRowClick(index)}
                    sx={{
                      '&:hover': { bgcolor: 'action.hover', cursor: 'pointer' },
                      bgcolor: pattern.is_abnormal 
                        ? 'rgba(244, 67, 54, 0.1)' 
                        : 'transparent',
                    }}
                  >
                    <TableCell>
                      <IconButton size="small">
                        {expandedRow === index ? <CollapseIcon /> : <ExpandIcon />}
                      </IconButton>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {pattern.source_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {pattern.target_id}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={pattern.request_rate.toFixed(2)}
                        size="small"
                        sx={{ 
                          minWidth: 60,
                          bgcolor: 'primary.dark',
                          fontWeight: 'bold'
                        }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${pattern.error_rate.toFixed(2)}%`}
                        size="small"
                        sx={{ 
                          minWidth: 60,
                          bgcolor: getErrorRateColor(pattern.error_rate),
                          color: 'white',
                          fontWeight: 'bold'
                        }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${pattern.latency_p95.toFixed(0)}ms`}
                        size="small"
                        sx={{ 
                          minWidth: 70,
                          bgcolor: getLatencyColor(pattern.latency_p95),
                          color: 'white',
                          fontWeight: 'bold'
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      {pattern.is_abnormal && (
                        <Chip
                          label="Abnormal"
                          size="small"
                          color="error"
                          sx={{ fontWeight: 'bold' }}
                        />
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={7}>
                      <Collapse in={expandedRow === index} timeout="auto" unmountOnExit>
                        {renderExpandedDetails(pattern)}
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </BaseWidget>
  );
}
