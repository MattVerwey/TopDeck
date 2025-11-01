# Enhanced Dependency Analysis

## Overview

TopDeck now includes advanced dependency analysis features that help you understand and improve the health of your infrastructure dependencies. These features go beyond simple dependency counting to provide deep insights into dependency quality, circular dependencies, and potential issues.

## New Features

### 1. Circular Dependency Detection

Circular dependencies can cause cascading failures, deployment deadlocks, and make it difficult to reason about system behavior. This feature detects all cycles in your dependency graph.

#### Why It Matters
- **Deployment Deadlocks**: Circular dependencies can prevent clean deployments
- **Cascading Failures**: Failures can loop infinitely through the cycle
- **Complex Debugging**: Hard to understand which service is the root cause
- **Tight Coupling**: Indicates poor architectural separation

#### API Endpoint

```bash
# Check specific resource for circular dependencies
curl "http://localhost:8000/api/v1/risk/dependencies/circular?resource_id={resource-id}"

# Find all circular dependencies in infrastructure
curl "http://localhost:8000/api/v1/risk/dependencies/circular"
```

#### Example Response

```json
{
  "resource_id": "app-service-1",
  "circular_dependencies_found": 2,
  "cycles": [
    ["app-service-1", "database-1", "cache-1", "app-service-1"],
    ["app-service-1", "message-queue-1", "app-service-1"]
  ],
  "severity": "critical",
  "recommendations": [
    "Break circular dependencies by introducing event-driven architecture",
    "Use dependency injection to decouple components",
    "Consider using mediator pattern to manage complex interactions",
    "Refactor to establish clear dependency hierarchy"
  ]
}
```

#### How to Fix Circular Dependencies

1. **Event-Driven Architecture**: Replace direct dependencies with async events
   ```
   Before: Service A → Service B → Service A
   After:  Service A → Event Bus ← Service B
   ```

2. **Introduce Mediator/Orchestrator**: Add a layer that manages interactions
   ```
   Before: A ↔ B ↔ C ↔ A
   After:  A → Orchestrator ← B, C
   ```

3. **Dependency Injection**: Use interfaces and inject dependencies at runtime
   ```
   Before: Concrete class dependencies
   After:  Interface-based dependencies with inversion of control
   ```

### 2. Dependency Health Scoring

Get a comprehensive health score (0-100) for your resource's dependencies that considers multiple factors.

#### Factors Analyzed

1. **Dependency Count** (Coupling)
   - High number of dependencies = tight coupling
   - Penalty applied for > 10 dependencies
   - Indicates complexity and maintenance burden

2. **Circular Dependencies**
   - Most severe issue
   - Can cause deadlocks and cascading failures
   - Heavy penalty (20 points per cycle)

3. **Single Points of Failure in Dependency Chain**
   - Identifies SPOFs that this resource depends on
   - Increases overall risk
   - Penalty based on number of SPOF dependencies

4. **Dependency Tree Depth**
   - Deep dependency trees = complex systems
   - Harder to reason about failures
   - Penalty for depth > 5 levels

#### API Endpoint

```bash
curl "http://localhost:8000/api/v1/risk/dependencies/{resource-id}/health"
```

#### Example Response

```json
{
  "resource_id": "app-service-1",
  "health_score": 65.5,
  "health_level": "good",
  "factors": {
    "high_dependency_count": {
      "count": 15,
      "penalty": 15.0,
      "reason": "Resource depends on 15 other resources (high coupling)"
    },
    "circular_dependencies": {
      "count": 1,
      "penalty": 20.0,
      "cycles": [
        ["app-service-1", "database-1", "app-service-1"]
      ],
      "reason": "Found 1 circular dependency path(s)"
    }
  },
  "recommendations": [
    "🔴 CRITICAL: Break circular dependencies immediately - they can cause deadlocks",
    "Refactor to use event-driven architecture or introduce a mediator",
    "⚠️ Reduce coupling by consolidating dependencies or using facade pattern",
    "Consider implementing dependency injection to manage complexity"
  ]
}
```

