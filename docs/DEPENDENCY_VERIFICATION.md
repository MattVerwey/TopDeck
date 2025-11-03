# Multi-Source Dependency Verification

## Overview

TopDeck's multi-source dependency verification ensures high accuracy in dependency detection by corroborating findings across multiple independent data sources:

1. **Azure Infrastructure Discovery** - Network topology, IPs, backends
2. **Azure DevOps Code Analysis** - Deployment configs, secrets, storage
3. **Prometheus Metrics** - Actual traffic patterns
4. **Tempo Traces** - Distributed transaction flows

This multi-layered approach dramatically reduces false positives and increases confidence in detected dependencies.

## Why Multi-Source Verification?

### The Problem

Single-source dependency detection can produce false positives:
- A connection string in code might reference an unused database
- A network backend pool might contain IPs that aren't actively used
- A Prometheus metric might capture test traffic, not production
- A single trace might be from a debugging session

### The Solution

By requiring **evidence from multiple sources**, we increase confidence:

| Evidence Sources | Confidence Level | Interpretation |
|-----------------|------------------|----------------|
| 4 sources | Very High (>85%) | Dependency confirmed by all methods |
| 3 sources | High (70-85%) | Strong evidence across most methods |
| 2 sources | Medium (50-70%) | Some evidence, requires validation |
| 1 source | Low (30-50%) | Weak evidence, likely false positive |
| 0 sources | None (0%) | No dependency exists |

## Verification Sources

### 1. Azure Infrastructure Discovery 🌐

**What it checks:**
- IP addresses in backend pools
- Load balancer backends
- Application Gateway backends
- Network connectivity (VNets, peering)
- Endpoint references in resource properties

**Example Evidence:**
```
✓ Target IPs [10.0.2.20] found in source backend pool 'backend-pool-1'
✓ Resources in same Virtual Network
✓ Target endpoint 'sql-server.database.windows.net' referenced in source properties
```

**Weight:** 0.9 (Most reliable - actual network configuration)

### 2. Azure DevOps Code Analysis 📝

**What it checks:**
- Deployment pipeline configurations
- Connection strings in config files
- Secret references (KeyVault, passwords)
- Storage account references
- Resource name references in deployment code

**Example Evidence:**
```
✓ Target resource 'sql-db' referenced in deployment config
✓ Connection string pattern found for target in deployment
✓ Storage account reference found in config
✓ Secret/KeyVault references found in config
```

**Weight:** 0.8 (Declared dependencies in code)

### 3. Prometheus Metrics 📈

**What it checks:**
- HTTP request rates between services
- Network traffic patterns
- Connection pool usage
- Active connections

**Example Evidence:**
```
✓ Detected 1,247 HTTP requests from source to target
✓ Active connection pool detected between resources
✓ Network traffic detected between resources
```

**Weight:** 0.75 (Aggregated traffic patterns)

### 4. Tempo Distributed Traces 🔄

**What it checks:**
- Traces showing source calling target
- Parent-child span relationships
- Service interaction patterns
- Transaction flows between services

**Example Evidence:**
```
✓ Found 23 distributed traces showing interaction
✓ Trace 12ab3456... shows direct call from source to target
✓ Average latency: 45.2ms
```

**Weight:** 0.85 (Actual transaction flows)

## Using Multi-Source Verification

### API Endpoint

```bash
GET /api/v1/accuracy/dependencies/verify
  ?source_id={source_resource_id}
  &target_id={target_resource_id}
  &duration_hours=24
```

### Example Request

```bash
curl "http://localhost:8000/api/v1/accuracy/dependencies/verify?source_id=web-app-prod&target_id=sql-db-prod&duration_hours=48"
```

### Example Response

