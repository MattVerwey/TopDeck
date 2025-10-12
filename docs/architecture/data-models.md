# TopDeck Data Models

## Overview

This document defines the core data models for TopDeck's graph database (Neo4j). These models represent cloud resources, applications, code repositories, and their relationships to provide a comprehensive view of the entire technology stack.

## Design Principles

1. **Cloud-Agnostic Core**: Common properties across all cloud providers with extensible cloud-specific attributes
2. **Rich Relationships**: Relationships capture not just connections but also their characteristics (type, strength, metadata)
3. **Temporal Tracking**: All nodes track creation, last seen, and update times for drift detection
4. **Flexible Properties**: Use of JSON/map properties for cloud-specific configurations
5. **Performance Optimized**: Strategic indexes on frequently queried properties
6. **Linkage-Ready**: All resources include properties needed to establish relationships across the environment

---

## Node Types

### 1. Resource (Cloud Resources)

Represents any cloud infrastructure resource (compute, network, data, configuration).

**Labels**: `:Resource` with additional label for specific type (e.g., `:Resource:AKS`, `:Resource:VirtualNetwork`)

**Properties**:
```yaml
# Core Properties
id: string                          # Unique identifier (Azure: resource ID, AWS: ARN, GCP: resource URL)
cloud_provider: string              # "azure" | "aws" | "gcp"
resource_type: string               # "aks" | "app_service" | "sql_database" | "vnet" | etc.
name: string                        # Resource name
display_name: string                # User-friendly name
region: string                      # Azure: "eastus", AWS: "us-east-1", GCP: "us-central1"
resource_group: string              # Azure resource group or AWS tag equivalent
subscription_id: string             # Azure subscription or AWS account ID

# Status & Health
status: string                      # "running" | "stopped" | "error" | "degraded" | "unknown"
health_status: string               # "healthy" | "warning" | "critical" | "unknown"
provisioning_state: string          # "Succeeded" | "Failed" | "Creating" | "Updating"

# Metadata
tags: map<string, string>           # Resource tags/labels
created_at: timestamp               # When resource was created in cloud
last_seen: timestamp                # Last time discovered by TopDeck
last_modified: timestamp            # Last modification in cloud
discovered_at: timestamp            # First time discovered by TopDeck

# Cost & Compliance
cost_per_day: float                 # Estimated daily cost in USD
cost_center: string                 # Cost center or billing tag
environment: string                 # "prod" | "staging" | "dev" | "test"
compliance_status: string           # "compliant" | "non-compliant" | "unknown"

# Cloud-Specific Properties
properties: json                    # Flexible storage for cloud-specific configs
sku: string                         # SKU/tier information
pricing_tier: string                # Pricing tier or instance type

# Network Properties (for resources with network presence)
private_ip_addresses: list<string>  # Internal IPs
public_ip_addresses: list<string>   # External IPs
fqdn: string                        # Fully qualified domain name
ports: list<int>                    # Exposed ports

# References
parent_resource_id: string          # Parent resource (e.g., AKS for pods)
managed_by: string                  # Managing service or controller
```

**Specific Resource Types**:

#### AKS Cluster (`:Resource:AKS`)
```yaml
kubernetes_version: string
node_pool_count: int
total_nodes: int
dns_prefix: string
network_plugin: string              # "azure" | "kubenet"
load_balancer_sku: string
api_server_address: string
identity_type: string               # "SystemAssigned" | "UserAssigned"
addon_profiles: json                # Enabled add-ons
```

#### App Service (`:Resource:AppService`)
```yaml
kind: string                        # "app" | "functionapp" | "api"
default_hostname: string
runtime_stack: string               # "node" | "python" | "dotnet" | etc.
runtime_version: string
app_service_plan_id: string         # Link to plan
always_on: boolean
https_only: boolean
ftps_state: string
min_tls_version: string
```

#### Virtual Machine (`:Resource:VirtualMachine`)
```yaml
vm_size: string                     # "Standard_D2s_v3"
os_type: string                     # "Linux" | "Windows"
os_disk_size_gb: int
image_publisher: string
image_offer: string
image_sku: string
availability_zone: string
vm_scale_set_id: string             # If part of scale set
```

#### SQL Database (`:Resource:SQLDatabase`)
```yaml
server_name: string
database_edition: string            # "Basic" | "Standard" | "Premium"
service_objective: string
max_size_bytes: int
collation: string
connection_string_template: string  # Masked connection string
backup_retention_days: int
geo_replication_enabled: boolean
```

#### Virtual Network (`:Resource:VirtualNetwork`)
```yaml
address_space: list<string>         # CIDR blocks
dhcp_options: json
enable_ddos_protection: boolean
enable_vm_protection: boolean
```

#### Subnet (`:Resource:Subnet`)
```yaml
address_prefix: string              # CIDR block
network_security_group_id: string
route_table_id: string
service_endpoints: list<string>
delegations: list<string>
```

#### Load Balancer (`:Resource:LoadBalancer`)
```yaml
lb_type: string                     # "public" | "internal"
frontend_ip_configurations: json
backend_pools: json
health_probes: json
load_balancing_rules: json
```

#### Application Gateway (`:Resource:ApplicationGateway`)
```yaml
sku_name: string
sku_tier: string
capacity: int
backend_pools: json
http_listeners: json
request_routing_rules: json
waf_enabled: boolean
waf_mode: string                    # "Detection" | "Prevention"
```

#### Network Security Group (`:Resource:NSG`)
```yaml
security_rules: json                # Inbound/outbound rules
default_security_rules: json
```

#### Storage Account (`:Resource:StorageAccount`)
```yaml
account_kind: string                # "StorageV2" | "BlobStorage"
account_tier: string                # "Standard" | "Premium"
replication_type: string            # "LRS" | "GRS" | "RA-GRS"
access_tier: string                 # "Hot" | "Cool"
enable_https_traffic_only: boolean
blob_endpoint: string
file_endpoint: string
queue_endpoint: string
table_endpoint: string
```

