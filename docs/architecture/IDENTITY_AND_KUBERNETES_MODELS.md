# Identity and Kubernetes Data Models

## Overview

This document describes the enhanced data models added to TopDeck to support:
1. **Kubernetes Resources**: Namespaces and Pods within AKS clusters
2. **Azure Identity & Access**: Managed Identities, Service Principals, and App Registrations

These additions enable TopDeck to model not just infrastructure resources, but also:
- How resources authenticate to each other
- What access rights different identities have
- How Kubernetes workloads are organized and deployed

---

## Kubernetes Models

### Namespace

Represents a Kubernetes namespace within a cluster (e.g., AKS).

**Use Cases**:
- Organize workloads by team, application, or environment
- Track resource quotas and limits
- Map deployment patterns

**Key Properties**:
```yaml
id: string                          # Unique identifier (cluster_id:namespace_name)
name: string                        # Namespace name (e.g., "production", "staging")
cluster_id: string                  # Parent AKS cluster resource ID
labels: map<string, string>         # Kubernetes labels
annotations: map<string, string>    # Kubernetes annotations
resource_quota: json                # CPU/memory quotas
limit_ranges: json                  # Resource limits
```

**Example**:
```cypher
CREATE (ns:Namespace {
  id: '/subscriptions/.../aks-prod:production',
  name: 'production',
  cluster_id: '/subscriptions/.../aks-prod',
  labels: {environment: 'prod', team: 'platform'},
  resource_quota: {cpu: '100', memory: '200Gi'}
})
```

---

### Pod

Represents a Kubernetes pod running in a cluster.

**Use Cases**:
- Track running workloads
- Monitor resource usage
- Map network connectivity
- Understand deployment patterns

**Key Properties**:
```yaml
id: string                          # Unique identifier
name: string                        # Pod name
namespace: string                   # Namespace name
cluster_id: string                  # Parent AKS cluster resource ID
phase: string                       # "Pending" | "Running" | "Succeeded" | "Failed" | "Unknown"
containers: json                    # Container specifications
pod_ip: string                      # Internal IP address
node_name: string                   # Node the pod is running on
cpu_requests: string                # CPU requests
cpu_limits: string                  # CPU limits
memory_requests: string             # Memory requests
memory_limits: string               # Memory limits
owner_kind: string                  # "Deployment" | "StatefulSet" | "DaemonSet"
owner_name: string                  # Owner resource name
labels: map<string, string>         # Kubernetes labels
```

**Example**:
```cypher
CREATE (pod:Pod {
  id: 'pod-12345',
  name: 'web-app-7b8c9d-xyz',
  namespace: 'production',
  cluster_id: '/subscriptions/.../aks-prod',
  phase: 'Running',
  pod_ip: '10.0.2.15',
  node_name: 'aks-nodepool1-12345',
  cpu_requests: '500m',
  memory_requests: '512Mi',
  owner_kind: 'Deployment',
  owner_name: 'web-app',
  labels: {app: 'web', version: 'v1.2.3'}
})
```

---

## Identity Models

### ManagedIdentity

Represents an Azure Managed Identity (system-assigned or user-assigned).

**Use Cases**:
- Show how resources authenticate without credentials
- Track which resources a managed identity can access
- Map identity propagation through the infrastructure

**Key Properties**:
```yaml
id: string                          # Azure resource ID
name: string                        # Identity name
identity_type: string               # "SystemAssigned" | "UserAssigned"
principal_id: string                # Azure AD object ID
client_id: string                   # Application ID
tenant_id: string                   # Azure AD tenant
assigned_to_resource_id: string     # For system-assigned identities
assigned_to_resource_type: string   # Resource type (e.g., "app_service")
```

**System-Assigned Identity Example**:
```cypher
CREATE (mi:ManagedIdentity {
  id: '/subscriptions/.../providers/Microsoft.Web/sites/myapp/identity',
  name: 'myapp-identity',
  identity_type: 'SystemAssigned',
  principal_id: 'abc123...',
  client_id: 'def456...',
  assigned_to_resource_id: '/subscriptions/.../Microsoft.Web/sites/myapp',
  assigned_to_resource_type: 'app_service'
})
```

**User-Assigned Identity Example**:
```cypher
CREATE (mi:ManagedIdentity {
  id: '/subscriptions/.../userAssignedIdentities/shared-identity',
  name: 'shared-identity',
  identity_type: 'UserAssigned',
  principal_id: 'xyz789...',
  client_id: 'uvw012...',
  resource_group: 'rg-shared',
  subscription_id: 'sub-123'
})
```

---

### ServicePrincipal

Represents an Azure Service Principal used for application and automation authentication.

**Use Cases**:
- Track automation accounts (CI/CD pipelines, scripts)
- Audit access rights for non-human identities
- Map credential lifecycle (expiration, rotation)

