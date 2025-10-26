"""
Tests for AWS Resource Discoverer.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from topdeck.discovery.aws.discoverer import AWSDiscoverer
from topdeck.discovery.models import DiscoveredResource


class TestAWSDiscoverer:
    """Test suite for AWSDiscoverer."""

    @pytest.fixture
    def discoverer(self):
        """Create an AWSDiscoverer instance for testing."""
        return AWSDiscoverer(
            access_key_id="test_key",
            secret_access_key="test_secret",
            region="us-east-1",
        )

    def test_initialization(self, discoverer):
        """Test that discoverer initializes correctly."""
        assert discoverer.access_key_id == "test_key"
        assert discoverer.secret_access_key == "test_secret"
        assert discoverer.region == "us-east-1"
        assert discoverer.mapper is not None

    @pytest.mark.asyncio
    async def test_discover_all_resources_without_boto3(self):
        """Test discovery when boto3 is not available."""
        with patch("topdeck.discovery.aws.discoverer.BOTO3_AVAILABLE", False):
            discoverer = AWSDiscoverer()
            result = await discoverer.discover_all_resources()

            assert result.cloud_provider == "aws"
            assert len(result.resources) == 0
            assert len(result.errors) == 1
            assert "boto3 not available" in result.errors[0]

    @pytest.mark.asyncio
    async def test_discover_ec2_instances(self, discoverer):
        """Test EC2 instance discovery."""
        # Mock boto3 EC2 client
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "InstanceType": "t2.micro",
                            "State": {"Name": "running"},
                            "VpcId": "vpc-12345",
                            "SubnetId": "subnet-12345",
                            "Tags": [
                                {"Key": "Name", "Value": "test-instance"},
                                {"Key": "Environment", "Value": "dev"},
                            ],
                        }
                    ]
                }
            ]
        }

        with patch.object(discoverer, "session") as mock_session:
            mock_session.client.return_value = mock_ec2
            with patch.object(discoverer, "get_account_id", return_value="123456789012"):
                resources = await discoverer._discover_ec2_instances("us-east-1")

                assert len(resources) == 1
                resource = resources[0]
                assert resource.resource_type == "ec2"
                assert "instance_type" in resource.properties
                assert resource.properties["instance_type"] == "t2.micro"
                assert resource.properties["state"] == "running"

    @pytest.mark.asyncio
    async def test_discover_eks_clusters(self, discoverer):
        """Test EKS cluster discovery."""
        # Mock boto3 EKS client
        mock_eks = MagicMock()
        mock_eks.list_clusters.return_value = {"clusters": ["test-cluster"]}
        mock_eks.describe_cluster.return_value = {
            "cluster": {
                "name": "test-cluster",
                "arn": "arn:aws:eks:us-east-1:123456789012:cluster/test-cluster",
                "status": "ACTIVE",
                "version": "1.24",
                "endpoint": "https://test-cluster.eks.amazonaws.com",
                "tags": {"Environment": "prod", "Team": "platform"},
            }
        }

        with patch.object(discoverer, "session") as mock_session:
            mock_session.client.return_value = mock_eks
            with patch.object(discoverer, "get_account_id", return_value="123456789012"):
                resources = await discoverer._discover_eks_clusters("us-east-1")

                assert len(resources) == 1
                resource = resources[0]
                assert resource.resource_type == "eks"
                assert resource.properties["status"] == "ACTIVE"
                assert resource.properties["version"] == "1.24"

    @pytest.mark.asyncio
    async def test_discover_rds_databases(self, discoverer):
        """Test RDS database discovery."""
        # Mock boto3 RDS client
        mock_rds = MagicMock()
        mock_rds.describe_db_instances.return_value = {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "test-db",
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:db:test-db",
                    "Engine": "postgres",
                    "EngineVersion": "14.2",
                    "DBInstanceStatus": "available",
                    "Endpoint": {"Address": "test-db.abc123.us-east-1.rds.amazonaws.com", "Port": 5432},
                    "TagList": [{"Key": "Environment", "Value": "prod"}],
                }
            ]
        }

        with patch.object(discoverer, "session") as mock_session:
            mock_session.client.return_value = mock_rds
            with patch.object(discoverer, "get_account_id", return_value="123456789012"):
                resources = await discoverer._discover_rds_databases("us-east-1")

                assert len(resources) == 1
                resource = resources[0]
                assert resource.resource_type == "rds"
                assert resource.properties["engine"] == "postgres"
                assert resource.properties["endpoint_address"] == "test-db.abc123.us-east-1.rds.amazonaws.com"

    @pytest.mark.asyncio
    async def test_discover_s3_buckets(self, discoverer):
        """Test S3 bucket discovery."""
        # Mock boto3 S3 client
        mock_s3 = MagicMock()
        mock_s3.list_buckets.return_value = {
            "Buckets": [
                {"Name": "test-bucket-1"},
                {"Name": "test-bucket-2"},
            ]
        }
        mock_s3.get_bucket_location.return_value = {"LocationConstraint": "us-east-1"}
        mock_s3.get_bucket_tagging.return_value = {
            "TagSet": [{"Key": "Project", "Value": "test"}]
        }

        with patch.object(discoverer, "session") as mock_session:
            mock_session.client.return_value = mock_s3
            with patch.object(discoverer, "get_account_id", return_value="123456789012"):
                resources = await discoverer._discover_s3_buckets("us-east-1")

                assert len(resources) == 2
                assert all(r.resource_type == "s3" for r in resources)

    @pytest.mark.asyncio
    async def test_discover_lambda_functions(self, discoverer):
        """Test Lambda function discovery."""
        # Mock boto3 Lambda client
        mock_lambda = MagicMock()
        mock_lambda.list_functions.return_value = {
            "Functions": [
                {
                    "FunctionName": "test-function",
                    "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:test-function",
                    "Runtime": "python3.9",
                    "Handler": "index.handler",
                }
            ]
        }
        mock_lambda.list_tags.return_value = {"Tags": {"Environment": "dev"}}

        with patch.object(discoverer, "session") as mock_session:
            mock_session.client.return_value = mock_lambda
            with patch.object(discoverer, "get_account_id", return_value="123456789012"):
                resources = await discoverer._discover_lambda_functions("us-east-1")

                assert len(resources) == 1
                resource = resources[0]
                assert resource.resource_type == "lambda"
                assert resource.properties["runtime"] == "python3.9"

    @pytest.mark.asyncio
    async def test_discover_dynamodb_tables(self, discoverer):
        """Test DynamoDB table discovery."""
        # Mock boto3 DynamoDB client
        mock_dynamodb = MagicMock()
        mock_dynamodb.list_tables.return_value = {"TableNames": ["test-table"]}
        mock_dynamodb.describe_table.return_value = {
            "Table": {
                "TableName": "test-table",
                "TableArn": "arn:aws:dynamodb:us-east-1:123456789012:table/test-table",
                "TableStatus": "ACTIVE",
                "ItemCount": 100,
            }
        }
        mock_dynamodb.list_tags_of_resource.return_value = {
            "Tags": [{"Key": "Environment", "Value": "prod"}]
        }

        with patch.object(discoverer, "session") as mock_session:
            mock_session.client.return_value = mock_dynamodb
            with patch.object(discoverer, "get_account_id", return_value="123456789012"):
                resources = await discoverer._discover_dynamodb_tables("us-east-1")

                assert len(resources) == 1
                resource = resources[0]
                assert resource.resource_type == "dynamodb"
                assert resource.properties["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_discover_vpcs(self, discoverer):
        """Test VPC discovery."""
        # Mock boto3 EC2 client
        mock_ec2 = MagicMock()
        mock_ec2.describe_vpcs.return_value = {
            "Vpcs": [
                {
                    "VpcId": "vpc-12345",
                    "CidrBlock": "10.0.0.0/16",
                    "IsDefault": False,
                    "Tags": [{"Key": "Name", "Value": "test-vpc"}],
                }
            ]
        }

        with patch.object(discoverer, "session") as mock_session:
            mock_session.client.return_value = mock_ec2
            with patch.object(discoverer, "get_account_id", return_value="123456789012"):
                resources = await discoverer._discover_vpcs("us-east-1")

                assert len(resources) == 1
                resource = resources[0]
                assert resource.resource_type == "vpc"
                assert resource.properties["cidr_block"] == "10.0.0.0/16"

    @pytest.mark.asyncio
    async def test_discover_load_balancers(self, discoverer):
        """Test Load Balancer discovery."""
        # Mock boto3 ELBv2 client
        mock_elbv2 = MagicMock()
        mock_elbv2.describe_load_balancers.return_value = {
            "LoadBalancers": [
                {
                    "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/test-lb/50dc6c495c0c9188",
                    "Type": "application",
                    "Scheme": "internet-facing",
                    "State": {"Code": "active"},
                }
            ]
        }
        mock_elbv2.describe_tags.return_value = {
            "TagDescriptions": [
                {"Tags": [{"Key": "Environment", "Value": "prod"}]}
            ]
        }

        with patch.object(discoverer, "session") as mock_session:
            mock_session.client.return_value = mock_elbv2
            with patch.object(discoverer, "get_account_id", return_value="123456789012"):
                resources = await discoverer._discover_load_balancers("us-east-1")

                assert len(resources) == 1
                resource = resources[0]
                assert resource.resource_type == "load_balancer"
                assert resource.properties["load_balancer_type"] == "application"

    @pytest.mark.asyncio
    async def test_discover_dependencies(self, discoverer):
        """Test dependency discovery between resources."""
        # Create mock resources
        vpc_resource = DiscoveredResource(
            id="arn:aws:ec2:us-east-1:123456789012:vpc/vpc-12345",
            name="test-vpc",
            resource_type="vpc",
            cloud_provider="aws",
            region="us-east-1",
        )

        ec2_resource = DiscoveredResource(
            id="arn:aws:ec2:us-east-1:123456789012:instance/i-12345",
            name="test-instance",
            resource_type="ec2",
            cloud_provider="aws",
            region="us-east-1",
        )
        ec2_resource.properties["vpc_id"] = "vpc-12345"

        resources = [vpc_resource, ec2_resource]

        dependencies = await discoverer._discover_dependencies(resources)

        # Should find EC2 -> VPC dependency
        assert len(dependencies) > 0
        dep = dependencies[0]
        assert dep.source_id == ec2_resource.id
        assert dep.target_id == vpc_resource.id
        assert dep.dependency_type == "network"

    @pytest.mark.asyncio
    async def test_infer_applications(self, discoverer):
        """Test application inference from resources."""
        # Create resources with application tags
        resource1 = DiscoveredResource(
            id="arn:aws:ec2:us-east-1:123456789012:instance/i-12345",
            name="web-server",
            resource_type="ec2",
            cloud_provider="aws",
            region="us-east-1",
            tags={"application": "web-app"},
        )

        resource2 = DiscoveredResource(
            id="arn:aws:rds:us-east-1:123456789012:db:mydb",
            name="database",
            resource_type="rds",
            cloud_provider="aws",
            region="us-east-1",
            tags={"application": "web-app"},
        )

        resources = [resource1, resource2]

        applications = await discoverer._infer_applications(resources)

        assert len(applications) == 1
        app = applications[0]
        assert app.name == "web-app"
        assert len(app.resource_ids) == 1

    def test_get_account_id_without_boto3(self):
        """Test getting account ID when boto3 is not available."""
        with patch("topdeck.discovery.aws.discoverer.BOTO3_AVAILABLE", False):
            discoverer = AWSDiscoverer()
            account_id = discoverer.get_account_id()
            assert account_id is None

    def test_get_account_id_with_boto3(self, discoverer):
        """Test getting account ID with boto3."""
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}

        with patch.object(discoverer, "session") as mock_session:
            mock_session.client.return_value = mock_sts
            account_id = discoverer.get_account_id()
            assert account_id == "123456789012"

    @pytest.mark.asyncio
    async def test_multi_region_discovery(self, discoverer):
        """Test discovery across multiple regions."""
        with patch.multiple(
            discoverer,
            _discover_ec2_instances=AsyncMock(),
            _discover_eks_clusters=AsyncMock(),
            _discover_rds_databases=AsyncMock(),
            _discover_s3_buckets=AsyncMock(),
            _discover_lambda_functions=AsyncMock(),
            _discover_dynamodb_tables=AsyncMock(),
            _discover_vpcs=AsyncMock(),
            _discover_load_balancers=AsyncMock(),
            _discover_dependencies=AsyncMock(),
            _infer_applications=AsyncMock(),
        ) as mocks:
            # Set return values
            mocks["_discover_ec2_instances"].return_value = []
            mocks["_discover_eks_clusters"].return_value = []
            mocks["_discover_rds_databases"].return_value = []
            mocks["_discover_s3_buckets"].return_value = []
            mocks["_discover_lambda_functions"].return_value = []
            mocks["_discover_dynamodb_tables"].return_value = []
            mocks["_discover_vpcs"].return_value = []
            mocks["_discover_load_balancers"].return_value = []
            mocks["_discover_dependencies"].return_value = []
            mocks["_infer_applications"].return_value = []

            regions = ["us-east-1", "us-west-2"]
            result = await discoverer.discover_all_resources(regions=regions)

            # Should call each discovery method once per region
            assert mocks["_discover_ec2_instances"].call_count == 2
            assert mocks["_discover_eks_clusters"].call_count == 2
            assert result.cloud_provider == "aws"
