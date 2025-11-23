"""
Baseline calculation and historical comparison for TopDeck.

Provides:
- Baseline calculation for normal service behavior
- Historical comparison (current vs previous periods)
- Deviation detection from baseline
- Trend analysis
"""

import logging
import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Optional

from topdeck.monitoring.prometheus_collector import PrometheusCollector
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics for baseline calculation."""
    
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    REQUEST_RATE = "request_rate"
    ERROR_RATE = "error_rate"
    LATENCY_P50 = "latency_p50"
    LATENCY_P95 = "latency_p95"
    LATENCY_P99 = "latency_p99"


class ComparisonPeriod(str, Enum):
    """Time period for historical comparison."""
    
    PREVIOUS_HOUR = "previous_hour"
    PREVIOUS_DAY = "previous_day"
    PREVIOUS_WEEK = "previous_week"
    SAME_HOUR_YESTERDAY = "same_hour_yesterday"
    SAME_DAY_LAST_WEEK = "same_day_last_week"


@dataclass
class BaselineMetric:
    """Baseline values for a metric."""
    
    metric_name: str
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentile_95: float
    percentile_99: float
    sample_count: int
    calculation_period: str  # e.g., "7 days"
    calculated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Baseline:
    """Complete baseline for a service."""
    
    resource_id: str
    resource_name: str
    metrics: dict[str, BaselineMetric]
    calculated_at: datetime
    valid_until: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricComparison:
    """Comparison between current and historical metric values."""
    
    metric_name: str
    current_value: float
    historical_value: float
    percent_change: float
    absolute_change: float
    is_anomalous: bool  # Exceeds baseline threshold
    deviation_from_baseline: float  # In standard deviations
    trend: str  # "improving", "degrading", "stable"


@dataclass
class HistoricalComparison:
    """Complete historical comparison result."""
    
    resource_id: str
    resource_name: str
    comparison_period: ComparisonPeriod
    current_time: datetime
    historical_time: datetime
    metrics: list[MetricComparison]
    overall_trend: str  # "improving", "degrading", "stable", "mixed"
    anomaly_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


class BaselineAnalyzer:
    """
    Baseline and historical comparison analyzer.
    
    Features:
    - Calculate baseline for normal service behavior
    - Compare current metrics with historical periods
    - Detect deviations from baseline
    - Identify trends
    """
    
    def __init__(
        self,
        prometheus_collector: PrometheusCollector,
        neo4j_client: Neo4jClient,
        baseline_period_days: int = 7,
        anomaly_threshold_stdev: float = 2.0,
    ):
        """
        Initialize baseline analyzer.
        
        Args:
            prometheus_collector: Prometheus collector for metrics
            neo4j_client: Neo4j client for topology
            baseline_period_days: Days of data to use for baseline (default 7)
            anomaly_threshold_stdev: Standard deviations for anomaly detection (default 2.0)
        """
        self.prometheus = prometheus_collector
        self.neo4j = neo4j_client
        self.baseline_period_days = baseline_period_days
        self.anomaly_threshold_stdev = anomaly_threshold_stdev
        
        # Cache for baselines (in production, use Redis or database)
        self.baseline_cache: dict[str, Baseline] = {}
    
    async def calculate_baseline(
        self,
        resource_id: str,
        metrics: Optional[list[MetricType]] = None,
        force_recalculate: bool = False,
    ) -> Baseline:
        """
        Calculate baseline for a service.
        
        Args:
            resource_id: Resource to calculate baseline for
            metrics: List of metrics to include (defaults to all)
            force_recalculate: Force recalculation even if cached
            
        Returns:
            Calculated baseline
        """
        # Check cache
        if not force_recalculate and resource_id in self.baseline_cache:
            cached = self.baseline_cache[resource_id]
            if cached.valid_until > datetime.now(UTC):
                logger.info(f"Using cached baseline for {resource_id}")
                return cached
        
        logger.info(f"Calculating baseline for {resource_id}")
        
        # Get resource info
        resource = await self._get_resource_info(resource_id)
        
        # Default to all metrics if not specified
        if metrics is None:
            metrics = list(MetricType)
        
        # Calculate baseline for each metric
        baseline_metrics = {}
        
        for metric_type in metrics:
            try:
                baseline_metric = await self._calculate_metric_baseline(
                    resource_id,
                    metric_type,
                )
                baseline_metrics[metric_type.value] = baseline_metric
            except Exception as e:
                logger.error(f"Error calculating baseline for {metric_type.value}: {e}")
        
        # Create baseline object
        baseline = Baseline(
            resource_id=resource_id,
            resource_name=resource.get("name", resource_id),
            metrics=baseline_metrics,
            calculated_at=datetime.now(UTC),
            valid_until=datetime.now(UTC) + timedelta(hours=24),  # Valid for 24 hours
            metadata={
                "period_days": self.baseline_period_days,
                "resource_type": resource.get("type", "unknown"),
            },
        )
        
        # Cache the baseline
        self.baseline_cache[resource_id] = baseline
        
        logger.info(f"Baseline calculated for {resource_id} with {len(baseline_metrics)} metrics")
        
        return baseline
    
    async def _get_resource_info(self, resource_id: str) -> dict[str, Any]:
        """Get resource information from Neo4j."""
        query = """
        MATCH (r:Resource {id: $resource_id})
        RETURN r.name as name, r.resource_type as type
        """
        
        result = await self.neo4j.execute_query(query, {"resource_id": resource_id})
        
        if result and len(result) > 0:
            return result[0]
        
        return {"name": resource_id, "type": "unknown"}
    
    async def _calculate_metric_baseline(
        self,
        resource_id: str,
        metric_type: MetricType,
    ) -> BaselineMetric:
        """Calculate baseline for a single metric."""
        # Get historical data
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=self.baseline_period_days)
        
        # Build Prometheus query based on metric type
        query = self._build_prometheus_query(resource_id, metric_type)
        
        # Query Prometheus for historical data
        try:
            data = await self.prometheus.query_range(
                query=query,
                start=start_time,
                end=end_time,
                step="5m",  # 5-minute granularity
            )
            
            # Extract values
            values = []
            if data and len(data) > 0:
                for result in data:
                    if "values" in result:
                        for timestamp, value in result["values"]:
                            try:
                                values.append(float(value))
                            except (ValueError, TypeError):
                                continue
            
            if not values:
                # No data available, return default baseline
                return BaselineMetric(
                    metric_name=metric_type.value,
                    mean=0.0,
                    median=0.0,
                    std_dev=0.0,
                    min_value=0.0,
                    max_value=0.0,
                    percentile_95=0.0,
                    percentile_99=0.0,
                    sample_count=0,
                    calculation_period=f"{self.baseline_period_days} days",
                )
            
            # Calculate statistics
            mean = statistics.mean(values)
            median = statistics.median(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
            min_val = min(values)
            max_val = max(values)
            
            # Calculate percentiles
            sorted_values = sorted(values)
            p95_idx = int(len(sorted_values) * 0.95)
            p99_idx = int(len(sorted_values) * 0.99)
            percentile_95 = sorted_values[p95_idx] if p95_idx < len(sorted_values) else max_val
            percentile_99 = sorted_values[p99_idx] if p99_idx < len(sorted_values) else max_val
            
            return BaselineMetric(
                metric_name=metric_type.value,
                mean=mean,
                median=median,
                std_dev=std_dev,
                min_value=min_val,
                max_value=max_val,
                percentile_95=percentile_95,
                percentile_99=percentile_99,
                sample_count=len(values),
                calculation_period=f"{self.baseline_period_days} days",
            )
            
        except Exception as e:
            logger.error(f"Error querying Prometheus for {metric_type.value}: {e}")
            # Return default baseline on error
            return BaselineMetric(
                metric_name=metric_type.value,
                mean=0.0,
                median=0.0,
                std_dev=0.0,
                min_value=0.0,
                max_value=0.0,
                percentile_95=0.0,
                percentile_99=0.0,
                sample_count=0,
                calculation_period=f"{self.baseline_period_days} days",
            )
    
    def _build_prometheus_query(self, resource_id: str, metric_type: MetricType) -> str:
        """Build Prometheus query for a metric type."""
        # Sanitize resource_id
        safe_id = resource_id.replace("-", "_").replace(".", "_")
        
        if metric_type == MetricType.CPU_USAGE:
            return f'container_cpu_usage_seconds_total{{pod=~"{safe_id}.*"}}'
        elif metric_type == MetricType.MEMORY_USAGE:
            return f'container_memory_usage_bytes{{pod=~"{safe_id}.*"}}'
        elif metric_type == MetricType.REQUEST_RATE:
            return f'rate(http_requests_total{{service="{safe_id}"}}[5m])'
        elif metric_type == MetricType.ERROR_RATE:
            return f'rate(http_requests_total{{service="{safe_id}", status=~"5.."}}[5m])'
        elif metric_type == MetricType.LATENCY_P50:
            return f'histogram_quantile(0.5, http_request_duration_seconds_bucket{{service="{safe_id}"}})'
        elif metric_type == MetricType.LATENCY_P95:
            return f'histogram_quantile(0.95, http_request_duration_seconds_bucket{{service="{safe_id}"}})'
        elif metric_type == MetricType.LATENCY_P99:
            return f'histogram_quantile(0.99, http_request_duration_seconds_bucket{{service="{safe_id}"}})'
        else:
            return f'up{{job="{safe_id}"}}'
    
    async def compare_with_historical(
        self,
        resource_id: str,
        comparison_period: ComparisonPeriod,
        metrics: Optional[list[MetricType]] = None,
    ) -> HistoricalComparison:
        """
        Compare current metrics with historical period.
        
        Args:
            resource_id: Resource to compare
            comparison_period: Which historical period to compare with
            metrics: List of metrics to compare (defaults to all)
            
        Returns:
            Historical comparison result
        """
        logger.info(f"Comparing {resource_id} with {comparison_period.value}")
        
        # Get resource info
        resource = await self._get_resource_info(resource_id)
        
        # Get baseline for anomaly detection
        baseline = await self.calculate_baseline(resource_id, metrics)
        
        # Default to all metrics if not specified
        if metrics is None:
            metrics = list(MetricType)
        
        # Determine time windows
        current_time = datetime.now(UTC)
        historical_time = self._get_historical_time(current_time, comparison_period)
        
        # Compare each metric
        comparisons = []
        anomaly_count = 0
        
        for metric_type in metrics:
            try:
                comparison = await self._compare_metric(
                    resource_id,
                    metric_type,
                    current_time,
                    historical_time,
                    baseline.metrics.get(metric_type.value),
                )
                comparisons.append(comparison)
                if comparison.is_anomalous:
                    anomaly_count += 1
            except Exception as e:
                logger.error(f"Error comparing {metric_type.value}: {e}")
        
        # Determine overall trend
        overall_trend = self._determine_overall_trend(comparisons)
        
        return HistoricalComparison(
            resource_id=resource_id,
            resource_name=resource.get("name", resource_id),
            comparison_period=comparison_period,
            current_time=current_time,
            historical_time=historical_time,
            metrics=comparisons,
            overall_trend=overall_trend,
            anomaly_count=anomaly_count,
            metadata={
                "total_metrics": len(comparisons),
                "baseline_period_days": self.baseline_period_days,
            },
        )
    
    def _get_historical_time(
        self,
        current_time: datetime,
        period: ComparisonPeriod,
    ) -> datetime:
        """Calculate historical timestamp based on comparison period."""
        if period == ComparisonPeriod.PREVIOUS_HOUR:
            return current_time - timedelta(hours=1)
        elif period == ComparisonPeriod.PREVIOUS_DAY:
            return current_time - timedelta(days=1)
        elif period == ComparisonPeriod.PREVIOUS_WEEK:
            return current_time - timedelta(weeks=1)
        elif period == ComparisonPeriod.SAME_HOUR_YESTERDAY:
            return current_time - timedelta(days=1)
        elif period == ComparisonPeriod.SAME_DAY_LAST_WEEK:
            return current_time - timedelta(weeks=1)
        else:
            return current_time - timedelta(hours=1)
    
    async def _compare_metric(
        self,
        resource_id: str,
        metric_type: MetricType,
        current_time: datetime,
        historical_time: datetime,
        baseline_metric: Optional[BaselineMetric],
    ) -> MetricComparison:
        """Compare a metric between current and historical time."""
        # Build query
        query = self._build_prometheus_query(resource_id, metric_type)
        
        # Get current value
        current_value = await self._get_metric_value(query, current_time)
        
        # Get historical value
        historical_value = await self._get_metric_value(query, historical_time)
        
        # Calculate changes
        if historical_value != 0:
            percent_change = ((current_value - historical_value) / historical_value) * 100
        else:
            percent_change = 0 if current_value == 0 else float('inf')
        
        absolute_change = current_value - historical_value
        
        # Check if anomalous (based on baseline)
        is_anomalous = False
        deviation_from_baseline = 0.0
        
        if baseline_metric and baseline_metric.std_dev > 0:
            deviation_from_baseline = (
                (current_value - baseline_metric.mean) / baseline_metric.std_dev
            )
            is_anomalous = abs(deviation_from_baseline) > self.anomaly_threshold_stdev
        
        # Determine trend
        trend = self._determine_trend(
            metric_type,
            current_value,
            historical_value,
            percent_change,
        )
        
        return MetricComparison(
            metric_name=metric_type.value,
            current_value=current_value,
            historical_value=historical_value,
            percent_change=percent_change,
            absolute_change=absolute_change,
            is_anomalous=is_anomalous,
            deviation_from_baseline=deviation_from_baseline,
            trend=trend,
        )
    
    async def _get_metric_value(self, query: str, timestamp: datetime) -> float:
        """Get metric value at a specific timestamp."""
        try:
            # Query Prometheus at specific timestamp
            data = await self.prometheus.query(query, time=timestamp)
            
            if data and len(data) > 0:
                result = data[0]
                if "value" in result and len(result["value"]) > 1:
                    return float(result["value"][1])
            
            return 0.0
        except Exception as e:
            logger.error(f"Error getting metric value: {e}")
            return 0.0
    
    def _determine_trend(
        self,
        metric_type: MetricType,
        current: float,
        historical: float,
        percent_change: float,
    ) -> str:
        """Determine if metric trend is improving, degrading, or stable."""
        # For error rate, lower is better
        # For latency, lower is better
        # For CPU/memory, depends on context (higher could be normal load)
        # For request rate, higher often means more traffic (not necessarily bad)
        
        threshold = 5.0  # 5% change threshold for "stable"
        
        if abs(percent_change) < threshold:
            return "stable"
        
        # Metrics where lower is better
        lower_is_better = {
            MetricType.ERROR_RATE,
            MetricType.LATENCY_P50,
            MetricType.LATENCY_P95,
            MetricType.LATENCY_P99,
        }
        
        if metric_type in lower_is_better:
            return "improving" if current < historical else "degrading"
        else:
            # For other metrics, significant changes are just noted
            return "stable" if abs(percent_change) < threshold else "changed"
    
    def _determine_overall_trend(self, comparisons: list[MetricComparison]) -> str:
        """Determine overall trend from individual metric comparisons."""
        if not comparisons:
            return "unknown"
        
        improving = sum(1 for c in comparisons if c.trend == "improving")
        degrading = sum(1 for c in comparisons if c.trend == "degrading")
        
        if improving > degrading and improving > len(comparisons) * 0.5:
            return "improving"
        elif degrading > improving and degrading > len(comparisons) * 0.5:
            return "degrading"
        elif improving == degrading and improving > 0:
            return "mixed"
        else:
            return "stable"
