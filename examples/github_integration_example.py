"""
Example demonstrating GitHub integration features.

This script shows how to use the GitHub integration to discover
repositories, workflows, and deployments.

NOTE: This script demonstrates the API. To run it, you need:
  1. pip install -r requirements.txt
  2. Set GITHUB_TOKEN environment variable
  3. Update organization/user as needed
"""

import asyncio
import os
import sys

# Add src to path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from topdeck.integration.github import GitHubIntegration


async def example_basic_discovery():
    """Example: Basic repository discovery."""
    print("\n" + "="*70)
    print("Example: Basic Repository Discovery")
    print("="*70)
    
    # Get token from environment
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("⚠️  GITHUB_TOKEN not set. Set it with:")
        print("   export GITHUB_TOKEN='ghp_your_token_here'")
        return
    
    # Initialize GitHub integration
    github = GitHubIntegration(
        token=token,
        # Uncomment to use organization or user
        # organization="your-org",
        # user="your-username",
    )
    
    try:
        # Discover repositories
        print("\n📚 Discovering repositories...")
        repositories = await github.discover_repositories()
        
        print(f"✓ Found {len(repositories)} repositories\n")
        
        # Display first 5 repositories
        for i, repo in enumerate(repositories[:5], 1):
            print(f"{i}. {repo.name}")
            print(f"   URL: {repo.url}")
            print(f"   Language: {repo.language or 'Not specified'}")
            print(f"   Stars: {repo.stars or 0}")
            print(f"   Private: {repo.is_private}")
            if repo.topics:
                print(f"   Topics: {', '.join(repo.topics)}")
            print()
        
        if len(repositories) > 5:
            print(f"... and {len(repositories) - 5} more repositories")
    
    finally:
        await github.close()


async def example_workflow_discovery():
    """Example: Discover GitHub Actions workflows."""
    print("\n" + "="*70)
    print("Example: GitHub Actions Workflow Discovery")
    print("="*70)
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("⚠️  GITHUB_TOKEN not set")
        return
    
    github = GitHubIntegration(token=token)
    
    try:
        # Discover repositories first
        print("\n📚 Discovering repositories...")
        repositories = await github.discover_repositories()
        
        if not repositories:
            print("No repositories found")
            return
        
        # Take first repository with workflows
        for repo in repositories[:10]:  # Check first 10
            print(f"\n🔍 Checking {repo.full_name} for workflows...")
            
            workflows = await github.discover_workflows(repo.full_name)
            
            if workflows:
                print(f"✓ Found {len(workflows)} workflows in {repo.full_name}\n")
                
                for workflow in workflows:
                    print(f"  • {workflow['name']}")
                    print(f"    Path: {workflow['path']}")
                    print(f"    State: {workflow['state']}")
                    print()
                
                # Get workflow runs for first workflow
                if workflows:
                    print(f"📊 Recent workflow runs...")
                    runs = await github.discover_workflow_runs(
                        repo.full_name,
                        workflow_id=workflows[0]['id'],
                        limit=5
                    )
                    
                    for run in runs:
                        status_icon = "✓" if run['conclusion'] == "success" else "✗"
                        print(f"  {status_icon} Run #{run['id']}: {run['name']}")
                        print(f"    Status: {run['status']} - {run['conclusion']}")
                        print()
                
                break  # Found workflows, stop looking
    
    finally:
        await github.close()


async def example_deployment_tracking():
    """Example: Track deployments."""
    print("\n" + "="*70)
    print("Example: Deployment Tracking")
    print("="*70)
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("⚠️  GITHUB_TOKEN not set")
        return
    
    github = GitHubIntegration(token=token)
    
    try:
        # Discover repositories
        print("\n📚 Discovering repositories...")
        repositories = await github.discover_repositories()
        
        if not repositories:
            print("No repositories found")
            return
        
        # Check first few repos for deployments
        total_deployments = 0
        for repo in repositories[:5]:
            print(f"\n🚀 Checking {repo.full_name} for deployments...")
            
            deployments = await github.discover_deployments(repo.full_name)
            
            if deployments:
                print(f"✓ Found {len(deployments)} deployments\n")
                total_deployments += len(deployments)
                
                for deployment in deployments[:3]:  # Show first 3
                    print(f"  • Deployment #{deployment.id}")
                    print(f"    Environment: {deployment.environment}")
                    print(f"    Version: {deployment.version}")
                    print(f"    Status: {deployment.status}")
                    print(f"    Deployed by: {deployment.deployed_by}")
                    print(f"    Deployed at: {deployment.deployed_at}")
                    print()
        
        print(f"\n📊 Total deployments found: {total_deployments}")
    
    finally:
        await github.close()


