# Enhanced Dependency Mapping Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│               Enhanced Dependency Discovery System               │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
    ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Connection     │ │    Loki      │ │  Prometheus  │
    │     String       │ │     Log      │ │   Metrics    │
    │    Analysis      │ │   Analysis   │ │   Analysis   │
    └──────────────────┘ └──────────────┘ └──────────────┘
            │                   │               │
            │                   │               │
            └───────────────────┴───────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Evidence Aggregation │
                    │   & Confidence Boost  │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   ResourceDependency  │
                    │    with Confidence    │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Neo4j Graph Store   │
                    └───────────────────────┘
```

## Discovery Flow

### 1. Connection String Discovery

```
Azure App Service                    Connection String Parser
┌────────────────┐                   ┌──────────────────────┐
│ App Settings:  │                   │ Parse Format         │
│                │  ──────────────▶  │ • Azure SQL          │
│ DB_CONNECTION  │                   │ • PostgreSQL         │
│ = "Server=tcp: │                   │ • MySQL              │
│   mydb.data... │                   │ • Redis              │
│   base.windows │                   │ • Storage            │
│   .net,1433;   │                   └──────────────────────┘
│   Database=    │                            │
│   prod;"       │                            ▼
└────────────────┘                   ┌──────────────────────┐
                                     │ ConnectionInfo       │
                                     │ • host: mydb.data... │
                                     │ • port: 1433         │
                                     │ • database: prod     │
                                     │ • service_type: sql  │
                                     └──────────────────────┘
                                              │
                                              ▼
                                     ┌──────────────────────┐
                                     │ ResourceDependency   │
                                     │ • source: app-1      │
                                     │ • target: mydb       │
                                     │ • category: DATA     │
                                     │ • strength: 0.9      │
                                     │ • method: connection_│
                                     │          string      │
                                     └──────────────────────┘
```

### 2. Loki Log Discovery

```
Application Logs (Loki)              Log Pattern Extractor
┌────────────────┐                   ┌──────────────────────┐
│ 2024-01-15     │                   │ Extract Patterns:    │
│ 10:23:45       │  ──────────────▶  │                      │
│                │                   │ • HTTP URLs          │
│ "Sending GET   │                   │ • DB connections     │
│  request to    │                   │ • Service names      │
│  https://api.  │                   │                      │
│  example.com/  │                   └──────────────────────┘
│  users"        │                            │
│                │                            ▼
│ "Connected to  │                   ┌──────────────────────┐
│  postgres://   │                   │ Target Extraction    │
│  db.example.   │                   │                      │
│  com:5432"     │                   │ • api.example.com    │
└────────────────┘                   │   (https, 0.8)       │
                                     │ • db.example.com     │
                                     │   (postgres, 0.85)   │
                                     └──────────────────────┘
                                              │
                                              ▼
                                     ┌──────────────────────┐
                                     │ DependencyEvidence   │
                                     │ • type: logs         │
                                     │ • confidence: 0.8    │
                                     └──────────────────────┘
```

### 3. Prometheus Metrics Discovery

```
Prometheus Metrics                   Metrics Analyzer
┌────────────────┐                   ┌──────────────────────┐
│ http_requests_ │                   │ Analyze Patterns:    │
│ total{         │  ──────────────▶  │                      │
│   source=      │                   │ • Request rates      │
│   "service-a", │                   │ • Connections        │
│   target=      │                   │ • Latencies          │
│   "service-b"  │                   │ • Error rates        │
│ } 1523         │                   └──────────────────────┘
│                │                            │
│ db_connections │                            ▼
│ {              │                   ┌──────────────────────┐
│   instance=    │                   │ Traffic Pattern      │
│   "service-a", │                   │                      │
│   database=    │                   │ • service-a →        │
│   "postgres-1" │                   │   service-b          │
│ } 5            │                   │   (1523 requests)    │
└────────────────┘                   │ • service-a →        │
                                     │   postgres-1         │
                                     │   (5 connections)    │
                                     └──────────────────────┘
                                              │
                                              ▼
                                     ┌──────────────────────┐
                                     │ DependencyEvidence   │
                                     │ • type: metrics      │
                                     │ • confidence: 0.8    │
                                     └──────────────────────┘
```

### 4. Evidence Aggregation

```
Multiple Evidence Sources
┌────────────────────────────────────────────────────┐
│                                                    │
│  Connection String: service-a → database-1  (0.9) │
│  Loki Logs:        service-a → database-1  (0.85) │
│  Prometheus:       service-a → database-1  (0.8)  │
│                                                    │
└────────────────────────────────────────────────────┘
                    │
                    ▼
        ┌─────────────────────┐
        │   Aggregation       │
        │                     │
        │ • Average: 0.85     │
        │ • Multi-source      │
        │   boost: +0.15      │
        │ • Final: 0.95       │
        └─────────────────────┘
                    │
                    ▼
        ┌─────────────────────┐
        │ High-Confidence     │
        │ Dependency          │
        │                     │
        │ confidence: 0.95    │
        │ method: aggregated  │
        └─────────────────────┘
