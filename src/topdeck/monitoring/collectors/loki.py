"""
Loki log collector.

Collects and queries logs from Loki for error tracking, failure analysis,
and correlation with resource topology.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx


@dataclass
class LogEntry:
    """Represents a single log entry."""
    
    timestamp: datetime
    message: str
    labels: Dict[str, str]
    level: str


@dataclass
class LogStream:
    """Represents a stream of log entries."""
    
    labels: Dict[str, str]
    entries: List[LogEntry]


@dataclass
class ErrorAnalysis:
    """Analysis of errors from logs."""
    
    resource_id: str
    error_count: int
    error_types: Dict[str, int]
    recent_errors: List[LogEntry]
    error_rate: float


class LokiCollector:
    """Collector for Loki logs."""
    
    def __init__(self, loki_url: str, timeout: int = 30):
        """
        Initialize Loki collector.
        
        Args:
            loki_url: URL of Loki server (e.g., "http://loki:3100")
            timeout: Request timeout in seconds
        """
        self.loki_url = loki_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
    
    async def query(
        self,
        query: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[LogStream]:
        """
        Execute a LogQL query.
        
        Args:
            query: LogQL query string
            start: Start time (default: 1 hour ago)
            end: End time (default: now)
            limit: Maximum number of entries
            
        Returns:
            List of log streams
        """
        if not start:
            start = datetime.utcnow() - timedelta(hours=1)
        if not end:
            end = datetime.utcnow()
        
        url = f"{self.loki_url}/loki/api/v1/query_range"
        params = {
            "query": query,
            "start": int(start.timestamp() * 1e9),  # Nanoseconds
            "end": int(end.timestamp() * 1e9),
            "limit": limit,
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "success":
                return self._parse_streams(data.get("data", {}).get("result", []))
            return []
        except Exception:
            return []
    
    async def get_resource_logs(
        self,
        resource_id: str,
        level: Optional[str] = None,
        duration: timedelta = timedelta(hours=1)
    ) -> List[LogStream]:
        """
        Get logs for a specific resource.
        
        Args:
            resource_id: Resource identifier
            level: Filter by log level (error, warn, info, etc.)
            duration: Time range to query
            
        Returns:
            List of log streams
        """
        # Build LogQL query
        query_parts = [f'{{resource_id="{resource_id}"}}']
        
        if level:
            query_parts.append(f'|~ "(?i)level.*{level}"')
        
        query = "".join(query_parts)
        
        end = datetime.utcnow()
        start = end - duration
        
        return await self.query(query, start, end)
    
    async def get_error_logs(
        self,
        resource_id: Optional[str] = None,
        duration: timedelta = timedelta(hours=1)
    ) -> List[LogStream]:
        """
        Get error logs, optionally filtered by resource.
        
        Args:
            resource_id: Optional resource identifier
            duration: Time range to query
            
        Returns:
            List of error log streams
        """
        # Build LogQL query for errors
        if resource_id:
            query = f'{{resource_id="{resource_id}"}} |~ "(?i)(error|exception|fatal|critical)"'
        else:
            query = '{job=~".+"} |~ "(?i)(error|exception|fatal|critical)"'
        
        end = datetime.utcnow()
        start = end - duration
        
        return await self.query(query, start, end)
    
    async def analyze_errors(
        self,
        resource_id: str,
        duration: timedelta = timedelta(hours=1)
    ) -> ErrorAnalysis:
        """
        Analyze errors for a specific resource.
        
        Args:
            resource_id: Resource identifier
            duration: Time range to analyze
            
        Returns:
            ErrorAnalysis with error statistics and details
        """
        error_streams = await self.get_error_logs(resource_id, duration)
        
        error_count = 0
        error_types: Dict[str, int] = {}
        recent_errors: List[LogEntry] = []
        
        for stream in error_streams:
            for entry in stream.entries:
                error_count += 1
                
                # Extract error type from message
                error_type = self._extract_error_type(entry.message)
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
                # Keep most recent errors
                if len(recent_errors) < 10:
                    recent_errors.append(entry)
        
        # Sort recent errors by timestamp
        recent_errors.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Calculate error rate (errors per minute)
        duration_minutes = duration.total_seconds() / 60
        error_rate = error_count / duration_minutes if duration_minutes > 0 else 0
        
        return ErrorAnalysis(
            resource_id=resource_id,
            error_count=error_count,
            error_types=error_types,
            recent_errors=recent_errors[:10],
            error_rate=error_rate,
        )
    
    async def correlate_errors_with_flow(
        self,
        flow_path: List[str],
        duration: timedelta = timedelta(hours=1)
    ) -> Dict[str, ErrorAnalysis]:
        """
        Correlate errors across resources in a data flow.
        
        Args:
            flow_path: List of resource IDs in the flow
            duration: Time range to analyze
            
        Returns:
            Dictionary mapping resource IDs to their error analysis
        """
        error_analyses = {}
        
        for resource_id in flow_path:
            analysis = await self.analyze_errors(resource_id, duration)
            if analysis.error_count > 0:
                error_analyses[resource_id] = analysis
        
        return error_analyses
    
    async def find_failure_point(
        self,
        flow_path: List[str],
        duration: timedelta = timedelta(minutes=30)
    ) -> Optional[Dict[str, Any]]:
        """
        Find the failure point in a data flow.
        
        Args:
            flow_path: List of resource IDs in the flow
            duration: Time range to analyze
            
        Returns:
            Dictionary with failure point details, or None if no failure detected
        """
        error_analyses = await self.correlate_errors_with_flow(flow_path, duration)
        
        if not error_analyses:
            return None
        
        # Find resource with highest error rate
        max_error_rate = 0.0
        failure_point = None
        
        for resource_id, analysis in error_analyses.items():
            if analysis.error_rate > max_error_rate:
                max_error_rate = analysis.error_rate
                failure_point = {
                    "resource_id": resource_id,
                    "error_rate": analysis.error_rate,
                    "error_count": analysis.error_count,
                    "error_types": analysis.error_types,
                    "recent_errors": [
                        {
                            "timestamp": e.timestamp.isoformat(),
                            "message": e.message,
                            "level": e.level,
                        }
                        for e in analysis.recent_errors[:5]
                    ]
                }
        
        return failure_point
    
    def _parse_streams(self, results: List[Dict[str, Any]]) -> List[LogStream]:
        """Parse Loki query results into LogStream objects."""
        streams = []
        
        for result in results:
            labels = result.get("stream", {})
            values = result.get("values", [])
            
            entries = []
            for value in values:
                # value is [timestamp_ns, message]
                timestamp_ns = int(value[0])
                message = value[1]
                
                # Extract log level from message
                level = self._extract_log_level(message)
                
                entries.append(LogEntry(
                    timestamp=datetime.fromtimestamp(timestamp_ns / 1e9),
                    message=message,
                    labels=labels,
                    level=level,
                ))
            
            streams.append(LogStream(
                labels=labels,
                entries=entries,
            ))
        
        return streams
    
    def _extract_log_level(self, message: str) -> str:
        """Extract log level from message."""
        message_lower = message.lower()
        
        if "fatal" in message_lower or "critical" in message_lower:
            return "fatal"
        elif "error" in message_lower:
            return "error"
        elif "warn" in message_lower:
            return "warn"
        elif "info" in message_lower:
            return "info"
        elif "debug" in message_lower:
            return "debug"
        else:
            return "unknown"
    
    def _extract_error_type(self, message: str) -> str:
        """Extract error type from message."""
        # Common error patterns
        if "timeout" in message.lower():
            return "TimeoutError"
        elif "connection" in message.lower():
            return "ConnectionError"
        elif "database" in message.lower() or "sql" in message.lower():
            return "DatabaseError"
        elif "authentication" in message.lower() or "auth" in message.lower():
            return "AuthenticationError"
        elif "permission" in message.lower() or "forbidden" in message.lower():
            return "PermissionError"
        elif "not found" in message.lower() or "404" in message:
            return "NotFoundError"
        elif "500" in message or "internal server error" in message.lower():
            return "InternalServerError"
        else:
            return "UnknownError"
