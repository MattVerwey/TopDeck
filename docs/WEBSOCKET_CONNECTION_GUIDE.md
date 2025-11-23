# WebSocket Connection Guide - How It Works & How to Verify

## How the WebSocket Connection Works

### 1. Connection Flow

**Frontend (Browser) → Backend (FastAPI Server)**

```
1. Browser opens WebSocket connection
   ws://localhost:8000/api/v1/ws/live-diagnostics?update_interval=10
   
2. Server accepts connection (ConnectionManager.connect())
   - Adds client to active_connections list
   - Logs connection with client info
   
3. Server sends welcome message
   {"type": "connected", "message": "Connected to live diagnostics WebSocket"}
   
4. Publisher starts broadcasting (if not already running)
   - Fetches diagnostics snapshot every 10 seconds
   - Broadcasts to all connected clients
   
5. Client receives and processes messages
   - snapshot_update: Full diagnostics data
   - health_change: Service status changed
   - anomaly_detected: New anomaly found
   
6. Keep-alive mechanism
   - Client sends ping every 30 seconds
   - Server responds with pong
```

### 2. Connection Lifecycle

```
┌─────────────┐
│   Browser   │
│  (Client)   │
└──────┬──────┘
       │
       │ 1. WebSocket.connect()
       ▼
┌─────────────────────────────────┐
│   FastAPI Server                │
│   /api/v1/ws/live-diagnostics  │
└──────┬──────────────────────────┘
       │
       │ 2. accept() + add to connections
       ▼
┌─────────────────────────────────┐
│   ConnectionManager             │
│   active_connections: [ws1]     │
└──────┬──────────────────────────┘
       │
       │ 3. has_connections() = true
       ▼
┌─────────────────────────────────┐
│   DiagnosticsUpdatePublisher    │
│   Broadcasts every 10s          │
└──────┬──────────────────────────┘
       │
       │ 4. snapshot_update messages
       ▼
┌─────────────┐
│   Browser   │
│   Updates   │
│   UI        │
└─────────────┘
```

## How the WebSocket is Used in the App

### Automatic Connection on Page Load

When you navigate to the Live Diagnostics page:

1. **React Component Mounts** (`LiveDiagnosticsPanel.tsx`)
   ```typescript
   const { snapshot, connectionStatus } = useLiveDiagnosticsWebSocket({
     updateInterval: 10,
     autoReconnect: true,
     fallbackToPolling: true
   });
   ```

2. **Hook Establishes Connection** (`useLiveDiagnosticsWebSocket.ts`)
   ```typescript
   useEffect(() => {
     connect(); // Automatically connects on mount
     return () => disconnect(); // Cleans up on unmount
   }, []);
   ```

3. **Browser Creates WebSocket**
   ```javascript
   const ws = new WebSocket('ws://localhost:8000/api/v1/ws/live-diagnostics?update_interval=10');
   ```

4. **Connection Status Updates**
   ```typescript
   connectionStatus = {
     connected: true,
     connectionType: 'websocket',
     reconnectAttempts: 0
   }
   ```

### What Maintains the Persistent Connection

The connection stays open because:

1. **Browser keeps WebSocket alive**: The WebSocket object in the browser maintains an open TCP connection
2. **Ping/Pong mechanism**: Client sends ping every 30 seconds, server responds with pong
3. **Auto-reconnection**: If connection drops, client automatically tries to reconnect (up to 5 attempts)
4. **Publisher broadcasts**: Server continuously sends updates every 10 seconds while clients are connected

## How to Verify It's Working

### Method 1: Browser Developer Tools (Easiest)

1. **Open TopDeck in browser**
   ```
   http://localhost:3000
   ```

2. **Navigate to Live Diagnostics page**
   - Click "Live Diagnostics" in the sidebar

3. **Open Browser DevTools** (F12 or Right-click → Inspect)
   - Go to **Network** tab
   - Filter by **WS** (WebSocket)
   - Look for connection to `/api/v1/ws/live-diagnostics`

4. **Verify Connection**
   - Connection status should show "101 Switching Protocols" (success)
   - You should see messages flowing in the **Messages** sub-tab
   - Green indicator in UI showing "WebSocket (Real-time)"

**Screenshot locations:**
- Network tab: Shows WebSocket connection
- Messages tab: Shows real-time messages being received
- UI: Connection status indicator (green = WebSocket, yellow = polling, red = disconnected)

### Method 2: Python Test Script (Programmatic)

1. **Start the API server**
   ```bash
   cd /home/runner/work/TopDeck/TopDeck
   uvicorn topdeck.api.main:app --host 0.0.0.0 --port 8000
   ```

2. **Run the test script**
   ```bash
   python scripts/test_websocket.py
   ```

3. **Expected output**
   ```
   ============================================================
   Live Diagnostics WebSocket Test
   ============================================================
   
   Health check: {'status': 'healthy', 'active_connections': 0, ...}
   ✓ Health endpoint working
   
   Connecting to WebSocket...
   ✓ Connected successfully
   ✓ Received welcome message: Connected to live diagnostics WebSocket
   ✓ Sent ping
   ✓ Received pong
   ✓ Requested snapshot
   
   Listening for messages (5 seconds)...
     1. Received snapshot_update message
     2. Received snapshot_update message
   
   ✓ WebSocket test completed successfully
   
   ============================================================
   ✓ All tests passed!
   ============================================================
   ```

