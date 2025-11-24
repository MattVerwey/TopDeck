# Live Diagnostics - Recommended Improvements

**Priority Guide:** 🔴 High | 🟠 Medium | 🟢 Low

## Immediate Actions Required 🔴

### 1. Add Missing Python Dependency
**File:** `requirements.txt`

**Issue:** The alerting module imports `aiosmtplib` which is not in requirements.txt

**Fix:**
```bash
# Add to requirements.txt:
aiosmtplib==5.0.0
```

**Impact:** Without this, the application fails to start when alerting is used

**Testing:**
```bash
pip install -r requirements.txt
python -c "import aiosmtplib; print('OK')"
```

---

### 2. Document or Fix TypeScript Build Errors
**Files:** Multiple frontend components

**Issue:** MUI v7 Grid API changes cause 20+ TypeScript compilation errors

**Root Cause:** Code uses MUI v5/v6 Grid API (`item` prop) but package.json has v7

**Option A: Migration (Recommended)**
```typescript
// Before (v5/v6):
<Grid item xs={12} md={6}>

// After (v7):
<Grid size={{ xs: 12, md: 6 }}>
```

**Option B: Downgrade (Quick Fix)**
```json
{
  "@mui/material": "^6.1.0",
  "@mui/lab": "^6.0.0-beta.19"
}
```

**Impact:** Build currently fails, preventing production deployment

**Affected Files:**
- `LiveDiagnosticsPanel.tsx`
- `CustomDashboards.tsx`
- `TopFailingServicesWidget.tsx`

---

## Short-term Improvements 🟠

### 3. Resolve Dependency Version Conflicts

#### Python: types-requests vs kubernetes
**Current Issue:**
```
types-requests 2.31.0.10 depends on urllib3>=2
kubernetes 28.1.0 depends on urllib3<2.0
```

**Fix:**
```txt
# requirements-dev.txt
# Remove types-requests or pin urllib3 version
```

**Impact:** Low - only affects type checking

#### Frontend: MUI Lab version mismatch
**Current Issue:**
```
@mui/material@7.3.5 installed
@mui/lab@6.0.0-beta.19 requires @mui/material@^6.0.0
```

**Fix:** Wait for MUI Lab v7 release or downgrade material to v6

**Workaround:**
```bash
npm install --legacy-peer-deps
```

---

### 4. Fix Cytoscape Type Definitions
**Files:** `LiveTopologyGraph.tsx`, `ServiceDependencyGraph.tsx`, `TopologyGraph.tsx`

**Issue:** Type definitions don't match Cytoscape.js API

**Fix:** Create custom type declarations
```typescript
// types/cytoscape.d.ts
declare module 'cytoscape' {
  interface NodeCss {
    'shadow-blur'?: number;
    'shadow-color'?: string;
    'shadow-opacity'?: number;
  }
  
  interface EdgeCss {
    'shadow-blur'?: number;
  }
}
```

**Impact:** Eliminates 3 TypeScript errors, improves IDE support

---

### 5. Add NodeJS Types
**File:** `hooks/useLiveDiagnosticsWebSocket.ts`

**Issue:**
```typescript
const reconnectTimer = useRef<NodeJS.Timeout>();  // ❌ Cannot find namespace
```

**Fix:**
```typescript
// Option 1: Use standard Timeout type
import type { Timeout } from 'node:timers';
const reconnectTimer = useRef<Timeout>();

// Option 2: Use number type (browser-compatible)
const reconnectTimer = useRef<number>();
```

**Impact:** Fixes 2 TypeScript errors

---

## Code Quality Improvements 🟢

### 6. Remove Unused Parameters

**File:** `frontend/src/utils/topologyGrouping.ts`

**Current:**
```typescript
export function assignNodeParents(
  nodes: Resource[],  // ⚠️ Never used
  groups: Map<string, Resource[]>,
  _groupBy: 'cluster' | 'namespace' | 'resource_type' | 'cloud_provider'
): Map<string, string> {
```

**Fix:** Remove if truly unused, or document why it's kept
```typescript
export function assignNodeParents(
  groups: Map<string, Resource[]>,
  _groupBy: 'cluster' | 'namespace' | 'resource_type' | 'cloud_provider'
): Map<string, string> {
```

