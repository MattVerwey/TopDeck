"""
Code Repository Scanner for Service Bus and Resource Dependencies.

Scans application source code from Azure DevOps repositories to discover
connection strings and resource dependencies, particularly for Service Bus topics/queues.
"""

import json
import re
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None

from ...common.logging_config import get_logger
from ..models import ResourceDependency, DependencyCategory, DependencyType
from .resources import parse_servicebus_connection_string

logger = get_logger(__name__)


class CodeRepositoryScanner:
    """
    Scans application code repositories for resource dependencies.
    
    Focuses on:
    - Service Bus connection strings and topic/queue references
    - Database connection strings
    - Storage account references
    - Other Azure resource references in configuration files
    """

    # Configuration file patterns to scan
    CONFIG_FILES = [
        "appsettings.json",
        "appsettings.*.json",  # appsettings.Production.json, etc.
        "appsettings.Development.json",
        "appsettings.Staging.json",
        "appsettings.Production.json",
        ".env",
        ".env.*",
        "config.json",
        "settings.json",
        "web.config",
        "app.config",
    ]

    # Service Bus connection string pattern
    # Matches: Endpoint=sb://namespace.servicebus.windows.net/;SharedAccessKeyName=...;SharedAccessKey=...
    SERVICEBUS_CONNECTION_PATTERN = re.compile(
        r'Endpoint=sb://([^.]+)\.servicebus\.windows\.net/',
        re.IGNORECASE
    )

    # Service Bus topic/queue name patterns in code
    # Matches: "fifa-1", "nba-5", "test-topic", etc. in context of Service Bus
    SERVICEBUS_TOPIC_PATTERN = re.compile(
        r'(?:topic|queue)(?:Name)?["\s:=]+["\']([a-zA-Z0-9\-_]+)["\']',
        re.IGNORECASE
    )

    # Environment variable patterns that might contain Service Bus references
    SERVICEBUS_ENV_PATTERNS = [
        r'SERVICE_?BUS',
        r'AZURE_?SERVICE_?BUS',
        r'TOPIC_?NAME',
        r'QUEUE_?NAME',
        r'MESSAGING',
    ]

    def __init__(
        self,
        organization: str,
        project: str | None = None,
        personal_access_token: str | None = None,
    ):
        """
        Initialize code repository scanner.

        Args:
            organization: Azure DevOps organization name
            project: Azure DevOps project name (optional - if None, scans all projects)
            personal_access_token: PAT for authentication
        """
        self.organization = organization
        self.project = project
        self.pat = personal_access_token
        self.base_url = (
            f"https://dev.azure.com/{organization}/{project}" 
            if project 
            else f"https://dev.azure.com/{organization}"
        )
        self._client: Any | None = None
        self._headers = self._create_auth_headers()

    def _create_auth_headers(self) -> dict[str, str]:
        """Create authentication headers for Azure DevOps API."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.pat:
            import base64
            auth_string = f":{self.pat}"
            encoded = base64.b64encode(auth_string.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        return headers

    def _get_client(self):
        """Get or create HTTP client."""
        if httpx is None:
            raise ImportError(
                "httpx is required for Azure DevOps API integration. "
                "Install with: pip install httpx"
            )

        if self._client is None:
            self._client = httpx.Client(
                headers=self._headers,
                timeout=30.0,
                follow_redirects=True,
            )

        return self._client

    async def scan_repository_for_servicebus(
        self,
        repository_id: str,
        repository_name: str,
        branch: str = "main",
        discovered_resources: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Scan a repository for Service Bus dependencies.

        Args:
            repository_id: Azure DevOps repository ID
            repository_name: Repository name
            branch: Branch to scan (default: main)
            discovered_resources: Dict of discovered Azure resources (keyed by name or ID)

        Returns:
            Dictionary with scan results:
            {
                "namespaces": ["namespace1", "namespace2"],
                "topics": ["topic1", "topic2"],
                "queues": ["queue1", "queue2"],
                "connection_strings_found": 5,
                "config_files_scanned": ["appsettings.json", ".env"],
            }
        """
        if httpx is None:
            logger.warning("httpx not available, skipping repository scanning")
            return {}

        results = {
            "namespaces": set(),
            "topics": set(),
            "queues": set(),
            "connection_strings_found": 0,
            "config_files_scanned": [],
        }

        try:
            client = self._get_client()

            # Get list of files in repository
            items_url = (
                f"{self.base_url}/_apis/git/repositories/{repository_id}/items"
                f"?recursionLevel=Full&versionDescriptor.version={branch}"
                f"&api-version=7.0"
            )

            response = client.get(items_url)
            if response.status_code != 200:
                logger.warning(
                    f"Failed to get repository items for {repository_name}: {response.status_code}"
                )
                return self._convert_sets_to_lists(results)

            items = response.json().get("value", [])

            # Filter for configuration files
            config_files = [
                item for item in items
                if item.get("gitObjectType") == "blob" and self._is_config_file(item.get("path", ""))
            ]

            logger.info(
                f"Found {len(config_files)} config files in {repository_name}: "
                f"{[f['path'] for f in config_files]}"
            )

            # Scan each configuration file
            for file_item in config_files:
                file_path = file_item.get("path", "")
                results["config_files_scanned"].append(file_path)

                # Get file content
                content_url = (
                    f"{self.base_url}/_apis/git/repositories/{repository_id}/items"
                    f"?path={file_path}&versionDescriptor.version={branch}"
                    f"&api-version=7.0"
                )

                content_response = client.get(content_url)
                if content_response.status_code != 200:
                    logger.debug(f"Failed to get content for {file_path}")
                    continue

                content = content_response.text

                # Parse file for Service Bus references
                file_results = self._parse_file_content(content, file_path, discovered_resources)
                
                # Merge results
                results["namespaces"].update(file_results["namespaces"])
                results["topics"].update(file_results["topics"])
                results["queues"].update(file_results["queues"])
                results["connection_strings_found"] += file_results["connection_strings_found"]

            logger.info(
                f"Repository {repository_name} scan complete: "
                f"{len(results['namespaces'])} namespaces, "
                f"{len(results['topics'])} topics, "
                f"{len(results['queues'])} queues, "
                f"{results['connection_strings_found']} connection strings"
            )

        except Exception as e:
            logger.error(f"Error scanning repository {repository_name}: {e}")

        return self._convert_sets_to_lists(results)

    def _is_config_file(self, file_path: str) -> bool:
        """Check if a file path matches configuration file patterns."""
        file_name = file_path.split("/")[-1].lower()
        
        # Direct matches
        if file_name in [
            "appsettings.json",
            "appsettings.development.json",
            "appsettings.staging.json",
            "appsettings.production.json",
            ".env",
            "config.json",
            "settings.json",
            "web.config",
            "app.config",
        ]:
            return True
        
        # Pattern matches
        if file_name.startswith("appsettings.") and file_name.endswith(".json"):
            return True
        
        if file_name.startswith(".env."):
            return True
        
        return False

    def _parse_file_content(
        self,
        content: str,
        file_path: str,
        discovered_resources: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Parse file content for Service Bus references.

        Args:
            content: File content
            file_path: Path to file (for context)
            discovered_resources: Dict of discovered Azure resources

        Returns:
            Dictionary with parsed results
        """
        results = {
            "namespaces": set(),
            "topics": set(),
            "queues": set(),
            "connection_strings_found": 0,
        }

        # Parse based on file type
        if file_path.endswith(".json"):
            self._parse_json_config(content, results, discovered_resources)
        elif ".env" in file_path.lower():
            self._parse_env_file(content, results, discovered_resources)
        elif file_path.endswith(".config"):
            self._parse_xml_config(content, results, discovered_resources)

        return results

    def _parse_json_config(
        self,
        content: str,
        results: dict[str, Any],
        discovered_resources: dict[str, Any] | None = None,
    ) -> None:
        """Parse JSON configuration file (appsettings.json, etc.)."""
        try:
            config = json.loads(content)
            self._extract_from_dict(config, results, discovered_resources)
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse JSON config: {e}")

    def _parse_env_file(
        self,
        content: str,
        results: dict[str, Any],
        discovered_resources: dict[str, Any] | None = None,
    ) -> None:
        """Parse .env file."""
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                # Check if this is a Service Bus related variable
                if any(re.search(pattern, key, re.IGNORECASE) for pattern in self.SERVICEBUS_ENV_PATTERNS):
                    self._extract_servicebus_info(value, results, discovered_resources)

    def _parse_xml_config(
        self,
        content: str,
        results: dict[str, Any],
        discovered_resources: dict[str, Any] | None = None,
    ) -> None:
        """Parse XML configuration file (web.config, app.config)."""
        # Extract connection strings from XML
        conn_string_pattern = re.compile(
            r'connectionString\s*=\s*["\']([^"\']+)["\']',
            re.IGNORECASE
        )
        
        for match in conn_string_pattern.finditer(content):
            conn_string = match.group(1)
            self._extract_servicebus_info(conn_string, results, discovered_resources)

    def _extract_from_dict(
        self,
        data: dict[str, Any],
        results: dict[str, Any],
        discovered_resources: dict[str, Any] | None = None,
    ) -> None:
        """Recursively extract Service Bus references from dictionary."""
        for key, value in data.items():
            if isinstance(value, dict):
                self._extract_from_dict(value, results, discovered_resources)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._extract_from_dict(item, results, discovered_resources)
                    elif isinstance(item, str):
                        self._extract_servicebus_info(item, results, discovered_resources)
            elif isinstance(value, str):
                self._extract_servicebus_info(value, results, discovered_resources)

    def _extract_servicebus_info(
        self,
        text: str,
        results: dict[str, Any],
        discovered_resources: dict[str, Any] | None = None,
    ) -> None:
        """Extract Service Bus namespace, topic, and queue information from text."""
        if not text:
            return

        # Check for Service Bus connection string
        sb_info = parse_servicebus_connection_string(text)
        if sb_info:
            namespace = sb_info.get("namespace")
            if namespace:
                results["namespaces"].add(namespace)
                results["connection_strings_found"] += 1
                logger.debug(f"Found Service Bus namespace: {namespace}")

        # Check for topic/queue names
        topic_matches = self.SERVICEBUS_TOPIC_PATTERN.findall(text)
        for topic_name in topic_matches:
            # Validate against discovered resources if available
            if discovered_resources:
                # Check if this topic exists in our discovered resources
                if self._validate_topic_exists(topic_name, discovered_resources):
                    results["topics"].add(topic_name)
                    logger.debug(f"Found Service Bus topic: {topic_name}")
            else:
                # No validation, add all found topics
                results["topics"].add(topic_name)

    def _validate_topic_exists(self, topic_name: str, discovered_resources: dict[str, Any]) -> bool:
        """
        Validate if a topic name matches discovered Service Bus resources.

        Args:
            topic_name: Topic name found in code
            discovered_resources: Dict of discovered Azure resources

        Returns:
            True if topic exists in discovered resources
        """
        # Look for Service Bus namespaces with topics property
        for resource in discovered_resources.values():
            if hasattr(resource, "resource_type") and resource.resource_type == "servicebus_namespace":
                topics = resource.properties.get("topics", [])
                if isinstance(topics, list):
                    for topic in topics:
                        if isinstance(topic, dict) and topic.get("name") == topic_name:
                            return True
        
        return False

    def _convert_sets_to_lists(self, results: dict[str, Any]) -> dict[str, Any]:
        """Convert sets to lists for JSON serialization."""
        return {
            "namespaces": list(results["namespaces"]),
            "topics": list(results["topics"]),
            "queues": list(results["queues"]),
            "connection_strings_found": results["connection_strings_found"],
            "config_files_scanned": results["config_files_scanned"],
        }

    async def create_dependencies_from_scan(
        self,
        repository_id: str,
        app_resource_id: str,
        scan_results: dict[str, Any],
        discovered_resources: dict[str, Any],
    ) -> list[ResourceDependency]:
        """
        Create ResourceDependency objects from scan results.

        Args:
            repository_id: Repository ID that was scanned
            app_resource_id: Application resource ID (App Service, etc.)
            scan_results: Results from scan_repository_for_servicebus()
            discovered_resources: Dict of discovered Azure resources

        Returns:
            List of ResourceDependency objects
        """
        dependencies = []

        # Find Service Bus namespace resources
        for namespace_name in scan_results.get("namespaces", []):
            # Find matching namespace resource
            for resource_id, resource in discovered_resources.items():
                if (
                    hasattr(resource, "resource_type") 
                    and resource.resource_type == "servicebus_namespace"
                    and resource.name == namespace_name
                ):
                    dep = ResourceDependency(
                        source_id=app_resource_id,
                        target_id=resource_id,
                        category=DependencyCategory.DATA,
                        dependency_type=DependencyType.REQUIRED,
                        strength=0.95,  # Very strong - found in source code
                        discovered_method="code_repository_scan",
                        description=f"Application uses Service Bus {namespace_name} (found in repository config)",
                    )
                    dependencies.append(dep)
                    logger.info(
                        f"Created dependency: {app_resource_id} -> {resource_id} "
                        f"(Service Bus {namespace_name})"
                    )

        logger.info(
            f"Created {len(dependencies)} dependencies from repository scan of {repository_id}"
        )

        return dependencies

    async def get_all_projects(self) -> list[dict[str, Any]]:
        """
        Get all projects in the Azure DevOps organization.

        Returns:
            List of project dictionaries with 'id' and 'name' keys
        """
        if httpx is None:
            logger.warning("httpx not available, cannot get projects")
            return []

        try:
            client = self._get_client()
            
            # Get all projects in the organization
            projects_url = (
                f"https://dev.azure.com/{self.organization}/_apis/projects"
                f"?api-version=7.0"
            )

            logger.info(f"Fetching projects from: {projects_url}")
            response = client.get(projects_url)
            logger.info(f"Projects API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(
                    f"Failed to get projects: {response.status_code} - {response.text}"
                )
                logger.error(f"Request URL was: {projects_url}")
                logger.error(f"Organization: {self.organization}")
                return []

            projects_data = response.json()
            projects = [
                {"id": p["id"], "name": p["name"]}
                for p in projects_data.get("value", [])
            ]

            logger.info(f"Found {len(projects)} projects in organization {self.organization}")
            return projects

        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []

    async def scan_all_projects_for_servicebus(
        self,
        discovered_resources: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Scan all projects in the organization for Service Bus dependencies.

        Args:
            discovered_resources: Dict of discovered Azure resources (keyed by name or ID)

        Returns:
            Dictionary with aggregated scan results across all projects:
            {
                "projects_scanned": ["Project1", "Project2"],
                "repositories_scanned": 15,
                "namespaces": ["namespace1", "namespace2"],
                "topics": ["topic1", "topic2"],
                "queues": ["queue1"],
                "connection_strings_found": 25,
                "config_files_scanned": 45,
            }
        """
        if httpx is None:
            logger.warning("httpx not available, skipping all-project scanning")
            return {}

        # Get all projects
        projects = await self.get_all_projects()
        if not projects:
            logger.warning("No projects found to scan")
            return {}

        # Aggregated results
        aggregated_results = {
            "projects_scanned": [],
            "repositories_scanned": 0,
            "namespaces": set(),
            "topics": set(),
            "queues": set(),
            "connection_strings_found": 0,
            "config_files_scanned": [],
            "repository_scan_results": [],  # NEW: Store individual repo results for dependency creation
        }

        # Scan each project
        for project in projects:
            project_name = project["name"]
            logger.info(f"Scanning project: {project_name}")

            try:
                # Get repositories for this project
                repos_url = (
                    f"https://dev.azure.com/{self.organization}/{project_name}/_apis/git/repositories"
                    f"?api-version=7.0"
                )

                client = self._get_client()
                response = client.get(repos_url)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to get repositories for project {project_name}")
                    continue

                repositories = response.json().get("value", [])
                logger.info(f"Found {len(repositories)} repositories in project {project_name}")

                # Scan each repository
                for repo in repositories:
                    repo_id = repo["id"]
                    repo_name = repo["name"]

                    # Try scanning different branches
                    for branch in ["main", "master", "develop"]:
                        try:
                            # Create scanner for this specific project
                            project_scanner = CodeRepositoryScanner(
                                organization=self.organization,
                                project=project_name,
                                personal_access_token=self.pat,
                            )

                            scan_results = await project_scanner.scan_repository_for_servicebus(
                                repository_id=repo_id,
                                repository_name=repo_name,
                                branch=branch,
                                discovered_resources=discovered_resources,
                            )

                            if scan_results.get("namespaces") or scan_results.get("topics"):
                                logger.info(
                                    f"Repository {project_name}/{repo_name} ({branch}): "
                                    f"Found {len(scan_results.get('namespaces', []))} namespaces, "
                                    f"{len(scan_results.get('topics', []))} topics"
                                )

                                # Merge aggregated results
                                aggregated_results["namespaces"].update(scan_results.get("namespaces", []))
                                aggregated_results["topics"].update(scan_results.get("topics", []))
                                aggregated_results["queues"].update(scan_results.get("queues", []))
                                aggregated_results["connection_strings_found"] += scan_results.get("connection_strings_found", 0)
                                aggregated_results["config_files_scanned"].extend(scan_results.get("config_files_scanned", []))
                                aggregated_results["repositories_scanned"] += 1

                                # Store individual repo results for dependency creation
                                aggregated_results["repository_scan_results"].append({
                                    "project": project_name,
                                    "repository_id": repo_id,
                                    "repository_name": repo_name,
                                    "branch": branch,
                                    "scan_results": scan_results,
                                })

                                # Found a valid branch, stop trying others
                                break

                        except Exception as branch_error:
                            logger.debug(
                                f"Branch {branch} not found or error in {project_name}/{repo_name}: {branch_error}"
                            )
                            continue

                aggregated_results["projects_scanned"].append(project_name)

            except Exception as project_error:
                logger.error(f"Error scanning project {project_name}: {project_error}")

        # Convert sets to lists
        return {
            "projects_scanned": aggregated_results["projects_scanned"],
            "repositories_scanned": aggregated_results["repositories_scanned"],
            "namespaces": list(aggregated_results["namespaces"]),
            "topics": list(aggregated_results["topics"]),
            "queues": list(aggregated_results["queues"]),
            "connection_strings_found": aggregated_results["connection_strings_found"],
            "config_files_scanned": aggregated_results["config_files_scanned"],
            "repository_scan_results": aggregated_results["repository_scan_results"],
        }

    def close(self):
        """Close HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
