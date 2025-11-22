# Risk Scoring Methodology

## Overview

TopDeck's risk scoring system assesses the risk of deploying changes or failures for cloud resources. The scoring is based on **industry research** and follows the standard formula:

```
Risk = Likelihood × Impact
```

This document explains how risk scores are calculated based on resource type, characteristics, and dependencies.

## Research Foundation

Our risk scoring methodology is based on:

1. **Microsoft Defender for Cloud** - Risk prioritization engine
2. **Azure Advisor** - Critical risk identification  
3. **NIST Cyber Risk Scoring** - Industry standards
4. **OWASP Risk Rating** - Security risk methodology
5. **Cloud Architecture Best Practices** - Cascading failure patterns

### Key Research Findings

- **Entry points** (API gateways, load balancers) can block access to ALL downstream services
- **Security resources** (Key Vault, auth) affect entire infrastructure if compromised
- **Data stores** have different risk profiles than storage (compliance, recovery complexity)
- **Infrastructure** (Kubernetes, clusters) failures cascade to all hosted workloads
- **Messaging systems** affect transaction integrity and async communication
- **Redundancy** significantly reduces risk, especially for infrastructure components

## Resource Impact Categories

Resources are categorized by their primary failure mode:

### 1. Entry Point (Highest Impact Multiplier: 1.3x)
**Resources:** API Gateway, Application Gateway, Load Balancer, Front Door, Traffic Manager

**Failure Characteristic:** Blocks access to all downstream services
- Single point of failure for traffic routing
- Affects all backend services simultaneously
- Can cause cascading failures through retry storms
- High visibility to end users

**Examples:**
- API Gateway failure blocks all API calls
- Load Balancer failure makes all backend services unreachable

### 2. Security (Impact Multiplier: 1.25x)
**Resources:** Key Vault, Authentication, Active Directory, Identity Provider

**Failure Characteristic:** Credential leaks or access failures affect entire infrastructure
- Compromised Key Vault exposes all secrets
- Auth failure blocks all user access
- Wide-ranging security implications
- Difficult to recover from

**Examples:**
- Key Vault down prevents services from accessing secrets
- Auth service failure locks out all users

### 3. Data Store (Impact Multiplier: 1.15x)
**Resources:** SQL Database, Cosmos DB, PostgreSQL, MySQL, Redis Cache

**Failure Characteristic:** Data availability, integrity, and compliance risk
- Business-critical data at stake
- Compliance requirements (GDPR, HIPAA)
- Complex recovery procedures
- Potential data loss

**Examples:**
- Database failure blocks data access for dependent services
- Cache failure degrades performance significantly

### 4. Infrastructure (Impact Multiplier: 1.2x)
**Resources:** AKS, EKS, GKE, Kubernetes, VM Scale Sets

**Failure Characteristic:** Cascades to all hosted workloads
- Hosts multiple services
- Failure brings down all workloads
- Requires infrastructure-level recovery
- Long recovery times

**Examples:**
- AKS cluster failure affects all deployed applications
- VM scale set failure impacts all instances

### 5. Messaging (Impact Multiplier: 1.1x)
**Resources:** Service Bus, Event Hub, Event Grid, Queues

**Failure Characteristic:** Message loss, transaction integrity, async communication
- Affects event-driven architecture
- Potential message/data loss
- Transaction processing delays
- Difficult to replay lost messages

**Examples:**
- Service Bus failure causes message loss
- Event Hub down affects event streaming

### 6. Compute (Impact Multiplier: 1.0x - Baseline)
**Resources:** Web Apps, Function Apps, VMs, Pods, Container Instances

**Failure Characteristic:** Service availability
- Individual service outage
- Usually can be replaced/restarted
- Standard recovery procedures

**Examples:**
- Web app failure affects single application
- Pod failure replaced by orchestrator

### 7. Storage (Impact Multiplier: 0.9x)
**Resources:** Blob Storage, File Storage, Storage Accounts, Data Lake

**Failure Characteristic:** Data availability (usually backed up)
- Data typically backed up
- Can restore from backup
- Lower compliance risk than databases
- Longer acceptable recovery time

**Examples:**
- Blob storage outage affects file access
- Can restore from backup/replication

