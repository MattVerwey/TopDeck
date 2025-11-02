/**
 * Hierarchical resource selector for filtering large topologies
 * Supports drilling down through subscription → cluster → namespace → app
 */

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Autocomplete,
  Stack,
  Typography,
  Chip,
  Box,
  Divider,
  Grid,
} from '@mui/material';
import {
  FilterList,
  Clear,
  Search,
} from '@mui/icons-material';
import type { Resource } from '../../types';

interface ResourceSelectorProps {
  open: boolean;
  onClose: () => void;
  resources: Resource[];
  onSelectResources: (resourceIds: string[]) => void;
  selectedResourceIds?: string[];
}

interface HierarchyLevel {
  subscriptions: string[];
  clusters: Map<string, string[]>;
  namespaces: Map<string, string[]>;
  apps: Map<string, Resource[]>;
}

export default function ResourceSelector({
  open,
  onClose,
  resources,
  onSelectResources,
  selectedResourceIds = [],
}: ResourceSelectorProps) {
  const [selectedSubscription, setSelectedSubscription] = useState<string | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null);
  const [selectedNamespace, setSelectedNamespace] = useState<string | null>(null);
  const [selectedApps, setSelectedApps] = useState<string[]>(selectedResourceIds);
  const [searchTerm, setSearchTerm] = useState('');

  const [hierarchy, setHierarchy] = useState<HierarchyLevel>({
    subscriptions: [],
    clusters: new Map(),
    namespaces: new Map(),
    apps: new Map(),
  });

  // Build hierarchy from resources
  useEffect(() => {
    const subscriptions = new Set<string>();
    const clusters = new Map<string, Set<string>>();
    const namespaces = new Map<string, Set<string>>();
    const apps = new Map<string, Resource[]>();

    resources.forEach((resource) => {
      // Extract subscription from resource ID (Azure pattern: /subscriptions/{sub}/...)
      const subMatch = resource.id.match(/\/subscriptions\/([^/]+)/);
      const subscription = subMatch ? subMatch[1] : resource.cloud_provider;
      subscriptions.add(subscription);

      // Extract cluster and namespace from properties or metadata
      const cluster = (resource.properties?.cluster as string) || 
                     (resource.metadata?.cluster as string) || 
                     (resource.resource_type === 'aks_cluster' ? resource.name : null);
      
      const namespace = (resource.properties?.namespace as string) || 
                       (resource.metadata?.namespace as string) || 
                       'default';

      if (cluster) {
        if (!clusters.has(subscription)) {
          clusters.set(subscription, new Set());
        }
        clusters.get(subscription)!.add(cluster);

        const clusterKey = `${subscription}/${cluster}`;
        if (!namespaces.has(clusterKey)) {
          namespaces.set(clusterKey, new Set());
        }
        namespaces.get(clusterKey)!.add(namespace);

        const namespaceKey = `${clusterKey}/${namespace}`;
        if (!apps.has(namespaceKey)) {
          apps.set(namespaceKey, []);
        }
        apps.get(namespaceKey)!.push(resource);
      }
    });

    setHierarchy({
      subscriptions: Array.from(subscriptions).sort(),
      clusters: new Map(
        Array.from(clusters.entries()).map(([k, v]) => [k, Array.from(v).sort()])
      ),
      namespaces: new Map(
        Array.from(namespaces.entries()).map(([k, v]) => [k, Array.from(v).sort()])
      ),
      apps,
    });
  }, [resources]);

  const availableClusters = selectedSubscription
    ? hierarchy.clusters.get(selectedSubscription) || []
    : [];

  const availableNamespaces = selectedSubscription && selectedCluster
    ? hierarchy.namespaces.get(`${selectedSubscription}/${selectedCluster}`) || []
    : [];

  const availableApps = selectedSubscription && selectedCluster && selectedNamespace
    ? hierarchy.apps.get(`${selectedSubscription}/${selectedCluster}/${selectedNamespace}`) || []
    : [];

  // Filter apps by search term
  const filteredApps = availableApps.filter((app) =>
    app.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    app.resource_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleApply = () => {
    onSelectResources(selectedApps);
    onClose();
  };

  const handleClear = () => {
    setSelectedSubscription(null);
    setSelectedCluster(null);
    setSelectedNamespace(null);
    setSelectedApps([]);
    setSearchTerm('');
  };

  const handleSelectAll = () => {
    setSelectedApps(filteredApps.map((app) => app.id));
  };

  const handleDeselectAll = () => {
    setSelectedApps([]);
  };

  const toggleAppSelection = (appId: string) => {
    setSelectedApps((prev) =>
      prev.includes(appId)
        ? prev.filter((id) => id !== appId)
        : [...prev, appId]
    );
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Stack direction="row" alignItems="center" spacing={1}>
          <FilterList />
          <Typography variant="h6">Select Resources</Typography>
        </Stack>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3}>
          {/* Info */}
          <Typography variant="body2" color="text.secondary">
            Filter resources hierarchically through subscription → cluster → namespace → app.
            This helps manage large topologies with thousands of resources.
          </Typography>

          {/* Subscription Selection */}
          <Autocomplete
            value={selectedSubscription}
            onChange={(_e, newValue) => {
              setSelectedSubscription(newValue);
              setSelectedCluster(null);
              setSelectedNamespace(null);
              setSelectedApps([]);
            }}
            options={hierarchy.subscriptions}
            renderInput={(params) => (
              <TextField {...params} label="Subscription / Cloud Provider" size="small" />
            )}
            fullWidth
          />

          {/* Cluster Selection */}
          <Autocomplete
            value={selectedCluster}
            onChange={(_e, newValue) => {
              setSelectedCluster(newValue);
              setSelectedNamespace(null);
              setSelectedApps([]);
            }}
            options={availableClusters}
            disabled={!selectedSubscription}
            renderInput={(params) => (
              <TextField {...params} label="Cluster" size="small" />
            )}
            fullWidth
          />

          {/* Namespace Selection */}
          <Autocomplete
            value={selectedNamespace}
            onChange={(_e, newValue) => {
              setSelectedNamespace(newValue);
              setSelectedApps([]);
            }}
            options={availableNamespaces}
            disabled={!selectedCluster}
            renderInput={(params) => (
              <TextField {...params} label="Namespace" size="small" />
            )}
            fullWidth
          />

          {/* App Search and Selection */}
          {selectedNamespace && (
            <>
              <Divider />
              <TextField
                label="Search Resources"
                size="small"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
                fullWidth
              />

              <Box>
                <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    {filteredApps.length} resources available
                    {selectedApps.length > 0 && ` • ${selectedApps.length} selected`}
                  </Typography>
                  <Stack direction="row" spacing={1}>
                    <Button size="small" onClick={handleSelectAll}>
                      Select All
                    </Button>
                    <Button size="small" onClick={handleDeselectAll}>
                      Deselect All
                    </Button>
                  </Stack>
                </Stack>

                <Box
                  sx={{
                    maxHeight: 400,
                    overflowY: 'auto',
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    p: 2,
                  }}
                >
                  <Grid container spacing={2}>
                    {filteredApps.map((app) => (
                      <Grid key={app.id} size={{ xs: 12, md: 6 }}>
                        <Box
                          onClick={() => toggleAppSelection(app.id)}
                          sx={{
                            cursor: 'pointer',
                            border: '2px solid',
                            borderColor: selectedApps.includes(app.id) ? 'primary.main' : 'divider',
                            borderRadius: 1,
                            p: 1.5,
                            transition: 'all 0.2s',
                            bgcolor: selectedApps.includes(app.id) 
                              ? 'action.selected' 
                              : 'transparent',
                            '&:hover': {
                              borderColor: 'primary.main',
                              bgcolor: 'action.hover',
                            },
                          }}
                        >
                          <Stack spacing={1}>
                            <Typography variant="subtitle2" fontWeight={600} noWrap>
                              {app.name}
                            </Typography>
                            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                              <Chip
                                label={app.resource_type}
                                size="small"
                                variant="outlined"
                                sx={{ fontSize: '0.7rem' }}
                              />
                              <Chip
                                label={app.cloud_provider.toUpperCase()}
                                size="small"
                                color="primary"
                                sx={{ fontSize: '0.7rem' }}
                              />
                            </Stack>
                          </Stack>
                        </Box>
                      </Grid>
                    ))}
                    {filteredApps.length === 0 && (
                      <Grid size={{ xs: 12 }}>
                        <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>
                          No resources found
                        </Typography>
                      </Grid>
                    )}
                  </Grid>
                </Box>
              </Box>
            </>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClear} startIcon={<Clear />}>
          Clear All
        </Button>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleApply} variant="contained">
          Apply ({selectedApps.length} selected)
        </Button>
      </DialogActions>
    </Dialog>
  );
}