```json
{
  "source_id": "web-app-prod",
  "target_id": "sql-db-prod",
  "is_verified": true,
  "overall_confidence": 0.87,
  "verification_score": 0.92,
  "evidence": [
    {
      "source": "azure_infrastructure",
      "evidence_type": "network_topology",
      "confidence": 0.9,
      "details": {
        "evidence_items": [
          "Target IPs [10.0.2.20] found in source backend pool 'backend-1'",
          "Resources in same Virtual Network"
        ],
        "source_ips": ["10.0.1.10"],
        "target_ips": ["10.0.2.20"],
        "backend_pools_checked": 1
      },
      "verified_at": "2024-01-15T10:30:00Z"
    },
    {
      "source": "ado_code",
      "evidence_type": "deployment_config",
      "confidence": 0.85,
      "details": {
        "evidence_items": [
          "Target resource 'sql-db-prod' referenced in deployment config",
          "Connection string pattern found for target in deployment"
        ],
        "deployments_analyzed": 3
      },
      "verified_at": "2024-01-15T10:30:00Z"
    },
    {
      "source": "prometheus",
      "evidence_type": "traffic_metrics",
      "confidence": 0.8,
      "details": {
        "evidence_items": [
          "Detected 12,453 HTTP requests from source to target",
          "Active connection pool detected between resources"
        ],
        "time_range_hours": 48,
        "queries_executed": 3
      },
      "verified_at": "2024-01-15T10:30:00Z"
    },
    {
      "source": "tempo",
      "evidence_type": "distributed_traces",
      "confidence": 0.88,
      "details": {
        "evidence_items": [
          "Found 45 distributed traces showing interaction",
          "Trace 12ab3456... shows direct call from source to target"
        ],
        "traces_analyzed": 100,
        "matching_traces": 45,
        "average_latency_ms": 52.3,
        "time_range_hours": 48
      },
      "verified_at": "2024-01-15T10:30:00Z"
    }
  ],
  "recommendations": [],
  "verified_at": "2024-01-15T10:30:00Z"
}
```

## Configuration

### Environment Variables

```bash
# Neo4j (Required)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# Azure DevOps (Optional - enables code analysis)
AZURE_DEVOPS_ORG=your-organization
AZURE_DEVOPS_PROJECT=your-project
AZURE_DEVOPS_PAT=your-personal-access-token

# Prometheus (Optional - enables metrics verification)
PROMETHEUS_URL=http://prometheus:9090

# Tempo (Optional - enables trace verification)
TEMPO_URL=http://tempo:3200
```

### Minimal Setup (Infrastructure Only)

If you only have Azure infrastructure discovered:
```bash
# Only Neo4j required
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

The verifier will work with whatever sources are available and adjust confidence accordingly.

## Understanding Verification Scores

### Verification Score

Based on number and quality of evidence sources:

```
Score = base_score(source_count) × avg_confidence

Where base_score:
  4 sources: 1.0
  3 sources: 0.85
  2 sources: 0.70
  1 source: 0.50
  0 sources: 0.0
```

### Overall Confidence

Weighted average of evidence confidences:

```
Confidence = Σ(evidence.confidence × source_weight) / Σ(source_weight)

Where source_weight:
  azure_infrastructure: 0.9
  tempo: 0.85
  ado_code: 0.8
  prometheus: 0.75
```

### Verification Threshold

A dependency is considered **verified** if:
- Verification score ≥ 0.6 (60%)
- This typically requires at least 2 sources

## Python Example

```python
from topdeck.analysis.accuracy.multi_source_verifier import (
    MultiSourceDependencyVerifier,
)
from topdeck.storage.neo4j_client import Neo4jClient
from topdeck.discovery.azure.devops import AzureDevOpsDiscoverer
from topdeck.monitoring.collectors.prometheus import PrometheusCollector
from topdeck.monitoring.collectors.tempo import TempoCollector

# Initialize verifier
neo4j = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
ado = AzureDevOpsDiscoverer("org", "project", "pat")
prometheus = PrometheusCollector("http://prometheus:9090")
tempo = TempoCollector("http://tempo:3200")

verifier = MultiSourceDependencyVerifier(
    neo4j_client=neo4j,
    ado_discoverer=ado,
    prometheus_collector=prometheus,
    tempo_collector=tempo,
)

