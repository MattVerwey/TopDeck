# Automated Discovery

TopDeck now includes an automated discovery scheduler that continuously scans your cloud environments for resources and updates the topology graph. This ensures your topology is always up-to-date without manual intervention.

## Overview

The automated discovery feature:
- **Runs on startup**: Initial discovery scan happens when the API server starts
- **Periodic refresh**: Automatically rescans every 8 hours (configurable)
- **Multi-cloud support**: Discovers resources from Azure, AWS, and GCP simultaneously
- **Credential-based**: Only runs for cloud providers with valid credentials
- **Manual trigger**: Can be triggered manually via API endpoint
- **Status monitoring**: Check discovery status and view last run time

## Configuration

### Environment Variables

Configure automated discovery in your `.env` file:

```bash
# Discovery Configuration
DISCOVERY_SCAN_INTERVAL=28800  # 8 hours in seconds (8 * 3600)
DISCOVERY_PARALLEL_WORKERS=5    # Number of parallel discovery workers
DISCOVERY_TIMEOUT=300           # Discovery timeout in seconds

# Feature Flags
ENABLE_AZURE_DISCOVERY=true
ENABLE_AWS_DISCOVERY=true
ENABLE_GCP_DISCOVERY=true

# Azure Credentials (required for Azure discovery)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id

# AWS Credentials (required for AWS discovery)
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1

# GCP Credentials (required for GCP discovery)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your-project-id
```

### Scan Interval

The default scan interval is 8 hours (28800 seconds). You can adjust this by changing the `DISCOVERY_SCAN_INTERVAL` environment variable:

- **4 hours**: `DISCOVERY_SCAN_INTERVAL=14400`
- **8 hours**: `DISCOVERY_SCAN_INTERVAL=28800` (default)
- **12 hours**: `DISCOVERY_SCAN_INTERVAL=43200`
- **24 hours**: `DISCOVERY_SCAN_INTERVAL=86400`

## How It Works

### 1. Automatic Startup Discovery

When the TopDeck API server starts, it:
1. Checks which cloud providers are enabled
2. Validates that credentials are configured
3. Runs an initial discovery scan immediately
4. Schedules periodic scans based on the configured interval

### 2. Periodic Scans

The scheduler runs discovery scans at the configured interval:
1. Discovers resources from all enabled cloud providers
2. Stores resources and dependencies in Neo4j
3. Updates existing resources if they've changed
4. Logs progress and any errors

### 3. Credential Validation

Discovery only runs if valid credentials are configured:
- **Azure**: Requires `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, and `AZURE_SUBSCRIPTION_ID`
- **AWS**: Requires `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- **GCP**: Requires `GOOGLE_APPLICATION_CREDENTIALS` and `GCP_PROJECT_ID`

If credentials are not configured for a cloud provider, that provider is skipped.

## API Endpoints

### Get Discovery Status

Check the status of automated discovery:

```bash
curl http://localhost:8000/api/v1/discovery/status
```

**Response:**
```json
{
  "scheduler_running": true,
  "discovery_in_progress": false,
  "last_discovery_time": "2025-10-21T12:00:00",
  "interval_hours": 8,
  "enabled_providers": {
    "azure": true,
    "aws": false,
    "gcp": false
  }
}
```

### Trigger Manual Discovery

Manually trigger a discovery scan:

```bash
curl -X POST http://localhost:8000/api/v1/discovery/trigger
```

**Response:**
```json
{
  "status": "scheduled",
  "message": "Discovery has been scheduled to run",
  "last_run": "2025-10-21T12:00:00"
}
```

If discovery is already in progress:
```json
{
  "status": "already_running",
  "message": "Discovery is already in progress"
}
```

## Monitoring and Logs

### View Logs

The scheduler logs all discovery activities. Check the logs to see:
- When discovery runs start and complete
- How many resources were discovered
- Any errors that occurred

Example log output:
```
INFO: Starting automated resource discovery
INFO: Discovering Azure resources...
INFO: Azure discovery completed: 42 resources
INFO: Storing Azure resources in Neo4j...
INFO: Stored 42 resources in Neo4j
INFO: Automated discovery completed in 12.34s. Next run in 8 hours.
```

### Check API Health

The health check endpoint includes Neo4j status:

```bash
curl http://localhost:8000/health/detailed
```

This shows if Neo4j (where discovered resources are stored) is healthy.

## Best Practices

### 1. Set Appropriate Scan Intervals

Choose a scan interval based on your needs:
- **Development**: 1-4 hours for faster feedback
- **Staging**: 8 hours (default) for regular updates
- **Production**: 8-12 hours to balance freshness with API load

### 2. Monitor Discovery Status

Regularly check the discovery status endpoint to ensure:
- The scheduler is running
- Scans are completing successfully
- No cloud providers are consistently failing

