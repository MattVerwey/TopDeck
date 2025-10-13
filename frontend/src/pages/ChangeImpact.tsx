/**
 * Change Impact Analysis page for ServiceNow/Jira changes
 */

import { useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Alert,
  Autocomplete,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  TrendingDown as PerformanceIcon,
  Schedule as DowntimeIcon,
  People as UsersIcon,
} from '@mui/icons-material';
import { useStore } from '../store/useStore';

export default function ChangeImpact() {
  const { topology } = useStore();
  const [selectedService, setSelectedService] = useState<string>('');
  const [changeType, setChangeType] = useState<string>('deployment');
  const [impactResult, setImpactResult] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);

  const services = topology?.nodes.map((n) => n.name) || [];

  const analyzeImpact = async () => {
    if (!selectedService) return;

    setAnalyzing(true);
    
    // Simulate impact analysis
    setTimeout(() => {
      setImpactResult({
        service: selectedService,
        changeType,
        affectedServices: 12,
        performanceDegradation: 15, // percentage
        estimatedDowntime: 300, // seconds
        userImpact: 'medium',
        breakdown: {
          directDependents: 5,
          indirectDependents: 7,
          criticalPath: true,
          recommendedWindow: 'maintenance',
        },
      });
      setAnalyzing(false);
    }, 2000);
  };

  const getUserImpactColor = (impact: string) => {
    switch (impact) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      default:
        return 'success';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight={600}>
        Change Impact Analysis
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        Analyze the impact of ServiceNow or Jira changes on your infrastructure
      </Typography>

      {/* Input Form */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 5 }}>
            <Autocomplete
              options={services}
              value={selectedService}
              onChange={(_, value) => setSelectedService(value || '')}
              renderInput={(params) => (
                <TextField {...params} label="Select Service" fullWidth />
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <FormControl fullWidth>
              <InputLabel>Change Type</InputLabel>
              <Select
                value={changeType}
                label="Change Type"
                onChange={(e) => setChangeType(e.target.value)}
              >
                <MenuItem value="deployment">Deployment</MenuItem>
                <MenuItem value="configuration">Configuration Change</MenuItem>
                <MenuItem value="scaling">Scaling</MenuItem>
                <MenuItem value="restart">Service Restart</MenuItem>
                <MenuItem value="update">Version Update</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <Button
              variant="contained"
              fullWidth
              size="large"
              startIcon={<SearchIcon />}
              onClick={analyzeImpact}
              disabled={!selectedService || analyzing}
            >
              Analyze
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Analysis Progress */}
      {analyzing && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="body2" gutterBottom>
            Analyzing change impact...
          </Typography>
          <LinearProgress />
        </Paper>
      )}

      {/* Impact Results */}
      {impactResult && !analyzing && (
        <>
          {/* Summary Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card sx={{ background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)' }}>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    <UsersIcon fontSize="large" color="primary" />
                    <Box>
                      <Typography variant="h4" fontWeight={700}>
                        {impactResult.affectedServices}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Services Affected
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card sx={{ background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)' }}>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    <PerformanceIcon fontSize="large" color="warning" />
                    <Box>
                      <Typography variant="h4" fontWeight={700}>
                        {impactResult.performanceDegradation}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Performance Impact
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card sx={{ background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)' }}>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    <DowntimeIcon fontSize="large" color="error" />
                    <Box>
                      <Typography variant="h4" fontWeight={700}>
                        {Math.floor(impactResult.estimatedDowntime / 60)}m
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Est. Downtime
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card sx={{ background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)' }}>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    <UsersIcon fontSize="large" color="info" />
                    <Box>
                      <Chip
                        label={impactResult.userImpact.toUpperCase()}
                        color={getUserImpactColor(impactResult.userImpact) as any}
                        sx={{ mb: 0.5 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        User Impact
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Detailed Breakdown */}
          <Paper sx={{ p: 3, mb: 4 }}>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              Impact Breakdown
            </Typography>
            <Divider sx={{ mb: 3 }} />

            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="body2" gutterBottom>
                  <strong>Direct Dependencies:</strong> {impactResult.breakdown.directDependents} services
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>Indirect Dependencies:</strong> {impactResult.breakdown.indirectDependents} services
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>Critical Path:</strong>{' '}
                  {impactResult.breakdown.criticalPath ? (
                    <Chip label="Yes" color="error" size="small" />
                  ) : (
                    <Chip label="No" color="success" size="small" />
                  )}
                </Typography>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Alert severity="warning">
                  <Typography variant="body2" fontWeight={600} gutterBottom>
                    Recommendation
                  </Typography>
                  <Typography variant="body2">
                    This change should be performed during {impactResult.breakdown.recommendedWindow} window
                    due to the number of affected services and potential downtime.
                  </Typography>
                </Alert>
              </Grid>
            </Grid>
          </Paper>

          {/* Affected Services */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              Affected Services
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Services that will be impacted by this change
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {Array.from({ length: impactResult.affectedServices }, (_, i) => (
                <Chip key={i} label={`Service ${i + 1}`} variant="outlined" />
              ))}
            </Box>
          </Paper>
        </>
      )}

      {/* Empty State */}
      {!impactResult && !analyzing && (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Select a service and change type to analyze impact
          </Typography>
        </Paper>
      )}
    </Box>
  );
}
