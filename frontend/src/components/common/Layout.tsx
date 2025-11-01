/**
 * Main application layout with navigation
 */

import { useState } from 'react';
import type { ReactNode } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  AccountTree as TopologyIcon,
  Warning as RiskIcon,
  Assessment as ImpactIcon,
  Extension as IntegrationsIcon,
  Layers as LayersIcon,
  Settings as SettingsIcon,
  AccountCircle as AccountCircleIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const DRAWER_WIDTH = 240;

interface LayoutProps {
  children: ReactNode;
}

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Topology', icon: <TopologyIcon />, path: '/topology' },
  { text: 'Risk Analysis', icon: <RiskIcon />, path: '/risk' },
  { text: 'Change Impact', icon: <ImpactIcon />, path: '/impact' },
  { text: 'Integrations', icon: <IntegrationsIcon />, path: '/integrations' },
];

export default function Layout({ children }: LayoutProps) {
  const [drawerOpen, setDrawerOpen] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: 'linear-gradient(90deg, #0a1929 0%, #132f4c 100%)',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={toggleDrawer}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <LayersIcon sx={{ mr: 1.5, fontSize: 28 }} />
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            TopDeck
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.7, mr: 2 }}>
            Multi-Cloud Platform
          </Typography>
          <IconButton
            color="inherit"
            sx={{ mr: 1 }}
            aria-label="settings"
          >
            <SettingsIcon />
          </IconButton>
          <IconButton
            color="inherit"
            edge="end"
            aria-label="user profile"
          >
            <AccountCircleIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Sidebar Drawer */}
      <Drawer
        variant="persistent"
        anchor="left"
        open={drawerOpen}
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
            mt: '64px',
            background: '#132f4c',
          },
        }}
      >
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  selected={location.pathname === item.path}
                  onClick={() => navigate(item.path)}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: 'rgba(33, 150, 243, 0.2)',
                      '&:hover': {
                        backgroundColor: 'rgba(33, 150, 243, 0.3)',
                      },
                    },
                  }}
                >
                  <ListItemIcon sx={{ color: 'primary.main' }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
          <Divider />
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          mt: '64px',
          ml: drawerOpen ? 0 : `-${DRAWER_WIDTH}px`,
          transition: (theme) =>
            theme.transitions.create('margin', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
          width: '100%',
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
