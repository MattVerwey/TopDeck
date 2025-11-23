# Neo4j Performance Quick Reference

## 🚀 Quick Start

### Use Shared Connection (Required!)
```python
from topdeck.storage import get_neo4j_client

client = get_neo4j_client()  # Always use this!
```

### Batch Operations (10-100x faster)
```python
# Create/update many resources
resources = [{"id": f"r{i}", "name": f"Resource {i}"} for i in range(1000)]
client.batch_upsert_resources(resources)  # ~100ms vs ~10s

# Create many dependencies
deps = [{"source_id": "r1", "target_id": "r2", "properties": {}}]
client.batch_create_dependencies(deps)
```

### Query Caching (50x faster)
```python
# For read-only queries that are called frequently
query = "MATCH (r:Resource {id: $id}) RETURN r"
params = {"id": "resource-123"}

results = client.run_cached_query(query, params)  # Cached!
results = client.run_cached_query(query, params, ttl=600)  # Custom TTL
```

### Monitor Performance
```bash
curl http://localhost:8000/api/cache/stats
# Target hit_rate: > 80%
```

## ⚠️ Important Rules

### DON'T
- ❌ Create Neo4jClient instances directly
- ❌ Use `run_cached_query()` for CREATE/MERGE/DELETE
- ❌ Forget to use batch operations for bulk data
- ❌ Create unbounded variable-length path queries

### DO
- ✅ Use `get_neo4j_client()` everywhere
- ✅ Use batch operations for > 10 items
- ✅ Cache read-only queries
- ✅ Limit query depth to <= 5 hops
- ✅ Add LIMIT to queries

## 🔍 Common Patterns

### Pattern 1: Bulk Resource Import
```python
from topdeck.storage import get_neo4j_client

client = get_neo4j_client()

resources = [
    {"id": "vm-1", "name": "Web VM", "resource_type": "vm"},
    {"id": "db-1", "name": "Database", "resource_type": "database"},
    # ... many more
]

count = client.batch_upsert_resources(resources)
print(f"Imported {count} resources")
```

### Pattern 2: Cached Topology Query
```python
client = get_neo4j_client()

query = """
MATCH (r:Resource {resource_type: $type})
RETURN r.id, r.name
LIMIT 100
"""

# First call: hits database
results = client.run_cached_query(query, {"type": "vm"})

# Subsequent calls within TTL: uses cache
results = client.run_cached_query(query, {"type": "vm"})
```

### Pattern 3: Safe Graph Traversal
```python
# ✅ Good: Limited depth and results
query = """
MATCH path = (r:Resource {id: $id})-[*1..5]->(dep)
WITH DISTINCT dep
RETURN dep
LIMIT 1000
"""

# ❌ Bad: Unbounded depth and results
query = """
MATCH path = (r:Resource {id: $id})-[*]->(dep)
RETURN dep
"""
```

### Pattern 4: Cache Invalidation After Updates
```python
client = get_neo4j_client()

# Update data
client.batch_upsert_resources(updated_resources)

# Invalidate affected caches
client.invalidate_cache()  # Clear all
# OR
client.invalidate_cache(query, params)  # Clear specific query
```

## 📊 Performance Metrics

| Metric | Good | Needs Attention |
|--------|------|-----------------|
| Cache Hit Rate | > 80% | < 60% |
| Query Response Time | < 100ms | > 500ms |
| Bulk Import (1000) | < 200ms | > 1s |
| Connection Time | < 10ms | > 50ms |

## 🐛 Troubleshooting

### Low Cache Hit Rate
```python
# Check stats
stats = client.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']}%")

# Solutions:
# - Increase cache size
# - Increase TTL
# - Use cached queries more consistently
```

### Slow Queries
```python
# Add LIMIT and depth constraints
query = """
MATCH path = (r)-[*1..5]->(dep)  -- Limit depth to 5
RETURN dep
LIMIT 1000  -- Limit results
"""
```

### Connection Pool Exhausted
```python
# Check if you're creating clients instead of using shared one
# ❌ DON'T DO THIS:
client = Neo4jClient(...)  

# ✅ DO THIS:
client = get_neo4j_client()
```

## 📚 Full Documentation

- **Comprehensive Guide**: `docs/NEO4J_PERFORMANCE_GUIDE.md`
- **Completion Summary**: `NEO4J_PERFORMANCE_COMPLETION.md`
- **API Docs**: `http://localhost:8000/api/docs`

## 💡 Tips

1. **Always use batch operations** for > 10 items
2. **Cache read-only queries** that run frequently
3. **Limit graph traversal** to 5 hops max
4. **Monitor cache hit rate** (target: > 80%)
5. **Invalidate cache** after data changes
6. **Use LIMIT** on all queries that could return many results

---
*For questions or issues, see full documentation in `docs/NEO4J_PERFORMANCE_GUIDE.md`*