### 8. Networking (Impact Multiplier: 0.85x - Lowest)
**Resources:** Virtual Networks, Subnets, NSGs, VPN Gateways

**Failure Characteristic:** Connectivity issues
- Usually redundant
- Alternative routes often available
- Infrastructure-level resource
- Lower direct business impact

**Examples:**
- VNet failure can route through alternate
- NSG misconfiguration affects connectivity

## Criticality Factors by Resource Type

### Critical Tier (45-35 points)

| Resource Type | Base Score | Reasoning |
|--------------|------------|-----------|
| Key Vault | 45 | Credential leaks affect entire infrastructure |
| Authentication | 45 | Auth failures block all user access |
| Active Directory | 40 | Identity provider affects all services |
| API Gateway | 35 | Central entry point, bottleneck for all APIs |
| Application Gateway | 35 | Application delivery affects all backends |
| SQL Database | 35 | Business-critical structured data |
| Cosmos DB | 35 | Mission-critical NoSQL data |

### High Tier (34-28 points)

| Resource Type | Base Score | Reasoning |
|--------------|------------|-----------|
| SQL Server | 33 | Hosts multiple databases |
| PostgreSQL Server | 33 | Relational database platform |
| Front Door | 33 | Global entry point |
| AKS/EKS/GKE | 32 | Container orchestration, multiple workloads |
| Service Bus Namespace | 32 | Message infrastructure |
| Service Bus Topic/Queue | 30 | Messaging channels |
| Event Hub | 30 | Event streaming platform |
| Redis Cache | 28 | Performance-critical in-memory cache |

### Medium-High Tier (27-20 points)

| Resource Type | Base Score | Reasoning |
|--------------|------------|-----------|
| Load Balancer | 26 | Traffic routing for backend services |
| Web App | 22 | User-facing application |
| Function App | 20 | Serverless compute |

### Medium Tier (19-12 points)

| Resource Type | Base Score | Reasoning |
|--------------|------------|-----------|
| Container Registry | 18 | Deployment dependency |
| VM Scale Set | 18 | Auto-scaling compute group |
| Blob Storage | 16 | Object storage |
| Express Route | 15 | Dedicated connectivity |
| VM | 15 | Single compute instance |

### Low Tier (11-5 points)

| Resource Type | Base Score | Reasoning |
|--------------|------------|-----------|
| VPN Gateway | 12 | VPN connectivity |
| DNS Zone | 12 | Name resolution |
| NSG | 10 | Firewall rules |
| Virtual Network | 8 | Network isolation |
| Subnet | 6 | Network segment |

## Risk Score Calculation

The final risk score (0-100) is calculated using multiple factors:

### Formula Components

```python
# 1. Base criticality (from resource type)
base_criticality = CRITICALITY_FACTORS[resource_type]

# 2. Impact category multiplier
multiplier = CATEGORY_MULTIPLIERS[impact_category]
base_criticality *= multiplier

# 3. Additional factors
if is_spof:
    base_criticality += 15

if is_infrastructure and not has_redundancy:
    base_criticality += 20

if dependents_count > 10:
    base_criticality += 20
elif dependents_count > 5:
    base_criticality += 10
elif dependents_count > 0:
    base_criticality += 5

# 4. Calculate contributions from other factors
dependency_contribution = (dependents_count / 50) * 100 * 0.833
failure_contribution = deployment_failure_rate * 100 * 0.667
recency_contribution = recency_risk * 0.333

# 5. Apply redundancy multiplier
if not has_redundancy:
    redundancy_multiplier = 1.2  # 20% increase
else:
    redundancy_multiplier = 0.85  # 15% reduction

# 6. Final score
score = (base_criticality + dependency_contribution + 
         failure_contribution + recency_contribution) * redundancy_multiplier

# Ensure bounds
score = max(0, min(100, score))
```

### Risk Levels

| Score Range | Risk Level | Description |
|-------------|-----------|-------------|
| 75-100 | CRITICAL | Deploy only in maintenance windows, full rollback plan |
| 50-74 | HIGH | Careful deployment, monitor closely, canary recommended |
| 25-49 | MEDIUM | Standard deployment procedures, good monitoring |
| 0-24 | LOW | Low risk, standard monitoring |

