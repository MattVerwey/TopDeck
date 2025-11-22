/**
 * Risk Drilldown Dialog
 * 
 * Shows detailed list of resources filtered by risk level
 */

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Collapse,
  Divider,
} from '@mui/material';
import {
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  Link as LinkIcon,
} from '@mui/icons-material';
import { useStore } from '../../store/useStore';
import apiClient from '../../services/api';
import type { RiskAssessment } from '../../types';
import { getRiskLevelFromScore, getRiskColor } from '../../utils/riskUtils';

interface RiskDrilldownDialogProps {
  open: boolean;
  onClose: () => void;
  riskLevel: 'critical' | 'high' | 'medium' | 'low';
  cachedRisks?: RiskAssessment[]; // Accept cached risk data from parent
}

export default function RiskDrilldownDialog({
  open,
  onClose,
  riskLevel,
  cachedRisks,
}: RiskDrilldownDialogProps) {
  const { topology } = useStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [risks, setRisks] = useState<RiskAssessment[]>([]);
  const [expandedResourceId, setExpandedResourceId] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      loadRisks();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, riskLevel, cachedRisks]);

  const loadRisks = async () => {
    setLoading(true);
    setError(null);

    try {
      let allRisks: RiskAssessment[] = [];

      // Use cached data if available
      if (cachedRisks && cachedRisks.length > 0) {
        console.log(`Using ${cachedRisks.length} cached risk assessments`);
        allRisks = cachedRisks;
      } else if (topology?.nodes) {
        // Fallback: Fetch risk assessments for all resources
        console.log('No cached data, fetching risk assessments...');
        const assessments = await Promise.allSettled(
          topology.nodes.map(node => apiClient.getRiskAssessment(node.id))
        );

        allRisks = assessments
          .filter((result): result is PromiseFulfilledResult<RiskAssessment> => 
            result.status === 'fulfilled'
          )
          .map(result => result.value);
      }

      // Filter by risk level - normalize both sides for case-insensitive comparison
      const filteredRisks = allRisks.filter(risk => {
        // Normalize both values for comparison to handle case sensitivity and missing data
        const riskLevel_normalized = (risk.risk_level?.toLowerCase() || getRiskLevelFromScore(risk.risk_score)).toLowerCase();
        const targetLevel_normalized = riskLevel.toLowerCase();
        return riskLevel_normalized === targetLevel_normalized;
      });

      console.log(`Found ${filteredRisks.length} resources with ${riskLevel} risk level out of ${allRisks.length} total resources`);
      
      // Sort by risk score descending to show most critical first
      filteredRisks.sort((a, b) => b.risk_score - a.risk_score);
      
      setRisks(filteredRisks);
    } catch (err) {
      console.error('Failed to load risks:', err);
      setError('Failed to load risk details');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleExpand = (resourceId: string) => {
    setExpandedResourceId(expandedResourceId === resourceId ? null : resourceId);
  };

  const title = `${riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)} Risk Resources`;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
        },
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6" fontWeight={600}>
            {title}
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        {loading && (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
          </Box>
        )}

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {!loading && !error && risks.length === 0 && (
          <Alert severity="info">
            No resources found with {riskLevel} risk level.
          </Alert>
        )}

        {!loading && !error && risks.length > 0 && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Found {risks.length} resource{risks.length !== 1 ? 's' : ''} with {riskLevel} risk level
            </Typography>
            <Box sx={{ maxHeight: '60vh', overflowY: 'auto' }}>
              {risks.map((risk) => (
                <Card 
                  key={risk.resource_id} 
                  sx={{ 
                    mb: 2, 
                    background: '#0a1929',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': {
                      boxShadow: 4,
                      borderColor: getRiskColor(riskLevel) === 'error' ? 'error.main' :
                                   getRiskColor(riskLevel) === 'warning' ? 'warning.main' :
                                   getRiskColor(riskLevel) === 'info' ? 'info.main' : 'success.main',
                    },
                  }}
                  onClick={() => handleToggleExpand(risk.resource_id)}
                >
                  <CardContent>
                    {/* Header Section */}
                    <Box display="flex" alignItems="flex-start" justifyContent="space-between" mb={2}>
                      <Box flex={1}>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="h6" fontWeight={600}>
                            {risk.resource_name || risk.resource_id}
                          </Typography>
                          <IconButton 
                            size="small"
                            sx={{ ml: 'auto' }}
                          >
                            {expandedResourceId === risk.resource_id ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </IconButton>
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {risk.resource_type || 'Unknown Type'}
                        </Typography>
                      </Box>
                      <Chip
                        label={riskLevel.toUpperCase()}
                        size="small"
                        color={getRiskColor(riskLevel) as 'error' | 'warning' | 'info' | 'success'}
                        sx={{ fontWeight: 600 }}
                      />
                    </Box>

                    {/* Quick Stats - Always Visible */}
                    <Box display="flex" gap={2} flexWrap="wrap" mb={2}>
                      <Chip
                        label={`Risk Score: ${(risk.risk_score !== null && risk.risk_score !== undefined) ? risk.risk_score.toFixed(1) : 'N/A'}`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={`Blast Radius: ${risk.blast_radius}`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={`Dependencies: ${risk.dependencies_count}`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={`Dependents: ${risk.dependents_count}`}
                        size="small"
                        variant="outlined"
                      />
                      {risk.single_point_of_failure && (
                        <Chip
                          label="SPOF"
                          size="small"
                          color="error"
                          variant="outlined"
                        />
                      )}
                    </Box>

                    {/* Expandable Details Section */}
                    <Collapse in={expandedResourceId === risk.resource_id} timeout="auto" unmountOnExit>
                      <Divider sx={{ my: 2 }} />
                      
                      {/* Why This is Risky Section */}
                      <Box mb={3}>
                        <Box display="flex" alignItems="center" gap={1} mb={1.5}>
                          <WarningIcon color="warning" fontSize="small" />
                          <Typography variant="subtitle2" fontWeight={600}>
                            Why This is Risky
                          </Typography>
                        </Box>
                        <Box component="ul" sx={{ pl: 3, mt: 0, mb: 2 }}>
                          {risk.single_point_of_failure && (
                            <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                              <strong>Single Point of Failure:</strong> No redundancy - if this fails, dependent services will be affected
                            </Typography>
                          )}
                          {risk.blast_radius > 10 && (
                            <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                              <strong>Large Blast Radius:</strong> Failure would impact {risk.blast_radius} resources
                            </Typography>
                          )}
                          {risk.dependents_count > 5 && (
                            <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                              <strong>High Dependency:</strong> {risk.dependents_count} services depend on this resource
                            </Typography>
                          )}
                          {risk.deployment_failure_rate && risk.deployment_failure_rate > 0.1 && (
                            <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                              <strong>Deployment Risk:</strong> {(risk.deployment_failure_rate * 100).toFixed(1)}% failure rate in deployments
                            </Typography>
                          )}
                          {risk.misconfiguration_count && risk.misconfiguration_count > 0 && (
                            <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                              <strong>Misconfigurations Detected:</strong> {risk.misconfiguration_count} configuration issue{risk.misconfiguration_count !== 1 ? 's' : ''} found
                            </Typography>
                          )}
                        </Box>
                      </Box>

                      {/* Misconfigurations */}
                      {risk.misconfigurations && risk.misconfigurations.length > 0 && (
                        <Box mb={3}>
                          <Box display="flex" alignItems="center" gap={1} mb={1.5}>
                            <LinkIcon color="error" fontSize="small" />
                            <Typography variant="subtitle2" fontWeight={600}>
                              Configuration Issues
                            </Typography>
                          </Box>
                          <Box>
                            {risk.misconfigurations.map((config, idx) => (
                              <Card key={idx} sx={{ mb: 1, bgcolor: 'rgba(244, 67, 54, 0.1)' }}>
                                <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                                  <Typography variant="body2" fontWeight={600} color="error.light" gutterBottom>
                                    {config.type || 'Configuration Issue'}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {config.description || config.message || 'Misconfiguration detected'}
                                  </Typography>
                                  {config.severity && (
                                    <Chip
                                      label={config.severity}
                                      size="small"
                                      color="error"
                                      variant="outlined"
                                      sx={{ mt: 1 }}
                                    />
                                  )}
                                </CardContent>
                              </Card>
                            ))}
                          </Box>
                        </Box>
                      )}

                      {/* Risk Factors */}
                      {risk.factors && Object.keys(risk.factors).length > 0 && (
                        <Box mb={3}>
                          <Box display="flex" alignItems="center" gap={1} mb={1.5}>
                            <TrendingUpIcon color="info" fontSize="small" />
                            <Typography variant="subtitle2" fontWeight={600}>
                              Risk Factors
                            </Typography>
                          </Box>
                          <Box display="flex" gap={1} flexWrap="wrap">
                            {Object.entries(risk.factors).map(([key, value]) => (
                              <Chip
                                key={key}
                                label={`${key}: ${typeof value === 'number' ? value.toFixed(2) : value}`}
                                size="small"
                                variant="outlined"
                                color="info"
                              />
                            ))}
                          </Box>
                        </Box>
                      )}

                      {/* Recommendations - Full List */}
                      {risk.recommendations && risk.recommendations.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" fontWeight={600} gutterBottom color="success.light">
                            Recommendations to Reduce Risk
                          </Typography>
                          <Box component="ul" sx={{ pl: 3, mt: 1, mb: 0 }}>
                            {risk.recommendations.map((rec, idx) => (
                              <Typography
                                key={idx}
                                component="li"
                                variant="body2"
                                color="text.secondary"
                                sx={{ mb: 0.5 }}
                              >
                                {rec}
                              </Typography>
                            ))}
                          </Box>
                        </Box>
                      )}

                      {/* Hint to click */}
                      <Box mt={2} pt={2} borderTop="1px solid" borderColor="divider">
                        <Typography variant="caption" color="primary.light" sx={{ fontStyle: 'italic' }}>
                          Click again to collapse details
                        </Typography>
                      </Box>
                    </Collapse>

                    {/* Hint to expand when collapsed */}
                    {expandedResourceId !== risk.resource_id && (
                      <Typography variant="caption" color="primary.light" sx={{ fontStyle: 'italic', display: 'block', mt: 1 }}>
                        Click to see why this resource is risky →
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}
