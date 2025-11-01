/**
 * Integrations management page for plugins and data sources
 */

import { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from '@mui/material';
import {
  GitHub as GitHubIcon,
  Cloud as AzureIcon,
  DeveloperMode as AzureDevOpsIcon,
  Assessment as PrometheusIcon,
  ConfirmationNumber as JiraIcon,
  BugReport as ServiceNowIcon,
  Storage as LokiIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useStore } from '../store/useStore';

interface Integration {
  id: string;
  name: string;
  type: string;
  description: string;
  enabled: boolean;
  configured: boolean;
  icon: React.ReactNode;
  lastSync?: string;
  config?: Record<string, string>;
}

export default function Integrations() {
  const { setLoading } = useStore();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [configDialog, setConfigDialog] = useState<{
    open: boolean;
    integration: Integration | null;
  }>({ open: false, integration: null });

  useEffect(() => {
    loadIntegrations();
  }, []);

  const loadIntegrations = async () => {
    setLoading(true);
    // Simulate loading integrations
    setTimeout(() => {
      setIntegrations([
        {
          id: '1',
          name: 'Azure',
          type: 'cloud-provider',
          description: 'Connect to Azure cloud resources and services',
          enabled: true,
          configured: true,
          icon: <AzureIcon fontSize="large" />,
          lastSync: '30 minutes ago',
        },
        {
          id: '2',
          name: 'GitHub',
          type: 'source-control',
          description: 'Connect to GitHub repositories and workflows',
          enabled: true,
          configured: true,
          icon: <GitHubIcon fontSize="large" />,
          lastSync: '2 hours ago',
        },
        {
          id: '3',
          name: 'Azure DevOps',
          type: 'source-control',
          description: 'Connect to Azure DevOps pipelines and repos',
          enabled: true,
          configured: true,
          icon: <AzureDevOpsIcon fontSize="large" />,
          lastSync: '1 hour ago',
        },
        {
          id: '4',
          name: 'Prometheus',
          type: 'monitoring',
          description: 'Pull metrics from Prometheus',
          enabled: true,
          configured: true,
          icon: <PrometheusIcon fontSize="large" />,
          lastSync: '5 minutes ago',
        },
        {
          id: '5',
          name: 'Loki',
          type: 'logging',
          description: 'Pull logs from Grafana Loki',
          enabled: true,
          configured: true,
          icon: <LokiIcon fontSize="large" />,
          lastSync: '10 minutes ago',
        },
        {
          id: '6',
          name: 'Jira',
          type: 'ticketing',
          description: 'Integrate with Jira for change tracking',
          enabled: false,
          configured: false,
          icon: <JiraIcon fontSize="large" />,
        },
        {
          id: '7',
          name: 'ServiceNow',
          type: 'ticketing',
          description: 'Integrate with ServiceNow for change requests',
          enabled: false,
          configured: false,
          icon: <ServiceNowIcon fontSize="large" />,
        },
      ]);
      setLoading(false);
    }, 500);
  };

  const handleToggle = (id: string) => {
    setIntegrations((prev) =>
      prev.map((int) =>
        int.id === id ? { ...int, enabled: !int.enabled } : int
      )
    );
  };

  const handleConfigure = (integration: Integration) => {
    setConfigDialog({ open: true, integration });
  };

  const handleCloseConfig = () => {
    setConfigDialog({ open: false, integration: null });
  };

  const handleSaveConfig = () => {
    // Save configuration logic here
    if (configDialog.integration) {
      setIntegrations((prev) =>
        prev.map((int) =>
          int.id === configDialog.integration?.id
            ? { ...int, configured: true }
            : int
        )
      );
    }
    handleCloseConfig();
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'cloud-provider':
        return 'secondary';
      case 'source-control':
        return 'primary';
      case 'monitoring':
        return 'success';
      case 'logging':
        return 'info';
      case 'ticketing':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight={600}>
        Integrations & Plugins
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        Manage your data sources and integrations
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        Enable and configure integrations to pull data from various sources into TopDeck
      </Alert>

      <Grid container spacing={3}>
        {integrations.map((integration) => (
          <Grid size={{ xs: 12, md: 6, lg: 4 }} key={integration.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
              }}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <Box sx={{ color: 'primary.main' }}>{integration.icon}</Box>
                  <Box flexGrow={1}>
                    <Typography variant="h6">{integration.name}</Typography>
                    <Chip
                      label={integration.type}
                      size="small"
                      color={getTypeColor(integration.type) as any}
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                  <Box>
                    {integration.configured ? (
                      <CheckIcon color="success" />
                    ) : (
                      <ErrorIcon color="disabled" />
                    )}
                  </Box>
                </Box>

                <Typography variant="body2" color="text.secondary" paragraph>
                  {integration.description}
                </Typography>

                {integration.lastSync && (
                  <Typography variant="caption" color="text.secondary">
                    Last sync: {integration.lastSync}
                  </Typography>
                )}
              </CardContent>

              <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={integration.enabled}
                      onChange={() => handleToggle(integration.id)}
                      disabled={!integration.configured}
                    />
                  }
                  label="Enabled"
                />
                <Button
                  size="small"
                  startIcon={<SettingsIcon />}
                  onClick={() => handleConfigure(integration)}
                >
                  Configure
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Configuration Dialog */}
      <Dialog open={configDialog.open} onClose={handleCloseConfig} maxWidth="sm" fullWidth>
        <DialogTitle>
          Configure {configDialog.integration?.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography variant="body2" color="text.secondary" paragraph>
              Enter the configuration details for {configDialog.integration?.name}
            </Typography>

            {configDialog.integration?.type === 'cloud-provider' && (
              <>
                <TextField
                  label="Tenant ID"
                  fullWidth
                  margin="normal"
                  placeholder="Enter Azure tenant ID"
                />
                <TextField
                  label="Client ID"
                  fullWidth
                  margin="normal"
                  placeholder="Enter Azure client ID"
                />
                <TextField
                  label="Client Secret"
                  fullWidth
                  margin="normal"
                  type="password"
                  placeholder="Enter Azure client secret"
                />
                <TextField
                  label="Subscription ID"
                  fullWidth
                  margin="normal"
                  placeholder="Enter Azure subscription ID"
                />
              </>
            )}

            {configDialog.integration?.type === 'source-control' && (
              <>
                <TextField
                  label="API Token"
                  fullWidth
                  margin="normal"
                  type="password"
                  placeholder="Enter your API token"
                />
                <TextField
                  label="Organization"
                  fullWidth
                  margin="normal"
                  placeholder="Enter organization name"
                />
              </>
            )}

            {configDialog.integration?.type === 'monitoring' && (
              <>
                <TextField
                  label="Endpoint URL"
                  fullWidth
                  margin="normal"
                  placeholder="https://prometheus.example.com"
                />
                <TextField
                  label="Authentication Token"
                  fullWidth
                  margin="normal"
                  type="password"
                  placeholder="Optional auth token"
                />
              </>
            )}

            {configDialog.integration?.type === 'ticketing' && (
              <>
                <TextField
                  label="Instance URL"
                  fullWidth
                  margin="normal"
                  placeholder="https://your-instance.atlassian.net"
                />
                <TextField
                  label="API Key"
                  fullWidth
                  margin="normal"
                  type="password"
                  placeholder="Enter your API key"
                />
                <TextField
                  label="Project Key"
                  fullWidth
                  margin="normal"
                  placeholder="PROJECT-KEY"
                />
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseConfig}>Cancel</Button>
          <Button onClick={handleSaveConfig} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
