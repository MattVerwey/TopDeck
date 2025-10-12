# Issue #8: Implement AWS Resource Discovery

**Labels**: `enhancement`, `cloud: aws`, `priority: high`, `phase-2`

## Description

Implement the AWS resource discovery module that can scan AWS accounts and discover all relevant resources for topology mapping. This implementation should leverage Terraform for infrastructure management and follow the patterns established in Azure discovery.

## Scope

### Resources to Discover

**Compute Resources**:
- Amazon Elastic Kubernetes Service (EKS) clusters
  - Node groups
  - Pods and deployments (via kubectl)
  - Ingress controllers
- Elastic Compute Cloud (EC2) instances
  - Auto Scaling Groups
  - Launch Templates
- AWS Lambda functions
- Elastic Container Service (ECS)
  - Tasks and services
  - Fargate

**Networking**:
- Virtual Private Clouds (VPCs)
- Subnets
- Security Groups
- Elastic Load Balancers (ALB, NLB, CLB)
- API Gateways
- NAT Gateways
- Internet Gateways
- VPC Peering connections

**Data Services**:
- Amazon RDS (PostgreSQL, MySQL, SQL Server)
- DynamoDB tables
- Amazon S3 buckets
- ElastiCache (Redis, Memcached)
- Amazon Aurora

**Configuration**:
- AWS Secrets Manager
- Systems Manager Parameter Store

## Requirements

### Authentication
- Support IAM Role authentication
- Support Access Key/Secret Key
- Support AWS CLI profile
- Support cross-account role assumption

### Discovery Strategy
- Parallel discovery across multiple regions
- Support for multi-account discovery via Organizations
- Incremental discovery (delta sync)
- Resource tagging awareness

### Terraform Integration
- Use Terraform for infrastructure deployment automation
- Generate Terraform configurations from discovered resources
- Maintain state consistency
- Support import of existing resources

## Technical Design

### Module Structure
```
src/discovery/aws/
├── __init__.py
├── client.py           # AWS client wrapper (boto3)
├── authenticator.py    # Authentication logic
├── discoverer.py       # Main discovery orchestrator
├── resources/
│   ├── compute.py      # EKS, EC2, Lambda discovery
│   ├── networking.py   # VPC, SG, LB discovery
│   ├── data.py         # RDS, DynamoDB, S3 discovery
│   └── config.py       # Secrets Manager discovery
├── mapper.py           # Map AWS resources to graph models
├── terraform/          # Terraform integration
│   ├── generator.py    # Generate TF configs
│   └── importer.py     # Import existing resources
└── config.py           # Configuration management
```

### Key Classes

```python
class AWSDiscoverer:
    def __init__(self, credentials, region='us-east-1'):
        """Initialize AWS discoverer with credentials"""
        
    def discover_all(self, regions: List[str] = None) -> List[Resource]:
        """Discover all resources across specified regions"""
        
    def discover_resource_type(self, resource_type: str, region: str) -> List[Resource]:
        """Discover specific resource type in a region"""
        
    def get_resource_relationships(self, resource_id: str) -> List[Relationship]:
        """Get relationships for a specific resource"""
        
    def generate_terraform(self, resources: List[Resource]) -> str:
        """Generate Terraform configuration for resources"""
```

### Configuration

```yaml
# config/aws.yaml
aws:
  authentication:
    method: iam_role  # or access_key, profile
    profile: default
    access_key_id: ${AWS_ACCESS_KEY_ID}
    secret_access_key: ${AWS_SECRET_ACCESS_KEY}
    assume_role_arn: ${AWS_ASSUME_ROLE_ARN}
  
  discovery:
    accounts:
      - account_id: "123456789012"
        regions:
          - us-east-1
          - us-west-2
          - eu-west-1
    
    resource_types:
      - eks
      - ec2
      - lambda
      - rds
      - dynamodb
      - s3
      - vpc
      - alb
    
    excluded_tags:
      - Environment: test
      - Temporary: true
    
    scan_interval: 3600  # seconds
    parallel_workers: 5
    
  terraform:
    enabled: true
    output_path: infrastructure/terraform/aws/
    state_backend: s3
    state_bucket: topdeck-terraform-state
```

## Tasks

- [ ] Set up AWS SDK (boto3) client
- [ ] Implement authentication module with multi-method support
- [ ] Implement compute resource discovery (EKS, EC2, Lambda, ECS)
- [ ] Implement networking resource discovery (VPC, SG, ALB, API Gateway)
- [ ] Implement data service discovery (RDS, DynamoDB, S3, ElastiCache)
- [ ] Implement configuration discovery (Secrets Manager, Parameter Store)
- [ ] Build Terraform integration layer
  - [ ] Generate Terraform configurations from discovered resources
  - [ ] Implement Terraform import functionality
  - [ ] State management integration
- [ ] Create resource-to-graph mapper
- [ ] Implement multi-region discovery
- [ ] Implement multi-account discovery via AWS Organizations
- [ ] Add error handling and retry logic with exponential backoff
- [ ] Write unit tests for all modules
- [ ] Write integration tests
- [ ] Create documentation and examples

## Success Criteria

- [ ] Successfully discovers all major AWS resource types
- [ ] Accurately identifies relationships between resources
- [ ] Generates valid Terraform configurations
- [ ] Can import existing resources into Terraform state
- [ ] Handles multi-region discovery efficiently
- [ ] Supports cross-account discovery
- [ ] Stores all data in Neo4j graph database
- [ ] Provides consistent interface with Azure discovery module
- [ ] Has >80% test coverage
- [ ] Documentation is complete with examples

## Security Considerations

- Use read-only IAM policies for discovery
- Never store credentials in code
- Support IAM roles over access keys when possible
- Mask sensitive data in logs
- Encrypt credentials at rest
- Use least privilege principle for IAM permissions

## Dependencies

- Issue #1: Technology Stack Decision (must complete first)
- Issue #2: Core Data Models (must complete first)
- Issue #3: Azure Resource Discovery (reference implementation)
- AWS SDK for Python (boto3)
- Terraform CLI

## Timeline

**Estimated Duration**: 2-3 weeks

**Phase 2 Priority**: High

## Related Issues

- Issue #2: Core Data Models
- Issue #3: Azure Resource Discovery
- Issue #9: GCP Resource Discovery

## Notes

- Leverage Terraform's existing AWS provider for resource definitions
- Follow the same patterns as Azure discovery for consistency
- Consider using AWS Config for resource inventory as an alternative/supplement
- AWS Organizations integration allows discovery across multiple accounts
- CloudFormation stacks should also be discovered for deployed infrastructure tracking
