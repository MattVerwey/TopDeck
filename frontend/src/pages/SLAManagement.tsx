/**
 * SLA/SLO Management page
 * Allows configuration of SLAs and monitoring of SLOs and error budgets
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  IconButton,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Chip,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import apiClient from '../services/api';
import type { SLAConfig, ErrorBudgetStatus } from '../types';

interface SLAFormData {
  name: string;
  description: string;
  sla_percentage: number;
  service_name: string;
  resources: string[];
}

// Constants for resource metrics thresholds
const RESOURCE_ID_DISPLAY_LENGTH = 16;
const ERROR_COUNT_HIGH_THRESHOLD = 50;
const ERROR_COUNT_MEDIUM_THRESHOLD = 20;
const AT_RISK_MARGIN_PERCENTAGE = 0.5;

export default function SLAManagement() {
  const [slaConfigs, setSlaConfigs] = useState<SLAConfig[]>([]);
  const [errorBudgets, setErrorBudgets] = useState<Record<string, ErrorBudgetStatus>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState<SLAConfig | null>(null);
  const [availableResources, setAvailableResources] = useState<Array<{ id: string; name: string }>>([]);
  const [formData, setFormData] = useState<SLAFormData>({
    name: '',
    description: '',
    sla_percentage: 99.0,
    service_name: '',
    resources: [],
  });
  const [resourceDialogOpen, setResourceDialogOpen] = useState(false);
  const [selectedSLAForResources, setSelectedSLAForResources] = useState<SLAConfig | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load SLA configurations
      const configs = await apiClient.listSLAConfigs();
      setSlaConfigs(configs);

      // Load error budget status for each SLA
      const budgets: Record<string, ErrorBudgetStatus> = {};
      await Promise.all(
        configs.map(async (config) => {
          if (config.id) {
            try {
              const budget = await apiClient.getErrorBudgetStatus(config.id);
              budgets[config.id] = budget;
            } catch (err) {
              console.error(`Failed to load error budget for ${config.id}:`, err);
            }
          }
        })
      );
      setErrorBudgets(budgets);

      // Load available resources from topology
      const topology = await apiClient.getTopology();
      const resources = topology.nodes.map(node => ({
        id: node.id,
        name: node.name,
      }));
      setAvailableResources(resources);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load SLA data');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (config?: SLAConfig) => {
    if (config) {
      setEditingConfig(config);
      setFormData({
        name: config.name,
        description: config.description || '',
        sla_percentage: config.sla_percentage,
        service_name: config.service_name,
        resources: config.resources,
      });
    } else {
      setEditingConfig(null);
      setFormData({
        name: '',
        description: '',
        sla_percentage: 99.0,
        service_name: '',
        resources: [],
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingConfig(null);
  };

  const handleSaveConfig = async () => {
    try {
      if (editingConfig?.id) {
        await apiClient.updateSLAConfig(editingConfig.id, {
          ...editingConfig,
          ...formData,
        });
      } else {
        await apiClient.createSLAConfig(formData);
      }
      handleCloseDialog();
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save SLA configuration');
    }
  };

  const handleDeleteConfig = async (slaId: string) => {
    if (!window.confirm('Are you sure you want to delete this SLA configuration?')) {
      return;
    }

    try {
      await apiClient.deleteSLAConfig(slaId);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete SLA configuration');
    }
  };

  const handleOpenResourceDialog = (config: SLAConfig) => {
    setSelectedSLAForResources(config);
    setResourceDialogOpen(true);
  };

  const handleCloseResourceDialog = () => {
    setResourceDialogOpen(false);
    setSelectedSLAForResources(null);
  };

  const getStatusColor = (budget: ErrorBudgetStatus) => {
    if (!budget.is_within_budget) return 'error';
    if (budget.error_budget_consumed_percentage > 80) return 'warning';
    if (budget.error_budget_consumed_percentage > 50) return 'info';
    return 'success';
  };

  const getStatusIcon = (budget: ErrorBudgetStatus) => {
    if (!budget.is_within_budget) return <ErrorIcon color="error" />;
    if (budget.error_budget_consumed_percentage > 80) return <WarningIcon color="warning" />;
    return <CheckCircleIcon color="success" />;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          SLA/SLO Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add SLA
        </Button>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography variant="h6" color="text.secondary">
                  Total SLAs
                </Typography>
                <TrendingUpIcon color="primary" />
              </Box>
              <Typography variant="h3" sx={{ mt: 1 }}>
                {slaConfigs.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography variant="h6" color="text.secondary">
                  Meeting SLA
                </Typography>
                <CheckCircleIcon color="success" />
              </Box>
              <Typography variant="h3" sx={{ mt: 1 }}>
                {Object.values(errorBudgets).filter(b => b.is_within_budget).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography variant="h6" color="text.secondary">
                  At Risk
                </Typography>
                <WarningIcon color="warning" />
              </Box>
              <Typography variant="h3" sx={{ mt: 1 }}>
                {Object.values(errorBudgets).filter(
                  b => b.is_within_budget && b.error_budget_consumed_percentage > 80
                ).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* SLA Configurations Table */}
        <Grid size={{ xs: 12 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              SLA Configurations
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Service Name</TableCell>
                    <TableCell>SLA Name</TableCell>
                    <TableCell align="right">SLA Target</TableCell>
                    <TableCell align="right">SLO Target</TableCell>
                    <TableCell align="right">Current Uptime</TableCell>
                    <TableCell align="center">Status</TableCell>
                    <TableCell align="right">Error Budget</TableCell>
                    <TableCell align="center">Resources</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {slaConfigs.map((config) => {
                    const budget = config.id ? errorBudgets[config.id] : null;
                    return (
                      <TableRow key={config.id}>
                        <TableCell>{config.service_name}</TableCell>
                        <TableCell>
                          <Typography variant="body2" fontWeight="bold">
                            {config.name}
                          </Typography>
                          {config.description && (
                            <Typography variant="caption" color="text.secondary">
                              {config.description}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell align="right">
                          <Chip label={`${config.sla_percentage}%`} size="small" />
                        </TableCell>
                        <TableCell align="right">
                          {budget && (
                            <Chip label={`${budget.slo_percentage.toFixed(3)}%`} size="small" color="primary" />
                          )}
                        </TableCell>
                        <TableCell align="right">
                          {budget && (
                            <Chip
                              label={`${budget.current_uptime_percentage.toFixed(2)}%`}
                              size="small"
                              color={budget.is_within_budget ? 'success' : 'error'}
                            />
                          )}
                        </TableCell>
                        <TableCell align="center">
                          {budget && (
                            <Tooltip title={budget.is_within_budget ? 'Meeting SLA' : 'Below SLA'}>
                              {getStatusIcon(budget)}
                            </Tooltip>
                          )}
                        </TableCell>
                        <TableCell align="right">
                          {budget && (
                            <Box>
                              <LinearProgress
                                variant="determinate"
                                value={budget.error_budget_consumed_percentage}
                                color={getStatusColor(budget)}
                                sx={{ mb: 0.5, height: 8, borderRadius: 1 }}
                              />
                              <Typography variant="caption">
                                {budget.error_budget_remaining_percentage.toFixed(1)}% remaining
                              </Typography>
                            </Box>
                          )}
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={config.resources.length}
                            size="small"
                            onClick={() => handleOpenResourceDialog(config)}
                            color={config.resources.length > 0 ? 'primary' : 'default'}
                            sx={{ cursor: 'pointer' }}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <IconButton
                            size="small"
                            onClick={() => handleOpenDialog(config)}
                            color="primary"
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => config.id && handleDeleteConfig(config.id)}
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  {slaConfigs.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={9} align="center">
                        <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                          No SLA configurations found. Click "Add SLA" to create one.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* SLA Info Box */}
        <Grid size={{ xs: 12 }}>
          <Alert severity="info" icon={<InfoIcon />}>
            <Typography variant="body2">
              <strong>About SLA/SLO:</strong> SLA (Service Level Agreement) is your commitment to customers. 
              SLO (Service Level Objective) is your internal target, set stricter than the SLA to provide a safety margin. 
              Error budget represents the acceptable downtime within your SLA target.
            </Typography>
          </Alert>
        </Grid>
      </Grid>

      {/* Resource Details Dialog */}
      <Dialog open={resourceDialogOpen} onClose={handleCloseResourceDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          Resource Metrics - {selectedSLAForResources?.name}
        </DialogTitle>
        <DialogContent>
          {selectedSLAForResources && selectedSLAForResources.id && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Showing metrics for all resources in this SLA. Resources in yellow or red are close to or failing SLO targets.
              </Typography>
              
              {errorBudgets[selectedSLAForResources.id]?.resources_status && errorBudgets[selectedSLAForResources.id].resources_status.length > 0 ? (
                <TableContainer component={Paper} sx={{ mt: 2 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Resource ID</TableCell>
                        <TableCell align="right">Uptime</TableCell>
                        <TableCell align="right">Error Count</TableCell>
                        <TableCell align="center">SLO Status</TableCell>
                        <TableCell>Health</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedSLAForResources.id && errorBudgets[selectedSLAForResources.id]?.resources_status.map((resourceStatus) => {
                        const resource = availableResources.find(r => r.id === resourceStatus.resource_id);
                        const uptimePercent = resourceStatus.uptime_percentage;
                        const errorBudget = errorBudgets[selectedSLAForResources.id!];
                        
                        // Safety check: if errorBudget doesn't exist, skip this resource
                        if (!errorBudget) return null;
                        
                        const sloPercent = errorBudget.slo_percentage;
                        const slaPercent = errorBudget.sla_percentage;
                        
                        // Determine status color based on how close to failing
                        let statusColor: 'success' | 'warning' | 'error' = 'success';
                        let statusText = 'Healthy';
                        
                        if (uptimePercent < slaPercent) {
                          statusColor = 'error';
                          statusText = 'Below SLA';
                        } else if (uptimePercent < sloPercent) {
                          statusColor = 'warning';
                          statusText = 'Below SLO';
                        } else if (uptimePercent < sloPercent + AT_RISK_MARGIN_PERCENTAGE) {
                          statusColor = 'warning';
                          statusText = 'At Risk';
                        }
                        
                        return (
                          <TableRow key={resourceStatus.resource_id}>
                            <TableCell>
                              <Typography variant="body2" fontWeight={statusColor !== 'success' ? 'bold' : 'normal'}>
                                {resource?.name || resourceStatus.resource_id}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {resourceStatus.resource_id.length > RESOURCE_ID_DISPLAY_LENGTH
                                  ? resourceStatus.resource_id.slice(0, RESOURCE_ID_DISPLAY_LENGTH) + '...'
                                  : resourceStatus.resource_id}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Chip
                                label={`${uptimePercent.toFixed(2)}%`}
                                size="small"
                                color={statusColor}
                              />
                            </TableCell>
                            <TableCell align="right">
                              <Chip
                                label={resourceStatus.error_count}
                                size="small"
                                color={resourceStatus.error_count > ERROR_COUNT_HIGH_THRESHOLD ? 'error' : resourceStatus.error_count > ERROR_COUNT_MEDIUM_THRESHOLD ? 'warning' : 'default'}
                              />
                            </TableCell>
                            <TableCell align="center">
                              {resourceStatus.meets_slo ? (
                                <CheckCircleIcon color="success" fontSize="small" />
                              ) : (
                                <WarningIcon color="warning" fontSize="small" />
                              )}
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={sloPercent > 0 ? Math.min(100, (uptimePercent / sloPercent) * 100) : 0}
                                  color={statusColor}
                                  sx={{ flexGrow: 1, height: 6, borderRadius: 1 }}
                                />
                                <Typography variant="caption" color={`${statusColor}.main`}>
                                  {statusText}
                                </Typography>
                              </Box>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info" sx={{ mt: 2 }}>
                  No resource metrics available for this SLA.
                </Alert>
              )}
              
              <Box sx={{ mt: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Metric Thresholds:
                </Typography>
                <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      SLA Target:
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {selectedSLAForResources.sla_percentage}%
                    </Typography>
                  </Box>
                  {selectedSLAForResources.id && (
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        SLO Target:
                      </Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {errorBudgets[selectedSLAForResources.id]?.slo_percentage.toFixed(3)}%
                      </Typography>
                    </Box>
                  )}
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Resources Monitored:
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {selectedSLAForResources.resources.length}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseResourceDialog}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* SLA Configuration Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingConfig ? 'Edit SLA Configuration' : 'Create SLA Configuration'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12 }}>
                <TextField
                  fullWidth
                  label="SLA Name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <TextField
                  fullWidth
                  label="Description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  multiline
                  rows={2}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  label="Service Name"
                  value={formData.service_name}
                  onChange={(e) => setFormData({ ...formData, service_name: e.target.value })}
                  required
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6 }}>
                <TextField
                  fullWidth
                  label="SLA Target (%)"
                  type="number"
                  value={formData.sla_percentage}
                  onChange={(e) => setFormData({ ...formData, sla_percentage: parseFloat(e.target.value) })}
                  inputProps={{ min: 0, max: 100, step: 0.1 }}
                  required
                />
              </Grid>
              <Grid size={{ xs: 12 }}>
                <FormControl fullWidth>
                  <InputLabel>Resources</InputLabel>
                  <Select
                    multiple
                    value={formData.resources}
                    onChange={(e) => setFormData({ ...formData, resources: e.target.value as string[] })}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => {
                          const resource = availableResources.find(r => r.id === value);
                          return (
                            <Chip key={value} label={resource?.name || value} size="small" />
                          );
                        })}
                      </Box>
                    )}
                  >
                    {availableResources.map((resource) => (
                      <MenuItem key={resource.id} value={resource.id}>
                        {resource.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSaveConfig}
            variant="contained"
            disabled={!formData.name || !formData.service_name}
          >
            {editingConfig ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
