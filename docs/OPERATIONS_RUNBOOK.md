# TopDeck Operations Runbook

**Version**: 1.0  
**Last Updated**: 2025-10-22

---

## Table of Contents

1. [Overview](#overview)
2. [Daily Operations](#daily-operations)
3. [Monitoring & Alerts](#monitoring--alerts)
4. [Incident Response](#incident-response)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Emergency Procedures](#emergency-procedures)
7. [Common Tasks](#common-tasks)

---

## Overview

This runbook provides step-by-step procedures for operating TopDeck in production environments.

### Team Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| On-Call Engineer | oncall@yourcompany.com | Manager |
| Database Admin | dba@yourcompany.com | Engineering Lead |
| Security Team | security@yourcompany.com | CISO |
| Platform Team | platform@yourcompany.com | VP Engineering |

---

## Daily Operations

### 1. Morning Health Check

**Frequency**: Daily at 9:00 AM  
**Owner**: On-call engineer  
**Duration**: 15 minutes

#### Steps:

1. Check overall system health:
   ```bash
   kubectl get pods -n topdeck-prod
   ```

2. Verify all services are running:
   ```bash
   # Should see all pods in Running state
   kubectl get pods -n topdeck-prod | grep -v Running | grep -v Completed
   ```

3. Check Grafana dashboards:
   - API response times (should be < 500ms p95)
   - Error rates (should be < 1%)
   - Discovery job success rate (should be > 95%)

4. Review overnight alerts:
   ```bash
   # Check Prometheus alerts
   kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
   # Navigate to http://localhost:9090/alerts
   ```

5. Check audit logs for suspicious activity:
   ```bash
   kubectl logs -n topdeck-prod deployment/topdeck-api --tail=100 | grep "AUDIT.*CRITICAL"
   ```

#### Expected Results:
- All pods Running
- No critical alerts
- API p95 < 500ms
- Error rate < 1%

#### If Issues Found:
- See [Incident Response](#incident-response) section

---

### 2. Discovery Job Monitoring

**Frequency**: Every 8 hours (after each discovery run)  
**Owner**: On-call engineer  
**Duration**: 10 minutes

#### Steps:

1. Check discovery job completion:
   ```bash
   kubectl logs -n topdeck-prod -l app=topdeck-api --tail=500 | grep "Discovery completed"
   ```

2. Verify resource counts are reasonable:
   ```bash
   # Query Neo4j for resource counts
   kubectl exec -n topdeck-prod neo4j-0 -- \
     cypher-shell -u neo4j -p <password> \
     "MATCH (r:Resource) RETURN r.cloud_provider, count(*) as count"
   ```

3. Check for discovery errors:
   ```bash
   kubectl logs -n topdeck-prod -l app=topdeck-api --tail=1000 | grep -i "discovery.*error"
   ```

#### Expected Results:
- Discovery completes within 30 minutes
- Resource counts increase or stay stable
- No critical discovery errors

### 3. SPOF Monitoring Check

**Frequency**: Daily at 10:00 AM  
**Owner**: On-call engineer  
**Duration**: 10 minutes

#### Steps:

1. Check current SPOFs:
   ```bash
   curl http://localhost:8000/api/v1/monitoring/spof/current
   ```

2. Review SPOF statistics:
   ```bash
   curl http://localhost:8000/api/v1/monitoring/spof/statistics
   ```

3. Check for new high-risk SPOFs:
   ```bash
   curl http://localhost:8000/api/v1/monitoring/spof/current | \
     jq '[.[] | select(.risk_score > 80)]'
   ```

4. Review recent SPOF changes:
   ```bash
   curl "http://localhost:8000/api/v1/monitoring/spof/history?limit=10"
   ```

#### Expected Results:
- No new high-risk SPOFs (risk_score > 80)
- Decreasing or stable SPOF count
- SPOF scan completed within last 20 minutes

#### If Issues Found:
- High-risk SPOF detected: Create incident ticket, escalate to team
- SPOF count increasing: Review recent infrastructure changes
- SPOF scan not running: Check scheduler status and logs

---

## Monitoring & Alerts

### Alert Severity Levels

| Level | Response Time | Action Required |
|-------|---------------|-----------------|
| **Critical** | 15 minutes | Immediate action, page on-call |
| **High** | 1 hour | Investigate during business hours |
| **Medium** | 4 hours | Address within same day |
| **Low** | 24 hours | Review and plan fix |

### Key Alerts

#### 1. API Down

**Severity**: Critical  
**Trigger**: All API pods unreachable for > 2 minutes

**Response**:
```bash
# 1. Check pod status
kubectl get pods -n topdeck-prod -l app=topdeck-api

# 2. Check recent events
kubectl get events -n topdeck-prod --sort-by='.lastTimestamp' | tail -20

# 3. Check logs
kubectl logs -n topdeck-prod -l app=topdeck-api --tail=100

# 4. If pods are CrashLooping, check for resource issues
kubectl describe pod -n topdeck-prod <pod-name>

# 5. If config issue, rollback to previous version
kubectl rollout undo deployment/topdeck-api -n topdeck-prod
```

#### 2. Neo4j Connection Lost

**Severity**: Critical  
**Trigger**: API cannot connect to Neo4j for > 1 minute

**Response**:
```bash
# 1. Check Neo4j pod status
kubectl get pods -n topdeck-prod -l app=neo4j

# 2. Check Neo4j logs
kubectl logs -n topdeck-prod neo4j-0 --tail=100

# 3. Verify Neo4j is responding
kubectl exec -n topdeck-prod neo4j-0 -- \
  cypher-shell -u neo4j -p <password> "RETURN 1"

# 4. If Neo4j is down, check for disk space
kubectl exec -n topdeck-prod neo4j-0 -- df -h

# 5. Restart Neo4j if needed
kubectl delete pod -n topdeck-prod neo4j-0  # StatefulSet will recreate
```

#### 3. High Error Rate

**Severity**: High  
**Trigger**: Error rate > 5% for > 5 minutes

**Response**:
```bash
# 1. Check error types
kubectl logs -n topdeck-prod -l app=topdeck-api --tail=500 | grep ERROR

# 2. Check if specific endpoint is failing
kubectl logs -n topdeck-prod -l app=topdeck-api --tail=500 | \
  grep ERROR | awk '{print $5}' | sort | uniq -c

# 3. Check external dependencies
kubectl exec -n topdeck-prod <api-pod> -- curl -I http://redis:6379
kubectl exec -n topdeck-prod <api-pod> -- curl -I http://rabbitmq:15672

# 4. If rate limiting issue, increase limits temporarily
kubectl edit configmap topdeck-config -n topdeck-prod
```

#### 4. High-Risk SPOF Detected

**Severity**: Critical  
**Trigger**: High-risk SPOF (risk_score > 80) detected

**Response**:
```bash
# 1. Get details of high-risk SPOFs
curl http://localhost:8000/api/v1/monitoring/spof/current | \
  jq '[.[] | select(.risk_score > 80)]'

# 2. Check blast radius and dependencies
curl http://localhost:8000/api/v1/risk/resources/<resource-id>

# 3. Review recommendations
curl http://localhost:8000/api/v1/monitoring/spof/current | \
  jq '.[] | select(.risk_score > 80) | .recommendations'

# 4. Create incident ticket
# Include: resource details, blast radius, recommendations

# 5. Plan and implement redundancy
# Follow recommendations (add replicas, failover, etc.)

# 6. Verify SPOF is resolved
curl http://localhost:8000/api/v1/monitoring/spof/history | \
  jq '.[] | select(.resource_id == "<resource-id>")'
```

**Prevention**:
- Review architecture for single points of failure
- Implement redundancy for critical resources
- Add automated failover mechanisms
- Set up monitoring and alerting

#### 5. SPOF Count Increasing

**Severity**: High  
**Trigger**: SPOF count increased by > 2 in last hour

**Response**:
```bash
# 1. Check recent SPOF changes
curl "http://localhost:8000/api/v1/monitoring/spof/history?limit=20"

# 2. Identify new SPOFs
curl "http://localhost:8000/api/v1/monitoring/spof/history?limit=20" | \
  jq '.[] | select(.change_type == "new")'

# 3. Review recent infrastructure changes
kubectl get events -n topdeck-prod --sort-by='.lastTimestamp' | tail -50

# 4. Check if deployments removed redundancy
kubectl get deployments -n topdeck-prod
kubectl get statefulsets -n topdeck-prod

# 5. Investigate and plan remediation
# Review why redundancy was lost
# Plan to restore redundant resources
```

#### 6. Disk Space Low

**Severity**: High  
**Trigger**: Disk usage > 80%

**Response**:
```bash
# 1. Identify which volume is full
kubectl exec -n topdeck-prod neo4j-0 -- df -h
kubectl exec -n topdeck-prod redis-0 -- df -h

# 2. For Neo4j, compact the database
kubectl exec -n topdeck-prod neo4j-0 -- \
  cypher-shell -u neo4j -p <password> \
  "CALL db.checkpoint()"

# 3. Clean old logs
kubectl exec -n topdeck-prod <pod> -- \
  find /var/log -type f -name "*.log" -mtime +7 -delete

# 4. If still full, expand PVC
kubectl edit pvc neo4j-data -n topdeck-prod
# Update storage request and apply
```

---

## Incident Response

### Incident Response Workflow

```
1. Detect → 2. Assess → 3. Mitigate → 4. Resolve → 5. Document
```

### 1. Detection

**Sources**:
- Monitoring alerts (PagerDuty/OpsGenie)
- User reports
- Automated health checks

**First Actions**:
- Acknowledge alert
- Create incident ticket
- Notify team in Slack #topdeck-incidents

### 2. Assessment

**Priority Matrix**:

| Impact | Urgency | Priority |
|--------|---------|----------|
| High | High | P1 - Critical |
| High | Medium | P2 - High |
| Medium | High | P2 - High |
| Medium | Medium | P3 - Medium |
| Low | Any | P4 - Low |

**Initial Assessment Questions**:
- How many users affected?
- Which features are impacted?
- Is data at risk?
- Are there security implications?

### 3. Mitigation

**P1 Critical Incident**:
```bash
# 1. Engage incident commander
# 2. Set up incident bridge (Zoom/Teams)
# 3. Start incident log in shared doc

# 4. Quick mitigations:
# - Rollback recent changes
kubectl rollout undo deployment/topdeck-api -n topdeck-prod

# - Scale up resources
kubectl scale deployment topdeck-api --replicas=5 -n topdeck-prod

# - Enable maintenance mode
kubectl patch ingress topdeck-ingress -n topdeck-prod \
  --type=json -p='[{"op": "add", "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1custom-http-errors", "value": "503"}]'
```

### 4. Resolution

**Root Cause Analysis**:
1. Collect all relevant logs
2. Identify timeline of events
3. Determine root cause
4. Implement permanent fix
5. Verify resolution

**Verification Steps**:
```bash
# 1. Verify services healthy
kubectl get pods -n topdeck-prod
kubectl get svc -n topdeck-prod

# 2. Run smoke tests
./scripts/smoke-test.sh production

# 3. Monitor for 30 minutes
watch kubectl top pods -n topdeck-prod
```

### 5. Documentation

**Post-Incident Report** (within 24 hours):
- Timeline of events
- Root cause
- Impact assessment
- Actions taken
- Lessons learned
- Action items to prevent recurrence

---

## Maintenance Procedures

### 1. Scheduled Maintenance Window

**Frequency**: Monthly, second Sunday 2:00 AM - 4:00 AM  
**Owner**: Platform team  
**Notification**: 1 week advance notice

#### Pre-Maintenance Checklist:
- [ ] Backup all data
- [ ] Test rollback procedures
- [ ] Prepare maintenance scripts
- [ ] Notify users via email/Slack
- [ ] Enable maintenance mode

#### Procedure:
```bash
# 1. Enable maintenance mode
kubectl apply -f maintenance-mode.yaml

# 2. Scale down to 1 replica
kubectl scale deployment topdeck-api --replicas=1 -n topdeck-prod

# 3. Perform updates
kubectl apply -f updates/

# 4. Wait for rollout
kubectl rollout status deployment/topdeck-api -n topdeck-prod

# 5. Run smoke tests
./scripts/smoke-test.sh

# 6. Scale back up
kubectl scale deployment topdeck-api --replicas=3 -n topdeck-prod

# 7. Disable maintenance mode
kubectl delete -f maintenance-mode.yaml

# 8. Monitor for 1 hour
```

### 2. Database Maintenance

**Frequency**: Weekly, Sunday 1:00 AM  
**Owner**: DBA  
**Duration**: 30 minutes

```bash
# 1. Backup database
kubectl exec -n topdeck-prod neo4j-0 -- \
  neo4j-admin database dump neo4j --to-path=/backups/$(date +%Y%m%d)

# 2. Compact database
kubectl exec -n topdeck-prod neo4j-0 -- \
  cypher-shell -u neo4j -p <password> "CALL db.checkpoint()"

# 3. Update statistics
kubectl exec -n topdeck-prod neo4j-0 -- \
  cypher-shell -u neo4j -p <password> "CALL db.stats.collect()"

# 4. Check index health
kubectl exec -n topdeck-prod neo4j-0 -- \
  cypher-shell -u neo4j -p <password> "SHOW INDEXES"
```

---

## Emergency Procedures

### 1. Complete System Failure

**Scenario**: All systems down, data center outage

**Steps**:
1. Activate disaster recovery plan
2. Contact cloud provider support
3. Failover to backup region:
   ```bash
   # Switch DNS to DR region
   ./scripts/failover-to-dr.sh
   
   # Restore from latest backup
   ./scripts/restore-from-backup.sh
   ```
4. Communicate with users
5. Document timeline

### 2. Security Breach

**Scenario**: Unauthorized access detected

**Immediate Actions**:
```bash
# 1. Isolate affected systems
kubectl scale deployment topdeck-api --replicas=0 -n topdeck-prod

# 2. Rotate all credentials
./scripts/rotate-credentials.sh

# 3. Review audit logs
kubectl logs -n topdeck-prod -l app=topdeck-api | grep "AUDIT.*SUSPICIOUS"

# 4. Contact security team
# 5. Preserve evidence
kubectl logs -n topdeck-prod -l app=topdeck-api > /secure/evidence/logs-$(date +%Y%m%d-%H%M%S).txt
```

### 3. Data Corruption

**Scenario**: Database corruption detected

**Steps**:
1. Stop all writes:
   ```bash
   kubectl scale deployment topdeck-api --replicas=0 -n topdeck-prod
   ```
2. Assess damage:
   ```bash
   kubectl exec -n topdeck-prod neo4j-0 -- neo4j-admin check-database
   ```
3. Restore from backup:
   ```bash
   ./scripts/restore-backup.sh latest
   ```
4. Verify data integrity
5. Resume operations

---

## Common Tasks

### Update TopDeck Version

```bash
# 1. Pull latest image
docker pull your-registry/topdeck-api:v1.2.0

# 2. Update deployment
kubectl set image deployment/topdeck-api \
  api=your-registry/topdeck-api:v1.2.0 \
  -n topdeck-prod

# 3. Monitor rollout
kubectl rollout status deployment/topdeck-api -n topdeck-prod

# 4. If issues, rollback
kubectl rollout undo deployment/topdeck-api -n topdeck-prod
```

### Add New User

```bash
# 1. Create user via API
curl -X POST https://api.topdeck.yourcompany.com/api/auth/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@company.com",
    "password": "temp-password",
    "roles": ["viewer"]
  }'

# 2. User changes password on first login
```

### View Audit Logs

```bash
# Recent audit events
kubectl logs -n topdeck-prod -l app=topdeck-api --tail=1000 | grep "AUDIT"

# Specific user activity
kubectl logs -n topdeck-prod -l app=topdeck-api | grep "AUDIT.*username=john.doe"

# Failed login attempts
kubectl logs -n topdeck-prod -l app=topdeck-api | grep "AUDIT.*LOGIN_FAILURE"
```

### Clear Cache

```bash
# Clear Redis cache
kubectl exec -n topdeck-prod redis-0 -- redis-cli FLUSHDB

# Restart API to rebuild caches
kubectl rollout restart deployment/topdeck-api -n topdeck-prod
```

---

## Appendix

### Useful Commands

```bash
# Get pod shell
kubectl exec -it -n topdeck-prod <pod-name> -- /bin/sh

# Port forward for local access
kubectl port-forward -n topdeck-prod svc/topdeck-api 8000:8000

# View resource usage
kubectl top pods -n topdeck-prod
kubectl top nodes

# Get cluster info
kubectl cluster-info
kubectl get nodes

# View events
kubectl get events -n topdeck-prod --sort-by='.lastTimestamp'
```

### Contact Information

- **On-Call Rotation**: https://pagerduty.com/schedules/topdeck
- **Incident Channel**: #topdeck-incidents (Slack)
- **Documentation**: https://wiki.yourcompany.com/topdeck
- **Monitoring**: https://grafana.yourcompany.com/dashboards/topdeck

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-22  
**Next Review Date**: 2025-11-22
