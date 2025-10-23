# Service Dependency Graph

Enhanced service dependency graph visualization for TopDeck with modern UI, clear data flow arrows, and comprehensive service details.

## Features

### Visual Design
- **Modern Dark Theme**: Professional dark theme (#0f172a) matching TopDeck's design system
- **Color-Coded Services**: Visual distinction by service type and cloud provider
  - Services/Pods: Green/Blue (#4caf50, #2196f3)
  - Databases: Purple (#9c27b0, #7b1fa2, #6a1b9a)
  - Load Balancers: Pink/Red (#e91e63, #ec407a)
  - Storage: Orange (#ff9800)
  - Cloud Providers: Azure (#0078d4), AWS (#ff9900), GCP (#4285f4)

### Interactive Features
- **Zoom Controls**: Zoom in/out and fit to screen
- **Node Selection**: Click nodes to view detailed information
- **Visual Highlighting**: Selected nodes show with yellow border, connected edges and nodes highlighted
- **Smooth Animations**: Smooth transitions and layout animations

### Information Display
- **Statistics Card**: Real-time counts of services, dependencies, and cloud providers
- **Service Legend**: Color-coded legend for quick reference
- **Detail Panel**: Comprehensive service information on selection:
  - Service name and type
  - Cloud provider and region
  - Health status with visual indicators
  - Resource ID
  - Custom properties
  - Action buttons for detailed exploration

## Usage

### Accessing the Feature
1. Navigate to the **Topology** page from the main navigation
2. Click the **Dependency View** button (default view)
3. The graph will load automatically

### Demo Mode
- Toggle **Demo Mode** to view sample data without connecting to the backend
- Useful for demonstration and testing

### Interacting with the Graph
- **Zoom**: Use the zoom controls in the top-right corner
- **Pan**: Click and drag the graph background
- **Select Node**: Click any service node to view details
- **Deselect**: Click the background to clear selection
- **Fit View**: Click the center icon to fit all nodes in view

### Switching Views
- **Dependency View**: Enhanced visualization with modern UI (recommended)
- **Standard View**: Classic Cytoscape visualization

## Data Structure

### Mock Data
The component includes comprehensive mock data demonstrating:
- 13 services across Azure and AWS
- 16 dependency relationships
- Multi-cloud architecture patterns
- Various service types (pods, databases, load balancers, storage, etc.)

### Real Data
When connected to the backend API, the graph displays:
- Discovered cloud resources
- Detected dependencies
- Real-time health status
- Actual cloud provider data

## Component Architecture

### ServiceDependencyGraph Component
Location: `frontend/src/components/topology/ServiceDependencyGraph.tsx`

**Props:**
- `data: TopologyGraph` - Graph data containing nodes and edges

**Key Features:**
- Cytoscape.js integration for graph rendering
- Material UI components for UI elements
- Responsive layout with flexible sizing
- TypeScript strict typing

### Mock Data Provider
Location: `frontend/src/utils/mockTopologyData.ts`

Provides sample data representing a typical multi-cloud deployment:
- Application Gateway → Load Balancer → AKS Cluster → Pods
- Pods connecting to SQL Database, Cosmos DB, Redis Cache
- Cross-cloud connections to AWS RDS and Lambda
- Various relationship types (routes_to, accesses, stores_in, uses, etc.)

## Graph Layout Algorithm

Uses Cytoscape's COSE (Compound Spring Embedder) layout with optimized parameters:
- **Node Repulsion**: 12,000 (keeps nodes well-spaced)
- **Ideal Edge Length**: 120px (optimal for readability)
- **Iterations**: 1,000 (ensures good positioning)
- **Gravity**: 80 (prevents nodes from floating too far)
- **Animation Duration**: 800ms with ease-in-out-cubic easing

## Health Status Indicators

Service health is indicated by colored chips:
- 🟢 **Healthy/Running**: Green (#4caf50)
- 🟡 **Degraded/Warning**: Orange (#ff9800)
- 🔴 **Unhealthy/Error**: Red (#f44336)
- ⚪ **Unknown**: Gray (#607d8b)

## Relationship Types

The graph displays various dependency relationships:
- `routes_to`: Network routing (Gateway → Load Balancer)
- `deployed_to`: Deployment relationships (Cluster → Pods)
- `accesses`: Data access (Pods → Databases)
- `uses`: Service usage (Pods → Cache, Lambda)
- `stores_in`: Data storage (Pods → Blob Storage)
- `connects_to`: Network connections

## Future Enhancements

Potential improvements for future versions:
- Expand/collapse node clusters
- Filter by health status
- Search functionality
- Export to PNG/SVG
- Dependency path highlighting
- Performance metrics overlay
- Real-time updates via WebSocket
- Service dependency strength indicators
- Critical path analysis

## Technical Details

### Dependencies
- `cytoscape`: Graph visualization library
- `@mui/material`: UI components
- `@mui/icons-material`: Icon library
- `react`: UI framework
- `zustand`: State management

### Browser Compatibility
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support

### Performance
- Handles up to 100+ nodes smoothly
- Optimized rendering with Cytoscape's canvas-based approach
- Lazy loading of detail panels
- Efficient state updates with React hooks

## Troubleshooting

### Graph Not Displaying
- Check browser console for errors
- Verify backend API is running (if not using Demo Mode)
- Enable Demo Mode to test with sample data

### Slow Performance
- Reduce number of nodes by using filters
- Disable animations in Cytoscape configuration
- Close detail panel when not needed

### Layout Issues
- Click "Fit to Screen" to reset view
- Try zooming out if nodes are overlapping
- Reload page to reinitialize layout

## Contributing

To enhance the service dependency graph:
1. Component location: `frontend/src/components/topology/ServiceDependencyGraph.tsx`
2. Mock data: `frontend/src/utils/mockTopologyData.ts`
3. Page integration: `frontend/src/pages/Topology.tsx`
4. Follow existing TypeScript patterns
5. Test with both mock and real data
6. Ensure responsive design
7. Add appropriate error handling