## Special Considerations

### Infrastructure Without Redundancy

Infrastructure resources (AKS, load balancers, gateways) without redundancy receive a **+20 point boost** to their criticality score. This is because:

1. Single cluster/instance can bring down multiple services
2. No failover capability
3. Extended recovery time
4. High blast radius

**Example:**
- AKS with HA: Base 32 * 1.2 (infrastructure) * 0.85 (has redundancy) = ~32 points
- AKS without HA: (Base 32 * 1.2 + 20 (no HA bonus)) * 1.2 (no redundancy) = ~70 points
  - Detailed: (32 * 1.2 + 20) = 58.4; 58.4 * 1.2 = 70.08

### Single Point of Failure (SPOF)

Resources identified as SPOFs receive **+15 points** boost. A resource is a SPOF if:
- It has dependents
- It has no redundant alternatives
- Failure would directly impact downstream services

### High Dependent Count

Resources with many dependents get boosted scores:
- 10+ dependents: +20 points
- 5-10 dependents: +10 points  
- 1-4 dependents: +5 points

This reflects the larger blast radius and impact scope.

## Practical Examples

### Example 1: Production API Gateway (No Redundancy)

```
Resource: api_gateway
Dependents: 15 services
SPOF: Yes
Redundancy: No

Criticality Calculation:
- Base: 35 (API gateway)
- Category multiplier: 35 * 1.3 = 45.5
- SPOF boost: +15 = 60.5
- Infrastructure without HA: +20 = 80.5
- High dependents: +20 = 100.5

Additional Factors (simplified, assuming defaults):
- Dependency contribution: ~5 (15 dependents)
- Failure contribution: 0 (no history)
- Recency contribution: 0 (no recent changes)

Final Score Calculation:
- (100.5 + 5 + 0 + 0) * 1.2 (no redundancy) = 126.6
- Capped at 100

Final Score: 100 (CRITICAL)
Risk Level: CRITICAL
```

**Recommendations:**
- ⚠️ CRITICAL RISK: Deploy only during maintenance windows
- 🔴 Single Point of Failure: Add redundancy across availability zones
- High dependency count (15 dependents): Implement circuit breakers
- Implement canary deployments to minimize blast radius

### Example 2: PostgreSQL Database (With Replicas)

```
Resource: postgresql_server
Dependents: 7 services
SPOF: No
Redundancy: Yes (read replicas)

Criticality Calculation:
- Base: 33 (PostgreSQL)
- Category multiplier: 33 * 1.15 = 37.95
- SPOF boost: 0
- Dependents (5-10): +10 = 47.95

Additional Factors (simplified, assuming defaults):
- Dependency contribution: ~2.8 (7 dependents)
- Failure contribution: 0 (no history)
- Recency contribution: 0 (no recent changes)

Final Score Calculation:
- (47.95 + 2.8 + 0 + 0) * 0.85 (has redundancy) = 43.14
- Rounded: 43

Final Score: 43 (MEDIUM)
Risk Level: MEDIUM
```

**Recommendations:**
- Monitor deployment closely and be prepared to rollback
- Has redundancy - good! Ensure failover is tested
- Consider canary deployment pattern

### Example 3: Function App (Individual Service)

```
Resource: function_app
Dependents: 2 services
SPOF: No
Redundancy: Yes (multiple instances)

Criticality Calculation:
- Base: 20 (Function App)
- Category multiplier: 20 * 1.0 = 20 (compute baseline)
- Dependents (1-4): +5 = 25

Additional Factors (simplified, assuming defaults):
- Dependency contribution: ~0.8 (2 dependents)
- Failure contribution: 0 (no history)
- Recency contribution: 0 (no recent changes)

Final Score Calculation:
- (25 + 0.8 + 0 + 0) * 0.85 (has redundancy) = 21.93
- Rounded: 22

Final Score: 22 (LOW)
Risk Level: LOW
```

**Recommendations:**
- Standard deployment procedures apply
- Monitor deployment

### Example 4: Key Vault (Secrets Management)

