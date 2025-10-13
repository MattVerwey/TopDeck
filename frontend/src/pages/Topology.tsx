/**
 * Topology visualization page with filtering and interactive graph
 */

import { useEffect, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Stack,
  CircularProgress,
  Alert,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import { useStore } from '../store/useStore';
import apiClient from '../services/api';
import TopologyGraph from '../components/topology/TopologyGraph';

export default function Topology() {
  const {
    topology,
    filters,
    viewMode,
    setTopology,
    setFilters,
    setViewMode,
    setLoading,
    setError,
    loading,
    error,
  } = useStore();

  const [availableProviders, setAvailableProviders] = useState<string[]>([]);
  const [availableTypes, setAvailableTypes] = useState<string[]>([]);

  useEffect(() => {
    loadTopology();
  }, [filters]);

  const loadTopology = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getTopology(filters);
      setTopology(data);

      // Extract unique providers and types
      const providers = [...new Set(data.nodes.map((n) => n.cloud_provider))];
      const types = [...new Set(data.nodes.map((n) => n.resource_type))];
      setAvailableProviders(providers);
      setAvailableTypes(types);
    } catch (err: any) {
      setError(err.message || 'Failed to load topology');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters({ ...filters, [key]: value || undefined });
  };

  const handleViewModeChange = (event: SelectChangeEvent) => {
    setViewMode(event.target.value as any);
  };

  const clearFilters = () => {
    setFilters({});
  };

  const activeFilterCount = Object.keys(filters).filter((k) => filters[k as keyof typeof filters]).length;

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight={600}>
        Network Topology
      </Typography>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
          <FormControl sx={{ minWidth: 150 }} size="small">
            <InputLabel>View Mode</InputLabel>
            <Select
              value={viewMode}
              label="View Mode"
              onChange={handleViewModeChange}
            >
              <MenuItem value="service">Service View</MenuItem>
              <MenuItem value="cluster">Cluster View</MenuItem>
              <MenuItem value="namespace">Namespace View</MenuItem>
              <MenuItem value="network">Network View</MenuItem>
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 150 }} size="small">
            <InputLabel>Cloud Provider</InputLabel>
            <Select
              value={filters.cloud_provider || ''}
              label="Cloud Provider"
              onChange={(e) => handleFilterChange('cloud_provider', e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              {availableProviders.map((provider) => (
                <MenuItem key={provider} value={provider}>
                  {provider.toUpperCase()}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 150 }} size="small">
            <InputLabel>Resource Type</InputLabel>
            <Select
              value={filters.resource_type || ''}
              label="Resource Type"
              onChange={(e) => handleFilterChange('resource_type', e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              {availableTypes.map((type) => (
                <MenuItem key={type} value={type}>
                  {type}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {activeFilterCount > 0 && (
            <Chip
              label={`${activeFilterCount} filter(s) active - Clear`}
              onDelete={clearFilters}
              color="primary"
              size="small"
            />
          )}
        </Stack>
      </Paper>

      {/* Topology Graph */}
      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="500px">
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : topology ? (
        <Paper sx={{ p: 0, height: 'calc(100vh - 300px)', minHeight: 500 }}>
          <TopologyGraph data={topology} viewMode={viewMode} />
        </Paper>
      ) : (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">No topology data available</Typography>
        </Paper>
      )}
    </Box>
  );
}
