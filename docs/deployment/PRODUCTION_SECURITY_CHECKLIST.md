# Production Security Checklist

This checklist ensures TopDeck is deployed with proper encryption and security measures.

## 🔒 Encryption Configuration

### ✅ Pre-Deployment Checklist

- [ ] **Generate or obtain SSL/TLS certificates** from a trusted Certificate Authority (Let's Encrypt, DigiCert, etc.)
- [ ] **Enable HTTPS for API Server** (`SSL_ENABLED=true`)
- [ ] **Enable Neo4j encryption** (`NEO4J_ENCRYPTED=true` or use `bolt+s://` URI)
- [ ] **Enable Redis encryption** (`REDIS_SSL=true`)
- [ ] **Enable RabbitMQ encryption** (`RABBITMQ_SSL=true`)
- [ ] **Configure secret key** (replace default `SECRET_KEY` with strong random value)
- [ ] **Store credentials securely** (use Azure Key Vault, AWS Secrets Manager, or HashiCorp Vault)
- [ ] **Enable volume encryption** (Azure Disk Encryption, AWS EBS encryption, or filesystem encryption)
- [ ] **Configure firewall rules** to block unencrypted ports (7687, 6379, 5672)
- [ ] **Set up certificate rotation** procedures
- [ ] **Enable audit logging** (`ENABLE_AUDIT_LOGGING=true`)
- [ ] **Review and test backup procedures**

---

## 📋 Environment Variables Template (Production)

Create a `.env` file with the following configuration:

```bash
# ============================================
# Application Configuration
# ============================================
APP_ENV=production
APP_PORT=443
SECRET_KEY=<GENERATE_STRONG_RANDOM_KEY_32_CHARS_MIN>

# ============================================
# SSL/TLS for API Server
# ============================================
SSL_ENABLED=true
SSL_KEYFILE=/etc/topdeck/ssl/server.key
SSL_CERTFILE=/etc/topdeck/ssl/server.crt

# ============================================
# Neo4j - ENCRYPTED
# ============================================
NEO4J_URI=bolt+s://your-neo4j-host.com:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<FROM_KEY_VAULT>
NEO4J_ENCRYPTED=true

# ============================================
# Redis - ENCRYPTED
# ============================================
REDIS_HOST=your-redis-host.com
REDIS_PORT=6380
REDIS_PASSWORD=<FROM_KEY_VAULT>
REDIS_DB=0
REDIS_SSL=true
REDIS_SSL_CERT_REQS=required

# ============================================
# RabbitMQ - ENCRYPTED
# ============================================
RABBITMQ_HOST=your-rabbitmq-host.com
RABBITMQ_PORT=5671
RABBITMQ_USERNAME=topdeck
RABBITMQ_PASSWORD=<FROM_KEY_VAULT>
RABBITMQ_SSL=true

# ============================================
# Cloud Provider Credentials
# ============================================
# Azure
AZURE_TENANT_ID=<FROM_KEY_VAULT>
AZURE_CLIENT_ID=<FROM_KEY_VAULT>
AZURE_CLIENT_SECRET=<FROM_KEY_VAULT>
AZURE_SUBSCRIPTION_ID=<FROM_KEY_VAULT>

# AWS
AWS_ACCESS_KEY_ID=<FROM_SECRETS_MANAGER>
AWS_SECRET_ACCESS_KEY=<FROM_SECRETS_MANAGER>
AWS_REGION=us-east-1

# GitHub
GITHUB_TOKEN=<FROM_SECRETS_MANAGER>
GITHUB_ORGANIZATION=your-org

# ============================================
# Security Configuration
# ============================================
ENABLE_RBAC=true
ENABLE_AUDIT_LOGGING=true
AUDIT_LOG_FILE=/var/log/topdeck/audit.log
```

---

## 🔐 Generating Secrets

### Generate Strong Secret Key

```bash
# Linux/macOS
openssl rand -base64 32

# Or using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Generate Self-Signed SSL Certificates (Testing Only)

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout server.key \
  -out server.crt \
  -days 365 \
  -subj "/CN=yourdomain.com"
```

### Get Free SSL Certificates (Production)

Use [Let's Encrypt](https://letsencrypt.org/) with Certbot:

```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Certificates will be in:
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
```

---

## 🛡️ Cloud Provider Security

### Azure

```bash
# Enable disk encryption
az disk update \
  --name myDisk \
  --resource-group myResourceGroup \
  --encryption-type EncryptionAtRestWithPlatformKey

# Store secrets in Key Vault
az keyvault secret set \
  --vault-name myKeyVault \
  --name neo4j-password \
  --value "your-password"

# Retrieve secrets
az keyvault secret show \
  --vault-name myKeyVault \
  --name neo4j-password \
  --query value -o tsv
```

### AWS

```bash
# Enable EBS encryption
aws ec2 enable-ebs-encryption-by-default

# Store secrets in Secrets Manager
aws secretsmanager create-secret \
  --name topdeck/neo4j-password \
  --secret-string "your-password"

# Retrieve secrets
aws secretsmanager get-secret-value \
  --secret-id topdeck/neo4j-password \
  --query SecretString \
  --output text
```

---

## 🔍 Validation

### Test Encrypted Connections

```bash
# Test API HTTPS
curl https://yourdomain.com/health

# Test Neo4j encryption
echo "RETURN 1" | cypher-shell -a bolt+s://your-host:7687 -u neo4j -p password

# Test Redis SSL
redis-cli --tls --cacert ca.crt -h your-host -p 6380 PING

# Verify certificate
openssl s_client -connect yourdomain.com:443 -showcerts
```

### Startup Security Checks

TopDeck validates security on startup. Watch for these messages:

```
✅ SSL/TLS: Enabled
✅ Neo4j: Encrypted connection (bolt+s://)
✅ Redis: SSL enabled
✅ RabbitMQ: SSL enabled
```

Warning messages indicate security issues:
```
⚠️  WARNING: Running in production without SSL/TLS encryption!
⚠️  WARNING: Production environment using unencrypted Neo4j connection
⚠️  WARNING: Production environment using unencrypted Redis connection
```

---

## 🚨 Security Incidents

If credentials are compromised:

1. **Immediately rotate all affected credentials**
2. **Review audit logs** for unauthorized access
3. **Check for data exfiltration**
4. **Update firewall rules** if needed
5. **Notify security team**
6. **Document incident** for post-mortem

---

## 📊 Monitoring

Monitor these security metrics:

- **Failed authentication attempts**
- **Unusual API access patterns**
- **Certificate expiration dates**
- **Disk encryption status**
- **Audit log anomalies**

Set up alerts for:
- Certificate expiring in < 30 days
- Multiple failed login attempts
- Access from unusual IP addresses
- Unencrypted connection attempts

---

## 📚 Related Documentation

- **[Security & Encryption Guide](SECURITY_ENCRYPTION.md)** - Comprehensive encryption documentation
- **[Deployment Readiness](../DEPLOYMENT_READINESS.md)** - Full deployment guide
- **[Contributing Security](../CONTRIBUTING.md#security)** - Security contribution guidelines

---

## ✅ Quick Validation Script

Save this as `validate_security.sh`:

```bash
#!/bin/bash
# Validate TopDeck security configuration

echo "🔍 Validating TopDeck security configuration..."
echo

# Check environment variables
check_var() {
    if [ -z "${!1}" ]; then
        echo "❌ $1 is not set"
        return 1
    else
        echo "✅ $1 is set"
        return 0
    fi
}

# Check SSL enabled
if [ "$SSL_ENABLED" = "true" ]; then
    echo "✅ SSL_ENABLED=true"
    check_var "SSL_KEYFILE"
    check_var "SSL_CERTFILE"
else
    echo "⚠️  SSL_ENABLED=false (not recommended for production)"
fi

# Check Neo4j encryption
if [[ "$NEO4J_URI" == *"+s://"* ]] || [ "$NEO4J_ENCRYPTED" = "true" ]; then
    echo "✅ Neo4j encryption enabled"
else
    echo "⚠️  Neo4j encryption disabled"
fi

# Check Redis SSL
if [ "$REDIS_SSL" = "true" ]; then
    echo "✅ Redis SSL enabled"
else
    echo "⚠️  Redis SSL disabled"
fi

# Check RabbitMQ SSL
if [ "$RABBITMQ_SSL" = "true" ]; then
    echo "✅ RabbitMQ SSL enabled"
else
    echo "⚠️  RabbitMQ SSL disabled"
fi

# Check secret key
if [ "$SECRET_KEY" = "change-this-secret-key-in-production" ]; then
    echo "❌ Using default SECRET_KEY (CRITICAL)"
else
    echo "✅ Custom SECRET_KEY configured"
fi

echo
echo "Validation complete!"
```

Run with:
```bash
source .env && bash validate_security.sh
```

---

**Last Updated:** 2025-10-30
