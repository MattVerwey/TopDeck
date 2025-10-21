"""
Integration tests for Azure test infrastructure.

These tests validate that the deployed Azure infrastructure is accessible
and discoverable by TopDeck.

Prerequisites:
- Azure infrastructure deployed via Terraform
- Azure credentials configured in environment
- Service principal with Reader role

Environment Variables:
- AZURE_TENANT_ID
- AZURE_CLIENT_ID
- AZURE_CLIENT_SECRET
- AZURE_SUBSCRIPTION_ID
- TEST_RESOURCE_GROUP (optional, defaults to topdeck-test-rg)
"""

import os

import pytest
from azure.identity import ClientSecretCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient


@pytest.fixture
def azure_credentials():
    """Get Azure credentials from environment."""
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")

    if not all([tenant_id, client_id, client_secret, subscription_id]):
        pytest.skip("Azure credentials not configured in environment")

    return {
        "credential": ClientSecretCredential(
            tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
        ),
        "subscription_id": subscription_id,
    }


@pytest.fixture
def test_resource_group():
    """Get test resource group name from environment."""
    return os.getenv("TEST_RESOURCE_GROUP", "topdeck-test-rg")


@pytest.mark.integration
@pytest.mark.azure
def test_resource_group_exists(azure_credentials, test_resource_group):
    """Test that the test resource group exists."""
    credential = azure_credentials["credential"]
    subscription_id = azure_credentials["subscription_id"]

    client = ResourceManagementClient(credential, subscription_id)

    # Get resource group
    rg = client.resource_groups.get(test_resource_group)

    assert rg is not None
    assert rg.name == test_resource_group
    assert rg.properties.provisioning_state == "Succeeded"

    # Check tags
    assert "ManagedBy" in rg.tags
    assert rg.tags["ManagedBy"] == "TopDeck"


@pytest.mark.integration
@pytest.mark.azure
def test_storage_account_discovery(azure_credentials, test_resource_group):
    """Test that storage accounts can be discovered."""
    credential = azure_credentials["credential"]
    subscription_id = azure_credentials["subscription_id"]

    client = StorageManagementClient(credential, subscription_id)

    # List storage accounts in resource group
    storage_accounts = list(client.storage_accounts.list_by_resource_group(test_resource_group))

    # Should have at least one storage account if test resources were created
    # This is optional, so we just log if not found
    if storage_accounts:
        account = storage_accounts[0]
        assert account.name is not None
        assert account.location is not None
        assert account.sku is not None
        print(f"Found storage account: {account.name}")
    else:
        print("No storage accounts found (optional test resource)")


@pytest.mark.integration
@pytest.mark.azure
def test_virtual_network_discovery(azure_credentials, test_resource_group):
    """Test that virtual networks can be discovered."""
    credential = azure_credentials["credential"]
    subscription_id = azure_credentials["subscription_id"]

    client = NetworkManagementClient(credential, subscription_id)

    # List virtual networks in resource group
    vnets = list(client.virtual_networks.list(test_resource_group))

    if vnets:
        vnet = vnets[0]
        assert vnet.name is not None
        assert vnet.location is not None
        assert len(vnet.address_space.address_prefixes) > 0
        print(f"Found virtual network: {vnet.name}")

        # Check subnets
        assert len(list(vnet.subnets)) > 0
        print(f"Found {len(list(vnet.subnets))} subnets")
    else:
        print("No virtual networks found (optional test resource)")


@pytest.mark.integration
@pytest.mark.azure
def test_network_security_group_discovery(azure_credentials, test_resource_group):
    """Test that network security groups can be discovered."""
    credential = azure_credentials["credential"]
    subscription_id = azure_credentials["subscription_id"]

    client = NetworkManagementClient(credential, subscription_id)

    # List NSGs in resource group
    nsgs = list(client.network_security_groups.list(test_resource_group))

    if nsgs:
        nsg = nsgs[0]
        assert nsg.name is not None
        assert nsg.location is not None
        print(f"Found NSG: {nsg.name}")

        # Check security rules
        if nsg.security_rules:
            print(f"Found {len(nsg.security_rules)} security rules")
    else:
        print("No NSGs found (optional test resource)")


@pytest.mark.integration
@pytest.mark.azure
def test_all_resources_discovery(azure_credentials, test_resource_group):
    """Test that all resources in the test resource group can be discovered."""
    credential = azure_credentials["credential"]
    subscription_id = azure_credentials["subscription_id"]

    client = ResourceManagementClient(credential, subscription_id)

    # List all resources in the resource group
    resources = list(client.resources.list_by_resource_group(test_resource_group))

    assert len(resources) > 0, "No resources found in test resource group"

    print(f"\nFound {len(resources)} resources:")
    for resource in resources:
        print(f"  - {resource.name} ({resource.type})")
        assert resource.name is not None
        assert resource.type is not None
        assert resource.location is not None


@pytest.mark.integration
@pytest.mark.azure
def test_resource_tags(azure_credentials, test_resource_group):
    """Test that resources have appropriate tags for discovery."""
    credential = azure_credentials["credential"]
    subscription_id = azure_credentials["subscription_id"]

    client = ResourceManagementClient(credential, subscription_id)

    # Get resource group tags
    rg = client.resource_groups.get(test_resource_group)

    # Check for common tags
    expected_tags = ["Environment", "ManagedBy"]
    for tag in expected_tags:
        assert tag in rg.tags, f"Missing expected tag: {tag}"

    print(f"Resource group tags: {rg.tags}")


@pytest.mark.integration
@pytest.mark.azure
@pytest.mark.slow
def test_cost_budget_exists(azure_credentials, test_resource_group):
    """Test that cost budget is configured (if enabled)."""
    # Note: This requires azure-mgmt-consumption package which may not be available
    # This test is marked as slow and optional
    pytest.skip("Cost budget validation requires azure-mgmt-consumption package")


@pytest.mark.integration
@pytest.mark.azure
def test_resource_permissions(azure_credentials, test_resource_group):
    """Test that the service principal has appropriate read permissions."""
    credential = azure_credentials["credential"]
    subscription_id = azure_credentials["subscription_id"]

    client = ResourceManagementClient(credential, subscription_id)

    try:
        # Try to list resources (requires Reader role)
        resources = list(client.resources.list_by_resource_group(test_resource_group))
        assert len(resources) >= 0  # Should succeed with Reader role

        # Try to list resource groups (requires subscription-level Reader)
        resource_groups = list(client.resource_groups.list())
        assert len(resource_groups) > 0

        print("✓ Service principal has appropriate read permissions")
    except Exception as e:
        pytest.fail(f"Permission test failed: {str(e)}")
