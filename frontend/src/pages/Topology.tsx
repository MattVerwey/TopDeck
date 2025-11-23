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
  FormControlLabel,
  Switch,
  Tooltip,
  Radio,
  RadioGroup,
  FormLabel,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import { AccountTree, ViewModule, FilterList, Info } from '@mui/icons-material';
import { useStore } from '../store/useStore';
import apiClient from '../services/api';
import TopologyGraph from '../components/topology/TopologyGraph';
import ServiceDependencyGraph from '../components/topology/ServiceDependencyGraph';
import ResourceSelector from '../components/topology/ResourceSelector';
import DocLink from '../components/common/DocLink';
import { mockTopologyData } from '../utils/mockTopologyData';
import type { TopologyGraph as TopologyGraphType, FilterMode } from '../types';

export default function Topology() {
  const {
    topology,
    filters,
    filterSettings,
    viewMode,
    setTopology,
    setFilters,
    setFilterSettings,
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
  const [expandedNodeIds, setExpandedNodeIds] = useState<Set<string>>(new Set());
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

  // Helper function to resolve transitive dependencies
  const resolveTransitiveDependencies = useCallback((
    initialIds: Set<string>,
    topology: TopologyGraphType
  ): Set<string> => {
    const relatedIds = new Set<string>(initialIds);
    const validNodeIds = new Set(topology.nodes.map(n => n.id));
    
    // Optimized: Only check edges connected to newly added nodes
    let newlyAdded = new Set(initialIds);
    while (newlyAdded.size > 0) {
      const nextNew = new Set<string>();
      
      topology.edges.forEach((edge) => {
        // Only check edges connected to newly added nodes
        if (newlyAdded.has(edge.source_id) && validNodeIds.has(edge.target_id) && !relatedIds.has(edge.target_id)) {
          relatedIds.add(edge.target_id);
          nextNew.add(edge.target_id);
        }
        if (newlyAdded.has(edge.target_id) && validNodeIds.has(edge.source_id) && !relatedIds.has(edge.source_id)) {
          relatedIds.add(edge.source_id);
          nextNew.add(edge.source_id);
        }
      });
      
      newlyAdded = nextNew;
    }
    
    return relatedIds;
  }, []);

  // Apply filters and resource selection
  useEffect(() => {
    if (!topology) {
      setFilteredTopology(null);
      return;
    }

    let filtered = { ...topology };

    // Filter by selected resources if any - this overrides other filters
    if (selectedResourceIds.length > 0) {
      // Include selected resources and their dependencies based on filter mode
      if (filterSettings.mode === 'strict') {
        // Show ONLY the selected resources, no dependencies
        filtered = applyNodeFilter(topology, (n) => selectedResourceIds.includes(n.id));
      } else if (filterSettings.mode === 'with-dependencies') {
        // Show selected resources and their DIRECT dependencies (1 level)
        const directlyRelatedIds = new Set<string>(selectedResourceIds);
        topology.edges.forEach((edge) => {
          if (selectedResourceIds.includes(edge.source_id)) {
            directlyRelatedIds.add(edge.target_id);
          }
          if (selectedResourceIds.includes(edge.target_id)) {
            directlyRelatedIds.add(edge.source_id);
          }
        });
        filtered = applyNodeFilter(topology, (n) => directlyRelatedIds.has(n.id));
      } else {
        // 'full-graph': Show selected resources and ALL their transitive dependencies
        const relatedIds = resolveTransitiveDependencies(new Set(selectedResourceIds), topology);
        filtered = applyNodeFilter(topology, (n) => relatedIds.has(n.id));
      }
    } else {
      // Apply standard filters only when no resources are selected
      const matchingNodeIds = new Set<string>();
      
      // If no filters are active, include all nodes
      const hasActiveFilters = !!(filters.cloud_provider || filters.resource_type || filters.cluster || filters.namespace);
      
      if (!hasActiveFilters) {
        // No filters - include all nodes
        topology.nodes.forEach(n => matchingNodeIds.add(n.id));
      } else {
        // Apply filters to find matching nodes
        topology.nodes.forEach((node) => {
          let matches = true;
          
          if (filters.cloud_provider && node.cloud_provider !== filters.cloud_provider) {
            matches = false;
          }
          
          if (filters.resource_type && node.resource_type !== filters.resource_type) {
            matches = false;
          }
          
          if (filters.cluster) {
            const nodeCluster = (node.properties?.cluster as string) || (node.metadata?.cluster as string);
            if (nodeCluster !== filters.cluster) {
              matches = false;
            }
          }
          
          if (filters.namespace) {
            const nodeNamespace = (node.properties?.namespace as string) || (node.metadata?.namespace as string);
            if (nodeNamespace !== filters.namespace) {
              matches = false;
            }
          }
          
          if (matches) {
            matchingNodeIds.add(node.id);
          }
        });
      }

      // Apply filter mode to determine what to show
      let nodesToShow = new Set(matchingNodeIds);
      
      if (filterSettings.mode === 'strict') {
        // Show ONLY the matching nodes (no dependencies)
        // But add expanded nodes' dependencies
        if (expandedNodeIds.size > 0) {
          topology.edges.forEach((edge) => {
            if (expandedNodeIds.has(edge.source_id)) {
              nodesToShow.add(edge.target_id);
            }
            if (expandedNodeIds.has(edge.target_id)) {
              nodesToShow.add(edge.source_id);
            }
          });
        }
        filtered = applyNodeFilter(topology, (n) => nodesToShow.has(n.id));
      } else if (filterSettings.mode === 'with-dependencies') {
        // Show matching nodes and their DIRECT dependencies (1 level)
        const directlyRelatedIds = new Set(matchingNodeIds);
        topology.edges.forEach((edge) => {
          if (matchingNodeIds.has(edge.source_id)) {
            directlyRelatedIds.add(edge.target_id);
          }
          if (matchingNodeIds.has(edge.target_id)) {
            directlyRelatedIds.add(edge.source_id);
          }
        });
        
        // Add expanded nodes' full dependencies
        if (expandedNodeIds.size > 0) {
          const expandedDeps = resolveTransitiveDependencies(expandedNodeIds, topology);
          expandedDeps.forEach(id => directlyRelatedIds.add(id));
        }
        
        filtered = applyNodeFilter(topology, (n) => directlyRelatedIds.has(n.id));
      } else {
        // 'full-graph': Show matching nodes and ALL their transitive dependencies
        const relatedIds = resolveTransitiveDependencies(matchingNodeIds, topology);
        filtered = applyNodeFilter(topology, (n) => relatedIds.has(n.id));
      }
    }

    filtered.metadata = {
      ...filtered.metadata,
      total_nodes: filtered.nodes.length,
      total_edges: filtered.edges.length,
      filter_mode: filterSettings.mode,
      expanded_nodes: expandedNodeIds.size,
    };

    setFilteredTopology(filtered);
  }, [topology, selectedResourceIds, filters, filterSettings, expandedNodeIds, applyNodeFilter, resolveTransitiveDependencies]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters({ ...filters, [key]: value || undefined } as typeof filters);
  };

  const handleViewModeChange = (event: SelectChangeEvent) => {
    setViewMode(event.target.value as 'service' | 'cluster' | 'namespace' | 'network');
  };

  const clearFilters = () => {
    setFilters({});
    setSelectedResourceIds([]);
    setExpandedNodeIds(new Set());
  };

  const handleResourceSelection = (resourceIds: string[]) => {
    setSelectedResourceIds(resourceIds);
  };

  const handleNodeExpand = (nodeId: string) => {
    setExpandedNodeIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        // Collapse: remove from expanded set
        newSet.delete(nodeId);
      } else {
        // Expand: add to expanded set
        newSet.add(nodeId);
      }
      return newSet;
    });
  };

  const activeFilterCount = Object.keys(filters).filter((k) => filters[k as keyof typeof filters]).length + 
    (selectedResourceIds.length > 0 ? 1 : 0);

  // Helper function to format filter mode name
  const getFilterModeName = (mode: FilterMode): string => {
    const modeNames: Record<FilterMode, string> = {
      'strict': 'Strict Mode',
      'with-dependencies': 'Direct Dependencies',
      'full-graph': 'Full Dependency Graph',
    };
    return modeNames[mode];
  };

  // Helper function to get filter mode description
  const getFilterModeDescription = (mode: FilterMode): string => {
    const descriptions: Record<FilterMode, string> = {
      'strict': ' (only matching resources)',
      'with-dependencies': ' (matching resources + direct dependencies)',
      'full-graph': ' (matching resources + all dependencies)',
    };
    return descriptions[mode];
  };

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
          {/* Filter Mode Selection */}
          <Box>
            <Stack direction="row" spacing={2} alignItems="center">
              <FormLabel component="legend" sx={{ minWidth: 120 }}>
                Filter Mode:
              </FormLabel>
              <RadioGroup
                row
                value={filterSettings.mode}
                onChange={(e) => setFilterSettings({ ...filterSettings, mode: e.target.value as FilterMode })}
              >
                <FormControlLabel
                  value="strict"
                  control={<Radio size="small" />}
                  label={
                    <Tooltip title="Show only resources that match the filter criteria (no dependencies)">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography variant="body2">Strict</Typography>
                        <Info fontSize="small" sx={{ fontSize: 14, color: 'text.secondary' }} />
                      </Box>
                    </Tooltip>
                  }
                />
                <FormControlLabel
                  value="with-dependencies"
                  control={<Radio size="small" />}
                  label={
                    <Tooltip title="Show filtered resources plus their direct dependencies (1 level)">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography variant="body2">With Direct Dependencies</Typography>
                        <Info fontSize="small" sx={{ fontSize: 14, color: 'text.secondary' }} />
                      </Box>
                    </Tooltip>
                  }
                />
                <FormControlLabel
                  value="full-graph"
                  control={<Radio size="small" />}
                  label={
                    <Tooltip title="Show filtered resources plus all transitive dependencies (full dependency chain)">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography variant="body2">Full Dependency Graph</Typography>
                        <Info fontSize="small" sx={{ fontSize: 14, color: 'text.secondary' }} />
                      </Box>
                    </Tooltip>
                  }
                />
              </RadioGroup>
            </Stack>
            <Typography variant="caption" color="text.secondary" sx={{ ml: 15, display: 'block', mt: 0.5 }}>
              {filterSettings.mode === 'strict' && 'Reduces clutter by showing only matching resources'}
              {filterSettings.mode === 'with-dependencies' && 'Shows immediate connections without overwhelming the view'}
              {filterSettings.mode === 'full-graph' && 'Shows complete dependency chains (may be cluttered with many resources)'}
            </Typography>
          </Box>

          {/* Grouping Options */}
          <Stack direction="row" spacing={2} alignItems="center">
            <FormControlLabel
              control={
                <Switch
                  checked={filterSettings.showGrouping}
                  onChange={(e) => setFilterSettings({ ...filterSettings, showGrouping: e.target.checked })}
                  size="small"
                />
              }
              label="Enable Grouping"
            />
            {filterSettings.showGrouping && (
              <FormControl sx={{ minWidth: 180 }} size="small">
                <InputLabel>Group By</InputLabel>
                <Select
                  value={filterSettings.groupBy || ''}
                  label="Group By"
                  onChange={(e) => setFilterSettings({ 
                    ...filterSettings, 
                    groupBy: e.target.value as TopologyFilterSettings['groupBy']
                  })}
                >
                  <MenuItem value="">None</MenuItem>
                  <MenuItem value="cluster">Cluster</MenuItem>
                  <MenuItem value="namespace">Namespace</MenuItem>
                  <MenuItem value="resource_type">Resource Type</MenuItem>
                  <MenuItem value="cloud_provider">Cloud Provider</MenuItem>
                </Select>
              </FormControl>
            )}
          </Stack>

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
              sx={{ minWidth: 200 }}
              options={availableTypes}
              value={filters.resource_type || null}
              onChange={(_e, newValue) => handleFilterChange('resource_type', newValue || '')}
              renderInput={(params) => <TextField {...params} label="Resource Type" />}
              renderOption={(props, option) => (
                <li {...props} key={option}>
                  <Stack direction="row" justifyContent="space-between" width="100%">
                    <Typography variant="body2">{option}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {topology?.nodes.filter((n) => n.resource_type === option).length}
                    </Typography>
                  </Stack>
                </li>
              )}
            />

            {availableClusters.length > 0 && (
              <Autocomplete
                size="small"
                sx={{ minWidth: 150 }}
                options={availableClusters}
                value={filters.cluster || null}
                onChange={(_e, newValue) => handleFilterChange('cluster', newValue || '')}
                renderInput={(params) => <TextField {...params} label="Cluster" />}
              />
            )}

            {availableNamespaces.length > 0 && (
              <Autocomplete
                size="small"
                sx={{ minWidth: 150 }}
                options={availableNamespaces}
                value={filters.namespace || null}
                onChange={(_e, newValue) => handleFilterChange('namespace', newValue || '')}
                renderInput={(params) => <TextField {...params} label="Namespace (Service Bus/Event Hub)" />}
              />
            )}

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
        <>
          {/* Filter Status Banner */}
          {(activeFilterCount > 0 || filterSettings.mode !== 'strict') && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Stack spacing={1}>
                <Typography variant="body2" fontWeight={600}>
                  Active Filtering: {getFilterModeName(filterSettings.mode)}
                </Typography>
                <Typography variant="caption">
                  Showing {filteredTopology.nodes.length} of {topology?.nodes.length || 0} total resources
                  {getFilterModeDescription(filterSettings.mode)}
                  {expandedNodeIds.size > 0 && ` • ${expandedNodeIds.size} node(s) expanded`}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  💡 Tip: Double-click any node to expand/collapse its dependencies
                </Typography>
                {activeFilterCount > 0 && (
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {filters.cloud_provider && <Chip size="small" label={`Provider: ${filters.cloud_provider}`} />}
                    {filters.resource_type && <Chip size="small" label={`Type: ${filters.resource_type}`} />}
                    {filters.cluster && <Chip size="small" label={`Cluster: ${filters.cluster}`} />}
                    {filters.namespace && <Chip size="small" label={`Namespace: ${filters.namespace}`} />}
                    {selectedResourceIds.length > 0 && <Chip size="small" label={`Selected: ${selectedResourceIds.length} resources`} />}
                  </Stack>
                )}
              </Stack>
            </Alert>
          )}
          
          <Paper sx={{ p: 0, height: 'calc(100vh - 400px)', minHeight: 500 }}>
            {graphView === 'dependency' ? (
              <ServiceDependencyGraph 
                data={filteredTopology} 
                onNodeExpand={handleNodeExpand}
                expandedNodeIds={expandedNodeIds}
              />
            ) : (
              <TopologyGraph 
                data={filteredTopology} 
                viewMode={viewMode}
                onNodeExpand={handleNodeExpand}
                expandedNodeIds={expandedNodeIds}
              />
            )}
          </Paper>
        </>
      ) : (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">No topology data available</Typography>
        </Paper>
      )}
    </Box>
  );
}
