"""
Azure Log Analytics collector.

Collects and queries logs from Azure Log Analytics for transaction tracing,
error tracking, and correlation with resource topology.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx
from azure.core.credentials import AccessToken
from azure.identity import DefaultAzureCredential


@dataclass
class LogAnalyticsEntry:
    """Represents a single log entry from Azure Log Analytics."""

    timestamp: datetime
    message: str
    properties: dict[str, Any]
    resource_id: str
    correlation_id: str | None = None
    operation_name: str | None = None
    level: str = "info"


@dataclass
class TransactionTrace:
    """Represents a trace of a transaction through the system."""

    transaction_id: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    entries: list[LogAnalyticsEntry]
    resource_path: list[str]
    error_count: int
    warning_count: int


class AzureLogAnalyticsCollector:
    """Collector for Azure Log Analytics logs."""

    def __init__(
        self, workspace_id: str, credential: DefaultAzureCredential | None = None, timeout: int = 30
    ):
        """
        Initialize Azure Log Analytics collector.

        Args:
            workspace_id: Azure Log Analytics workspace ID
            credential: Azure credential (defaults to DefaultAzureCredential)
            timeout: Request timeout in seconds
        """
        self.workspace_id = workspace_id
        self.credential = credential or DefaultAzureCredential()
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.base_url = f"https://api.loganalytics.io/v1/workspaces/{workspace_id}/query"
        self._access_token: AccessToken | None = None

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def _get_access_token(self) -> str:
        """Get Azure access token for Log Analytics API."""
        if (
            self._access_token is None
            or self._access_token.expires_on < datetime.utcnow().timestamp()
        ):
            # Get token synchronously (azure-identity doesn't support async yet)
            self._access_token = self.credential.get_token("https://api.loganalytics.io/.default")
        return self._access_token.token

    async def query(self, query: str, timespan: str | None = None) -> list[dict[str, Any]]:
        """
        Execute a KQL (Kusto Query Language) query.

        Args:
            query: KQL query string
            timespan: ISO8601 time span (e.g., "PT1H" for 1 hour)

        Returns:
            List of query results
        """
        try:
            token = await self._get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            body = {"query": query}
            if timespan:
                body["timespan"] = timespan

            response = await self.client.post(self.base_url, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Parse results
            tables = data.get("tables", [])
            if not tables:
                return []

            # Get first table (usually only one)
            table = tables[0]
            columns = table.get("columns", [])
            rows = table.get("rows", [])

            # Convert to list of dicts
            results = []
            for row in rows:
                result = {}
                for i, col in enumerate(columns):
                    result[col["name"]] = row[i]
                results.append(result)

            return results
        except Exception:
            return []

    async def get_logs_by_correlation_id(
        self, correlation_id: str, duration: timedelta = timedelta(hours=1)
    ) -> list[LogAnalyticsEntry]:
        """
        Get all logs for a specific correlation/transaction ID.

        Args:
            correlation_id: Transaction/correlation ID to trace
            duration: Time range to search (backwards from now)

        Returns:
            List of log entries ordered by timestamp
        """
        # Build KQL query to find logs with correlation_id
        timespan = f"PT{int(duration.total_seconds() / 3600)}H"

        query = f"""
        union isfuzzy=true
            AppTraces,
            AppRequests,
            AppDependencies,
            AppExceptions,
            ContainerLog
        | where CorrelationId == '{correlation_id}'
            or Properties['correlation_id'] == '{correlation_id}'
            or Properties['transaction_id'] == '{correlation_id}'
            or Message contains '{correlation_id}'
        | project
            TimeGenerated,
            Message,
            Properties,
            ResourceId = coalesce(ResourceId, _ResourceId, ''),
            CorrelationId = coalesce(CorrelationId, Properties['correlation_id'], Properties['transaction_id'], ''),
            OperationName = coalesce(OperationName, Properties['operation_name'], ''),
            Level = coalesce(SeverityLevel, Properties['level'], 'Information')
        | order by TimeGenerated asc
        """

        results = await self.query(query, timespan)

        entries = []
        for result in results:
            entries.append(
                LogAnalyticsEntry(
                    timestamp=datetime.fromisoformat(
                        result["TimeGenerated"].replace("Z", "+00:00")
                    ),
                    message=result.get("Message", ""),
                    properties=result.get("Properties", {}),
                    resource_id=result.get("ResourceId", ""),
                    correlation_id=result.get("CorrelationId"),
                    operation_name=result.get("OperationName"),
                    level=self._normalize_level(result.get("Level", "Information")),
                )
            )

        return entries

    async def trace_transaction_flow(
        self, correlation_id: str, duration: timedelta = timedelta(hours=1)
    ) -> TransactionTrace | None:
        """
        Trace a transaction through the system using correlation ID.

        Args:
            correlation_id: Transaction/correlation ID to trace
            duration: Time range to search

        Returns:
            TransactionTrace with complete flow information
        """
        entries = await self.get_logs_by_correlation_id(correlation_id, duration)

        if not entries:
            return None

        # Extract resource path (order of resources touched)
        resource_path = []
        seen_resources = set()
        for entry in entries:
            if entry.resource_id and entry.resource_id not in seen_resources:
                resource_path.append(entry.resource_id)
                seen_resources.add(entry.resource_id)

        # Count errors and warnings
        error_count = sum(1 for e in entries if e.level in ("error", "critical", "fatal"))
        warning_count = sum(1 for e in entries if e.level == "warning")

        # Calculate duration
        start_time = entries[0].timestamp
        end_time = entries[-1].timestamp
        duration_ms = (end_time - start_time).total_seconds() * 1000

        return TransactionTrace(
            transaction_id=correlation_id,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            entries=entries,
            resource_path=resource_path,
            error_count=error_count,
            warning_count=warning_count,
        )

    async def get_resource_logs(
        self, resource_id: str, level: str | None = None, duration: timedelta = timedelta(hours=1)
    ) -> list[LogAnalyticsEntry]:
        """
        Get logs for a specific resource.

        Args:
            resource_id: Azure resource ID
            level: Filter by log level (error, warn, info, etc.)
            duration: Time range to query

        Returns:
            List of log entries
        """
        timespan = f"PT{int(duration.total_seconds() / 3600)}H"

        level_filter = ""
        if level:
            level_filter = f"| where Level == '{level.capitalize()}'"

        query = f"""
        union isfuzzy=true
            AppTraces,
            AppRequests,
            AppDependencies,
            ContainerLog
        | where ResourceId == '{resource_id}' or _ResourceId == '{resource_id}'
        {level_filter}
        | project
            TimeGenerated,
            Message,
            Properties,
            ResourceId = coalesce(ResourceId, _ResourceId, ''),
            CorrelationId = coalesce(CorrelationId, Properties['correlation_id'], ''),
            OperationName = coalesce(OperationName, Properties['operation_name'], ''),
            Level = coalesce(SeverityLevel, Properties['level'], 'Information')
        | order by TimeGenerated desc
        | limit 1000
        """

        results = await self.query(query, timespan)

        entries = []
        for result in results:
            entries.append(
                LogAnalyticsEntry(
                    timestamp=datetime.fromisoformat(
                        result["TimeGenerated"].replace("Z", "+00:00")
                    ),
                    message=result.get("Message", ""),
                    properties=result.get("Properties", {}),
                    resource_id=result.get("ResourceId", ""),
                    correlation_id=result.get("CorrelationId"),
                    operation_name=result.get("OperationName"),
                    level=self._normalize_level(result.get("Level", "Information")),
                )
            )

        return entries

    async def find_correlation_ids_for_resource(
        self, resource_id: str, duration: timedelta = timedelta(hours=1), limit: int = 100
    ) -> list[str]:
        """
        Find correlation IDs associated with a resource.

        Args:
            resource_id: Azure resource ID
            duration: Time range to search
            limit: Maximum number of correlation IDs to return

        Returns:
            List of unique correlation IDs
        """
        timespan = f"PT{int(duration.total_seconds() / 3600)}H"

        query = f"""
        union isfuzzy=true
            AppTraces,
            AppRequests,
            AppDependencies,
            ContainerLog
        | where ResourceId == '{resource_id}' or _ResourceId == '{resource_id}'
        | where isnotempty(CorrelationId)
            or isnotempty(Properties['correlation_id'])
            or isnotempty(Properties['transaction_id'])
        | project CorrelationId = coalesce(
            CorrelationId,
            Properties['correlation_id'],
            Properties['transaction_id']
        )
        | where isnotempty(CorrelationId)
        | distinct CorrelationId
        | limit {limit}
        """

        results = await self.query(query, timespan)
        return [r["CorrelationId"] for r in results if r.get("CorrelationId")]

    def _normalize_level(self, level: str) -> str:
        """Normalize log level to standard format."""
        level_lower = level.lower()

        if level_lower in ("0", "verbose", "trace", "debug"):
            return "debug"
        elif level_lower in ("1", "information", "info"):
            return "info"
        elif level_lower in ("2", "warning", "warn"):
            return "warning"
        elif level_lower in ("3", "error"):
            return "error"
        elif level_lower in ("4", "critical", "fatal"):
            return "critical"
        else:
            return "info"
