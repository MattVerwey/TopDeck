# TopDeck Production Deployment Guide

**Version**: 1.0  
**Last Updated**: 2025-10-22  
**Status**: Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Infrastructure Setup](#infrastructure-setup)
5. [Security Configuration](#security-configuration)
6. [Deployment Steps](#deployment-steps)
7. [Monitoring & Observability](#monitoring--observability)
8. [Backup & Recovery](#backup--recovery)
9. [Scaling & Performance](#scaling--performance)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides comprehensive instructions for deploying TopDeck to a production environment. TopDeck is a multi-cloud integration and risk analysis platform that requires careful configuration of security, networking, and data storage components.

### Deployment Options

1. **Kubernetes** (Recommended for production)
2. **Docker Compose** (Suitable for small deployments)
3. **Cloud-native services** (Azure Container Apps, AWS ECS, GCP Cloud Run)

---

## Prerequisites

### Required Knowledge
- Kubernetes administration
- Container orchestration (Docker/Kubernetes)
- Cloud platform administration (Azure/AWS/GCP)
- Security best practices
- Database administration (Neo4j)

### Required Access
- Cloud platform credentials with appropriate permissions
- Container registry access
- DNS management access
- Certificate management access

### Minimum System Requirements

#### API Server
- **CPU**: 2 cores (4 cores recommended)
- **Memory**: 4 GB RAM (8 GB recommended)
- **Storage**: 20 GB (SSD recommended)

#### Neo4j Database
- **CPU**: 4 cores (8 cores recommended)
- **Memory**: 8 GB RAM (16 GB recommended)
- **Storage**: 100 GB SSD (depends on resource count)

#### Redis Cache
- **CPU**: 1 core
- **Memory**: 2 GB RAM
- **Storage**: 10 GB

#### RabbitMQ
- **CPU**: 1 core
- **Memory**: 2 GB RAM
- **Storage**: 20 GB

---

## Architecture

### Production Architecture Diagram

```
                                    ┌─────────────────┐
                                    │   Load Balancer │
                                    │   (Ingress)     │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┴────────────────────────┐
                    │                                                  │
          ┌─────────▼─────────┐                           ┌──────────▼──────────┐
          │   TopDeck API     │◄──────────────────────────│   Frontend          │
          │   (3 replicas)    │                           │   (2 replicas)      │
          └─────────┬─────────┘                           └─────────────────────┘
                    │
      ┌─────────────┼─────────────┬──────────────┬────────────────┐
      │             │              │              │                │
┌─────▼──────┐ ┌───▼────────┐ ┌──▼──────────┐ ┌─▼─────────┐  ┌──▼──────────┐
│  Neo4j     │ │  Redis     │ │  RabbitMQ   │ │ Prometheus│  │   Loki      │
│  (Primary) │ │  (Cache)   │ │  (Queue)    │ │ (Metrics) │  │   (Logs)    │
└────────────┘ └────────────┘ └─────────────┘ └───────────┘  └─────────────┘
      │
┌─────▼──────┐
│  Neo4j     │
│  (Replica) │
└────────────┘
```

### Component Overview

| Component | Purpose | Replicas | Dependencies |
|-----------|---------|----------|--------------|
| API Server | REST API and discovery engine | 3+ | Neo4j, Redis, RabbitMQ |
| Frontend | React web interface | 2+ | API Server |
| Neo4j | Graph database (primary) | 1 | Storage volume |
| Neo4j Replica | Read replica for queries | 1-2 | Neo4j Primary |
| Redis | Caching layer | 1 | None |
| RabbitMQ | Message queue for async tasks | 1 | None |
| Prometheus | Metrics collection | 1 | None |
| Loki | Log aggregation | 1 | None |

---

## Infrastructure Setup

### 1. Kubernetes Cluster Setup

#### Azure (AKS)

```bash
# Create resource group
az group create --name topdeck-prod --location eastus

# Create AKS cluster
az aks create \
  --resource-group topdeck-prod \
  --name topdeck-cluster \
  --node-count 5 \
  --node-vm-size Standard_D4s_v3 \
  --enable-managed-identity \
  --enable-addons monitoring \
  --network-plugin azure \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group topdeck-prod --name topdeck-cluster
```

#### AWS (EKS)

```bash
# Create EKS cluster using eksctl
eksctl create cluster \
  --name topdeck-prod \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type m5.xlarge \
  --nodes 5 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed
```

#### GCP (GKE)

```bash
# Create GKE cluster
gcloud container clusters create topdeck-prod \
  --region us-central1 \
  --num-nodes 5 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10
```

### 2. Namespace Setup

```bash
# Create namespace
kubectl create namespace topdeck-prod

# Set as default
kubectl config set-context --current --namespace=topdeck-prod

# Create service account
kubectl create serviceaccount topdeck-api
```

### 3. Storage Setup

Create persistent volumes for Neo4j, Redis, and RabbitMQ:

```yaml
# neo4j-pv.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: neo4j-data
  namespace: topdeck-prod
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 100Gi
---
# redis-pv.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-data
  namespace: topdeck-prod
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi
---
# rabbitmq-pv.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rabbitmq-data
  namespace: topdeck-prod
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 20Gi
```

Apply:
```bash
kubectl apply -f neo4j-pv.yaml -f redis-pv.yaml -f rabbitmq-pv.yaml
```

---

## Security Configuration

### 1. Secrets Management

Create Kubernetes secrets for sensitive data:

```bash
# Create Neo4j credentials
kubectl create secret generic neo4j-credentials \
  --from-literal=username=neo4j \
  --from-literal=password='<strong-password>' \
  --namespace=topdeck-prod

# Create API secrets
kubectl create secret generic topdeck-api-secrets \
  --from-literal=secret-key='<random-256-bit-key>' \
  --from-literal=jwt-secret='<jwt-secret-key>' \
  --namespace=topdeck-prod

# Create cloud provider credentials
kubectl create secret generic cloud-credentials \
  --from-literal=azure-client-id='<client-id>' \
  --from-literal=azure-client-secret='<client-secret>' \
  --from-literal=azure-tenant-id='<tenant-id>' \
  --from-literal=aws-access-key-id='<access-key>' \
  --from-literal=aws-secret-access-key='<secret-key>' \
  --from-file=gcp-sa.json=./path/to/gcp-service-account.json \
  --namespace=topdeck-prod

# Create Redis password
kubectl create secret generic redis-credentials \
  --from-literal=password='<redis-password>' \
  --namespace=topdeck-prod

# Create RabbitMQ credentials
kubectl create secret generic rabbitmq-credentials \
  --from-literal=username=topdeck \
  --from-literal=password='<rabbitmq-password>' \
  --namespace=topdeck-prod
```

### 2. TLS/SSL Certificates

```bash
# Using cert-manager (recommended)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourcompany.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### 3. Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: topdeck-api-policy
  namespace: topdeck-prod
spec:
  podSelector:
    matchLabels:
      app: topdeck-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: topdeck-frontend
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: neo4j
    ports:
    - protocol: TCP
      port: 7687
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - podSelector:
        matchLabels:
          app: rabbitmq
    ports:
    - protocol: TCP
      port: 5672
```

### 4. RBAC Configuration

```yaml
# rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: topdeck-api-role
  namespace: topdeck-prod
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: topdeck-api-rolebinding
  namespace: topdeck-prod
subjects:
- kind: ServiceAccount
  name: topdeck-api
  namespace: topdeck-prod
roleRef:
  kind: Role
  name: topdeck-api-role
  apiGroup: rbac.authorization.k8s.io
```

---

## Deployment Steps

### 1. Deploy Neo4j

```yaml
# neo4j-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: topdeck-prod
spec:
  serviceName: neo4j
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.15.0-enterprise
        ports:
        - containerPort: 7474
          name: http
        - containerPort: 7687
          name: bolt
        env:
        - name: NEO4J_AUTH
          valueFrom:
            secretKeyRef:
              name: neo4j-credentials
              key: username
        - name: NEO4J_PASSWORD
          valueFrom:
            secretKeyRef:
              name: neo4j-credentials
              key: password
        - name: NEO4J_dbms_memory_heap_max__size
          value: "8G"
        - name: NEO4J_dbms_memory_pagecache_size
          value: "4G"
        volumeMounts:
        - name: data
          mountPath: /data
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
          limits:
            memory: "16Gi"
            cpu: "8"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: neo4j-data
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j
  namespace: topdeck-prod
spec:
  selector:
    app: neo4j
  ports:
  - name: http
    port: 7474
    targetPort: 7474
  - name: bolt
    port: 7687
    targetPort: 7687
  type: ClusterIP
```

Deploy:
```bash
kubectl apply -f neo4j-deployment.yaml
```

### 2. Deploy Redis

```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: topdeck-prod
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        args:
        - --requirepass
        - $(REDIS_PASSWORD)
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: password
        volumeMounts:
        - name: data
          mountPath: /data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: redis-data
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: topdeck-prod
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
```

Deploy:
```bash
kubectl apply -f redis-deployment.yaml
```

### 3. Deploy RabbitMQ

```yaml
# rabbitmq-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rabbitmq
  namespace: topdeck-prod
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rabbitmq
  template:
    metadata:
      labels:
        app: rabbitmq
    spec:
      containers:
      - name: rabbitmq
        image: rabbitmq:3-management-alpine
        ports:
        - containerPort: 5672
          name: amqp
        - containerPort: 15672
          name: management
        env:
        - name: RABBITMQ_DEFAULT_USER
          valueFrom:
            secretKeyRef:
              name: rabbitmq-credentials
              key: username
        - name: RABBITMQ_DEFAULT_PASS
          valueFrom:
            secretKeyRef:
              name: rabbitmq-credentials
              key: password
        volumeMounts:
        - name: data
          mountPath: /var/lib/rabbitmq
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: rabbitmq-data
---
apiVersion: v1
kind: Service
metadata:
  name: rabbitmq
  namespace: topdeck-prod
spec:
  selector:
    app: rabbitmq
  ports:
  - name: amqp
    port: 5672
    targetPort: 5672
  - name: management
    port: 15672
    targetPort: 15672
  type: ClusterIP
```

Deploy:
```bash
kubectl apply -f rabbitmq-deployment.yaml
```

### 4. Deploy TopDeck API

```yaml
# topdeck-api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: topdeck-api
  namespace: topdeck-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: topdeck-api
  template:
    metadata:
      labels:
        app: topdeck-api
    spec:
      serviceAccountName: topdeck-api
      containers:
      - name: api
        image: your-registry/topdeck-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: APP_ENV
          value: "production"
        - name: NEO4J_URI
          value: "bolt://neo4j:7687"
        - name: NEO4J_USERNAME
          valueFrom:
            secretKeyRef:
              name: neo4j-credentials
              key: username
        - name: NEO4J_PASSWORD
          valueFrom:
            secretKeyRef:
              name: neo4j-credentials
              key: password
        - name: REDIS_HOST
          value: "redis"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: password
        - name: RABBITMQ_HOST
          value: "rabbitmq"
        - name: RABBITMQ_USERNAME
          valueFrom:
            secretKeyRef:
              name: rabbitmq-credentials
              key: username
        - name: RABBITMQ_PASSWORD
          valueFrom:
            secretKeyRef:
              name: rabbitmq-credentials
              key: password
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: topdeck-api-secrets
              key: secret-key
        - name: ENABLE_RBAC
          value: "true"
        - name: ENABLE_AUDIT_LOGGING
          value: "true"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
---
apiVersion: v1
kind: Service
metadata:
  name: topdeck-api
  namespace: topdeck-prod
spec:
  selector:
    app: topdeck-api
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

Deploy:
```bash
kubectl apply -f topdeck-api-deployment.yaml
```

### 5. Deploy Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: topdeck-ingress
  namespace: topdeck-prod
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.topdeck.yourcompany.com
    - app.topdeck.yourcompany.com
    secretName: topdeck-tls
  rules:
  - host: api.topdeck.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: topdeck-api
            port:
              number: 8000
  - host: app.topdeck.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: topdeck-frontend
            port:
              number: 80
```

Deploy:
```bash
kubectl apply -f ingress.yaml
```

---

## Monitoring & Observability

### 1. Prometheus Setup

Use the Prometheus Operator or kube-prometheus-stack:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

### 2. Service Monitors

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: topdeck-api
  namespace: topdeck-prod
spec:
  selector:
    matchLabels:
      app: topdeck-api
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

### 3. Grafana Dashboards

Import TopDeck dashboards from `docs/grafana-dashboards/` directory.

---

## Backup & Recovery

### 1. Neo4j Backups

```bash
# Create backup job
kubectl create job neo4j-backup-$(date +%Y%m%d) \
  --image=neo4j:5.15.0 \
  --namespace=topdeck-prod \
  -- neo4j-admin database dump neo4j --to-path=/backups
```

### 2. Automated Backup Schedule

```yaml
# backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: neo4j-backup
  namespace: topdeck-prod
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: neo4j:5.15.0
            command:
            - /bin/sh
            - -c
            - neo4j-admin database dump neo4j --to-path=/backups/$(date +%Y%m%d)
            volumeMounts:
            - name: backup-volume
              mountPath: /backups
          restartPolicy: OnFailure
          volumes:
          - name: backup-volume
            persistentVolumeClaim:
              claimName: backup-pvc
```

---

## Scaling & Performance

### 1. Horizontal Pod Autoscaling

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: topdeck-api-hpa
  namespace: topdeck-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: topdeck-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. Neo4j Read Replicas

For read-heavy workloads, deploy Neo4j read replicas following the Neo4j Cluster documentation.

---

## Troubleshooting

### Common Issues

#### 1. API Pods Not Starting

```bash
# Check pod status
kubectl get pods -n topdeck-prod

# Check logs
kubectl logs -n topdeck-prod deployment/topdeck-api

# Check events
kubectl describe pod -n topdeck-prod <pod-name>
```

#### 2. Database Connection Issues

```bash
# Test Neo4j connectivity
kubectl run -it --rm debug --image=neo4j:5.15.0 --restart=Never -- \
  cypher-shell -a bolt://neo4j:7687 -u neo4j -p <password>
```

#### 3. High Memory Usage

```bash
# Check resource usage
kubectl top pods -n topdeck-prod

# Increase resources if needed
kubectl edit deployment topdeck-api -n topdeck-prod
```

---

## Next Steps

1. Configure monitoring alerts
2. Set up backup verification
3. Test disaster recovery procedures
4. Configure log aggregation
5. Set up CI/CD pipelines
6. Document operational procedures

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/MattVerwey/TopDeck/issues
- Documentation: https://github.com/MattVerwey/TopDeck/tree/main/docs

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-22  
**Maintained By**: TopDeck Team
