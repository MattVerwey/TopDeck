# Dependency Verification Quick Reference

Quick commands and examples for multi-source dependency verification.

## Quick Start

```bash
# Verify a single dependency
curl "http://localhost:8000/api/v1/accuracy/dependencies/verify?source_id=app-1&target_id=db-1"

# Verify with longer monitoring window (7 days)
curl "http://localhost:8000/api/v1/accuracy/dependencies/verify?source_id=app-1&target_id=db-1&duration_hours=168"

# Run the demo
python examples/multi_source_verification_demo.py
```

## Verification Sources

| Source | What It Checks | Weight |
|--------|---------------|---------|
| 🌐 Azure Infrastructure | IPs, backends, VNets | 0.9 |
| 📝 Azure DevOps | Deployment configs, secrets | 0.8 |
| 🔄 Tempo | Distributed traces | 0.85 |
| 📈 Prometheus | Traffic metrics | 0.75 |

## Interpreting Results

### Confidence Levels

- **>85%**: Very High - All sources confirmed
- **70-85%**: High - Most sources confirmed
- **50-70%**: Medium - Some evidence
- **30-50%**: Low - Weak evidence
- **<30%**: None - Likely false positive

### Verification Status

- ✅ **Verified** (score ≥ 60%): Dependency confirmed by multiple sources
- ⚠️ **Needs Review** (score 40-60%): Some evidence, needs validation
- ❌ **Unverified** (score < 40%): Likely false positive

## Common Commands

### Check Stale Dependencies

```bash
# Find dependencies not seen in 7 days
curl "http://localhost:8000/api/v1/accuracy/dependencies/stale?max_age_days=7"
```

### Apply Confidence Decay

```bash
# Reduce confidence for unconfirmed dependencies
curl -X POST "http://localhost:8000/api/v1/accuracy/dependencies/decay?decay_rate=0.1&days_threshold=3"
```

### Get Accuracy Metrics

```bash
# View dependency detection accuracy for last 30 days
curl "http://localhost:8000/api/v1/accuracy/dependencies/metrics?days=30"
```

## Configuration

### Minimal (Infrastructure Only)

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

### Full Setup (All Sources)

```bash
# Neo4j (Required)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Azure DevOps (Optional)
AZURE_DEVOPS_ORG=your-org
AZURE_DEVOPS_PROJECT=your-project
AZURE_DEVOPS_PAT=your-pat

# Monitoring (Optional)
PROMETHEUS_URL=http://prometheus:9090
TEMPO_URL=http://tempo:3200
```

## Python Usage

```python
from topdeck.analysis.accuracy import MultiSourceDependencyVerifier
from topdeck.storage.neo4j_client import Neo4jClient
from datetime import timedelta

# Initialize
neo4j = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
verifier = MultiSourceDependencyVerifier(neo4j_client=neo4j)

# Verify
result = await verifier.verify_dependency(
    source_id="app-1",
    target_id="db-1",
    duration=timedelta(hours=24)
)

# Check result
if result.is_verified:
    print(f"✅ Verified with {result.overall_confidence:.0%} confidence")
    print(f"Evidence from {len(result.evidence)} sources")
else:
    print(f"❌ Not verified - only {result.verification_score:.0%} score")
```

## Example Response

```json
{
  "is_verified": true,
  "overall_confidence": 0.87,
  "verification_score": 0.92,
  "evidence": [
    {
      "source": "azure_infrastructure",
      "confidence": 0.9,
      "evidence_items": [
        "Target IPs [10.0.2.20] in backend pool",
        "Same Virtual Network"
      ]
    },
    {
      "source": "ado_code",
      "confidence": 0.85,
      "evidence_items": [
        "Connection string found",
        "Resource referenced in config"
      ]
    },
    {
      "source": "prometheus",
      "confidence": 0.8,
      "evidence_items": [
        "12,453 HTTP requests detected",
        "Active connection pool"
      ]
    },
    {
      "source": "tempo",
      "confidence": 0.88,
      "evidence_items": [
        "45 distributed traces found",
        "Direct call pattern detected"
      ]
    }
  ]
}
```

## Decision Tree

```
Has 4 sources? ────── YES ──→ Very High Confidence (>85%)
    │
    NO
    │
Has 3 sources? ────── YES ──→ High Confidence (70-85%)
    │
    NO
    │
Has 2 sources? ────── YES ──→ Medium Confidence (50-70%)
    │                          └─→ Investigate & validate
    NO
    │
Has 1 source? ─────── YES ──→ Low Confidence (30-50%)
    │                          └─→ Likely false positive
    NO
    │
    └──────────────────────────→ No Evidence (0%)
                                 └─→ Dependency doesn't exist
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No evidence | Enable more sources, check resource IDs |
| Low confidence | Increase duration_hours, enable all sources |
| False positive | Run confidence decay, check stale dependencies |
| API timeout | Reduce duration_hours, check Neo4j connection |

## See Also

- [Full Documentation](DEPENDENCY_VERIFICATION.md)
- [Enhanced Dependency Analysis](ENHANCED_DEPENDENCY_ANALYSIS.md)
- [Risk Analysis Guide](ENHANCED_RISK_ANALYSIS.md)
