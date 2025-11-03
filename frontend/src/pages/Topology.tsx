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
  Button,
  Autocomplete,
  TextField,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import { AccountTree, ViewModule, FilterList } from '@mui/icons-material';
import { useStore } from '../store/useStore';
import apiClient from '../services/api';
import TopologyGraph from '../components/topology/TopologyGraph';
import ServiceDependencyGraph from '../components/topology/ServiceDependencyGraph';
import ResourceSelector from '../components/topology/ResourceSelector';
import DocLink from '../components/common/DocLink';
import { mockTopologyData } from '../utils/mockTopologyData';
import type { TopologyGraph as TopologyGraphType } from '../types';

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
  const [availableClusters, setAvailableClusters] = useState<string[]>([]);
  const [availableNamespaces, setAvailableNamespaces] = useState<string[]>([]);
  const [graphView, setGraphView] = useState<'standard' | 'dependency'>('dependency');
  const [useMockData, setUseMockData] = useState(false); // Start with live data from API
  const [resourceSelectorOpen, setResourceSelectorOpen] = useState(false);
  const [selectedResourceIds, setSelectedResourceIds] = useState<string[]>([]);
  const [filteredTopology, setFilteredTopology] = useState<TopologyGraphType | null>(null);

  const loadTopology = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let data: TopologyGraphType;
      if (useMockData) {
        // Use mock data for demonstration
        data = mockTopologyData;
      } else {
        // Load from API
        data = await apiClient.getTopology(filters);
      }
      setTopology(data);

      // Extract unique providers, types, clusters, and namespaces
      const providers = [...new Set(data.nodes.map((n) => n.cloud_provider))];
      const types = [...new Set(data.nodes.map((n) => n.resource_type))];
      const clusters = [...new Set(
        data.nodes
          .map((n) => (n.properties?.cluster as string) || (n.metadata?.cluster as string))
          .filter(Boolean)
      )];
      const namespaces = [...new Set(
        data.nodes
          .map((n) => (n.properties?.namespace as string) || (n.metadata?.namespace as string))
          .filter(Boolean)
      )];
      
      setAvailableProviders(providers);
      setAvailableTypes(types);
      setAvailableClusters(clusters);
      setAvailableNamespaces(namespaces);
    } catch (err) {
      const error = err as Error;
      setError(error.message || 'Failed to load topology');
    } finally {
      setLoading(false);
    }
  }, [useMockData, filters, setLoading, setError, setTopology]);

  useEffect(() => {
    loadTopology();
  }, [loadTopology]);

  // Helper function to apply a filter and update edges accordingly
  const applyNodeFilter = useCallback((
    data: TopologyGraphType,
    predicate: (node: TopologyGraphType['nodes'][0]) => boolean
  ): TopologyGraphType => {
    const filteredNodes = data.nodes.filter(predicate);
    const nodeIds = new Set(filteredNodes.map((n) => n.id));
    const filteredEdges = data.edges.filter(
      (e) => nodeIds.has(e.source_id) && nodeIds.has(e.target_id)
    );
    
    return {
      ...data,
      nodes: filteredNodes,
      edges: filteredEdges,
    };
  }, []);

  // Apply filters and resource selection
  useEffect(() => {
    if (!topology) {
      setFilteredTopology(null);
      return;
    }

    let filtered = { ...topology };

    // Filter by selected resources if any
    if (selectedResourceIds.length > 0) {
      const selectedSet = new Set(selectedResourceIds);
      // Include selected resources and their direct dependencies
      const relatedIds = new Set<string>(selectedResourceIds);
      
      // Add upstream and downstream dependencies
      topology.edges.forEach((edge) => {
        if (selectedSet.has(edge.source_id)) {
          relatedIds.add(edge.target_id);
        }
        if (selectedSet.has(edge.target_id)) {
          relatedIds.add(edge.source_id);
        }
      });

      filtered = applyNodeFilter(filtered, (n) => relatedIds.has(n.id));
    }

    // Apply other filters using the helper function
    if (filters.cloud_provider) {
      filtered = applyNodeFilter(filtered, (n) => n.cloud_provider === filters.cloud_provider);
    }

    if (filters.resource_type) {
      filtered = applyNodeFilter(filtered, (n) => n.resource_type === filters.resource_type);
    }

    if (filters.cluster) {
      filtered = applyNodeFilter(filtered, (n) => 
        (n.properties?.cluster as string) === filters.cluster ||
        (n.metadata?.cluster as string) === filters.cluster
      );
    }

    if (filters.namespace) {
      filtered = applyNodeFilter(filtered, (n) => 
        (n.properties?.namespace as string) === filters.namespace ||
        (n.metadata?.namespace as string) === filters.namespace
      );
    }

    filtered.metadata = {
      ...filtered.metadata,
      total_nodes: filtered.nodes.length,
      total_edges: filtered.edges.length,
    };

    setFilteredTopology(filtered);
  }, [topology, selectedResourceIds, filters, applyNodeFilter]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters({ ...filters, [key]: value || undefined } as typeof filters);
  };

  const handleViewModeChange = (event: SelectChangeEvent) => {
    setViewMode(event.target.value as 'service' | 'cluster' | 'namespace' | 'network');
  };

  const clearFilters = () => {
    setFilters({});
    setSelectedResourceIds([]);
  };

  const handleResourceSelection = (resourceIds: string[]) => {
    setSelectedResourceIds(resourceIds);
  };

  const activeFilterCount = Object.keys(filters).filter((k) => filters[k as keyof typeof filters]).length + 
    (selectedResourceIds.length > 0 ? 1 : 0);

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight={600}>
          Network Topology
        </Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <DocLink href="docs/ENHANCED_TOPOLOGY_ANALYSIS.md" text="Topology Guide" />
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
        <Stack spacing={2}>
          {/* Resource Selector Button */}
          <Box>
            <Button
              variant="outlined"
              startIcon={<FilterList />}
              onClick={() => setResourceSelectorOpen(true)}
              size="small"
            >
              Select Resources
              {selectedResourceIds.length > 0 && ` (${selectedResourceIds.length})`}
            </Button>
            {selectedResourceIds.length > 0 && (
              <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                Showing {selectedResourceIds.length} selected resources and their dependencies
              </Typography>
            )}
          </Box>

          {/* Quick Filters */}
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

            <Autocomplete
              size="small"
              sx={{ minWidth: 150 }}
              options={availableClusters}
              value={filters.cluster || null}
              onChange={(_e, newValue) => handleFilterChange('cluster', newValue || '')}
              renderInput={(params) => <TextField {...params} label="Cluster" />}
            />

            <Autocomplete
              size="small"
              sx={{ minWidth: 150 }}
              options={availableNamespaces}
              value={filters.namespace || null}
              onChange={(_e, newValue) => handleFilterChange('namespace', newValue || '')}
              renderInput={(params) => <TextField {...params} label="Namespace" />}
            />

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
        </Stack>
      </Paper>

      {/* Resource Selector Dialog */}
      {topology && (
        <ResourceSelector
          open={resourceSelectorOpen}
          onClose={() => setResourceSelectorOpen(false)}
          resources={topology.nodes}
          selectedResourceIds={selectedResourceIds}
          onSelectResources={handleResourceSelection}
        />
      )}

      {/* Topology Graph */}
      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="500px">
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : filteredTopology ? (
        <Paper sx={{ p: 0, height: 'calc(100vh - 400px)', minHeight: 500 }}>
          {graphView === 'dependency' ? (
            <ServiceDependencyGraph data={filteredTopology} />
          ) : (
            <TopologyGraph data={filteredTopology} viewMode={viewMode} />
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
