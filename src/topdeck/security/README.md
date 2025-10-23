# TopDeck Security Module

**Version**: 1.0  
**Last Updated**: 2025-10-22

---

## Overview

The TopDeck security module provides comprehensive authentication, authorization, and audit logging capabilities for the platform. It implements Role-Based Access Control (RBAC) with JWT tokens and tracks all security-relevant events.

---

## Components

### 1. Authentication (`auth.py`)

Handles user authentication and JWT token management.

**Features**:
- Password hashing with bcrypt
- JWT token creation and validation
- OAuth2 password flow
- Token expiration
- User session management

**Example**:
```python
from topdeck.security import create_access_token, authenticate_user

# Authenticate user
user = await authenticate_user("username", "password")
if user:
    # Create JWT token
    token = create_access_token(
        data={"sub": user.username, "roles": [r.value for r in user.roles]}
    )
```

### 2. Models (`models.py`)

Data models for users, roles, and permissions.

**Built-in Roles**:
- **Admin**: Full system access
- **Operator**: Configuration and discovery access
- **Analyst**: Read-only analysis access
- **Viewer**: Read-only viewing access
- **Service Account**: API access for CI/CD

**Permissions** (15+ granular permissions):
- `discover:resources` - Discover cloud resources
- `view:resources` - View discovered resources
- `analyze:risk` - Analyze risk
- `view:risk` - View risk assessments
- `view:topology` - View topology
- `modify:topology` - Modify topology
- `view:monitoring` - View monitoring data
- `configure:monitoring` - Configure monitoring
- `view:integrations` - View integrations
- `configure:integrations` - Configure integrations
- `view:users` - View user list
- `manage:users` - Create/update/delete users
- `view:config` - View configuration
- `modify:config` - Modify configuration
- `view:audit_logs` - View audit logs

### 3. RBAC (`rbac.py`)

Role-Based Access Control implementation.

**Usage**:
```python
from fastapi import Depends
from topdeck.security import Permission, Role, require_permission, require_role

# Require specific permission
@app.get("/resources", dependencies=[Depends(require_permission(Permission.VIEW_RESOURCES))])
async def list_resources():
    ...

# Require specific role
@app.get("/admin", dependencies=[Depends(require_role(Role.ADMIN))])
async def admin_panel():
    ...

# Require any of multiple permissions
@app.get("/data", dependencies=[Depends(require_any_permission(
    Permission.VIEW_RESOURCES,
    Permission.VIEW_MONITORING
))])
async def get_data():
    ...
```

### 4. Audit Logging (`audit.py`)

Comprehensive audit logging for security events.

**Event Types** (20+):
- Authentication: login, logout, token creation
- Authorization: permission grants/denials, role changes
- Resource access: view, create, update, delete
- Discovery: started, completed, failed
- Risk analysis: analysis performed
- Configuration: config viewed/updated
- User management: user created/updated/deleted
- Security: suspicious activity, rate limit exceeded

**Example**:
```python
from topdeck.security.audit import log_login, log_resource_access, log_config_change

# Log login attempt
log_login("username", success=True, ip_address="192.168.1.100")

# Log resource access
log_resource_access("username", "resource", "resource-id", "view")

# Log config change
log_config_change("admin", "rate_limit", old_value=60, new_value=100)
```

---

## Quick Start

### 1. Configuration

Add to your `.env` file:

```bash
# Security Configuration
SECRET_KEY=your-256-bit-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENABLE_RBAC=true
ENABLE_AUDIT_LOGGING=true
AUDIT_LOG_FILE=/var/log/topdeck/audit.log
```

### 2. Enable Authentication

Add to your FastAPI app:

```python
from fastapi import FastAPI, Depends
from topdeck.security import get_current_active_user, User
from topdeck.api.routes import auth

app = FastAPI()

# Include auth routes
app.include_router(auth.router)

# Protect your routes
@app.get("/protected", dependencies=[Depends(get_current_active_user)])
async def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"user": current_user.username}
```

### 3. Add Permission Checks

```python
from fastapi import Depends
from topdeck.security import Permission, require_permission

@app.post("/discover", dependencies=[Depends(require_permission(Permission.DISCOVER_RESOURCES))])
async def start_discovery():
    # Only users with discover:resources permission can access
    ...
```

---

## API Endpoints

### Authentication

#### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Get Current User
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <token>"
```

#### Get My Permissions
```bash
curl -X GET http://localhost:8000/api/auth/me/permissions \
  -H "Authorization: Bearer <token>"
```

### User Management (Admin only)

#### List Users
```bash
curl -X GET http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer <admin-token>"
```

#### List Roles
```bash
curl -X GET http://localhost:8000/api/auth/roles \
  -H "Authorization: Bearer <token>"
