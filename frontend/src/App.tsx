/**
 * Main App component with routing and theme
 */

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Layout from './components/common/Layout';
import Dashboard from './pages/Dashboard';
import Topology from './pages/Topology';
import RiskAnalysis from './pages/RiskAnalysis';
import ChangeImpact from './pages/ChangeImpact';
import SLAManagement from './pages/SLAManagement';
import Integrations from './pages/Integrations';
import Settings from './pages/Settings';
import LiveDiagnostics from './pages/LiveDiagnostics';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#0a1929',
      paper: '#132f4c',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/topology" element={<Topology />} />
            <Route path="/risk" element={<RiskAnalysis />} />
            <Route path="/impact" element={<ChangeImpact />} />
            <Route path="/sla" element={<SLAManagement />} />
            <Route path="/integrations" element={<Integrations />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/live-diagnostics" element={<LiveDiagnostics />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
