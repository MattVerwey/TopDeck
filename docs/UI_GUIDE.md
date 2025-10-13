# TopDeck UI Guide

## Overview

The TopDeck UI is a modern, React-based web application that provides comprehensive visualization and analysis of your multi-cloud infrastructure.

## Features

### 1. Dashboard
The main dashboard provides an at-a-glance overview of your infrastructure:
- Total resources count
- High-risk services count
- Single Points of Failure (SPOFs)
- Overall health percentage
- Recent changes feed
- Top risks visualization

### 2. Network Topology Visualization
Interactive network graph showing your infrastructure topology:
- **View Modes**:
  - Service View: Shows individual services and their relationships
  - Cluster View: Groups resources by cluster
  - Namespace View: Groups resources by namespace
  - Network View: Shows network-level topology

- **Filtering**:
  - Filter by cloud provider (Azure, AWS, GCP)
  - Filter by resource type (Pod, Service, Database, etc.)
  - Filter by region

- **Interactions**:
  - Click nodes to see details
  - Zoom and pan to navigate
  - Color-coded by cloud provider
  - Real-time updates

### 3. Risk Analysis
Comprehensive risk analysis dashboard:
- Risk distribution by severity (Critical, High, Medium, Low)
- Visual charts showing risk metrics
- Default risks automatically detected:
  - Single Points of Failure
  - High dependency counts
  - Missing backup configurations
  - And more...
- Recommendations for each risk

### 4. Change Impact Analysis
Analyze the impact of changes before deployment:
- Select a service to analyze
- Choose change type (Deployment, Configuration, Scaling, etc.)
- View impact metrics:
  - Number of affected services
  - Performance degradation estimate
  - Estimated downtime
  - User impact level
- Detailed breakdown:
  - Direct dependencies
  - Indirect dependencies
  - Critical path detection
  - Recommended deployment window

Supports integration with:
- ServiceNow change requests
- Jira tickets

### 5. Integrations Management
Configure and manage data source plugins:
- **Source Control**:
  - GitHub
  - Azure DevOps
- **Monitoring**:
  - Prometheus
  - Grafana Loki
- **Ticketing**:
  - Jira
  - ServiceNow

Each integration can be:
- Enabled/disabled
- Configured with credentials
- Monitored for sync status

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- TopDeck backend running

### Installation

```bash
cd frontend
npm install
```

### Configuration

Create a `.env` file (copy from `.env.example`):

```env
VITE_API_URL=http://localhost:8000
```

### Running Locally

```bash
# Development mode with hot reload
npm run dev

# Access at http://localhost:3000
```

### Building for Production

```bash
npm run build

# Output will be in dist/
```

## Architecture

### Technology Stack
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Library**: Material-UI (MUI) v7
- **State Management**: Zustand
- **Routing**: React Router v6
- **Network Visualization**: Cytoscape.js
- **Charts**: Recharts
- **HTTP Client**: Axios

### Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable React components
│   │   ├── common/      # Common components (Layout, etc.)
│   │   └── topology/    # Topology-specific components
│   ├── pages/           # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Topology.tsx
│   │   ├── RiskAnalysis.tsx
│   │   ├── ChangeImpact.tsx
│   │   └── Integrations.tsx
│   ├── services/        # API clients
│   │   └── api.ts
│   ├── store/           # Zustand state management
│   │   └── useStore.ts
│   ├── types/           # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx          # Main app component
│   └── main.tsx         # Entry point
├── public/              # Static assets
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### State Management

The app uses Zustand for lightweight state management:
- Topology data
- Selected resources
- Filters
- View modes
- Risk assessments
- Integrations
- Loading states

### API Integration

The UI communicates with the TopDeck backend via REST APIs:
- `/api/v1/topology` - Topology data
- `/api/v1/topology/resources/{id}/dependencies` - Resource dependencies
- `/api/v1/topology/flows` - Data flows
- `/api/v1/monitoring/*` - Monitoring data
- `/api/v1/integrations` - Integration management

## Customization

### Theming

The app uses Material-UI theming. Colors and styles can be customized in `App.tsx`:

```typescript
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2196f3',  // Customize primary color
    },
    // ... more theme options
  },
});
```

### Adding New Views

1. Create a new page component in `src/pages/`
2. Add the route in `App.tsx`
3. Add a menu item in `Layout.tsx`
4. Create any new API calls in `services/api.ts`

### Adding New Integrations

To add a new integration type:
1. Update the `Integration` type in `src/types/index.ts`
2. Add the integration to the list in `Integrations.tsx`
3. Implement the configuration form
4. Add backend API support

## Performance Considerations

- Large topologies (500+ nodes) are optimized using Cytoscape.js layout algorithms
- Components use React.memo where appropriate
- API calls are debounced to prevent excessive requests
- Loading states provide feedback during async operations

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Troubleshooting

### Build Errors

If you encounter build errors:
```bash
# Clean and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### API Connection Issues

Check that:
1. Backend is running on the configured URL
2. CORS is properly configured in the backend
3. `.env` file has correct API URL

### TypeScript Errors

Run type checking:
```bash
npm run build
```

## Contributing

When contributing to the UI:
1. Follow the existing code structure
2. Use TypeScript for type safety
3. Add proper error handling
4. Test on multiple browsers
5. Update this documentation for new features

## License

MIT
