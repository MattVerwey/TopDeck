# Identity and Access Relationship Diagram

## Overview

This document provides visual diagrams showing how identity and access relationships work in TopDeck's data model.

---

## Diagram 1: App Service with Managed Identity

Shows how an App Service uses a system-assigned managed identity to access Key Vault and Storage.

```
┌──────────────────────────────────────────────────────────────────┐
│                         Identity Flow                             │
└──────────────────────────────────────────────────────────────────┘

    [App Service]
         │
         │ AUTHENTICATES_WITH
         │ (authentication_type: system_identity)
         ↓
    [ManagedIdentity]
         │ (identity_type: SystemAssigned)
         │ (assigned_to_resource: App Service)
         │
         ├──→ ACCESSES ──→ [Key Vault]
         │    (role: Key Vault Secrets User)
         │    (access_level: read)
         │
         └──→ ACCESSES ──→ [Storage Account]
              (role: Storage Blob Data Reader)
              (access_level: read)

    [App Service] ──→ USES_SECRET_FROM ──→ [Key Vault]
                  └──→ STORES_IN ──→ [Storage Account]
```

**Use Case**: Web application needs to read secrets from Key Vault and store files in Blob Storage without managing credentials.

---

## Diagram 2: Service Principal for CI/CD

Shows how a GitHub Actions pipeline uses a Service Principal to deploy resources.

```
┌──────────────────────────────────────────────────────────────────┐
│                      CI/CD Authentication                         │
└──────────────────────────────────────────────────────────────────┘

    [Deployment]
    (pipeline: GitHub Actions)
         │
         │ AUTHENTICATES_WITH
         │ (authentication_type: service_principal)
         ↓
    [ServicePrincipal]
         │ (display_name: GitHub Actions Deployer)
         │ (app_id: xxx-xxx-xxx)
         │
         │ LINKED_TO_APP
         ↓
    [AppRegistration]
         │ (display_name: GitHub Actions App)
         │
         │
    [ServicePrincipal]
         │
         ├──→ HAS_ROLE ──→ [Resource Group]
         │    (role: Contributor)
         │    (scope: resource_group)
         │
         └──→ HAS_ROLE ──→ [AKS Cluster]
              (role: Azure Kubernetes Service Cluster User)
              (scope: resource)
```

**Use Case**: Automated deployments need to create and manage resources in Azure.

---

## Diagram 3: AKS with Multiple Identities

Shows how an AKS cluster uses managed identities for different purposes.

```
┌──────────────────────────────────────────────────────────────────┐
│                   AKS Identity Architecture                       │
└──────────────────────────────────────────────────────────────────┘

                        [AKS Cluster]
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              │               │               │
         AUTHENTICATES   CONTAINS        CONTAINS
              │               │               │
              ↓               ↓               ↓
    [ManagedIdentity]   [Namespace:prod]  [Namespace:dev]
    (Cluster Identity)        │               │
              │               │               │
              │          IN_NAMESPACE    IN_NAMESPACE
              │               │               │
              │               ↓               ↓
              │            [Pod]           [Pod]
              │               │               │
              │               │               │
    [ManagedIdentity] ←───────┴───────────────┘
    (Workload Identity)    AUTHENTICATES_WITH
              │
              │
              └──→ ACCESSES ──→ [SQL Database]
                   (role: SQL DB Contributor)


    [AKS Cluster] ──→ PART_OF_NETWORK ──→ [Virtual Network]
                  └──→ DEPENDS_ON ──→ [Storage Account]
```

**Use Case**: Kubernetes cluster with workload identity for pods to access Azure resources.

---

## Diagram 4: Complete Application Stack with Identities

Shows a full application topology including compute, storage, networking, and identity.

