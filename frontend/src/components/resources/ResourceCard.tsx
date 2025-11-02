/**
 * Enhanced resource card component with visual hierarchy and metadata display
 */

import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  Tooltip,
  Avatar,
} from '@mui/material';
import {
  Cloud as CloudIcon,
  Storage as StorageIcon,
  AccountTree as ServiceIcon,
  Dataset as DatabaseIcon,
  Router as LoadBalancerIcon,
  Circle as CircleIcon,
} from '@mui/icons-material';
import type { Resource } from '../../types';

interface ResourceCardProps {
  resource: Resource;
  onClick?: () => void;
  selected?: boolean;
  compact?: boolean;
}

const getResourceIcon = (resourceType: string) => {
  const type = resourceType.toLowerCase();
  if (type.includes('database') || type.includes('sql') || type.includes('cosmos')) {
    return <DatabaseIcon />;
  }
  if (type.includes('storage') || type.includes('blob')) {
    return <StorageIcon />;
  }
  if (type.includes('gateway') || type.includes('load_balancer') || type.includes('alb')) {
    return <LoadBalancerIcon />;
  }
  if (type.includes('service') || type.includes('app') || type.includes('aks') || type.includes('eks')) {
    return <ServiceIcon />;
  }
  return <CloudIcon />;
};

const getCloudProviderColor = (provider: string) => {
  switch (provider.toLowerCase()) {
    case 'azure':
      return '#0078D4';
    case 'aws':
      return '#FF9900';
    case 'gcp':
      return '#4285F4';
    default:
      return '#666';
  }
};

const getHealthStatus = (resource: Resource) => {
  const hasIssues = resource.properties?.hasIssues || resource.metadata?.hasIssues;
  if (hasIssues) return { status: 'error', label: 'Unhealthy', color: 'error' as const };
  
  const isWarning = resource.properties?.warning || resource.metadata?.warning;
  if (isWarning) return { status: 'warning', label: 'Warning', color: 'warning' as const };
  
  return { status: 'success', label: 'Healthy', color: 'success' as const };
};

export default function ResourceCard({ resource, onClick, selected = false, compact = false }: ResourceCardProps) {
  const healthStatus = getHealthStatus(resource);
  const providerColor = getCloudProviderColor(resource.cloud_provider);

  const getMetadataChips = () => {
    const chips = [];
    
    if (resource.metadata?.region && typeof resource.metadata.region === 'string') {
      chips.push(
        <Chip
          key="region"
          label={resource.metadata.region}
          size="small"
          variant="outlined"
          sx={{ fontSize: '0.7rem' }}
        />
      );
    }
    
    if (resource.properties?.cluster) {
      chips.push(
        <Chip
          key="cluster"
          label={`Cluster: ${String(resource.properties.cluster)}`}
          size="small"
          variant="outlined"
          sx={{ fontSize: '0.7rem' }}
        />
      );
    }
    
    if (resource.metadata?.namespace) {
      chips.push(
        <Chip
          key="namespace"
          label={`NS: ${String(resource.metadata.namespace)}`}
          size="small"
          variant="outlined"
          sx={{ fontSize: '0.7rem' }}
        />
      );
    }
    
    return chips;
  };

  return (
    <Card
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s ease-in-out',
        border: selected ? '2px solid #2196f3' : '1px solid rgba(255, 255, 255, 0.12)',
        '&:hover': onClick ? {
          transform: 'translateY(-2px)',
          boxShadow: 4,
          borderColor: 'primary.main',
        } : {},
        background: selected 
          ? 'linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(33, 150, 243, 0.05) 100%)'
          : 'linear-gradient(135deg, #132f4c 0%, #1a3e5e 100%)',
      }}
      onClick={onClick}
    >
      <CardContent sx={{ p: compact ? 2 : 3, '&:last-child': { pb: compact ? 2 : 3 } }}>
        <Box display="flex" flexDirection="column" gap={compact ? 1 : 2}>
          <Box display="flex" alignItems="flex-start" gap={2}>
            <Avatar
              sx={{
                bgcolor: providerColor,
                width: compact ? 40 : 48,
                height: compact ? 40 : 48,
              }}
            >
              {getResourceIcon(resource.resource_type)}
            </Avatar>
            <Box flex={1} minWidth={0}>
              <Tooltip title={resource.name} arrow>
                <Typography
                  variant={compact ? 'subtitle1' : 'h6'}
                  fontWeight={600}
                  noWrap
                  sx={{ mb: 0.5 }}
                >
                  {resource.name}
                </Typography>
              </Tooltip>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: '-webkit-box',
                  WebkitLineClamp: 1,
                  WebkitBoxOrient: 'vertical',
                }}
              >
                {resource.resource_type}
              </Typography>
            </Box>
          </Box>

          <Box display="flex" flexDirection="row" gap={1} flexWrap="wrap">
            <Chip
              icon={<CircleIcon sx={{ fontSize: 12 }} />}
              label={resource.cloud_provider.toUpperCase()}
              size="small"
              sx={{
                bgcolor: `${providerColor}20`,
                color: providerColor,
                fontWeight: 600,
                fontSize: '0.7rem',
              }}
            />
            <Chip
              label={healthStatus.label}
              size="small"
              color={healthStatus.color}
              sx={{
                fontWeight: 600,
                fontSize: '0.7rem',
              }}
            />
            {getMetadataChips()}
          </Box>

          {!compact && resource.properties?.description && typeof resource.properties.description === 'string' ? (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
              }}
            >
              {resource.properties.description}
            </Typography>
          ) : null}
        </Box>
      </CardContent>
    </Card>
  );
}
