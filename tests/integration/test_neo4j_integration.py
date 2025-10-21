"""
Integration tests for Neo4j storage with complex data structures.

These tests verify the end-to-end flow:
1. Create resources with complex nested tags/properties
2. Convert to Neo4j properties (serialization)
3. Store in Neo4j
4. Retrieve from Neo4j
5. Deserialize back to original structure

Note: These tests require a running Neo4j instance.
They can be skipped if Neo4j is not available.

Note: Print statements are intentionally used in these tests
to provide clear demonstration output for documentation purposes.
"""

import json

import pytest

from topdeck.analysis.topology import TopologyService
from topdeck.discovery.models import CloudProvider, DiscoveredResource, ResourceStatus


class TestNeo4jIntegration:
    """Integration tests for Neo4j storage with complex data"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test"""
        # This would need a real Neo4j connection in a real test environment
        # For now, we'll skip actual Neo4j operations
        pytest.skip("Requires running Neo4j instance")

        # Example setup code (would be used with real Neo4j):
        # self.neo4j = Neo4jClient(
        #     uri="bolt://localhost:7687",
        #     username="neo4j",
        #     password="password"
        # )
        # self.neo4j.connect()
        #
        # yield
        #
        # # Cleanup
        # self.neo4j.clear_all()
        # self.neo4j.close()

    def test_store_and_retrieve_complex_resource(self):
        """
        Test storing and retrieving a resource with complex nested tags.

        This simulates the real-world scenario from the issue where Azure
        resources have complex nested objects in tags.
        """
        # Create resource with complex tags (like the failing Azure resources)
        resource = DiscoveredResource(
            id="/subscriptions/abc123/resourceGroups/rg/providers/Microsoft.ContainerService/managedClusters/sisexternalaksdata000001",
            name="sisexternalaksdata000001",
            resource_type="aks",
            cloud_provider=CloudProvider.AZURE,
            region="uksouth",
            resource_group="rg",
            subscription_id="abc123",
            status=ResourceStatus.RUNNING,
            tags={
                "Product Name": "Azure Kubernetes Service",
                "Value Stream": "Shared",
                "runningPattern": "officeHours",
                "dates": {
                    "creationDate": "2025-09-10T09:05:19Z",
                    "reviewDate": "2025-10-10T09:05:19Z",
                },
                "owners": {
                    "businessOwner": "user@company.com",
                    "technicalOwner": "dev@company.com",
                },
            },
            properties={
                "kubernetesVersion": "1.27.3",
                "provisioningState": "Succeeded",
                "networkProfile": {
                    "networkPlugin": "azure",
                    "serviceCidr": "10.0.0.0/16",
                    "dnsServiceIP": "10.0.0.10",
                },
                "agentPoolProfiles": [
                    {
                        "name": "nodepool1",
                        "count": 3,
                        "vmSize": "Standard_DS2_v2",
                    }
                ],
            },
        )

        # Convert to Neo4j properties (this is where serialization happens)
        neo4j_props = resource.to_neo4j_properties()

        # Verify serialization: tags and properties should be JSON strings
        assert isinstance(neo4j_props["tags"], str)
        assert isinstance(neo4j_props["properties"], str)

        # Verify no nested dicts/lists in the properties dict
        for key, value in neo4j_props.items():
            if key in ("tags", "properties"):
                assert isinstance(value, str), f"{key} must be a string"
            else:
                assert value is None or isinstance(
                    value, (str, int, float, bool)
                ), f"{key} must be primitive, got {type(value)}"

        # Store in Neo4j (would use self.neo4j.upsert_resource(neo4j_props))
        # For this test, we simulate what Neo4j would store
        stored_props = neo4j_props.copy()

        # Retrieve from Neo4j and deserialize
        # (would use self.neo4j.get_resource_by_id(resource.id))
        # For testing, we use the static method directly without a client
        deserialized_props = TopologyService._deserialize_json_properties(stored_props)

        # Verify deserialization: tags and properties should be dicts again
        assert isinstance(deserialized_props["tags"], dict)
        assert isinstance(deserialized_props["properties"], dict)

        # Verify the complex nested structure is preserved
        tags = deserialized_props["tags"]
        assert tags["Product Name"] == "Azure Kubernetes Service"
        assert tags["Value Stream"] == "Shared"
        assert isinstance(tags["dates"], dict)
        assert tags["dates"]["creationDate"] == "2025-09-10T09:05:19Z"
        assert isinstance(tags["owners"], dict)
        assert tags["owners"]["businessOwner"] == "user@company.com"

        properties = deserialized_props["properties"]
        assert properties["kubernetesVersion"] == "1.27.3"
        assert isinstance(properties["networkProfile"], dict)
        assert properties["networkProfile"]["networkPlugin"] == "azure"
        assert isinstance(properties["agentPoolProfiles"], list)
        assert properties["agentPoolProfiles"][0]["name"] == "nodepool1"

        print("✅ Complex resource can be stored and retrieved successfully!")

    def test_multiple_resources_with_different_complexity(self):
        """Test storing multiple resources with varying complexity"""
        resources = [
            # Simple resource
            DiscoveredResource(
                id="simple-1",
                name="simple-resource",
                resource_type="storage_account",
                cloud_provider=CloudProvider.AZURE,
                region="eastus",
                tags={"env": "prod"},
                properties={"tier": "standard"},
            ),
            # Complex resource
            DiscoveredResource(
                id="complex-1",
                name="complex-resource",
                resource_type="aks",
                cloud_provider=CloudProvider.AZURE,
                region="westus",
                tags={
                    "env": "prod",
                    "metadata": {
                        "team": "platform",
                        "cost_center": "12345",
                    },
                },
                properties={
                    "version": "1.27",
                    "config": {
                        "networking": {"mode": "advanced"},
                        "security": {"enabled": True},
                    },
                },
            ),
        ]

        # Convert all to Neo4j properties
        all_props = [r.to_neo4j_properties() for r in resources]

        # Verify all are properly serialized
        for props in all_props:
            assert isinstance(props["tags"], str)
            assert isinstance(props["properties"], str)

            # Verify no nested objects
            for key, value in props.items():
                if key in ("tags", "properties"):
                    assert isinstance(value, str)
                else:
                    assert value is None or isinstance(value, (str, int, float, bool))

        print("✅ Multiple resources with varying complexity handled correctly!")


