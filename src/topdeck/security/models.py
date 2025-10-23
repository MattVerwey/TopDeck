"""
Security models for authentication and authorization.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Permission(str, Enum):
    """
    Permissions for different operations in TopDeck.
    """

    # Discovery permissions
    DISCOVER_RESOURCES = "discover:resources"
    VIEW_RESOURCES = "view:resources"

    # Risk analysis permissions
    ANALYZE_RISK = "analyze:risk"
    VIEW_RISK = "view:risk"

    # Topology permissions
    VIEW_TOPOLOGY = "view:topology"
    MODIFY_TOPOLOGY = "modify:topology"

    # Monitoring permissions
    VIEW_MONITORING = "view:monitoring"
    CONFIGURE_MONITORING = "configure:monitoring"

    # Integration permissions
    VIEW_INTEGRATIONS = "view:integrations"
    CONFIGURE_INTEGRATIONS = "configure:integrations"

    # User management permissions
    VIEW_USERS = "view:users"
    MANAGE_USERS = "manage:users"

    # Configuration permissions
    VIEW_CONFIG = "view:config"
    MODIFY_CONFIG = "modify:config"

    # Audit permissions
    VIEW_AUDIT_LOGS = "view:audit_logs"


class Role(str, Enum):
    """
    Built-in roles with predefined permissions.
    """

    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SERVICE_ACCOUNT = "service_account"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, list[Permission]] = {
    Role.ADMIN: [
        # All permissions
        Permission.DISCOVER_RESOURCES,
        Permission.VIEW_RESOURCES,
        Permission.ANALYZE_RISK,
        Permission.VIEW_RISK,
        Permission.VIEW_TOPOLOGY,
        Permission.MODIFY_TOPOLOGY,
        Permission.VIEW_MONITORING,
        Permission.CONFIGURE_MONITORING,
        Permission.VIEW_INTEGRATIONS,
        Permission.CONFIGURE_INTEGRATIONS,
        Permission.VIEW_USERS,
        Permission.MANAGE_USERS,
        Permission.VIEW_CONFIG,
        Permission.MODIFY_CONFIG,
        Permission.VIEW_AUDIT_LOGS,
    ],
    Role.OPERATOR: [
        # Can discover, view, and configure but not manage users
        Permission.DISCOVER_RESOURCES,
        Permission.VIEW_RESOURCES,
        Permission.ANALYZE_RISK,
        Permission.VIEW_RISK,
        Permission.VIEW_TOPOLOGY,
        Permission.VIEW_MONITORING,
        Permission.CONFIGURE_MONITORING,
        Permission.VIEW_INTEGRATIONS,
        Permission.CONFIGURE_INTEGRATIONS,
        Permission.VIEW_CONFIG,
    ],
    Role.ANALYST: [
        # Read access to analysis and monitoring
        Permission.VIEW_RESOURCES,
        Permission.ANALYZE_RISK,
        Permission.VIEW_RISK,
        Permission.VIEW_TOPOLOGY,
        Permission.VIEW_MONITORING,
        Permission.VIEW_INTEGRATIONS,
    ],
    Role.VIEWER: [
        # Read-only access
        Permission.VIEW_RESOURCES,
        Permission.VIEW_RISK,
        Permission.VIEW_TOPOLOGY,
        Permission.VIEW_MONITORING,
    ],
    Role.SERVICE_ACCOUNT: [
        # Automated access for CI/CD
        Permission.DISCOVER_RESOURCES,
        Permission.VIEW_RESOURCES,
        Permission.ANALYZE_RISK,
        Permission.VIEW_RISK,
        Permission.VIEW_TOPOLOGY,
    ],
}


class User(BaseModel):
    """User model."""

    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool = False
    roles: list[Role] = Field(default_factory=lambda: [Role.VIEWER])
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def has_role(self, role: Role) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission through any of their roles."""
        for role in self.roles:
            if permission in ROLE_PERMISSIONS.get(role, []):
                return True
        return False

    def get_all_permissions(self) -> set[Permission]:
        """Get all permissions for this user."""
        permissions: set[Permission] = set()
        for role in self.roles:
            permissions.update(ROLE_PERMISSIONS.get(role, []))
        return permissions


class UserInDB(User):
    """User model with hashed password for database storage."""

    hashed_password: str


class TokenData(BaseModel):
    """Token payload data."""

    username: str | None = None
    roles: list[Role] = Field(default_factory=list)


class Token(BaseModel):
    """OAuth2 token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class CreateUserRequest(BaseModel):
    """Request to create a new user."""

    username: str
    email: str
    full_name: str | None = None
    password: str
    roles: list[Role] = Field(default_factory=lambda: [Role.VIEWER])


class UpdateUserRequest(BaseModel):
    """Request to update a user."""

    email: str | None = None
    full_name: str | None = None
    roles: list[Role] | None = None
    disabled: bool | None = None
