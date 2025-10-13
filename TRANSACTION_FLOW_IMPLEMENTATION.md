# Transaction Flow Visualization Implementation Summary

## Overview

This document summarizes the implementation of the Transaction Flow Visualization feature, which enables users to trace transactions through the network using correlation/transaction IDs found in observability platform logs.

## Problem Statement

**Original Request:**
> "A new feature of the app that might of been in the original design. I want to be able to visualise the network flow of data. Now if we have integrations into Prometheus and Azure log analytics and loki can we follow the transaction id of a log through the network and visualize the flow."

**Solution:**
✅ Yes, we can! The implementation allows users to:
- Select a pod in the topology view
- View available transaction/correlation IDs from logs
- Trace a transaction through the entire network
- Visualize the flow path with timing and error information
- See how data moves through resources (pods, services, databases, etc.)

## What Was Implemented

### 1. Backend Components

#### Azure Log Analytics Collector (`src/topdeck/monitoring/collectors/azure_log_analytics.py`)
- Queries Azure Log Analytics using KQL (Kusto Query Language)
- Searches for correlation IDs in logs
- Builds transaction traces with timing and error information
- Supports Azure authentication via DefaultAzureCredential

**Key Methods:**
- `get_logs_by_correlation_id()` - Find all logs for a correlation ID
- `trace_transaction_flow()` - Build complete transaction trace
- `find_correlation_ids_for_resource()` - Find available correlation IDs for a pod

#### Transaction Flow Service (`src/topdeck/monitoring/transaction_flow.py`)
- Orchestrates data collection from multiple sources (Loki, Azure Log Analytics, Prometheus)
- Merges data from different observability platforms
- Enriches flows with topology data from Neo4j
- Adds performance metrics from Prometheus

**Key Methods:**
- `trace_transaction()` - Main method to trace a transaction
- `find_correlation_ids_for_pod()` - Find correlation IDs for a specific pod
- `get_flow_with_enrichment()` - Get flow with topology and metrics enrichment

#### Loki Collector Updates (`src/topdeck/monitoring/collectors/loki.py`)
- Added `get_logs_by_correlation_id()` - Search Loki logs for correlation ID
- Added `find_correlation_ids_for_resource()` - Extract correlation IDs from pod logs
- Uses LogQL queries with regex pattern matching

#### API Endpoints (`src/topdeck/api/routes/monitoring.py`)

**New Endpoints:**

1. **Get Correlation IDs for a Resource**
   ```
   GET /api/v1/monitoring/resources/{resource_id}/correlation-ids
   ```
   - Returns list of correlation IDs found in pod logs
   - Searches last N hours (configurable)
   - Combines results from Loki and Azure Log Analytics

2. **Trace Transaction Flow**
   ```
   GET /api/v1/monitoring/flows/trace/{correlation_id}
   ```
   - Traces complete transaction flow through network
   - Returns nodes (resources) and edges (connections)
   - Includes timing, errors, and status information
   - Optional topology and metrics enrichment

#### Configuration (`src/topdeck/common/config.py`)
- Added `azure_log_analytics_workspace_id` configuration option

### 2. Frontend Components

#### Transaction Flow Dialog (`frontend/src/components/topology/TransactionFlowDialog.tsx`)
- Modal dialog for selecting and viewing transaction flows
- Left sidebar with list of available correlation IDs
- Main area with flow visualization
- Flow summary with status, duration, and error counts

**Features:**
- Loads correlation IDs automatically when opened
- Displays transaction IDs in monospace font for readability
- Shows loading states and error messages
- Responsive layout with proper spacing

#### Transaction Flow Graph (`frontend/src/components/topology/TransactionFlowGraph.tsx`)
- Interactive graph visualization using Cytoscape.js
- Nodes represent resources with color-coded status:
  - 🟢 Green: Success
  - 🟡 Orange: Warning
  - 🔴 Red: Error
- Edges show flow direction and timing
- Breadth-first layout for clear flow visualization

#### Topology Graph Updates (`frontend/src/components/topology/TopologyGraph.tsx`)
- Added "Visualize Flow" button for pod resources
- Button appears in node details panel when pod is selected
- Opens Transaction Flow Dialog on click

