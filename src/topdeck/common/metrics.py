"""
Prometheus metrics for TopDeck API.

Provides custom metrics for monitoring API performance and resource usage.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import structlog

logger = structlog.get_logger(__name__)

# Request metrics
http_requests_total = Counter(
    "topdeck_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "topdeck_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Resource discovery metrics
discovery_runs_total = Counter(
    "topdeck_discovery_runs_total",
    "Total discovery runs",
    ["cloud_provider", "status"],
)

discovery_resources_found = Gauge(
    "topdeck_discovery_resources_found",
    "Number of resources found in last discovery",
    ["cloud_provider", "resource_type"],
)

discovery_duration_seconds = Histogram(
    "topdeck_discovery_duration_seconds",
    "Discovery run duration in seconds",
    ["cloud_provider"],
    buckets=(10, 30, 60, 120, 300, 600),
)

# Risk analysis metrics
risk_assessments_total = Counter(
    "topdeck_risk_assessments_total",
    "Total risk assessments performed",
    ["resource_type"],
)

risk_score_distribution = Histogram(
    "topdeck_risk_score_distribution",
    "Distribution of risk scores",
    ["resource_type"],
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

single_points_of_failure = Gauge(
    "topdeck_single_points_of_failure",
    "Number of single points of failure detected",
)

# Database metrics
neo4j_query_duration_seconds = Histogram(
    "topdeck_neo4j_query_duration_seconds",
    "Neo4j query duration in seconds",
    ["query_type"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0),
)

neo4j_queries_total = Counter(
    "topdeck_neo4j_queries_total",
    "Total Neo4j queries",
    ["query_type", "status"],
)

redis_operations_total = Counter(
    "topdeck_redis_operations_total",
    "Total Redis operations",
    ["operation", "status"],
)

cache_hits_total = Counter(
    "topdeck_cache_hits_total",
    "Total cache hits",
    ["cache_key_prefix"],
)

cache_misses_total = Counter(
    "topdeck_cache_misses_total",
    "Total cache misses",
    ["cache_key_prefix"],
)


def get_metrics_handler() -> Response:
    """
    Handler for Prometheus metrics endpoint.

    Returns:
        Response with Prometheus metrics in text format
    """
    metrics_output = generate_latest()
    return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)


# Context managers for timing operations

class MetricsTimer:
    """Context manager for timing operations and recording metrics."""

    def __init__(self, histogram: Histogram, *labels):
        """
        Initialize metrics timer.

        Args:
            histogram: Histogram metric to record to
            *labels: Labels for the histogram
        """
        self.histogram = histogram
        self.labels = labels
        self.timer = None

    def __enter__(self):
        """Start the timer."""
        self.timer = self.histogram.labels(*self.labels).time()
        self.timer.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer and record the duration."""
        if self.timer:
            self.timer.__exit__(exc_type, exc_val, exc_tb)


# Helper functions

def record_http_request(method: str, endpoint: str, status_code: int, duration: float) -> None:
    """
    Record an HTTP request.

    Args:
        method: HTTP method
        endpoint: Request endpoint
        status_code: Response status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_discovery_run(cloud_provider: str, status: str, duration: float) -> None:
    """
    Record a discovery run.

    Args:
        cloud_provider: Cloud provider name (azure, aws, gcp)
        status: Run status (success, failure)
        duration: Run duration in seconds
    """
    discovery_runs_total.labels(cloud_provider=cloud_provider, status=status).inc()
    discovery_duration_seconds.labels(cloud_provider=cloud_provider).observe(duration)


def record_resources_found(cloud_provider: str, resource_type: str, count: int) -> None:
    """
    Record the number of resources found.

    Args:
        cloud_provider: Cloud provider name
        resource_type: Type of resource
        count: Number of resources found
    """
    discovery_resources_found.labels(cloud_provider=cloud_provider, resource_type=resource_type).set(count)


def record_risk_assessment(resource_type: str, risk_score: float) -> None:
    """
    Record a risk assessment.

    Args:
        resource_type: Type of resource assessed
        risk_score: Risk score (0.0 to 1.0)
    """
    risk_assessments_total.labels(resource_type=resource_type).inc()
    risk_score_distribution.labels(resource_type=resource_type).observe(risk_score)
