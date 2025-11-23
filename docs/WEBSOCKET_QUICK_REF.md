# WebSocket Quick Reference Card

## What Connects?

**Browser (Frontend) ←→ FastAPI Server (Backend)**

- **URL**: `ws://localhost:8000/api/v1/ws/live-diagnostics`
- **Protocol**: WebSocket (bidirectional, persistent connection)
- **Trigger**: Automatic when you open Live Diagnostics page

## How Connection is Established

```
1. User opens Live Diagnostics page
2. React component (LiveDiagnosticsPanel) mounts
3. React hook (useLiveDiagnosticsWebSocket) calls connect()
4. Browser creates WebSocket: new WebSocket('ws://...')
5. Server accepts: ConnectionManager.connect()
6. Server sends: "connected" message
7. Connection established! ✅
```

## How Connection Stays Persistent

| Component | Action | Frequency |
|-----------|--------|-----------|
| **Browser** | Keeps WebSocket object alive | Continuous |
| **Client** | Sends ping | Every 30s |
| **Server** | Responds pong | On ping |
| **Server** | Broadcasts snapshot_update | Every 10s |
| **Both** | Detect disconnection | Immediate |
| **Client** | Auto-reconnect | On disconnect |

## Visual Connection Flow

```
┌─────────────────────────┐
│ Browser                 │
│ Opens Live Diagnostics  │
└────────┬────────────────┘
         │
         │ WebSocket.connect()
         ▼
┌─────────────────────────┐
│ FastAPI Server          │
│ /ws/live-diagnostics    │
└────────┬────────────────┘
         │
         │ accept() ✅
         ▼
┌─────────────────────────┐
│ ConnectionManager       │
│ Adds to connections[]   │
└────────┬────────────────┘
         │
         │ broadcasts every 10s
         ▼
┌─────────────────────────┐
│ Browser Updates UI      │
│ Green "WebSocket" chip  │
└─────────────────────────┘
```

## How to Verify It's Working (3 Quick Ways)

### 1. UI Indicator (Fastest - 5 seconds)
```
1. Open http://localhost:3000
2. Click "Live Diagnostics"
3. Look at top right corner
4. See: 🟢 "WebSocket (Real-time)" = WORKING ✅
5. See: 🟡 "Polling (Fallback)" = Fallback mode
6. See: 🔴 "Disconnected" = Not working
```

### 2. Browser DevTools (Most Visual - 30 seconds)
```
1. Open http://localhost:3000 → Live Diagnostics
2. Press F12 (DevTools)
3. Go to Network tab
4. Click "WS" filter
5. See: Connection with messages = WORKING ✅
6. Click connection → Messages tab
7. See: Messages every 10s = Data flowing ✅
```

### 3. Health Endpoint (Programmatic - 10 seconds)
```bash
curl http://localhost:8000/api/v1/ws/live-diagnostics/health

# Response if working:
{
  "status": "healthy",
  "active_connections": 1,  # > 0 means clients connected
  "publisher_running": true, # = broadcaster active
  "timestamp": "2024-11-23T16:00:00Z"
}
```

## Message Types You'll See

### Server → Client (What browser receives)

| Type | When | What It Means |
|------|------|---------------|
| `connected` | On connect | "Welcome! You're connected" |
| `snapshot_update` | Every 10s | Full diagnostics data |
| `health_change` | On change | "Service X is now degraded" |
| `anomaly_detected` | On detect | "New anomaly in Service Y" |
| `pong` | After ping | "I'm alive" |

### Client → Server (What browser sends)

| Type | When | What It Means |
|------|------|---------------|
| `ping` | Every 30s | "Are you alive?" |
| `get_snapshot` | On click | "Send me data now" |

## Troubleshooting Quick Guide

| Problem | Indicator | Solution |
|---------|-----------|----------|
| **Server not running** | Red "Disconnected" | Start server: `uvicorn topdeck.api.main:app --port 8000` |
| **WebSocket unavailable** | Yellow "Polling" | Normal! Client auto-falls back to polling |
| **No data updates** | UI not changing | Check Neo4j/Prometheus, click Refresh |
| **Connection drops** | Reconnecting... | Auto-reconnects 5x, then falls back to polling |

## Test Command (Verify Everything)

```bash
# Start server (if not running)
uvicorn topdeck.api.main:app --host 0.0.0.0 --port 8000

# Run test script
python scripts/test_websocket.py

# Expected output:
✓ Health endpoint working
✓ Connected successfully
✓ Received welcome message
✓ Sent ping
✓ Received pong
✓ All tests passed!
```

## Configuration

**Default Settings (Production-Ready):**
```typescript
{
  updateInterval: 10,        // Broadcast every 10 seconds
  autoReconnect: true,       // Auto-reconnect on disconnect
  maxReconnectAttempts: 5,   // Try 5 times before giving up
  reconnectDelay: 3000,      // Wait 3s between attempts
  fallbackToPolling: true,   // Use polling if WebSocket fails
  pollingInterval: 30000     // Poll every 30s in fallback
}
```

**To Change Update Speed:**
```
ws://localhost:8000/api/v1/ws/live-diagnostics?update_interval=5
                                                 ↑
                                                 5 seconds (faster)
```

## Summary

✅ **WebSocket connects automatically** when you open Live Diagnostics page
✅ **Connection persists** via ping/pong keep-alive every 30s
✅ **Server broadcasts** diagnostics data every 10s to all connected clients
✅ **Auto-reconnects** up to 5 times if connection drops
✅ **Falls back to polling** if WebSocket unavailable (seamless!)
✅ **Visual indicator** shows connection status in real-time

**Key Point**: You don't need to do anything! Just open the page and it works automatically. 🎉