**Key Properties**:
```yaml
id: string                          # Azure AD object ID
app_id: string                      # Application (client) ID
display_name: string                # Human-readable name
service_principal_type: string      # "Application" | "ManagedIdentity" | "Legacy"
enabled: boolean                    # Whether the SP is enabled
password_credentials_count: int     # Number of client secrets
key_credentials_count: int          # Number of certificates
app_roles: json                     # Application roles
```

**Example**:
```cypher
CREATE (sp:ServicePrincipal {
  id: 'obj-abc123',
  app_id: 'app-def456',
  display_name: 'GitHub Actions Deployer',
  service_principal_type: 'Application',
  enabled: true,
  password_credentials_count: 1,
  key_credentials_count: 0
})
```

---

### AppRegistration

Represents an Azure AD App Registration that defines application identity.

**Use Cases**:
- Track application identity configurations
- Map API permissions and consent
- Understand multi-tenant application access

**Key Properties**:
```yaml
id: string                          # Azure AD object ID
app_id: string                      # Application (client) ID
display_name: string                # Application name
sign_in_audience: string            # "AzureADMyOrg" | "AzureADMultipleOrgs"
identifier_uris: list<string>       # Application ID URIs
redirect_uris: list<string>         # OAuth redirect URIs
required_resource_access: json      # API permissions
```

**Example**:
```cypher
CREATE (ar:AppRegistration {
  id: 'obj-xyz789',
  app_id: 'app-uvw012',
  display_name: 'Web Application',
  sign_in_audience: 'AzureADMyOrg',
  identifier_uris: ['api://mywebapp'],
  redirect_uris: ['https://mywebapp.com/auth/callback'],
  required_resource_access: [{resourceAppId: '00000003-0000-0000-c000-000000000000'}]
})
```

---

## Relationships

### AUTHENTICATES_WITH

**Usage**: `(Resource)-[:AUTHENTICATES_WITH]->(ManagedIdentity|ServicePrincipal)`

Shows how a resource authenticates to other services.

**Examples**:
```cypher
// App Service using managed identity
(AppService)-[:AUTHENTICATES_WITH {authentication_type: 'system_identity'}]->(ManagedIdentity)

// AKS cluster identity
(AKS)-[:AUTHENTICATES_WITH {authentication_type: 'user_identity'}]->(ManagedIdentity)

// Pipeline using service principal
(Deployment)-[:AUTHENTICATES_WITH {authentication_type: 'service_principal'}]->(ServicePrincipal)
```

---

### ACCESSES

**Usage**: `(ManagedIdentity|ServicePrincipal)-[:ACCESSES]->(Resource)`

Shows what resources an identity can access.

**Examples**:
```cypher
// Managed identity can read from storage
(ManagedIdentity)-[:ACCESSES {
  access_level: 'read',
  role_name: 'Storage Blob Data Reader',
  scope: 'resource'
}]->(StorageAccount)

// Service principal can manage resource group
(ServicePrincipal)-[:ACCESSES {
  access_level: 'write',
  role_name: 'Contributor',
  scope: 'resource_group'
}]->(ResourceGroup)
```

---

### HAS_ROLE

**Usage**: `(ServicePrincipal|ManagedIdentity)-[:HAS_ROLE]->(Resource)`

Represents RBAC role assignments.

**Example**:
```cypher
(ServicePrincipal)-[:HAS_ROLE {
  role_name: 'Key Vault Secrets User',
  scope: 'resource',
  role_definition_id: '/subscriptions/.../roleDefinitions/...',
  assigned_at: '2024-01-15T10:30:00Z'
}]->(KeyVault)
```

---

### IN_NAMESPACE

**Usage**: `(Pod)-[:IN_NAMESPACE]->(Namespace)`

Links pods to their containing namespace.

**Example**:
```cypher
(Pod {name: 'web-app-xyz'})-[:IN_NAMESPACE]->(Namespace {name: 'production'})
```

---

### LINKED_TO_APP

**Usage**: `(ServicePrincipal)-[:LINKED_TO_APP]->(AppRegistration)`

Links service principals to their app registrations.

**Example**:
```cypher
(ServicePrincipal {display_name: 'GitHub Actions'})-[:LINKED_TO_APP]->(AppRegistration {display_name: 'GitHub Actions App'})
```

---

## Query Patterns

### Find Identity Access Chain

```cypher
// Find what a resource can access through its identity
MATCH (r:Resource {name: 'my-app-service'})-[:AUTHENTICATES_WITH]->(mi:ManagedIdentity)
MATCH (mi)-[:ACCESSES]->(target:Resource)
RETURN r.name as resource, mi.name as identity, collect(target.name) as can_access;
```

### Find All Identities with Access to a Resource

```cypher
// Find all managed identities and service principals that can access a resource
MATCH (identity)-[:ACCESSES|HAS_ROLE]->(r:Resource {name: 'production-keyvault'})
RETURN identity.name, labels(identity)[0] as identity_type, identity.principal_id;
```

### Find Kubernetes Workload Distribution