#### Key Vault (`:Resource:KeyVault`)
```yaml
vault_uri: string
enable_soft_delete: boolean
soft_delete_retention_days: int
enable_purge_protection: boolean
enable_rbac_authorization: boolean
network_acls: json
```

---

### 2. Application

Represents a deployed application or service.

**Label**: `:Application`

**Properties**:
```yaml
# Core Properties
id: string                          # Unique identifier
name: string                        # Application name
description: string                 # Application description

# Ownership & Organization
owner_team: string                  # Owning team
owner_email: string                 # Team contact
business_unit: string
cost_center: string

# Code & Deployment
repository_url: string              # Git repository URL
repository_id: string               # Link to Repository node
deployment_method: string           # "aks" | "app_service" | "vm" | "container_instance"
environment: string                 # "prod" | "staging" | "dev"

# Health & Metrics
health_score: float                 # 0-100 overall health score
availability: float                 # 0-100 uptime percentage
error_rate: float                   # Errors per minute
response_time_avg: float            # Average response time in ms

# Version & Deployment
current_version: string             # Current deployed version
last_deployed: timestamp            # Last deployment time
last_deployed_by: string            # User who deployed
deployment_frequency: float         # Deployments per day

# Discovery
last_seen: timestamp
discovered_at: timestamp
```

---

### 3. Repository

Represents a code repository (GitHub, Azure DevOps, GitLab).

**Label**: `:Repository`

**Properties**:
```yaml
# Core Properties
id: string                          # Unique identifier
platform: string                    # "github" | "azure_devops" | "gitlab"
url: string                         # Repository URL
name: string                        # Repository name
full_name: string                   # org/repo format

# Branch & Commit Info
default_branch: string              # Usually "main" or "master"
last_commit_sha: string
last_commit_message: string
last_commit_date: timestamp
last_commit_author: string

# Repository Metadata
description: string
language: string                    # Primary language
topics: list<string>                # Tags/topics
is_private: boolean
is_archived: boolean

# Activity Metrics
stars: int
forks: int
open_issues: int
contributors_count: int
last_activity: timestamp

# Discovery
last_seen: timestamp
discovered_at: timestamp
```

---

### 4. Deployment

Represents a deployment event or pipeline run.

**Label**: `:Deployment`

**Properties**:
```yaml
# Core Properties
id: string                          # Unique identifier
pipeline_id: string                 # CI/CD pipeline identifier
pipeline_name: string
run_number: int                     # Build/run number

# Version & Artifact
version: string                     # Deployed version (tag, commit, etc.)
artifact_url: string                # URL to deployment artifact
commit_sha: string                  # Git commit SHA

# Deployment Details
deployed_at: timestamp
deployed_by: string                 # User or service principal
deployment_duration: int            # Duration in seconds
status: string                      # "success" | "failed" | "in_progress" | "cancelled"

# Environment
environment: string                 # Target environment
target_resources: list<string>      # Resource IDs where deployed

# Change Information
change_ticket_id: string            # Change management ticket
approval_status: string             # "approved" | "rejected" | "pending"
approvers: list<string>

# Metadata
notes: string                       # Deployment notes
rollback_available: boolean
previous_version: string

# Discovery
discovered_at: timestamp
```

---

### 5. Namespace (Kubernetes)

Represents a Kubernetes namespace within an AKS cluster.

**Label**: `:Namespace`

**Properties**:
```yaml
# Core Properties
id: string                          # Unique identifier (cluster_id:namespace_name)
name: string                        # Namespace name
cluster_id: string                  # Parent AKS cluster ID

# Metadata
labels: map<string, string>
annotations: map<string, string>
created_at: timestamp

# Resource Quotas
resource_quota: json                # CPU/memory quotas
limit_ranges: json

# Discovery
last_seen: timestamp
discovered_at: timestamp
```

---

### 6. Pod (Kubernetes)

Represents a Kubernetes pod.

**Label**: `:Pod`

**Properties**:
```yaml
# Core Properties
id: string                          # Unique identifier
name: string                        # Pod name
namespace: string
cluster_id: string                  # Parent AKS cluster ID

# Pod Specification
containers: json                    # Container details
init_containers: json
volumes: json
service_account: string

# Status
phase: string                       # "Pending" | "Running" | "Succeeded" | "Failed" | "Unknown"
conditions: json                    # Ready, Initialized, etc.
pod_ip: string
host_ip: string
node_name: string

# Resource Usage
cpu_requests: string
cpu_limits: string
memory_requests: string
memory_limits: string

# Ownership
owner_kind: string                  # "Deployment" | "StatefulSet" | "DaemonSet" | "Job"
owner_name: string

# Metadata
labels: map<string, string>
annotations: map<string, string>
created_at: timestamp
started_at: timestamp

# Discovery
last_seen: timestamp
discovered_at: timestamp
```

---

### 7. ManagedIdentity

Represents an Azure Managed Identity (system-assigned or user-assigned) used for authentication between resources.

**Label**: `:ManagedIdentity`

**Properties**:
```yaml
# Core Properties
id: string                          # Azure resource ID
name: string                        # Identity name
identity_type: string               # "SystemAssigned" | "UserAssigned"

# Identity Details
principal_id: string                # Azure AD object ID
client_id: string                   # Application ID
tenant_id: string

# Location & Organization
region: string
resource_group: string
subscription_id: string

# Associated Resource (for system-assigned)
assigned_to_resource_id: string     # Resource this identity is assigned to
assigned_to_resource_type: string   # Type of resource

# Metadata
tags: map<string, string>
created_at: timestamp

# Discovery
last_seen: timestamp
discovered_at: timestamp
```

---

### 8. ServicePrincipal

