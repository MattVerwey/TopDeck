# Network Flow Diagrams

This document provides comprehensive network flow diagrams showing how data flows through cloud infrastructure resources. These diagrams illustrate the complete path from client requests through load balancers, gateways, compute resources, and data storage.

## Table of Contents

1. [Azure Network Flow Patterns](#azure-network-flow-patterns)
2. [AWS Network Flow Patterns](#aws-network-flow-patterns)
3. [GCP Network Flow Patterns](#gcp-network-flow-patterns)
4. [Multi-Cloud Flow Patterns](#multi-cloud-flow-patterns)
5. [Common Flow Scenarios](#common-flow-scenarios)

---

## Azure Network Flow Patterns

### Pattern 1: Web Application with Application Gateway

This pattern shows a typical web application deployment with Application Gateway as the entry point, routing traffic to App Service and AKS pods, with data stored in SQL Database and Storage Account.

```
                              [Internet]
                                  │
                                  │ HTTPS (443)
                                  ▼
                    ┌─────────────────────────┐
                    │  Application Gateway    │
                    │  (Public IP)            │
                    │  - WAF Enabled          │
                    │  - SSL Termination      │
                    └───────────┬─────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    │ ROUTES_TO             │ ROUTES_TO
                    │ (Backend Pool 1)      │ (Backend Pool 2)
                    │                       │
          ┌─────────▼──────────┐   ┌───────▼────────┐
          │    Load Balancer   │   │   App Service  │
          │    (Internal)      │   │   "web-app"    │
          │    10.0.1.4        │   │                │
          └─────────┬──────────┘   └───────┬────────┘
                    │                      │
                    │ DISTRIBUTES          │ CONNECTS_TO
                    │ (Port 8080)          │ (HTTPS:443)
                    │                      │
    ┌───────────────┼──────────────┐      │
    │               │              │      │
    ▼               ▼              ▼      │
┌────────┐     ┌────────┐     ┌────────┐ │
│  Pod   │     │  Pod   │     │  Pod   │ │
│ "api-1"│     │ "api-2"│     │ "api-3"│ │
│ AKS    │     │ AKS    │     │ AKS    │ │
└───┬────┘     └───┬────┘     └───┬────┘ │
    │              │              │      │
    └──────────────┼──────────────┘      │
                   │                     │
                   │ READS/WRITES        │ READS/WRITES
                   │ (SQL:1433)          │ (SQL:1433)
                   │                     │
            ┌──────▼─────────────────────▼───────┐
            │      SQL Database                  │
            │      "prod-db"                     │
            │      - Private Endpoint            │
            │      - Geo-Replication Enabled     │
            └──────┬─────────────────────────────┘
                   │
                   │ BACKED_UP_TO
                   │ (Automated Backup)
                   │
            ┌──────▼─────────────────────────────┐
            │   Storage Account                  │
            │   "prodbackups"                    │
            │   - Blob Storage                   │
            │   - Private Endpoint               │
            └────────────────────────────────────┘

Data Flow:
1. Client → Application Gateway (HTTPS:443)
2. Application Gateway → Load Balancer or App Service (HTTP:80/8080)
3. Load Balancer → AKS Pods (Round-robin distribution)
4. Pods/App Service → SQL Database (SQL:1433)
5. SQL Database → Storage Account (Backup operations)
```

### Pattern 2: AKS Microservices with Service Mesh

This pattern shows microservices running in AKS with service mesh (Istio), demonstrating pod-to-pod communication, external services, and data storage.

```
                              [Internet]
                                  │
                                  │ HTTPS (443)
                                  ▼
                    ┌─────────────────────────┐
                    │    Public IP / DNS      │
                    └───────────┬─────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Azure Kubernetes Service                     │
│                         Virtual Network: 10.0.0.0/16                │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    Namespace: "production"                  │   │
│  │                                                             │   │
│  │   ┌──────────────┐          Istio Service Mesh            │   │
│  │   │ Ingress      │                                          │   │
│  │   │ Gateway      │                                          │   │
│  │   │ (Istio)      │                                          │   │
│  │   └──────┬───────┘                                          │   │
│  │          │ ROUTES_TO                                        │   │
│  │          │ (Virtual Service)                                │   │
│  │          │                                                   │   │
│  │   ┌──────▼────────────────────────────────┐                │   │
│  │   │                                        │                │   │
│  │   │  ┌──────────┐      ┌──────────┐      │                │   │
│  │   │  │Frontend  │      │  API     │      │                │   │
│  │   │  │Pod       │─────▶│  Gateway │      │                │   │
│  │   │  │          │ HTTP │  Pod     │      │                │   │
│  │   │  └──────────┘      └─────┬────┘      │                │   │
│  │   │                           │           │                │   │
│  │   │                           │ CALLS     │                │   │
│  │   │          ┌────────────────┼──────────────────┐        │   │
│  │   │          │                │                  │        │   │
│  │   │   ┌──────▼────┐    ┌──────▼────┐    ┌───────▼───┐   │   │
│  │   │   │  Order    │    │   User    │    │  Payment  │   │   │
│  │   │   │  Service  │    │  Service  │    │  Service  │   │   │
│  │   │   │  Pod      │    │  Pod      │    │  Pod      │   │   │
│  │   │   └─────┬─────┘    └─────┬─────┘    └─────┬─────┘   │   │
│  │   │         │                │                 │         │   │
│  │   └─────────┼────────────────┼─────────────────┼─────────┘   │
│  │             │                │                 │             │
│  └─────────────┼────────────────┼─────────────────┼─────────────┘
│                │                │                 │               │
│                │ CONNECTS_TO    │ CONNECTS_TO     │ CONNECTS_TO  │
│                │ (Port 5432)    │ (Port 6379)     │ (HTTPS:443)  │
└────────────────┼────────────────┼─────────────────┼───────────────┘
                 │                │                 │
         ┌───────▼──────┐  ┌──────▼─────┐   ┌──────▼─────────┐
         │ PostgreSQL   │  │  Redis     │   │ External       │
         │ Database     │  │  Cache     │   │ Payment        │
         │ (Azure DB)   │  │ (Azure     │   │ Gateway API    │
         │              │  │  Cache)    │   │                │
         └──────┬───────┘  └────────────┘   └────────────────┘
                │
                │ STORES_LOGS
                │
         ┌──────▼─────────────────────┐
         │  Storage Account           │
         │  - Logs & Metrics          │
         │  - Audit Trail             │
         └────────────────────────────┘

Data Flow:
1. Client → Ingress Gateway (HTTPS:443)
2. Ingress Gateway → Frontend Pod (HTTP:8080)
3. Frontend Pod → API Gateway Pod (HTTP:8080)
4. API Gateway → Order/User/Payment Service Pods (HTTP:8080)
5. Service Pods → PostgreSQL/Redis/External APIs
6. All Services → Storage Account (Logs, Metrics)

Service Mesh Features:
- mTLS between all pods
- Circuit breaking and retries
- Distributed tracing
- Metrics and monitoring
```

### Pattern 3: Hub-Spoke Network with Private Endpoints

This pattern demonstrates enterprise network architecture with hub-spoke topology, private endpoints, and network security groups.

```
┌────────────────────────────────────────────────────────────────────┐
│                          Hub Virtual Network                        │
│                          10.0.0.0/16                                │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │          Gateway Subnet (10.0.0.0/27)                   │      │
│  │                                                          │      │
│  │  ┌──────────────────┐      ┌──────────────────┐        │      │
│  │  │ VPN Gateway      │      │ ExpressRoute     │        │      │
│  │  │                  │      │ Gateway          │        │      │
│  │  └────────┬─────────┘      └────────┬─────────┘        │      │
│  └───────────┼────────────────────────┼──────────────────┘       │
│              │                        │                           │
│  ┌───────────┼────────────────────────┼──────────────────┐       │
│  │           │   Firewall Subnet      │                  │       │
│  │           │   (10.0.1.0/26)        │                  │       │
│  │    ┌──────▼────────────────────────▼──────┐           │       │
│  │    │    Azure Firewall / NVA              │           │       │
│  │    │    - Central traffic inspection      │           │       │
│  │    │    - Network filtering               │           │       │
│  │    └──────┬───────────────────────────────┘           │       │
│  └───────────┼───────────────────────────────────────────┘       │
│              │                                                     │
└──────────────┼─────────────────────────────────────────────────────┘
               │
               │ ROUTES_TO (Peering)
               │
      ┌────────┴──────────┬──────────────────────┐
      │                   │                      │
      ▼                   ▼                      ▼
┌─────────────┐    ┌─────────────┐      ┌─────────────┐
│  Spoke 1    │    │  Spoke 2    │      │  Spoke 3    │
│  VNet       │    │  VNet       │      │  VNet       │
│ (Production)│    │  (Dev/Test) │      │  (Shared)   │
│ 10.1.0.0/16 │    │ 10.2.0.0/16 │      │ 10.3.0.0/16 │
└──────┬──────┘    └──────┬──────┘      └──────┬──────┘
       │                  │                     │
       │                  │                     │
┌──────▼──────────────────────────────────────────────────┐
│         Spoke 1 - Production Workloads                  │
│                                                          │
│  ┌───────────────────────────────────────────────┐     │
│  │  App Service Subnet (10.1.1.0/24)             │     │
│  │  - Regional VNet Integration                  │     │
│  │                                                │     │
│  │  ┌──────────┐        ┌──────────┐            │     │
│  │  │App Service│       │App Service│            │     │
│  │  │  "web"   │       │  "api"    │            │     │
│  │  └─────┬────┘       └─────┬─────┘            │     │
│  └────────┼──────────────────┼───────────────────┘     │
│           │                  │                         │
│           │ CONNECTS_TO      │ CONNECTS_TO             │
│           │ (Private         │ (Private                │
│           │  Endpoint)       │  Endpoint)              │
│           │                  │                         │
│  ┌────────▼──────────────────▼───────────────────┐    │
│  │  Data Subnet (10.1.2.0/24)                    │    │
│  │  - Private Endpoints Only                     │    │
│  │                                                │    │
│  │  ┌────────────────┐    ┌────────────────┐    │    │
│  │  │ Private        │    │ Private        │    │    │
│  │  │ Endpoint       │    │ Endpoint       │    │    │
│  │  │ (SQL DB)       │    │ (Storage)      │    │    │
│  │  └───────┬────────┘    └───────┬────────┘    │    │
│  └──────────┼─────────────────────┼──────────────┘    │
│             │                     │                    │
└─────────────┼─────────────────────┼────────────────────┘
              │                     │
              │ PRIVATE_LINK        │ PRIVATE_LINK
              │ (No public IP)      │ (No public IP)
              │                     │
       ┌──────▼──────────┐   ┌──────▼──────────┐
       │  SQL Database   │   │ Storage Account │
       │  "prod-db"      │   │ "proddata"      │
       │  - Private Only │   │ - Private Only  │
       └─────────────────┘   └─────────────────┘

Data Flow:
1. On-Premises → VPN/ExpressRoute Gateway → Hub VNet
2. Hub VNet → Azure Firewall (Inspection) → Spoke VNet
3. App Service → Private Endpoint → SQL Database (10.1.2.x)
4. App Service → Private Endpoint → Storage Account (10.1.2.x)
5. All traffic inspected by Azure Firewall
6. No public endpoints exposed

Security Features:
- Network Security Groups on all subnets
- Azure Firewall for central filtering
- Private Endpoints for PaaS services
- No public IP addresses on data services
- VPN/ExpressRoute for secure connectivity
```

---

## AWS Network Flow Patterns

### Pattern 1: EKS Application with ALB

This pattern shows an EKS cluster with Application Load Balancer for ingress, connecting to RDS and S3.

```
                            [Internet]
                                │
                                │ HTTPS (443)
                                ▼
                   ┌─────────────────────────┐
                   │ Application Load        │
                   │ Balancer (ALB)          │
                   │ - Public Subnets        │
                   │ - AWS WAF Enabled       │
                   └──────────┬──────────────┘
                              │
                              │ ROUTES_TO
                              │ (Target Group)
                              │
┌─────────────────────────────┼────────────────────────────────────────┐
│                   Amazon EKS Cluster                                 │
│                   VPC: 10.0.0.0/16                                   │
│                             │                                        │
│  ┌──────────────────────────┼──────────────────────────────────┐   │
│  │          Private Subnet 1 (10.0.1.0/24)                      │   │
│  │                          │                                   │   │
│  │   ┌──────────────────────▼──────────────────┐               │   │
│  │   │        Node Group (EC2 Instances)       │               │   │
│  │   │                                          │               │   │
│  │   │  ┌────────┐  ┌────────┐  ┌────────┐   │               │   │
│  │   │  │  Pod   │  │  Pod   │  │  Pod   │   │               │   │
│  │   │  │"web-1" │  │"web-2" │  │"api-1" │   │               │   │
│  │   │  └───┬────┘  └───┬────┘  └───┬────┘   │               │   │
│  │   └──────┼───────────┼───────────┼─────────┘               │   │
│  └──────────┼───────────┼───────────┼──────────────────────────┘   │
│             │           │           │                              │
│  ┌──────────┼───────────┼───────────┼──────────────────────────┐   │
│  │          │Private Subnet 2 (10.0.2.0/24)                    │   │
│  │          │           │           │                           │   │
│  │   ┌──────▼───────────▼───────────▼───────────┐              │   │
│  │   │        Node Group (EC2 Instances)        │              │   │
│  │   │                                           │              │   │
│  │   │  ┌────────┐  ┌────────┐  ┌────────┐     │              │   │
│  │   │  │  Pod   │  │  Pod   │  │  Pod   │     │              │   │
│  │   │  │"api-2" │  │"api-3" │  │"worker"│     │              │   │
│  │   │  └───┬────┘  └───┬────┘  └───┬────┘     │              │   │
│  │   └──────┼───────────┼───────────┼───────────┘              │   │
│  └──────────┼───────────┼───────────┼───────────────────────────┘   │
└─────────────┼───────────┼───────────┼───────────────────────────────┘
              │           │           │
              │ READS/    │ READS/    │ READS/WRITES
              │ WRITES    │ WRITES    │ (S3 API)
              │ (5432)    │ (5432)    │
              │           │           │
       ┌──────▼───────────▼─────┐     │
       │   Amazon RDS            │     │
       │   (PostgreSQL)          │     │
       │   - Multi-AZ            │     │
       │   - Private Subnet      │     │
       └─────────────────────────┘     │
                                       │
                                ┌──────▼─────────────┐
                                │   Amazon S3        │
                                │   - VPC Endpoint   │
                                │   - Bucket Policy  │
                                └────────────────────┘

Data Flow:
1. Client → ALB (HTTPS:443)
2. ALB → EKS Node Group → Pods (HTTP:8080)
3. Pods → RDS PostgreSQL (Port 5432)
4. Pods → S3 (HTTPS via VPC Endpoint)
5. NAT Gateway for outbound internet (not shown)
```

### Pattern 2: Lambda with API Gateway

This pattern shows serverless architecture with API Gateway, Lambda, DynamoDB, and S3.

```
                            [Internet]
                                │
                                │ HTTPS (443)
                                ▼
                   ┌─────────────────────────┐
                   │  Amazon API Gateway     │
                   │  (REST API)             │
                   │  - Custom Domain        │
                   │  - WAF Enabled          │
                   └──────────┬──────────────┘
                              │
                              │ INVOKES
                              │ (Async/Sync)
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐          ┌─────────┐         ┌─────────┐
    │ Lambda  │          │ Lambda  │         │ Lambda  │
    │Function │          │Function │         │Function │
    │ "API"   │          │ "Auth"  │         │ "Process"
    └────┬────┘          └────┬────┘         └────┬────┘
         │                    │                    │
         │ READS/WRITES       │ READS             │ READS/WRITES
         │ (HTTPS)            │ (HTTPS)           │ (HTTPS)
         │                    │                    │
    ┌────▼────────────────────▼────────────────────▼─────┐
    │            Amazon DynamoDB Tables                   │
    │                                                      │
    │  ┌──────────────┐  ┌──────────────┐               │
    │  │  Users       │  │  Orders      │               │
    │  │  Table       │  │  Table       │               │
    │  └──────────────┘  └──────────────┘               │
    └──────────────────────────────────────────────────────┘
         │
         │ STREAMS_TO
         │ (DynamoDB Streams)
         ▼
    ┌─────────┐
    │ Lambda  │
    │Function │──────────┐
    │"Stream" │          │ WRITES
    └─────────┘          │ (S3 API)
                         │
                    ┌────▼──────────────┐
                    │   Amazon S3       │
                    │   - Archive       │
                    │   - Analytics     │
                    └───────────────────┘

Data Flow:
1. Client → API Gateway (HTTPS:443)
2. API Gateway → Lambda Functions (Invocation)
3. Lambda → DynamoDB (Read/Write operations)
4. DynamoDB Streams → Lambda (Change data capture)
5. Lambda → S3 (Archive/Analytics)

Features:
- Fully serverless, no server management
- Auto-scaling based on load
- Pay-per-request pricing
- Event-driven architecture
```

---

## GCP Network Flow Patterns

### Pattern 1: GKE with Cloud Load Balancing

This pattern shows GKE cluster with Global Load Balancer and Cloud SQL.

```
                            [Internet]
                                │
                                │ HTTPS (443)
                                ▼
                   ┌─────────────────────────┐
                   │  Cloud Load Balancing   │
                   │  (Global HTTPS LB)      │
                   │  - Cloud CDN            │
                   │  - Cloud Armor          │
                   └──────────┬──────────────┘
                              │
                              │ ROUTES_TO
                              │ (Backend Service)
                              │
┌─────────────────────────────┼────────────────────────────────────────┐
│              Google Kubernetes Engine (GKE)                          │
│              VPC Network: 10.0.0.0/16                                │
│                             │                                        │
│  ┌──────────────────────────┼──────────────────────────────────┐   │
│  │          Node Pool (us-central1-a)                           │   │
│  │                          │                                   │   │
│  │   ┌──────────────────────▼──────────────────┐               │   │
│  │   │              Nodes (VMs)                 │               │   │
│  │   │                                          │               │   │
│  │   │  ┌────────┐  ┌────────┐  ┌────────┐   │               │   │
│  │   │  │  Pod   │  │  Pod   │  │  Pod   │   │               │   │
│  │   │  │"web"   │  │"api-1" │  │"api-2" │   │               │   │
│  │   │  └───┬────┘  └───┬────┘  └───┬────┘   │               │   │
│  │   └──────┼───────────┼───────────┼─────────┘               │   │
│  └──────────┼───────────┼───────────┼──────────────────────────┘   │
│             │           │           │                              │
│  ┌──────────┼───────────┼───────────┼──────────────────────────┐   │
│  │          │  Node Pool (us-central1-b)                       │   │
│  │          │           │           │                           │   │
│  │   ┌──────▼───────────▼───────────▼───────────┐              │   │
│  │   │              Nodes (VMs)                  │              │   │
│  │   │                                           │              │   │
│  │   │  ┌────────┐  ┌────────┐  ┌────────┐     │              │   │
│  │   │  │  Pod   │  │  Pod   │  │  Pod   │     │              │   │
│  │   │  │"api-3" │  │"worker"│  │"cache" │     │              │   │
│  │   │  └───┬────┘  └───┬────┘  └───┬────┘     │              │   │
│  │   └──────┼───────────┼───────────┼───────────┘              │   │
│  └──────────┼───────────┼───────────┼───────────────────────────┘   │
└─────────────┼───────────┼───────────┼───────────────────────────────┘
              │           │           │
              │ CONNECTS  │ CONNECTS  │ CONNECTS
              │ (3306)    │ (6379)    │ (HTTPS)
              │           │           │
       ┌──────▼───────────▼─────┐     │
       │   Cloud SQL             │     │
       │   (MySQL)               │     │
       │   - Private IP          │     │
       │   - Auto Backups        │     │
       └─────────────────────────┘     │
                                       │
                                ┌──────▼─────────────┐
                                │ Cloud Storage      │
                                │ - Private Access   │
                                │ - Lifecycle Policy │
                                └────────────────────┘

Data Flow:
1. Client → Cloud Load Balancer (HTTPS:443)
2. Load Balancer → GKE Ingress → Pods (HTTP:8080)
3. Pods → Cloud SQL (MySQL:3306)
4. Pods → Cloud Storage (HTTPS)
5. Cross-region replication for high availability
```

### Pattern 2: Cloud Run with Cloud Functions

This pattern shows serverless microservices with Cloud Run and Cloud Functions.

```
                            [Internet]
                                │
                                │ HTTPS (443)
                                ▼
                   ┌─────────────────────────┐
                   │  Cloud Load Balancing   │
                   │  (Global HTTPS LB)      │
                   └──────────┬──────────────┘
                              │
                              │ ROUTES_TO
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐          ┌─────────┐         ┌─────────┐
    │ Cloud   │          │ Cloud   │         │ Cloud   │
    │ Run     │          │ Run     │         │ Run     │
    │"Frontend"         │ "API"   │         │"Payment"│
    └────┬────┘          └────┬────┘         └────┬────┘
         │                    │                    │
         │ CALLS              │ CALLS             │ CALLS
         │ (HTTPS)            │ (HTTPS)           │ (HTTPS)
         │                    │                    │
         │              ┌─────▼────────────────────▼─────┐
         │              │    Cloud Functions              │
         │              │                                 │
         │              │  ┌──────────┐  ┌──────────┐   │
         │              │  │ Auth     │  │ Process  │   │
         │              │  │ Function │  │ Function │   │
         │              │  └─────┬────┘  └─────┬────┘   │
         │              └────────┼─────────────┼─────────┘
         │                       │             │
         │ READS                 │ WRITES      │ READS/WRITES
         │ (HTTPS)               │ (HTTPS)     │ (HTTPS)
         │                       │             │
    ┌────▼───────────────────────▼─────────────▼──────┐
    │            Cloud Firestore                       │
    │            (NoSQL Database)                      │
    │                                                   │
    │  ┌──────────────┐  ┌──────────────┐            │
    │  │ users        │  │ transactions │            │
    │  │ collection   │  │ collection   │            │
    │  └──────────────┘  └──────────────┘            │
    └───────────────────────────────────────────────────┘
              │
              │ TRIGGERS
              │ (Firestore Triggers)
              ▼
         ┌─────────┐
         │ Cloud   │
         │Function │──────────┐
         │"OnWrite"│          │ PUBLISHES
         └─────────┘          │ (Pub/Sub)
                              │
                         ┌────▼──────────────┐
                         │  Cloud Pub/Sub    │
                         │  - Topic: events  │
                         └───────┬───────────┘
                                 │
                                 │ SUBSCRIBES
                                 ▼
                         ┌───────────────────┐
                         │  Cloud Function   │
                         │  "Analytics"      │
                         └───────┬───────────┘
                                 │ WRITES
                                 │
                         ┌───────▼───────────┐
                         │  BigQuery         │
                         │  - Analytics Data │
                         └───────────────────┘

Data Flow:
1. Client → Cloud Load Balancer → Cloud Run Services
2. Cloud Run → Cloud Functions (HTTP invocation)
3. Cloud Functions → Cloud Firestore (CRUD operations)
4. Firestore Changes → Cloud Functions (Triggers)
5. Cloud Functions → Pub/Sub → Analytics Pipeline
6. Analytics → BigQuery (Data warehouse)

Features:
- Fully managed, serverless platform
- Automatic scaling from 0 to N
- Built-in security and SSL
- Event-driven architecture
```

---

## Multi-Cloud Flow Patterns

### Pattern 1: Multi-Cloud Application

This pattern shows an application spanning Azure, AWS, and GCP with data replication.

```
┌─────────────────────────────────────────────────────────────────────┐
│                              Azure                                   │
│                                                                      │
│  ┌────────────────┐         ┌────────────────┐                     │
│  │ App Service    │────────▶│ SQL Database   │                     │
│  │ "Primary"      │ WRITES  │ "Primary"      │                     │
│  └───────┬────────┘         └───────┬────────┘                     │
│          │                          │                               │
│          │ REPLICATES               │ GEO-REPLICATES               │
└──────────┼──────────────────────────┼───────────────────────────────┘
           │                          │
           │                          ▼
           │              ┌─────────────────────────┐
           │              │   Azure SQL             │
           │              │   Geo-Replication       │
           │              │   (Read Replica)        │
           │              └───────┬─────────────────┘
           │                      │
           │ SYNCS_TO             │ SYNCS_TO
           │ (Event Hub)          │ (CDC)
           │                      │
           ▼                      ▼
┌─────────────────────┐    ┌─────────────────────┐
│        AWS          │    │        GCP          │
│                     │    │                     │
│  ┌──────────────┐  │    │  ┌──────────────┐  │
│  │   Lambda     │  │    │  │ Cloud Function│ │
│  │   (Consumer) │  │    │  │ (Consumer)   │  │
│  └──────┬───────┘  │    │  └──────┬───────┘  │
│         │          │    │         │          │
│         │ WRITES   │    │         │ WRITES   │
│         ▼          │    │         ▼          │
│  ┌──────────────┐  │    │  ┌──────────────┐  │
│  │  DynamoDB    │  │    │  │  Firestore   │  │
│  │  (Secondary) │  │    │  │  (Secondary) │  │
│  └──────────────┘  │    │  └──────────────┘  │
└─────────────────────┘    └─────────────────────┘

Data Flow:
1. Primary writes → Azure SQL Database
2. Azure SQL → Geo-replication to secondary regions
3. Change Data Capture → Event Hub
4. Event Hub → AWS Lambda / GCP Cloud Functions
5. Lambda/Functions → DynamoDB/Firestore (Eventual consistency)

Multi-Cloud Benefits:
- Disaster recovery across cloud providers
- Data locality for compliance
- Cloud-specific optimizations
- Vendor independence
```

---

## Common Flow Scenarios

### Scenario 1: Request/Response Flow

Typical synchronous request/response pattern:

```
Client Request
     │
     ▼
Load Balancer ───────┐
     │               │ Health Check
     │               │
     ▼               │
Application Pod ◄────┘
     │
     │ Query
     ▼
Database
     │
     │ Result
     ▼
Application Pod
     │
     │ Response
     ▼
Load Balancer
     │
     ▼
Client Response
```

### Scenario 2: Event-Driven Flow

Asynchronous event-driven pattern:

```
Event Source (API/UI)
     │
     ▼
Message Queue/Event Hub
     │
     ├─────────┬─────────┬─────────┐
     ▼         ▼         ▼         ▼
Worker-1  Worker-2  Worker-3  Worker-4
     │         │         │         │
     └─────────┴─────────┴─────────┘
               │
               ▼
         Data Store
               │
               ▼
      Analytics Pipeline
```

### Scenario 3: Caching Pattern

Request flow with caching layer:

```
Client Request
     │
     ▼
Load Balancer
     │
     ▼
Application
     │
     ├─────────► Cache (Redis)
     │               │
     │               │ Cache Miss
     │               │
     │◄──────────────┘
     │
     ▼
Database
     │
     ▼
Application
     │
     ├─────────► Cache (Write-Through)
     │
     ▼
Client Response
```

---

## Security Patterns

### Network Security Flow

```
Internet Traffic
     │
     ▼
WAF (Web Application Firewall)
     │ Filters malicious traffic
     ▼
DDoS Protection
     │ Rate limiting
     ▼
Load Balancer (Public)
     │ SSL Termination
     ▼
Application Gateway
     │ Routing rules
     ▼
Application Pods (Private Subnet)
     │ Network policy enforcement
     ▼
Database (Private Subnet)
     │ Private endpoint only
     ▼
Firewall/NSG
     │ Network rules
     ▼
Data Storage (Private)
```

### Identity and Access Flow

```
User/Service
     │
     ▼
Identity Provider (Azure AD / AWS IAM / GCP IAM)
     │ Authentication
     ▼
Access Token
     │
     ▼
API Gateway
     │ Authorization
     ▼
Application
     │ Managed Identity
     ▼
Azure Key Vault / AWS Secrets Manager / GCP Secret Manager
     │ Secret retrieval
     ▼
Database/Storage
     │ Connection with credentials
     ▼
Data Access
```

---

## Performance Optimization Patterns

### CDN with Origin

```
User Request
     │
     ▼
CDN Edge Location (Closest POP)
     │
     ├─── Cache Hit ───► Return cached content
     │
     └─── Cache Miss
           │
           ▼
     Origin (Load Balancer)
           │
           ▼
     Application
           │
           ▼
     Static Storage (S3/Blob/GCS)
           │
           ▼
     Content returned to CDN
           │
           ▼
     CDN caches content
           │
           ▼
     Return to user
```

### Auto-Scaling Flow

```
Metrics Collection
     │
     ▼
Monitor (CPU/Memory/Request Rate)
     │
     ▼
Auto-Scaler
     │
     ├─── Scale Up (Add instances)
     │         │
     │         ▼
     │    New Instances
     │         │
     │         ▼
     │    Load Balancer (Updated pool)
     │
     └─── Scale Down (Remove instances)
               │
               ▼
          Graceful Shutdown
               │
               ▼
          Load Balancer (Updated pool)
```

---

## Monitoring and Observability Flow

### Telemetry Collection

```
Application Code
     │
     ├────────► Logs
     │            │
     ├────────► Metrics
     │            │
     └────────► Traces
                  │
                  ▼
          Collection Agent
                  │
                  ▼
          Aggregation Service
                  │
     ┌────────────┼────────────┐
     ▼            ▼            ▼
Log Storage  Metrics DB   Trace DB
     │            │            │
     └────────────┴────────────┘
                  │
                  ▼
          Analysis Platform
                  │
     ┌────────────┴────────────┐
     ▼                         ▼
Dashboards              Alert Manager
                              │
                              ▼
                         Notifications
```

---

## Summary

These network flow diagrams provide a comprehensive view of how data flows through cloud infrastructure:

1. **Azure Patterns**: Application Gateway, AKS with service mesh, hub-spoke topology
2. **AWS Patterns**: ALB with EKS, serverless Lambda architecture
3. **GCP Patterns**: Global load balancing with GKE, Cloud Run serverless
4. **Multi-Cloud**: Cross-cloud replication and disaster recovery
5. **Common Patterns**: Caching, event-driven, request/response
6. **Security**: WAF, DDoS protection, identity management
7. **Performance**: CDN, auto-scaling
8. **Observability**: Logs, metrics, traces

These diagrams serve as the foundation for:
- Network topology visualization in TopDeck
- Understanding resource dependencies
- Security analysis and compliance
- Performance optimization
- Incident response and troubleshooting

For implementation in TopDeck's visualization dashboard, these patterns will be rendered as interactive graphs using Cytoscape.js or D3.js, allowing users to explore their infrastructure topology in real-time.