```

## Resource-Specific Extraction

### Azure App Service

```
Azure App Service Resource
┌─────────────────────────────────────────────┐
│ Resource ID: /subscriptions/.../myapp       │
│                                             │
│ Properties:                                 │
│ ┌─────────────────────────────────────────┐ │
│ │ siteConfig:                             │ │
│ │   appSettings:                          │ │
│ │   - name: "DB_CONNECTION"               │ │  ──┐
│ │     value: "Server=tcp:mydb.data..."    │ │    │
│ │   - name: "REDIS_CACHE"                 │ │    │  Extracted
│ │     value: "redis://cache.redis..."     │ │    │  by Mapper
│ │   - name: "STORAGE_ACCOUNT"             │ │    │
│ │     value: "DefaultEndpointsProtocol=..."│ │    │
│ │                                          │ │  ──┘
│ │   connectionStrings:                     │ │
│ │   - name: "DefaultConnection"            │ │  ──┐
│ │     value: "Server=tcp:..."              │ │    │  Also
│ └─────────────────────────────────────────┘ │  ──┘  Extracted
└─────────────────────────────────────────────┘

         Results in 3 Dependencies:
         ├── myapp → mydb (SQL)
         ├── myapp → cache (Redis)
         └── myapp → storage (Storage)
```

### AWS Lambda Function

```
AWS Lambda Function
┌─────────────────────────────────────────────┐
│ ARN: arn:aws:lambda:us-east-1:.../myfunction│
│                                             │
│ Properties:                                 │
│ ┌─────────────────────────────────────────┐ │
│ │ Environment:                            │ │
│ │   Variables:                            │ │
│ │     DB_HOST: "mydb.rds.amazonaws.com"   │ │  ──┐
│ │     DB_NAME: "production"               │ │    │
│ │     REDIS_URL: "redis://cache.elastic..." │    │  Extracted
│ │     S3_BUCKET: "my-bucket"              │ │    │  by Mapper
│ │     DYNAMODB_TABLE: "users"             │ │    │
│ └─────────────────────────────────────────┘ │  ──┘
└─────────────────────────────────────────────┘

         Results in 4 Dependencies:
         ├── myfunction → mydb.rds (RDS)
         ├── myfunction → cache.elastic (ElastiCache)
         ├── myfunction → my-bucket (S3)
         └── myfunction → users (DynamoDB)
```

### GCP Cloud Run Service

```
GCP Cloud Run Service
┌─────────────────────────────────────────────┐
│ Resource: projects/.../services/myservice   │
│                                             │
│ Properties:                                 │
│ ┌─────────────────────────────────────────┐ │
│ │ template:                               │ │
│ │   containers:                           │ │
│ │   - env:                                │ │
│ │     - name: "DATABASE_URL"              │ │  ──┐
│ │       value: "postgresql://sql.goog..." │ │    │
│ │     - name: "REDIS_HOST"                │ │    │  Extracted
│ │       value: "redis://memstore.goog..." │ │    │  by Mapper
│ │     - name: "STORAGE_BUCKET"            │ │    │
│ │       value: "gs://my-bucket"           │ │    │
│ └─────────────────────────────────────────┘ │  ──┘
└─────────────────────────────────────────────┘

         Results in 3 Dependencies:
         ├── myservice → sql.goog (Cloud SQL)
         ├── myservice → memstore.goog (Memorystore)
         └── myservice → my-bucket (Cloud Storage)
```

## Confidence Scoring

```
Evidence Source         Base Confidence    Boost Conditions
─────────────────────────────────────────────────────────
Connection String       90%                None (already high)
Loki HTTP URL          80%                +10% if also in metrics
Loki DB Connection     85%                +10% if also in metrics
Loki Service Name      60%                +15% if also in metrics
Prometheus Requests    80%                +15% if also in logs
Prometheus Connections 85%                +10% if also in logs

Multiple Sources       Average            +20% for 2+ sources
                                         (capped at 100%)

Examples:
─────────────────────────────────────────────────────────
Connection String only:       0.90 (no boost)
Logs + Metrics (HTTP):        0.80 + 0.15 = 0.95
Connection + Logs + Metrics:  (0.90 + 0.80 + 0.80) / 3 
                             = 0.83 + 0.20 = 1.00 (max)
