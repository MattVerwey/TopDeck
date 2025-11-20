/**
 * Remediation Suggestions Component
 * 
 * Displays automated remediation suggestions including:
 * - Risk mitigation recommendations
 * - Mitigation strategies for failure scenarios
 * - Monitoring recommendations
 * - Dependency vulnerability fixes
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
  Alert,
  CircularProgress,
  Button,
  TextField,
  Autocomplete,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Build as BuildIcon,
  Security as SecurityIcon,
  Visibility as MonitoringIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  BugReport as VulnerabilityIcon,
} from '@mui/icons-material';
import { useStore } from '../../store/useStore';
import apiClient from '../../services/api';

interface RemediationData {
  resource_id: string;
  resource_name: string;
  risk_level: string;
  recommendations: string[];
  mitigation_strategies: string[];
  monitoring_recommendations: string[];
  dependency_vulnerabilities: Array<{
    package_name: string;
    current_version: string;
    vulnerability_id: string;
    severity: string;
    description: string;
    fixed_version?: string;
    exploit_available: boolean;
  }>;
}

export default function RemediationSuggestions() {
  const { topology } = useStore();
  const [selectedResource, setSelectedResource] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [remediationData, setRemediationData] = useState<RemediationData | null>(null);

  const resources = topology?.nodes || [];

  const fetchRemediations = async () => {
    if (!selectedResource) return;

    setLoading(true);
    setError(null);

    try {
      // Fetch comprehensive risk analysis which includes all remediation data
      const comprehensive = await apiClient.getComprehensiveRiskAnalysis(selectedResource);
      
      // Combine all recommendations and strategies
      const allRecommendations = comprehensive.all_recommendations || [];
      const mitigationStrategies = [
        ...(comprehensive.degraded_performance_scenario?.mitigation_strategies || []),
        ...(comprehensive.intermittent_failure_scenario?.mitigation_strategies || []),
      ];
      const monitoringRecommendations = [
        ...(comprehensive.degraded_performance_scenario?.monitoring_recommendations || []),
        ...(comprehensive.intermittent_failure_scenario?.monitoring_recommendations || []),
      ];

      // Remove duplicates
      const uniqueMitigations = Array.from(new Set(mitigationStrategies));
      const uniqueMonitoring = Array.from(new Set(monitoringRecommendations));

      setRemediationData({
        resource_id: selectedResource,
        resource_name: comprehensive.standard_assessment.resource_name || 'Unknown',
        risk_level: comprehensive.standard_assessment.risk_level || 'medium',
        recommendations: allRecommendations,
        mitigation_strategies: uniqueMitigations,
        monitoring_recommendations: uniqueMonitoring,
        dependency_vulnerabilities: comprehensive.dependency_vulnerabilities || [],
      });
    } catch (err) {
      console.error('Failed to fetch remediation data:', err);
      setError('Failed to fetch remediation suggestions. The backend may be unavailable or the resource may not have risk analysis data yet.');
      
      // Set empty state instead of mock data
      setRemediationData(null);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      default:
        return 'success';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'high':
        return <WarningIcon color="warning" />;
      case 'medium':
        return <InfoIcon color="info" />;
      default:
        return <CheckCircleIcon color="success" />;
    }
  };

  const getRecommendationIcon = (recommendation: string) => {
    if (recommendation.includes('🔴') || recommendation.includes('CRITICAL')) {
      return <ErrorIcon color="error" />;
    } else if (recommendation.includes('⚠️') || recommendation.includes('WARNING')) {
      return <WarningIcon color="warning" />;
    } else {
      return <InfoIcon color="info" />;
    }
  };

  return (
    <Box>
      {/* Selection Form */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Automated Remediation Suggestions
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Get comprehensive remediation suggestions including risk mitigation, failure scenarios, monitoring, and dependency vulnerabilities
        </Typography>
        
        <Grid container spacing={2} alignItems="center">
          <Grid size={{ xs: 12, md: 9 }}>
            <Autocomplete
              options={resources}
              getOptionLabel={(option) => `${option.name} (${option.resource_type})`}
              value={resources.find((r) => r.id === selectedResource) || null}
              onChange={(_, value) => setSelectedResource(value?.id || '')}
              renderInput={(params) => (
                <TextField {...params} label="Select Resource" fullWidth />
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <Button
              variant="contained"
              fullWidth
              size="large"
              onClick={fetchRemediations}
              disabled={!selectedResource || loading}
            >
              Get Suggestions
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {loading && (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
          <CircularProgress />
        </Box>
      )}

      {error && <Alert severity="warning" sx={{ mb: 3 }}>{error}</Alert>}

      {remediationData && !loading && (
        <>
          {/* Header with Risk Level */}
          <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)' }}>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h5" fontWeight={600}>
                  {remediationData.resource_name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Resource ID: {remediationData.resource_id}
                </Typography>
              </Box>
              <Chip
                label={`${remediationData.risk_level.toUpperCase()} RISK`}
                color={getSeverityColor(remediationData.risk_level) as 'error' | 'warning' | 'info' | 'success'}
                icon={getSeverityIcon(remediationData.risk_level)}
              />
            </Box>
          </Paper>

          {/* Risk Mitigation Recommendations */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box display="flex" alignItems="center" gap={2}>
                <BuildIcon color="primary" />
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    Risk Mitigation Recommendations
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {remediationData.recommendations.length} recommendation{remediationData.recommendations.length !== 1 ? 's' : ''}
                  </Typography>
                </Box>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {remediationData.recommendations.length > 0 ? (
                <List>
                  {remediationData.recommendations.map((rec, index) => (
                    <Box key={index}>
                      <ListItem>
                        <ListItemIcon>
                          {getRecommendationIcon(rec)}
                        </ListItemIcon>
                        <ListItemText
                          primary={rec}
                          primaryTypographyProps={{ variant: 'body1' }}
                        />
                      </ListItem>
                      {index < remediationData.recommendations.length - 1 && <Divider />}
                    </Box>
                  ))}
                </List>
              ) : (
                <Alert severity="success">
                  No critical recommendations - resource appears well-configured
                </Alert>
              )}
            </AccordionDetails>
          </Accordion>

          {/* Mitigation Strategies */}
          <Accordion defaultExpanded sx={{ mt: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box display="flex" alignItems="center" gap={2}>
                <SecurityIcon color="primary" />
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    Failure Mitigation Strategies
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {remediationData.mitigation_strategies.length} strateg{remediationData.mitigation_strategies.length !== 1 ? 'ies' : 'y'}
                  </Typography>
                </Box>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {remediationData.mitigation_strategies.length > 0 ? (
                <List>
                  {remediationData.mitigation_strategies.map((strategy, index) => (
                    <Box key={index}>
                      <ListItem>
                        <ListItemIcon>
                          <CheckCircleIcon color="success" />
                        </ListItemIcon>
                        <ListItemText
                          primary={strategy}
                          primaryTypographyProps={{ variant: 'body1' }}
                        />
                      </ListItem>
                      {index < remediationData.mitigation_strategies.length - 1 && <Divider />}
                    </Box>
                  ))}
                </List>
              ) : (
                <Alert severity="info">
                  No specific mitigation strategies needed for this resource
                </Alert>
              )}
            </AccordionDetails>
          </Accordion>

          {/* Monitoring Recommendations */}
          <Accordion defaultExpanded sx={{ mt: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box display="flex" alignItems="center" gap={2}>
                <MonitoringIcon color="primary" />
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    Monitoring Recommendations
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {remediationData.monitoring_recommendations.length} recommendation{remediationData.monitoring_recommendations.length !== 1 ? 's' : ''}
                  </Typography>
                </Box>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {remediationData.monitoring_recommendations.length > 0 ? (
                <List>
                  {remediationData.monitoring_recommendations.map((rec, index) => (
                    <Box key={index}>
                      <ListItem>
                        <ListItemIcon>
                          <MonitoringIcon color="info" />
                        </ListItemIcon>
                        <ListItemText
                          primary={rec}
                          primaryTypographyProps={{ variant: 'body1' }}
                        />
                      </ListItem>
                      {index < remediationData.monitoring_recommendations.length - 1 && <Divider />}
                    </Box>
                  ))}
                </List>
              ) : (
                <Alert severity="info">
                  Standard monitoring should be sufficient for this resource
                </Alert>
              )}
            </AccordionDetails>
          </Accordion>

          {/* Dependency Vulnerabilities */}
          {remediationData.dependency_vulnerabilities.length > 0 && (
            <Accordion defaultExpanded sx={{ mt: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" gap={2}>
                  <VulnerabilityIcon color="error" />
                  <Box>
                    <Typography variant="h6" fontWeight={600}>
                      Dependency Vulnerabilities
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {remediationData.dependency_vulnerabilities.length} vulnerabilit{remediationData.dependency_vulnerabilities.length !== 1 ? 'ies' : 'y'} found
                    </Typography>
                  </Box>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  {remediationData.dependency_vulnerabilities.map((vuln, index) => (
                    <Grid size={{ xs: 12 }} key={index}>
                      <Card sx={{ background: '#132f4c' }}>
                        <CardContent>
                          <Box display="flex" alignItems="flex-start" justifyContent="space-between" mb={2}>
                            <Box>
                              <Typography variant="h6" fontWeight={600}>
                                {vuln.package_name} {vuln.current_version}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {vuln.vulnerability_id}
                              </Typography>
                            </Box>
                            <Chip
                              label={vuln.severity.toUpperCase()}
                              color={getSeverityColor(vuln.severity) as 'error' | 'warning' | 'info' | 'success'}
                              size="small"
                            />
                          </Box>
                          <Typography variant="body2" paragraph>
                            {vuln.description}
                          </Typography>
                          {vuln.fixed_version && (
                            <Alert severity="success" sx={{ mt: 2 }}>
                              <strong>Fix Available:</strong> Upgrade to version {vuln.fixed_version}
                            </Alert>
                          )}
                          {vuln.exploit_available && (
                            <Alert severity="error" sx={{ mt: 2 }}>
                              <strong>Warning:</strong> Public exploit is available for this vulnerability
                            </Alert>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </AccordionDetails>
            </Accordion>
          )}
        </>
      )}

      {/* Empty State */}
      {!remediationData && !loading && (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <BuildIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Select a resource to view automated remediation suggestions
          </Typography>
        </Paper>
      )}
    </Box>
  );
}
