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
    url = `ws://${window.location.hostname}:8000/api/v1/ws/live-diagnostics`,
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
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isIntentionalCloseRef = useRef(false);

  // Polling fallback function
  const pollSnapshot = useCallback(async () => {
    try {
      const response = await fetch(
        `http://${window.location.hostname}:8000/api/v1/live-diagnostics/snapshot?duration_hours=1`
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

  // Handle WebSocket messages
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
          // Update specific service in snapshot
          if (message.data) {
            const { resource_id, new_status, health_score } = message.data;
            
            // Update snapshot if it exists
            if (snapshot) {
              const updatedServices = snapshot.services.map(service =>
                service.resource_id === resource_id
                  ? { ...service, status: new_status, health_score }
                  : service
              );
              setSnapshot({ ...snapshot, services: updatedServices });
            }
            
            // Log health change even if no snapshot yet
            console.log('Health change:', message.data);
          }
          break;
        
        case 'anomaly_detected':
          // Add new anomaly to snapshot
          if (message.data) {
            // Use crypto.randomUUID() for better ID generation
            const newAnomaly = {
              alert_id: crypto.randomUUID(),
              ...message.data,
              timestamp: message.timestamp,
            };
            
            if (snapshot) {
              setSnapshot({
                ...snapshot,
                anomalies: [newAnomaly, ...snapshot.anomalies],
              });
            } else {
              // Log anomaly even if no snapshot yet
              console.log('Anomaly detected:', newAnomaly);
            }
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
  }, [snapshot]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    // Don't connect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      // Stop polling when attempting WebSocket connection
      stopPolling();

      // Build WebSocket URL with parameters
      const wsUrl = `${url}?update_interval=${updateInterval}`;
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
          if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
            reconnectAttemptsRef.current += 1;
            
            console.log(
              `Attempting to reconnect... (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
            );
            
            reconnectTimeoutRef.current = setTimeout(() => {
              connect();
            }, reconnectDelay);
          } else if (fallbackToPolling) {
            console.log('Max reconnect attempts reached, falling back to polling');
            startPolling();
          }
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError(err instanceof Error ? err.message : 'Failed to create WebSocket');
      
      if (fallbackToPolling) {
        startPolling();
      }
    }
  }, [
    url,
    updateInterval,
    autoReconnect,
    maxReconnectAttempts,
    reconnectDelay,
    fallbackToPolling,
    handleMessage,
    startPolling,
    stopPolling,
  ]);

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

  // Send ping to keep connection alive
  const ping = useCallback(() => {
    sendMessage({ type: 'ping' });
  }, [sendMessage]);

  // Effect: Connect on mount, disconnect on unmount
  useEffect(() => {
    isIntentionalCloseRef.current = false;
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

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
