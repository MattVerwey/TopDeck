"""
Authentication and authorization API routes.
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from topdeck.security import (
    Permission,
    Role,
    Token,
    User,
    create_access_token,
    get_current_active_user,
    require_permission,
    require_role,
)
from topdeck.security.auth import ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint to obtain JWT access token.

    Args:
        form_data: OAuth2 password request form (username and password)

    Returns:
        JWT access token

    Raises:
        HTTPException: If authentication fails
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": [role.value for role in user.roles]},
        expires_delta=access_token_expires,
    )

    logger.info(f"User {user.username} logged in successfully")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User object with current user's information
    """
    return current_user


@router.get("/me/permissions")
async def read_my_permissions(current_user: User = Depends(get_current_active_user)):
    """
    Get current user's permissions.

    Args:
        current_user: Current authenticated user

    Returns:
        List of permissions
    """
    permissions = current_user.get_all_permissions()
    return {
        "username": current_user.username,
        "roles": current_user.roles,
        "permissions": [p.value for p in permissions],
    }


@router.get("/users", dependencies=[Depends(require_permission(Permission.VIEW_USERS))])
async def list_users(current_user: User = Depends(get_current_active_user)):
    """
    List all users (requires VIEW_USERS permission).

    Args:
        current_user: Current authenticated user

    Returns:
        List of users

    Note:
        This is a placeholder implementation. In production, query Neo4j.
    """
    # TODO: Implement actual database query
    return {
        "users": [
            {"username": "admin", "roles": ["admin"]},
            {"username": "operator", "roles": ["operator"]},
            {"username": "analyst", "roles": ["analyst"]},
            {"username": "viewer", "roles": ["viewer"]},
        ]
    }


@router.get("/roles")
async def list_roles(current_user: User = Depends(get_current_active_user)):
    """
    List all available roles.

    Args:
        current_user: Current authenticated user

    Returns:
        List of roles with their permissions
    """
    from topdeck.security.models import ROLE_PERMISSIONS

    roles_info = []
    for role in Role:
        permissions = ROLE_PERMISSIONS.get(role, [])
        roles_info.append(
            {
                "role": role.value,
                "permissions": [p.value for p in permissions],
            }
        )

    return {"roles": roles_info}


@router.get(
    "/permissions",
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def list_permissions():
    """
    List all available permissions (admin only).

    Returns:
        List of all permissions in the system
    """
    return {"permissions": [p.value for p in Permission]}