```

## Neo4j Storage Structure

```cypher
// Resource nodes
(app:Resource {
  id: "/subscriptions/.../myapp",
  name: "myapp",
  resource_type: "app_service",
  cloud_provider: "azure"
})

(db:Resource {
  id: "/subscriptions/.../mydb",
  name: "mydb",
  resource_type: "sql_database",
  cloud_provider: "azure"
})

// Enhanced dependency relationship
(app)-[dep:DEPENDS_ON {
  // Original fields
  category: "data",
  dependency_type: "required",
  
  // Enhanced fields
  strength: 0.95,
  discovered_method: "aggregated",
  discovered_at: "2024-01-15T10:23:45Z",
  
  // Evidence details
  evidence_sources: ["connection_string", "logs", "metrics"],
  connection_info: "{host: 'mydb.database.windows.net', port: 1433}",
  
  // Optional description
  description: "Database connection from app settings"
}]->(db)
```

## Query Examples

### Find High-Confidence Dependencies

```cypher
MATCH (source)-[dep:DEPENDS_ON]->(target)
WHERE dep.strength >= 0.9
RETURN source.name, target.name, dep.strength, dep.discovered_method
ORDER BY dep.strength DESC
```

### Find Dependencies by Discovery Method

```cypher
MATCH (source)-[dep:DEPENDS_ON]->(target)
WHERE dep.discovered_method = "connection_string"
RETURN source.name, target.name, dep.description
```

### Find Multi-Source Validated Dependencies

```cypher
MATCH (source)-[dep:DEPENDS_ON]->(target)
WHERE dep.discovered_method = "aggregated"
  AND dep.strength >= 0.9
RETURN source.name, target.name, 
       dep.evidence_sources as sources,
       dep.strength as confidence
```

### Find All Dependencies for a Resource

```cypher
MATCH (resource {id: $resource_id})-[dep:DEPENDS_ON]->(dependency)
RETURN dependency.name, 
       dep.category,
       dep.dependency_type,
       dep.strength,
       dep.discovered_method
ORDER BY dep.strength DESC
```

## Benefits Visualization

```
Traditional (Resource Group Only)
═════════════════════════════════════════════
Resource Group: "production-rg"
├── App Service    ─┐
├── SQL Database   ─┤ Same RG = Dependency?
├── Redis Cache    ─┤ Confidence: 30%
└── Storage Acct   ─┘ Many false positives

Enhanced (Multi-Method)
═════════════════════════════════════════════
App Service
├─ Connection String ──┐
├─ Loki Logs         ──┼─▶ SQL Database
└─ Prometheus Metrics─┘   Confidence: 95%
                          ✓ Verified by 3 sources

├─ Connection String ──┐
└─ Prometheus Metrics─┘─▶ Redis Cache
                          Confidence: 87%
                          ✓ Verified by 2 sources

└─ Connection String ──▶ Storage Account
                         Confidence: 90%
                         ✓ Direct connection string
```

## Performance Characteristics

```
Method              Speed       Memory      Network     Accuracy
─────────────────────────────────────────────────────────────────
Connection String   <10ms       Low         None        90%
Loki Analysis       2-5s        Medium      High        60-85%
Prometheus Analysis 1-3s        Medium      Medium      80-85%
Combined Analysis   5-10s       Medium      High        90-95%

Recommended Usage:
─────────────────────────────────────────────────────────────────
Real-time Discovery    Use: Connection Strings only
Periodic Enrichment    Use: All methods, hourly/daily schedule
Critical Resources     Use: All methods, validate frequently
Development/Testing    Use: All methods, analyze deeply
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      TopDeck Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐     ┌────────────────────────────┐   │
│  │ Discovery Engine │────▶│ Enhanced Dependency        │   │
│  │  (Existing)      │     │ Enrichment Service         │   │
│  └──────────────────┘     │ (NEW)                      │   │
│           │               └────────────────────────────┘   │
│           │                      │          │               │
│           ▼                      ▼          ▼               │
│  ┌──────────────────┐   ┌────────────┐ ┌──────────────┐  │
│  │  Neo4j Database  │   │   Loki     │ │ Prometheus   │  │
│  │  (Topology)      │   │  (Logs)    │ │ (Metrics)    │  │
│  └──────────────────┘   └────────────┘ └──────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │                        │                │
         ▼                        ▼                ▼
┌──────────────┐        ┌──────────────┐  ┌──────────────┐
│ Azure/AWS/   │        │ Application  │  │ Infrastructure│
│ GCP          │        │ Logs         │  │ Metrics      │
│ Resources    │        │              │  │              │
└──────────────┘        └──────────────┘  └──────────────┘
```
