/**
 * Custom Dashboards Page
 * 
 * Page for viewing and managing custom monitoring dashboards.
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Dashboard as DashboardIcon,
} from '@mui/icons-material';
import DashboardBuilder from '../components/dashboards/DashboardBuilder';
import apiClient from '../services/api';

interface DashboardSummary {
  id: string;
  name: string;
  description?: string;
  is_default: boolean;
  widget_count: number;
  updated_at: string;
}

export default function CustomDashboards() {
  const [dashboards, setDashboards] = useState<DashboardSummary[]>([]);
  const [selectedDashboard, setSelectedDashboard] = useState<string | null>(null);
  const [showBuilder, setShowBuilder] = useState(false);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboards();
  }, []);

  const loadDashboards = async () => {
    try {
      setLoading(true);
      // const dashboardList = await apiClient.listDashboards();
      // setDashboards(dashboardList);
      
      // For now, use placeholder data
      setDashboards([
        {
          id: '1',
          name: 'System Overview',
          description: 'High-level system health',
          is_default: true,
          widget_count: 4,
          updated_at: new Date().toISOString(),
        },
      ]);
    } catch (error) {
      console.error('Failed to load dashboards:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDashboard = () => {
    setSelectedDashboard(null);
    setShowBuilder(true);
  };

  const handleSelectDashboard = (dashboardId: string) => {
    setSelectedDashboard(dashboardId);
    setShowBuilder(true);
  };

  const handleDeleteDashboard = async (dashboardId: string) => {
    if (!confirm('Are you sure you want to delete this dashboard?')) {
      return;
    }

    try {
      // await apiClient.deleteDashboard(dashboardId);
      await loadDashboards();
    } catch (error) {
      console.error('Failed to delete dashboard:', error);
    }
  };

  const handleCreateFromTemplate = async (templateId: string) => {
    try {
      // await apiClient.createDashboardFromTemplate(templateId);
      await loadDashboards();
      setTemplateDialogOpen(false);
    } catch (error) {
      console.error('Failed to create dashboard from template:', error);
    }
  };

  if (showBuilder) {
    return (
      <DashboardBuilder
        dashboardId={selectedDashboard || undefined}
        onSave={() => {
          setShowBuilder(false);
          loadDashboards();
        }}
      />
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" fontWeight="bold">
          Custom Dashboards
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            onClick={() => setTemplateDialogOpen(true)}
          >
            Use Template
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateDashboard}
          >
            Create Dashboard
          </Button>
        </Box>
      </Box>

      {/* Dashboard List */}
      {dashboards.length === 0 ? (
        <Box
          sx={{
            textAlign: 'center',
            py: 8,
          }}
        >
          <DashboardIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No dashboards yet
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Create your first custom dashboard to monitor your services
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateDashboard}
          >
            Create Dashboard
          </Button>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {dashboards.map((dashboard) => (
            <Grid item xs={12} sm={6} md={4} key={dashboard.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Typography variant="h6" fontWeight="medium">
                      {dashboard.name}
                    </Typography>
                    {dashboard.is_default && (
                      <Chip label="Default" size="small" color="primary" />
                    )}
                  </Box>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {dashboard.description || 'No description'}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      {dashboard.widget_count} widgets
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Updated {new Date(dashboard.updated_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    onClick={() => handleSelectDashboard(dashboard.id)}
                  >
                    Open
                  </Button>
                  {!dashboard.is_default && (
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteDashboard(dashboard.id)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  )}
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Template Dialog */}
      <Dialog
        open={templateDialogOpen}
        onClose={() => setTemplateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Choose a Template</DialogTitle>
        <DialogContent>
          <List>
            <ListItem disablePadding>
              <ListItemButton onClick={() => handleCreateFromTemplate('overview')}>
                <ListItemText
                  primary="System Overview"
                  secondary="High-level view of system health and performance"
                />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton onClick={() => handleCreateFromTemplate('performance')}>
                <ListItemText
                  primary="Performance Monitoring"
                  secondary="Focus on latency, throughput, and resource utilization"
                />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton onClick={() => handleCreateFromTemplate('error_tracking')}>
                <ListItemText
                  primary="Error Tracking"
                  secondary="Monitor errors, anomalies, and service failures"
                />
              </ListItemButton>
            </ListItem>
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTemplateDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
