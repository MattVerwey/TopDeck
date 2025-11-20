/**
 * Prediction Analysis Component
 * 
 * Displays resources that are predicted to fail or cause issues using ML-based predictions
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  TextField,
  MenuItem,
  Button,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon,
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useStore } from '../../store/useStore';
import apiClient from '../../services/api';

interface PredictionResult {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  prediction_type: 'failure' | 'performance' | 'anomaly';
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  confidence: 'low' | 'medium' | 'high';
  summary: string;
  details: Record<string, unknown>;
  recommendations: string[];
  predicted_at: string;
}

export default function PredictionAnalysis() {
  const { topology } = useStore();
  const [loading, setLoading] = useState(false);
  const [predictions, setPredictions] = useState<PredictionResult[]>([]);
  const [selectedRiskLevel, setSelectedRiskLevel] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [minConfidence, setMinConfidence] = useState<number | ''>('');
  const [minRiskScore, setMinRiskScore] = useState<number | ''>('');

  useEffect(() => {
    loadPredictions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topology]);

  const loadPredictions = async () => {
    setLoading(true);
    setError(null);
    try {
      const resources = topology?.nodes || [];
      
      if (resources.length === 0) {
        setPredictions([]);
        setLoading(false);
        return;
      }

      // Fetch predictions for a sample of resources (limit to prevent overload)
      const sampleResources = resources.slice(0, 10);
      const predictionPromises: Promise<PredictionResult | null>[] = [];

      for (const resource of sampleResources) {
        // Try to get failure prediction
        predictionPromises.push(
          apiClient
            .getFailurePrediction(resource.id, resource.name, resource.resource_type)
            .then((data) => ({
              resource_id: data.resource_id,
              resource_name: data.resource_name,
              resource_type: data.resource_type,
              prediction_type: 'failure' as const,
              risk_level: data.risk_level,
              confidence: data.confidence,
              summary: `Failure probability: ${(data.failure_probability * 100).toFixed(1)}%${
                data.time_to_failure_hours
                  ? `, Estimated time to failure: ${data.time_to_failure_hours}h`
                  : ''
              }`,
              details: {
                failure_probability: data.failure_probability,
                time_to_failure_hours: data.time_to_failure_hours,
                contributing_factors: data.contributing_factors,
              },
              recommendations: data.recommendations,
              predicted_at: data.predicted_at,
            }))
            .catch((err) => {
              console.warn('Failed to fetch prediction for resource:', resource.id, err);
              return null;
            })
        );
      }

      const results = await Promise.all(predictionPromises);
      const validPredictions = results.filter((p): p is PredictionResult => p !== null);

      // Filter to only show resources with issues (medium, high, or critical)
      const issuesOnly = validPredictions.filter(
        (p) => p.risk_level !== 'low'
      );

      setPredictions(issuesOnly);
    } catch (err) {
      console.error('Failed to load predictions:', err);
      setError('Failed to load predictions. Please try again.');
    } finally {
      setLoading(false);
    }
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

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'critical':
      case 'high':
        return <ErrorIcon />;
      case 'medium':
        return <WarningIcon />;
      default:
        return <CheckCircleIcon />;
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return '#4caf50';
      case 'medium':
        return '#ff9800';
      default:
        return '#757575';
    }
  };

  const filteredPredictions = predictions.filter((p) => {
    const matchesRiskLevel = selectedRiskLevel === 'all' || p.risk_level === selectedRiskLevel;
    const matchesType = selectedType === 'all' || p.prediction_type === selectedType;
    const matchesSearch =
      searchTerm === '' ||
      p.resource_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.resource_type.toLowerCase().includes(searchTerm.toLowerCase());
    
    // Map confidence to percentage for filtering
    const confidencePercentage = p.confidence === 'high' ? 100 : p.confidence === 'medium' ? 66 : 33;
    const matchesMinConfidence = minConfidence === '' || confidencePercentage >= minConfidence;
    
    // Get risk score from details if available (with type safety)
    const riskScore = typeof p.details.failure_probability === 'number'
      ? p.details.failure_probability * 100
      : 0;
    const matchesMinRiskScore = minRiskScore === '' || riskScore >= minRiskScore;
    
    return matchesRiskLevel && matchesType && matchesSearch && matchesMinConfidence && matchesMinRiskScore;
  });

  const summaryStats = {
    total: predictions.length,
    critical: predictions.filter((p) => p.risk_level === 'critical').length,
    high: predictions.filter((p) => p.risk_level === 'high').length,
    medium: predictions.filter((p) => p.risk_level === 'medium').length,
  };

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={1} mb={3}>
        <TrendingUpIcon color="primary" fontSize="large" />
        <Typography variant="h5" fontWeight={600}>
          Prediction-Based Analysis
        </Typography>
      </Box>

      <Typography variant="body2" color="text.secondary" paragraph>
        ML-powered predictions showing resources that are predicted to fail or cause issues
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
              cursor: 'pointer',
              transition: 'transform 0.2s, box-shadow 0.2s',
              border: selectedRiskLevel === 'all' ? '2px solid #2196f3' : '2px solid transparent',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 16px rgba(33, 150, 243, 0.3)',
              },
            }}
            onClick={() => setSelectedRiskLevel('all')}
          >
            <CardContent>
              <Typography variant="h4" fontWeight={700}>
                {summaryStats.total}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Issues Predicted
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
              borderLeft: '4px solid #f44336',
              cursor: 'pointer',
              transition: 'transform 0.2s, box-shadow 0.2s',
              border: selectedRiskLevel === 'critical' ? '2px solid #f44336' : '2px solid transparent',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 16px rgba(244, 67, 54, 0.3)',
              },
            }}
            onClick={() => setSelectedRiskLevel('critical')}
          >
            <CardContent>
              <Typography variant="h4" fontWeight={700} color="error">
                {summaryStats.critical}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Critical Risk
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
              borderLeft: '4px solid #ff9800',
              cursor: 'pointer',
              transition: 'transform 0.2s, box-shadow 0.2s',
              border: selectedRiskLevel === 'high' ? '2px solid #ff9800' : '2px solid transparent',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 16px rgba(255, 152, 0, 0.3)',
              },
            }}
            onClick={() => setSelectedRiskLevel('high')}
          >
            <CardContent>
              <Typography variant="h4" fontWeight={700} color="warning.main">
                {summaryStats.high}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                High Risk
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
              borderLeft: '4px solid #2196f3',
              cursor: 'pointer',
              transition: 'transform 0.2s, box-shadow 0.2s',
              border: selectedRiskLevel === 'medium' ? '2px solid #2196f3' : '2px solid transparent',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 16px rgba(33, 150, 243, 0.3)',
              },
            }}
            onClick={() => setSelectedRiskLevel('medium')}
          >
            <CardContent>
              <Typography variant="h4" fontWeight={700} color="info.main">
                {summaryStats.medium}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Medium Risk
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid size={{ xs: 12, md: 3 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search resources..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <TextField
              fullWidth
              select
              size="small"
              label="Risk Level"
              value={selectedRiskLevel}
              onChange={(e) => setSelectedRiskLevel(e.target.value)}
            >
              <MenuItem value="all">All Levels</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="low">Low</MenuItem>
            </TextField>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <TextField
              fullWidth
              select
              size="small"
              label="Prediction Type"
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
            >
              <MenuItem value="all">All Types</MenuItem>
              <MenuItem value="failure">Failure Prediction</MenuItem>
              <MenuItem value="performance">Performance Degradation</MenuItem>
              <MenuItem value="anomaly">Anomaly Detection</MenuItem>
            </TextField>
          </Grid>
          <Grid size={{ xs: 6, sm: 6, md: 2 }}>
            <TextField
              fullWidth
              size="small"
              type="number"
              label="Min Confidence %"
              value={minConfidence}
              onChange={(e) => setMinConfidence(e.target.value === '' ? '' : Number(e.target.value))}
              inputProps={{ min: 0, max: 100, step: 10 }}
            />
          </Grid>
          <Grid size={{ xs: 6, sm: 6, md: 2 }}>
            <TextField
              fullWidth
              size="small"
              type="number"
              label="Min Risk Score"
              value={minRiskScore}
              onChange={(e) => setMinRiskScore(e.target.value === '' ? '' : Number(e.target.value))}
              inputProps={{ min: 0, max: 100, step: 5 }}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 1 }}>
            <Button
              fullWidth
              variant="outlined"
              onClick={loadPredictions}
              disabled={loading}
            >
              Refresh
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Loading State */}
      {loading && (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
          <CircularProgress />
        </Box>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* No Data State */}
      {!loading && !error && predictions.length === 0 && (
        <Alert severity="info" icon={<InfoIcon />}>
          No resources with predicted issues found. This is good news! Your infrastructure appears healthy.
        </Alert>
      )}

      {/* No Filtered Results */}
      {!loading && !error && predictions.length > 0 && filteredPredictions.length === 0 && (
        <Alert severity="info">
          No predictions match your current filters. Try adjusting the filters above.
        </Alert>
      )}

      {/* Predictions List */}
      {!loading && !error && filteredPredictions.length > 0 && (
        <Box>
          {filteredPredictions.map((prediction, index) => (
            <Accordion key={`${prediction.resource_id}-${index}`} sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" gap={2} width="100%">
                  {getRiskIcon(prediction.risk_level)}
                  <Box flex={1}>
                    <Typography variant="h6" fontWeight={600}>
                      {prediction.resource_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {prediction.resource_type} • {prediction.summary}
                    </Typography>
                  </Box>
                  <Box display="flex" gap={1} alignItems="center">
                    <Chip
                      label={prediction.risk_level.toUpperCase()}
                      color={getRiskColor(prediction.risk_level) as 'error' | 'warning' | 'info' | 'success'}
                      size="small"
                    />
                    <Chip
                      label={`${prediction.confidence.toUpperCase()} CONFIDENCE`}
                      size="small"
                      sx={{
                        backgroundColor: getConfidenceColor(prediction.confidence),
                        color: 'white',
                      }}
                    />
                  </Box>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Box>
                  {/* Contributing Factors */}
                  {prediction.details.contributing_factors &&
                  Array.isArray(prediction.details.contributing_factors) &&
                  (prediction.details.contributing_factors as Array<{
                    factor: string;
                    importance: number;
                    description: string;
                  }>).length > 0 ? (
                    <Box>
                      <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                        Contributing Factors:
                      </Typography>
                      <List dense>
                        {(
                          prediction.details.contributing_factors as Array<{
                            factor: string;
                            importance: number;
                            description: string;
                          }>
                        ).map((factor, idx) => (
                          <ListItem key={idx}>
                            <Box width="100%">
                              <Box display="flex" justifyContent="space-between" mb={1}>
                                <Typography variant="body2">{factor.factor}</Typography>
                                <Typography variant="caption" color="text.secondary">
                                  Importance: {(factor.importance * 100).toFixed(0)}%
                                </Typography>
                              </Box>
                              <LinearProgress
                                variant="determinate"
                                value={factor.importance * 100}
                                sx={{ mb: 0.5, height: 4, borderRadius: 2 }}
                              />
                              <Typography variant="caption" color="text.secondary">
                                {factor.description}
                              </Typography>
                            </Box>
                          </ListItem>
                        ))}
                      </List>
                      <Divider sx={{ my: 2 }} />
                    </Box>
                  ) : null}

                  {/* Recommendations */}
                  {prediction.recommendations.length > 0 ? (
                    <Box>
                      <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                        Recommendations:
                      </Typography>
                      <List dense>
                        {prediction.recommendations.map((rec, idx) => (
                          <ListItem key={idx}>
                            <ListItemText
                              primary={rec}
                              primaryTypographyProps={{
                                variant: 'body2',
                              }}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  ) : null}

                  {/* Prediction Details */}
                  <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                    <Typography variant="caption" color="text.secondary">
                      Predicted at: {new Date(prediction.predicted_at).toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}
    </Box>
  );
}