Represents an Azure Service Principal used for application and automation authentication.

**Label**: `:ServicePrincipal`

**Properties**:
```yaml
# Core Properties
id: string                          # Azure AD object ID
app_id: string                      # Application (client) ID
display_name: string

# Identity Details
tenant_id: string
app_owner_organization_id: string

# Type & Configuration
service_principal_type: string      # "Application" | "ManagedIdentity" | "Legacy"
password_credentials_count: int     # Number of password credentials
key_credentials_count: int          # Number of certificate credentials

# Permissions
app_roles: json                     # Application roles
oauth2_permissions: json            # OAuth2 permissions

# Metadata
enabled: boolean
tags: list<string>
created_at: timestamp

# Discovery
last_seen: timestamp
discovered_at: timestamp
```

---

### 9. AppRegistration

Represents an Azure AD App Registration defining application identity and API permissions.

**Label**: `:AppRegistration`

**Properties**:
```yaml
# Core Properties
id: string                          # Azure AD object ID
app_id: string                      # Application (client) ID
display_name: string

# Identity Configuration
tenant_id: string
publisher_domain: string
sign_in_audience: string            # "AzureADMyOrg" | "AzureADMultipleOrgs" | etc.

# URIs
identifier_uris: list<string>       # Application ID URIs
redirect_uris: list<string>         # Redirect URIs
home_page_url: string
logout_url: string

# API Permissions
required_resource_access: json      # Required API permissions

# Credentials
password_credentials_count: int
key_credentials_count: int

# Exposed API
app_roles: json                     # Exposed app roles
oauth2_permissions: json            # Exposed OAuth2 permissions

# Metadata
tags: list<string>
created_at: timestamp

# Discovery
last_seen: timestamp
discovered_at: timestamp
```

---

## Relationship Types

### 1. DEPENDS_ON

Represents a dependency between resources where one resource requires another to function.

**Usage**: `(Resource)-[:DEPENDS_ON]->(Resource)`

**Properties**:
```yaml
dependency_type: string             # "required" | "optional" | "strong" | "weak"
category: string                    # "network" | "data" | "configuration" | "compute"
strength: float                     # 0.0-1.0 (criticality of dependency)
discovered_at: timestamp
discovered_method: string           # "configuration" | "network_traffic" | "tags" | "explicit"
description: string                 # Human-readable dependency description
```

**Examples**:
- `(AppService)-[:DEPENDS_ON {category: "data"}]->(SQLDatabase)`
- `(AKS)-[:DEPENDS_ON {category: "network"}]->(VirtualNetwork)`
- `(ApplicationGateway)-[:DEPENDS_ON {category: "network"}]->(AKS)`

---

### 2. CONNECTS_TO

Represents network connectivity or communication between resources.

**Usage**: `(Resource)-[:CONNECTS_TO]->(Resource)`

**Properties**:
```yaml
protocol: string                    # "http" | "https" | "tcp" | "udp" | "sql" | "grpc"
port: int                           # Target port
source_port: int                    # Source port (if applicable)
direction: string                   # "inbound" | "outbound" | "bidirectional"

# Traffic Metrics
frequency: int                      # Requests/connections per minute
latency_avg: float                  # Average latency in ms
latency_p95: float                  # 95th percentile latency
error_rate: float                   # Error percentage
bandwidth_mbps: float               # Average bandwidth usage

# Discovery & Validation
discovered_at: timestamp
discovered_method: string           # "nsg_rules" | "network_trace" | "config" | "observation"
last_verified: timestamp
connection_status: string           # "active" | "idle" | "failed"
```

**Examples**:
- `(Pod)-[:CONNECTS_TO {protocol: "https", port: 443}]->(SQLDatabase)`
- `(LoadBalancer)-[:CONNECTS_TO {protocol: "http", port: 80}]->(Pod)`

---

### 3. CONTAINS

Represents a parent-child containment relationship.

**Usage**: `(ParentResource)-[:CONTAINS]->(ChildResource)`

**Properties**:
```yaml
containment_type: string            # "logical" | "physical" | "network"
discovered_at: timestamp
```

**Examples**:
- `(AKS)-[:CONTAINS]->(Namespace)`
- `(Namespace)-[:CONTAINS]->(Pod)`
- `(VirtualNetwork)-[:CONTAINS]->(Subnet)`
- `(Subnet)-[:CONTAINS]->(VirtualMachine)`
- `(ResourceGroup)-[:CONTAINS]->(Resource)`

---

### 4. DEPLOYED_TO

Represents deployment of an application to infrastructure.

**Usage**: `(Application)-[:DEPLOYED_TO]->(Resource)`

**Properties**:
```yaml
deployment_id: string               # Link to Deployment node
deployed_at: timestamp
version: string                     # Deployed version
deployment_status: string           # "active" | "inactive" | "failed"
deployment_method: string           # "helm" | "kubectl" | "terraform" | "arm_template"
configuration: json                 # Deployment-specific config
```

**Examples**:
- `(Application)-[:DEPLOYED_TO]->(AKS)`
- `(Application)-[:DEPLOYED_TO]->(AppService)`
- `(Application)-[:DEPLOYED_TO]->(Pod)`

---

### 5. BUILT_FROM

Represents the relationship between an application and its source code.

**Usage**: `(Application)-[:BUILT_FROM]->(Repository)`

**Properties**:
```yaml
branch: string                      # Git branch
commit_sha: string                  # Git commit
build_date: timestamp
build_pipeline: string
```

---

### 6. DEPLOYS_TO

Represents CI/CD pipeline deployment to infrastructure.

**Usage**: `(Deployment)-[:DEPLOYS_TO]->(Resource)`

**Properties**:
```yaml
deployed_at: timestamp
status: string                      # "success" | "failed"
duration: int                       # Deployment duration in seconds
```

---

### 7. ORIGINATED_FROM

