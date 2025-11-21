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
import DocLink from '../components/common/DocLink';

export default function ChangeImpact() {
  const { topology } = useStore();
  const [selectedResourceType, setSelectedResourceType] = useState<string>('');
  const [selectedService, setSelectedService] = useState<string>('');
  const [impactResult, setImpactResult] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);

  // Get unique resource types for filtering
  const resourceTypes = [...new Set(topology?.nodes.map((n) => n.resource_type) || [])].sort();
  
  // Filter services by selected resource type
  const filteredNodes = selectedResourceType
    ? topology?.nodes.filter((n) => n.resource_type === selectedResourceType) || []
    : topology?.nodes || [];
  
  // Create service list with resource type labels
  const services = filteredNodes.map((n) => ({
    label: `${n.name} (${n.resource_type})`,
    value: n.name,
    type: n.resource_type,
  }));

  const analyzeImpact = async () => {
    if (!selectedService) return;

    setAnalyzing(true);
    
    try {
      // Find the selected service node in the topology
      const selectedNode = topology?.nodes.find(n => n.name === selectedService);
      
      if (!selectedNode) {
        throw new Error('Selected service not found in topology');
      }

      // Get all edges where this node is the source (things it depends on)
      // or target (things that depend on it)
      const directDependents = topology?.edges?.filter(
        e => e.source_id === selectedNode.id
      ) || [];
      
      const indirectDependents = topology?.edges?.filter(
        e => e.target_id === selectedNode.id
      ) || [];

      // Get the actual resource nodes
      const directResources = directDependents
        .map(edge => topology?.nodes.find(n => n.id === edge.target_id))
        .filter(n => n != null);
      
      const indirectResources = indirectDependents
        .map(edge => topology?.nodes.find(n => n.id === edge.source_id))
        .filter(n => n != null);

      // Deduplicate resources by id to prevent duplicates from bidirectional edges
      const allResourcesMap = new Map();
      [...directResources, ...indirectResources].forEach(resource => {
        if (resource && resource.id) {
          allResourcesMap.set(resource.id, resource);
        }
      });
      const allAffectedResources = Array.from(allResourcesMap.values());
      const totalAffected = allAffectedResources.length;

      // Calculate impact metrics based on dependencies
      const criticalPath = totalAffected > 10 || directResources.length > 5;
      const performanceDegradation = Math.min(totalAffected * 2, 25);
      const estimatedDowntime = Math.min(totalAffected * 30, 600);
      
      setImpactResult({
        service: selectedService,
        changeType: 'deployment',
        affectedServices: totalAffected,
        performanceDegradation,
        estimatedDowntime,
        userImpact: totalAffected > 15 ? 'high' : totalAffected > 8 ? 'medium' : 'low',
        breakdown: {
          directDependents: directResources.length,
          indirectDependents: indirectResources.length,
          criticalPath,
          recommendedWindow: criticalPath ? 'maintenance' : 'normal',
        },
        affectedResourcesList: allAffectedResources,
      });
    } catch (error) {
      console.error('Failed to analyze impact:', error);
      // Show error message instead of mock data
      alert(`Failed to analyze impact: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setImpactResult(null);
    } finally {
      setAnalyzing(false);
    }
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
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4" fontWeight={600}>
          Change Impact Analysis
        </Typography>
        <DocLink href="docs/CHANGE_MANAGEMENT_GUIDE.md" text="Change Management Guide" />
      </Box>

      <Typography variant="body1" color="text.secondary" paragraph>
        Analyze the impact of ServiceNow or Jira changes on your infrastructure
      </Typography>

      {/* Input Form */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 3 }}>
            <Autocomplete
              options={resourceTypes}
              value={selectedResourceType}
              onChange={(_, value) => {
                setSelectedResourceType(value || '');
                setSelectedService(''); // Reset service when type changes
              }}
              renderInput={(params) => (
                <TextField {...params} label="Resource Type" fullWidth />
              )}
              renderOption={(props, option) => (
                <li {...props}>
                  <Box display="flex" justifyContent="space-between" width="100%">
                    <Typography variant="body2">{option}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {topology?.nodes.filter((n) => n.resource_type === option).length}
                    </Typography>
                  </Box>
                </li>
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Autocomplete
              options={services}
              value={services.find((s) => s.value === selectedService) || null}
              onChange={(_, value) => setSelectedService(value?.value || '')}
              getOptionLabel={(option) => option.label}
              isOptionEqualToValue={(option, value) => option.value === value.value}
              renderInput={(params) => (
                <TextField {...params} label="Select Service" fullWidth />
              )}
              disabled={!selectedResourceType}
            />
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
            <Grid container spacing={1.5}>
              {impactResult.affectedResourcesList && impactResult.affectedResourcesList.length > 0 ? (
                impactResult.affectedResourcesList.map((resource: any) => (
                  <Grid key={resource.id || resource.name} size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
                    <Box
                      sx={{
                        p: 2,
                        border: '1px solid',
                        borderColor: 'divider',
                        borderRadius: 1,
                        transition: 'all 0.2s',
                        '&:hover': {
                          borderColor: 'primary.main',
                          bgcolor: 'action.hover',
                        },
                      }}
                    >
                      <Typography variant="body2" fontWeight={600} noWrap title={resource.name}>
                        {resource.name || resource.id || 'Unknown'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" noWrap>
                        {resource.resource_type || 'Unknown type'}
                      </Typography>
                    </Box>
                  </Grid>
                ))
              ) : (
                // Fallback to mock data if affectedResourcesList is not available
                Array.from({ length: impactResult.affectedServices }, (_, i) => (
                  <Grid key={i} size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
                    <Box
                      sx={{
                        p: 2,
                        border: '1px solid',
                        borderColor: 'divider',
                        borderRadius: 1,
                        transition: 'all 0.2s',
                        '&:hover': {
                          borderColor: 'primary.main',
                          bgcolor: 'action.hover',
                        },
                      }}
                    >
                      <Typography variant="body2" fontWeight={600} noWrap>
                        Service {i + 1}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Affected service
                      </Typography>
                    </Box>
                  </Grid>
                ))
              )}
            </Grid>
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