```cypher
// Pods per namespace with their phases
MATCH (ns:Namespace {cluster_id: $cluster_id})<-[:IN_NAMESPACE]-(pod:Pod)
RETURN ns.name, 
       count(pod) as total_pods,
       collect(DISTINCT pod.phase) as phases,
       collect(DISTINCT pod.owner_kind) as workload_types;
```

### Find Resources Without Managed Identities

```cypher
// App Services not using managed identity
MATCH (app:Resource {resource_type: 'app_service'})
WHERE NOT (app)-[:AUTHENTICATES_WITH]->(:ManagedIdentity)
RETURN app.name, app.resource_group;
```

### Find Overprivileged Identities

```cypher
// Identities with access to many resources
MATCH (identity)-[:ACCESSES]->(r:Resource)
WITH identity, count(r) as access_count
WHERE access_count > 10
RETURN identity.name, 
       labels(identity)[0] as type,
       access_count
ORDER BY access_count DESC;
```

### Find Pod Network Topology

```cypher
// Pods and their network connections
MATCH (pod:Pod {namespace: 'production'})-[:CONNECTS_TO]->(target)
RETURN pod.name, pod.pod_ip, 
       collect({name: target.name, type: labels(target)[0]}) as connections;
```

---

## Integration Examples

### Scenario 1: App Service with Managed Identity Accessing Key Vault

```cypher
// Create resources
CREATE (app:Resource:AppService {
  id: '/subscriptions/.../sites/myapp',
  name: 'myapp',
  resource_type: 'app_service'
})

CREATE (mi:ManagedIdentity {
  id: '/subscriptions/.../sites/myapp/identity',
  name: 'myapp-identity',
  identity_type: 'SystemAssigned',
  assigned_to_resource_id: app.id
})

CREATE (kv:Resource:KeyVault {
  id: '/subscriptions/.../vaults/myvault',
  name: 'myvault',
  resource_type: 'key_vault'
})

// Create relationships
CREATE (app)-[:AUTHENTICATES_WITH {authentication_type: 'system_identity'}]->(mi)
CREATE (mi)-[:ACCESSES {role_name: 'Key Vault Secrets User', access_level: 'read'}]->(kv)
CREATE (app)-[:USES_SECRET_FROM]->(kv)

// Query: What can myapp access?
MATCH (app:Resource {name: 'myapp'})-[:AUTHENTICATES_WITH]->(mi)-[:ACCESSES]->(target)
RETURN target.name, target.resource_type;
```

### Scenario 2: AKS Cluster with Pods and Identities

```cypher
// Create AKS cluster
CREATE (aks:Resource:AKS {
  id: '/subscriptions/.../aks-prod',
  name: 'aks-prod',
  resource_type: 'aks'
})

// Create cluster managed identity
CREATE (mi:ManagedIdentity {
  id: '/subscriptions/.../userAssignedIdentities/aks-identity',
  name: 'aks-identity',
  identity_type: 'UserAssigned'
})

// Create namespace
CREATE (ns:Namespace {
  id: '/subscriptions/.../aks-prod:production',
  name: 'production',
  cluster_id: aks.id
})

// Create pod
CREATE (pod:Pod {
  id: 'pod-12345',
  name: 'web-app-xyz',
  namespace: 'production',
  cluster_id: aks.id,
  phase: 'Running'
})

// Create relationships
CREATE (aks)-[:CONTAINS]->(ns)
CREATE (pod)-[:IN_NAMESPACE]->(ns)
CREATE (aks)-[:AUTHENTICATES_WITH]->(mi)

// Query: Full AKS topology
MATCH path = (aks:Resource:AKS)-[*]-(n)
WHERE aks.name = 'aks-prod'
RETURN path;
```

---

## Benefits

### Security Visibility
- **Identity Audit**: See all identities and their access rights
- **Least Privilege**: Find overprivileged identities
- **Access Patterns**: Understand authentication flows

### Compliance
- **RBAC Mapping**: Complete view of role assignments
- **Credential Tracking**: Monitor service principals with credentials
- **Access Reviews**: Regular audit of identity access

### Kubernetes Operations
- **Resource Tracking**: See all workloads across clusters
- **Namespace Organization**: Understand workload distribution
- **Capacity Planning**: Analyze resource usage patterns

### Troubleshooting
- **Authentication Issues**: Trace identity configuration problems
- **Access Denied**: Find missing role assignments
- **Pod Failures**: Analyze pod status and relationships

---

## Next Steps

1. **Discovery Implementation**:
   - Implement Azure AD discovery for identities
   - Implement RBAC role assignment discovery
   - Implement Kubernetes API discovery for pods/namespaces

2. **Enhanced Queries**:
   - Build dashboards for identity access patterns
   - Create alerts for overprivileged identities
   - Monitor pod health across clusters

3. **Security Analysis**:
   - Detect resources without managed identities
   - Find service principals with expiring credentials
   - Audit identity access to sensitive resources

4. **Cost Optimization**:
   - Track AKS resource usage by namespace
   - Identify underutilized pods
   - Analyze identity-related costs
