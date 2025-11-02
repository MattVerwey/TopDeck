/**
 * Settings page for viewing and managing application configuration
 */

import { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Typography,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Stack,
  Divider,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  CloudQueue as CloudIcon,
  Security as SecurityIcon,
  Speed as PerformanceIcon,
  Link as ConnectionIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useStore } from '../store/useStore';
import ErrorDisplay from '../components/common/ErrorDisplay';

interface FeatureFlags {
  azure_discovery: boolean;
  aws_discovery: boolean;
  gcp_discovery: boolean;
  github_integration: boolean;
  azure_devops_integration: boolean;
  risk_analysis: boolean;
  monitoring: boolean;
}

interface DiscoverySettings {
  scan_interval: number;
  parallel_workers: number;
  timeout: number;
}

interface CacheSettings {
  ttl_resources: number;
  ttl_risk_scores: number;
  ttl_topology: number;
}

interface SecuritySettings {
  rbac_enabled: boolean;
  audit_logging_enabled: boolean;
  ssl_enabled: boolean;
  neo4j_encrypted: boolean;
  redis_ssl: boolean;
  rabbitmq_ssl: boolean;
}

interface RateLimitSettings {
  enabled: boolean;
  requests_per_minute: number;
}

interface ApplicationSettings {
  version: string;
  environment: string;
  features: FeatureFlags;
  discovery: DiscoverySettings;
  cache: CacheSettings;
  security: SecuritySettings;
  rate_limiting: RateLimitSettings;
  integrations: Record<string, boolean>;
}

interface ConnectionStatus {
  neo4j: Record<string, string>;
  redis: Record<string, string>;
  rabbitmq: Record<string, string>;
  monitoring: Record<string, string>;
}

