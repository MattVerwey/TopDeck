"""
Dependency Health Dashboard.

Addresses Market Gap #5: Service Dependency Health Dashboard

Problem:
- During incidents, SREs need to quickly see which dependencies are healthy
- Current dashboards show individual service health, not dependency health
- No quick view of "is my database healthy? is my cache healthy?"

Solution:
- Real-time health status of all dependencies
- Latency/error rate to each dependency
- Connection pool status
- Historical dependency health trends
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class DependencyType(str, Enum):
    """Type of dependency."""

    DATABASE = "database"
    CACHE = "cache"
    API = "api"
    MESSAGE_QUEUE = "message_queue"
    STORAGE = "storage"
    EXTERNAL = "external"


@dataclass
class ConnectionPoolStatus:
    """Status of a connection pool."""

    pool_name: str
    total_connections: int
    active_connections: int
    idle_connections: int
    waiting_requests: int
    max_connections: int
    utilization_percent: float
    status: HealthStatus
    last_updated: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pool_name": self.pool_name,
            "total_connections": self.total_connections,
            "active_connections": self.active_connections,
            "idle_connections": self.idle_connections,
            "waiting_requests": self.waiting_requests,
            "max_connections": self.max_connections,
            "utilization_percent": self.utilization_percent,
            "status": self.status.value,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class DependencyMetrics:
    """Metrics for a dependency."""

    latency_p50_ms: float | None = None
    latency_p95_ms: float | None = None
    latency_p99_ms: float | None = None
    request_rate_per_sec: float | None = None
    error_rate_percent: float | None = None
    success_rate_percent: float | None = None
    timeout_rate_percent: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "latency_p50_ms": self.latency_p50_ms,
            "latency_p95_ms": self.latency_p95_ms,
            "latency_p99_ms": self.latency_p99_ms,
            "request_rate_per_sec": self.request_rate_per_sec,
            "error_rate_percent": self.error_rate_percent,
            "success_rate_percent": self.success_rate_percent,
            "timeout_rate_percent": self.timeout_rate_percent,
        }


@dataclass
class DependencyStatus:
    """Complete status of a single dependency."""

    dependency_id: str
    dependency_name: str
    dependency_type: DependencyType
    status: HealthStatus
    health_score: float  # 0-100
    metrics: DependencyMetrics
    connection_pool: ConnectionPoolStatus | None
    circuit_breaker_status: str | None  # "closed", "open", "half-open"
    last_success: datetime | None
    last_failure: datetime | None
    failure_count_1h: int
    anomalies: list[str]
    last_updated: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "dependency_id": self.dependency_id,
            "dependency_name": self.dependency_name,
            "dependency_type": self.dependency_type.value,
            "status": self.status.value,
            "health_score": self.health_score,
            "metrics": self.metrics.to_dict(),
            "connection_pool": self.connection_pool.to_dict() if self.connection_pool else None,
            "circuit_breaker_status": self.circuit_breaker_status,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "failure_count_1h": self.failure_count_1h,
            "anomalies": self.anomalies,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class HistoricalDataPoint:
    """A single data point in historical trend."""

    timestamp: datetime
    health_score: float
    latency_p95_ms: float | None
    error_rate_percent: float | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "health_score": self.health_score,
            "latency_p95_ms": self.latency_p95_ms,
            "error_rate_percent": self.error_rate_percent,
        }


@dataclass
class DependencyTimeline:
    """Historical health timeline for a dependency."""

    dependency_id: str
    dependency_name: str
    time_range_start: datetime
    time_range_end: datetime
    data_points: list[HistoricalDataPoint]
    average_health_score: float
    degraded_periods: list[tuple[datetime, datetime]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "dependency_id": self.dependency_id,
            "dependency_name": self.dependency_name,
            "time_range_start": self.time_range_start.isoformat(),
            "time_range_end": self.time_range_end.isoformat(),
            "data_points": [dp.to_dict() for dp in self.data_points],
            "average_health_score": self.average_health_score,
            "degraded_periods": [
                {"start": s.isoformat(), "end": e.isoformat()}
                for s, e in self.degraded_periods
            ],
        }


@dataclass
class DependencyHealthReport:
    """Complete health report for all dependencies of a service."""

    resource_id: str
    resource_name: str
    overall_health: HealthStatus
    overall_health_score: float
    dependencies: list[DependencyStatus]
    critical_issues: list[str]
    recommendations: list[str]
    generated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "overall_health": self.overall_health.value,
            "overall_health_score": self.overall_health_score,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "critical_issues": self.critical_issues,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass
class DashboardSummary:
    """Summary for the dependency health dashboard."""

    total_services: int
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    total_dependencies: int
    healthy_dependencies: int
    critical_alerts: list[str]
    top_issues: list[dict[str, Any]]
    generated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_services": self.total_services,
            "healthy_services": self.healthy_services,
            "degraded_services": self.degraded_services,
            "unhealthy_services": self.unhealthy_services,
            "total_dependencies": self.total_dependencies,
            "healthy_dependencies": self.healthy_dependencies,
            "critical_alerts": self.critical_alerts,
            "top_issues": self.top_issues,
            "generated_at": self.generated_at.isoformat(),
        }


class DependencyHealthMonitor:
    """
    Monitor for dependency health.

    This addresses the critical SRE need to quickly see which dependencies
    are healthy during incidents.

    Features:
    - Real-time health status of all dependencies
    - Latency/error rate to each dependency
    - Connection pool status
    - Historical dependency health trends
    """

    # Health score thresholds
    HEALTHY_THRESHOLD = 80
    DEGRADED_THRESHOLD = 50

    # Metric thresholds
    LATENCY_WARNING_MS = 200
    LATENCY_CRITICAL_MS = 500
    ERROR_RATE_WARNING = 1.0  # 1%
    ERROR_RATE_CRITICAL = 5.0  # 5%
    POOL_WARNING_PERCENT = 70
    POOL_CRITICAL_PERCENT = 90

    def __init__(
        self,
        prometheus_collector: Any = None,
        neo4j_client: Any = None,
    ):
        """
        Initialize the dependency health monitor.

        Args:
            prometheus_collector: Prometheus metrics collector
            neo4j_client: Neo4j client for topology
        """
        self.prometheus = prometheus_collector
        self.neo4j = neo4j_client
        self._health_cache: dict[str, DependencyHealthReport] = {}
        self._cache_ttl_seconds = 30

    async def get_dependency_health(
        self,
        resource_id: str,
    ) -> DependencyHealthReport:
        """
        Get comprehensive health status of all dependencies for a resource.

        Args:
            resource_id: Resource identifier

        Returns:
            DependencyHealthReport with all dependency statuses
        """
        now = datetime.now(UTC)

        # Check cache
        cached = self._health_cache.get(resource_id)
        if cached and (now - cached.generated_at).total_seconds() < self._cache_ttl_seconds:
            return cached

        logger.info("Getting dependency health", resource_id=resource_id)

        # Get resource name
        resource_name = await self._get_resource_name(resource_id)

        # Get all dependencies
        dependencies = await self._get_dependencies(resource_id)

        # Collect health status for each dependency
        dependency_statuses: list[DependencyStatus] = []
        for dep in dependencies:
            status = await self._get_dependency_status(resource_id, dep)
            dependency_statuses.append(status)

        # Calculate overall health
        overall_score = self._calculate_overall_health(dependency_statuses)
        overall_status = self._score_to_status(overall_score)

        # Identify critical issues
        critical_issues = self._identify_critical_issues(dependency_statuses)

        # Generate recommendations
        recommendations = self._generate_recommendations(dependency_statuses)

        report = DependencyHealthReport(
            resource_id=resource_id,
            resource_name=resource_name,
            overall_health=overall_status,
            overall_health_score=overall_score,
            dependencies=dependency_statuses,
            critical_issues=critical_issues,
            recommendations=recommendations,
            generated_at=now,
        )

        # Cache the report
        self._health_cache[resource_id] = report

        return report

    async def get_dependency_timeline(
        self,
        resource_id: str,
        dependency_id: str,
        hours: int = 24,
    ) -> DependencyTimeline:
        """
        Get historical health timeline for a specific dependency.

        Args:
            resource_id: Resource identifier
            dependency_id: Dependency identifier
            hours: Number of hours of history (default 24)

        Returns:
            DependencyTimeline with historical data
        """
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=hours)

        # Get dependency name
        dep_name = await self._get_resource_name(dependency_id)

        # Get historical metrics from Prometheus
        data_points = await self._get_historical_metrics(
            resource_id, dependency_id, start_time, end_time
        )

        # Calculate average health score
        if data_points:
            avg_score = sum(dp.health_score for dp in data_points) / len(data_points)
        else:
            avg_score = 100.0

        # Find degraded periods
        degraded_periods = self._find_degraded_periods(data_points)

        return DependencyTimeline(
            dependency_id=dependency_id,
            dependency_name=dep_name,
            time_range_start=start_time,
            time_range_end=end_time,
            data_points=data_points,
            average_health_score=avg_score,
            degraded_periods=degraded_periods,
        )

    async def get_dashboard_summary(self) -> DashboardSummary:
        """
        Get summary for the dependency health dashboard.

        Returns:
            DashboardSummary with overall system health
        """
        now = datetime.now(UTC)

        # Get all services from Neo4j
        services = await self._get_all_services()

        healthy_services = 0
        degraded_services = 0
        unhealthy_services = 0
        total_dependencies = 0
        healthy_dependencies = 0
        critical_alerts: list[str] = []
        top_issues: list[dict[str, Any]] = []

        for service_id in services:
            try:
                report = await self.get_dependency_health(service_id)

                # Count service health
                if report.overall_health == HealthStatus.HEALTHY:
                    healthy_services += 1
                elif report.overall_health == HealthStatus.DEGRADED:
                    degraded_services += 1
                else:
                    unhealthy_services += 1

                # Count dependencies
                total_dependencies += len(report.dependencies)
                healthy_dependencies += sum(
                    1 for d in report.dependencies if d.status == HealthStatus.HEALTHY
                )

                # Collect critical alerts
                if report.overall_health == HealthStatus.UNHEALTHY:
                    critical_alerts.append(
                        f"{report.resource_name} is unhealthy: {report.critical_issues[0] if report.critical_issues else 'Unknown issue'}"
                    )

                # Collect top issues
                for issue in report.critical_issues[:2]:
                    top_issues.append({
                        "service": report.resource_name,
                        "issue": issue,
                        "severity": "critical",
                    })
            except Exception as e:
                logger.warning(
                    "Failed to get health for service",
                    service_id=service_id,
                    error=str(e),
                )
                unhealthy_services += 1

        # Sort and limit top issues
        top_issues = top_issues[:10]

        return DashboardSummary(
            total_services=len(services),
            healthy_services=healthy_services,
            degraded_services=degraded_services,
            unhealthy_services=unhealthy_services,
            total_dependencies=total_dependencies,
            healthy_dependencies=healthy_dependencies,
            critical_alerts=critical_alerts[:5],
            top_issues=top_issues,
            generated_at=now,
        )

    # Private helper methods

    async def _get_resource_name(self, resource_id: str) -> str:
        """Get the resource name from Neo4j."""
        if not self.neo4j:
            return resource_id

        try:
            query = """
            MATCH (r:Resource {resource_id: $resource_id})
            RETURN r.name as name
            """
            results = await self.neo4j.execute_query(query, {"resource_id": resource_id})
            if results:
                return results[0].get("name", resource_id)
        except Exception:
            pass

        return resource_id

    async def _get_dependencies(
        self,
        resource_id: str,
    ) -> list[dict[str, Any]]:
        """Get list of dependencies for a resource."""
        if not self.neo4j:
            return []

        try:
            query = """
            MATCH (r:Resource {resource_id: $resource_id})-[:DEPENDS_ON]->(d:Resource)
            RETURN d.resource_id as id,
                   d.name as name,
                   d.resource_type as type
            """
            results = await self.neo4j.execute_query(query, {"resource_id": resource_id})
            return [
                {
                    "id": r.get("id", ""),
                    "name": r.get("name", ""),
                    "type": r.get("type", ""),
                }
                for r in results
            ]
        except Exception as e:
            logger.warning("Failed to get dependencies", error=str(e))
            return []

    async def _get_all_services(self) -> list[str]:
        """Get all service IDs from Neo4j."""
        if not self.neo4j:
            return []

        try:
            query = """
            MATCH (r:Resource)
            WHERE r.resource_type IN ['kubernetes_deployment', 'app_service', 'function_app', 'container_app', 'aks_cluster']
            RETURN r.resource_id as id
            LIMIT 100
            """
            results = await self.neo4j.execute_query(query, {})
            return [r.get("id", "") for r in results if r.get("id")]
        except Exception as e:
            logger.warning("Failed to get services", error=str(e))
            return []

    async def _get_dependency_status(
        self,
        source_id: str,
        dependency: dict[str, Any],
    ) -> DependencyStatus:
        """Get complete status for a single dependency."""
        dep_id = dependency["id"]
        dep_name = dependency["name"]
        dep_type = self._categorize_dependency_type(dependency["type"])

        now = datetime.now(UTC)

        # Get metrics from Prometheus
        metrics = await self._get_dependency_metrics(source_id, dep_id)

        # Get connection pool status
        pool_status = await self._get_connection_pool_status(source_id, dep_id)

        # Get circuit breaker status
        cb_status = await self._get_circuit_breaker_status(source_id, dep_id)

        # Calculate health score
        health_score = self._calculate_health_score(metrics, pool_status)
        status = self._score_to_status(health_score)

        # Detect anomalies
        anomalies = self._detect_anomalies(metrics, pool_status)

        # Get recent failure count
        failure_count = await self._get_failure_count(source_id, dep_id, hours=1)

        return DependencyStatus(
            dependency_id=dep_id,
            dependency_name=dep_name,
            dependency_type=dep_type,
            status=status,
            health_score=health_score,
            metrics=metrics,
            connection_pool=pool_status,
            circuit_breaker_status=cb_status,
            last_success=now,  # Would need to track this properly
            last_failure=None,
            failure_count_1h=failure_count,
            anomalies=anomalies,
            last_updated=now,
        )

    async def _get_dependency_metrics(
        self,
        source_id: str,
        dep_id: str,
    ) -> DependencyMetrics:
        """Get metrics for a dependency."""
        if not self.prometheus:
            return DependencyMetrics()

        metrics = DependencyMetrics()
        sanitized_source = source_id.replace("-", "_")
        sanitized_dep = dep_id.replace("-", "_")

        try:
            # Latency metrics
            latency_queries = {
                "p50": f'histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{{source=~".*{sanitized_source}.*",target=~".*{sanitized_dep}.*"}}[5m]))',
                "p95": f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{source=~".*{sanitized_source}.*",target=~".*{sanitized_dep}.*"}}[5m]))',
                "p99": f'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{{source=~".*{sanitized_source}.*",target=~".*{sanitized_dep}.*"}}[5m]))',
            }

            for percentile, query in latency_queries.items():
                result = await self.prometheus.query(query)
                if result and "data" in result:
                    for item in result["data"].get("result", []):
                        if item.get("value"):
                            value_ms = float(item["value"][1]) * 1000
                            if percentile == "p50":
                                metrics.latency_p50_ms = value_ms
                            elif percentile == "p95":
                                metrics.latency_p95_ms = value_ms
                            elif percentile == "p99":
                                metrics.latency_p99_ms = value_ms
                            break

            # Request rate
            rate_query = f'sum(rate(http_requests_total{{source=~".*{sanitized_source}.*",target=~".*{sanitized_dep}.*"}}[5m]))'
            rate_result = await self.prometheus.query(rate_query)
            if rate_result and "data" in rate_result:
                for item in rate_result["data"].get("result", []):
                    if item.get("value"):
                        metrics.request_rate_per_sec = float(item["value"][1])
                        break

            # Error rate
            error_query = f'sum(rate(http_requests_total{{source=~".*{sanitized_source}.*",target=~".*{sanitized_dep}.*",status=~"5.."}}[5m])) / sum(rate(http_requests_total{{source=~".*{sanitized_source}.*",target=~".*{sanitized_dep}.*"}}[5m])) * 100'
            error_result = await self.prometheus.query(error_query)
            if error_result and "data" in error_result:
                for item in error_result["data"].get("result", []):
                    if item.get("value"):
                        error_rate = float(item["value"][1])
                        if not (error_rate != error_rate):  # Check for NaN
                            metrics.error_rate_percent = error_rate
                            metrics.success_rate_percent = 100 - error_rate
                        break

        except Exception as e:
            logger.warning("Failed to get dependency metrics", error=str(e))

        return metrics

    async def _get_connection_pool_status(
        self,
        source_id: str,
        dep_id: str,
    ) -> ConnectionPoolStatus | None:
        """Get connection pool status for a dependency."""
        if not self.prometheus:
            return None

        sanitized_source = source_id.replace("-", "_")
        sanitized_dep = dep_id.replace("-", "_")

        try:
            # Look for common connection pool metrics
            pool_queries = {
                "active": f'db_pool_active_connections{{service=~".*{sanitized_source}.*",database=~".*{sanitized_dep}.*"}}',
                "idle": f'db_pool_idle_connections{{service=~".*{sanitized_source}.*",database=~".*{sanitized_dep}.*"}}',
                "max": f'db_pool_max_connections{{service=~".*{sanitized_source}.*",database=~".*{sanitized_dep}.*"}}',
                "waiting": f'db_pool_waiting_requests{{service=~".*{sanitized_source}.*",database=~".*{sanitized_dep}.*"}}',
            }

            pool_data: dict[str, float] = {}
            for metric_name, query in pool_queries.items():
                result = await self.prometheus.query(query)
                if result and "data" in result:
                    for item in result["data"].get("result", []):
                        if item.get("value"):
                            pool_data[metric_name] = float(item["value"][1])
                            break

            if not pool_data:
                return None

            active = int(pool_data.get("active", 0))
            idle = int(pool_data.get("idle", 0))
            max_conns = int(pool_data.get("max", 100))
            waiting = int(pool_data.get("waiting", 0))
            total = active + idle
            utilization = (active / max_conns * 100) if max_conns > 0 else 0

            # Determine pool status
            if utilization >= self.POOL_CRITICAL_PERCENT or waiting > 0:
                pool_status = HealthStatus.UNHEALTHY
            elif utilization >= self.POOL_WARNING_PERCENT:
                pool_status = HealthStatus.DEGRADED
            else:
                pool_status = HealthStatus.HEALTHY

            return ConnectionPoolStatus(
                pool_name=f"{source_id}->{dep_id}",
                total_connections=total,
                active_connections=active,
                idle_connections=idle,
                waiting_requests=waiting,
                max_connections=max_conns,
                utilization_percent=utilization,
                status=pool_status,
                last_updated=datetime.now(UTC),
            )

        except Exception as e:
            logger.warning("Failed to get connection pool status", error=str(e))

        return None

    async def _get_circuit_breaker_status(
        self,
        source_id: str,
        dep_id: str,
    ) -> str | None:
        """Get circuit breaker status for a dependency."""
        if not self.prometheus:
            return None

        sanitized_source = source_id.replace("-", "_")
        sanitized_dep = dep_id.replace("-", "_")

        try:
            # Look for circuit breaker metrics (common patterns)
            cb_query = f'circuit_breaker_state{{source=~".*{sanitized_source}.*",target=~".*{sanitized_dep}.*"}}'
            result = await self.prometheus.query(cb_query)

            if result and "data" in result:
                for item in result["data"].get("result", []):
                    state = item.get("metric", {}).get("state", "")
                    if state:
                        return state

            # Try alternative metric names
            for metric_name in ["hystrix_circuit_breaker_open", "resilience4j_circuitbreaker_state"]:
                alt_query = f'{metric_name}{{source=~".*{sanitized_source}.*",target=~".*{sanitized_dep}.*"}}'
                result = await self.prometheus.query(alt_query)
                if result and "data" in result:
                    for item in result["data"].get("result", []):
                        if item.get("value"):
                            value = float(item["value"][1])
                            return "open" if value == 1 else "closed"

        except Exception:
            pass

        return None

    async def _get_failure_count(
        self,
        source_id: str,
        dep_id: str,
        hours: int = 1,
    ) -> int:
        """Get failure count for a dependency in the last N hours."""
        if not self.prometheus:
            return 0

        sanitized_source = source_id.replace("-", "_")
        sanitized_dep = dep_id.replace("-", "_")

        try:
            query = f'sum(increase(http_requests_total{{source=~".*{sanitized_source}.*",target=~".*{sanitized_dep}.*",status=~"5.."}}[{hours}h]))'
            result = await self.prometheus.query(query)

            if result and "data" in result:
                for item in result["data"].get("result", []):
                    if item.get("value"):
                        return int(float(item["value"][1]))

        except Exception:
            pass

        return 0

    async def _get_historical_metrics(
        self,
        source_id: str,
        dep_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[HistoricalDataPoint]:
        """Get historical metrics for a dependency."""
        if not self.prometheus:
            return []

        data_points: list[HistoricalDataPoint] = []
        sanitized_source = source_id.replace("-", "_")
        sanitized_dep = dep_id.replace("-", "_")

        try:
            # Query historical latency
            latency_query = f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{source=~".*{sanitized_source}.*",target=~".*{sanitized_dep}.*"}}[5m]))'
            latency_result = await self.prometheus.query_range(
                latency_query,
                start=start_time,
                end=end_time,
                step="5m",
            )

            # Query historical error rate
            error_query = f'sum(rate(http_requests_total{{source=~".*{sanitized_source}.*",target=~".*{sanitized_dep}.*",status=~"5.."}}[5m])) / sum(rate(http_requests_total{{source=~".*{sanitized_source}.*",target=~".*{sanitized_dep}.*"}}[5m])) * 100'
            error_result = await self.prometheus.query_range(
                error_query,
                start=start_time,
                end=end_time,
                step="5m",
            )

            # Combine results
            latency_data = {}
            if latency_result and "data" in latency_result:
                for item in latency_result["data"].get("result", []):
                    for ts, value in item.get("values", []):
                        latency_data[ts] = float(value) * 1000  # Convert to ms

            error_data = {}
            if error_result and "data" in error_result:
                for item in error_result["data"].get("result", []):
                    for ts, value in item.get("values", []):
                        error_data[ts] = float(value)

            # Create data points
            all_timestamps = set(latency_data.keys()) | set(error_data.keys())
            for ts in sorted(all_timestamps):
                latency = latency_data.get(ts)
                error_rate = error_data.get(ts)

                # Calculate health score
                health_score = 100.0
                if latency and latency > self.LATENCY_CRITICAL_MS:
                    health_score -= 30
                elif latency and latency > self.LATENCY_WARNING_MS:
                    health_score -= 15

                if error_rate and error_rate > self.ERROR_RATE_CRITICAL:
                    health_score -= 40
                elif error_rate and error_rate > self.ERROR_RATE_WARNING:
                    health_score -= 20

                data_points.append(
                    HistoricalDataPoint(
                        timestamp=datetime.fromtimestamp(ts, tz=UTC),
                        health_score=max(0, health_score),
                        latency_p95_ms=latency,
                        error_rate_percent=error_rate,
                    )
                )

        except Exception as e:
            logger.warning("Failed to get historical metrics", error=str(e))

        return data_points

    def _categorize_dependency_type(self, resource_type: str) -> DependencyType:
        """Categorize resource type into dependency type."""
        type_lower = resource_type.lower()

        if any(db in type_lower for db in ["sql", "database", "postgres", "mysql", "mongodb", "cosmos"]):
            return DependencyType.DATABASE
        elif any(cache in type_lower for cache in ["redis", "memcached", "cache", "elasticache"]):
            return DependencyType.CACHE
        elif any(queue in type_lower for queue in ["queue", "rabbitmq", "servicebus", "sqs", "kafka"]):
            return DependencyType.MESSAGE_QUEUE
        elif any(storage in type_lower for storage in ["storage", "blob", "s3", "bucket"]):
            return DependencyType.STORAGE
        elif any(ext in type_lower for ext in ["external", "third-party", "api-gateway"]):
            return DependencyType.EXTERNAL
        else:
            return DependencyType.API

    def _calculate_health_score(
        self,
        metrics: DependencyMetrics,
        pool_status: ConnectionPoolStatus | None,
    ) -> float:
        """Calculate health score from metrics."""
        score = 100.0

        # Latency impact
        if metrics.latency_p95_ms:
            if metrics.latency_p95_ms > self.LATENCY_CRITICAL_MS:
                score -= 25
            elif metrics.latency_p95_ms > self.LATENCY_WARNING_MS:
                score -= 10

        # Error rate impact
        if metrics.error_rate_percent:
            if metrics.error_rate_percent > self.ERROR_RATE_CRITICAL:
                score -= 35
            elif metrics.error_rate_percent > self.ERROR_RATE_WARNING:
                score -= 15

        # Connection pool impact
        if pool_status:
            if pool_status.utilization_percent >= self.POOL_CRITICAL_PERCENT:
                score -= 20
            elif pool_status.utilization_percent >= self.POOL_WARNING_PERCENT:
                score -= 10

            if pool_status.waiting_requests > 0:
                score -= 10

        return max(0, score)

    def _score_to_status(self, score: float) -> HealthStatus:
        """Convert health score to status."""
        if score >= self.HEALTHY_THRESHOLD:
            return HealthStatus.HEALTHY
        elif score >= self.DEGRADED_THRESHOLD:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

    def _calculate_overall_health(
        self,
        dependencies: list[DependencyStatus],
    ) -> float:
        """Calculate overall health from all dependencies."""
        if not dependencies:
            return 100.0

        # Weighted average - unhealthy dependencies have more impact
        total_weight = 0
        weighted_sum = 0

        for dep in dependencies:
            if dep.status == HealthStatus.UNHEALTHY:
                weight = 3
            elif dep.status == HealthStatus.DEGRADED:
                weight = 2
            else:
                weight = 1

            weighted_sum += dep.health_score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 100.0

    def _identify_critical_issues(
        self,
        dependencies: list[DependencyStatus],
    ) -> list[str]:
        """Identify critical issues from dependencies."""
        issues: list[str] = []

        for dep in dependencies:
            if dep.status == HealthStatus.UNHEALTHY:
                if dep.metrics.error_rate_percent and dep.metrics.error_rate_percent > self.ERROR_RATE_CRITICAL:
                    issues.append(
                        f"{dep.dependency_name}: High error rate ({dep.metrics.error_rate_percent:.1f}%)"
                    )
                if dep.metrics.latency_p95_ms and dep.metrics.latency_p95_ms > self.LATENCY_CRITICAL_MS:
                    issues.append(
                        f"{dep.dependency_name}: High latency ({dep.metrics.latency_p95_ms:.0f}ms)"
                    )
                if dep.circuit_breaker_status == "open":
                    issues.append(
                        f"{dep.dependency_name}: Circuit breaker is OPEN"
                    )
                if dep.connection_pool and dep.connection_pool.waiting_requests > 0:
                    issues.append(
                        f"{dep.dependency_name}: Connection pool exhausted "
                        f"({dep.connection_pool.waiting_requests} requests waiting)"
                    )

        return issues

    def _detect_anomalies(
        self,
        metrics: DependencyMetrics,
        pool_status: ConnectionPoolStatus | None,
    ) -> list[str]:
        """Detect anomalies in dependency metrics."""
        anomalies: list[str] = []

        if metrics.latency_p95_ms and metrics.latency_p95_ms > self.LATENCY_CRITICAL_MS:
            anomalies.append(f"Latency spike: {metrics.latency_p95_ms:.0f}ms (threshold: {self.LATENCY_CRITICAL_MS}ms)")

        if metrics.error_rate_percent and metrics.error_rate_percent > self.ERROR_RATE_CRITICAL:
            anomalies.append(f"High error rate: {metrics.error_rate_percent:.1f}% (threshold: {self.ERROR_RATE_CRITICAL}%)")

        if pool_status:
            if pool_status.utilization_percent >= self.POOL_CRITICAL_PERCENT:
                anomalies.append(f"Connection pool near exhaustion: {pool_status.utilization_percent:.0f}% utilized")
            if pool_status.waiting_requests > 0:
                anomalies.append(f"Connection pool contention: {pool_status.waiting_requests} requests waiting")

        return anomalies

    def _generate_recommendations(
        self,
        dependencies: list[DependencyStatus],
    ) -> list[str]:
        """Generate recommendations based on dependency health."""
        recommendations: list[str] = []

        for dep in dependencies:
            if dep.status == HealthStatus.UNHEALTHY:
                if dep.circuit_breaker_status == "open":
                    recommendations.append(
                        f"Check {dep.dependency_name} availability - circuit breaker is protecting the system"
                    )
                if dep.metrics.error_rate_percent and dep.metrics.error_rate_percent > self.ERROR_RATE_CRITICAL:
                    recommendations.append(
                        f"Investigate errors in {dep.dependency_name} - consider implementing retry with backoff"
                    )
                if dep.connection_pool and dep.connection_pool.utilization_percent >= self.POOL_CRITICAL_PERCENT:
                    recommendations.append(
                        f"Increase connection pool size for {dep.dependency_name} or investigate slow queries"
                    )

            elif dep.status == HealthStatus.DEGRADED:
                if dep.metrics.latency_p95_ms and dep.metrics.latency_p95_ms > self.LATENCY_WARNING_MS:
                    recommendations.append(
                        f"Monitor {dep.dependency_name} latency - consider caching or query optimization"
                    )

        if not recommendations:
            recommendations.append("All dependencies are healthy - no action required")

        return recommendations

    def _find_degraded_periods(
        self,
        data_points: list[HistoricalDataPoint],
    ) -> list[tuple[datetime, datetime]]:
        """Find periods where health was degraded."""
        degraded_periods: list[tuple[datetime, datetime]] = []

        in_degraded = False
        period_start: datetime | None = None

        for dp in data_points:
            is_degraded = dp.health_score < self.HEALTHY_THRESHOLD

            if is_degraded and not in_degraded:
                # Start of degraded period
                period_start = dp.timestamp
                in_degraded = True
            elif not is_degraded and in_degraded:
                # End of degraded period
                if period_start:
                    degraded_periods.append((period_start, dp.timestamp))
                in_degraded = False
                period_start = None

        # Handle case where still degraded at end
        if in_degraded and period_start and data_points:
            degraded_periods.append((period_start, data_points[-1].timestamp))

        return degraded_periods
