"""
Tests for Role-Based Access Control (RBAC).
"""

from topdeck.security.models import ROLE_PERMISSIONS, Permission, Role, User
from topdeck.security.rbac import check_permission


class TestRolePermissions:
    """Test role-permission mappings."""

    def test_admin_has_all_permissions(self):
        """Test that admin role has all permissions."""
        admin_perms = ROLE_PERMISSIONS[Role.ADMIN]

        # Admin should have most permissions
        assert Permission.DISCOVER_RESOURCES in admin_perms
        assert Permission.VIEW_RESOURCES in admin_perms
        assert Permission.ANALYZE_RISK in admin_perms
        assert Permission.VIEW_RISK in admin_perms
        assert Permission.VIEW_TOPOLOGY in admin_perms
        assert Permission.MODIFY_TOPOLOGY in admin_perms
        assert Permission.VIEW_MONITORING in admin_perms
        assert Permission.CONFIGURE_MONITORING in admin_perms
        assert Permission.VIEW_USERS in admin_perms
        assert Permission.MANAGE_USERS in admin_perms

    def test_viewer_has_read_only_permissions(self):
        """Test that viewer role has only read permissions."""
        viewer_perms = ROLE_PERMISSIONS[Role.VIEWER]

        # Viewer should have read permissions
        assert Permission.VIEW_RESOURCES in viewer_perms
        assert Permission.VIEW_RISK in viewer_perms
        assert Permission.VIEW_TOPOLOGY in viewer_perms
        assert Permission.VIEW_MONITORING in viewer_perms

        # Viewer should not have write permissions
        assert Permission.DISCOVER_RESOURCES not in viewer_perms
        assert Permission.MODIFY_TOPOLOGY not in viewer_perms
        assert Permission.CONFIGURE_MONITORING not in viewer_perms
        assert Permission.MANAGE_USERS not in viewer_perms

    def test_operator_has_configuration_permissions(self):
        """Test that operator role can configure but not manage users."""
        operator_perms = ROLE_PERMISSIONS[Role.OPERATOR]

        # Operator should have discovery and configuration
        assert Permission.DISCOVER_RESOURCES in operator_perms
        assert Permission.CONFIGURE_MONITORING in operator_perms
        assert Permission.CONFIGURE_INTEGRATIONS in operator_perms

        # But not user management
        assert Permission.MANAGE_USERS not in operator_perms

    def test_analyst_has_analysis_permissions(self):
        """Test that analyst role has analysis-related permissions."""
        analyst_perms = ROLE_PERMISSIONS[Role.ANALYST]

        # Analyst should have analysis permissions
        assert Permission.ANALYZE_RISK in analyst_perms
        assert Permission.VIEW_RISK in analyst_perms
        assert Permission.VIEW_TOPOLOGY in analyst_perms
        assert Permission.VIEW_MONITORING in analyst_perms

        # But not configuration or discovery
        assert Permission.DISCOVER_RESOURCES not in analyst_perms
        assert Permission.CONFIGURE_MONITORING not in analyst_perms


class TestUserPermissions:
    """Test user permission checking."""

    def test_user_has_role(self):
        """Test checking if user has a specific role."""
        user = User(
            username="test_user",
            roles=[Role.ADMIN, Role.OPERATOR],
        )

        assert user.has_role(Role.ADMIN)
        assert user.has_role(Role.OPERATOR)
        assert not user.has_role(Role.VIEWER)

    def test_user_has_permission_through_role(self):
        """Test that user has permission through their role."""
        user = User(
            username="test_admin",
            roles=[Role.ADMIN],
        )

        # Admin should have all permissions
        assert user.has_permission(Permission.DISCOVER_RESOURCES)
        assert user.has_permission(Permission.MANAGE_USERS)
        assert user.has_permission(Permission.VIEW_AUDIT_LOGS)

    def test_user_without_permission(self):
        """Test that viewer doesn't have admin permissions."""
        user = User(
            username="test_viewer",
            roles=[Role.VIEWER],
        )

        # Viewer should have read permissions
        assert user.has_permission(Permission.VIEW_RESOURCES)

        # But not write permissions
        assert not user.has_permission(Permission.DISCOVER_RESOURCES)
        assert not user.has_permission(Permission.MANAGE_USERS)

    def test_user_with_multiple_roles(self):
        """Test user with multiple roles gets combined permissions."""
        user = User(
            username="test_multi",
            roles=[Role.VIEWER, Role.ANALYST],
        )

        # Should have all permissions from both roles
        assert user.has_permission(Permission.VIEW_RESOURCES)  # From viewer
        assert user.has_permission(Permission.ANALYZE_RISK)  # From analyst

    def test_get_all_permissions(self):
        """Test getting all permissions for a user."""
        user = User(
            username="test_user",
            roles=[Role.VIEWER, Role.ANALYST],
        )

        all_perms = user.get_all_permissions()

        # Should be a set
        assert isinstance(all_perms, set)

        # Should include permissions from both roles
        assert Permission.VIEW_RESOURCES in all_perms
        assert Permission.ANALYZE_RISK in all_perms


class TestCheckPermission:
    """Test check_permission function."""

    def test_check_permission_granted(self):
        """Test checking permission that user has."""
        user = User(
            username="admin",
            roles=[Role.ADMIN],
        )

        assert check_permission(user, Permission.DISCOVER_RESOURCES)
        assert check_permission(user, Permission.MANAGE_USERS)

    def test_check_permission_denied(self):
        """Test checking permission that user doesn't have."""
        user = User(
            username="viewer",
            roles=[Role.VIEWER],
        )

        assert not check_permission(user, Permission.DISCOVER_RESOURCES)
        assert not check_permission(user, Permission.MANAGE_USERS)


class TestServiceAccountRole:
    """Test service account role for CI/CD."""

    def test_service_account_has_api_permissions(self):
        """Test that service account can use API for CI/CD."""
        service_perms = ROLE_PERMISSIONS[Role.SERVICE_ACCOUNT]

        # Should have discovery and analysis for CI/CD
        assert Permission.DISCOVER_RESOURCES in service_perms
        assert Permission.VIEW_RESOURCES in service_perms
        assert Permission.ANALYZE_RISK in service_perms

        # But not user management or configuration
        assert Permission.MANAGE_USERS not in service_perms
        assert Permission.CONFIGURE_MONITORING not in service_perms
