"""
Authentication and JWT token handling.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from topdeck.common.config import settings

from .models import TokenData, User, UserInDB

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# JWT settings (from config)
SECRET_KEY = settings.secret_key or "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes or 60


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to verify against

    Returns:
        True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def get_user_from_db(username: str) -> UserInDB | None:
    """
    Get user from database.

    In a real implementation, this would query Neo4j or another database.
    For now, we'll use a simple in-memory store.

    Args:
        username: The username to look up

    Returns:
        UserInDB object if found, None otherwise
    """
    # TODO: Implement actual database lookup
    # This is a placeholder implementation
    from .models import Role

    # Example users (in production, store in Neo4j)
    fake_users_db = {
        "admin": UserInDB(
            username="admin",
            email="admin@topdeck.local",
            full_name="Admin User",
            disabled=False,
            roles=[Role.ADMIN],
            hashed_password=get_password_hash("admin123"),  # Change in production
        ),
        "operator": UserInDB(
            username="operator",
            email="operator@topdeck.local",
            full_name="Operator User",
            disabled=False,
            roles=[Role.OPERATOR],
            hashed_password=get_password_hash("operator123"),
        ),
        "analyst": UserInDB(
            username="analyst",
            email="analyst@topdeck.local",
            full_name="Analyst User",
            disabled=False,
            roles=[Role.ANALYST],
            hashed_password=get_password_hash("analyst123"),
        ),
        "viewer": UserInDB(
            username="viewer",
            email="viewer@topdeck.local",
            full_name="Viewer User",
            disabled=False,
            roles=[Role.VIEWER],
            hashed_password=get_password_hash("viewer123"),
        ),
    }

    return fake_users_db.get(username)


async def authenticate_user(username: str, password: str) -> UserInDB | None:
    """
    Authenticate a user with username and password.

    Args:
        username: The username
        password: The plain text password

    Returns:
        UserInDB if authentication succeeds, None otherwise
    """
    user = await get_user_from_db(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from JWT token.

    Args:
        token: JWT token from Authorization header

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = await get_user_from_db(token_data.username)
    if user is None:
        raise credentials_exception

    # Update last login
    user.last_login = datetime.utcnow()

    return User(**user.model_dump())


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user (not disabled).

    Args:
        current_user: The current user from token

    Returns:
        User object

    Raises:
        HTTPException: If user is disabled
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