```
┌──────────────────────────────────────────────────────────────────┐
│               Complete Application Topology                       │
└──────────────────────────────────────────────────────────────────┘

[Application]
     │
     │ BUILT_FROM
     ↓
[Repository] ──→ DEPLOYS_TO ──→ [Deployment]
     │                               │
     │                               │ AUTHENTICATES_WITH
     │                               ↓
     │                          [ServicePrincipal]
     │                               │
     │                               │ HAS_ROLE
     │ DEPLOYED_TO                   ↓
     ↓                          [Resource Group]
[AKS Cluster] ←───────────────────────┘
     │                               
     │ AUTHENTICATES_WITH            
     ↓                               
[ManagedIdentity] ────────────┐      
(Cluster Identity)            │      
     │                        │      
     │ ACCESSES               │      
     ↓                        │      
[Container Registry]          │      
                              │      
[AKS Cluster]                 │      
     │                        │      
     │ CONTAINS               │      
     ↓                        │      
[Namespace]                   │      
     │                        │      
     │ IN_NAMESPACE           │      
     ↓                        │      
[Pod] ←──────────────────────┘      
     │ AUTHENTICATES_WITH            
     │ (via Workload Identity)       
     ↓                               
[ManagedIdentity] ─────────┬────────┬────────────┐
(Workload Identity)        │        │            │
                          │        │            │
                      ACCESSES  ACCESSES    ACCESSES
                          │        │            │
                          ↓        ↓            ↓
                    [SQL DB]  [Key Vault]  [Storage]
                                   │
                                   │ STORES_IN
                                   ↓
                              [Storage Account]


[AKS Cluster] ──→ PART_OF_NETWORK ──→ [Virtual Network]
                                            │
                                            │ CONTAINS
                                            ↓
                                        [Subnet]
                                            │
                                            │ SECURED_BY
                                            ↓
                                          [NSG]
```

**Use Case**: Production application with proper identity management, network security, and resource organization.

---

## Diagram 5: Identity Access Audit Pattern

Shows how to trace all access paths from a resource through identities.

```
┌──────────────────────────────────────────────────────────────────┐
│                    Identity Access Audit                          │
└──────────────────────────────────────────────────────────────────┘

Starting Point: What can access my Key Vault?

                    [Key Vault]
                         ↑
            ┌────────────┼────────────┐
            │            │            │
         ACCESSES     ACCESSES     HAS_ROLE
            │            │            │
            ↑            ↑            ↑
    [ManagedIdentity] [ManagedIdentity] [ServicePrincipal]
    (app-identity)    (aks-identity)    (automation-sp)
            ↑            ↑            ↑
            │            │            │
    AUTHENTICATES  AUTHENTICATES  AUTHENTICATES
            │            │            │
            │            │            │
      [App Service]  [AKS Cluster]  [Deployment]


Query Result:
1. App Service (via app-identity) - Role: Key Vault Secrets User
2. AKS Cluster (via aks-identity) - Role: Key Vault Secrets User  
3. GitHub Actions (via automation-sp) - Role: Key Vault Administrator
```

**Query**:
```cypher
MATCH (kv:Resource:KeyVault {name: 'production-keyvault'})
MATCH (identity)-[:ACCESSES|HAS_ROLE]->(kv)
MATCH (resource)-[:AUTHENTICATES_WITH]->(identity)
RETURN resource.name, identity.name, labels(identity)[0] as identity_type
```

---

## Diagram 6: Overprivileged Identity Detection

Shows how to find identities with too many access rights.

```
┌──────────────────────────────────────────────────────────────────┐
│              Overprivileged Identity Pattern                      │
└──────────────────────────────────────────────────────────────────┘

[ManagedIdentity: legacy-app-identity]
     │
     ├──→ ACCESSES ──→ [Key Vault 1]
     │
     ├──→ ACCESSES ──→ [Key Vault 2]
     │
     ├──→ ACCESSES ──→ [Storage Account 1]
     │
     ├──→ ACCESSES ──→ [Storage Account 2]
     │
     ├──→ ACCESSES ──→ [SQL Database 1]
     │
     ├──→ ACCESSES ──→ [SQL Database 2]
     │
     └──→ HAS_ROLE ──→ [Resource Group]
          (role: Contributor) ⚠️  Too broad!


⚠️  Alert: Identity has access to 7 resources!
    Recommendation: Apply principle of least privilege
```

**Query**:
```cypher
MATCH (identity)-[:ACCESSES|HAS_ROLE]->(r:Resource)
WITH identity, count(r) as access_count
WHERE access_count > 5
RETURN identity.name, access_count
ORDER BY access_count DESC
```

---

## Real-World Scenarios

### Scenario 1: New Application Deployment

**Requirements**:
- App Service needs to read secrets from Key Vault
- App Service needs to write to Storage Account
- Database connection string stored in Key Vault

