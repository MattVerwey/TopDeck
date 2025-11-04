"""
Verify Azure DevOps configuration for Code Repository Scanner.
"""

import os
import sys

def check_ado_config():
    """Check if Azure DevOps is properly configured."""
    
    print("=" * 80)
    print("Azure DevOps Configuration Check")
    print("=" * 80)
    
    # Check environment variables
    org = os.getenv("AZURE_DEVOPS_ORGANIZATION", "")
    project = os.getenv("AZURE_DEVOPS_PROJECT", "")
    pat = os.getenv("AZURE_DEVOPS_PAT", "")
    enabled = os.getenv("ENABLE_AZURE_DEVOPS_INTEGRATION", "false")
    
    print(f"\n✓ Organization: {org if org and org != 'your-org' else '❌ NOT SET'}")
    print(f"✓ Project: {project if project and project != 'your-project' else '❌ NOT SET'}")
    print(f"✓ PAT: {'***' + pat[-4:] if pat and len(pat) > 10 and pat != 'your-personal-access-token' else '❌ NOT SET'}")
    print(f"✓ Integration Enabled: {enabled}")
    
    if not org or org == "your-org":
        print("\n❌ AZURE_DEVOPS_ORGANIZATION not configured")
        print("   Set in .env: AZURE_DEVOPS_ORGANIZATION=CodeGalaxy")
        return False
        
    if not project or project == "your-project":
        print("\n❌ AZURE_DEVOPS_PROJECT not configured")
        print("   Set in .env: AZURE_DEVOPS_PROJECT=YourProjectName")
        return False
        
    if not pat or pat == "your-personal-access-token" or len(pat) < 10:
        print("\n❌ AZURE_DEVOPS_PAT not configured")
        print("   Generate PAT at: https://dev.azure.com/{org}/_usersSettings/tokens")
        print("   Required scopes: Code (Read), Project and Team (Read)")
        return False
    
    print("\n✅ All Azure DevOps credentials configured!")
    print(f"\nConfiguration:")
    print(f"  Organization: {org}")
    print(f"  Project: {project}")
    print(f"  Base URL: https://dev.azure.com/{org}/{project}")
    
    return True

def show_next_steps():
    """Show next steps after configuration."""
    print("\n" + "=" * 80)
    print("Next Steps")
    print("=" * 80)
    print("""
1. Restart the API to load new environment variables:
   docker-compose up -d --build api

2. Test the repository scanner endpoint:
   POST http://localhost:8000/api/v1/discovery/scan-repositories

3. The scanner will:
   ✓ Connect to your Azure DevOps organization
   ✓ List all repositories in your project
   ✓ Scan appsettings.json, .env files for Service Bus references
   ✓ Match to your 21 discovered Service Bus topics
   ✓ Create dependencies in Neo4j (App Service → Service Bus)

4. View updated topology with new dependencies:
   GET http://localhost:8000/api/v1/topology
""")

if __name__ == "__main__":
    # Try to load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Loaded .env file\n")
    except ImportError:
        print("python-dotenv not installed, reading system environment\n")
    
    if check_ado_config():
        show_next_steps()
    else:
        print("\n" + "=" * 80)
        print("Configuration Required")
        print("=" * 80)
        print("""
To enable code repository scanning:

1. Edit c:\\Code\\Custom Repos\\TopDeck\\.env
2. Set your Azure DevOps credentials:
   
   AZURE_DEVOPS_ORGANIZATION=CodeGalaxy
   AZURE_DEVOPS_PROJECT=YourProjectName
   AZURE_DEVOPS_PAT=your-pat-token-here

3. Run this script again to verify
""")
        sys.exit(1)