# Verify dependency
result = await verifier.verify_dependency(
    source_id="web-app",
    target_id="database",
    duration=timedelta(hours=24),
)

print(f"Verified: {result.is_verified}")
print(f"Confidence: {result.overall_confidence:.2%}")
print(f"Evidence sources: {len(result.evidence)}")
for evidence in result.evidence:
    print(f"  - {evidence.source}: {evidence.confidence:.2%}")
```

## Demo Script

Run the included demo to see multi-source verification in action:

```bash
# Start API server
make run

# In another terminal, run demo
python examples/multi_source_verification_demo.py
```

The demo will:
1. Fetch sample resources from your topology
2. Run multi-source verification
3. Display evidence from each source
4. Show verification score and confidence
5. Provide recommendations

## Best Practices

### 1. Enable All Sources

For maximum accuracy, enable all verification sources:
- Azure infrastructure discovery (always available)
- Azure DevOps integration (enables code verification)
- Prometheus metrics (enables traffic verification)
- Tempo traces (enables transaction verification)

### 2. Regular Verification

Run verification periodically:
```bash
# Check all dependencies daily
for dep in $(get_all_dependencies); do
  verify_dependency $dep
done
```

### 3. Act on Low Confidence

Dependencies with low confidence should be investigated:
- Confidence < 0.4: Likely false positive, consider removing
- Confidence 0.4-0.7: Needs more evidence, enable more sources
- Confidence > 0.7: High confidence, dependency confirmed

### 4. Monitor Stale Dependencies

Use the stale dependency endpoint to find dependencies that haven't been confirmed recently:

```bash
curl "http://localhost:8000/api/v1/accuracy/dependencies/stale?max_age_days=7"
```

### 5. Decay Unconfirmed Dependencies

Apply confidence decay to dependencies that aren't regularly confirmed:

```bash
curl -X POST "http://localhost:8000/api/v1/accuracy/dependencies/decay?decay_rate=0.1&days_threshold=3"
```

## Integration with Existing Features

### Risk Analysis

Multi-source verification enhances risk analysis:
- High-confidence dependencies are weighted more heavily
- Low-confidence dependencies are flagged for review
- Verified SPOFs have higher priority

### Topology Visualization

Verification scores can be shown in topology view:
- Line thickness based on confidence
- Color coding by verification status
- Hover tooltips showing evidence sources

### Change Impact Analysis

Verified dependencies provide more accurate change impact:
- Only verified dependencies used in blast radius
- Confidence levels affect impact severity
- Unverified dependencies highlighted for review

## Troubleshooting

### No Evidence Found

**Problem:** Verification returns 0 confidence with no evidence.

**Solutions:**
1. Ensure resources exist in Neo4j: `GET /api/v1/topology`
2. Check resource IDs are correct
3. Verify at least one data source is configured
4. Run Azure discovery if resources are missing

### Low Confidence Despite Real Dependency

**Problem:** Verification returns low confidence for known dependency.

**Solutions:**
1. Enable more verification sources (ADO, Prometheus, Tempo)
2. Increase monitoring time range: `duration_hours=168` (7 days)
3. Check if resources are actively communicating (not idle)
4. Verify monitoring tools are collecting data correctly

### False Positive Not Caught

**Problem:** Dependency has high confidence but shouldn't exist.

**Solutions:**
1. Check if dependency existed in the past (legacy config)
2. Review evidence sources for accuracy
3. Update source configurations to reflect current state
4. Run confidence decay to reduce old dependencies

## See Also

- [Enhanced Dependency Analysis Guide](ENHANCED_DEPENDENCY_ANALYSIS.md)
- [Enhanced Risk Analysis Guide](ENHANCED_RISK_ANALYSIS.md)
- [Monitoring Integration](MONITORING.md)
- [Azure DevOps Integration](AZURE_DEVOPS_INTEGRATION.md)