**Implementation**:
```cypher
// 1. Create resources
CREATE (app:Resource:AppService {id: '...', name: 'myapp'})
CREATE (kv:Resource:KeyVault {id: '...', name: 'myapp-kv'})
CREATE (storage:Resource:StorageAccount {id: '...', name: 'myappstorage'})
CREATE (db:Resource:SQLDatabase {id: '...', name: 'myapp-db'})

// 2. Create system-assigned managed identity
CREATE (mi:ManagedIdentity {
  id: '...',
  name: 'myapp-identity',
  identity_type: 'SystemAssigned',
  assigned_to_resource_id: app.id
})

// 3. Setup authentication
CREATE (app)-[:AUTHENTICATES_WITH]->(mi)

// 4. Grant access rights
CREATE (mi)-[:ACCESSES {role: 'Key Vault Secrets User'}]->(kv)
CREATE (mi)-[:ACCESSES {role: 'Storage Blob Data Contributor'}]->(storage)

// 5. Define dependencies
CREATE (app)-[:USES_SECRET_FROM]->(kv)
CREATE (app)-[:STORES_IN]->(storage)
CREATE (app)-[:DEPENDS_ON]->(db)
```

### Scenario 2: Kubernetes with Workload Identity

**Requirements**:
- AKS pods need to access SQL Database
- Each namespace uses different identity
- Minimize blast radius

**Implementation**:
```cypher
// 1. Create AKS and namespaces
CREATE (aks:Resource:AKS {id: '...', name: 'aks-prod'})
CREATE (ns_prod:Namespace {id: '...', name: 'production', cluster_id: aks.id})
CREATE (ns_dev:Namespace {id: '...', name: 'development', cluster_id: aks.id})

// 2. Create separate identities per namespace
CREATE (mi_prod:ManagedIdentity {name: 'prod-workload-identity', identity_type: 'UserAssigned'})
CREATE (mi_dev:ManagedIdentity {name: 'dev-workload-identity', identity_type: 'UserAssigned'})

// 3. Create pods
CREATE (pod_prod:Pod {name: 'app-pod', namespace: 'production', cluster_id: aks.id})
CREATE (pod_dev:Pod {name: 'app-pod', namespace: 'development', cluster_id: aks.id})

// 4. Create databases
CREATE (db_prod:Resource:SQLDatabase {name: 'db-prod'})
CREATE (db_dev:Resource:SQLDatabase {name: 'db-dev'})

// 5. Setup pod relationships
CREATE (pod_prod)-[:IN_NAMESPACE]->(ns_prod)
CREATE (pod_dev)-[:IN_NAMESPACE]->(ns_dev)

// 6. Setup authentication per environment
CREATE (pod_prod)-[:AUTHENTICATES_WITH]->(mi_prod)
CREATE (pod_dev)-[:AUTHENTICATES_WITH]->(mi_dev)

// 7. Grant minimal access (prod only accesses prod DB)
CREATE (mi_prod)-[:ACCESSES {role: 'SQL DB Contributor'}]->(db_prod)
CREATE (mi_dev)-[:ACCESSES {role: 'SQL DB Contributor'}]->(db_dev)
```

---

## Security Best Practices

### 1. Always Use Managed Identities
```cypher
// Find App Services not using managed identity
MATCH (app:Resource:AppService)
WHERE NOT (app)-[:AUTHENTICATES_WITH]->(:ManagedIdentity)
RETURN app.name, app.resource_group
```

### 2. Audit High-Privilege Roles
```cypher
// Find identities with Contributor or Owner roles
MATCH (identity)-[r:HAS_ROLE]->(resource)
WHERE r.role_name IN ['Contributor', 'Owner']
RETURN identity.name, r.role_name, resource.name
```

### 3. Find Service Principals with Expiring Credentials
```cypher
// Service principals with credentials (should rotate)
MATCH (sp:ServicePrincipal)
WHERE sp.password_credentials_count > 0 OR sp.key_credentials_count > 0
RETURN sp.display_name, sp.password_credentials_count, sp.key_credentials_count
```

### 4. Detect Cross-Environment Access
```cypher
// Identities that access resources in multiple environments
MATCH (mi:ManagedIdentity)-[:ACCESSES]->(r:Resource)
WITH mi, collect(DISTINCT r.environment) as environments
WHERE size(environments) > 1
RETURN mi.name, environments
```

---

## Summary

The identity and access models in TopDeck enable:

1. **Complete Visibility**: See all authentication flows and access rights
2. **Security Auditing**: Find overprivileged identities and missing controls
3. **Compliance**: Document who can access what and why
4. **Troubleshooting**: Quickly diagnose access-denied issues
5. **Best Practices**: Enforce least-privilege and managed identities

These models work together with resource, application, and Kubernetes models to provide a comprehensive view of your entire infrastructure and how everything connects and authenticates.
