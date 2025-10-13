# AWS Resource Discovery

Discover and map AWS resources to TopDeck's unified topology graph.

## Features

- Discover compute resources (EKS, EC2, Lambda, ECS)
- Discover networking resources (VPC, Security Groups, Load Balancers)
- Discover data services (RDS, DynamoDB, S3, ElastiCache)
- Discover configuration resources (Secrets Manager, Parameter Store)
- Map AWS resources to Neo4j-compatible format
- Extract metadata from AWS tags
- Support for multiple regions and accounts

## Components

### AWSResourceMapper (`mapper.py`)

Maps AWS resources to TopDeck's normalized model.

**Supported Resource Types**:
- ✅ EKS Clusters (`AWS::EKS::Cluster`)
- ✅ EC2 Instances (`AWS::EC2::Instance`)
- ✅ Lambda Functions (`AWS::Lambda::Function`)
- ✅ ECS Clusters/Services (`AWS::ECS::*`)
- ✅ RDS Instances/Clusters (`AWS::RDS::*`)
- ✅ DynamoDB Tables (`AWS::DynamoDB::Table`)
- ✅ S3 Buckets (`AWS::S3::Bucket`)
- ✅ ElastiCache Clusters (`AWS::ElastiCache::CacheCluster`)
- ✅ VPCs (`AWS::EC2::VPC`)
- ✅ Subnets (`AWS::EC2::Subnet`)
- ✅ Security Groups (`AWS::EC2::SecurityGroup`)
- ✅ Load Balancers (`AWS::ElasticLoadBalancingV2::LoadBalancer`)
- ✅ Secrets Manager (`AWS::SecretsManager::Secret`)
- ✅ Parameter Store (`AWS::SSM::Parameter`)

**Mapping Features**:
- ARN parsing (account, region extraction)
- State → status mapping
- Environment detection from tags
- Tag normalization (list to dict)
- Neo4j-compatible property formatting

### AWSDiscoverer (`discoverer.py`)

Main orchestrator for AWS resource discovery.

**Features**:
- Multi-region discovery
- Multi-account support (via role assumption)
- Async/parallel resource scanning
- Credential management (IAM roles, access keys)
- Resource filtering by tags

## Data Models

### DiscoveredResource

Represents a discovered AWS resource in normalized format.

**Properties**:
- `id`: AWS ARN (Amazon Resource Name)
- `name`: Resource name
- `resource_type`: TopDeck normalized type
- `cloud_provider`: "aws"
- `region`: AWS region
- `subscription_id`: AWS account ID
- `status`: Resource status (running, stopped, error, etc.)
- `environment`: Environment tag (prod, staging, dev)
- `tags`: Resource tags (normalized to dict)
- `properties`: AWS-specific properties (as JSON)
- `discovered_at`: Discovery timestamp
- `last_seen`: Last seen timestamp

## Usage

```python
from topdeck.discovery.aws import AWSDiscoverer, AWSResourceMapper

# Initialize discoverer
discoverer = AWSDiscoverer(
    access_key_id="YOUR_ACCESS_KEY",
    secret_access_key="YOUR_SECRET_KEY",
    region="us-east-1"
)

# Discover all resources
result = await discoverer.discover_all_resources(
    regions=["us-east-1", "us-west-2"],
    resource_types=["eks", "ec2_instance", "rds_instance"]
)

# Access discovered resources
for resource in result.resources:
    print(f"Found: {resource.name} ({resource.resource_type})")
```

### Mapping a Single Resource

```python
from topdeck.discovery.aws import AWSResourceMapper

# Map an EC2 instance
resource = AWSResourceMapper.map_aws_resource(
    arn="arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
    resource_name="web-server-01",
    resource_type="AWS::EC2::Instance",
    region="us-east-1",
    tags=[
        {"Key": "Environment", "Value": "production"},
        {"Key": "Application", "Value": "web"}
    ],
    properties={"InstanceType": "t3.large"},
    state="running"
)

# Convert to Neo4j properties
neo4j_props = resource.to_neo4j_properties()
```

### Store in Neo4j

```python
from topdeck.storage.neo4j_client import Neo4jClient

client = Neo4jClient("bolt://localhost:7687", "neo4j", "password")
client.connect()

# Store resources
for resource in result.resources:
    client.upsert_resource(resource.to_neo4j_properties())
```

## Neo4j Format

Resources are formatted for Neo4j storage with proper data types:

```python
{
    'id': 'arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0',
    'name': 'web-server-01',
    'resource_type': 'ec2_instance',
    'cloud_provider': 'aws',
    'region': 'us-east-1',
    'subscription_id': '123456789012',  # AWS account ID
    'status': 'running',
    'environment': 'production',
    'tags': {'Environment': 'production', 'Application': 'web'},  # Dict format
    'properties': '{"InstanceType": "t3.large"}',  # JSON string
    'discovered_at': '2024-01-01T12:00:00',  # ISO format
    'last_seen': '2024-01-01T12:00:00'
}
```

## Configuration

AWS configuration is managed through the main TopDeck settings:

```python
# Environment variables
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

Or programmatically:

```python
from topdeck.common.config import Settings

settings = Settings(
    aws_access_key_id="your_access_key",
    aws_secret_access_key="your_secret_key",
    aws_region="us-east-1"
)
```
