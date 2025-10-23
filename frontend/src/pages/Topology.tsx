/**
 * Topology visualization page with filtering and interactive graph
 */

import { useEffect, useState, useCallback } from 'react';
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
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import { AccountTree, ViewModule } from '@mui/icons-material';
import { useStore } from '../store/useStore';
import apiClient from '../services/api';
import TopologyGraph from '../components/topology/TopologyGraph';
import ServiceDependencyGraph from '../components/topology/ServiceDependencyGraph';
import { mockTopologyData } from '../utils/mockTopologyData';

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
  const [graphView, setGraphView] = useState<'standard' | 'dependency'>('dependency');
  const [useMockData, setUseMockData] = useState(true); // Start with demo data

  const loadTopology = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let data;
      if (useMockData) {
        // Use mock data for demonstration
        data = mockTopologyData;
      } else {
        // Load from API
        data = await apiClient.getTopology(filters);
      }
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
  }, [useMockData, filters, setLoading, setError, setTopology]);

  useEffect(() => {
    loadTopology();
  }, [loadTopology]);

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
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight={600}>
          Network Topology
        </Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <Chip
            label={useMockData ? 'Demo Mode' : 'Live Data'}
            color={useMockData ? 'warning' : 'success'}
            onClick={() => setUseMockData(!useMockData)}
            sx={{ cursor: 'pointer' }}
          />
          <ToggleButtonGroup
            value={graphView}
            exclusive
            onChange={(_e, newView) => newView && setGraphView(newView)}
            size="small"
          >
            <ToggleButton value="dependency">
              <AccountTree sx={{ mr: 1 }} />
              Dependency View
            </ToggleButton>
            <ToggleButton value="standard">
              <ViewModule sx={{ mr: 1 }} />
              Standard View
            </ToggleButton>
          </ToggleButtonGroup>
        </Stack>
      </Stack>

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
          {graphView === 'dependency' ? (
            <ServiceDependencyGraph data={topology} />
          ) : (
            <TopologyGraph data={topology} viewMode={viewMode} />
          )}
        </Paper>
      ) : (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">No topology data available</Typography>
        </Paper>
      )}
    </Box>
  );
}
