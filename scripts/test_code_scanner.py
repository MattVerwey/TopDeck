"""
Test script for Code Repository Scanner.

This demonstrates how the scanner works by testing it with sample configuration files.
"""

import asyncio
import json


# Sample appsettings.json content that might be in a .NET application
SAMPLE_APPSETTINGS = '''
{
  "ConnectionStrings": {
    "ServiceBusConnection": "Endpoint=sb://cg-dev-uks-sbns-1.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=xxxxx",
    "SqlDatabase": "Server=tcp:myserver.database.windows.net,1433;Database=mydb;"
  },
  "ServiceBus": {
    "TopicName": "fifa-1",
    "QueueName": "nba-5",
    "Namespace": "cg-dev-uks-sbns-1"
  },
  "Messaging": {
    "Topics": [
      "fifa-1",
      "fifa-2", 
      "test-topic"
    ],
    "Subscriptions": {
      "fifa-1": "my-subscription",
      "nba-5": "another-subscription"
    }
  }
}
'''

# Sample .env file
SAMPLE_ENV = '''
# Service Bus Configuration
AZURE_SERVICEBUS_CONNECTION=Endpoint=sb://cg-dev-uks-sbns-1.servicebus.windows.net/;SharedAccessKeyName=SendPolicy;SharedAccessKey=yyyyy
SERVICEBUS_TOPIC_NAME=test-topic-2
SERVICEBUS_NAMESPACE=cg-dev-uks-sbns-1

# Database
DATABASE_URL=postgresql://user:pass@mydb.postgres.database.azure.com:5432/prod
'''


async def test_scanner():
    """Test the code repository scanner with sample data."""
    from topdeck.discovery.azure.code_scanner import CodeRepositoryScanner
    
    # Create a mock scanner (won't actually connect to ADO)
    scanner = CodeRepositoryScanner(
        organization="test-org",
        project="test-project",
        personal_access_token="test-pat"
    )
    
    print("=" * 80)
    print("Testing Code Repository Scanner")
    print("=" * 80)
    
    # Test 1: Parse JSON configuration
    print("\n1. Testing appsettings.json parsing...")
    print("-" * 80)
    json_results = scanner._parse_file_content(
        SAMPLE_APPSETTINGS,
        "appsettings.json",
        None
    )
    
    print(f"Namespaces found: {json_results['namespaces']}")
    print(f"Topics found: {json_results['topics']}")
    print(f"Connection strings: {json_results['connection_strings_found']}")
    
    # Test 2: Parse .env file
    print("\n2. Testing .env file parsing...")
    print("-" * 80)
    env_results = scanner._parse_file_content(
        SAMPLE_ENV,
        ".env",
        None
    )
    
    print(f"Namespaces found: {env_results['namespaces']}")
    print(f"Topics found: {env_results['topics']}")
    print(f"Connection strings: {env_results['connection_strings_found']}")
    
    # Test 3: Show what would be discovered
    print("\n3. Combined Results:")
    print("-" * 80)
    all_namespaces = json_results['namespaces'] | env_results['namespaces']
    all_topics = json_results['topics'] | env_results['topics']
    
    print(f"\n✅ Service Bus Namespaces Discovered: {len(all_namespaces)}")
    for ns in all_namespaces:
        print(f"   - {ns}")
    
    print(f"\n✅ Service Bus Topics/Queues Discovered: {len(all_topics)}")
    for topic in sorted(all_topics):
        print(f"   - {topic}")
    
    print(f"\n✅ Total Connection Strings: {json_results['connection_strings_found'] + env_results['connection_strings_found']}")
    
    print("\n" + "=" * 80)
    print("DEMO: How This Works in Production")
    print("=" * 80)
    print("""
When you call the API endpoint /api/v1/discovery/scan-repositories:

1. Connects to your Azure DevOps organization
2. Gets all repositories in the project
3. For each repository:
   - Downloads appsettings.json, appsettings.Production.json, .env files
   - Parses them for Service Bus connection strings
   - Extracts topic and queue names
   
4. Matches found resources against your discovered Azure resources:
   - Namespace 'cg-dev-uks-sbns-1' → Matches your Service Bus namespace
   - Topics 'fifa-1', 'fifa-2', 'test-topic-2' → Match your 21 topics
   
5. Creates dependencies in Neo4j:
   - App Service → Service Bus Namespace (strength: 0.95)
   - Discovered method: 'code_repository_scan'
   
6. These dependencies appear in the topology visualization!

IMPORTANT: Only creates dependencies for resources in your subscription.
If code references 'other-service-bus' but it's not in your subscription,
no dependency is created (it's filtered out).
""")
    
    print("\n" + "=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print("""
1. Set environment variables:
   AZURE_DEVOPS_ORGANIZATION=your-org
   AZURE_DEVOPS_PROJECT=your-project  
   AZURE_DEVOPS_PAT=your-personal-access-token

2. Restart API: docker-compose up -d --build api

3. Call the scanning endpoint:
   POST http://localhost:8000/api/v1/discovery/scan-repositories

4. Check the topology to see new dependencies!
   GET http://localhost:8000/api/v1/topology
""")


if __name__ == "__main__":
    asyncio.run(test_scanner())
