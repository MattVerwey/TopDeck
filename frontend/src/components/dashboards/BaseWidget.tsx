/**
 * Base Widget Component
 * 
 * Base component for all dashboard widgets, providing common functionality
 * like refresh, error handling, and configuration.
 */

import { ReactNode, useState, useEffect } from 'react';
import {
  Paper,
  Box,
  Typography,
  IconButton,
  CircularProgress,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

export interface WidgetPosition {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface WidgetConfig {
  id: string;
  type: string;
  title: string;
  position: WidgetPosition;
  config: Record<string, any>;
  refresh_interval?: number;
}

interface BaseWidgetProps {
  config: WidgetConfig;
  onRefresh?: () => void;
  onRemove?: () => void;
  onConfigure?: () => void;
  loading?: boolean;
  error?: string | null;
  children: ReactNode;
}

export default function BaseWidget({
  config,
  onRefresh,
  onRemove,
  onConfigure,
  loading = false,
  error = null,
  children,
}: BaseWidgetProps) {
  const [autoRefresh] = useState(true);

  // Auto-refresh functionality
  useEffect(() => {
    if (!autoRefresh || !onRefresh || !config.refresh_interval) {
      return;
    }

    const interval = setInterval(() => {
      onRefresh();
    }, config.refresh_interval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, onRefresh, config.refresh_interval]);

  return (
    <Paper
      elevation={2}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Widget Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 1.5,
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.default',
        }}
      >
        <Typography variant="subtitle1" fontWeight="medium">
          {config.title}
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {onRefresh && (
            <Tooltip title="Refresh">
              <IconButton
                size="small"
                onClick={onRefresh}
                disabled={loading}
              >
                <RefreshIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {onConfigure && (
            <Tooltip title="Configure">
              <IconButton size="small" onClick={onConfigure}>
                <SettingsIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {onRemove && (
            <Tooltip title="Remove">
              <IconButton size="small" onClick={onRemove} color="error">
                <CloseIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      {/* Widget Content */}
      <Box
        sx={{
          flex: 1,
          position: 'relative',
          overflow: 'auto',
          p: 2,
        }}
      >
        {loading && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: 'background.paper',
              zIndex: 1,
              opacity: 0.9,
            }}
          >
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!loading && !error && children}
      </Box>
    </Paper>
  );
}
