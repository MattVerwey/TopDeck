"""
Azure DevOps Integration for Repository and Deployment Discovery.

Discovers repositories, pipelines, and deployments from Azure DevOps.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import base64
import logging
import time

try:
    import httpx
except ImportError:
    httpx = None

from ..models import Repository, Deployment, Application
from ...common.resilience import (
    RateLimiter,
    RetryConfig,
    retry_with_backoff,
    ErrorTracker,
)
from ...common.logging_config import get_logger, log_operation_metrics

logger = get_logger(__name__)


class AzureDevOpsDiscoverer:
    """
    Discovers repositories and deployments from Azure DevOps.
    
    Uses Azure DevOps REST API to discover:
    - Git repositories
    - Build pipelines
    - Release pipelines
    - Deployment history
    """
    
    def __init__(
        self,
        organization: str,
        project: str,
        personal_access_token: Optional[str] = None,
    ):
        """
        Initialize Azure DevOps discoverer.
        
        Args:
            organization: Azure DevOps organization name
            project: Azure DevOps project name
            personal_access_token: PAT for authentication
        """
        self.organization = organization
        self.project = project
        self.pat = personal_access_token
        self.base_url = f"https://dev.azure.com/{organization}/{project}"
        self.api_version = "7.0"
        
        # Set up authentication headers
        self._headers = self._create_auth_headers()
        
        # HTTP client for API calls (will be initialized when needed)
        self._client: Optional[Any] = None
        
        # Rate limiter for Azure DevOps API (max 200 requests per minute)
        self._rate_limiter = RateLimiter(max_calls=200, time_window=60.0)
        
        # Retry configuration
        self._retry_config = RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=30.0,
        )
    
    def _create_auth_headers(self) -> Dict[str, str]:
        """
        Create authentication headers for Azure DevOps API.
        
        Returns:
            Dictionary with authentication headers
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        if self.pat:
            # Encode PAT for basic authentication
            auth_string = f":{self.pat}"
            encoded = base64.b64encode(auth_string.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        
        return headers
    
    def _get_client(self):
        """Get or create HTTP client."""
        if httpx is None:
            raise ImportError(
                "httpx is required for Azure DevOps API integration. "
                "Install it with: pip install httpx"
            )
        
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self._headers,
                timeout=30.0,
            )
        
        return self._client
    
    @retry_with_backoff()
    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to Azure DevOps API with rate limiting and retry.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: API endpoint URL
            params: Query parameters
            json_data: JSON body for POST/PUT requests
            
        Returns:
            JSON response or None if error
        """
        # Apply rate limiting
        await self._rate_limiter.acquire()
        
        client = self._get_client()
        
        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limit exceeded, will be retried by decorator
                logger.warning(f"Azure DevOps rate limit exceeded, retrying...")
                raise
            elif e.response.status_code >= 500:
                # Server error, will be retried
                logger.warning(f"Azure DevOps server error {e.response.status_code}, retrying...")
                raise
            else:
                # Client error, don't retry
                logger.error(f"Azure DevOps API request failed: {e}")
                return None
        except Exception as e:
            logger.error(f"Azure DevOps API request failed: {e}")
            raise
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
    
    async def discover_repositories(self) -> List[Repository]:
        """
        Discover all repositories in the Azure DevOps project.
        
        Returns:
            List of Repository objects
            
        Uses: GET https://dev.azure.com/{organization}/{project}/_apis/git/repositories
        """
        start_time = time.time()
        repositories = []
        error_tracker = ErrorTracker()
        
        try:
            # Build API URL
            url = f"{self.base_url}/_apis/git/repositories"
            params = {"api-version": self.api_version}
            
            # Make API request
            response_data = await self._make_request("GET", url, params=params)
            
            if not response_data or "value" not in response_data:
                logger.warning("No repositories found or API error")
                return repositories
            
            # Parse repositories
            for repo_data in response_data["value"]:
                repo_id = repo_data.get("id", "unknown")
                try:
                    repo = await self._parse_repository(repo_data)
                    if repo:
                        repositories.append(repo)
                        error_tracker.record_success(repo_id)
                    else:
                        error_tracker.record_error(repo_id, Exception("Failed to parse repository"))
                except Exception as e:
                    error_tracker.record_error(repo_id, e)
            
            logger.info(f"Discovered {len(repositories)} repositories")
            
        finally:
            # Log operation metrics
            duration = time.time() - start_time
            log_operation_metrics(
                operation="discover_repositories",
                duration=duration,
                success=not error_tracker.has_errors(),
                items_processed=len(repositories),
                errors=error_tracker.failure_count,
            )
        
        return repositories
    
    async def _parse_repository(self, repo_data: Dict[str, Any]) -> Optional[Repository]:
        """
        Parse repository data from Azure DevOps API response.
        
        Args:
            repo_data: Repository data from API
            
        Returns:
            Repository object or None
        """
        try:
            repo_id = repo_data.get("id")
            repo_name = repo_data.get("name")
            repo_url = repo_data.get("remoteUrl") or repo_data.get("webUrl")
            
            if not repo_id or not repo_name:
                return None
            
            # Get default branch
            default_branch = repo_data.get("defaultBranch", "")
            if default_branch.startswith("refs/heads/"):
                default_branch = default_branch.replace("refs/heads/", "")
            
            # Get last commit info if available
            last_commit_sha = None
            last_commit_date = None
            
            # Try to get commits for more details
            commits_url = f"{self.base_url}/_apis/git/repositories/{repo_id}/commits"
            commits_params = {"api-version": self.api_version, "$top": 1}
            commits_data = await self._make_request("GET", commits_url, params=commits_params)
            
            if commits_data and "value" in commits_data and len(commits_data["value"]) > 0:
                commit = commits_data["value"][0]
                last_commit_sha = commit.get("commitId")
                commit_date_str = commit.get("author", {}).get("date")
                if commit_date_str:
                    try:
                        last_commit_date = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass
            
            # Create Repository object
            repository = Repository(
                id=f"azdo-{self.organization}-{self.project}-{repo_id}",
                platform="azure_devops",
                url=repo_url or f"https://dev.azure.com/{self.organization}/{self.project}/_git/{repo_name}",
                name=repo_name,
                full_name=f"{self.organization}/{self.project}/{repo_name}",
                default_branch=default_branch or "main",
                last_commit_sha=last_commit_sha,
                last_commit_date=last_commit_date,
                is_private=True,  # Azure DevOps repos are typically private
                is_archived=False,
            )
            
            return repository
            
        except Exception as e:
            logger.error(f"Error parsing repository data: {e}")
            return None
    
    async def discover_deployments(
        self,
        repository_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Deployment]:
        """
        Discover recent deployments from Azure Pipelines.
        
        Args:
            repository_id: Optional repository ID to filter deployments
            limit: Maximum number of deployments to retrieve
            
        Returns:
            List of Deployment objects
            
        Uses: GET https://dev.azure.com/{organization}/{project}/_apis/build/builds
        """
        deployments = []
        
        # Build API URL for builds
        url = f"{self.base_url}/_apis/build/builds"
        params = {
            "api-version": self.api_version,
            "$top": min(limit, 100),  # Azure DevOps has max 100 per page
            "queryOrder": "finishTimeDescending",
        }
        
        if repository_id:
            params["repositoryId"] = repository_id
        
        # Make API request
        response_data = await self._make_request("GET", url, params=params)
        
        if not response_data or "value" not in response_data:
            logger.warning("No builds found or API error")
            return deployments
        
        # Parse builds
        for build_data in response_data["value"]:
            try:
                deployment = await self._parse_deployment(build_data)
                if deployment:
                    deployments.append(deployment)
            except Exception as e:
                logger.error(f"Error parsing deployment: {e}")
        
        logger.info(f"Discovered {len(deployments)} deployments")
        return deployments
    
    async def _parse_deployment(self, build_data: Dict[str, Any]) -> Optional[Deployment]:
        """
        Parse deployment data from Azure DevOps build API response.
        
        Args:
            build_data: Build data from API
            
        Returns:
            Deployment object or None
        """
        try:
            build_id = build_data.get("id")
            build_number = build_data.get("buildNumber")
            
            if not build_id:
                return None
            
            # Get pipeline info
            definition = build_data.get("definition", {})
            pipeline_id = str(definition.get("id", ""))
            pipeline_name = definition.get("name", "")
            
            # Get deployment status
            status_map = {
                "completed": "success",
                "inProgress": "in_progress",
                "notStarted": "in_progress",
                "cancelling": "cancelled",
                "cancelled": "cancelled",
            }
            result_map = {
                "succeeded": "success",
                "partiallySucceeded": "success",
                "failed": "failed",
                "canceled": "cancelled",
            }
            
            status = build_data.get("status", "unknown")
            result = build_data.get("result")
            
            # Use result if available, otherwise use status
            deployment_status = result_map.get(result) if result else status_map.get(status, "in_progress")
            
            # Get timestamps
            start_time_str = build_data.get("startTime")
            finish_time_str = build_data.get("finishTime")
            
            deployed_at = None
            if start_time_str:
                try:
                    deployed_at = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
            
            deployment_duration = None
            if start_time_str and finish_time_str:
                try:
                    start = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                    finish = datetime.fromisoformat(finish_time_str.replace("Z", "+00:00"))
                    deployment_duration = int((finish - start).total_seconds())
                except (ValueError, AttributeError):
                    pass
            
            # Get source version (commit SHA)
            commit_sha = build_data.get("sourceVersion")
            
            # Get requester/deployer
            requested_for = build_data.get("requestedFor", {})
            deployed_by = requested_for.get("displayName") or requested_for.get("uniqueName")
            
            # Create Deployment object
            deployment = Deployment(
                id=f"azdo-build-{self.organization}-{self.project}-{build_id}",
                pipeline_id=pipeline_id,
                pipeline_name=pipeline_name,
                run_number=int(build_number) if build_number and build_number.isdigit() else None,
                version=build_number,
                commit_sha=commit_sha,
                deployed_at=deployed_at or datetime.utcnow(),
                deployed_by=deployed_by,
                deployment_duration=deployment_duration,
                status=deployment_status,
            )
            
            return deployment
            
        except Exception as e:
            logger.error(f"Error parsing deployment data: {e}")
            return None
    
    async def discover_applications(self) -> List[Application]:
        """
        Discover applications from Azure DevOps metadata.
        
        Applications can be inferred from:
        - Repository naming conventions
        - Pipeline definitions
        - Variable groups
        - Service connections
        
        Returns:
            List of Application objects
        """
        applications = []
        application_map: Dict[str, Application] = {}
        
        # First, discover repositories to infer applications
        repositories = await self.discover_repositories()
        
        for repo in repositories:
            # Infer application from repository name
            app = self._infer_application_from_repository(repo)
            if app:
                app_key = f"{app.name}-{app.environment}"
                if app_key not in application_map:
                    application_map[app_key] = app
                    app.repository_id = repo.id
                    app.repository_url = repo.url
        
        # Convert to list
        applications = list(application_map.values())
        
        logger.info(f"Discovered {len(applications)} applications")
        return applications
    
    def _infer_application_from_repository(self, repository: Repository) -> Optional[Application]:
        """
        Infer application from repository.
        
        Args:
            repository: Repository object
            
        Returns:
            Application object or None
        """
        # Extract application name from repository name
        # Common patterns: {app-name}-{type}, {env}-{app-name}, {app-name}
        repo_name = repository.name.lower()
        
        # Remove common suffixes
        for suffix in ["-api", "-web", "-service", "-backend", "-frontend", "-app"]:
            if repo_name.endswith(suffix):
                repo_name = repo_name[:-len(suffix)]
                break
        
        # Detect environment from repository name or branch
        environment = "unknown"
        for env in ["prod", "production", "staging", "stage", "dev", "development", "test"]:
            if env in repo_name or env in (repository.default_branch or "").lower():
                if env in ["prod", "production"]:
                    environment = "production"
                elif env in ["staging", "stage"]:
                    environment = "staging"
                elif env in ["dev", "development"]:
                    environment = "development"
                elif env == "test":
                    environment = "test"
                break
        
        # Create application
        app_id = f"app-{repo_name}-{environment}"
        app = Application(
            id=app_id,
            name=repo_name,
            environment=environment,
            repository_url=repository.url,
            repository_id=repository.id,
        )
        
        return app
    
    def extract_deployment_metadata_from_tags(
        self,
        tags: Dict[str, str],
    ) -> Optional[Dict[str, Any]]:
        """
        Extract deployment metadata from resource tags.
        
        Common Azure tags that indicate deployment information:
        - deploy_version, version, app_version
        - deploy_date, deployed_at
        - deploy_pipeline, pipeline_id
        - deploy_commit, commit_sha
        - deployed_by
        
        Args:
            tags: Resource tags dictionary
            
        Returns:
            Dictionary with deployment metadata or None
        """
        if not tags:
            return None
        
        metadata = {}
        
        # Version
        for version_key in ['deploy_version', 'version', 'app_version', 'image_tag']:
            if version_key in tags:
                metadata['version'] = tags[version_key]
                break
        
        # Deployment date
        for date_key in ['deploy_date', 'deployed_at', 'deployment_date']:
            if date_key in tags:
                try:
                    # Try to parse as ISO format
                    metadata['deployed_at'] = datetime.fromisoformat(tags[date_key])
                except (ValueError, TypeError):
                    # Keep as string if not parseable
                    metadata['deployed_at'] = tags[date_key]
                break
        
        # Pipeline information
        for pipeline_key in ['deploy_pipeline', 'pipeline_id', 'pipeline_name', 'build_id']:
            if pipeline_key in tags:
                metadata['pipeline_id'] = tags[pipeline_key]
                break
        
        # Commit information
        for commit_key in ['deploy_commit', 'commit_sha', 'git_commit', 'commit']:
            if commit_key in tags:
                metadata['commit_sha'] = tags[commit_key]
                break
        
        # Deployed by
        for user_key in ['deployed_by', 'deployer', 'owner']:
            if user_key in tags:
                metadata['deployed_by'] = tags[user_key]
                break
        
        # Repository URL
        for repo_key in ['repository', 'repo_url', 'git_url']:
            if repo_key in tags:
                metadata['repository_url'] = tags[repo_key]
                break
        
        return metadata if metadata else None
    
    def infer_application_from_resource(
        self,
        resource_name: str,
        resource_type: str,
        tags: Dict[str, str],
    ) -> Optional[Application]:
        """
        Infer application information from a resource.
        
        Uses naming conventions and tags to identify the application:
        - Resource naming patterns (e.g., "prod-myapp-aks")
        - Application tags (app_name, application, service_name)
        - Environment tags to determine deployment method
        
        Args:
            resource_name: Resource name
            resource_type: Resource type
            tags: Resource tags
            
        Returns:
            Application object or None
        """
        # Extract application name from tags
        app_name = None
        for app_key in ['app_name', 'application', 'service_name', 'app', 'service']:
            if app_key in tags:
                app_name = tags[app_key]
                break
        
        # If no tag, try to infer from resource name
        # Common patterns: {env}-{app}-{resource_type}
        if not app_name:
            # Remove environment prefix (prod-, staging-, dev-)
            name_without_env = re.sub(r'^(prod|staging|dev|test)-', '', resource_name)
            # Remove resource type suffix
            name_without_type = re.sub(r'-(aks|app|service|api|web|db)$', '', name_without_env)
            if name_without_type and name_without_type != resource_name:
                app_name = name_without_type
        
        if not app_name:
            return None
        
        # Create application ID
        environment = tags.get('environment', tags.get('env', 'unknown'))
        app_id = f"app-{app_name}-{environment}"
        
        # Extract deployment method from resource type
        deployment_method_map = {
            'aks': 'aks',
            'app_service': 'app_service',
            'virtual_machine': 'vm',
            'container_instance': 'container_instance',
        }
        deployment_method = deployment_method_map.get(resource_type)
        
        # Create Application object
        app = Application(
            id=app_id,
            name=app_name,
            environment=environment,
            deployment_method=deployment_method,
            owner_team=tags.get('owner_team', tags.get('team', tags.get('owner'))),
            repository_url=tags.get('repository', tags.get('repo_url')),
            current_version=tags.get('version', tags.get('app_version')),
        )
        
        return app