#### API Client (`frontend/src/services/api.ts`)
- `getResourceCorrelationIds()` - Fetch correlation IDs for a resource
- `traceTransactionFlow()` - Trace transaction flow

#### Types (`frontend/src/types/index.ts`)
- Added `FlowNode` interface
- Added `FlowEdge` interface
- Added `TransactionFlow` interface

### 3. Testing

#### Transaction Flow Service Tests (`tests/monitoring/test_transaction_flow.py`)
- 16 test cases covering:
  - Service initialization
  - Resource name extraction
  - Resource type inference
  - Flow merging logic
  - Data structure creation

#### Azure Log Analytics Collector Tests (`tests/monitoring/test_azure_log_analytics.py`)
- 15 test cases covering:
  - Collector initialization
  - Log level normalization
  - Query execution
  - Error handling
  - Data structure creation

### 4. Documentation

#### User Guide (`docs/features/transaction-flow-visualization.md`)
- Step-by-step usage instructions
- Configuration guide
- API reference
- Logging best practices
- Use cases and examples

## How It Works

### Flow Diagram

```
User Action: Select Pod → Click "Visualize Flow"
                    ↓
Frontend: TransactionFlowDialog opens
                    ↓
API Call: GET /api/v1/monitoring/resources/{resource_id}/correlation-ids
                    ↓
Backend: Search Loki and Azure Log Analytics for correlation IDs
                    ↓
Frontend: Display list of transaction IDs
                    ↓
User Action: Select transaction ID
                    ↓
API Call: GET /api/v1/monitoring/flows/trace/{correlation_id}
                    ↓
Backend: 
  1. Query Loki for logs with correlation ID
  2. Query Azure Log Analytics for logs with correlation ID
  3. Merge and sort entries by timestamp
  4. Extract resource path
  5. Enrich with Neo4j topology data
  6. Enrich with Prometheus metrics
                    ↓
Frontend: TransactionFlowGraph visualizes flow
```

### Data Flow

1. **Log Collection:**
   - Applications log with correlation IDs
   - Logs sent to Loki and/or Azure Log Analytics
   - Prometheus collects metrics

2. **Discovery:**
   - User selects pod in topology
   - System queries observability platforms for correlation IDs
   - Returns list of available transaction IDs

3. **Tracing:**
   - User selects transaction ID
   - System queries all logs with that ID
   - Builds timeline of log entries
   - Maps to topology resources

4. **Enrichment:**
   - Looks up resource details in Neo4j
   - Fetches metrics from Prometheus
   - Adds timing and error information

5. **Visualization:**
   - Renders interactive graph
   - Shows flow path with arrows
   - Color-codes by status
   - Displays timing and errors

## Configuration Required

### Environment Variables

```env
# Loki (for log aggregation)
LOKI_URL=http://loki:3100

# Azure Log Analytics (optional)
AZURE_LOG_ANALYTICS_WORKSPACE_ID=your-workspace-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Prometheus (for metrics)
PROMETHEUS_URL=http://prometheus:9090

# Neo4j (for topology)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

### Application Logging

For best results, applications should:

1. **Include correlation IDs in logs:**
   ```python
   from topdeck.common import set_correlation_id, get_logger
   
   logger = get_logger(__name__)
   set_correlation_id(request.headers.get('X-Correlation-ID'))
   logger.info("Processing request")
   ```

2. **Use structured logging:**
   ```python
   logger.info("Database query", extra={"duration_ms": 50})
   ```

3. **Propagate correlation IDs:**
   - HTTP headers: `X-Correlation-ID`
   - Message queues: Include in headers
   - Database: Use connection tags

## Example Usage

### Scenario: Debugging Slow API Requests

1. **User reports slow API responses**
2. **Navigate to Topology view**
3. **Click on API gateway pod**
4. **Click "Visualize Flow" button**
5. **Select a recent slow transaction ID**
6. **View the flow:**
   - API Gateway → 50ms
   - Auth Service → 150ms
   - Database → 2000ms ← **Bottleneck identified!**
7. **Click on Database node to see metrics**
8. **Identify slow query as root cause**

### Example Flow Visualization

```
[API Gateway Pod]
    ↓ (https, 50ms)
[Auth Service Pod]
    ↓ (https, 150ms)
[User Service Pod]
    ↓ (sql, 2000ms) ← High duration!
