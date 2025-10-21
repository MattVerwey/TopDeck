"""
Tests for AWS Resource Mapper.
"""

from topdeck.discovery.aws.mapper import AWSResourceMapper
from topdeck.discovery.models import CloudProvider, ResourceStatus


class TestAWSResourceMapper:
    """Tests for AWSResourceMapper"""

    def test_map_resource_type_known(self):
        """Test mapping known AWS resource types"""
        assert AWSResourceMapper.map_resource_type("AWS::EC2::Instance") == "ec2_instance"
        assert AWSResourceMapper.map_resource_type("AWS::EKS::Cluster") == "eks"
        assert AWSResourceMapper.map_resource_type("AWS::RDS::DBInstance") == "rds_instance"
        assert AWSResourceMapper.map_resource_type("AWS::S3::Bucket") == "s3_bucket"

    def test_map_resource_type_unknown(self):
        """Test mapping unknown AWS resource type"""
        assert AWSResourceMapper.map_resource_type("AWS::Unknown::Resource") == "unknown"

    def test_extract_account_id(self):
        """Test extracting account ID from ARN"""
        arn = "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"
        assert AWSResourceMapper.extract_account_id(arn) == "123456789012"

    def test_extract_account_id_invalid(self):
        """Test extracting account ID from invalid ARN"""
        assert AWSResourceMapper.extract_account_id("not-an-arn") is None

    def test_extract_region(self):
        """Test extracting region from ARN"""
        arn = "arn:aws:ec2:us-west-2:123456789012:instance/i-1234567890abcdef0"
        assert AWSResourceMapper.extract_region(arn) == "us-west-2"

    def test_extract_region_global(self):
        """Test extracting region from global ARN"""
        arn = "arn:aws:iam::123456789012:role/MyRole"
        # Global services have empty region
        result = AWSResourceMapper.extract_region(arn)
        assert result == "" or result is None

    def test_map_state_to_status_running(self):
        """Test mapping running states"""
        assert AWSResourceMapper.map_state_to_status("running") == ResourceStatus.RUNNING
        assert AWSResourceMapper.map_state_to_status("available") == ResourceStatus.RUNNING
        assert AWSResourceMapper.map_state_to_status("active") == ResourceStatus.RUNNING
        assert AWSResourceMapper.map_state_to_status("in-service") == ResourceStatus.RUNNING

    def test_map_state_to_status_stopped(self):
        """Test mapping stopped states"""
        assert AWSResourceMapper.map_state_to_status("stopped") == ResourceStatus.STOPPED
        assert AWSResourceMapper.map_state_to_status("stopping") == ResourceStatus.STOPPED
        assert AWSResourceMapper.map_state_to_status("shutting-down") == ResourceStatus.STOPPED

    def test_map_state_to_status_error(self):
        """Test mapping error states"""
        assert AWSResourceMapper.map_state_to_status("failed") == ResourceStatus.ERROR
        assert AWSResourceMapper.map_state_to_status("error") == ResourceStatus.ERROR
        assert AWSResourceMapper.map_state_to_status("unhealthy") == ResourceStatus.ERROR

    def test_map_state_to_status_degraded(self):
        """Test mapping degraded states"""
        assert AWSResourceMapper.map_state_to_status("pending") == ResourceStatus.DEGRADED
        assert AWSResourceMapper.map_state_to_status("creating") == ResourceStatus.DEGRADED
        assert AWSResourceMapper.map_state_to_status("updating") == ResourceStatus.DEGRADED

    def test_map_state_to_status_unknown(self):
        """Test mapping unknown states"""
        assert AWSResourceMapper.map_state_to_status(None) == ResourceStatus.UNKNOWN
        assert AWSResourceMapper.map_state_to_status("unknown-state") == ResourceStatus.UNKNOWN

    def test_extract_environment_from_tags_list(self):
        """Test extracting environment from AWS tags (list format)"""
        tags = [
            {"Key": "Environment", "Value": "production"},
            {"Key": "Application", "Value": "web"},
        ]
        assert AWSResourceMapper.extract_environment_from_tags(tags) == "production"

    def test_extract_environment_from_tags_lowercase(self):
        """Test extracting environment from lowercase tag key"""
        tags = [{"Key": "env", "Value": "Staging"}]
        assert AWSResourceMapper.extract_environment_from_tags(tags) == "staging"

    def test_extract_environment_from_tags_none(self):
        """Test extracting environment when no environment tag exists"""
        tags = [{"Key": "Application", "Value": "web"}]
        assert AWSResourceMapper.extract_environment_from_tags(tags) is None

    def test_extract_environment_from_tags_empty(self):
        """Test extracting environment from empty tags"""
        assert AWSResourceMapper.extract_environment_from_tags([]) is None
        assert AWSResourceMapper.extract_environment_from_tags(None) is None

    def test_normalize_tags_list(self):
        """Test normalizing AWS tags from list format"""
        tags = [
            {"Key": "Environment", "Value": "production"},
            {"Key": "Application", "Value": "web"},
        ]
        result = AWSResourceMapper.normalize_tags(tags)
        assert result == {"Environment": "production", "Application": "web"}

    def test_normalize_tags_dict(self):
        """Test normalizing AWS tags from dict format"""
        tags = {"Environment": "production", "Application": "web"}
        result = AWSResourceMapper.normalize_tags(tags)
        assert result == tags

    def test_normalize_tags_empty(self):
        """Test normalizing empty tags"""
        assert AWSResourceMapper.normalize_tags([]) == {}
        assert AWSResourceMapper.normalize_tags(None) == {}

    def test_map_aws_resource_complete(self):
        """Test mapping a complete AWS resource"""
        arn = "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"
        tags = [
            {"Key": "Environment", "Value": "production"},
            {"Key": "Application", "Value": "web"},
        ]

        resource = AWSResourceMapper.map_aws_resource(
            arn=arn,
            resource_name="web-server-01",
            resource_type="AWS::EC2::Instance",
            region="us-east-1",
            tags=tags,
            properties={"InstanceType": "t3.large"},
            state="running",
        )

        assert resource.id == arn
        assert resource.name == "web-server-01"
        assert resource.resource_type == "ec2_instance"
        assert resource.cloud_provider == CloudProvider.AWS
        assert resource.region == "us-east-1"
        assert resource.subscription_id == "123456789012"
        assert resource.status == ResourceStatus.RUNNING
        assert resource.environment == "production"
        assert resource.tags == {"Environment": "production", "Application": "web"}
        assert resource.properties == {"InstanceType": "t3.large"}

    def test_map_aws_resource_minimal(self):
        """Test mapping AWS resource with minimal data"""
        arn = "arn:aws:s3:::my-bucket"

        resource = AWSResourceMapper.map_aws_resource(
            arn=arn, resource_name="my-bucket", resource_type="AWS::S3::Bucket", region="us-east-1"
        )

        assert resource.id == arn
        assert resource.name == "my-bucket"
        assert resource.resource_type == "s3_bucket"
        assert resource.cloud_provider == CloudProvider.AWS
        assert resource.region == "us-east-1"
        assert resource.tags == {}
        assert resource.properties == {}
        assert resource.status == ResourceStatus.UNKNOWN

    def test_map_aws_resource_neo4j_format(self):
        """Test Neo4j formatting of mapped AWS resource"""
        arn = "arn:aws:rds:us-west-2:123456789012:db:mydb"
        tags = [{"Key": "env", "Value": "dev"}]

        resource = AWSResourceMapper.map_aws_resource(
            arn=arn,
            resource_name="mydb",
            resource_type="AWS::RDS::DBInstance",
            region="us-west-2",
            tags=tags,
            properties={"Engine": "postgres"},
            state="available",
        )

        neo4j_props = resource.to_neo4j_properties()

        assert neo4j_props["id"] == arn
        assert neo4j_props["name"] == "mydb"
        assert neo4j_props["resource_type"] == "rds_instance"
        assert neo4j_props["cloud_provider"] == "aws"
        assert neo4j_props["region"] == "us-west-2"
        assert neo4j_props["subscription_id"] == "123456789012"
        assert neo4j_props["status"] == "running"
        assert neo4j_props["environment"] == "dev"
        assert neo4j_props["tags"] == {"env": "dev"}
        assert '"Engine": "postgres"' in neo4j_props["properties"]
        assert "discovered_at" in neo4j_props
        assert "last_seen" in neo4j_props