Links a deployment to its source repository.

**Usage**: `(Deployment)-[:ORIGINATED_FROM]->(Repository)`

**Properties**:
```yaml
branch: string
commit_sha: string
pipeline_id: string
```

---

### 8. SECURED_BY

Represents security relationships (NSG, firewall rules, etc.).

**Usage**: `(Resource)-[:SECURED_BY]->(NSG|ApplicationGateway)`

**Properties**:
```yaml
rule_type: string                   # "firewall" | "nsg" | "waf"
rules_applied: json                 # Specific rules
discovered_at: timestamp
```

**Examples**:
- `(Subnet)-[:SECURED_BY]->(NSG)`
- `(ApplicationGateway)-[:SECURED_BY {rule_type: "waf"}]->(ApplicationGateway)`

---

### 9. ROUTES_TO

Represents routing relationships (load balancers, application gateways).

**Usage**: `(LoadBalancer|ApplicationGateway)-[:ROUTES_TO]->(Resource)`

**Properties**:
```yaml
routing_rule: string                # Rule name/identifier
port: int                           # Target port
protocol: string                    # "http" | "https" | "tcp"
health_probe: string                # Health check configuration
priority: int                       # Routing priority
path_pattern: string                # URL path pattern (for L7 routing)
```

**Examples**:
- `(LoadBalancer)-[:ROUTES_TO]->(Pod)`
- `(ApplicationGateway)-[:ROUTES_TO {path_pattern: "/api/*"}]->(AppService)`

---

### 10. STORES_IN

Represents data storage relationships.

**Usage**: `(Resource)-[:STORES_IN]->(StorageAccount|SQLDatabase)`

**Properties**:
```yaml
storage_type: string                # "blob" | "file" | "queue" | "table" | "database"
access_pattern: string              # "read" | "write" | "read_write"
encryption_enabled: boolean
discovered_at: timestamp
```

---

### 11. USES_SECRET_FROM

Represents configuration/secrets sourcing.

**Usage**: `(Resource)-[:USES_SECRET_FROM]->(KeyVault)`

**Properties**:
```yaml
secret_names: list<string>          # Secret identifiers used
access_method: string               # "system_identity" | "user_identity" | "connection_string"
discovered_at: timestamp
```

---

### 12. PART_OF_NETWORK

Represents network membership.

**Usage**: `(Resource)-[:PART_OF_NETWORK]->(VirtualNetwork|Subnet)`

**Properties**:
```yaml
ip_address: string
allocation_method: string           # "static" | "dynamic"
is_primary: boolean
discovered_at: timestamp
```

---

### 13. EXPOSES_SERVICE

Represents service exposure (Kubernetes services, ingress).

**Usage**: `(Pod|Deployment)-[:EXPOSES_SERVICE]->(Service|Ingress)`

**Properties**:
```yaml
service_type: string                # "ClusterIP" | "LoadBalancer" | "NodePort"
ports: json                         # Port mappings
selectors: json                     # Service selectors
```

---

### 14. AUTHENTICATES_WITH

Represents authentication relationships between resources and identities.

**Usage**: `(Resource)-[:AUTHENTICATES_WITH]->(ManagedIdentity|ServicePrincipal)`

**Properties**:
```yaml
authentication_type: string         # "system_identity" | "user_identity" | "service_principal"
scope: string                       # Scope of authentication
discovered_at: timestamp
discovered_method: string           # "configuration" | "iam_policy" | "rbac"
```

**Examples**:
- `(AppService)-[:AUTHENTICATES_WITH]->(ManagedIdentity)` - App Service uses managed identity
- `(AKS)-[:AUTHENTICATES_WITH]->(ManagedIdentity)` - AKS cluster identity
- `(Deployment)-[:AUTHENTICATES_WITH]->(ServicePrincipal)` - Pipeline uses service principal

---

### 15. ACCESSES

Represents access rights from identities to resources.

**Usage**: `(ManagedIdentity|ServicePrincipal)-[:ACCESSES]->(Resource)`

**Properties**:
```yaml
access_level: string                # "read" | "write" | "admin" | "owner"
role_name: string                   # RBAC role name
scope: string                       # Scope of access (subscription, resource group, resource)
granted_at: timestamp
discovered_at: timestamp
discovered_method: string           # "rbac" | "iam_policy" | "configuration"
```

**Examples**:
- `(ManagedIdentity)-[:ACCESSES {role_name: "Storage Blob Data Reader"}]->(StorageAccount)`
- `(ServicePrincipal)-[:ACCESSES {role_name: "Contributor"}]->(ResourceGroup)`

---

### 16. HAS_ROLE

Represents role assignments for identities on resources.

**Usage**: `(ServicePrincipal|ManagedIdentity)-[:HAS_ROLE]->(Resource)`

**Properties**:
```yaml
role_definition_id: string          # Azure role definition ID
role_name: string                   # Role name (e.g., "Contributor", "Reader")
scope: string                       # Scope of the role assignment
assigned_at: timestamp
assigned_by: string                 # Who assigned the role
principal_type: string              # "ServicePrincipal" | "ManagedIdentity" | "User" | "Group"
discovered_at: timestamp
```

**Examples**:
- `(ServicePrincipal)-[:HAS_ROLE {role_name: "Key Vault Secrets User"}]->(KeyVault)`
- `(ManagedIdentity)-[:HAS_ROLE {role_name: "SQL DB Contributor"}]->(SQLDatabase)`

---

### 17. LINKED_TO_APP

Links Service Principals to their App Registrations.

**Usage**: `(ServicePrincipal)-[:LINKED_TO_APP]->(AppRegistration)`

**Properties**:
```yaml
created_at: timestamp
discovered_at: timestamp
```

**Example**:
- `(ServicePrincipal)-[:LINKED_TO_APP]->(AppRegistration)` - SP is the service identity for the app

