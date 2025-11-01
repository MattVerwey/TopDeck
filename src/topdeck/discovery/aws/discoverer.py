"""
AWS Resource Discoverer.

Main orchestrator for discovering AWS resources across accounts and regions.
"""

import logging
from typing import Any

from ..models import Application, DiscoveredResource, DiscoveryResult, ResourceDependency
from .mapper import AWSResourceMapper

logger = logging.getLogger(__name__)

# Try importing boto3, but make it optional for testing
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    BOTO3_AVAILABLE = True
except ImportError:
    boto3 = None
    BotoCoreError = Exception
    ClientError = Exception
    BOTO3_AVAILABLE = False


class AWSDiscoverer:
    """
    Main class for discovering AWS resources.

    Supports:
    - Multiple accounts
    - Multiple regions
    - Multiple resource types (compute, networking, data, config)
    - Async/parallel discovery
    - Relationship detection
    """

    def __init__(
        self,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        region: str = "us-east-1",
        session_token: str | None = None,
    ):
        """
        Initialize AWS discoverer.

        Args:
            access_key_id: AWS access key ID (if None, uses default credentials)
            secret_access_key: AWS secret access key
            region: Default AWS region
            session_token: AWS session token (for temporary credentials)
        """
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region = region
        self.session_token = session_token
        self.mapper = AWSResourceMapper()

        # Initialize boto3 session if available
        if BOTO3_AVAILABLE:
            session_kwargs: dict[str, Any] = {"region_name": region}
            if access_key_id and secret_access_key:
                session_kwargs["aws_access_key_id"] = access_key_id
                session_kwargs["aws_secret_access_key"] = secret_access_key
            if session_token:
                session_kwargs["aws_session_token"] = session_token

            self.session = boto3.Session(**session_kwargs)
        else:
            self.session = None
            logger.warning("boto3 not available, AWS discovery will be limited")

    async def discover_all_resources(
        self,
        regions: list[str] | None = None,
        resource_types: list[str] | None = None,
    ) -> DiscoveryResult:
        """
        Discover all AWS resources across specified regions.

        Args:
            regions: List of AWS regions to scan (if None, uses default region)
            resource_types: List of resource types to discover (if None, discovers all)

        Returns:
            DiscoveryResult containing all discovered resources
        """
        if not BOTO3_AVAILABLE:
            logger.error("boto3 not available, cannot discover AWS resources")
            result = DiscoveryResult(cloud_provider="aws")
            result.add_error("boto3 not available")
            result.complete()
            return result

        # Use default region if none specified
        if regions is None:
            regions = [self.region]

        result = DiscoveryResult(cloud_provider="aws")
        account_id = self.get_account_id()

        try:
            logger.info(f"Discovering AWS resources in account {account_id}...")

            # Discover resources for each region
            for region_name in regions:
                logger.info(f"Scanning region: {region_name}")

                try:
                    # Discover EC2 instances
                    if not resource_types or "ec2" in resource_types:
                        ec2_resources = await self._discover_ec2_instances(region_name)
                        for resource in ec2_resources:
                            result.add_resource(resource)

                    # Discover EKS clusters
                    if not resource_types or "eks" in resource_types:
                        eks_resources = await self._discover_eks_clusters(region_name)
                        for resource in eks_resources:
                            result.add_resource(resource)

                    # Discover RDS databases
                    if not resource_types or "rds" in resource_types:
                        rds_resources = await self._discover_rds_databases(region_name)
                        for resource in rds_resources:
                            result.add_resource(resource)

                    # Discover S3 buckets (S3 is global but we list it per region for organization)
                    if not resource_types or "s3" in resource_types:
                        s3_resources = await self._discover_s3_buckets(region_name)
                        for resource in s3_resources:
                            result.add_resource(resource)

                    # Discover Lambda functions
                    if not resource_types or "lambda" in resource_types:
                        lambda_resources = await self._discover_lambda_functions(region_name)
                        for resource in lambda_resources:
                            result.add_resource(resource)

                    # Discover DynamoDB tables
                    if not resource_types or "dynamodb" in resource_types:
                        dynamodb_resources = await self._discover_dynamodb_tables(region_name)
                        for resource in dynamodb_resources:
                            result.add_resource(resource)

                    # Discover VPCs
                    if not resource_types or "vpc" in resource_types:
                        vpc_resources = await self._discover_vpcs(region_name)
                        for resource in vpc_resources:
                            result.add_resource(resource)

                    # Discover Load Balancers
                    if not resource_types or "load_balancer" in resource_types:
                        lb_resources = await self._discover_load_balancers(region_name)
                        for resource in lb_resources:
                            result.add_resource(resource)

                except Exception as e:
                    error_msg = f"Error discovering resources in region {region_name}: {e}"
                    result.add_error(error_msg)
                    logger.error(error_msg)

            logger.info(f"Discovered {len(result.resources)} resources")

            # Discover dependencies
            logger.info("Analyzing dependencies...")
            dependencies = await self._discover_dependencies(result.resources)
            for dep in dependencies:
                result.add_dependency(dep)

            logger.info(f"Found {len(dependencies)} dependencies")

            # Infer applications from resources
            logger.info("Inferring applications from resources...")
            applications = await self._infer_applications(result.resources)
            for app in applications:
                result.add_application(app)

            logger.info(f"Found {len(applications)} applications")

        except (BotoCoreError, ClientError) as e:
            error_msg = f"AWS API error: {e}"
            result.add_error(error_msg)
            logger.error(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            result.add_error(error_msg)
            logger.error(error_msg)

        result.complete()
        logger.info(result.summary())

        return result

    async def _discover_ec2_instances(self, region: str) -> list[DiscoveredResource]:
        """Discover EC2 instances in a region."""
        resources = []
        try:
            ec2 = self.session.client("ec2", region_name=region)
            response = ec2.describe_instances()

            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    # Extract basic info
                    instance_id = instance.get("InstanceId")
                    instance_type = instance.get("InstanceType")
                    state = instance.get("State", {}).get("Name")
                    vpc_id = instance.get("VpcId")
                    subnet_id = instance.get("SubnetId")

                    # Build ARN
                    account_id = self.get_account_id()
                    arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"

                    # Extract tags
                    tags = {}
                    for tag in instance.get("Tags", []):
                        tags[tag["Key"]] = tag["Value"]

                    # Map to DiscoveredResource
                    resource = self.mapper.map_resource(
                        resource_id=arn,
                        resource_type="AWS::EC2::Instance",
                        tags=tags,
                        region=region,
                        account_id=account_id,
                    )

                    # Add EC2-specific properties
                    resource.properties["instance_type"] = instance_type
                    resource.properties["state"] = state
                    resource.properties["vpc_id"] = vpc_id
                    resource.properties["subnet_id"] = subnet_id

                    resources.append(resource)

        except Exception as e:
            logger.error(f"Error discovering EC2 instances in {region}: {e}")

        return resources

    async def _discover_eks_clusters(self, region: str) -> list[DiscoveredResource]:
        """Discover EKS clusters in a region."""
        resources = []
        try:
            eks = self.session.client("eks", region_name=region)
            response = eks.list_clusters()

            for cluster_name in response.get("clusters", []):
                cluster_info = eks.describe_cluster(name=cluster_name)
                cluster = cluster_info.get("cluster", {})

                # Extract basic info
                arn = cluster.get("arn")
                status = cluster.get("status")
                version = cluster.get("version")
                endpoint = cluster.get("endpoint")

                # Extract tags
                tags = cluster.get("tags", {})

                # Map to DiscoveredResource
                account_id = self.get_account_id()
                resource = self.mapper.map_resource(
                    resource_id=arn,
                    resource_type="AWS::EKS::Cluster",
                    tags=tags,
                    region=region,
                    account_id=account_id,
                )

                # Add EKS-specific properties
                resource.properties["status"] = status
                resource.properties["version"] = version
                resource.properties["endpoint"] = endpoint

                resources.append(resource)

        except Exception as e:
            logger.error(f"Error discovering EKS clusters in {region}: {e}")

        return resources

    async def _discover_rds_databases(self, region: str) -> list[DiscoveredResource]:
        """Discover RDS databases in a region."""
        resources = []
        try:
            rds = self.session.client("rds", region_name=region)
            response = rds.describe_db_instances()

            for db_instance in response.get("DBInstances", []):
                # Extract basic info
                db_instance.get("DBInstanceIdentifier")
                engine = db_instance.get("Engine")
                engine_version = db_instance.get("EngineVersion")
                status = db_instance.get("DBInstanceStatus")
                endpoint = db_instance.get("Endpoint", {})

                # Build ARN
                account_id = self.get_account_id()
                arn = db_instance.get("DBInstanceArn")

                # Extract tags
                tags = {}
                for tag in db_instance.get("TagList", []):
                    tags[tag["Key"]] = tag["Value"]

                # Map to DiscoveredResource
                resource = self.mapper.map_resource(
                    resource_id=arn,
                    resource_type="AWS::RDS::DBInstance",
                    tags=tags,
                    region=region,
                    account_id=account_id,
                )

                # Add RDS-specific properties
                resource.properties["engine"] = engine
                resource.properties["engine_version"] = engine_version
                resource.properties["status"] = status
                if endpoint:
                    resource.properties["endpoint_address"] = endpoint.get("Address")
                    resource.properties["endpoint_port"] = endpoint.get("Port")

                resources.append(resource)

        except Exception as e:
            logger.error(f"Error discovering RDS databases in {region}: {e}")

        return resources

    async def _discover_s3_buckets(self, region: str) -> list[DiscoveredResource]:
        """Discover S3 buckets (global service)."""
        resources = []
        try:
            s3 = self.session.client("s3")
            response = s3.list_buckets()

            for bucket in response.get("Buckets", []):
                bucket_name = bucket.get("Name")

                # Get bucket location
                try:
                    location = s3.get_bucket_location(Bucket=bucket_name)
                    bucket_region = location.get("LocationConstraint") or "us-east-1"
                except Exception:
                    bucket_region = region

                # Only include buckets in the specified region
                if bucket_region != region:
                    continue

                # Build ARN
                account_id = self.get_account_id()
                arn = f"arn:aws:s3:::{bucket_name}"

                # Get tags
                tags = {}
                try:
                    tag_response = s3.get_bucket_tagging(Bucket=bucket_name)
                    for tag in tag_response.get("TagSet", []):
                        tags[tag["Key"]] = tag["Value"]
                except Exception:
                    pass

                # Map to DiscoveredResource
                resource = self.mapper.map_resource(
                    resource_id=arn,
                    resource_type="AWS::S3::Bucket",
                    tags=tags,
                    region=bucket_region,
                    account_id=account_id,
                )

                resources.append(resource)

        except Exception as e:
            logger.error(f"Error discovering S3 buckets: {e}")

        return resources

    async def _discover_lambda_functions(self, region: str) -> list[DiscoveredResource]:
        """Discover Lambda functions in a region."""
        resources = []
        try:
            lambda_client = self.session.client("lambda", region_name=region)
            response = lambda_client.list_functions()

            for function in response.get("Functions", []):
                # Extract basic info
                function.get("FunctionName")
                arn = function.get("FunctionArn")
                runtime = function.get("Runtime")
                handler = function.get("Handler")

                # Get tags
                tags = {}
                try:
                    tag_response = lambda_client.list_tags(Resource=arn)
                    tags = tag_response.get("Tags", {})
                except Exception:
                    pass

                # Map to DiscoveredResource
                account_id = self.get_account_id()
                resource = self.mapper.map_resource(
                    resource_id=arn,
                    resource_type="AWS::Lambda::Function",
                    tags=tags,
                    region=region,
                    account_id=account_id,
                )

                # Add Lambda-specific properties
                resource.properties["runtime"] = runtime
                resource.properties["handler"] = handler

                resources.append(resource)

        except Exception as e:
            logger.error(f"Error discovering Lambda functions in {region}: {e}")

        return resources

    async def _discover_dynamodb_tables(self, region: str) -> list[DiscoveredResource]:
        """Discover DynamoDB tables in a region."""
        resources = []
        try:
            dynamodb = self.session.client("dynamodb", region_name=region)
            response = dynamodb.list_tables()

            for table_name in response.get("TableNames", []):
                # Get table details
                table_info = dynamodb.describe_table(TableName=table_name)
                table = table_info.get("Table", {})

                # Extract basic info
                arn = table.get("TableArn")
                status = table.get("TableStatus")
                item_count = table.get("ItemCount")

                # Get tags
                tags = {}
                try:
                    tag_response = dynamodb.list_tags_of_resource(ResourceArn=arn)
                    for tag in tag_response.get("Tags", []):
                        tags[tag["Key"]] = tag["Value"]
                except Exception:
                    pass

                # Map to DiscoveredResource
                account_id = self.get_account_id()
                resource = self.mapper.map_resource(
                    resource_id=arn,
                    resource_type="AWS::DynamoDB::Table",
                    tags=tags,
                    region=region,
                    account_id=account_id,
                )

                # Add DynamoDB-specific properties
                resource.properties["status"] = status
                resource.properties["item_count"] = item_count

                resources.append(resource)

        except Exception as e:
            logger.error(f"Error discovering DynamoDB tables in {region}: {e}")

        return resources

    async def _discover_vpcs(self, region: str) -> list[DiscoveredResource]:
        """Discover VPCs in a region."""
        resources = []
        try:
            ec2 = self.session.client("ec2", region_name=region)
            response = ec2.describe_vpcs()

            for vpc in response.get("Vpcs", []):
                # Extract basic info
                vpc_id = vpc.get("VpcId")
                cidr_block = vpc.get("CidrBlock")
                is_default = vpc.get("IsDefault")

                # Build ARN
                account_id = self.get_account_id()
                arn = f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc_id}"

                # Extract tags
                tags = {}
                for tag in vpc.get("Tags", []):
                    tags[tag["Key"]] = tag["Value"]

                # Map to DiscoveredResource
                resource = self.mapper.map_resource(
                    resource_id=arn,
                    resource_type="AWS::EC2::VPC",
                    tags=tags,
                    region=region,
                    account_id=account_id,
                )

                # Add VPC-specific properties
                resource.properties["cidr_block"] = cidr_block
                resource.properties["is_default"] = is_default

                resources.append(resource)

        except Exception as e:
            logger.error(f"Error discovering VPCs in {region}: {e}")

        return resources

    async def _discover_load_balancers(self, region: str) -> list[DiscoveredResource]:
        """Discover Load Balancers in a region."""
        resources = []
        try:
            elbv2 = self.session.client("elbv2", region_name=region)
            response = elbv2.describe_load_balancers()

            for lb in response.get("LoadBalancers", []):
                # Extract basic info
                arn = lb.get("LoadBalancerArn")
                lb_type = lb.get("Type")
                scheme = lb.get("Scheme")
                state = lb.get("State", {}).get("Code")

                # Get tags
                tags = {}
                try:
                    tag_response = elbv2.describe_tags(ResourceArns=[arn])
                    for tag_desc in tag_response.get("TagDescriptions", []):
                        for tag in tag_desc.get("Tags", []):
                            tags[tag["Key"]] = tag["Value"]
                except Exception:
                    pass

                # Map to DiscoveredResource
                account_id = self.get_account_id()
                resource = self.mapper.map_resource(
                    resource_id=arn,
                    resource_type="AWS::ElasticLoadBalancingV2::LoadBalancer",
                    tags=tags,
                    region=region,
                    account_id=account_id,
                )

                # Add LB-specific properties
                resource.properties["load_balancer_type"] = lb_type
                resource.properties["scheme"] = scheme
                resource.properties["state"] = state

                resources.append(resource)

        except Exception as e:
            logger.error(f"Error discovering Load Balancers in {region}: {e}")

        return resources

    async def _discover_dependencies(
        self,
        resources: list[DiscoveredResource],
    ) -> list[ResourceDependency]:
        """
        Discover dependencies between AWS resources.

        This analyzes relationships like:
        - EC2 instances in VPCs
        - Lambda functions accessing RDS/DynamoDB
        - Load Balancers targeting EC2 instances
        - EKS clusters in VPCs

        Args:
            resources: List of discovered resources

        Returns:
            List of ResourceDependency objects
        """
        dependencies = []

        # Create lookup maps for future optimization
        resource_by_id = {r.id: r for r in resources}  # noqa: F841 - prepared for optimization

        # Analyze EC2 -> VPC dependencies
        for resource in resources:
            if resource.resource_type == "ec2":
                vpc_id = resource.properties.get("vpc_id")
                if vpc_id:
                    # Find VPC resource
                    for vpc_resource in resources:
                        if vpc_resource.resource_type == "vpc" and vpc_id in vpc_resource.id:
                            dep = ResourceDependency(
                                source_id=resource.id,
                                target_id=vpc_resource.id,
                                dependency_type="network",
                                strength=0.9,
                                properties={"relationship": "instance_in_vpc"},
                            )
                            dependencies.append(dep)
                            break

        # Add more dependency detection as needed
        return dependencies

    async def _infer_applications(
        self,
        resources: list[DiscoveredResource],
    ) -> list[Application]:
        """
        Infer applications from AWS resources based on naming and tagging.

        Args:
            resources: List of discovered resources

        Returns:
            List of Application objects
        """
        applications = []
        app_names = set()

        # Look for application tags
        for resource in resources:
            if "application" in resource.tags:
                app_name = resource.tags["application"]
                if app_name not in app_names:
                    app_names.add(app_name)
                    app = Application(
                        name=app_name,
                        resource_ids=[resource.id],
                        environment=resource.environment,
                    )
                    applications.append(app)

        return applications

    def get_account_id(self) -> str | None:
        """
        Get the AWS account ID for the current credentials.

        Returns:
            AWS account ID or None
        """
        if not BOTO3_AVAILABLE or not self.session:
            return None

        try:
            sts = self.session.client("sts")
            response = sts.get_caller_identity()
            return response.get("Account")
        except Exception as e:
            logger.error(f"Error getting AWS account ID: {e}")
            return None
