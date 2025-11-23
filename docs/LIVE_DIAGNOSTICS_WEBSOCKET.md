# Live Diagnostics WebSocket Implementation Guide

## Overview

Phase 6 of Live Diagnostics implements WebSocket support for true real-time updates, replacing the previous polling mechanism with an event-driven architecture.

## Architecture

### Backend Components

#### 1. WebSocket Endpoint (`/api/v1/ws/live-diagnostics`)

**Location:** `src/topdeck/api/routes/live_diagnostics_ws.py`

**Features:**
- FastAPI WebSocket route with query parameter support
- Connection management for multiple concurrent clients
- Automatic broadcasting of diagnostics snapshots
- Event publishing for specific change types
- Client message handling (ping, subscribe, request snapshot)

**Query Parameters:**
- `update_interval`: Update frequency in seconds (1-60, default: 10)

#### 2. Connection Manager

Manages all active WebSocket connections and provides:
- Thread-safe connection tracking
- Broadcast messaging to all clients
- Personal messaging to specific clients
- Automatic cleanup of disconnected clients

#### 3. Diagnostics Update Publisher

Background task that:
- Fetches diagnostics snapshots at regular intervals
- Broadcasts updates to all connected clients
- Only runs when clients are connected (resource efficient)
- Publishes specific events (health changes, anomalies, traffic anomalies)

### Frontend Components

#### 1. WebSocket Hook (`useLiveDiagnosticsWebSocket`)

**Location:** `frontend/src/hooks/useLiveDiagnosticsWebSocket.ts`

**Features:**
- Automatic connection establishment
- Auto-reconnection with exponential backoff
- Fallback to polling when WebSocket unavailable
- Message handling for all event types
- Connection status tracking
- Ping/pong keep-alive mechanism

**Configuration Options:**
```typescript
{
  url?: string;                    // WebSocket URL
  updateInterval?: number;         // Update interval in seconds (1-60)
  autoReconnect?: boolean;         // Enable auto-reconnection
  maxReconnectAttempts?: number;   // Max reconnection attempts
  reconnectDelay?: number;         // Delay between reconnects (ms)
  fallbackToPolling?: boolean;     // Fallback to polling on failure
  pollingInterval?: number;        // Polling interval when in fallback (ms)
}
```

#### 2. Updated LiveDiagnosticsPanel

**Location:** `frontend/src/components/diagnostics/LiveDiagnosticsPanel.tsx`

**Changes:**
- Replaced polling with WebSocket hook
- Added connection status indicator
- Removed auto-refresh toggle (always on with WebSocket)
- Manual refresh now requests immediate snapshot

## WebSocket Message Protocol

### Server → Client Messages

#### 1. Connected
```json
{
  "type": "connected",
  "timestamp": "2024-11-23T16:00:00Z",
  "message": "Connected to live diagnostics WebSocket",
  "update_interval": 10
}
```

#### 2. Snapshot Update
```json
{
  "type": "snapshot_update",
  "timestamp": "2024-11-23T16:00:10Z",
  "data": {
    "services": [...],
    "anomalies": [...],
    "traffic_patterns": [...],
    "failing_dependencies": [...],
    "overall_health": "healthy"
  }
}
```

#### 3. Health Change
```json
{
  "type": "health_change",
  "timestamp": "2024-11-23T16:00:15Z",
  "data": {
    "resource_id": "api-gateway-prod",
    "old_status": "healthy",
    "new_status": "degraded",
    "health_score": 72.5
  }
}
```

#### 4. Anomaly Detected
```json
{
  "type": "anomaly_detected",
  "timestamp": "2024-11-23T16:00:20Z",
  "data": {
    "resource_id": "database-prod",
    "metric_name": "error_rate",
    "severity": "high",
    "description": "Error rate is 3.5x above normal baseline"
  }
}
```

#### 5. Traffic Anomaly
```json
{
  "type": "traffic_anomaly",
  "timestamp": "2024-11-23T16:00:25Z",
  "data": {
    "source_id": "api-gateway",
    "target_id": "user-service",
    "anomaly_type": "latency_spike",
    "description": "P95 latency increased by 200%"
  }
}
```

#### 6. Pong
```json
{
  "type": "pong",
  "timestamp": "2024-11-23T16:00:30Z"
}
```

#### 7. Error
```json
{
  "type": "error",
  "timestamp": "2024-11-23T16:00:35Z",
  "message": "Invalid message format"
}
```

### Client → Server Messages

#### 1. Ping
```json
{
  "type": "ping"
}
```

#### 2. Get Snapshot
```json
{
  "type": "get_snapshot"
}
```

#### 3. Subscribe (Future Enhancement)
```json
{
  "type": "subscribe",
  "resource_ids": ["api-gateway", "database-prod"]
}
```

#### 4. Unsubscribe (Future Enhancement)
```json
{
  "type": "unsubscribe",
  "resource_ids": ["api-gateway"]
}
```

## Connection Flow

### Normal Operation

1. Client establishes WebSocket connection
2. Server sends "connected" message
3. Publisher starts broadcasting snapshots every 10 seconds
4. Client receives and processes updates
5. Client sends ping every 30 seconds for keep-alive
6. Server responds with pong
7. Repeat 3-6 until disconnection

### Reconnection Flow

1. WebSocket connection drops
2. Client detects disconnection
3. Client attempts reconnection (attempt 1/5)
4. If successful: resume normal operation
5. If failed: wait 3 seconds, retry
6. Repeat until max attempts (5) reached
7. Fall back to polling if all attempts fail

### Fallback to Polling