export default function Settings() {
  const { setLoading, setError, loading, error } = useStore();
  const [settings, setSettings] = useState<ApplicationSettings | null>(null);
  const [connections, setConnections] = useState<ConnectionStatus | null>(null);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch settings from API
      const settingsResponse = await fetch('http://localhost:8000/api/v1/settings');
      if (!settingsResponse.ok) {
        throw new Error('Failed to fetch settings');
      }
      const settingsData = await settingsResponse.json();
      setSettings(settingsData);

      // Fetch connection status
      const connectionsResponse = await fetch('http://localhost:8000/api/v1/settings/connections');
      if (!connectionsResponse.ok) {
        throw new Error('Failed to fetch connection status');
      }
      const connectionsData = await connectionsResponse.json();
      setConnections(connectionsData);
    } catch (err: any) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const formatInterval = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={loadSettings} title="Failed to load settings" />;
  }

  if (!settings || !connections) {
    return null;
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <SettingsIcon fontSize="large" />
        <Box>
          <Typography variant="h4" fontWeight={600}>
            Application Settings
          </Typography>
          <Typography variant="body2" color="text.secondary">
            View and manage TopDeck configuration
          </Typography>
        </Box>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Settings are configured through environment variables. Changes require restarting the application.
        See <strong>.env.example</strong> for configuration options.
      </Alert>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Version
              </Typography>
              <Typography variant="h4" fontWeight={700}>
                {settings.version}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Environment
              </Typography>
              <Chip
                label={settings.environment.toUpperCase()}
                color={
                  settings.environment === 'production'
                    ? 'error'
                    : settings.environment === 'staging'
                    ? 'warning'
                    : 'success'
                }
                sx={{ fontSize: '1.2rem', height: 40 }}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Rate Limiting
              </Typography>
              <Box display="flex" alignItems="center" gap={1}>
                {settings.rate_limiting.enabled ? (
                  <CheckIcon color="success" />
                ) : (
                  <CancelIcon color="error" />
                )}
                <Typography variant="body1">
                  {settings.rate_limiting.enabled
                    ? `${settings.rate_limiting.requests_per_minute} req/min`
                    : 'Disabled'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab label="Feature Flags" icon={<CloudIcon />} iconPosition="start" />
          <Tab label="Security" icon={<SecurityIcon />} iconPosition="start" />
          <Tab label="Performance" icon={<PerformanceIcon />} iconPosition="start" />
          <Tab label="Connections" icon={<ConnectionIcon />} iconPosition="start" />
        </Tabs>
      </Paper>

      {activeTab === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Feature Flags
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Control which features are enabled in the application
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Stack spacing={2}>
              {Object.entries(settings.features).map(([key, enabled]) => (
                <Box
                  key={key}
                  display="flex"
                  justifyContent="space-between"
                  alignItems="center"
                  p={1}
                >
                  <Box>
                    <Typography variant="body1" fontWeight={500}>
                      {key.replace(/_/g, ' ').toUpperCase()}
                    </Typography>
                  </Box>
                  <Chip
                    label={enabled ? 'Enabled' : 'Disabled'}
                    color={enabled ? 'success' : 'default'}
                    icon={enabled ? <CheckIcon /> : <CancelIcon />}
                  />
                </Box>
              ))}
            </Stack>

            <Divider sx={{ my: 3 }} />
            <Typography variant="h6" gutterBottom>
              Integration Status
            </Typography>
            <Stack spacing={2}>
              {Object.entries(settings.integrations).map(([key, configured]) => (
                <Box
                  key={key}
                  display="flex"
                  justifyContent="space-between"
                  alignItems="center"
                  p={1}
                >
                  <Box>
                    <Typography variant="body1" fontWeight={500}>
                      {key.toUpperCase()}
                    </Typography>
                  </Box>
                  <Chip
                    label={configured ? 'Configured' : 'Not Configured'}
                    color={configured ? 'success' : 'default'}
                    icon={configured ? <CheckIcon /> : <CancelIcon />}
                  />
                </Box>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}

      {activeTab === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Security Settings
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              View security and encryption configuration
            </Typography>
            <Divider sx={{ my: 2 }} />
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Setting</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Description</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>RBAC</TableCell>
                    <TableCell>
                      <Chip
                        label={settings.security.rbac_enabled ? 'Enabled' : 'Disabled'}
                        color={settings.security.rbac_enabled ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>Role-Based Access Control</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Audit Logging</TableCell>
                    <TableCell>
                      <Chip
                        label={settings.security.audit_logging_enabled ? 'Enabled' : 'Disabled'}
                        color={settings.security.audit_logging_enabled ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>Security event tracking</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>API SSL/TLS</TableCell>
                    <TableCell>
                      <Chip
                        label={settings.security.ssl_enabled ? 'Enabled' : 'Disabled'}
                        color={settings.security.ssl_enabled ? 'success' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>HTTPS encryption for API server</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Neo4j Encryption</TableCell>
                    <TableCell>
                      <Chip
                        label={settings.security.neo4j_encrypted ? 'Enabled' : 'Disabled'}
                        color={settings.security.neo4j_encrypted ? 'success' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>Database connection encryption</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Redis SSL</TableCell>
                    <TableCell>
                      <Chip
                        label={settings.security.redis_ssl ? 'Enabled' : 'Disabled'}
                        color={settings.security.redis_ssl ? 'success' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>Redis connection encryption</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>RabbitMQ SSL</TableCell>
                    <TableCell>
                      <Chip
                        label={settings.security.rabbitmq_ssl ? 'Enabled' : 'Disabled'}
                        color={settings.security.rabbitmq_ssl ? 'success' : 'warning'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>Message queue encryption</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
            {settings.environment === 'production' && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                For production environments, it is recommended to enable SSL/TLS encryption for all services.
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 2 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Performance Settings
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Discovery and caching configuration
            </Typography>
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle1" fontWeight={600} gutterBottom sx={{ mt: 2 }}>
              Discovery Configuration
            </Typography>
            <TableContainer>
              <Table>
                <TableBody>
                  <TableRow>
                    <TableCell>Scan Interval</TableCell>
                    <TableCell>{formatInterval(settings.discovery.scan_interval)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Parallel Workers</TableCell>
                    <TableCell>{settings.discovery.parallel_workers}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Timeout</TableCell>
                    <TableCell>{settings.discovery.timeout}s</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="subtitle1" fontWeight={600} gutterBottom sx={{ mt: 3 }}>
              Cache TTL Settings
            </Typography>
            <TableContainer>
              <Table>
                <TableBody>
                  <TableRow>
                    <TableCell>Resources Cache</TableCell>
                    <TableCell>{settings.cache.ttl_resources}s</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Risk Scores Cache</TableCell>
                    <TableCell>{settings.cache.ttl_risk_scores}s</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Topology Cache</TableCell>
                    <TableCell>{settings.cache.ttl_topology}s</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {activeTab === 3 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              External Connections
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Database, cache, and monitoring integrations
            </Typography>
            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle1" fontWeight={600} gutterBottom sx={{ mt: 2 }}>
              Database & Infrastructure
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Service</TableCell>
                    <TableCell>Configuration</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Neo4j</TableCell>
                    <TableCell>
                      <Typography variant="body2">{connections.neo4j.uri}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        Encrypted: {connections.neo4j.encrypted}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={connections.neo4j.status} color="success" size="small" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Redis</TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {connections.redis.host}:{connections.redis.port}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        SSL: {connections.redis.ssl}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={connections.redis.status} color="success" size="small" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>RabbitMQ</TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {connections.rabbitmq.host}:{connections.rabbitmq.port}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        SSL: {connections.rabbitmq.ssl}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={connections.rabbitmq.status} color="success" size="small" />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="subtitle1" fontWeight={600} gutterBottom sx={{ mt: 3 }}>
              Monitoring Integrations
            </Typography>
            <TableContainer>
              <Table>
                <TableBody>
                  {Object.entries(connections.monitoring).map(([key, value]) => (
                    <TableRow key={key}>
                      <TableCell>{key.toUpperCase()}</TableCell>
                      <TableCell>
                        {value === 'not configured' ? (
                          <Chip label="Not Configured" size="small" />
                        ) : (
                          <>
                            <Typography variant="body2">{value}</Typography>
                            <Chip label="Configured" color="success" size="small" sx={{ mt: 0.5 }} />
                          </>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
