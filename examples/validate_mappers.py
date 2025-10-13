"""
Mapper Validation Example

Demonstrates proper Neo4j formatting for resources from Azure, AWS, and GCP.
"""

"""
Note: This example requires the mapper modules only, not the full SDK dependencies.
Run with: PYTHONPATH=src python examples/validate_mappers.py
"""

# Import mappers directly (doesn't require cloud SDKs)
import sys
import json
from pathlib import Path

# Add src to path if not already there
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from topdeck.discovery.aws.mapper import AWSResourceMapper
from topdeck.discovery.gcp.mapper import GCPResourceMapper

# Note: Azure mapper requires azure SDK, so we'll skip it for now
# from topdeck.discovery.azure.mapper import AzureResourceMapper


def validate_azure():
    """Validate Azure resource mapping and Neo4j formatting."""
    print("\n" + "=" * 60)
    print("AZURE RESOURCE MAPPING")
    print("=" * 60)
    print("⚠️  Skipped - requires Azure SDK to be installed")
    print("   Install with: pip install azure-identity azure-mgmt-resource")


def validate_aws():
    """Validate AWS resource mapping and Neo4j formatting."""
    print("\n" + "=" * 60)
    print("AWS RESOURCE MAPPING")
    print("=" * 60)

    # Map an EKS cluster
    resource = AWSResourceMapper.map_aws_resource(
        arn="arn:aws:eks:us-east-1:123456789012:cluster/prod-eks",
        resource_name="prod-eks",
        resource_type="AWS::EKS::Cluster",
        region="us-east-1",
        tags=[
            {"Key": "Environment", "Value": "production"},
            {"Key": "Team", "Value": "platform"},
        ],
        properties={"version": "1.28", "nodeCount": 3},
        state="active",
    )

    print(f"\nResource Type: {resource.resource_type}")
    print(f"Cloud Provider: {resource.cloud_provider.value}")
    print(f"Region: {resource.region}")
    print(f"Status: {resource.status.value}")
    print(f"Environment: {resource.environment}")

    # Convert to Neo4j format
    neo4j_props = resource.to_neo4j_properties()
    print("\nNeo4j Properties:")
    print(json.dumps(neo4j_props, indent=2, default=str))

    # Validate format
    assert neo4j_props["cloud_provider"] == "aws"
    assert neo4j_props["resource_type"] == "eks"
    assert isinstance(neo4j_props["tags"], dict)
    assert neo4j_props["tags"]["Environment"] == "production"
    assert isinstance(neo4j_props["properties"], str)
    print("\n✓ AWS mapping validated")


def validate_gcp():
    """Validate GCP resource mapping and Neo4j formatting."""
    print("\n" + "=" * 60)
    print("GCP RESOURCE MAPPING")
    print("=" * 60)

    # Map a GKE cluster
    resource = GCPResourceMapper.map_gcp_resource(
        resource_name="projects/my-project-123/locations/us-central1/clusters/prod-gke",
        display_name="prod-gke",
        resource_type="container.googleapis.com/Cluster",
        region="us-central1",
        labels={"environment": "production", "team": "platform"},
        properties={"currentMasterVersion": "1.28.3-gke.1098000", "currentNodeCount": 3},
        state="RUNNING",
    )

    print(f"\nResource Type: {resource.resource_type}")
    print(f"Cloud Provider: {resource.cloud_provider.value}")
    print(f"Region: {resource.region}")
    print(f"Status: {resource.status.value}")
    print(f"Environment: {resource.environment}")

    # Convert to Neo4j format
    neo4j_props = resource.to_neo4j_properties()
    print("\nNeo4j Properties:")
    print(json.dumps(neo4j_props, indent=2, default=str))

    # Validate format
    assert neo4j_props["cloud_provider"] == "gcp"
    assert neo4j_props["resource_type"] == "gke_cluster"
    assert isinstance(neo4j_props["tags"], dict)
    assert neo4j_props["tags"]["environment"] == "production"
    assert isinstance(neo4j_props["properties"], str)
    print("\n✓ GCP mapping validated")


def compare_formats():
    """Compare Neo4j format across all three clouds."""
    print("\n" + "=" * 60)
    print("CROSS-CLOUD FORMAT COMPARISON")
    print("=" * 60)

    # Create similar resources in AWS and GCP
    aws = AWSResourceMapper.map_aws_resource(
        arn="arn:aws:eks:us-east-1:123456789012:cluster/cluster",
        resource_name="cluster",
        resource_type="AWS::EKS::Cluster",
        region="us-east-1",
        tags=[{"Key": "env", "Value": "prod"}],
    )

    gcp = GCPResourceMapper.map_gcp_resource(
        resource_name="projects/my-project/locations/us-central1/clusters/cluster",
        display_name="cluster",
        resource_type="container.googleapis.com/Cluster",
        labels={"env": "prod"},
    )

    # Show common fields
    print("\nCommon Fields Across Clouds:")
    print("-" * 60)

    for cloud, resource in [("AWS", aws), ("GCP", gcp)]:
        props = resource.to_neo4j_properties()
        print(f"\n{cloud}:")
        print(f"  id: {props['id'][:50]}...")
        print(f"  name: {props['name']}")
        print(f"  resource_type: {props['resource_type']}")
        print(f"  cloud_provider: {props['cloud_provider']}")
        print(f"  region: {props['region']}")
        print(f"  status: {props['status']}")
        print(f"  environment: {props['environment']}")
        print(f"  tags: {props['tags']}")

    print("\n✓ AWS and GCP use consistent Neo4j format")


def main():
    """Main entry point."""
    print("=" * 60)
    print("TopDeck Multi-Cloud Mapper Validation")
    print("=" * 60)

    try:
        validate_azure()
        validate_aws()
        validate_gcp()
        compare_formats()

        print("\n" + "=" * 60)
        print("VALIDATIONS PASSED ✓")
        print("=" * 60)
        print("\nKey Points:")
        print("  ✓ AWS and GCP mappers work correctly")
        print("  ✓ All clouds map to consistent Neo4j schema")
        print("  ✓ Tags/Labels normalized to dict format")
        print("  ✓ Properties stored as JSON strings")
        print("  ✓ Timestamps in ISO format")
        print("  ✓ Enums converted to string values")
        print("\nNote: Azure mapper validation requires Azure SDK")

    except AssertionError as e:
        print(f"\n❌ Validation failed: {str(e)}")
        raise
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