---

### 18. IN_NAMESPACE

Represents Kubernetes pod containment in namespaces.

**Usage**: `(Pod)-[:IN_NAMESPACE]->(Namespace)`

**Properties**:
```yaml
discovered_at: timestamp
```

**Example**:
- `(Pod)-[:IN_NAMESPACE]->(Namespace {name: "production"})`

---

## Indexes

Indexes are critical for query performance. The following indexes should be created:

```cypher
-- Resource indexes
CREATE INDEX resource_id FOR (r:Resource) ON (r.id);
CREATE INDEX resource_type FOR (r:Resource) ON (r.resource_type);
CREATE INDEX resource_cloud_provider FOR (r:Resource) ON (r.cloud_provider);
CREATE INDEX resource_name FOR (r:Resource) ON (r.name);
CREATE INDEX resource_region FOR (r:Resource) ON (r.region);
CREATE INDEX resource_status FOR (r:Resource) ON (r.status);
CREATE INDEX resource_environment FOR (r:Resource) ON (r.environment);
CREATE INDEX resource_subscription FOR (r:Resource) ON (r.subscription_id);

-- Application indexes
CREATE INDEX application_id FOR (a:Application) ON (a.id);
CREATE INDEX application_name FOR (a:Application) ON (a.name);
CREATE INDEX application_owner FOR (a:Application) ON (a.owner_team);
CREATE INDEX application_environment FOR (a:Application) ON (a.environment);

-- Repository indexes
CREATE INDEX repository_id FOR (r:Repository) ON (r.id);
CREATE INDEX repository_url FOR (r:Repository) ON (r.url);
CREATE INDEX repository_name FOR (r:Repository) ON (r.name);

-- Deployment indexes
CREATE INDEX deployment_id FOR (d:Deployment) ON (d.id);
CREATE INDEX deployment_status FOR (d:Deployment) ON (d.status);
CREATE INDEX deployment_date FOR (d:Deployment) ON (d.deployed_at);

-- Namespace indexes
CREATE INDEX namespace_id FOR (n:Namespace) ON (n.id);
CREATE INDEX namespace_name FOR (n:Namespace) ON (n.name);
CREATE INDEX namespace_cluster FOR (n:Namespace) ON (n.cluster_id);

-- Pod indexes
CREATE INDEX pod_id FOR (p:Pod) ON (p.id);
CREATE INDEX pod_name FOR (p:Pod) ON (p.name);
CREATE INDEX pod_namespace FOR (p:Pod) ON (p.namespace);
CREATE INDEX pod_cluster FOR (p:Pod) ON (p.cluster_id);

-- ManagedIdentity indexes
CREATE INDEX managed_identity_id FOR (mi:ManagedIdentity) ON (mi.id);
CREATE INDEX managed_identity_principal_id FOR (mi:ManagedIdentity) ON (mi.principal_id);
CREATE INDEX managed_identity_type FOR (mi:ManagedIdentity) ON (mi.identity_type);
CREATE INDEX managed_identity_assigned_to FOR (mi:ManagedIdentity) ON (mi.assigned_to_resource_id);

-- ServicePrincipal indexes
CREATE INDEX service_principal_id FOR (sp:ServicePrincipal) ON (sp.id);
CREATE INDEX service_principal_app_id FOR (sp:ServicePrincipal) ON (sp.app_id);
CREATE INDEX service_principal_display_name FOR (sp:ServicePrincipal) ON (sp.display_name);

-- AppRegistration indexes
CREATE INDEX app_registration_id FOR (ar:AppRegistration) ON (ar.id);
CREATE INDEX app_registration_app_id FOR (ar:AppRegistration) ON (ar.app_id);
CREATE INDEX app_registration_display_name FOR (ar:AppRegistration) ON (ar.display_name);

-- Composite indexes for common queries
CREATE INDEX resource_type_provider FOR (r:Resource) ON (r.resource_type, r.cloud_provider);
CREATE INDEX resource_region_type FOR (r:Resource) ON (r.region, r.resource_type);
```

---

## Constraints

Enforce uniqueness and data integrity:

```cypher
-- Unique constraints
CREATE CONSTRAINT resource_id_unique FOR (r:Resource) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT application_id_unique FOR (a:Application) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT repository_id_unique FOR (r:Repository) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT deployment_id_unique FOR (d:Deployment) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT namespace_id_unique FOR (n:Namespace) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT pod_id_unique FOR (p:Pod) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT managed_identity_id_unique FOR (mi:ManagedIdentity) REQUIRE mi.id IS UNIQUE;
CREATE CONSTRAINT service_principal_id_unique FOR (sp:ServicePrincipal) REQUIRE sp.id IS UNIQUE;
CREATE CONSTRAINT app_registration_id_unique FOR (ar:AppRegistration) REQUIRE ar.id IS UNIQUE;

-- Existence constraints (ensure critical properties exist)
CREATE CONSTRAINT resource_type_exists FOR (r:Resource) REQUIRE r.resource_type IS NOT NULL;
CREATE CONSTRAINT resource_cloud_exists FOR (r:Resource) REQUIRE r.cloud_provider IS NOT NULL;
CREATE CONSTRAINT application_name_exists FOR (a:Application) REQUIRE a.name IS NOT NULL;
```

---

## Common Query Patterns

### 1. Find All Dependencies of a Resource

```cypher
// Direct dependencies
MATCH (r:Resource {id: $resource_id})-[:DEPENDS_ON]->(dep:Resource)
RETURN dep;

// Transitive dependencies (up to 5 levels deep)
MATCH path = (r:Resource {id: $resource_id})-[:DEPENDS_ON*1..5]->(dep:Resource)
RETURN dep, length(path) as depth
ORDER BY depth;

// Dependency chain with details
MATCH path = (r:Resource {id: $resource_id})-[:DEPENDS_ON*1..5]->(dep:Resource)
RETURN 
  nodes(path) as resources,
  relationships(path) as dependencies,
  length(path) as depth;
```

