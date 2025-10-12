# Issue #6: Build Topology Visualization Dashboard

**Labels**: `enhancement`, `ui`, `visualization`, `priority: high`, `phase-3`

## Description

Build an interactive web dashboard that visualizes the application topology, network flows, and dependencies. This is the primary user interface for TopDeck.

## Requirements

### Core Visualizations

1. **Network Topology Graph**
   - Interactive node-link diagram
   - Nodes represent resources (VMs, containers, databases, etc.)
   - Edges represent relationships (depends on, connects to)
   - Color-coding by resource type
   - Size based on criticality or traffic volume

2. **Dependency Tree View**
   - Hierarchical view of dependencies
   - Expandable/collapsible nodes
   - Show dependency depth

3. **Risk Heatmap**
   - Grid or treemap showing risk scores
   - Color gradient from green (low risk) to red (high risk)
   - Click to drill into details

4. **Flow Diagram**
   - Show data flow through system
   - Animated flows for real-time data
   - Highlight bottlenecks

### Interactive Features

- **Search**: Find specific resources
- **Filter**: Filter by cloud provider, resource type, risk level
- **Zoom/Pan**: Navigate large topologies
- **Highlight**: Highlight paths and dependencies
- **Details Panel**: Show resource details on click
- **Time Travel**: View topology at different points in time

### Dashboard Views

1. **Overview Dashboard**
   - Key metrics (total resources, high-risk services, SPOFs)
   - Recent changes
   - Top risks
   - Health status

2. **Resource Detail View**
   - Full resource information
   - Dependencies (upstream and downstream)
   - Risk assessment
   - Recent changes and deployments
   - Performance metrics

3. **Impact Analysis View**
   - "What if" scenarios
   - Blast radius visualization
   - Change impact preview

## Technical Design

### Technology Stack

**Framework**: React 18+ with TypeScript
**State Management**: Redux Toolkit or Zustand
**Visualization**: 
  - D3.js for custom visualizations
  - Cytoscape.js for network graphs
  - Recharts for charts and graphs
**UI Components**: Material-UI or Ant Design
**API Client**: Axios or React Query
**Routing**: React Router

### Project Structure
```
src/ui/
├── components/
│   ├── common/          # Reusable components
│   ├── topology/        # Topology visualization components
│   ├── risk/            # Risk visualization components
│   ├── dashboard/       # Dashboard components
│   └── resource/        # Resource detail components
├── pages/
│   ├── Dashboard.tsx    # Main dashboard
│   ├── Topology.tsx     # Topology view
│   ├── Resources.tsx    # Resource list/search
│   ├── RiskAnalysis.tsx # Risk analysis view
│   └── ResourceDetail.tsx # Resource detail page
├── services/
│   ├── api.ts           # API client
│   └── websocket.ts     # WebSocket for real-time updates
├── store/               # State management
├── hooks/               # Custom React hooks
├── utils/               # Utility functions
└── types/               # TypeScript types
```

### Key Components

```typescript
// TopologyGraph.tsx
interface TopologyGraphProps {
  resources: Resource[];
  relationships: Relationship[];
  onNodeClick: (nodeId: string) => void;
  highlightPath?: string[];
  filterBy?: FilterOptions;
}

export const TopologyGraph: React.FC<TopologyGraphProps> = ({...}) => {
  // Render interactive topology using Cytoscape.js
};

// RiskHeatmap.tsx
interface RiskHeatmapProps {
  resources: Resource[];
  riskScores: Map<string, number>;
  onResourceSelect: (resourceId: string) => void;
}

// DependencyTree.tsx
interface DependencyTreeProps {
  rootResourceId: string;
  depth?: number;
  direction: 'upstream' | 'downstream';
}
```

## Wireframes