async def example_application_inference():
    """Example: Infer applications from repositories."""
    print("\n" + "="*70)
    print("Example: Application Inference")
    print("="*70)
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("⚠️  GITHUB_TOKEN not set")
        return
    
    github = GitHubIntegration(token=token)
    
    try:
        # Discover applications
        print("\n📱 Inferring applications from repositories...")
        applications = await github.discover_applications()
        
        print(f"✓ Found {len(applications)} applications\n")
        
        # Display first 10 applications
        for i, app in enumerate(applications[:10], 1):
            print(f"{i}. {app.name}")
            print(f"   Environment: {app.environment}")
            print(f"   Owner: {app.owner_team or 'Not specified'}")
            print(f"   Repository: {app.repository_url}")
            print()
        
        if len(applications) > 10:
            print(f"... and {len(applications) - 10} more applications")
        
        # Statistics
        print("\n📊 Environment Distribution:")
        env_counts = {}
        for app in applications:
            env = app.environment or "unknown"
            env_counts[env] = env_counts.get(env, 0) + 1
        
        for env, count in sorted(env_counts.items()):
            print(f"  {env}: {count}")
    
    finally:
        await github.close()


async def example_complete_discovery():
    """Example: Complete discovery workflow."""
    print("\n" + "="*70)
    print("Example: Complete Discovery Workflow")
    print("="*70)
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("⚠️  GITHUB_TOKEN not set")
        return
    
    github = GitHubIntegration(
        token=token,
        # organization="your-org",  # Uncomment to use
    )
    
    try:
        print("\n🔍 Starting complete GitHub discovery...\n")
        
        # Step 1: Discover repositories
        print("1️⃣  Discovering repositories...")
        repositories = await github.discover_repositories()
        print(f"   ✓ Found {len(repositories)} repositories")
        
        # Step 2: Analyze each repository
        print("\n2️⃣  Analyzing repositories...")
        
        workflow_count = 0
        deployment_count = 0
        
        # Process first 3 repos for demo
        for i, repo in enumerate(repositories[:3], 1):
            print(f"\n   Repository {i}/{min(3, len(repositories))}: {repo.full_name}")
            
            # Discover workflows
            workflows = await github.discover_workflows(repo.full_name)
            workflow_count += len(workflows)
            print(f"      Workflows: {len(workflows)}")
            
            # Discover deployments
            deployments = await github.discover_deployments(repo.full_name)
            deployment_count += len(deployments)
            print(f"      Deployments: {len(deployments)}")
        
        # Step 3: Infer applications
        print("\n3️⃣  Inferring applications...")
        applications = await github.discover_applications()
        print(f"   ✓ Found {len(applications)} applications")
        
        # Summary
        print("\n" + "="*70)
        print("📊 Discovery Summary")
        print("="*70)
        print(f"Repositories: {len(repositories)}")
        print(f"Workflows: {workflow_count} (from {min(3, len(repositories))} repos)")
        print(f"Deployments: {deployment_count} (from {min(3, len(repositories))} repos)")
        print(f"Applications: {len(applications)}")
        print()
        
        # Environment breakdown
        print("Environment Distribution:")
        env_counts = {}
        for app in applications:
            env = app.environment or "unknown"
            env_counts[env] = env_counts.get(env, 0) + 1
        
        for env, count in sorted(env_counts.items()):
            percentage = (count / len(applications) * 100) if applications else 0
            print(f"  {env}: {count} ({percentage:.1f}%)")
    
    finally:
        await github.close()


async def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("GitHub Integration Examples")
    print("="*70)
    
    print("\nThese examples demonstrate the GitHub integration module.")
    print("Make sure to set GITHUB_TOKEN environment variable.")
    print("\nExamples:")
    print("  1. Basic repository discovery")
    print("  2. GitHub Actions workflow discovery")
    print("  3. Deployment tracking")
    print("  4. Application inference")
    print("  5. Complete discovery workflow")
    
    print("\n" + "="*70)
    
    # Run examples
    await example_basic_discovery()
    
    # Uncomment to run other examples
    # await example_workflow_discovery()
    # await example_deployment_tracking()
    # await example_application_inference()
    # await example_complete_discovery()
    
    print("\n" + "="*70)
    print("✓ Examples completed")
    print("="*70)
    print("\nNote: Uncomment other examples in main() to run them.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