### 2. Find All Resources in an Environment

```cypher
MATCH (r:Resource {environment: $environment})
RETURN r
ORDER BY r.resource_type, r.name;

// With relationships
MATCH (r:Resource {environment: $environment})
OPTIONAL MATCH (r)-[rel]-(other:Resource)
RETURN r, rel, other;
```

### 3. Find Application Topology

```cypher
// Find application and all its deployed resources
MATCH (app:Application {name: $app_name})-[:DEPLOYED_TO]->(resource:Resource)
RETURN app, resource;

// Full application graph including dependencies
MATCH path = (app:Application {name: $app_name})-[:DEPLOYED_TO]->(r:Resource)-[:DEPENDS_ON*0..3]-(dep:Resource)
RETURN path;

// Application with source code
MATCH (app:Application {name: $app_name})-[:BUILT_FROM]->(repo:Repository)
RETURN app, repo;
```

### 4. Find Network Topology

```cypher
// Find all network connections for a resource
MATCH (r:Resource {id: $resource_id})-[conn:CONNECTS_TO]-(other:Resource)
RETURN r, conn, other;

// Find network path between two resources
MATCH path = shortestPath(
  (r1:Resource {id: $resource_id_1})-[:CONNECTS_TO*]-(r2:Resource {id: $resource_id_2})
)
RETURN path;

// Find all resources in a VNet
MATCH (vnet:Resource:VirtualNetwork {id: $vnet_id})-[:CONTAINS*]->(resource:Resource)
RETURN resource;
```

### 5. Find Resources by Tag

```cypher
// Resources with specific tag
MATCH (r:Resource)
WHERE r.tags[$tag_key] = $tag_value
RETURN r;

// Resources with any of several tags
MATCH (r:Resource)
WHERE any(key IN keys(r.tags) WHERE key IN $tag_keys)
RETURN r;
```

### 6. Find Resources in AKS Cluster

```cypher
// All namespaces in cluster
MATCH (aks:Resource:AKS {id: $aks_id})-[:CONTAINS]->(ns:Namespace)
RETURN ns;

// All pods in cluster
MATCH (aks:Resource:AKS {id: $aks_id})-[:CONTAINS]->(ns:Namespace)-[:CONTAINS]->(pod:Pod)
RETURN pod;

// Pods with their network connections
MATCH (aks:Resource:AKS {id: $aks_id})-[:CONTAINS*]->(pod:Pod)
OPTIONAL MATCH (pod)-[conn:CONNECTS_TO]-(target)
RETURN pod, conn, target;
```

### 7. Find Deployment History

```cypher
// Recent deployments for an application
MATCH (app:Application {name: $app_name})-[:DEPLOYED_TO]->(resource:Resource),
      (deployment:Deployment)-[:DEPLOYS_TO]->(resource)
WHERE deployment.deployed_at > datetime() - duration('P7D')
RETURN deployment
ORDER BY deployment.deployed_at DESC;

// Deployment with source commit
MATCH (deployment:Deployment)-[:ORIGINATED_FROM]->(repo:Repository)
WHERE deployment.id = $deployment_id
RETURN deployment, repo;
```

### 8. Find Security Posture

```cypher
// Resources without NSG
MATCH (r:Resource:Subnet)
WHERE NOT (r)-[:SECURED_BY]->(:Resource:NSG)
RETURN r;

// Resources with public IPs
MATCH (r:Resource)
WHERE size(r.public_ip_addresses) > 0
RETURN r;

// Resources using Key Vault
MATCH (r:Resource)-[:USES_SECRET_FROM]->(kv:Resource:KeyVault)
RETURN r, kv;
```

### 9. Find Impact Radius

```cypher
// Find all resources that depend on a specific resource (blast radius)
MATCH path = (dependent:Resource)-[:DEPENDS_ON*1..5]->(r:Resource {id: $resource_id})
RETURN DISTINCT dependent, length(path) as impact_distance
ORDER BY impact_distance;

// Find critical dependencies (high strength)
MATCH (r:Resource {id: $resource_id})-[dep:DEPENDS_ON]->(critical:Resource)
WHERE dep.strength > 0.7
RETURN critical, dep;
```

### 10. Find Cost Analysis

```cypher
// Total cost by environment
MATCH (r:Resource)
WHERE r.cost_per_day IS NOT NULL
RETURN r.environment, sum(r.cost_per_day) as daily_cost
ORDER BY daily_cost DESC;

// Cost by resource type
MATCH (r:Resource)
WHERE r.cost_per_day IS NOT NULL
RETURN r.resource_type, count(r) as count, sum(r.cost_per_day) as daily_cost
ORDER BY daily_cost DESC;

// Most expensive resources
MATCH (r:Resource)
WHERE r.cost_per_day IS NOT NULL
RETURN r.name, r.resource_type, r.cost_per_day
ORDER BY r.cost_per_day DESC
LIMIT 10;
```

### 11. Find Identity and Access Patterns

```cypher
// Find all resources a managed identity can access
MATCH (mi:ManagedIdentity {name: $identity_name})-[:ACCESSES]->(r:Resource)
RETURN mi.name, mi.identity_type, collect(r.name) as accessible_resources;

// Find which resources use a specific managed identity
MATCH (r:Resource)-[:AUTHENTICATES_WITH]->(mi:ManagedIdentity {name: $identity_name})
RETURN r.name, r.resource_type, mi.identity_type;

// Find all service principals with access to a resource
MATCH (sp:ServicePrincipal)-[:HAS_ROLE]->(r:Resource {name: $resource_name})
RETURN sp.display_name, sp.app_id, sp.enabled;

// Find identity chain: which resources can access what through identities
MATCH (r:Resource)-[:AUTHENTICATES_WITH]->(mi:ManagedIdentity)-[:ACCESSES]->(target:Resource)
RETURN r.name as source, mi.name as identity, collect(target.name) as can_access;

// Find service principals linked to app registrations
MATCH (sp:ServicePrincipal)-[:LINKED_TO_APP]->(ar:AppRegistration)
RETURN sp.display_name, ar.display_name, ar.required_resource_access;

// Find overprivileged identities (access to many resources)
MATCH (mi:ManagedIdentity)-[:ACCESSES]->(r:Resource)
WITH mi, count(r) as resource_count
WHERE resource_count > 5
RETURN mi.name, mi.identity_type, resource_count
ORDER BY resource_count DESC;
```

