/**
 * Main App component with routing and dynamic seasonal theme
 */

import { useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Layout from './components/common/Layout';
import Dashboard from './pages/Dashboard';
import Topology from './pages/Topology';
import RiskAnalysis from './pages/RiskAnalysis';
import ChangeImpact from './pages/ChangeImpact';
import Integrations from './pages/Integrations';
import { getCurrentTheme } from './utils/themeDetector';

/**
 * Create MUI theme based on the current season/festivity
 */
function createSeasonalTheme() {
  const seasonalTheme = getCurrentTheme();
  
  return createTheme({
    palette: {
      mode: 'dark',
      primary: {
        main: seasonalTheme.primary,
      },
      secondary: {
        main: seasonalTheme.secondary,
      },
      background: {
        default: seasonalTheme.background,
        paper: seasonalTheme.paper,
      },
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    },
  });
}

function App() {
  // Create theme based on current date - recalculates when component mounts
  const theme = useMemo(() => createSeasonalTheme(), []);
  const currentTheme = getCurrentTheme();

  // Log current theme for debugging
  console.log(`🎨 Active theme: ${currentTheme.displayName} ${currentTheme.emoji}`);

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
            <Route path="/integrations" element={<Integrations />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