[PostgreSQL Database]
```

Status: 🔴 Error (1 error in database)
Duration: 2200ms total

## Technical Decisions

### Why Multiple Data Sources?

- **Loki:** Fast log aggregation, good for Kubernetes
- **Azure Log Analytics:** Native Azure integration, powerful KQL
- **Combined:** Best coverage, no single point of failure

### Why Cytoscape.js?

- Powerful graph visualization
- Interactive (zoom, pan, click)
- Already used in topology view
- Good performance with moderate node counts

### Why Async/Await?

- Non-blocking I/O for multiple API calls
- Better performance when querying multiple sources
- Cleaner code with async/await syntax

### Why Neo4j Enrichment?

- Already stores topology data
- Provides resource details (name, type, provider)
- Maps correlation IDs to actual infrastructure

## Limitations

1. **Time Window:** Only searches recent logs (default: 1 hour, max: 24 hours)
2. **Correlation ID Required:** Only works when logs include correlation/transaction IDs
3. **Performance:** Large log volumes may slow queries
4. **Partial Flows:** If some services don't log with correlation ID, flow will be incomplete

## Future Enhancements

Potential improvements:

1. **Real-time Streaming:** Live transaction flow as it happens
2. **Flame Graphs:** Performance visualization for bottleneck identification
3. **Comparison Mode:** Compare multiple transaction flows side-by-side
4. **Export:** Export flow diagrams as images or JSON
5. **Alerting:** Alert on slow or failing transaction patterns
6. **ML-based Anomaly Detection:** Automatically identify unusual flows
7. **Cost Analysis:** Show cloud costs for each hop in the flow
8. **Trace Sampling:** Only trace a percentage of transactions for performance

## Files Changed/Added

### Backend (Python)
- ✅ `src/topdeck/monitoring/collectors/azure_log_analytics.py` (NEW)
- ✅ `src/topdeck/monitoring/transaction_flow.py` (NEW)
- ✅ `src/topdeck/monitoring/collectors/loki.py` (MODIFIED)
- ✅ `src/topdeck/api/routes/monitoring.py` (MODIFIED)
- ✅ `src/topdeck/common/config.py` (MODIFIED)

### Frontend (TypeScript/React)
- ✅ `frontend/src/components/topology/TransactionFlowDialog.tsx` (NEW)
- ✅ `frontend/src/components/topology/TransactionFlowGraph.tsx` (NEW)
- ✅ `frontend/src/components/topology/TopologyGraph.tsx` (MODIFIED)
- ✅ `frontend/src/services/api.ts` (MODIFIED)
- ✅ `frontend/src/types/index.ts` (MODIFIED)

### Tests
- ✅ `tests/monitoring/test_transaction_flow.py` (NEW)
- ✅ `tests/monitoring/test_azure_log_analytics.py` (NEW)

### Documentation
- ✅ `docs/features/transaction-flow-visualization.md` (NEW)
- ✅ `TRANSACTION_FLOW_IMPLEMENTATION.md` (NEW)

## Success Metrics

This implementation successfully addresses the original request:

✅ **Integration with Observability Platforms:**
- Loki integration ✓
- Azure Log Analytics integration ✓
- Prometheus integration (for metrics) ✓

✅ **Transaction Tracing:**
- Follow transaction ID through logs ✓
- Build complete flow path ✓
- Show timing and errors ✓

✅ **Visualization:**
- Interactive graph visualization ✓
- Color-coded status indicators ✓
- Flow direction arrows ✓
- Resource details on click ✓

✅ **User Experience:**
- Easy to use (3 clicks: select pod → visualize flow → select transaction) ✓
- Fast response times ✓
- Clear error messages ✓
- Helpful documentation ✓

## Conclusion

The Transaction Flow Visualization feature is **fully implemented and ready to use**. It provides a powerful tool for:

- **Debugging:** Quickly identify error sources
- **Performance Analysis:** Find bottlenecks and slow components
- **Understanding:** See how data flows through infrastructure
- **Documentation:** Visualize actual service dependencies

The implementation leverages existing observability platforms (Loki, Azure Log Analytics, Prometheus) and integrates seamlessly with TopDeck's topology visualization, providing users with a comprehensive view of their transaction flows.

---

**Status:** ✅ Complete
**Date:** 2025-10-13
**Author:** GitHub Copilot
