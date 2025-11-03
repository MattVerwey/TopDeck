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
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { useStore } from '../../store/useStore';
import apiClient from '../../services/api';
import type { RiskAssessment } from '../../types';

interface RiskDrilldownDialogProps {
  open: boolean;
  onClose: () => void;
  riskLevel: 'critical' | 'high' | 'medium' | 'low';
}

export default function RiskDrilldownDialog({
  open,
  onClose,
  riskLevel,
}: RiskDrilldownDialogProps) {
  const { topology } = useStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [risks, setRisks] = useState<RiskAssessment[]>([]);

  useEffect(() => {
    if (open && topology?.nodes) {
      loadRisks();
    }
  }, [open, riskLevel, topology?.nodes]);

  const loadRisks = async () => {
    if (!topology?.nodes) return;

    setLoading(true);
    setError(null);

    try {
      // Fetch risk assessments for all resources
      const assessments = await Promise.allSettled(
        topology.nodes.map(node => apiClient.getRiskAssessment(node.id))
      );

      // Filter successful results and match risk level
      const allRisks = assessments
        .filter((result): result is PromiseFulfilledResult<RiskAssessment> => 
          result.status === 'fulfilled'
        )
        .map(result => result.value)
        .filter(risk => {
          const level = risk.risk_level?.toLowerCase() || getRiskLevelFromScore(risk.risk_score);
          return level === riskLevel;
        });

      setRisks(allRisks);
    } catch (err) {
      console.error('Failed to load risks:', err);
      setError('Failed to load risk details');
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevelFromScore = (score: number): string => {
    if (score >= 80) return 'critical';
    if (score >= 60) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  };

  const getRiskColor = (level: string) => {
    switch (level) {
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
                <Card key={risk.resource_id} sx={{ mb: 2, background: '#0a1929' }}>
                  <CardContent>
                    <Box display="flex" alignItems="flex-start" justifyContent="space-between" mb={2}>
                      <Box>
                        <Typography variant="h6" fontWeight={600}>
                          {risk.resource_name || risk.resource_id}
                        </Typography>
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

                    <Box display="flex" gap={2} flexWrap="wrap" mb={2}>
                      <Chip
                        label={`Risk Score: ${risk.risk_score.toFixed(1)}`}
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

                    {risk.recommendations && risk.recommendations.length > 0 && (
                      <Box>
                        <Typography variant="body2" fontWeight={600} gutterBottom>
                          Recommendations:
                        </Typography>
                        <Box component="ul" sx={{ pl: 2, mt: 0.5 }}>
                          {risk.recommendations.slice(0, 2).map((rec, idx) => (
                            <Typography
                              key={idx}
                              component="li"
                              variant="caption"
                              color="text.secondary"
                            >
                              {rec}
                            </Typography>
                          ))}
                        </Box>
                      </Box>
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
