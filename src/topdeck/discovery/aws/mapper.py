"""
AWS Resource Mapper.

Maps AWS SDK resource objects to TopDeck's normalized DiscoveredResource model.
"""

import re
from typing import Any

from ..models import CloudProvider, DiscoveredResource, ResourceStatus


class AWSResourceMapper:
    """
    Maps AWS resources to TopDeck's normalized resource model.
    """

    # Mapping from AWS resource types to TopDeck resource types
    RESOURCE_TYPE_MAP = {
        # Compute
        "AWS::EKS::Cluster": "eks",
        "AWS::EC2::Instance": "ec2_instance",
        "AWS::Lambda::Function": "lambda_function",
        "AWS::ECS::Cluster": "ecs_cluster",
        "AWS::ECS::Service": "ecs_service",
        # Databases
        "AWS::RDS::DBInstance": "rds_instance",
        "AWS::RDS::DBCluster": "rds_cluster",
        "AWS::DynamoDB::Table": "dynamodb_table",
        "AWS::ElastiCache::CacheCluster": "elasticache_cluster",
        # Storage
        "AWS::S3::Bucket": "s3_bucket",
        # Networking
        "AWS::EC2::VPC": "vpc",
        "AWS::EC2::Subnet": "subnet",
        "AWS::EC2::SecurityGroup": "security_group",
        "AWS::ElasticLoadBalancingV2::LoadBalancer": "load_balancer",
        "AWS::EC2::NatGateway": "nat_gateway",
        "AWS::EC2::InternetGateway": "internet_gateway",
        # Configuration & Secrets
        "AWS::SecretsManager::Secret": "secrets_manager_secret",
        "AWS::SSM::Parameter": "ssm_parameter",
    }

    @staticmethod
    def map_resource_type(aws_type: str) -> str:
        """
        Map AWS resource type to TopDeck resource type.

        Args:
            aws_type: AWS resource type (e.g., "AWS::EC2::Instance")

        Returns:
            Normalized resource type (e.g., "ec2_instance")
        """
        return AWSResourceMapper.RESOURCE_TYPE_MAP.get(aws_type, "unknown")

    @staticmethod
    def extract_account_id(arn: str) -> str | None:
        """
        Extract account ID from AWS ARN.

        Args:
            arn: AWS ARN (Amazon Resource Name)

        Returns:
            Account ID or None
        """
        # ARN format: arn:aws:service:region:account-id:resource
        match = re.search(r"arn:aws:[^:]*:[^:]*:(\d+):", arn)
        return match.group(1) if match else None

    @staticmethod
    def extract_region(arn: str) -> str | None:
        """
        Extract region from AWS ARN.

        Args:
            arn: AWS ARN (Amazon Resource Name)

        Returns:
            Region or None
        """
        # ARN format: arn:aws:service:region:account-id:resource
        match = re.search(r"arn:aws:[^:]*:([^:]+):", arn)
        return match.group(1) if match else None

    @staticmethod
    def map_state_to_status(state: str | None) -> ResourceStatus:
        """
        Map AWS resource state to TopDeck resource status.

        Args:
            state: AWS resource state (e.g., "running", "available", "stopped")

        Returns:
            Normalized resource status
        """
        if not state:
            return ResourceStatus.UNKNOWN

        state_lower = state.lower()

        if state_lower in ("running", "available", "active", "in-service"):
            return ResourceStatus.RUNNING
        elif state_lower in ("stopped", "stopping", "shutting-down"):
            return ResourceStatus.STOPPED
        elif state_lower in ("failed", "error", "unhealthy"):
            return ResourceStatus.ERROR
        elif state_lower in ("pending", "creating", "updating", "deleting", "degraded"):
            return ResourceStatus.DEGRADED
        else:
            return ResourceStatus.UNKNOWN

    @staticmethod
    def extract_environment_from_tags(tags: list | None) -> str | None:
        """
        Extract environment from AWS resource tags.

        AWS tags are typically a list of dicts with 'Key' and 'Value'.
        Looks for common tag keys: environment, env, Environment, Env

        Args:
            tags: AWS resource tags list

        Returns:
            Environment name (e.g., "prod", "staging", "dev") or None
        """
        if not tags:
            return None

        # Convert list of {Key, Value} to dict
        tags_dict = {}
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, dict) and "Key" in tag and "Value" in tag:
                    tags_dict[tag["Key"]] = tag["Value"]
        elif isinstance(tags, dict):
            tags_dict = tags

        # Check common environment tag keys
        for key in ("environment", "env", "Environment", "Env", "ENVIRONMENT"):
            if key in tags_dict:
                return tags_dict[key].lower()

        return None

    @staticmethod
    def normalize_tags(tags: list | None) -> dict[str, str]:
        """
        Normalize AWS tags to a simple dict format for Neo4j.

        Args:
            tags: AWS resource tags (list of {Key, Value} dicts)

        Returns:
            Normalized tags dictionary
        """
        if not tags:
            return {}

        tags_dict = {}
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, dict) and "Key" in tag and "Value" in tag:
                    tags_dict[tag["Key"]] = tag["Value"]
        elif isinstance(tags, dict):
            return tags

        return tags_dict

    @staticmethod
    def map_aws_resource(
        arn: str,
        resource_name: str,
        resource_type: str,
        region: str,
        tags: list | None = None,
        properties: dict[str, Any] | None = None,
        state: str | None = None,
    ) -> DiscoveredResource:
        """
        Map an AWS resource to a DiscoveredResource.

        Args:
            arn: AWS ARN (Amazon Resource Name)
            resource_name: Resource name
            resource_type: AWS resource type
            region: AWS region
            tags: AWS resource tags (list format)
            properties: AWS-specific properties
            state: Resource state

        Returns:
            DiscoveredResource instance formatted for Neo4j
        """
        normalized_tags = AWSResourceMapper.normalize_tags(tags)

        return DiscoveredResource(
            id=arn,
            name=resource_name,
            resource_type=AWSResourceMapper.map_resource_type(resource_type),
            cloud_provider=CloudProvider.AWS,
            region=region,
            resource_group=None,  # AWS doesn't have resource groups
            subscription_id=AWSResourceMapper.extract_account_id(arn),
            status=AWSResourceMapper.map_state_to_status(state),
            environment=AWSResourceMapper.extract_environment_from_tags(tags),
            tags=normalized_tags,
            properties=properties or {},
        )
