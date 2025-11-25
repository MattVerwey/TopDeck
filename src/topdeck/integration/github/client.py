"""
GitHub Integration Client for Repository and Deployment Discovery.

Uses GitHub REST API to discover:
- Repositories
- GitHub Actions workflows
- Workflow runs and deployments
- Deployment history
"""

from datetime import UTC, datetime
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None

from ...common.logging_config import get_logger, log_operation_metrics
from ...common.resilience import (
    ErrorTracker,
    RateLimiter,
    RetryConfig,
    retry_with_backoff,
)
from ...discovery.models import Application, Deployment, Repository

logger = get_logger(__name__)


class GitHubIntegration:
    """
    Discovers repositories and deployments from GitHub.

    Uses GitHub REST API to discover:
    - Repositories (public and private)
    - GitHub Actions workflows
    - Workflow runs
    - Deployment history
    """

    def __init__(
        self,
        token: str,
        organization: str | None = None,
        user: str | None = None,
    ):
        """
        Initialize GitHub integration.

        Args:
            token: GitHub Personal Access Token
            organization: GitHub organization name (optional)
            user: GitHub user name (optional)
        """
        self.token = token
        self.organization = organization
        self.user = user
        self.base_url = "https://api.github.com"

        # Set up authentication headers
        self._headers = self._create_auth_headers()

        # HTTP client for API calls (will be initialized when needed)
        self._client: Any | None = None

        # Rate limiter for GitHub API (5000 requests per hour for authenticated users)
        # That's roughly 83 requests per minute
        self._rate_limiter = RateLimiter(max_calls=80, time_window=60.0)

        # Retry configuration
        self._retry_config = RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=30.0,
        )

    def _create_auth_headers(self) -> dict[str, str]:
        """
        Create authentication headers for GitHub API.

        Returns:
            Dictionary with authentication headers
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.token}",
        }

        return headers

    def _get_client(self):
        """Get or create HTTP client."""
        if httpx is None:
            raise ImportError(
                "httpx is required for GitHub API integration. "
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
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Make an API request with rate limiting and retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full API URL
            params: Query parameters
            json_data: JSON request body

        Returns:
            Response data as dictionary
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

            # Check for rate limit headers
            if "X-RateLimit-Remaining" in response.headers:
                remaining = int(response.headers["X-RateLimit-Remaining"])
                if remaining < 10:
                    logger.warning(f"GitHub API rate limit low: {remaining} requests remaining")

            response.raise_for_status()

            # Return empty dict for 204 No Content
            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Resource not found: {url}")
                return None
            elif e.response.status_code == 403:
                logger.error(f"Access forbidden: {url} - Check token permissions")
                return None
            elif e.response.status_code == 401:
                logger.error(f"Unauthorized: {url} - Check token validity")
                return None
            else:
                logger.error(f"HTTP error: {e.response.status_code} - {url}")
                raise

        except Exception as e:
            logger.error(f"Request failed: {url} - {str(e)}")
            raise

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def discover_repositories(self) -> list[Repository]:
        """
        Discover repositories from GitHub.

        Returns:
            List of discovered repositories
        """
        start_time = datetime.now(UTC)
        repositories = []
        error_tracker = ErrorTracker()

        logger.info("Starting GitHub repository discovery")

        try:
            # Determine which repositories to discover
            if self.organization:
                url = f"{self.base_url}/orgs/{self.organization}/repos"
                logger.info(f"Discovering repositories for organization: {self.organization}")
            elif self.user:
                url = f"{self.base_url}/users/{self.user}/repos"
                logger.info(f"Discovering repositories for user: {self.user}")
            else:
                # Get authenticated user's repositories
                url = f"{self.base_url}/user/repos"
                logger.info("Discovering repositories for authenticated user")

            # GitHub API pagination
            page = 1
            per_page = 100

            while True:
                params = {
                    "page": page,
                    "per_page": per_page,
                    "sort": "updated",
                    "direction": "desc",
                }

                try:
                    data = await self._make_request("GET", url, params=params)

                    if not data:
                        break

                    # Process repositories
                    for repo_data in data:
                        try:
                            repo = self._parse_repository(repo_data)
                            if repo:
                                repositories.append(repo)
                                error_tracker.record_success(repo.id)
                        except Exception as e:
                            error_tracker.record_error(repo_data.get("id", "unknown"), e)
                            logger.warning(f"Failed to parse repository: {e}")

                    # Check if there are more pages
                    if len(data) < per_page:
                        break

                    page += 1

                except Exception as e:
                    logger.error(f"Failed to fetch repositories page {page}: {e}")
                    break

        except Exception as e:
            logger.error(f"Repository discovery failed: {e}")

        # Log metrics
        duration = (datetime.now(UTC) - start_time).total_seconds()
        summary = error_tracker.get_summary()

        log_operation_metrics(
            operation="github_repository_discovery",
            duration=duration,
            success=summary["failure"] == 0,
            items_processed=summary["total"],
            errors=summary["failure"],
        )

        logger.info(
            f"Discovered {len(repositories)} repositories in {duration:.2f}s "
            f"(errors: {summary['failure']})"
        )

        return repositories

    def _parse_repository(self, data: dict[str, Any]) -> Repository | None:
        """
        Parse GitHub repository data into Repository model.

        Args:
            data: Repository data from GitHub API

        Returns:
            Repository object or None if parsing fails
        """
        try:
            return Repository(
                id=str(data["id"]),
                platform="github",
                url=data["html_url"],
                name=data["name"],
                full_name=data.get("full_name"),
                default_branch=data.get("default_branch"),
                description=data.get("description"),
                language=data.get("language"),
                topics=data.get("topics", []),
                is_private=data.get("private", False),
                is_archived=data.get("archived", False),
                stars=data.get("stargazers_count"),
                forks=data.get("forks_count"),
                open_issues=data.get("open_issues_count"),
                last_activity=(
                    datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
                    if data.get("updated_at")
                    else None
                ),
            )
        except Exception as e:
            logger.error(f"Failed to parse repository data: {e}")
            return None

    async def discover_workflows(self, repo_full_name: str) -> list[dict[str, Any]]:
        """
        Discover GitHub Actions workflows in a repository.

        Args:
            repo_full_name: Repository full name (owner/repo)

        Returns:
            List of workflow definitions
        """
        logger.info(f"Discovering workflows for repository: {repo_full_name}")

        url = f"{self.base_url}/repos/{repo_full_name}/actions/workflows"

        try:
            data = await self._make_request("GET", url)

            if not data or "workflows" not in data:
                return []

            workflows = data["workflows"]
            logger.info(f"Found {len(workflows)} workflows in {repo_full_name}")

            return workflows

        except Exception as e:
            logger.error(f"Failed to discover workflows for {repo_full_name}: {e}")
            return []

    async def discover_workflow_runs(
        self,
        repo_full_name: str,
        workflow_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Discover workflow runs for a repository.

        Args:
            repo_full_name: Repository full name (owner/repo)
            workflow_id: Optional workflow ID to filter by
            limit: Maximum number of runs to fetch

        Returns:
            List of workflow runs
        """
        logger.info(f"Discovering workflow runs for repository: {repo_full_name}")

        if workflow_id:
            url = f"{self.base_url}/repos/{repo_full_name}/actions/workflows/{workflow_id}/runs"
        else:
            url = f"{self.base_url}/repos/{repo_full_name}/actions/runs"

        params = {
            "per_page": min(limit, 100),
            "status": "completed",
        }

        try:
            data = await self._make_request("GET", url, params=params)

            if not data or "workflow_runs" not in data:
                return []

            runs = data["workflow_runs"][:limit]
            logger.info(f"Found {len(runs)} workflow runs in {repo_full_name}")

            return runs

        except Exception as e:
            logger.error(f"Failed to discover workflow runs for {repo_full_name}: {e}")
            return []

    async def discover_deployments(self, repo_full_name: str) -> list[Deployment]:
        """
        Discover deployments for a repository.

        Args:
            repo_full_name: Repository full name (owner/repo)

        Returns:
            List of discovered deployments
        """
        start_time = datetime.now(UTC)
        deployments = []
        error_tracker = ErrorTracker()

        logger.info(f"Discovering deployments for repository: {repo_full_name}")

        url = f"{self.base_url}/repos/{repo_full_name}/deployments"

        try:
            # Get deployments with pagination
            page = 1
            per_page = 100

            while True:
                params = {
                    "page": page,
                    "per_page": per_page,
                }

                try:
                    data = await self._make_request("GET", url, params=params)

                    if not data:
                        break

                    # Process deployments
                    for deploy_data in data:
                        try:
                            deployment = self._parse_deployment(deploy_data, repo_full_name)
                            if deployment:
                                deployments.append(deployment)
                                error_tracker.record_success(deployment.id)
                        except Exception as e:
                            error_tracker.record_error(deploy_data.get("id", "unknown"), e)
                            logger.warning(f"Failed to parse deployment: {e}")

                    # Check if there are more pages
                    if len(data) < per_page:
                        break

                    page += 1

                except Exception as e:
                    logger.error(f"Failed to fetch deployments page {page}: {e}")
                    break

        except Exception as e:
            logger.error(f"Deployment discovery failed: {e}")

        # Log metrics
        duration = (datetime.now(UTC) - start_time).total_seconds()
        summary = error_tracker.get_summary()

        log_operation_metrics(
            operation="github_deployment_discovery",
            duration=duration,
            success=summary["failure"] == 0,
            items_processed=summary["total"],
            errors=summary["failure"],
        )

        logger.info(
            f"Discovered {len(deployments)} deployments in {duration:.2f}s "
            f"(errors: {summary['failure']})"
        )

        return deployments

    def _parse_deployment(
        self,
        data: dict[str, Any],
        repo_full_name: str,
    ) -> Deployment | None:
        """
        Parse GitHub deployment data into Deployment model.

        Args:
            data: Deployment data from GitHub API
            repo_full_name: Repository full name

        Returns:
            Deployment object or None if parsing fails
        """
        try:
            return Deployment(
                id=str(data["id"]),
                pipeline_id=str(data.get("id")),
                pipeline_name=f"{repo_full_name} - {data.get('task', 'deploy')}",
                version=data.get("sha", "unknown"),
                environment=data.get("environment", "production"),
                deployed_at=(
                    datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                    if data.get("created_at")
                    else datetime.now(UTC)
                ),
                deployed_by=data.get("creator", {}).get("login", "unknown"),
                status="success" if data.get("statuses_url") else "pending",
                commit_sha=data.get("sha"),
                notes=data.get("description"),
                artifact_url=data.get("url"),
            )
        except Exception as e:
            logger.error(f"Failed to parse deployment data: {e}")
            return None

    async def discover_applications(self) -> list[Application]:
        """
        Infer applications from repositories.

        This method attempts to identify applications based on repository
        metadata and structure.

        Returns:
            List of inferred applications
        """
        logger.info("Inferring applications from repositories")

        repositories = await self.discover_repositories()
        applications = []

        for repo in repositories:
            # Try to infer application from repository
            # For now, treat each repository as a potential application
            # In the future, we can enhance this with more sophisticated logic

            # Skip archived and forked repositories
            if repo.is_archived:
                continue

            app = Application(
                id=f"github-app-{repo.id}",
                name=repo.name,
                description=repo.description
                or f"Application from GitHub repository {repo.full_name}",
                owner_team=repo.full_name.split("/")[0] if repo.full_name else None,
                repository_url=repo.url,
                repository_id=repo.id,
                environment=self._infer_environment_from_repo(repo),
            )

            applications.append(app)

        logger.info(f"Inferred {len(applications)} applications from repositories")

        return applications

    def _infer_environment_from_repo(self, repo: Repository) -> str | None:
        """
        Infer environment from repository metadata.

        Args:
            repo: Repository object

        Returns:
            Environment string or None
        """
        # Check topics for environment indicators
        if repo.topics:
            topics_lower = [t.lower() for t in repo.topics]
            if "production" in topics_lower or "prod" in topics_lower:
                return "production"
            elif "staging" in topics_lower or "stage" in topics_lower:
                return "staging"
            elif "development" in topics_lower or "dev" in topics_lower:
                return "development"

        # Check repository name
        name_lower = repo.name.lower()
        if "prod" in name_lower:
            return "production"
        elif "staging" in name_lower or "stage" in name_lower:
            return "staging"
        elif "dev" in name_lower:
            return "development"

        # Default to production for non-private repos, dev for private
        return "development" if repo.is_private else "production"
