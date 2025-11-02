/**
 * Resource list component with filtering and sorting
 */

import { useState, useMemo } from 'react';
import {
  Box,
  Grid,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Typography,
  Chip,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import type { Resource } from '../../types';
import ResourceCard from './ResourceCard';

interface ResourceListProps {
  resources: Resource[];
  onResourceClick?: (resource: Resource) => void;
  selectedResourceIds?: string[];
  compact?: boolean;
  columns?: { xs: number; sm: number; md: number; lg: number };
}

export default function ResourceList({
  resources,
  onResourceClick,
  selectedResourceIds = [],
  compact = false,
  columns = { xs: 12, sm: 6, md: 4, lg: 3 },
}: ResourceListProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterProvider, setFilterProvider] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('name');

  // Extract unique providers and types
  const providers = useMemo(() => {
    return [...new Set(resources.map((r) => r.cloud_provider))].sort();
  }, [resources]);

  const resourceTypes = useMemo(() => {
    return [...new Set(resources.map((r) => r.resource_type))].sort();
  }, [resources]);

  // Filter and sort resources
  const filteredResources = useMemo(() => {
    let filtered = resources;

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (r) =>
          r.name.toLowerCase().includes(term) ||
          r.resource_type.toLowerCase().includes(term) ||
          r.id.toLowerCase().includes(term)
      );
    }

    // Apply provider filter
    if (filterProvider !== 'all') {
      filtered = filtered.filter((r) => r.cloud_provider === filterProvider);
    }

    // Apply type filter
    if (filterType !== 'all') {
      filtered = filtered.filter((r) => r.resource_type === filterType);
    }

    // Apply sorting
    filtered = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'type':
          return a.resource_type.localeCompare(b.resource_type);
        case 'provider':
          return a.cloud_provider.localeCompare(b.cloud_provider);
        default:
          return 0;
      }
    });

    return filtered;
  }, [resources, searchTerm, filterProvider, filterType, sortBy]);

  return (
    <Box>
      {/* Filters and search */}
      <Stack spacing={2} mb={3}>
        <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
          <TextField
            placeholder="Search resources..."
            size="small"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 250, flex: 1 }}
          />

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Cloud Provider</InputLabel>
            <Select
              value={filterProvider}
              label="Cloud Provider"
              onChange={(e) => setFilterProvider(e.target.value)}
            >
              <MenuItem value="all">All Providers</MenuItem>
              {providers.map((provider) => (
                <MenuItem key={provider} value={provider}>
                  {provider.toUpperCase()}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Resource Type</InputLabel>
            <Select
              value={filterType}
              label="Resource Type"
              onChange={(e) => setFilterType(e.target.value)}
            >
              <MenuItem value="all">All Types</MenuItem>
              {resourceTypes.map((type) => (
                <MenuItem key={type} value={type}>
                  {type}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 130 }}>
            <InputLabel>Sort By</InputLabel>
            <Select
              value={sortBy}
              label="Sort By"
              onChange={(e) => setSortBy(e.target.value)}
            >
              <MenuItem value="name">Name</MenuItem>
              <MenuItem value="type">Type</MenuItem>
              <MenuItem value="provider">Provider</MenuItem>
            </Select>
          </FormControl>
        </Stack>

        {/* Results summary */}
        <Box display="flex" alignItems="center" gap={1}>
          <Typography variant="body2" color="text.secondary">
            Showing {filteredResources.length} of {resources.length} resources
          </Typography>
          {selectedResourceIds.length > 0 && (
            <Chip
              label={`${selectedResourceIds.length} selected`}
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
        </Box>
      </Stack>

      {/* Resource grid */}
      {filteredResources.length > 0 ? (
        <Grid container spacing={2}>
          {filteredResources.map((resource) => (
            <Grid key={resource.id} size={columns}>
              <ResourceCard
                resource={resource}
                onClick={onResourceClick ? () => onResourceClick(resource) : undefined}
                selected={selectedResourceIds.includes(resource.id)}
                compact={compact}
              />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Box
          sx={{
            p: 4,
            textAlign: 'center',
            border: '2px dashed',
            borderColor: 'divider',
            borderRadius: 2,
          }}
        >
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No resources found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your filters or search term
          </Typography>
        </Box>
      )}
    </Box>
  );
}
