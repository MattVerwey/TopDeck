/**
 * Transaction Flow Dialog Component
 * 
 * Displays a dialog for selecting correlation IDs and visualizing transaction flows
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
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Chip,
  Stack,
  Divider,
  Paper,
} from '@mui/material';
import {
  Timeline,
  Error as ErrorIcon,
  Warning as WarningIcon,
  CheckCircle as SuccessIcon,
} from '@mui/icons-material';
import apiClient from '../../services/api';
import type { TransactionFlow } from '../../types';
import TransactionFlowGraph from './TransactionFlowGraph';

interface TransactionFlowDialogProps {
  open: boolean;
  onClose: () => void;
  resourceId: string;
  resourceName: string;
}

export default function TransactionFlowDialog({
  open,
  onClose,
  resourceId,
  resourceName,
}: TransactionFlowDialogProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [correlationIds, setCorrelationIds] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [flow, setFlow] = useState<TransactionFlow | null>(null);
  const [loadingFlow, setLoadingFlow] = useState(false);

  useEffect(() => {
    if (open && resourceId) {
      loadCorrelationIds();
    }
  }, [open, resourceId]);

  const loadCorrelationIds = async () => {
    setLoading(true);
    setError(null);
    try {
      const ids = await apiClient.getResourceCorrelationIds(resourceId, 1);
      setCorrelationIds(ids);
      if (ids.length === 0) {
        setError('No transaction IDs found for this resource in the last hour.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load correlation IDs');
    } finally {
      setLoading(false);
    }
  };

  const loadFlow = async (correlationId: string) => {
    setLoadingFlow(true);
    setError(null);
    try {
      const flowData = await apiClient.traceTransactionFlow(correlationId, 1, 'auto', true);
      setFlow(flowData);
      setSelectedId(correlationId);
    } catch (err: any) {
      setError(err.message || 'Failed to load transaction flow');
      setFlow(null);
    } finally {
      setLoadingFlow(false);
    }
  };

  const handleSelectId = (id: string) => {
    loadFlow(id);
  };

  const handleClose = () => {
    setCorrelationIds([]);
    setSelectedId(null);
    setFlow(null);
    setError(null);
    onClose();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <SuccessIcon color="success" fontSize="small" />;
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      case 'partial':
        return <WarningIcon color="warning" fontSize="small" />;
      default:
        return <Timeline fontSize="small" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'partial':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: { height: '90vh' },
      }}
    >
      <DialogTitle>
        <Stack direction="row" alignItems="center" spacing={2}>
          <Timeline />
          <Box>
            <Typography variant="h6">Transaction Flow Visualization</Typography>
            <Typography variant="caption" color="text.secondary">
              {resourceName}
            </Typography>
          </Box>
        </Stack>
      </DialogTitle>

      <DialogContent dividers>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', height: '100%', gap: 2 }}>
          {/* Left Sidebar - Correlation ID Selection */}
          <Paper
            elevation={0}
            sx={{
              width: 300,
              flexShrink: 0,
              border: 1,
              borderColor: 'divider',
              overflow: 'auto',
            }}
          >
            <Box sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Transaction/Correlation IDs
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Select a transaction to visualize its flow
              </Typography>
            </Box>

            <Divider />

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress size={32} />
              </Box>
            ) : correlationIds.length > 0 ? (
              <List dense>
                {correlationIds.map((id) => (
                  <ListItem key={id} disablePadding>
                    <ListItemButton
                      selected={selectedId === id}
                      onClick={() => handleSelectId(id)}
                    >
                      <ListItemText
                        primary={
                          <Typography
                            variant="body2"
                            sx={{
                              fontFamily: 'monospace',
                              fontSize: '0.75rem',
                              wordBreak: 'break-all',
                            }}
                          >
                            {id}
                          </Typography>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            ) : (
              <Box sx={{ p: 2 }}>
                <Typography variant="body2" color="text.secondary" align="center">
                  No transaction IDs found
                </Typography>
              </Box>
            )}
          </Paper>

          {/* Main Content - Flow Visualization */}
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            {loadingFlow ? (
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: '100%',
                }}
              >
                <CircularProgress />
              </Box>
            ) : flow ? (
              <>
                {/* Flow Summary */}
                <Paper
                  elevation={0}
                  sx={{ p: 2, mb: 2, border: 1, borderColor: 'divider' }}
                >
                  <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
                    <Chip
                      icon={getStatusIcon(flow.status)}
                      label={flow.status.toUpperCase()}
                      color={getStatusColor(flow.status) as any}
                      size="small"
                    />
                    <Typography variant="body2">
                      <strong>Duration:</strong> {flow.total_duration_ms.toFixed(2)}ms
                    </Typography>
                    <Typography variant="body2">
                      <strong>Nodes:</strong> {flow.nodes.length}
                    </Typography>
                    {flow.error_count > 0 && (
                      <Typography variant="body2" color="error.main">
                        <strong>Errors:</strong> {flow.error_count}
                      </Typography>
                    )}
                    {flow.warning_count > 0 && (
                      <Typography variant="body2" color="warning.main">
                        <strong>Warnings:</strong> {flow.warning_count}
                      </Typography>
                    )}
                    <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                      Source: {flow.source}
                    </Typography>
                  </Stack>
                </Paper>

                {/* Flow Graph */}
                <Paper
                  elevation={0}
                  sx={{
                    flex: 1,
                    border: 1,
                    borderColor: 'divider',
                    overflow: 'hidden',
                    position: 'relative',
                  }}
                >
                  <TransactionFlowGraph flow={flow} />
                </Paper>
              </>
            ) : (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: '100%',
                  color: 'text.secondary',
                }}
              >
                <Timeline sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />
                <Typography variant="body1">
                  Select a transaction ID to visualize its flow
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