### Main Dashboard
```
┌────────────────────────────────────────────────────────┐
│  TopDeck  🔍 Search...  [Filter] [Cloud] [View]  👤   │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Overview                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │ 245      │ │ 12       │ │ 3        │ │ 98%      ││
│  │Resources │ │High Risk │ │SPOFs     │ │Healthy   ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                                                         │
│  ┌─────────────────────────┐ ┌─────────────────────┐ │
│  │  Recent Changes         │ │  Top Risks          │ │
│  │  • webapp-prod updated  │ │  • sql-db-prod (85) │ │
│  │  • aks-cluster scaled   │ │  • api-gateway (78) │ │
│  └─────────────────────────┘ └─────────────────────┘ │
│                                                         │
│  Network Topology                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │         [Interactive Graph Visualization]       │  │
│  │                                                  │  │
│  │   (○)──────(○)                                  │  │
│  │    │        │                                   │  │
│  │   (○)──────(◎)──────(○)                       │  │
│  │            │         │                          │  │
│  │           (○)       (○)                        │  │
│  │                                                  │  │
│  └────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### Resource Detail View
```
┌────────────────────────────────────────────────────────┐
│  ← Back to Topology                              👤   │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Resource: webapp-prod                                 │
│  Type: Azure App Service | Region: East US            │
│  Status: ● Running | Risk Score: 65 (Medium)          │
│                                                         │
│  ┌──── Dependencies ────────────────────────────────┐ │
│  │  Depends On:                                      │ │
│  │  • sql-db-prod (Azure SQL)                       │ │
│  │  • redis-cache (Redis)                           │ │
│  │  • storage-account-prod (Storage)                │ │
│  │                                                   │ │
│  │  Depended Upon By:                               │ │
│  │  • frontend-cdn (CDN)                            │ │
│  │  • mobile-app-backend (AKS)                      │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌──── Deployment History ─────────────────────────┐  │
│  │  [Chart showing deployments over time]          │  │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌──── Risk Analysis ──────────────────────────────┐  │
│  │  ⚠️ 5 services depend on this resource          │  │
│  │  ℹ️ Last deployed 2 days ago                     │  │
│  │  ✓ High test coverage                           │  │
│  └───────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

## Tasks

### Phase 1: Foundation
- [ ] Set up React project with TypeScript
- [ ] Configure build tools (Vite or CRA)
- [ ] Set up routing
- [ ] Set up state management
- [ ] Create API client
- [ ] Design component structure

### Phase 2: Core Components
- [ ] Build TopologyGraph component with Cytoscape.js
- [ ] Build DependencyTree component
- [ ] Build ResourceCard component
- [ ] Build Dashboard layout
- [ ] Build search/filter functionality

### Phase 3: Advanced Features
- [ ] Implement RiskHeatmap
- [ ] Add real-time updates via WebSocket
- [ ] Implement time travel feature
- [ ] Add export/screenshot functionality
- [ ] Build responsive design

### Phase 4: Polish
- [ ] Add loading states and error handling
- [ ] Optimize performance
- [ ] Add animations and transitions
- [ ] Write component tests
- [ ] Create user documentation

## Success Criteria

- [ ] Can visualize topology with 500+ nodes without lag
- [ ] Interactive and responsive
- [ ] Intuitive navigation and filtering
- [ ] Real-time updates work smoothly
- [ ] Works on desktop and tablet
- [ ] Comprehensive component tests
- [ ] User documentation complete

## Performance Considerations

- Virtualize large lists
- Lazy load components
- Debounce search/filter
- Use React.memo for expensive components
- Implement canvas rendering for large graphs
- Progressive loading for topology

## Accessibility

- Keyboard navigation support
- Screen reader compatible
- Color-blind friendly color schemes
- High contrast mode option

## Dependencies

- Issue #2: Core Data Models (for API contracts)
- Backend API endpoints available
- Risk analysis data available

## Timeline

Weeks 6-8

## Related Issues

- Issue #7: REST API Implementation
- Issue #5: Risk Analysis Engine (provides data)