1. WebSocket fails after max reconnection attempts
2. Client switches to polling mode
3. Polls REST API every 30 seconds
4. Continues until WebSocket becomes available again

## Configuration

### Backend Environment Variables

```bash
# FastAPI already supports WebSocket (included in fastapi[all])
# No additional configuration needed
```

### Frontend Configuration

```typescript
// Default configuration
const config = {
  url: `ws://${window.location.hostname}:8000/api/v1/ws/live-diagnostics`,
  updateInterval: 10,
  autoReconnect: true,
  maxReconnectAttempts: 5,
  reconnectDelay: 3000,
  fallbackToPolling: true,
  pollingInterval: 30000,
};

// Usage
const { snapshot, connectionStatus } = useLiveDiagnosticsWebSocket(config);
```

## Performance Characteristics

### WebSocket vs Polling

| Metric | WebSocket | Polling |
|--------|-----------|---------|
| Update Latency | ~10 seconds | ~30 seconds |
| Server Load | Low (push) | Higher (poll) |
| Network Overhead | Minimal | Higher |
| Client Complexity | Medium | Low |
| Scalability | High | Medium |

### Resource Usage

**Backend:**
- Memory: ~1KB per connected client
- CPU: Minimal (background task runs only when clients connected)
- Network: ~2-5KB per broadcast (depending on topology size)

**Frontend:**
- Memory: ~100KB for WebSocket connection
- CPU: Minimal
- Network: Receive only (no constant polling requests)

## Testing

### Manual Testing

1. **Test WebSocket Connection:**
```bash
python scripts/test_websocket.py
```

2. **Test in Browser:**
- Open Developer Tools → Network → WS tab
- Navigate to Live Diagnostics
- Look for WebSocket connection to `/api/v1/ws/live-diagnostics`
- Verify messages are being received

3. **Test Reconnection:**
- Open Live Diagnostics
- Restart API server
- Verify client reconnects automatically
- Check connection status indicator changes

4. **Test Fallback:**
- Disable WebSocket on server
- Verify client falls back to polling
- Check connection status shows "Polling (Fallback)"

### Automated Testing

```python
# tests/integration/test_websocket.py
import pytest
from fastapi.testclient import TestClient
from topdeck.api.main import app

def test_websocket_connection():
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/live-diagnostics") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connected"
```

## Troubleshooting

### Connection Issues

**Problem:** WebSocket fails to connect

**Solutions:**
1. Check if API server is running
2. Verify port 8000 is accessible
3. Check browser console for errors
4. Verify firewall allows WebSocket connections

### Reconnection Loops

**Problem:** Client constantly reconnecting

**Solutions:**
1. Check server logs for errors
2. Verify Neo4j and Prometheus are accessible
3. Increase `reconnectDelay` to reduce retry frequency
4. Check for authentication issues

### High Memory Usage

**Problem:** Server memory increases over time

**Solutions:**
1. Check for connection leaks (disconnected clients not cleaned up)
2. Verify publisher stops when no clients connected
3. Monitor `active_connections` count in health endpoint

### Fallback to Polling Not Working

**Problem:** Client doesn't fall back to polling

**Solutions:**
1. Verify `fallbackToPolling` is `true` in config
2. Check REST API endpoints are accessible
3. Look for CORS errors in browser console

## Security Considerations

### Authentication (Future Enhancement)

Currently, WebSocket connections are not authenticated. For production deployment:

1. Add token-based authentication
2. Validate JWT tokens in WebSocket handshake
3. Close connections for unauthorized clients

Example:
```python
@router.websocket("/live-diagnostics")
async def websocket_live_diagnostics(
    websocket: WebSocket,
    token: str = Query(...),
):
    # Validate token
    user = await verify_token(token)
    if not user:
        await websocket.close(code=1008)  # Policy violation
        return
    
    await manager.connect(websocket)
    # ... rest of handler
```

### Rate Limiting

Consider implementing:
- Max connections per client/IP
- Message rate limiting
- Connection throttling

### Data Sanitization

All data sent via WebSocket should be:
- Validated for type safety
- Sanitized to prevent injection
- Limited in size to prevent DoS

## Future Enhancements

### Phase 7.1: Custom Dashboards

- Subscribe to specific resources only
- Custom update intervals per subscription
- Dashboard-specific WebSocket channels

### Phase 7.2: Alerting Integration

- Real-time alert notifications via WebSocket
- Alert acknowledgment via WebSocket
- Alert rule updates broadcast to all clients

### Phase 8: Testing & Optimization

- Load testing with 1000+ concurrent connections
- WebSocket compression
- Binary protocol for reduced bandwidth
- Clustering support for horizontal scaling

## API Reference

### WebSocket Endpoint

```
GET /api/v1/ws/live-diagnostics
```

**Query Parameters:**
- `update_interval` (optional): Integer, 1-60, default 10

**Response:** WebSocket connection

### Health Check Endpoint

```
GET /api/v1/ws/live-diagnostics/health
```

**Response:**
```json
{
  "status": "healthy",
  "active_connections": 5,
  "publisher_running": true,
  "timestamp": "2024-11-23T16:00:00Z"
}
```

## Summary

Phase 6 successfully implements WebSocket support for Live Diagnostics, providing:

✅ **True Real-Time Updates**: 10-second updates vs 30-second polling
✅ **Auto-Reconnection**: Graceful handling of connection failures
✅ **Fallback Support**: Seamless transition to polling when needed
✅ **Connection Monitoring**: Visual indicator of connection status
✅ **Resource Efficient**: Only broadcasts when clients connected
✅ **Scalable Architecture**: Supports multiple concurrent clients

**Next Steps:** Testing, documentation updates, and preparation for Phase 7 advanced features.