```
Resource: key_vault
Dependents: 12 services
SPOF: Yes (central secrets)
Redundancy: No

Criticality Calculation:
- Base: 45 (Key Vault)
- Category multiplier: 45 * 1.25 = 56.25 (security)
- SPOF boost: +15 = 71.25
- High dependents: +20 = 91.25

Additional Factors (simplified, assuming defaults):
- Dependency contribution: ~4.8 (12 dependents)
- Failure contribution: 0 (no history)
- Recency contribution: 0 (no recent changes)

Final Score Calculation:
- (91.25 + 4.8 + 0 + 0) * 1.2 (no redundancy) = 115.26
- Capped at 100

Final Score: 100 (CRITICAL)
Risk Level: CRITICAL
```

**Recommendations:**
- ⚠️ CRITICAL RISK: Deploy only during maintenance windows
- 🔴 Single Point of Failure: Consider geo-replication
- Credential impact affects all 12 dependent services
- Implement comprehensive monitoring and alerting
- Have detailed rollback procedures ready

## Using Risk Scores

### Pre-Deployment Risk Assessment

```python
from topdeck.analysis.risk import RiskAnalyzer

analyzer = RiskAnalyzer(neo4j_client)
assessment = analyzer.analyze_resource("api-gateway-prod")

if assessment.risk_score >= 75:
    print("⚠️ CRITICAL RISK - Schedule maintenance window")
    print(f"Impact: {assessment.dependents_count} services depend on this")
    print("Recommendations:")
    for rec in assessment.recommendations:
        print(f"  - {rec}")
```

### Comparing Multiple Resources

```python
# Compare risk across similar resources
resources = ["db-prod-1", "db-prod-2", "db-prod-3"]
comparison = analyzer.compare_risk_scores(resources)

print(f"Highest risk: {comparison['highest_risk']['resource_name']}")
print(f"Average risk: {comparison['average_risk_score']}")
print(f"Common factors: {comparison['common_risk_factors']}")
```

### Identifying Critical Infrastructure

```python
# Find all SPOFs
spofs = analyzer.identify_single_points_of_failure()

for spof in spofs:
    print(f"{spof.resource_name}: {spof.risk_score}")
    print(f"  Type: {spof.resource_type}")
    print(f"  Dependents: {spof.dependents_count}")
    print(f"  Blast radius: {spof.blast_radius}")
```

## Best Practices

### 1. Regularly Review High-Risk Resources
- Weekly review of resources with risk score > 75
- Monthly review of SPOFs
- Quarterly architecture review to reduce risk

### 2. Prioritize Redundancy for Critical Resources
- All resources with score > 50 should have redundancy
- Infrastructure components must have HA configuration
- Entry points require load balancing/failover

### 3. Consider Resource Type in Architecture
- Avoid single API gateway for all services
- Implement circuit breakers for entry points
- Use message queues with persistence for critical flows
- Separate critical and non-critical databases

### 4. Monitor Risk Over Time
- Track risk scores as topology changes
- Alert on new SPOFs
- Review risk before major deployments

### 5. Use Risk Scores in CI/CD
- Automated risk checks in deployment pipeline
- Require approvals for high-risk deployments
- Generate risk reports for change management

## Future Enhancements

Potential improvements to the risk scoring system:

1. **Machine Learning** - Learn from actual incidents to adjust weights
2. **Cost Impact** - Include financial impact of downtime
3. **SLA Integration** - Factor in SLA requirements
4. **Historical Data** - Use actual failure rates instead of estimates
5. **Network Exposure** - Consider public vs private resources
6. **Data Classification** - Weight by data sensitivity (PII, financial)
7. **Compliance Impact** - Consider regulatory requirements

## References

- [Microsoft Defender for Cloud - Risk Prioritization](https://learn.microsoft.com/en-us/azure/defender-for-cloud/risk-prioritization)
- [Azure Advisor - Critical Risks](https://learn.microsoft.com/en-us/azure/advisor/advisor-critical-risks)
- [NIST Cyber Risk Scoring](https://csrc.nist.gov/)
- [OWASP Risk Rating Methodology](https://owasp.org/www-community/OWASP_Risk_Rating_Methodology)
- [Microservices Cascading Failures](https://isdown.app/blog/microservices-and-cascading-failures)
