# Enhanced Topology Analysis - Quick Reference

## Quick Commands

### Get Resource Attachments
```bash
# All attachments (both directions)
curl http://localhost:8000/api/v1/topology/resources/{RESOURCE_ID}/attachments

# Upstream only (what this resource connects to)
curl http://localhost:8000/api/v1/topology/resources/{RESOURCE_ID}/attachments?direction=upstream

# Downstream only (what connects to this resource)
curl http://localhost:8000/api/v1/topology/resources/{RESOURCE_ID}/attachments?direction=downstream
```

### Get Dependency Chains
```bash
# Downstream chains (what depends on this)
curl http://localhost:8000/api/v1/topology/resources/{RESOURCE_ID}/chains?direction=downstream

# Upstream chains (what this depends on)
curl http://localhost:8000/api/v1/topology/resources/{RESOURCE_ID}/chains?direction=upstream

# Limit chain depth
curl http://localhost:8000/api/v1/topology/resources/{RESOURCE_ID}/chains?max_depth=3
```

### Get Comprehensive Analysis
```bash
# Complete analysis with all metrics
curl http://localhost:8000/api/v1/topology/resources/{RESOURCE_ID}/analysis
```

### Enhanced Dependencies (Existing Endpoint)
```bash
# Now includes attachment details
curl http://localhost:8000/api/v1/topology/resources/{RESOURCE_ID}/dependencies?depth=3&direction=both
```

## Common Patterns

### Impact Analysis
```bash
# "What breaks if this fails?"
curl http://localhost:8000/api/v1/topology/resources/{RESOURCE_ID}/chains?direction=downstream
```

### Dependency Review
```bash
# "What does this depend on?"
curl http://localhost:8000/api/v1/topology/resources/{RESOURCE_ID}/attachments?direction=upstream
```

### Security Audit
```bash
# Get critical attachments
curl http://localhost:8000/api/v1/topology/resources/{RESOURCE_ID}/analysis | jq '.critical_attachments'
```

### Network Mapping
```bash
# Get all connection details (ports, protocols)
curl http://localhost:8000/api/v1/topology/resources/{RESOURCE_ID}/attachments | jq '.[].attachment_context'
```

## Response Fields Quick Reference

### Attachment Response
- `source_id`, `target_id` - Resource identifiers
- `relationship_type` - Type of connection (DEPENDS_ON, CONNECTS_TO, etc.)
- `relationship_properties` - Connection details (port, protocol, endpoint)
- `attachment_context` - Categorization and criticality
  - `relationship_category`: dependency, connectivity, deployment, security, other
  - `is_critical`: true/false

### Chain Response
- `resource_ids` - List of resource IDs in the chain
- `relationships` - List of relationship types connecting them
- `chain_length` - Number of hops in the chain
- `metadata.direction` - Direction the chain was traced

### Analysis Response
- `total_attachments` - Count of all connections
- `attachment_by_type` - Breakdown by relationship type
- `critical_attachments` - List of critical connections
- `attachment_strength` - Strength scores by type
- `dependency_chains` - All chains found
- `impact_radius` - Number of affected resources within 3 hops

## Relationship Types

### Dependency
- DEPENDS_ON (critical)
- USES

### Connectivity
- CONNECTS_TO (critical)
- ROUTES_TO (critical)
- ACCESSES

### Deployment
- DEPLOYED_TO
- BUILT_FROM
- CONTAINS

### Security
- AUTHENTICATES_WITH (critical)
- AUTHORIZES

## Filtering & Limits

### Direction Options
- `upstream` - Resources this connects to
- `downstream` - Resources that connect to this
- `both` - Both directions (default for attachments)

### Depth Limits
- `max_depth` for chains: 1-10 (default: 5)
- `depth` for dependencies: 1-10 (default: 3)

## jq Examples