### 3. Review Logs

Monitor logs for:
- Discovery failures
- Credential issues
- Network timeouts
- Resource storage errors

### 4. Use Manual Triggers Sparingly

The manual trigger endpoint is useful for:
- Testing after configuration changes
- Forcing a refresh after known infrastructure changes
- Troubleshooting

However, avoid triggering too frequently as it can:
- Increase API costs for cloud providers
- Impact performance
- Create unnecessary Neo4j load

## Troubleshooting

### Discovery Not Running

If discovery isn't running, check:

1. **Scheduler started**: Verify in logs that scheduler started on API startup
2. **Credentials configured**: Ensure all required environment variables are set
3. **Feature flags enabled**: Check that `ENABLE_*_DISCOVERY` flags are true
4. **Neo4j available**: Verify Neo4j is running and accessible

### Discovery Failing

If discovery fails, check:

1. **Cloud credentials**: Verify credentials are valid and have required permissions
2. **Network connectivity**: Ensure API server can reach cloud provider APIs
3. **Rate limits**: Check if you're hitting cloud provider API rate limits
4. **Timeout**: Increase `DISCOVERY_TIMEOUT` if scans are timing out

### No Resources Found

If discovery completes but finds no resources:

1. **Correct subscription/account**: Verify you're scanning the right subscription/account
2. **Resource groups**: Check if resources exist in the cloud provider
3. **Permissions**: Ensure service principal/IAM role has Reader permissions
4. **Filters**: Check if any filters are excluding resources

## Example: Complete Setup

Here's a complete example for setting up automated discovery for Azure:

1. **Create a service principal** (if you don't have one):
   ```bash
   az ad sp create-for-rbac --name topdeck-discovery --role Reader
   ```

2. **Configure `.env`**:
   ```bash
   # Enable Azure discovery
   ENABLE_AZURE_DISCOVERY=true
   
   # Azure credentials (from previous step)
   AZURE_TENANT_ID=your-tenant-id
   AZURE_CLIENT_ID=your-client-id
   AZURE_CLIENT_SECRET=your-client-secret
   AZURE_SUBSCRIPTION_ID=your-subscription-id
   
   # Discovery settings
   DISCOVERY_SCAN_INTERVAL=28800  # 8 hours
   DISCOVERY_PARALLEL_WORKERS=5
   
   # Neo4j connection
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-password
   ```

3. **Start services**:
   ```bash
   # Start Neo4j
   docker-compose up -d
   
   # Start API server
   make run
   ```

4. **Verify discovery**:
   ```bash
   # Check status
   curl http://localhost:8000/api/v1/discovery/status
   
   # View logs
   tail -f logs/topdeck.log
   ```

5. **Query discovered resources**:
   ```bash
   # Get topology
   curl http://localhost:8000/api/v1/topology
   
   # Or browse in Neo4j
   # Open http://localhost:7474 in browser
   ```

## Security Considerations

### Credential Storage

- Store credentials securely in environment variables
- Never commit credentials to source control
- Use secrets management systems in production (e.g., Azure Key Vault, AWS Secrets Manager)
- Rotate credentials regularly

### API Permissions

The discovery process only requires **read** permissions:
- **Azure**: Reader role
- **AWS**: ReadOnlyAccess policy
- **GCP**: Viewer role

Never grant write permissions to the discovery service principal/IAM role.

### Network Security

- Restrict API server network access to only required cloud provider endpoints
- Use private endpoints where available
- Consider running discovery in a separate security zone

## FAQ

**Q: Can I disable automatic discovery?**

A: Yes, set all `ENABLE_*_DISCOVERY` flags to `false` in your `.env` file. You can still trigger discovery manually via the API.

**Q: Does discovery affect my cloud provider costs?**

A: Discovery makes read-only API calls which have minimal cost. Most cloud providers offer free read API calls or charge fractions of a cent per call.

**Q: How long does a discovery scan take?**

A: Scan time depends on the number of resources:
- Small environment (10-50 resources): 5-15 seconds
- Medium environment (50-500 resources): 15-60 seconds
- Large environment (500+ resources): 1-5 minutes

**Q: What happens if discovery fails?**

A: The scheduler logs the error and continues. The next scheduled scan will run normally. You can check logs and manually trigger a scan after fixing issues.

**Q: Can I run multiple TopDeck instances?**

A: Yes, but only one instance should run discovery to avoid duplicate scans. Configure `ENABLE_*_DISCOVERY=false` on secondary instances.

**Q: How do I test discovery without waiting 8 hours?**

A: Use the manual trigger endpoint or temporarily set a shorter `DISCOVERY_SCAN_INTERVAL` (e.g., 300 for 5 minutes) during testing.