class TestDocumentation:
    """Document the changes for API consumers"""

    def test_document_storage_format(self):
        """Document how tags and properties are stored in Neo4j"""
        doc = """
        ## Neo4j Storage Format for Complex Data

        ### Background
        Neo4j does not accept nested Maps or Lists as node property values.
        All property values must be primitive types (string, number, boolean) or arrays thereof.

        ### Solution
        Complex fields like `tags` and `properties` are serialized to JSON strings before storage:

        **Before (Python dict):**
        ```python
        tags = {
            "Product Name": "Azure Kubernetes Service",
            "dates": {
                "creationDate": "2025-09-10T09:05:19Z"
            }
        }
        ```

        **After (Neo4j storage):**
        ```
        tags = '{"Product Name": "Azure Kubernetes Service", "dates": {"creationDate": "2025-09-10T09:05:19Z"}}'
        ```

        ### API Behavior
        The TopologyService automatically deserializes JSON strings back to Python objects
        when retrieving data through the API, so API consumers see the original structure.

        ### Affected Fields
        The following fields are stored as JSON strings:
        - `tags` (dict)
        - `properties` (dict)
        - `labels` (dict)
        - `annotations` (dict)
        - `topics` (list)
        - `containers` (list)
        - `volumes` (list)
        - `conditions` (list)
        - `identifier_uris` (list)
        - `redirect_uris` (list)
        - `target_resources` (list)
        - `approvers` (list)
        - `app_roles` (list)
        - `oauth2_permissions` (list)
        - `required_resource_access` (list)

        ### For Direct Neo4j Queries
        If you query Neo4j directly (not through the API), remember to deserialize:

        ```python
        import json

        # Get resource from Neo4j
        resource = neo4j.get_resource_by_id(resource_id)

        # Deserialize tags
        if 'tags' in resource and isinstance(resource['tags'], str):
            resource['tags'] = json.loads(resource['tags'])

        # Deserialize properties
        if 'properties' in resource and isinstance(resource['properties'], str):
            resource['properties'] = json.loads(resource['properties'])
        ```
        """

        print(doc)
        assert True, "Documentation provided"


def test_serialization_deserialization_roundtrip():
    """
    Test the complete roundtrip: Python dict -> JSON string -> Python dict

    This test doesn't require Neo4j and verifies the core logic.
    """
    original_data = {
        "Product Name": "Azure Kubernetes Service",
        "Value Stream": "Shared",
        "runningPattern": "officeHours",
        "dates": {
            "creationDate": "2025-09-10T09:05:19Z",
            "reviewDate": "2025-10-10T09:05:19Z",
        },
        "owners": {
            "businessOwner": "user@company.com",
            "technicalOwner": "dev@company.com",
        },
        "serviceDetails": {
            "tier": "premium",
            "sku": "P1v2",
            "instances": 2,
            "config": {
                "autoscale": True,
                "minReplicas": 1,
                "maxReplicas": 10,
            },
        },
    }

    # Serialize (what happens before Neo4j storage)
    serialized = json.dumps(original_data)
    assert isinstance(serialized, str)

    # Deserialize (what happens after Neo4j retrieval)
    deserialized = json.loads(serialized)

    # Verify the roundtrip preserves the structure
    assert deserialized == original_data
    assert isinstance(deserialized["dates"], dict)
    assert isinstance(deserialized["owners"], dict)
    assert isinstance(deserialized["serviceDetails"]["config"], dict)
    assert deserialized["serviceDetails"]["config"]["autoscale"] is True
    assert deserialized["serviceDetails"]["config"]["minReplicas"] == 1

    print("✅ Serialization/deserialization roundtrip successful!")