### Extract Just Relationship Types
```bash
curl -s http://localhost:8000/api/v1/topology/resources/{ID}/attachments | \
  jq '[.[].relationship_type] | unique'
```

### Find Critical Attachments
```bash
curl -s http://localhost:8000/api/v1/topology/resources/{ID}/attachments | \
  jq '[.[] | select(.attachment_context.is_critical == true)]'
```

### Get Longest Chain
```bash
curl -s http://localhost:8000/api/v1/topology/resources/{ID}/chains | \
  jq 'max_by(.chain_length)'
```

### Count Attachments by Category
```bash
curl -s http://localhost:8000/api/v1/topology/resources/{ID}/attachments | \
  jq 'group_by(.attachment_context.relationship_category) | 
      map({category: .[0].attachment_context.relationship_category, count: length})'
```

### Extract All Ports in Use
```bash
curl -s http://localhost:8000/api/v1/topology/resources/{ID}/attachments | \
  jq '[.[].relationship_properties.port] | unique | sort'
```

## Python Examples

### Get and Process Attachments
```python
import requests

resource_id = "my-app-service"
response = requests.get(
    f"http://localhost:8000/api/v1/topology/resources/{resource_id}/attachments"
)
attachments = response.json()

# Filter critical attachments
critical = [a for a in attachments if a["attachment_context"]["is_critical"]]
print(f"Found {len(critical)} critical attachments")

# Group by relationship type
from collections import defaultdict
by_type = defaultdict(list)
for att in attachments:
    by_type[att["relationship_type"]].append(att)
```

### Trace Complete Dependency Chain
```python
import requests

def get_full_chain(resource_id, direction="downstream"):
    response = requests.get(
        f"http://localhost:8000/api/v1/topology/resources/{resource_id}/chains",
        params={"direction": direction, "max_depth": 10}
    )
    chains = response.json()
    
    # Find the longest chain
    if chains:
        longest = max(chains, key=lambda c: c["chain_length"])
        return longest
    return None

chain = get_full_chain("my-database")
if chain:
    print(f"Longest chain: {' -> '.join(chain['resource_names'])}")
```

### Get Impact Summary
```python
import requests

def get_impact_summary(resource_id):
    response = requests.get(
        f"http://localhost:8000/api/v1/topology/resources/{resource_id}/analysis"
    )
    analysis = response.json()
    
    print(f"Resource: {analysis['resource_name']}")
    print(f"Total Attachments: {analysis['total_attachments']}")
    print(f"Critical Attachments: {len(analysis['critical_attachments'])}")
    print(f"Impact Radius: {analysis['impact_radius']} resources")
    print(f"Max Chain Length: {analysis['metadata']['max_chain_length']}")
    
    print("\nAttachment Breakdown:")
    for rel_type, count in analysis['attachment_by_type'].items():
        strength = analysis['attachment_strength'].get(rel_type, 0)
        print(f"  {rel_type}: {count} (strength: {strength:.2f})")

get_impact_summary("my-app-service")
```

## Tips & Tricks

1. **Start Broad, Then Narrow**: Use `/analysis` first, then drill down with `/attachments` or `/chains`

2. **Use jq for Filtering**: Pipe results through jq to extract exactly what you need

3. **Check Critical First**: Always review `critical_attachments` for important connections

4. **Monitor Impact Radius**: High values indicate broad potential impact

5. **Trace Both Directions**: Run chains in both directions to get complete picture

6. **Limit Depth Initially**: Start with depth 3, increase if needed

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Empty results | Check resource ID exists, verify Neo4j has data |
| 404 error | Resource ID not found in database |
| Slow response | Reduce depth, filter by direction |
| Too many results | Use direction filter, reduce max_depth |

## See Also

- [Complete Documentation](ENHANCED_TOPOLOGY_ANALYSIS.md)
- [API Reference](../README.md#api-endpoints)
- [Risk Analysis Guide](ENHANCED_RISK_ANALYSIS.md)
