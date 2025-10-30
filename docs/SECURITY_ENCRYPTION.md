# Security: Data Encryption at Rest and In Transit

This document describes TopDeck's encryption capabilities for securing data at rest and in transit.

## Overview

TopDeck supports encryption for all data connections:

- ✅ **Data in Transit**: TLS/SSL encryption for API, Neo4j, Redis, and RabbitMQ
- ✅ **Data at Rest**: Relies on underlying database encryption (Neo4j, Redis, RabbitMQ)
- ✅ **API Security**: HTTPS support with custom SSL certificates
- ✅ **Credential Protection**: Secure handling of cloud credentials and API keys

## Table of Contents

1. [Data in Transit Encryption](#data-in-transit-encryption)
2. [Data at Rest Encryption](#data-at-rest-encryption)
3. [Configuration](#configuration)
4. [Production Deployment](#production-deployment)
5. [Troubleshooting](#troubleshooting)

---

## Data in Transit Encryption

### API Server (HTTPS)

#### Development (HTTP)
```bash
# Default development setup - HTTP only
APP_ENV=development
SSL_ENABLED=false
```

#### Production (HTTPS)
```bash
# Enable HTTPS with SSL certificates
APP_ENV=production
SSL_ENABLED=true
SSL_KEYFILE=/path/to/server.key
SSL_CERTFILE=/path/to/server.crt
```

**Generating Self-Signed Certificates (for testing only):**
```bash
# Generate private key and certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout server.key \
  -out server.crt \
  -days 365 \
  -subj "/CN=localhost"
```

**⚠️ Important:** Use certificates from a trusted CA (Let's Encrypt, DigiCert, etc.) in production.

### Neo4j Database Encryption

Neo4j supports encrypted connections using the `bolt+s://` or `neo4j+s://` protocols.

#### Unencrypted (Development Only)
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_ENCRYPTED=false
```

#### Encrypted Connection
```bash
# Option 1: Use bolt+s:// URI directly
NEO4J_URI=bolt+s://your-neo4j-host:7687

# Option 2: Enable encryption flag (auto-upgrades bolt:// to bolt+s://)
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_ENCRYPTED=true
```

**Neo4j Server Configuration:**

To enable encryption on Neo4j server, configure in `neo4j.conf`:
```conf
# Enable TLS/SSL
dbms.ssl.policy.bolt.enabled=true
dbms.ssl.policy.bolt.base_directory=certificates/bolt

# Certificate paths
dbms.ssl.policy.bolt.private_key=private.key
dbms.ssl.policy.bolt.public_certificate=public.crt
```

### Redis Cache Encryption

Redis supports TLS/SSL encryption for connections.

#### Unencrypted (Development Only)
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_SSL=false
```

#### Encrypted Connection
```bash
REDIS_HOST=your-redis-host
REDIS_PORT=6380  # Typically 6380 for SSL
REDIS_SSL=true
REDIS_SSL_CERT_REQS=required  # Options: none, optional, required
```

**Redis Server Configuration:**

To enable TLS on Redis server:
```bash
# redis.conf
port 0  # Disable plain text port
tls-port 6380
tls-cert-file /path/to/redis.crt
tls-key-file /path/to/redis.key
tls-ca-cert-file /path/to/ca.crt
```

### RabbitMQ Message Queue Encryption

RabbitMQ supports TLS/SSL encryption for AMQP connections.

#### Unencrypted (Development Only)
```bash
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_SSL=false
```

#### Encrypted Connection
```bash
RABBITMQ_HOST=your-rabbitmq-host
RABBITMQ_PORT=5671  # Standard SSL port
RABBITMQ_SSL=true
```

**RabbitMQ Server Configuration:**

To enable TLS in RabbitMQ, add to `rabbitmq.conf`:
```ini
listeners.ssl.default = 5671
ssl_options.cacertfile = /path/to/ca_certificate.pem
ssl_options.certfile   = /path/to/server_certificate.pem
ssl_options.keyfile    = /path/to/server_key.pem
ssl_options.verify     = verify_peer
ssl_options.fail_if_no_peer_cert = false
```

---

## Data at Rest Encryption

TopDeck relies on the underlying databases for data-at-rest encryption. Configure encryption at the infrastructure level:

### Neo4j Data at Rest

Neo4j Enterprise Edition supports transparent encryption at rest:

```conf
# neo4j.conf - Enterprise Edition only
dbms.security.encryption.enabled=true
dbms.security.encryption.key_provider=file
dbms.security.encryption.key_file=/path/to/encryption.key
```

For open-source deployments, use:
- **Filesystem encryption**: LUKS, dm-crypt (Linux), BitLocker (Windows), FileVault (macOS)
- **Volume encryption**: Cloud provider volume encryption (Azure Disk Encryption, AWS EBS encryption)

### Redis Data at Rest

Redis does not natively support encryption at rest. Use:
- **Filesystem encryption**: Encrypt the Redis data directory
- **Cloud volume encryption**: Enable encryption on cloud storage volumes

### Environment Variables and Secrets

**Never commit credentials to version control.** TopDeck uses environment variables for sensitive configuration:

```bash
# Store in .env file (add to .gitignore)
AZURE_CLIENT_SECRET=your-secret
GITHUB_TOKEN=your-token
NEO4J_PASSWORD=your-password
SECRET_KEY=your-secret-key
```

**Best Practices:**
1. ✅ Use secret management systems (Azure Key Vault, AWS Secrets Manager, HashiCorp Vault)
2. ✅ Rotate credentials regularly
3. ✅ Use read-only permissions where possible
4. ✅ Never log sensitive values
5. ✅ Use strong, randomly generated passwords

---

## Configuration

### Complete Example: Production with Full Encryption

`.env` file for production:
```bash
# Application
APP_ENV=production
APP_PORT=443
SECRET_KEY=<strong-random-key-at-least-32-chars>

# SSL/TLS for API Server
SSL_ENABLED=true
SSL_KEYFILE=/etc/topdeck/ssl/server.key
SSL_CERTFILE=/etc/topdeck/ssl/server.crt

# Neo4j - Encrypted
NEO4J_URI=bolt+s://neo4j.yourdomain.com:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<strong-password>
NEO4J_ENCRYPTED=true

# Redis - Encrypted
REDIS_HOST=redis.yourdomain.com
REDIS_PORT=6380
REDIS_PASSWORD=<strong-password>
REDIS_SSL=true
REDIS_SSL_CERT_REQS=required

# RabbitMQ - Encrypted
RABBITMQ_HOST=rabbitmq.yourdomain.com
RABBITMQ_PORT=5671
RABBITMQ_USERNAME=topdeck
RABBITMQ_PASSWORD=<strong-password>
RABBITMQ_SSL=true

# Cloud Credentials
AZURE_CLIENT_SECRET=<from-key-vault>
AWS_SECRET_ACCESS_KEY=<from-secrets-manager>
GITHUB_TOKEN=<from-secrets-manager>
```

### Docker Compose with Encryption

Update `docker-compose.yml` for encrypted services:

```yaml
services:
  neo4j:
    image: neo4j:5.13-enterprise  # Enterprise for encryption at rest
    environment:
      - NEO4J_AUTH=neo4j/strongpassword
      - NEO4J_dbms_ssl_policy_bolt_enabled=true
      - NEO4J_dbms_ssl_policy_bolt_base__directory=/var/lib/neo4j/certificates
    volumes:
      - ./certificates/neo4j:/var/lib/neo4j/certificates
      - neo4j_data:/data
    ports:
      - "7687:7687"

  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --requirepass strongpassword
      --tls-port 6380
      --port 0
      --tls-cert-file /tls/redis.crt
      --tls-key-file /tls/redis.key
      --tls-ca-cert-file /tls/ca.crt
    volumes:
      - ./certificates/redis:/tls
      - redis_data:/data
    ports:
      - "6380:6380"

  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      - RABBITMQ_DEFAULT_USER=topdeck
      - RABBITMQ_DEFAULT_PASS=strongpassword
    volumes:
      - ./rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf
      - ./certificates/rabbitmq:/etc/rabbitmq/ssl
      - rabbitmq_data:/var/lib/rabbitmq
    ports:
      - "5671:5671"
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Generate or obtain SSL/TLS certificates from trusted CA
- [ ] Enable encryption for all database connections
- [ ] Store credentials in secret management system
- [ ] Configure firewall rules to block unencrypted ports
- [ ] Enable filesystem or volume encryption
- [ ] Set up certificate rotation procedures
- [ ] Configure audit logging
- [ ] Review security settings validation

### Security Validation

TopDeck validates security settings on startup:

```python
# Production checks (automatic)
if app_env == "production":
    # ❌ Fails if default secret key is used
    # ⚠️  Warns if Neo4j encryption is disabled
    # ⚠️  Warns if Redis SSL is disabled
    # ⚠️  Warns if API SSL is disabled
```

### Cloud Provider Encryption

#### Azure
- **Azure Disk Encryption**: Encrypt VM disks at rest
- **Azure Key Vault**: Store secrets and certificates
- **TLS 1.2+**: Enforce on all Azure services

#### AWS
- **EBS Encryption**: Encrypt EC2 volumes at rest
- **AWS Secrets Manager**: Store credentials
- **TLS 1.2+**: Enforce on RDS, ElastiCache

#### GCP
- **Encryption at Rest**: Automatic for all storage
- **Secret Manager**: Store sensitive configuration
- **TLS 1.2+**: Enforce on Cloud SQL, Memorystore

---

## Troubleshooting

### Common Issues

#### Issue: "SSL: CERTIFICATE_VERIFY_FAILED"

**Cause:** Self-signed certificates or missing CA certificates

**Solution for Development:**
```bash
# Temporarily allow self-signed certs (development only)
REDIS_SSL_CERT_REQS=none
```

**Solution for Production:**
Install proper CA certificates or use certificates from trusted CA.

#### Issue: Neo4j Connection Fails with bolt+s://

**Cause:** Neo4j server doesn't have SSL configured

**Solution:**
1. Check Neo4j server SSL configuration in `neo4j.conf`
2. Verify certificate files exist and are readable
3. Check Neo4j logs: `/var/log/neo4j/neo4j.log`

#### Issue: Redis SSL Connection Timeout

**Cause:** Redis server not listening on SSL port

**Solution:**
```bash
# Verify Redis SSL port is open
netstat -tlnp | grep 6380

# Check Redis logs
tail -f /var/log/redis/redis-server.log
```

### Testing Encrypted Connections

#### Test API HTTPS
```bash
# Should succeed with valid certificate
curl https://your-domain.com:443/health

# Check certificate details
openssl s_client -connect your-domain.com:443 -showcerts
```

#### Test Neo4j Encryption
```bash
# Using cypher-shell
cypher-shell -a bolt+s://your-host:7687 -u neo4j -p password

# Check connection encryption
echo "RETURN 1" | cypher-shell -a bolt+s://your-host:7687
```

#### Test Redis SSL
```bash
# Using redis-cli
redis-cli --tls \
  --cert /path/to/client.crt \
  --key /path/to/client.key \
  --cacert /path/to/ca.crt \
  -h your-host -p 6380 \
  PING
```

---

## Additional Resources

- **Neo4j SSL Configuration**: https://neo4j.com/docs/operations-manual/current/security/ssl-framework/
- **Redis TLS Support**: https://redis.io/topics/encryption
- **RabbitMQ TLS**: https://www.rabbitmq.com/ssl.html
- **FastAPI HTTPS**: https://fastapi.tiangolo.com/deployment/https/
- **Let's Encrypt**: https://letsencrypt.org/ (Free SSL certificates)

---

## Security Contact

For security concerns or to report vulnerabilities, please contact the security team or create a confidential issue in the repository.

**Last Updated:** 2025-10-30
