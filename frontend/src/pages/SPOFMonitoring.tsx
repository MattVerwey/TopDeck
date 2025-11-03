/**
 * SPOF (Single Point of Failure) Monitoring Page
 */

import { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import apiClient from '../services/api';
import ErrorDisplay from '../components/common/ErrorDisplay';
import type { SPOF, SPOFChange, SPOFStatistics } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`spof-tabpanel-${index}`}
      aria-labelledby={`spof-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function SPOFMonitoring() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statistics, setStatistics] = useState<SPOFStatistics | null>(null);
  const [currentSPOFs, setCurrentSPOFs] = useState<SPOF[]>([]);
  const [history, setHistory] = useState<SPOFChange[]>([]);
  const [tabValue, setTabValue] = useState(0);
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [stats, spofs, changes] = await Promise.all([
        apiClient.getSPOFStatistics(),
        apiClient.getCurrentSPOFs(),
        apiClient.getSPOFHistory(50),
      ]);
      setStatistics(stats);
      setCurrentSPOFs(spofs);
      setHistory(changes);
    } catch (err: any) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    try {
      await apiClient.triggerSPOFScan();
      // Wait a bit for the scan to complete, then reload
      setTimeout(() => {
        loadData();
      }, 2000);
    } catch (err: any) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setScanning(false);
    }
  };

  const getRiskColor = (riskScore: number) => {
    if (riskScore >= 80) return 'error';
    if (riskScore >= 60) return 'warning';
    return 'info';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading && !statistics) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={loadData} title="Failed to load SPOF monitoring data" />;
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight={600}>
            SPOF Monitoring
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Single Point of Failure Detection and Tracking
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadData}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={scanning ? <CircularProgress size={20} /> : <ScheduleIcon />}
            onClick={handleScan}
            disabled={scanning}
          >
            {scanning ? 'Scanning...' : 'Scan Now'}
          </Button>
        </Box>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
              borderLeft: '4px solid #f44336',
            }}
          >
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h3" fontWeight={700}>
                    {statistics?.total_spofs ?? 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total SPOFs
                  </Typography>
                </Box>
                <Box sx={{ color: '#f44336' }}>
                  <ErrorIcon fontSize="large" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
              borderLeft: '4px solid #ff9800',
            }}
          >
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h3" fontWeight={700}>
                    {statistics?.high_risk_spofs ?? 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    High Risk
                  </Typography>
                </Box>
                <Box sx={{ color: '#ff9800' }}>
                  <WarningIcon fontSize="large" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
              borderLeft: '4px solid #4caf50',
            }}
          >
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h3" fontWeight={700}>
                    {statistics?.recent_changes?.resolved ?? 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Resolved
                  </Typography>
                </Box>
                <Box sx={{ color: '#4caf50' }}>
                  <TrendingDownIcon fontSize="large" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
              borderLeft: '4px solid #2196f3',
            }}
          >
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h3" fontWeight={700}>
                    {statistics?.recent_changes?.new ?? 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    New (Recent)
                  </Typography>
                </Box>
                <Box sx={{ color: '#2196f3' }}>
                  <TrendingUpIcon fontSize="large" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Last Scan Info */}
      {statistics?.last_scan && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Last scan: {formatDate(statistics.last_scan)}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label={`Current SPOFs (${currentSPOFs.length})`} />
          <Tab label={`Change History (${history.length})`} />
          <Tab label="By Resource Type" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        {currentSPOFs.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <CheckIcon sx={{ fontSize: 64, color: '#4caf50', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No Single Points of Failure Detected
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Your infrastructure has proper redundancy configured.
            </Typography>
          </Paper>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Resource</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell align="center">Risk Score</TableCell>
                  <TableCell align="center">Dependents</TableCell>
                  <TableCell align="center">Blast Radius</TableCell>
                  <TableCell>Recommendations</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {currentSPOFs.map((spof) => (
                  <TableRow key={spof.resource_id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>
                        {spof.resource_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {spof.resource_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={spof.resource_type} size="small" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={spof.risk_score.toFixed(1)}
                        color={getRiskColor(spof.risk_score)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">{spof.dependents_count}</TableCell>
                    <TableCell align="center">{spof.blast_radius}</TableCell>
                    <TableCell>
                      <Box>
                        {spof.recommendations.slice(0, 2).map((rec, idx) => (
                          <Typography key={idx} variant="caption" display="block" color="text.secondary">
                            • {rec}
                          </Typography>
                        ))}
                        {spof.recommendations.length > 2 && (
                          <Tooltip title={spof.recommendations.slice(2).join('\n')}>
                            <Typography variant="caption" color="primary" sx={{ cursor: 'pointer' }}>
                              +{spof.recommendations.length - 2} more
                            </Typography>
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Change Type</TableCell>
                <TableCell>Resource</TableCell>
                <TableCell>Type</TableCell>
                <TableCell align="center">Risk Score</TableCell>
                <TableCell align="center">Blast Radius</TableCell>
                <TableCell>Detected At</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {history.map((change, idx) => (
                <TableRow key={idx} hover>
                  <TableCell>
                    <Chip
                      label={change.change_type}
                      color={change.change_type === 'new' ? 'error' : 'success'}
                      size="small"
                      icon={change.change_type === 'new' ? <TrendingUpIcon /> : <TrendingDownIcon />}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight={600}>
                      {change.resource_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {change.resource_id}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip label={change.resource_type} size="small" />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={change.risk_score.toFixed(1)}
                      color={getRiskColor(change.risk_score)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">{change.blast_radius}</TableCell>
                  <TableCell>{formatDate(change.detected_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          {Object.entries(statistics?.by_resource_type ?? {}).map(([type, count]) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={type}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  {type}
                </Typography>
                <Typography variant="h3" fontWeight={700} color="error.main">
                  {count}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  SPOFs detected
                </Typography>
              </Paper>
            </Grid>
          ))}
          {Object.keys(statistics?.by_resource_type ?? {}).length === 0 && (
            <Grid size={{ xs: 12 }}>
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <Typography variant="body1" color="text.secondary">
                  No SPOFs detected by resource type
                </Typography>
              </Paper>
            </Grid>
          )}
        </Grid>
      </TabPanel>
    </Box>
  );
}
