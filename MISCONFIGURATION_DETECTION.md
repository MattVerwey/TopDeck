# Misconfiguration Detection

## Overview

The misconfiguration detection feature identifies common security and reliability issues in infrastructure resources. This ensures that change impact assessments and risk analyses show **resource-specific vulnerabilities** rather than generic demo data.

## Problem Solved

**Before:** Change impact analysis showed the same demo vulnerability for all resources, making it impossible to identify actual configuration issues.

**After:** Each resource is analyzed for specific misconfigurations based on its type and properties, providing actionable insights for improving infrastructure security and reliability.

## Detected Misconfigurations

The system checks for the following issues:

### 1. **No Availability Zone Redundancy** (HIGH severity)
- **Applies to:** Databases, VMs, Kubernetes clusters, Load Balancers, Storage Accounts
- **Description:** Resource is not configured across multiple availability zones
- **Impact:** Vulnerable to zone-level failures
- **Recommendation:** Enable multi-availability zone deployment

### 2. **No Replication Configured** (HIGH severity)
- **Applies to:** Databases, Storage Accounts, Redis Cache
- **Description:** No data replication or geo-redundancy enabled
- **Impact:** Risk of data loss and reduced availability
- **Recommendation:** Enable geo-replication or configure read replicas

### 3. **No Backup Configured** (CRITICAL severity)
- **Applies to:** Databases, Storage Accounts, Virtual Machines
- **Description:** No automated backups configured
- **Impact:** Risk of permanent data loss
- **Recommendation:** Enable automated backups with appropriate retention policies

### 4. **No Firewall Rules Configured** (CRITICAL severity)
- **Applies to:** Databases, VMs, Storage Accounts, Web Apps, Function Apps
- **Description:** No firewall rules or network security groups
- **Impact:** Exposed to unauthorized access
- **Recommendation:** Configure firewall rules to restrict access

### 5. **Encryption Not Enabled** (HIGH severity)
- **Applies to:** Databases, Storage Accounts, Virtual Machines
- **Description:** Encryption at rest is not enabled
- **Impact:** Sensitive data exposed to potential breaches
- **Recommendation:** Enable encryption at rest

### 6. **No Redundancy Configured** (MEDIUM severity)
- **Applies to:** Load Balancers, API Gateways, Kubernetes Clusters
- **Description:** No redundant instances configured
- **Impact:** Single point of failure
- **Recommendation:** Configure multiple instances for redundancy

### 7. **Monitoring Not Configured** (MEDIUM severity)
- **Applies to:** All resource types
- **Description:** Monitoring or diagnostics not enabled
- **Impact:** Limited visibility into performance and issues
- **Recommendation:** Enable monitoring, diagnostics, and alerting

## Risk Score Impact

Each misconfiguration adds to the resource's overall risk score:

| Severity | Risk Score Impact |
|----------|------------------|
| Critical | +25 points |
| High | +15 points |
| Medium | +8 points |
| Low | +3 points |

**Maximum Impact:** +50 points (capped to prevent unrealistic scores)

## Usage

### In Risk Assessment

Risk assessments now automatically include misconfiguration data:

```python
from topdeck.analysis.risk import RiskAnalyzer
from topdeck.storage.neo4j_client import Neo4jClient

# Create analyzer
neo4j_client = Neo4jClient(uri="bolt://localhost:7687", username="neo4j", password="password")
analyzer = RiskAnalyzer(neo4j_client)

# Analyze a resource
assessment = analyzer.analyze_resource("resource-id")

# Access misconfiguration data
print(f"Misconfigurations found: {assessment.misconfiguration_count}")
for issue in assessment.misconfigurations:
    print(f"  - {issue['title']} ({issue['severity']})")
    print(f"    {issue['description']}")
    print(f"    Fix: {issue['recommendation']}")
```

### In Change Impact Assessment

Change impact assessments include misconfiguration details for affected resources:

```python
from topdeck.change_management.service import ChangeManagementService

service = ChangeManagementService(neo4j_client)

# Create and assess a change request
change_request = service.create_change_request(
    title="Database Update",
    description="Update database version",
    change_type=ChangeType.UPDATE,
    affected_resources=["db-001"]
)

assessment = service.assess_change_impact(change_request)

# View misconfiguration data for affected resources
for resource in assessment.directly_affected_resources:
    if resource['misconfiguration_count'] > 0:
        print(f"\n{resource['name']} has {resource['misconfiguration_count']} misconfigurations:")
        for issue in resource['misconfigurations']:
            print(f"  - {issue['title']}")
```

### Standalone Misconfiguration Detection

You can also use the detector independently:

