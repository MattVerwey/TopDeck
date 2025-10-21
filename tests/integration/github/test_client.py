"""
Tests for GitHub integration client.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from topdeck.integration.github.client import GitHubIntegration


@pytest.fixture
def github_client():
    """Create a GitHub integration client for testing."""
    return GitHubIntegration(
        token="test_token_123",
        organization="test-org",
    )


@pytest.fixture
def sample_repo_data():
    """Sample repository data from GitHub API."""
    return {
        "id": 12345,
        "name": "test-repo",
        "full_name": "test-org/test-repo",
        "html_url": "https://github.com/test-org/test-repo",
        "description": "A test repository",
        "default_branch": "main",
        "language": "Python",
        "topics": ["python", "test", "production"],
        "private": False,
        "archived": False,
        "stargazers_count": 100,
        "forks_count": 20,
        "open_issues_count": 5,
        "updated_at": "2023-10-01T12:00:00Z",
    }


@pytest.fixture
def sample_workflow_data():
    """Sample workflow data from GitHub API."""
    return {
        "id": 67890,
        "name": "CI/CD Pipeline",
        "path": ".github/workflows/deploy.yml",
        "state": "active",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-10-01T12:00:00Z",
    }


@pytest.fixture
def sample_deployment_data():
    """Sample deployment data from GitHub API."""
    return {
        "id": 99999,
        "sha": "abc123def456",
        "task": "deploy",
        "environment": "production",
        "description": "Deploy to production",
        "creator": {"login": "testuser"},
        "created_at": "2023-10-01T12:00:00Z",
        "url": "https://api.github.com/repos/test-org/test-repo/deployments/99999",
        "statuses_url": "https://api.github.com/repos/test-org/test-repo/deployments/99999/statuses",
    }


class TestGitHubIntegration:
    """Test suite for GitHub integration."""

    def test_initialization(self):
        """Test GitHub client initialization."""
        client = GitHubIntegration(
            token="test_token",
            organization="test-org",
            user="test-user",
        )

        assert client.token == "test_token"
        assert client.organization == "test-org"
        assert client.user == "test-user"
        assert client.base_url == "https://api.github.com"
        assert client._client is None

    def test_auth_headers(self, github_client):
        """Test authentication headers creation."""
        headers = github_client._headers

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token_123"
        assert "Accept" in headers
        assert headers["Accept"] == "application/vnd.github.v3+json"

    def test_parse_repository(self, github_client, sample_repo_data):
        """Test repository data parsing."""
        repo = github_client._parse_repository(sample_repo_data)

        assert repo is not None
        assert repo.id == "12345"
        assert repo.platform == "github"
        assert repo.name == "test-repo"
        assert repo.full_name == "test-org/test-repo"
        assert repo.url == "https://github.com/test-org/test-repo"
        assert repo.default_branch == "main"
        assert repo.language == "Python"
        assert "python" in repo.topics
        assert repo.is_private is False
        assert repo.is_archived is False
        assert repo.stars == 100
        assert repo.forks == 20
        assert repo.open_issues == 5

    def test_parse_repository_missing_fields(self, github_client):
        """Test repository parsing with missing optional fields."""
        minimal_data = {
            "id": 12345,
            "name": "test-repo",
            "html_url": "https://github.com/test-org/test-repo",
        }

        repo = github_client._parse_repository(minimal_data)

        assert repo is not None
        assert repo.id == "12345"
        assert repo.name == "test-repo"
        assert repo.description is None
        assert repo.language is None
        assert repo.topics == []

    def test_parse_deployment(self, github_client, sample_deployment_data):
        """Test deployment data parsing."""
        deployment = github_client._parse_deployment(sample_deployment_data, "test-org/test-repo")

        assert deployment is not None
        assert deployment.id == "99999"
        assert deployment.version == "abc123def456"
        assert deployment.environment == "production"
        assert deployment.deployed_by == "testuser"
        assert deployment.status == "success"
        assert deployment.commit_sha == "abc123def456"
        assert deployment.repository_url == "https://github.com/test-org/test-repo"

    def test_infer_environment_from_topics(self, github_client):
        """Test environment inference from repository topics."""
        from topdeck.discovery.models import Repository

        # Test production
        repo_prod = Repository(
            id="1",
            platform="github",
            url="https://github.com/test/repo",
            name="test-repo",
            topics=["production", "python"],
        )
        env = github_client._infer_environment_from_repo(repo_prod)
        assert env == "production"

        # Test staging
        repo_staging = Repository(
            id="2",
            platform="github",
            url="https://github.com/test/repo",
            name="test-repo",
            topics=["staging", "python"],
        )
        env = github_client._infer_environment_from_repo(repo_staging)
        assert env == "staging"

        # Test development
        repo_dev = Repository(
            id="3",
            platform="github",
            url="https://github.com/test/repo",
            name="test-repo",
            topics=["development", "python"],
        )
        env = github_client._infer_environment_from_repo(repo_dev)
        assert env == "development"

    def test_infer_environment_from_name(self, github_client):
        """Test environment inference from repository name."""
        from topdeck.discovery.models import Repository

        # Test production from name
        repo_prod = Repository(
            id="1",
            platform="github",
            url="https://github.com/test/repo",
            name="myapp-prod",
        )
        env = github_client._infer_environment_from_repo(repo_prod)
        assert env == "production"

        # Test staging from name
        repo_staging = Repository(
            id="2",
            platform="github",
            url="https://github.com/test/repo",
            name="myapp-staging",
        )
        env = github_client._infer_environment_from_repo(repo_staging)
        assert env == "staging"

    def test_infer_environment_default(self, github_client):
        """Test default environment inference."""
        from topdeck.discovery.models import Repository

        # Public repo defaults to production
        repo_public = Repository(
            id="1",
            platform="github",
            url="https://github.com/test/repo",
            name="myapp",
            is_private=False,
        )
        env = github_client._infer_environment_from_repo(repo_public)
        assert env == "production"

        # Private repo defaults to development
        repo_private = Repository(
            id="2",
            platform="github",
            url="https://github.com/test/repo",
            name="myapp",
            is_private=True,
        )
        env = github_client._infer_environment_from_repo(repo_private)
        assert env == "development"


@pytest.mark.asyncio
class TestGitHubIntegrationAsync:
    """Test suite for asynchronous GitHub integration operations."""

    async def test_discover_repositories(self, github_client, sample_repo_data):
        """Test repository discovery."""
        # Mock the HTTP client
        mock_response = [sample_repo_data]

        with patch.object(
            github_client, "_make_request", return_value=mock_response
        ) as mock_request:
            repos = await github_client.discover_repositories()

            assert len(repos) == 1
            assert repos[0].name == "test-repo"
            assert repos[0].full_name == "test-org/test-repo"

            # Verify API was called correctly
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"
            assert "orgs/test-org/repos" in call_args[0][1]

    async def test_discover_repositories_pagination(self, github_client, sample_repo_data):
        """Test repository discovery with pagination."""
        # Create 150 repos to test pagination (100 per page)
        repos_page1 = [{**sample_repo_data, "id": i, "name": f"repo-{i}"} for i in range(100)]
        repos_page2 = [{**sample_repo_data, "id": i, "name": f"repo-{i}"} for i in range(100, 150)]

        # Mock pagination
        call_count = 0

        async def mock_make_request(method, url, params=None, json_data=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return repos_page1
            elif call_count == 2:
                return repos_page2
            else:
                return []

        with patch.object(github_client, "_make_request", side_effect=mock_make_request):
            repos = await github_client.discover_repositories()

            assert len(repos) == 150
            assert call_count == 2

    async def test_discover_workflows(self, github_client, sample_workflow_data):
        """Test workflow discovery."""
        mock_response = {"workflows": [sample_workflow_data]}

        with patch.object(github_client, "_make_request", return_value=mock_response):
            workflows = await github_client.discover_workflows("test-org/test-repo")

            assert len(workflows) == 1
            assert workflows[0]["name"] == "CI/CD Pipeline"

    async def test_discover_workflow_runs(self, github_client):
        """Test workflow run discovery."""
        mock_run = {
            "id": 12345,
            "name": "Deploy",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2023-10-01T12:00:00Z",
        }
        mock_response = {"workflow_runs": [mock_run]}

        with patch.object(github_client, "_make_request", return_value=mock_response):
            runs = await github_client.discover_workflow_runs("test-org/test-repo")

            assert len(runs) == 1
            assert runs[0]["name"] == "Deploy"
            assert runs[0]["conclusion"] == "success"

    async def test_discover_deployments(self, github_client, sample_deployment_data):
        """Test deployment discovery."""
        mock_response = [sample_deployment_data]

        with patch.object(github_client, "_make_request", return_value=mock_response):
            deployments = await github_client.discover_deployments("test-org/test-repo")

            assert len(deployments) == 1
            assert deployments[0].environment == "production"
            assert deployments[0].deployed_by == "testuser"

    async def test_discover_applications(self, github_client, sample_repo_data):
        """Test application inference from repositories."""
        mock_response = [sample_repo_data]

        with patch.object(github_client, "_make_request", return_value=mock_response):
            apps = await github_client.discover_applications()

            assert len(apps) == 1
            assert apps[0].name == "test-repo"
            assert apps[0].repository_url == "https://github.com/test-org/test-repo"
            assert apps[0].environment == "production"  # From topics

    async def test_error_handling_404(self, github_client):
        """Test handling of 404 errors."""
        import httpx

        # Create a mock response with 404
        mock_response = MagicMock()
        mock_response.status_code = 404

        # Create mock exception
        mock_error = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)

        with patch.object(github_client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request.side_effect = mock_error
            mock_get_client.return_value = mock_client

            # Should return None instead of raising
            result = await github_client._make_request("GET", "https://api.github.com/test")
            assert result is None

    async def test_rate_limiting(self, github_client):
        """Test rate limiting behavior."""
        # Rate limiter should be called for each request
        assert github_client._rate_limiter.max_calls == 80
        assert github_client._rate_limiter.time_window == 60.0

    async def test_close_client(self, github_client):
        """Test closing the HTTP client."""
        # Create a mock client
        mock_client = AsyncMock()
        github_client._client = mock_client

        await github_client.close()

        mock_client.aclose.assert_called_once()
        assert github_client._client is None