#### Health Levels

| Score | Level | Description |
|-------|-------|-------------|
| 80-100 | Excellent | Healthy dependencies, well-structured |
| 60-79 | Good | Generally good with minor issues |
| 40-59 | Fair | Some issues that should be addressed |
| 20-39 | Poor | Significant issues requiring attention |
| 0-19 | Critical | Severe problems, immediate action needed |

### 3. Risk Comparison

Compare risk scores across multiple resources to prioritize which resources need attention.

#### Use Cases
- **Prioritization**: Which resources to focus on first?
- **Similar Resources**: Compare database instances to find the riskiest
- **Pattern Detection**: Identify common risk factors across resources
- **Resource Planning**: Understand risk distribution in your infrastructure

#### API Endpoint

```bash
# Compare up to 50 resources
curl "http://localhost:8000/api/v1/risk/compare?resource_ids=res-1,res-2,res-3"
```

#### Example Response

```json
{
  "resources_compared": 3,
  "average_risk_score": 62.5,
  "highest_risk": {
    "resource_id": "database-prod-1",
    "resource_name": "Production Database",
    "risk_score": 85.2,
    "risk_level": "critical"
  },
  "lowest_risk": {
    "resource_id": "cache-dev-1",
    "resource_name": "Dev Cache",
    "risk_score": 32.1,
    "risk_level": "medium"
  },
  "risk_distribution": {
    "critical": 1,
    "high": 1,
    "medium": 1,
    "low": 0
  },
  "common_risk_factors": [
    "2/3 resources are single points of failure",
    "3/3 resources lack redundancy"
  ],
  "all_assessments": [
    {
      "resource_id": "database-prod-1",
      "resource_name": "Production Database",
      "risk_score": 85.2,
      "risk_level": "critical",
      "is_spof": true
    }
  ]
}
```

### 4. Cascading Failure Probability

Model how a failure propagates through dependencies with realistic probability calculations.

#### How It Works

The analysis models failure propagation with decreasing probability at each level:
- **Level 1**: Initial failure (100% probability)
- **Level 2**: 30% propagation (accounting for circuit breakers)
- **Level 3**: 9% propagation (30% of 30%)
- And so on...

This accounts for:
- Circuit breakers (80% effective)
- Retry mechanisms (90% success rate)
- Fallback mechanisms (70% coverage)

#### API Endpoint

```bash
# Default initial probability of 1.0 (100%)
curl "http://localhost:8000/api/v1/risk/cascading-failure/{resource-id}"

# Custom initial failure probability
curl "http://localhost:8000/api/v1/risk/cascading-failure/{resource-id}?initial_probability=0.5"
```

#### Example Response

```json
{
  "initial_resource": "app-service-1",
  "initial_failure_probability": 1.0,
  "levels": [
    {
      "level": 1,
      "failure_probability": 0.3,
      "affected_resources": [
        {
          "resource_id": "database-1",
          "resource_name": "Primary Database",
          "resource_type": "database",
          "failure_probability": 0.3
        },
        {
          "resource_id": "cache-1",
          "resource_name": "Redis Cache",
          "resource_type": "cache",
          "failure_probability": 0.3
        }
      ]
    },
    {
      "level": 2,
      "failure_probability": 0.09,
      "affected_resources": [
        {
          "resource_id": "storage-1",
          "resource_name": "Blob Storage",
          "resource_type": "storage",
          "failure_probability": 0.09
        }
      ]
    }
  ],
  "summary": {
    "max_cascade_depth": 2,
    "total_resources_at_risk": 3,
    "expected_failures": 0.69,
    "recommendations": [
      "Implement retry with exponential backoff",
      "Add fallback mechanisms for critical dependencies",
      "Set up monitoring for cascade detection (correlated failures)",
      "Consider implementing timeout policies to prevent cascade propagation"
    ]
  }
}
```