```python
from topdeck.analysis.risk.misconfiguration import MisconfigurationDetector

detector = MisconfigurationDetector()

# Analyze a resource with its properties
report = detector.detect_misconfigurations(
    resource_id="db-001",
    resource_name="production-db",
    resource_type="database",
    properties={
        "name": "production-db",
        "region": "eastus",
        # properties here...
    }
)

print(f"Risk score impact: +{report.risk_score_impact} points")
print(f"Issues: {len(report.issues)}")
print(f"Critical: {report.severity_counts['critical']}")
print(f"High: {report.severity_counts['high']}")
```

## API Response Format

The REST API now includes misconfiguration data in risk assessments:

```json
{
  "resource_id": "db-001",
  "resource_name": "production-db",
  "resource_type": "database",
  "risk_score": 78.5,
  "risk_level": "high",
  "misconfiguration_count": 3,
  "misconfigurations": [
    {
      "type": "no_backup",
      "severity": "critical",
      "title": "No Backup Configured",
      "description": "This database does not have automated backups configured...",
      "recommendation": "Enable automated backups with appropriate retention policies...",
      "affected_property": "backup_enabled"
    },
    {
      "type": "no_availability_zone",
      "severity": "high",
      "title": "No Availability Zone Redundancy",
      "description": "This database is not configured with availability zone redundancy...",
      "recommendation": "Enable multi-availability zone deployment...",
      "affected_property": "availability_zones"
    }
  ],
  "recommendations": [
    "Add redundant instances across availability zones",
    "🔧 No Backup Configured: Enable automated backups...",
    "🔧 No Availability Zone Redundancy: Enable multi-availability zone deployment..."
  ]
}
```

## Configuration Properties

The detector looks for these property names in resource data:

### Availability Zones
- `availability_zones`
- `zones`
- `zone_redundant`
- `zone_redundancy`

### Replication
- `replication_enabled`
- `geo_replication`
- `replicas`
- `replica_count`
- `replication_factor`
- `replication_type`
- `geo_redundant`
- `redundancy`

### Backup
- `backup_enabled`
- `backup_policy`
- `backup_retention_days`
- `automated_backups`
- `backup_configuration`
- `backup_vault`

### Firewall/Security
- `firewall_enabled`
- `firewall_rules`
- `network_security_group`
- `security_rules`
- `access_policies`
- `ip_rules`
- `network_acls`

### Encryption
- `encryption_enabled`
- `encrypted`
- `encryption_at_rest`
- `tde_enabled`
- `transparent_data_encryption`

### Redundancy
- `redundancy_enabled`
- `redundant_instances`
- `instance_count`
- `min_instances`
- `replica_count`

### Monitoring
- `monitoring_enabled`
- `diagnostics_enabled`
- `logs_enabled`
- `metrics_enabled`
- `alerts_configured`

## Benefits

1. **Resource-Specific Insights:** Each resource shows vulnerabilities relevant to its type and configuration
2. **Actionable Recommendations:** Clear guidance on how to fix each issue
3. **Risk Quantification:** Misconfigurations directly impact risk scores
4. **Security Compliance:** Helps identify resources that don't meet security best practices
5. **Change Impact Awareness:** Understand configuration issues before making changes

## Examples

See `examples/misconfiguration_demo.py` for a comprehensive demonstration showing:
- Database with multiple misconfigurations
- Well-configured database with no issues
- Web application without firewall
- Storage account without encryption
- Different vulnerabilities for different resource types

Run the demo:
```bash
cd /home/runner/work/TopDeck/TopDeck
PYTHONPATH=./src python3 examples/misconfiguration_demo.py
```

## Testing

Tests are included in `tests/unit/test_change_impact_improvements.py` to validate:
- Method name corrections
- Misconfiguration integration into risk assessments
- Change impact calculations with misconfigurations

## Future Enhancements

Potential improvements for future versions:

1. **Cloud Provider Specific Checks:** Add AWS/GCP/Azure specific best practices
2. **Compliance Frameworks:** Map misconfigurations to compliance standards (PCI-DSS, HIPAA, etc.)
3. **Auto-Remediation:** Generate Terraform/ARM templates to fix issues
4. **Trending:** Track misconfiguration changes over time
5. **Custom Rules:** Allow users to define custom misconfiguration checks
6. **Integration:** Connect to cloud provider APIs to automatically fetch resource properties

## Related Files

- `src/topdeck/analysis/risk/misconfiguration.py` - Detector implementation
- `src/topdeck/analysis/risk/analyzer.py` - Integration into risk analysis
- `src/topdeck/analysis/risk/models.py` - Data models
- `src/topdeck/change_management/service.py` - Change impact integration
- `examples/misconfiguration_demo.py` - Usage demonstration