```

---

## Default Users

For development and testing, the following default users are available:

| Username | Password | Roles | Use Case |
|----------|----------|-------|----------|
| admin | admin123 | Admin | Full system access |
| operator | operator123 | Operator | Configuration and discovery |
| analyst | analyst123 | Analyst | Risk analysis and reporting |
| viewer | viewer123 | Viewer | Read-only access |

**⚠️ IMPORTANT**: Change these passwords in production!

---

## Security Best Practices

### 1. Password Management

```python
from topdeck.security import get_password_hash, verify_password

# Always hash passwords before storing
hashed_password = get_password_hash(plain_password)

# Verify passwords during login
is_valid = verify_password(plain_password, hashed_password)
```

### 2. Token Security

- Use HTTPS in production
- Set appropriate token expiration (default: 60 minutes)
- Rotate JWT secret keys regularly
- Store tokens securely on client-side (httpOnly cookies preferred)

### 3. Audit Logging

- Review audit logs regularly
- Set up alerts for suspicious activity
- Archive audit logs to secure, immutable storage
- Monitor for failed login attempts

### 4. Role Assignment

- Follow principle of least privilege
- Use Service Account role for CI/CD pipelines
- Review user roles quarterly
- Remove access promptly when users leave

---

## Production Deployment

### 1. Generate Secure Secret Key

```python
import secrets

# Generate 256-bit secret key
secret_key = secrets.token_urlsafe(32)
print(f"SECRET_KEY={secret_key}")
```

### 2. Configure Environment

```bash
# Production .env
SECRET_KEY=<generated-secret-key>
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENABLE_RBAC=true
ENABLE_AUDIT_LOGGING=true
AUDIT_LOG_FILE=/var/log/topdeck/audit.log
```

### 3. Set Up Audit Log Rotation

```bash
# /etc/logrotate.d/topdeck-audit
/var/log/topdeck/audit.log {
    daily
    rotate 90
    compress
    delaycompress
    notifempty
    create 0640 topdeck topdeck
    sharedscripts
    postrotate
        systemctl reload topdeck
    endscript
}
```

### 4. Monitor Audit Logs

```bash
# Watch for suspicious activity
tail -f /var/log/topdeck/audit.log | grep "CRITICAL"

# Failed login attempts
tail -f /var/log/topdeck/audit.log | grep "LOGIN_FAILURE"

# Permission denials
tail -f /var/log/topdeck/audit.log | grep "PERMISSION_DENIED"
```

---

## Testing

### Run Tests

```bash
# Run all security tests
pytest tests/security/ -v

# Run specific test modules
pytest tests/security/test_auth.py -v
pytest tests/security/test_rbac.py -v

# Run with coverage
pytest tests/security/ --cov=topdeck.security --cov-report=term-missing
```

### Manual Testing

```bash
# 1. Start API server
make run

# 2. Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# 3. Test authenticated endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me

# 4. Test permission check
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/topology/resources
```

---

## Troubleshooting

### Issue: "Could not validate credentials"

**Cause**: Invalid or expired JWT token

**Solution**:
- Check token expiration
- Verify SECRET_KEY is consistent
- Ensure Authorization header format: `Bearer <token>`

### Issue: "Permission denied"

**Cause**: User lacks required permission

**Solution**:
- Check user's roles: `GET /api/auth/me/permissions`
- Verify role has required permission
- Update user roles if needed

### Issue: Audit logs not appearing

**Cause**: Audit logging disabled or log file not writable

**Solution**:
```bash
# 1. Check configuration
echo $ENABLE_AUDIT_LOGGING

# 2. Check log file permissions
ls -la /var/log/topdeck/audit.log

# 3. Create log directory if needed
sudo mkdir -p /var/log/topdeck
sudo chown topdeck:topdeck /var/log/topdeck
```

---

## Migration from No Auth

If upgrading from a version without authentication:

1. **Add environment variables** to `.env`
2. **Include auth router** in main.py
3. **Add dependencies** to protected routes
4. **Create initial admin user**
5. **Test thoroughly** before deploying

---

## Future Enhancements

- OAuth2/OIDC integration (Azure AD, Okta, Auth0)
- API key authentication for service accounts
- Multi-factor authentication (MFA)
- Session management and revocation
- Rate limiting per user
- Password complexity requirements
- Account lockout after failed attempts

---

## Support

For issues or questions:
- Documentation: `/docs/PRODUCTION_DEPLOYMENT_GUIDE.md`
- GitHub Issues: https://github.com/MattVerwey/TopDeck/issues

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-22
