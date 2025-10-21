/**
 * Error Display Component
 * 
 * Displays API errors in a user-friendly format with retry capability.
 */

import { Alert, AlertTitle, Box, Button, Typography } from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import { ApiError } from '../../services/api';

interface ErrorDisplayProps {
  error: Error | ApiError | unknown;
  onRetry?: () => void;
  title?: string;
}

export default function ErrorDisplay({ error, onRetry, title = 'Error' }: ErrorDisplayProps) {
  let errorMessage = 'An unexpected error occurred';
  let errorCode: string | undefined;
  let requestId: string | undefined;

  if (error instanceof ApiError) {
    errorMessage = error.message;
    errorCode = error.code;
    requestId = error.requestId;
  } else if (error instanceof Error) {
    errorMessage = error.message;
  } else if (typeof error === 'string') {
    errorMessage = error;
  }

  return (
    <Alert severity="error" sx={{ mb: 2 }}>
      <AlertTitle>{title}</AlertTitle>
      <Typography variant="body2" paragraph>
        {errorMessage}
      </Typography>
      
      {errorCode && (
        <Typography variant="caption" display="block" color="text.secondary" gutterBottom>
          Error Code: {errorCode}
        </Typography>
      )}
      
      {requestId && (
        <Typography variant="caption" display="block" color="text.secondary" gutterBottom>
          Request ID: {requestId}
        </Typography>
      )}

      {onRetry && (
        <Box sx={{ mt: 2 }}>
          <Button
            size="small"
            startIcon={<RefreshIcon />}
            onClick={onRetry}
            variant="outlined"
          >
            Retry
          </Button>
        </Box>
      )}
    </Alert>
  );
}
