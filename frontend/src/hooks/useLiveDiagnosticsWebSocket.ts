/**
 * Custom React hook for Live Diagnostics WebSocket connection.
 * 
 * Provides real-time updates for diagnostics data with automatic reconnection,
 * error handling, and fallback to polling when WebSocket is unavailable.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { LiveDiagnosticsSnapshot } from '../types/diagnostics';

export interface WebSocketConfig {
  /** WebSocket URL (default: ws://localhost:8000/api/v1/ws/live-diagnostics) */
  url?: string;
  /** Update interval in seconds (1-60) */
  updateInterval?: number;
  /** Enable automatic reconnection */
  autoReconnect?: boolean;
  /** Maximum reconnection attempts before giving up */
  maxReconnectAttempts?: number;
  /** Delay between reconnection attempts in ms */
  reconnectDelay?: number;
  /** Fallback to polling if WebSocket fails */
  fallbackToPolling?: boolean;
  /** Polling interval in ms when using fallback */
  pollingInterval?: number;
}

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  data?: any;
  message?: string;
}

export interface ConnectionStatus {
  connected: boolean;
  connectionType: 'websocket' | 'polling' | 'disconnected';
  reconnectAttempts: number;
  lastError?: string;
}

export function useLiveDiagnosticsWebSocket(config: WebSocketConfig = {}) {
  const {
    url = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.hostname}:8000/api/v1/ws/live-diagnostics`,
    updateInterval = 10,
    autoReconnect = true,
    maxReconnectAttempts = 5,
    reconnectDelay = 3000,
    fallbackToPolling = true,
    pollingInterval = 30000,
  } = config;

  const [snapshot, setSnapshot] = useState<LiveDiagnosticsSnapshot | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    connected: false,
    connectionType: 'disconnected',
    reconnectAttempts: 0,
  });
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const pollingIntervalRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isIntentionalCloseRef = useRef(false);

  // Polling fallback function
  const pollSnapshot = useCallback(async () => {
    try {
      const response = await fetch(
        `${window.location.protocol}//${window.location.hostname}:8000/api/v1/live-diagnostics/snapshot?duration_hours=1`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSnapshot(data);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch snapshot';
      setError(errorMessage);
      console.error('Polling error:', errorMessage);
    }
  }, []);

  // Start polling fallback
  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    setConnectionStatus({
      connected: true,
      connectionType: 'polling',
      reconnectAttempts: reconnectAttemptsRef.current,
    });

    // Initial poll
    pollSnapshot();

    // Set up polling interval
    pollingIntervalRef.current = setInterval(pollSnapshot, pollingInterval);
  }, [pollSnapshot, pollingInterval]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  // Store config values in refs for stable access
  const configRef = useRef({
    url,
    updateInterval,
    autoReconnect,
    maxReconnectAttempts,
    reconnectDelay,
    fallbackToPolling,
  });

  // Update config ref when values change
  useEffect(() => {
    configRef.current = {
      url,
      updateInterval,
      autoReconnect,
      maxReconnectAttempts,
      reconnectDelay,
      fallbackToPolling,
    };
  }, [url, updateInterval, autoReconnect, maxReconnectAttempts, reconnectDelay, fallbackToPolling]);

  // Handle WebSocket messages - using functional setState to avoid stale closure
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      switch (message.type) {
        case 'snapshot_update':
          if (message.data) {
            setSnapshot(message.data as LiveDiagnosticsSnapshot);
            setError(null);
          }
          break;
        
        case 'health_change':
          // Update specific service in snapshot using functional setState
          if (message.data) {
            const { resource_id, new_status, health_score } = message.data;
            
            setSnapshot(prev => {
              if (!prev) {
                // Log health change even if no snapshot yet
                console.log('Health change (no snapshot):', message.data);
                return prev;
              }
              
              const updatedServices = prev.services.map(service =>
                service.resource_id === resource_id
                  ? { ...service, status: new_status, health_score }
                  : service
              );
              return { ...prev, services: updatedServices };
            });
          }
          break;
        
        case 'anomaly_detected':
          // Add new anomaly to snapshot using functional setState
          if (message.data) {
            // Use crypto.randomUUID() for better ID generation
            const newAnomaly = {
              alert_id: crypto.randomUUID(),
              ...message.data,
              timestamp: message.timestamp,
            };
            
            setSnapshot(prev => {
              if (!prev) {
                // Log anomaly even if no snapshot yet
                console.log('Anomaly detected (no snapshot):', newAnomaly);
                return prev;
              }
              
              return {
                ...prev,
                anomalies: [newAnomaly, ...prev.anomalies],
              };
            });
          }
          break;
        
        case 'traffic_anomaly':
          // Update traffic patterns
          console.log('Traffic anomaly detected:', message.data);
          break;
        
        case 'connected':
          console.log('WebSocket connected:', message.message);
          break;
        
        case 'pong':
          // Response to ping
          break;
        
        case 'error':
          console.error('WebSocket error message:', message.message);
          setError(message.message || 'WebSocket error');
          break;
        
        default:
          console.log('Unknown message type:', message.type);
      }
    } catch (err) {
      console.error('Error parsing WebSocket message:', err);
    }
  }, []); // Empty dependencies - using functional setState

  // Connect to WebSocket - stable function using refs
  const connect = useCallback(() => {
    // Don't connect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      // Stop polling when attempting WebSocket connection
      stopPolling();

      // Build WebSocket URL with parameters
      const config = configRef.current;
      const wsUrl = `${config.url}?update_interval=${config.updateInterval}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttemptsRef.current = 0;
        setConnectionStatus({
          connected: true,
          connectionType: 'websocket',
          reconnectAttempts: 0,
        });
        setError(null);
      };

      ws.onmessage = handleMessage;

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        
        setConnectionStatus({
          connected: false,
          connectionType: 'disconnected',
          reconnectAttempts: reconnectAttemptsRef.current,
        });

        // Only attempt reconnection if not intentionally closed
        if (!isIntentionalCloseRef.current) {
          const config = configRef.current;
          if (config.autoReconnect && reconnectAttemptsRef.current < config.maxReconnectAttempts) {
            reconnectAttemptsRef.current += 1;
            
            // Exponential backoff with maximum cap: delay = min(reconnectDelay * 2^(attempts - 1), 30000ms)
            const exponentialDelay = Math.min(
              config.reconnectDelay * Math.pow(2, reconnectAttemptsRef.current - 1),
              30000 // Cap at 30 seconds maximum
            );
            
            console.log(
              `Attempting to reconnect... (${reconnectAttemptsRef.current}/${config.maxReconnectAttempts}) in ${exponentialDelay}ms`
            );
            
            reconnectTimeoutRef.current = setTimeout(() => {
              connect();
            }, exponentialDelay);
          } else if (config.fallbackToPolling) {
            console.log('Max reconnect attempts reached, falling back to polling');
            startPolling();
          }
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError(err instanceof Error ? err.message : 'Failed to create WebSocket');
      
      if (configRef.current.fallbackToPolling) {
        startPolling();
      }
    }
  }, [handleMessage, stopPolling, startPolling]); // Stable dependencies only

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    isIntentionalCloseRef.current = true;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    stopPolling();
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setConnectionStatus({
      connected: false,
      connectionType: 'disconnected',
      reconnectAttempts: 0,
    });
  }, [stopPolling]);

  // Send message to WebSocket
  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected, cannot send message');
    }
  }, []);

  // Request immediate snapshot
  const requestSnapshot = useCallback(() => {
    sendMessage({ type: 'get_snapshot' });
  }, [sendMessage]);

  // Subscribe to specific resources
  const subscribe = useCallback((resourceIds: string[]) => {
    sendMessage({ type: 'subscribe', resource_ids: resourceIds });
  }, [sendMessage]);

  // Unsubscribe from specific resources
  const unsubscribe = useCallback((resourceIds: string[]) => {
    sendMessage({ type: 'unsubscribe', resource_ids: resourceIds });
  }, [sendMessage]);

  // Effect: Connect on mount, disconnect on unmount
  // Note: connect/disconnect have stable dependencies (handleMessage uses functional setState,
  // stopPolling/startPolling use minimal deps) so they won't change on every render.
  // Using empty deps array is safe here as we want to connect once on mount.
  useEffect(() => {
    isIntentionalCloseRef.current = false;
    connect();

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Intentionally empty - connect only on mount, disconnect on unmount

  // Effect: Set up ping interval to keep connection alive
  useEffect(() => {
    if (connectionStatus.connectionType === 'websocket') {
      const pingInterval = setInterval(() => {
        // Use sendMessage directly instead of ping function to avoid dependency issues
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000); // Ping every 30 seconds

      return () => clearInterval(pingInterval);
    }
  }, [connectionStatus.connectionType]); // Removed ping from dependencies

  return {
    snapshot,
    connectionStatus,
    error,
    connect,
    disconnect,
    requestSnapshot,
    subscribe,
    unsubscribe,
    sendMessage,
  };
}
