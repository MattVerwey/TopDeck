"""
Role-Based Access Control (RBAC) implementation.
"""

import logging
from typing import Callable

from fastapi import Depends, HTTPException, status

from .auth import get_current_active_user
from .models import Permission, Role, User

logger = logging.getLogger(__name__)


def check_permission(user: User, permission: Permission) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        user: The user to check
        permission: The permission to check for

    Returns:
        True if user has permission, False otherwise
    """
    return user.has_permission(permission)


def require_permission(permission: Permission) -> Callable:
    """
    Dependency that requires a specific permission.

    Usage:
        @app.get("/resources", dependencies=[Depends(require_permission(Permission.VIEW_RESOURCES))])
        async def list_resources():
            ...

    Args:
        permission: The required permission

    Returns:
        Dependency function
    """

    async def permission_checker(user: User = Depends(get_current_active_user)) -> User:
        if not check_permission(user, permission):
            logger.warning(
                f"Permission denied: User {user.username} does not have {permission.value}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required",
            )
        return user

    return permission_checker


def require_role(role: Role) -> Callable:
    """
    Dependency that requires a specific role.

    Usage:
        @app.get("/admin", dependencies=[Depends(require_role(Role.ADMIN))])
        async def admin_endpoint():
            ...

    Args:
        role: The required role

    Returns:
        Dependency function
    """

    async def role_checker(user: User = Depends(get_current_active_user)) -> User:
        if not user.has_role(role):
            logger.warning(f"Access denied: User {user.username} does not have role {role.value}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {role.value} role required",
            )
        return user

    return role_checker


def require_any_permission(*permissions: Permission) -> Callable:
    """
    Dependency that requires any one of the specified permissions.

    Args:
        permissions: The permissions (user needs at least one)

    Returns:
        Dependency function
    """

    async def permission_checker(user: User = Depends(get_current_active_user)) -> User:
        for permission in permissions:
            if check_permission(user, permission):
                return user

        logger.warning(
            f"Permission denied: User {user.username} does not have any of {[p.value for p in permissions]}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: insufficient permissions",
        )

    return permission_checker


def require_all_permissions(*permissions: Permission) -> Callable:
    """
    Dependency that requires all of the specified permissions.

    Args:
        permissions: The permissions (user needs all of them)

    Returns:
        Dependency function
    """

    async def permission_checker(user: User = Depends(get_current_active_user)) -> User:
        for permission in permissions:
            if not check_permission(user, permission):
                logger.warning(
                    f"Permission denied: User {user.username} missing {permission.value}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value} required",
                )
        return user

    return permission_checker
