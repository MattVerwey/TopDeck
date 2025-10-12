// TopDeck Neo4j Database Schema
// This file contains all the constraints and indexes needed for the TopDeck graph database

// ============================================================================
// CONSTRAINTS - Enforce uniqueness and data integrity
// ============================================================================

// Unique ID constraints
CREATE CONSTRAINT resource_id_unique IF NOT EXISTS
FOR (r:Resource) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT application_id_unique IF NOT EXISTS
FOR (a:Application) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT repository_id_unique IF NOT EXISTS
FOR (r:Repository) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT deployment_id_unique IF NOT EXISTS
FOR (d:Deployment) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT namespace_id_unique IF NOT EXISTS
FOR (n:Namespace) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT pod_id_unique IF NOT EXISTS
FOR (p:Pod) REQUIRE p.id IS UNIQUE;

// Existence constraints - Ensure critical properties exist
CREATE CONSTRAINT resource_type_exists IF NOT EXISTS
FOR (r:Resource) REQUIRE r.resource_type IS NOT NULL;

CREATE CONSTRAINT resource_cloud_exists IF NOT EXISTS
FOR (r:Resource) REQUIRE r.cloud_provider IS NOT NULL;

CREATE CONSTRAINT application_name_exists IF NOT EXISTS
FOR (a:Application) REQUIRE a.name IS NOT NULL;

// ============================================================================
// INDEXES - Optimize query performance
// ============================================================================

// Resource indexes
CREATE INDEX resource_id IF NOT EXISTS
FOR (r:Resource) ON (r.id);

CREATE INDEX resource_type IF NOT EXISTS
FOR (r:Resource) ON (r.resource_type);

CREATE INDEX resource_cloud_provider IF NOT EXISTS
FOR (r:Resource) ON (r.cloud_provider);

CREATE INDEX resource_name IF NOT EXISTS
FOR (r:Resource) ON (r.name);

CREATE INDEX resource_region IF NOT EXISTS
FOR (r:Resource) ON (r.region);

CREATE INDEX resource_status IF NOT EXISTS
FOR (r:Resource) ON (r.status);

CREATE INDEX resource_environment IF NOT EXISTS
FOR (r:Resource) ON (r.environment);

CREATE INDEX resource_subscription IF NOT EXISTS
FOR (r:Resource) ON (r.subscription_id);

CREATE INDEX resource_resource_group IF NOT EXISTS
FOR (r:Resource) ON (r.resource_group);

CREATE INDEX resource_last_seen IF NOT EXISTS
FOR (r:Resource) ON (r.last_seen);

// Application indexes
CREATE INDEX application_id IF NOT EXISTS
FOR (a:Application) ON (a.id);

CREATE INDEX application_name IF NOT EXISTS
FOR (a:Application) ON (a.name);

CREATE INDEX application_owner IF NOT EXISTS
FOR (a:Application) ON (a.owner_team);

CREATE INDEX application_environment IF NOT EXISTS
FOR (a:Application) ON (a.environment);

// Repository indexes
CREATE INDEX repository_id IF NOT EXISTS
FOR (r:Repository) ON (r.id);

CREATE INDEX repository_url IF NOT EXISTS
FOR (r:Repository) ON (r.url);

CREATE INDEX repository_name IF NOT EXISTS
FOR (r:Repository) ON (r.name);

CREATE INDEX repository_platform IF NOT EXISTS
FOR (r:Repository) ON (r.platform);

// Deployment indexes
CREATE INDEX deployment_id IF NOT EXISTS
FOR (d:Deployment) ON (d.id);

CREATE INDEX deployment_status IF NOT EXISTS
FOR (d:Deployment) ON (d.status);

CREATE INDEX deployment_date IF NOT EXISTS
FOR (d:Deployment) ON (d.deployed_at);

CREATE INDEX deployment_pipeline IF NOT EXISTS
FOR (d:Deployment) ON (d.pipeline_id);

// Namespace indexes
CREATE INDEX namespace_id IF NOT EXISTS
FOR (n:Namespace) ON (n.id);

CREATE INDEX namespace_name IF NOT EXISTS
FOR (n:Namespace) ON (n.name);

CREATE INDEX namespace_cluster IF NOT EXISTS
FOR (n:Namespace) ON (n.cluster_id);

// Pod indexes
CREATE INDEX pod_id IF NOT EXISTS
FOR (p:Pod) ON (p.id);

CREATE INDEX pod_name IF NOT EXISTS
FOR (p:Pod) ON (p.name);

CREATE INDEX pod_namespace IF NOT EXISTS
FOR (p:Pod) ON (p.namespace);

CREATE INDEX pod_cluster IF NOT EXISTS
FOR (p:Pod) ON (p.cluster_id);

CREATE INDEX pod_phase IF NOT EXISTS
FOR (p:Pod) ON (p.phase);

// Composite indexes for common query patterns
CREATE INDEX resource_type_provider IF NOT EXISTS
FOR (r:Resource) ON (r.resource_type, r.cloud_provider);

CREATE INDEX resource_region_type IF NOT EXISTS
FOR (r:Resource) ON (r.region, r.resource_type);

CREATE INDEX resource_env_type IF NOT EXISTS
FOR (r:Resource) ON (r.environment, r.resource_type);

CREATE INDEX application_env_owner IF NOT EXISTS
FOR (a:Application) ON (a.environment, a.owner_team);

// ============================================================================
// SAMPLE QUERIES - Common operations
// ============================================================================

// Find all resources in a specific environment
// MATCH (r:Resource {environment: 'prod'})
// RETURN r
// ORDER BY r.resource_type, r.name;

// Find all dependencies of a resource
// MATCH path = (r:Resource {id: $resource_id})-[:DEPENDS_ON*1..5]->(dep:Resource)
// RETURN dep, length(path) as depth
// ORDER BY depth;

// Find application topology
// MATCH path = (app:Application {name: $app_name})-[:DEPLOYED_TO]->(r:Resource)-[:DEPENDS_ON*0..3]-(dep:Resource)
// RETURN path;

// Find network connections
// MATCH (r:Resource {id: $resource_id})-[conn:CONNECTS_TO]-(other:Resource)
// RETURN r, conn, other;

// Find resources without security groups
// MATCH (r:Resource:Subnet)
// WHERE NOT (r)-[:SECURED_BY]->(:Resource:NSG)
// RETURN r;

// Calculate blast radius
// MATCH path = (dependent:Resource)-[:DEPENDS_ON*1..5]->(r:Resource {id: $resource_id})
// RETURN DISTINCT dependent, length(path) as impact_distance
// ORDER BY impact_distance;

// Cost analysis by environment
// MATCH (r:Resource)
// WHERE r.cost_per_day IS NOT NULL
// RETURN r.environment, sum(r.cost_per_day) as daily_cost
// ORDER BY daily_cost DESC;

// ============================================================================
// SCHEMA VALIDATION
// ============================================================================

// You can run this query to verify the schema setup:
// CALL db.indexes() YIELD name, labelsOrTypes, properties, type, state
// RETURN name, labelsOrTypes, properties, type, state
// ORDER BY name;

// To verify constraints:
// SHOW CONSTRAINTS;