---

### 7. Remove Unused Imports

**File:** `frontend/src/components/diagnostics/LiveDiagnosticsPanel.tsx`

**Current:**
```typescript
import type {
  LiveDiagnosticsSnapshot,  // ⚠️ Type used in hook, not here
} from '../../types/diagnostics';
```

**Fix:** Remove unused import (type is used in the hook)

---

### 8. Replace `any` Types with Proper Types

**Files:** Multiple (52 instances total)

**Examples:**
```typescript
// Before:
const handleChange = (event: any) => { ... }

// After:
const handleChange = (event: ChangeEvent<HTMLInputElement>) => { ... }
```

**Impact:** Improves type safety, catches bugs at compile time

**Priority:** Lower since feature works, but good for long-term maintenance

---

## Testing Improvements 🟢

### 9. Add Unit Tests for Live Diagnostics Service

**File:** `tests/monitoring/test_live_diagnostics_service.py`

**Suggested Tests:**
```python
async def test_get_live_snapshot():
    """Test snapshot generation with mock data"""
    
async def test_detect_anomalies_with_ml():
    """Test ML anomaly detection integration"""
    
async def test_analyze_traffic_patterns():
    """Test traffic pattern analysis"""
    
async def test_health_score_calculation():
    """Test health score thresholds"""
```

---

### 10. Add E2E Tests for Frontend

**File:** `tests/e2e/test_live_diagnostics_ui.py`

**Suggested Tests:**
```python
def test_topology_graph_renders():
    """Test graph visualization loads"""
    
def test_anomaly_filtering():
    """Test anomaly severity filtering"""
    
def test_error_drawer_opens():
    """Test clicking node opens details"""
    
def test_websocket_connection():
    """Test real-time updates work"""
```

---

## Performance Improvements 🟢

### 11. Add Performance Telemetry

**File:** `src/topdeck/monitoring/live_diagnostics.py`

**Suggestion:** Track snapshot generation time
```python
import time
from topdeck.common.telemetry import track_metric

async def get_live_snapshot(self, duration_hours: int = 1):
    start = time.time()
    try:
        # ... existing code ...
        return snapshot
    finally:
        duration_ms = (time.time() - start) * 1000
        track_metric("live_diagnostics.snapshot_duration_ms", duration_ms)
```

**Benefit:** Monitor performance degradation over time

---

### 12. Add Caching for Topology Queries

**File:** `src/topdeck/monitoring/live_diagnostics.py`

**Current:** Every snapshot queries Neo4j for topology
```python
async def _get_topology_resources(self):
    # Query runs every time
    return await self.neo4j.query(...)
```

**Suggestion:** Cache topology for 30 seconds
```python
from functools import lru_cache
from datetime import datetime

@lru_cache(maxsize=1)
async def _get_topology_resources(self, cache_key: int):
    return await self.neo4j.query(...)

async def get_live_snapshot(self):
    # Use current minute as cache key
    cache_key = int(datetime.now().timestamp() / 30)
    resources = await self._get_topology_resources(cache_key)
```

**Benefit:** Reduces Neo4j load, improves response time

---

## Documentation Improvements 🟢

### 13. Add Migration Guide for MUI v7

**File:** `docs/FRONTEND_MUI_V7_MIGRATION.md`

**Content:**
```markdown
# MUI v7 Migration Guide

## Grid Component Changes

### Before (v5/v6):
<Grid container spacing={2}>
  <Grid item xs={12} md={6}>
    <Card>...</Card>
  </Grid>
</Grid>

### After (v7):
<Grid container spacing={2}>
  <Grid size={{ xs: 12, md: 6 }}>
    <Card>...</Card>
  </Grid>
</Grid>

## Files to Update:
- [ ] LiveDiagnosticsPanel.tsx
- [ ] CustomDashboards.tsx
- [ ] TopFailingServicesWidget.tsx
- [ ] (list all affected files)
```

---

### 14. Add Troubleshooting Guide

**File:** `docs/LIVE_DIAGNOSTICS_TROUBLESHOOTING.md`

