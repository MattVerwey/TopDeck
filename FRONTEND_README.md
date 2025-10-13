# TopDeck Frontend UI

## Overview

The TopDeck frontend is a modern, sleek React-based web application that provides comprehensive visualization and management of multi-cloud infrastructure. Built with TypeScript, Material-UI, and powerful visualization libraries, it delivers an intuitive interface for topology mapping, risk analysis, and change impact assessment.

## Screenshots

### Dashboard
![Dashboard](https://github.com/user-attachments/assets/e83d082a-233b-4501-8616-62ad59298d25)

The main dashboard provides quick access to key metrics and system health.

### Network Topology
![Topology View](https://github.com/user-attachments/assets/397e9492-22bc-4b08-9ec5-53fc1796afe1)

Interactive network topology visualization with multiple view modes and advanced filtering.

### Change Impact Analysis
![Change Impact](https://github.com/user-attachments/assets/52e86284-ba26-4624-9236-0cf79e1d87f2)

Analyze the impact of ServiceNow/Jira changes before deployment with detailed metrics.

### Integrations Management
![Integrations](https://github.com/user-attachments/assets/682892fd-754a-44ee-b5f3-970f76f7f6ac)

Manage and configure data source plugins including GitHub, Azure DevOps, Prometheus, and more.

## Key Features

### 🎯 Dashboard
- Real-time infrastructure metrics
- Resource count and health status
- High-risk service identification
- Single Points of Failure (SPOF) detection
- Recent changes feed

### 🗺️ Network Topology Visualization
- **Interactive Graph**: Powered by Cytoscape.js for smooth, interactive network visualization
- **Multiple View Modes**:
  - **Service View**: Individual service relationships
  - **Cluster View**: Resources grouped by cluster
  - **Namespace View**: Resources grouped by namespace
  - **Network View**: Network-level topology
- **Advanced Filtering**:
  - Cloud provider (Azure, AWS, GCP)
  - Resource type (Pod, Service, Database, etc.)
  - Region
  - Custom filters
- **Interactive Features**:
  - Click nodes for detailed information
  - Zoom and pan navigation
  - Color-coded by cloud provider
  - Real-time updates

### ⚠️ Risk Analysis
- Risk distribution visualization with charts
- Severity-based categorization (Critical, High, Medium, Low)
- Default risk detection:
  - Single Points of Failure
  - High dependency counts
  - Missing backup configurations
  - Security vulnerabilities
- Actionable recommendations
- Risk heatmaps and trend analysis

### 📊 Change Impact Analysis
- **ServiceNow/Jira Integration**: Analyze change requests before implementation
- **Impact Metrics**:
  - Number of affected services
  - Performance degradation estimates
  - Estimated downtime calculations
  - User impact assessment (Low/Medium/High)
- **Detailed Breakdown**:
  - Direct dependencies
  - Indirect (cascade) dependencies
  - Critical path detection
  - Recommended deployment windows
- **Change Types**: Deployment, Configuration, Scaling, Restart, Updates

### 🔌 Integrations Management
Comprehensive plugin system for data sources:

**Source Control:**
- GitHub (repositories, workflows, deployments)
- Azure DevOps (pipelines, repos)

**Monitoring:**
- Prometheus (metrics collection)
- Grafana Loki (log aggregation)

**Ticketing:**
- Jira (change tracking)
- ServiceNow (change requests)

Each integration features:
- Enable/disable toggles
- Configuration management
- Sync status tracking
- Last sync timestamps

## Technology Stack

| Technology | Purpose |
|------------|---------|
| React 18 | UI framework |
| TypeScript | Type safety |
| Vite | Build tool & dev server |
| Material-UI v7 | Component library |
| Zustand | State management |
| React Router v6 | Routing |
| Cytoscape.js | Network graph visualization |
| Recharts | Charts and graphs |
| Axios | HTTP client |

## Getting Started

### Prerequisites
- Node.js 18 or higher
- npm or yarn
- TopDeck backend running (default: `http://localhost:8000`)

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment configuration
cp .env.example .env

# Update .env with your backend URL if different
# VITE_API_URL=http://localhost:8000
```

### Development

```bash
# Start development server with hot reload
npm run dev

# Access at http://localhost:3000
```

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Output will be in dist/ directory
```

## Project Structure

```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── common/          # Shared components (Layout, etc.)
│   │   └── topology/        # Topology-specific components
│   ├── pages/               # Page components
│   │   ├── Dashboard.tsx    # Main dashboard
│   │   ├── Topology.tsx     # Topology visualization
│   │   ├── RiskAnalysis.tsx # Risk analysis dashboard
│   │   ├── ChangeImpact.tsx # Change impact analysis
│   │   └── Integrations.tsx # Integration management
│   ├── services/            # API clients
│   │   └── api.ts          # Backend API client
│   ├── store/               # State management
│   │   └── useStore.ts     # Zustand store
│   ├── types/               # TypeScript definitions
│   │   └── index.ts        # Type definitions
│   ├── App.tsx              # Main app component
│   └── main.tsx             # Entry point
├── public/                  # Static assets
├── .env.example            # Environment template
├── package.json            # Dependencies
├── vite.config.ts          # Vite configuration
└── tsconfig.json           # TypeScript configuration
```

## Configuration

### Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
# Backend API URL
VITE_API_URL=http://localhost:8000
```

### Backend Requirements

The frontend expects the following backend endpoints:

- `GET /api/v1/topology` - Topology data
- `GET /api/v1/topology/resources/{id}/dependencies` - Resource dependencies
- `GET /api/v1/topology/flows` - Data flows
- `GET /api/v1/monitoring/resources/{id}/metrics` - Resource metrics
- `GET /api/v1/integrations` - Integration list

### CORS Configuration

Ensure the backend has CORS properly configured to allow requests from `http://localhost:3000` during development.

## Usage Guide

### Viewing Topology

1. Navigate to **Topology** from the sidebar
2. Select your preferred view mode (Service/Cluster/Namespace/Network)
3. Apply filters as needed (Cloud Provider, Resource Type, Region)
4. Click on nodes to see detailed information
5. Use zoom and pan to navigate large topologies

### Analyzing Risk

1. Navigate to **Risk Analysis**
2. View risk distribution across your infrastructure
3. Review default detected risks
4. Click on individual risks for details and recommendations

### Analyzing Change Impact

1. Navigate to **Change Impact**
2. Select the service you plan to change
3. Choose the change type (Deployment, Configuration, etc.)
4. Click **Analyze** to see impact assessment
5. Review:
   - Affected services count
   - Performance degradation estimate
   - Estimated downtime
   - User impact level
   - Direct and indirect dependencies
   - Recommended deployment window

### Managing Integrations

1. Navigate to **Integrations**
2. View all available integrations
3. Toggle **Enabled** switch to activate/deactivate
4. Click **Configure** to set up credentials and settings
5. Monitor last sync status

## Development

### Adding New Pages

1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/common/Layout.tsx`
4. Create API methods in `src/services/api.ts` if needed

### Theming

The app uses Material-UI's theming system. Customize in `src/App.tsx`:

```typescript
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#2196f3' },
    secondary: { main: '#f50057' },
    // ... more options
  },
});
```

### State Management

The app uses Zustand for lightweight state management. Add new state in `src/store/useStore.ts`:

```typescript
interface AppState {
  // Add new state
  myNewState: string;
  setMyNewState: (value: string) => void;
}
```

## Performance Considerations

- Large topologies (500+ nodes) are optimized with Cytoscape.js layout algorithms
- Components use React.memo for optimization
- API calls are debounced to prevent excessive requests
- Loading states provide immediate feedback
- Lazy loading for route-based code splitting

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Troubleshooting

### Build Errors

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
npm run build
```

### API Connection Issues

- Verify backend is running at configured URL
- Check CORS configuration in backend
- Verify `.env` has correct `VITE_API_URL`

### TypeScript Errors

```bash
# Run type checking
npm run build
```

## Documentation

- [UI Guide](docs/UI_GUIDE.md) - Comprehensive usage guide
- [API Documentation](docs/api/) - Backend API reference
- [Issue #6](docs/issues/issue-006-topology-visualization.md) - Original requirements

## Contributing

When contributing to the UI:
1. Follow existing code structure and patterns
2. Use TypeScript for type safety
3. Add proper error handling
4. Test on multiple browsers
5. Update documentation for new features

## License

MIT

---

**Note**: The frontend is designed to work seamlessly with the TopDeck backend. Ensure the backend is properly configured and running before starting the frontend application.
