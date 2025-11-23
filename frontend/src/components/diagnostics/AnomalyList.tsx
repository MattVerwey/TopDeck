/**
 * Anomaly List Component
 * 
 * Displays list of detected anomalies with severity filtering
 */

import {
  Box,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Typography,
  Stack,
} from '@mui/material';
import { Warning, Error as ErrorIcon, Info, BugReport } from '@mui/icons-material';
import type { AnomalyAlert } from '../../types/diagnostics';

interface AnomalyListProps {
  anomalies: AnomalyAlert[];
  onAnomalyClick: (anomaly: AnomalyAlert) => void;
}

export default function AnomalyList({ anomalies, onAnomalyClick }: AnomalyListProps) {
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'high':
        return <ErrorIcon color="error" />;
      case 'medium':
        return <Warning color="warning" />;
      case 'low':
        return <Info color="info" />;
      default:
        return <BugReport />;
    }
  };

  const getSeverityColor = (severity: string): 'default' | 'error' | 'warning' | 'info' => {
    switch (severity) {
      case 'critical':
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  if (anomalies.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Typography variant="body1" color="textSecondary">
          No anomalies detected
        </Typography>
      </Box>
    );
  }

  return (
    <Paper>
      <List>
        {anomalies.map((anomaly) => (
          <ListItem 
            key={anomaly.alert_id} 
            component="button"
            onClick={() => onAnomalyClick(anomaly)}
          >
            <ListItemIcon>{getSeverityIcon(anomaly.severity)}</ListItemIcon>
            <ListItemText
              primary={
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography variant="subtitle1">{anomaly.resource_name}</Typography>
                  <Chip
                    size="small"
                    label={anomaly.severity}
                    color={getSeverityColor(anomaly.severity)}
                  />
                  <Chip size="small" label={anomaly.metric_name} variant="outlined" />
                </Stack>
              }
              secondary={
                <Box>
                  <Typography variant="body2" color="textSecondary">
                    {anomaly.message}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Deviation: {anomaly.deviation_percentage.toFixed(1)}% | Current:{' '}
                    {anomaly.current_value.toFixed(2)} | Expected:{' '}
                    {anomaly.expected_value.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="textSecondary" display="block">
                    Detected: {new Date(anomaly.detected_at).toLocaleString()}
                  </Typography>
                  {anomaly.potential_causes.length > 0 && (
                    <Typography variant="caption" color="textSecondary" display="block">
                      Possible causes: {anomaly.potential_causes.join(', ')}
                    </Typography>
                  )}
                </Box>
              }
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
}
