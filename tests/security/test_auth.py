"""
Tests for authentication module.
"""

from datetime import timedelta

import pytest
from jose import jwt

from topdeck.security.auth import (
    ALGORITHM,
    SECRET_KEY,
    authenticate_user,
    create_access_token,
    get_password_hash,
    verify_password,
)
from topdeck.security.models import Role


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_password_hashing(self):
        """Test that password hashing and verification work."""
        plain_password = "test_password_123"
        hashed = get_password_hash(plain_password)

        # Hashed password should be different from plain text
        assert hashed != plain_password

        # Should verify correctly
        assert verify_password(plain_password, hashed)

        # Wrong password should not verify
        assert not verify_password("wrong_password", hashed)

    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2

        # But both should verify
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test creating a JWT access token."""
        data = {"sub": "testuser", "roles": ["admin"]}
        token = create_access_token(data)

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_create_token_with_custom_expiration(self):
        """Test creating token with custom expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta)

        # Should create valid token
        assert isinstance(token, str)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"

    def test_token_includes_roles(self):
        """Test that token includes user roles."""
        data = {"sub": "admin", "roles": ["admin", "operator"]}
        token = create_access_token(data)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "roles" in payload
        assert payload["roles"] == ["admin", "operator"]


class TestAuthentication:
    """Test user authentication."""

    @pytest.mark.asyncio
    async def test_authenticate_valid_user(self):
        """Test authenticating with valid credentials."""
        # Using the default admin user
        user = await authenticate_user("admin", "admin123")

        assert user is not None
        assert user.username == "admin"
        assert Role.ADMIN in user.roles

    @pytest.mark.asyncio
    async def test_authenticate_invalid_username(self):
        """Test authentication with invalid username."""
        user = await authenticate_user("nonexistent", "password")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_invalid_password(self):
        """Test authentication with invalid password."""
        user = await authenticate_user("admin", "wrong_password")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_different_roles(self):
        """Test authenticating users with different roles."""
        # Test operator
        operator = await authenticate_user("operator", "operator123")
        assert operator is not None
        assert Role.OPERATOR in operator.roles

        # Test analyst
        analyst = await authenticate_user("analyst", "analyst123")
        assert analyst is not None
        assert Role.ANALYST in analyst.roles

        # Test viewer
        viewer = await authenticate_user("viewer", "viewer123")
        assert viewer is not None
        assert Role.VIEWER in viewer.roles