#### Understanding the Results

- **max_cascade_depth**: How many levels deep the failure could cascade
- **total_resources_at_risk**: Total number of resources that could be affected
- **expected_failures**: Probability-weighted number of expected failures
  - Example: 0.69 means we expect ~1 resource to fail on average

## Integration with Existing Features

These new features integrate seamlessly with existing risk analysis:

### Combined Risk Assessment

```bash
# Get comprehensive risk analysis including dependency health
curl "http://localhost:8000/api/v1/risk/resources/{resource-id}/comprehensive"
```

This includes:
- Standard risk assessment
- Degraded performance scenarios
- Intermittent failure scenarios
- **NEW**: Dependency health automatically factored in

### Enhanced SPOF Detection

```bash
# Find all single points of failure
curl "http://localhost:8000/api/v1/risk/spof"
```

Now enhanced with:
- Circular dependency detection
- Dependency health scoring
- Cascading failure impact

## Best Practices

### 1. Regular Dependency Audits

Run dependency health checks regularly:
```bash
# Weekly dependency health audit script
for resource in $(get_all_resources); do
  curl "http://localhost:8000/api/v1/risk/dependencies/${resource}/health"
done
```

### 2. Monitor for Circular Dependencies

Set up automated monitoring:
```bash
# Daily circular dependency check
circles=$(curl "http://localhost:8000/api/v1/risk/dependencies/circular")
if [ $circles -gt 0 ]; then
  alert "Circular dependencies detected!"
fi
```

### 3. Prioritize with Risk Comparison

Before refactoring, compare risk scores:
```bash
# Compare all database instances
curl "http://localhost:8000/api/v1/risk/compare?resource_ids=db1,db2,db3,db4"
# Focus on the highest risk resource first
```

### 4. Use Cascading Analysis for Critical Changes

Before major changes, analyze cascade impact:
```bash
# Before updating a critical service
curl "http://localhost:8000/api/v1/risk/cascading-failure/critical-service"
# Review expected_failures and recommendations
```

## Interpreting Results

### When to Act Immediately

⚠️ **Critical Issues** requiring immediate attention:
- Circular dependencies found (any count > 0)
- Health score < 40
- Cascading failure depth > 4 levels
- Expected failures > 5 resources

### When to Plan Improvements

📋 **Issues** to address in next sprint:
- Health score 40-60
- High dependency count (> 10)
- Dependency depth > 5 levels
- SPOF in dependency chain

### Healthy Indicators

✅ **Good signs**:
- No circular dependencies
- Health score > 80
- Cascading failure depth < 3
- Expected failures < 2 resources

## Troubleshooting

### "No circular dependencies found but I know they exist"

Check that:
1. Resources have `DEPENDS_ON` relationships in Neo4j
2. Resource IDs match exactly
3. Relationship direction is correct

### "Health score seems too low"

Remember that the score penalizes:
- High dependency count (> 10)
- Any circular dependencies
- SPOFs in dependency chain
- Deep dependency trees (> 5 levels)

These are intentional to highlight areas for improvement.

### "Cascading failure probability seems too high/low"

The propagation factor (30%) is a reasonable default but may need tuning for your environment:
- More circuit breakers → lower propagation
- Fewer fallbacks → higher propagation
- Tighter coupling → higher propagation

## Future Enhancements

Planned improvements:
- Configurable propagation factors per resource type
- Historical dependency health trends
- Automated dependency refactoring suggestions
- Integration with deployment pipelines to block circular dependencies
- Dependency version tracking and compatibility analysis

## Questions?

For more information:
- [Risk Analysis Guide](ENHANCED_RISK_ANALYSIS.md)
- [Topology Analysis Guide](ENHANCED_TOPOLOGY_ANALYSIS.md)
- [API Documentation](http://localhost:8000/api/docs)