### Method 3: Health Check Endpoint (Quick Check)

**Check if WebSocket server is running:**
```bash
curl http://localhost:8000/api/v1/ws/live-diagnostics/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "active_connections": 2,
  "publisher_running": true,
  "timestamp": "2024-11-23T16:00:00Z"
}
```

**What to look for:**
- `status`: "healthy" means WebSocket endpoint is running
- `active_connections`: Number of currently connected clients (0 if no one is connected)
- `publisher_running`: true if the broadcaster is active

### Method 4: Server Logs (Debugging)

**Start server with logging:**
```bash
uvicorn topdeck.api.main:app --host 0.0.0.0 --port 8000 --log-level info
```

**Look for these log messages:**
```
INFO:     WebSocket connected client=('127.0.0.1', 54321) total_connections=1
INFO:     Started diagnostics update publisher update_interval=10
INFO:     WebSocket disconnected client=('127.0.0.1', 54321) total_connections=0
```

## Troubleshooting

### "WebSocket connection failed"

**Problem:** Browser can't connect to WebSocket

**Check:**
1. Is API server running? `curl http://localhost:8000/health`
2. Is WebSocket endpoint registered? Check `http://localhost:8000/api/docs` for `/ws/live-diagnostics`
3. Firewall blocking WebSocket? Try from localhost first

**Solution:**
- Restart API server
- Check browser console for error details
- Client will automatically fall back to polling

### "Connection status shows Polling (Fallback)"

**Problem:** WebSocket failed, using polling instead

**This is normal when:**
- API server is not running
- WebSocket endpoint unavailable
- Network blocks WebSocket protocol

**What happens:**
- Client tries WebSocket 5 times (with 3-second delays)
- After 5 failed attempts, switches to HTTP polling (30-second intervals)
- Yellow indicator in UI shows "Polling (Fallback)"
- Still works, just slower updates (30s vs 10s)

### "No messages received"

**Problem:** Connected but no data flowing

**Check:**
1. Health endpoint shows `publisher_running: true`?
2. Neo4j database accessible?
3. Prometheus metrics available?
4. Any errors in server logs?

**Solution:**
- Check server logs for errors
- Verify Neo4j and Prometheus connections
- Request manual snapshot: Click "Refresh" button in UI

## Connection Confirmation Checklist

✅ **WebSocket is working if:**

1. **UI Shows**: Green chip with "WebSocket (Real-time)" and Wifi icon
2. **Network Tab**: WS connection with 101 status and flowing messages
3. **Health Endpoint**: `active_connections > 0` and `publisher_running: true`
4. **Server Logs**: "WebSocket connected" messages appear
5. **Data Updates**: Diagnostics data refreshes every 10 seconds
6. **Test Script**: `python scripts/test_websocket.py` passes all tests

✅ **Polling fallback is working if:**

1. **UI Shows**: Yellow chip with "Polling (Fallback)" and CloudQueue icon
2. **Network Tab**: Regular HTTP requests to `/live-diagnostics/snapshot` every 30s
3. **Data Updates**: Diagnostics data refreshes every 30 seconds

## Example: Full Verification Flow

```bash
# Terminal 1: Start API server
cd /home/runner/work/TopDeck/TopDeck
uvicorn topdeck.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Check health
curl http://localhost:8000/api/v1/ws/live-diagnostics/health
# Should show: {"status": "healthy", "active_connections": 0, ...}

# Terminal 3: Run test
python scripts/test_websocket.py
# Should show: ✓ All tests passed!

# Browser: Open http://localhost:3000 → Live Diagnostics
# Should show: Green "WebSocket (Real-time)" indicator

# Browser DevTools: Network → WS tab
# Should show: Active WebSocket connection with messages
```

## Connection Architecture Summary

```
┌──────────────────────────────────────────────────────────┐
│                        Browser                            │
│                                                           │
│  LiveDiagnosticsPanel (React Component)                  │
│         ↓                                                 │
│  useLiveDiagnosticsWebSocket (React Hook)                │
│         ↓                                                 │
│  WebSocket API (Browser Native)                          │
└────────────┬─────────────────────────────────────────────┘
             │
             │ ws://localhost:8000/api/v1/ws/live-diagnostics
             │
┌────────────▼─────────────────────────────────────────────┐
│                    FastAPI Server                         │
│                                                           │
│  /api/v1/ws/live-diagnostics (WebSocket Endpoint)        │
│         ↓                                                 │
│  ConnectionManager (Tracks active connections)           │
│         ↓                                                 │
│  DiagnosticsUpdatePublisher (Broadcasts every 10s)       │
│         ↓                                                 │
│  LiveDiagnosticsService (Fetches data)                   │
│         ↓                                                 │
│  Neo4j + Prometheus (Data sources)                       │
└───────────────────────────────────────────────────────────┘
```

**Persistent Connection:** The WebSocket stays open as long as:
- Browser page is open
- API server is running
- Network connection is stable
- No errors occur

**Automatic Reconnection:** If connection drops:
- Client waits 3 seconds
- Tries to reconnect (attempt 1/5)
- Repeats up to 5 times
- Falls back to polling if all fail

This ensures **continuous real-time updates** with **graceful degradation** when WebSocket is unavailable.