### 12. Find Kubernetes Resources

```cypher
// Find all pods in a namespace
MATCH (ns:Namespace {name: $namespace_name})<-[:IN_NAMESPACE]-(pod:Pod)
RETURN pod.name, pod.phase, pod.pod_ip, pod.node_name;

// Find all namespaces in a cluster
MATCH (ns:Namespace {cluster_id: $cluster_id})
RETURN ns.name, ns.labels, ns.resource_quota;

// Find pods with specific labels
MATCH (pod:Pod)
WHERE pod.labels.app = $app_name
RETURN pod.name, pod.namespace, pod.phase, pod.cluster_id;

// Find resource usage by namespace
MATCH (ns:Namespace)<-[:IN_NAMESPACE]-(pod:Pod)
RETURN ns.name, 
       count(pod) as pod_count,
       collect(pod.phase) as pod_phases;
```

---

## Example Graph Structure

Here's how a typical Azure environment would be modeled:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌──────────┬─────────┴─────────┬──────────┐
         │          │                   │          │
    [Application]─BUILT_FROM─>[Repository]    [Deployment]
         │                                       │
         │                              ORIGINATED_FROM
         │                                       │
    DEPLOYED_TO                          [Repository]
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Infrastructure Layer                         │
└─────────────────────────────────────────────────────────────────┘
         │
    [AKS Cluster] ◄───SECURED_BY─── [NSG]
         │                              ▲
         │                              │
    CONTAINS                    PART_OF_NETWORK
         │                              │
         ▼                              │
    [Namespace] ◄────────┐       [VirtualNetwork]
         │               │              │
    CONTAINS             │         CONTAINS
         │               │              │
         ▼               │              ▼
      [Pod]──────────────┘          [Subnet]
         │                              │
         │                         CONTAINS
    CONNECTS_TO                         │
         │                              ▼
         ▼                    [Application Gateway]
 [Load Balancer]                        │
         │                         ROUTES_TO
    ROUTES_TO                           │
         │                              │
         └──────────────┬───────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                               │
└─────────────────────────────────────────────────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         │                             │
         ▼                             ▼
   [SQL Database] ◄──────────────► [Storage Account]
         │            STORES_IN          │
         │                               │
    USES_SECRET_FROM              USES_SECRET_FROM
         │                               │
         └───────────┬───────────────────┘
                     ▼
                [Key Vault]
```

### Detailed Example: E-commerce Application

```cypher
// Application and Repository
CREATE (app:Application {
  id: 'app-ecommerce-prod',
  name: 'E-commerce Platform',
  owner_team: 'Platform Team',
  environment: 'prod',
  health_score: 95.5
})

CREATE (repo:Repository {
  id: 'repo-github-ecommerce',
  platform: 'github',
  url: 'https://github.com/company/ecommerce',
  name: 'ecommerce',
  default_branch: 'main'
})

CREATE (app)-[:BUILT_FROM {branch: 'main', commit_sha: 'abc123'}]->(repo)

// Infrastructure
CREATE (aks:Resource:AKS {
  id: '/subscriptions/.../providers/Microsoft.ContainerService/managedClusters/prod-aks',
  cloud_provider: 'azure',
  resource_type: 'aks',
  name: 'prod-aks',
  region: 'eastus',
  status: 'running',
  environment: 'prod',
  kubernetes_version: '1.27.3'
})

CREATE (ns:Namespace {
  id: 'prod-aks:ecommerce',
  name: 'ecommerce',
  cluster_id: aks.id
})

CREATE (pod:Pod {
  id: 'prod-aks:ecommerce:api-pod-xyz',
  name: 'api-pod-xyz',
  namespace: 'ecommerce',
  cluster_id: aks.id,
  phase: 'Running'
})

CREATE (sqldb:Resource:SQLDatabase {
  id: '/subscriptions/.../providers/Microsoft.Sql/servers/prod-sql/databases/ecommerce',
  cloud_provider: 'azure',
  resource_type: 'sql_database',
  name: 'ecommerce',
  region: 'eastus',
  status: 'running',
  environment: 'prod'
})

CREATE (storage:Resource:StorageAccount {
  id: '/subscriptions/.../providers/Microsoft.Storage/storageAccounts/prodecommstorage',
  cloud_provider: 'azure',
  resource_type: 'storage_account',
  name: 'prodecommstorage',
  region: 'eastus',
  status: 'running',
  environment: 'prod'
})

CREATE (kv:Resource:KeyVault {
  id: '/subscriptions/.../providers/Microsoft.KeyVault/vaults/prod-keyvault',
  cloud_provider: 'azure',
  resource_type: 'key_vault',
  name: 'prod-keyvault',
  region: 'eastus',
  status: 'running',
  environment: 'prod'
})

CREATE (appgw:Resource:ApplicationGateway {
  id: '/subscriptions/.../providers/Microsoft.Network/applicationGateways/prod-appgw',
  cloud_provider: 'azure',
  resource_type: 'application_gateway',
  name: 'prod-appgw',
  region: 'eastus',
  status: 'running',
  environment: 'prod'
})

