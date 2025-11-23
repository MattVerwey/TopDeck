/**
 * Global state management using Zustand
 */

import { create } from 'zustand';
import type {
  TopologyGraph,
  Resource,
  FilterOptions,
  ViewMode,
  Integration,
  RiskAssessment,
  TopologyFilterSettings,
} from '../types';

interface AppState {
  // Topology state
  topology: TopologyGraph | null;
  selectedResource: Resource | null;
  filters: FilterOptions;
  filterSettings: TopologyFilterSettings;
  viewMode: ViewMode;

  // Risk state
  risks: RiskAssessment[];
  
  // Integrations state
  integrations: Integration[];
  
  // UI state
  loading: boolean;
  error: string | null;
  sidebarOpen: boolean;

  // Actions
  setTopology: (topology: TopologyGraph) => void;
  setSelectedResource: (resource: Resource | null) => void;
  setFilters: (filters: FilterOptions) => void;
  setFilterSettings: (settings: TopologyFilterSettings) => void;
  setViewMode: (mode: ViewMode) => void;
  setRisks: (risks: RiskAssessment[]) => void;
  setIntegrations: (integrations: Integration[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  toggleSidebar: () => void;
  clearFilters: () => void;
}

export const useStore = create<AppState>((set) => ({
  // Initial state
  topology: null,
  selectedResource: null,
  filters: {},
  filterSettings: {
    mode: 'strict',
    showGrouping: false,
  },
  viewMode: 'service',
  risks: [],
  integrations: [],
  loading: false,
  error: null,
  sidebarOpen: true,

  // Actions
  setTopology: (topology) => set({ topology }),
  setSelectedResource: (resource) => set({ selectedResource: resource }),
  setFilters: (filters) => set({ filters }),
  setFilterSettings: (settings) => set({ filterSettings: settings }),
  setViewMode: (mode) => set({ viewMode: mode }),
  setRisks: (risks) => set({ risks }),
  setIntegrations: (integrations) => set({ integrations }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  clearFilters: () => set({ filters: {} }),
}));
