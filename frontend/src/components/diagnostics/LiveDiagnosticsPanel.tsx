/**
 * Live Diagnostics Panel Component
 * 
 * Real-time diagnostics panel with ML-based anomaly detection and service health monitoring.
 * Displays topology with visual highlighting of failed/degraded services.
 * 
 * Now supports WebSocket for real-time updates with automatic fallback to polling.
 */

import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  Stack,
  LinearProgress,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  Refresh,
  Timeline,
  NetworkCheck,
  BugReport,
  Info,
  Wifi,
  WifiOff,
  CloudQueue,
} from '@mui/icons-material';
import type {
  LiveDiagnosticsSnapshot,
} from '../../types/diagnostics';
import LiveTopologyGraph from './LiveTopologyGraph';
import AnomalyList from './AnomalyList';
import TrafficPatternChart from './TrafficPatternChart';
import ErrorDetailDrawer from './ErrorDetailDrawer';
import { useLiveDiagnosticsWebSocket } from '../../hooks/useLiveDiagnosticsWebSocket';

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
      id={`diagnostics-tabpanel-${index}`}
      aria-labelledby={`diagnostics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function LiveDiagnosticsPanel() {
  const [tabValue, setTabValue] = useState(0);
  const [selectedResource, setSelectedResource] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Use WebSocket hook for real-time updates
  const {
    snapshot,
    connectionStatus,
    error,
    requestSnapshot,
  } = useLiveDiagnosticsWebSocket({
    updateInterval: 10, // 10 seconds for WebSocket
    autoReconnect: true,
    maxReconnectAttempts: 5,
    reconnectDelay: 3000,
    fallbackToPolling: true,
    pollingInterval: 30000, // 30 seconds for polling fallback
  });

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleResourceClick = (resourceId: string) => {
    setSelectedResource(resourceId);
    setDrawerOpen(true);
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle color="success" />;
      case 'degraded':
        return <Warning color="warning" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      default:
        return <Info />;
    }
  };

  const getConnectionIcon = () => {
    switch (connectionStatus.connectionType) {
      case 'websocket':
        return <Wifi color="success" />;
      case 'polling':
        return <CloudQueue color="warning" />;
      default:
        return <WifiOff color="error" />;
    }
  };

  const getConnectionLabel = () => {
    switch (connectionStatus.connectionType) {
      case 'websocket':
        return 'WebSocket (Real-time)';
      case 'polling':
        return 'Polling (Fallback)';
      default:
        return 'Disconnected';
    }
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Live Diagnostics
        </Typography>
        <Stack direction="row" spacing={2}>
          <Chip
            icon={getStatusIcon(snapshot?.overall_health || 'unknown')}
            label={`System: ${snapshot?.overall_health || 'Loading...'}`}
            color={getStatusColor(snapshot?.overall_health || 'unknown') as any}
          />
          <Tooltip title={`Connection: ${getConnectionLabel()}`}>
            <Chip
              icon={getConnectionIcon()}
              label={getConnectionLabel()}
              color={
                connectionStatus.connectionType === 'websocket'
                  ? 'success'
                  : connectionStatus.connectionType === 'polling'
                  ? 'warning'
                  : 'default'
              }
              size="small"
            />
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<Refresh />}
            onClick={requestSnapshot}
            disabled={!connectionStatus.connected}
          >
            Refresh
          </Button>
        </Stack>
      </Box>

      {!connectionStatus.connected && !snapshot && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {snapshot && (
        <>
          {/* Summary Cards */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Services
                  </Typography>
                  <Typography variant="h4">{snapshot.services.length}</Typography>
                  <LinearProgress
                    variant="determinate"
                    value={
                      snapshot.services.length > 0
                        ? (snapshot.services.filter((s) => s.status === 'healthy').length /
                            snapshot.services.length) *
                          100
                        : 0
                    }
                    color="success"
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Active Anomalies
                  </Typography>
                  <Typography variant="h4" color="error">
                    {snapshot.anomalies.length}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {snapshot.anomalies.filter((a) => a.severity === 'critical').length} critical
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Failing Dependencies
                  </Typography>
                  <Typography variant="h4" color="warning.main">
                    {snapshot.failing_dependencies.length}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {
                      snapshot.failing_dependencies.filter((d) => d.status === 'failed')
                        .length
                    }{' '}
                    failed
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Abnormal Traffic
                  </Typography>
                  <Typography variant="h4" color="info.main">
                    {snapshot.traffic_patterns.filter((p) => p.is_abnormal).length}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    of {snapshot.traffic_patterns.length} flows
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Tabs */}
          <Paper sx={{ mb: 3 }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="diagnostics tabs">
              <Tab icon={<NetworkCheck />} label="Topology" />
              <Tab icon={<BugReport />} label="Anomalies" />
              <Tab icon={<Timeline />} label="Traffic Patterns" />
              <Tab icon={<ErrorIcon />} label="Failing Dependencies" />
            </Tabs>
          </Paper>

          {/* Topology View */}
          <TabPanel value={tabValue} index={0}>
            <Paper sx={{ p: 2, minHeight: 600 }}>
              <LiveTopologyGraph
                services={snapshot.services}
                anomalies={snapshot.anomalies}
                failingDependencies={snapshot.failing_dependencies}
                onResourceClick={handleResourceClick}
              />
            </Paper>
          </TabPanel>

          {/* Anomalies View */}
          <TabPanel value={tabValue} index={1}>
            <AnomalyList
              anomalies={snapshot.anomalies}
              onAnomalyClick={(anomaly) => handleResourceClick(anomaly.resource_id)}
            />
          </TabPanel>

          {/* Traffic Patterns View */}
          <TabPanel value={tabValue} index={2}>
            <TrafficPatternChart
              patterns={snapshot.traffic_patterns}
              onPatternClick={(pattern) => handleResourceClick(pattern.source_id)}
            />
          </TabPanel>

          {/* Failing Dependencies View */}
          <TabPanel value={tabValue} index={3}>
            <Paper>
              <List>
                {snapshot.failing_dependencies.length === 0 ? (
                  <ListItem>
                    <ListItemText
                      primary="No failing dependencies"
                      secondary="All service dependencies are healthy"
                    />
                  </ListItem>
                ) : (
                  snapshot.failing_dependencies.map((dep, index) => (
                    <ListItem
                      key={index}
                      onClick={() => handleResourceClick(dep.target_id)}
                      sx={{ cursor: 'pointer' }}
                      secondaryAction={
                        <IconButton edge="end">
                          <Info />
                        </IconButton>
                      }
                    >
                      <ListItemIcon>{getStatusIcon(dep.status)}</ListItemIcon>
                      <ListItemText
                        primary={`${dep.source_name} → ${dep.target_name}`}
                        secondary={
                          <Stack direction="row" spacing={1}>
                            <Chip
                              size="small"
                              label={dep.status}
                              color={getStatusColor(dep.status) as any}
                            />
                            <Chip
                              size="small"
                              label={`Health: ${dep.health_score.toFixed(1)}%`}
                              color={
                                dep.health_score > 70
                                  ? 'success'
                                  : dep.health_score > 50
                                  ? 'warning'
                                  : 'error'
                              }
                            />
                            <Typography variant="caption" sx={{ ml: 1 }}>
                              {dep.anomalies.length} anomalies
                            </Typography>
                          </Stack>
                        }
                      />
                    </ListItem>
                  ))
                )}
              </List>
            </Paper>
          </TabPanel>
        </>
      )}

      {/* Error Detail Drawer */}
      {selectedResource && (
        <ErrorDetailDrawer
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          resourceId={selectedResource}
          snapshot={snapshot}
        />
      )}
    </Box>
  );
}
