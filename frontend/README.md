# TopDeck Frontend

Modern, sleek React-based frontend for the TopDeck multi-cloud platform with topology visualization, risk analysis, and change impact features.

## Features

- **Dashboard Overview**: Real-time metrics and health status
- **Network Topology Visualization**: Interactive graph with Cytoscape.js
  - Service, Cluster, Namespace, and Network views
  - Filter by cloud provider, resource type, and region
  - Zoom, pan, and click for details
- **Risk Analysis**: Identify and visualize infrastructure risks
  - Risk distribution charts
  - Default risk detection
  - SPOF identification
- **Change Impact Analysis**: Analyze ServiceNow/Jira changes
  - Performance degradation estimation
  - Downtime calculation
  - Affected services breakdown
- **Integrations Management**: Configure data source plugins
  - GitHub, Azure DevOps
  - Prometheus, Loki
  - Jira, ServiceNow

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: Material-UI (MUI)
- **State Management**: Zustand
- **Routing**: React Router
- **Visualization**: 
  - Cytoscape.js for network graphs
  - Recharts for charts and graphs
- **API Client**: Axios

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- TopDeck backend running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Project Structure

```
src/
├── components/       # React components
│   ├── common/      # Reusable components (Layout, etc.)
│   ├── topology/    # Topology visualization components
│   ├── risk/        # Risk visualization components
│   ├── dashboard/   # Dashboard components
│   └── integrations/# Integration components
├── pages/           # Page components
│   ├── Dashboard.tsx
│   ├── Topology.tsx
│   ├── RiskAnalysis.tsx
│   ├── ChangeImpact.tsx
│   └── Integrations.tsx
├── services/        # API client and services
│   └── api.ts
├── store/           # State management
│   └── useStore.ts
├── types/           # TypeScript type definitions
│   └── index.ts
├── hooks/           # Custom React hooks
└── utils/           # Utility functions
```

## Configuration

Edit `.env` to configure the backend API URL:

```env
VITE_API_URL=http://localhost:8000
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Features Overview

### Topology View

- Interactive network graph visualization
- Multiple view modes (Service, Cluster, Namespace, Network)
- Filtering by cloud provider, resource type, region
- Click nodes to see details
- Real-time topology updates

### Risk Analysis

- Visual risk distribution
- Default risk detection
- SPOF identification
- Risk scoring and recommendations

### Change Impact

- Analyze impact of changes before deployment
- ServiceNow/Jira integration ready
- Performance degradation estimates
- Downtime calculations
- Affected services breakdown

### Integrations

- Manage data source plugins
- GitHub and Azure DevOps support
- Prometheus and Loki monitoring
- Jira and ServiceNow ticketing (configurable)

## Development

The frontend uses hot module replacement (HMR) for fast development. Changes to components will be reflected immediately without full page reload.

API calls are proxied to the backend through Vite's dev server configuration.

## License

MIT