**Suggested Sections:**
- WebSocket connection failures
- Anomaly detection not working
- Graph not rendering
- High latency issues
- Common configuration mistakes

---

## Implementation Checklist

Use this checklist to track improvements:

### Immediate (Before Deployment)
- [ ] Add `aiosmtplib==5.0.0` to requirements.txt
- [ ] Fix or document MUI v7 TypeScript errors
- [ ] Test in staging environment

### Short-term (Next Sprint)
- [ ] Resolve dependency version conflicts
- [ ] Fix Cytoscape type definitions
- [ ] Add NodeJS types for WebSocket hook
- [ ] Run full test suite with real data

### Long-term (Backlog)
- [ ] Remove unused parameters and imports
- [ ] Replace `any` types with proper types
- [ ] Add unit tests for all service methods
- [ ] Add E2E tests for all UI flows
- [ ] Add performance telemetry
- [ ] Implement topology query caching
- [ ] Create MUI v7 migration guide
- [ ] Write troubleshooting documentation

---

## Summary of Impact

| Improvement | Priority | Effort | Impact |
|-------------|----------|--------|--------|
| Add aiosmtplib | 🔴 High | 5 min | Prevents deployment failures |
| Fix MUI v7 errors | 🔴 High | 2-4 hrs | Enables successful builds |
| Resolve dep conflicts | 🟠 Medium | 1 hr | Cleaner installations |
| Fix Cytoscape types | 🟠 Medium | 1 hr | Better type safety |
| Add NodeJS types | 🟠 Medium | 15 min | Fixes WebSocket types |
| Remove unused code | 🟢 Low | 30 min | Code cleanliness |
| Replace `any` types | 🟢 Low | 4-8 hrs | Long-term maintainability |
| Add tests | 🟢 Low | 8-16 hrs | Quality assurance |
| Add telemetry | 🟢 Low | 2 hrs | Performance monitoring |
| Add caching | 🟢 Low | 1-2 hrs | Performance improvement |

**Total Effort for High Priority:** ~3-5 hours  
**Total Effort for All Improvements:** ~24-40 hours

---

## Questions for Product Owner

1. **MUI v7 Migration:** Should we migrate now or downgrade to v6?
   - Migration: More work upfront, future-proof
   - Downgrade: Quick fix, need to migrate later

2. **Test Coverage:** What's the minimum acceptable test coverage before deployment?
   - Current: 0% for Live Diagnostics (new feature)
   - Recommended: 80%+ for production

3. **Performance Requirements:** Are the current metrics acceptable?
   - Snapshot: ~500ms for 100 services
   - Graph render: ~500ms for 100 nodes
   - Any SLAs we need to meet?

4. **TypeScript Strict Mode:** Should we fix all `any` types before deployment?
   - Impact: Significant effort but better long-term
   - Alternative: Create tech debt ticket for future sprint

---

## Getting Started

To implement these improvements:

1. **Create a branch:**
   ```bash
   git checkout -b improvements/live-diagnostics
   ```

2. **Start with high priority items:**
   ```bash
   # 1. Add missing dependency
   echo "aiosmtplib==5.0.0" >> requirements.txt
   
   # 2. Test the fix
   pip install -r requirements.txt
   python -c "import aiosmtplib; print('✅ OK')"
   ```

3. **Address TypeScript errors:**
   ```bash
   cd frontend
   # Option A: Migrate to v7
   npm run build  # Fix errors one by one
   
   # Option B: Downgrade (quick fix)
   npm install @mui/material@^6.1.0
   ```

4. **Test thoroughly:**
   ```bash
   # Backend
   pytest tests/api/test_live_diagnostics_routes.py -v
   
   # Frontend
   npm run lint
   npm run build
   ```

5. **Commit and push:**
   ```bash
   git add .
   git commit -m "fix: implement high-priority Live Diagnostics improvements"
   git push origin improvements/live-diagnostics
   ```

---

**Document Created:** 2025-11-24  
**Review Reference:** LIVE_DIAGNOSTICS_REVIEW.md  
**Next Update:** After implementing improvements