CREATE (vnet:Resource:VirtualNetwork {
  id: '/subscriptions/.../providers/Microsoft.Network/virtualNetworks/prod-vnet',
  cloud_provider: 'azure',
  resource_type: 'vnet',
  name: 'prod-vnet',
  region: 'eastus',
  address_space: ['10.0.0.0/16']
})

CREATE (subnet:Resource:Subnet {
  id: '/subscriptions/.../providers/Microsoft.Network/virtualNetworks/prod-vnet/subnets/aks-subnet',
  cloud_provider: 'azure',
  resource_type: 'subnet',
  name: 'aks-subnet',
  region: 'eastus',
  address_prefix: '10.0.1.0/24'
})

// Relationships
CREATE (app)-[:DEPLOYED_TO {deployed_at: datetime(), version: 'v2.3.1'}]->(aks)
CREATE (aks)-[:CONTAINS]->(ns)
CREATE (ns)-[:CONTAINS]->(pod)
CREATE (pod)-[:CONNECTS_TO {protocol: 'sql', port: 1433}]->(sqldb)
CREATE (pod)-[:STORES_IN {storage_type: 'blob'}]->(storage)
CREATE (pod)-[:USES_SECRET_FROM {secret_names: ['db-connection-string']}]->(kv)
CREATE (sqldb)-[:USES_SECRET_FROM {secret_names: ['admin-password']}]->(kv)
CREATE (appgw)-[:ROUTES_TO {protocol: 'https', port: 443}]->(aks)
CREATE (aks)-[:DEPENDS_ON {category: 'network', strength: 1.0}]->(vnet)
CREATE (vnet)-[:CONTAINS]->(subnet)
CREATE (aks)-[:PART_OF_NETWORK]->(subnet)
CREATE (aks)-[:DEPENDS_ON {category: 'data', strength: 0.9}]->(sqldb)
CREATE (aks)-[:DEPENDS_ON {category: 'configuration', strength: 0.8}]->(kv)
```

---

## Schema Evolution Strategy

### Versioning Approach

1. **Node Version Property**: Add `schema_version: string` to track model version
2. **Backward Compatibility**: New properties should be optional
3. **Migration Scripts**: Maintain Cypher scripts for schema migrations
4. **Deprecation Policy**: Mark deprecated properties, remove after 2 versions

### Adding New Resource Types

When adding support for new Azure/AWS/GCP resources:

1. Create new sub-label under `:Resource` (e.g., `:Resource:CosmosDB`)
2. Document specific properties in this file
3. Update indexes if new query patterns emerge
4. Add example queries
5. Update mapper code to populate new properties

### Example Migration Script

```cypher
// Migration: Add health_status property to all resources
MATCH (r:Resource)
WHERE r.health_status IS NULL
SET r.health_status = 'unknown', r.schema_version = '1.1.0';
```

---

## Integration with Azure SDK

The schema is designed to map directly to Azure SDK responses:

### Azure SDK → Graph Model Mapping

**Azure Resource Manager (ARM) Response:**
```python
{
    "id": "/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
    "name": "vm1",
    "type": "Microsoft.Compute/virtualMachines",
    "location": "eastus",
    "tags": {"environment": "prod", "owner": "platform-team"},
    "properties": {
        "hardwareProfile": {"vmSize": "Standard_D2s_v3"},
        "storageProfile": {...},
        "osProfile": {...},
        "networkProfile": {...}
    }
}
```

**Mapped to Resource Node:**
```yaml
id: "/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1"
name: "vm1"
resource_type: "virtual_machine"
cloud_provider: "azure"
region: "eastus"
tags: {"environment": "prod", "owner": "platform-team"}
properties: {entire properties object as JSON}
vm_size: "Standard_D2s_v3"  # Extracted for convenience
```

### Relationship Discovery

Relationships are discovered through:

1. **Configuration Analysis**: Parse resource configurations for references
2. **Network Topology**: Analyze VNets, subnets, NSGs, route tables
3. **Dependency Tags**: Read dependency metadata from tags
4. **Application Insights**: Observe actual network traffic
5. **Kubernetes Metadata**: Parse K8s manifests, services, ingresses

---

## Performance Considerations

### Query Optimization Tips

1. **Use Indexes**: Always filter on indexed properties first
2. **Limit Traversal Depth**: Use `*1..5` instead of `*` for relationship patterns
3. **Filter Early**: Apply WHERE clauses as early as possible
4. **Use OPTIONAL MATCH**: For relationships that may not exist
5. **Batch Operations**: Use `UNWIND` for bulk operations

### Recommended Cache Strategy

- Cache resource lists by type/region (TTL: 5 minutes)
- Cache topology subgraphs (TTL: 10 minutes)
- Cache dependency analysis results (TTL: 15 minutes)
- Invalidate cache on resource updates

---

## Validation Rules

### Resource Validation

- `id` must be unique and non-null
- `cloud_provider` must be one of: "azure", "aws", "gcp"
- `resource_type` must be non-null
- `status` must be one of: "running", "stopped", "error", "degraded", "unknown"
- `last_seen` should be updated on every discovery run

### Relationship Validation

- Both source and target nodes must exist
- Circular dependencies should be flagged (not blocked, but reported)
- `DEPENDS_ON` relationships should have `strength` between 0 and 1
- `CONNECTS_TO` relationships should have valid protocol and port

---

## Summary

This data model provides:

✅ **Complete cloud resource representation** for Azure (extensible to AWS/GCP)  
✅ **Rich relationship modeling** to show how resources link together  
✅ **Support for Azure SDK data structures** with flexible properties  
✅ **Performance optimization** through strategic indexes  
✅ **Common query patterns** for typical topology questions  
✅ **Real-world examples** showing connected environments  
✅ **Evolution strategy** for schema changes  

The model is designed to support the full lifecycle of resource discovery, topology mapping, dependency analysis, and risk assessment that TopDeck aims to provide.
