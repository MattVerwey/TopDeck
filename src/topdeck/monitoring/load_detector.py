"""
Load change detector for Prometheus metrics.

Detects load changes when new pods/services are added or when traffic increases,
based on historical Prometheus metrics and patterns.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog

from topdeck.monitoring.collectors.prometheus import PrometheusCollector

logger = structlog.get_logger(__name__)


@dataclass
class LoadBaseline:
    """Baseline metrics for a service before load changes."""

    resource_id: str
    timestamp: datetime
    pod_count: int
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_request_rate: float
    avg_latency_p95: float
    avg_error_rate: float


@dataclass
class ScalingEvent:
    """Represents a scaling event detected in the infrastructure."""

    resource_id: str
    timestamp: datetime
    pod_count_before: int
    pod_count_after: int
    scaling_type: str  # "scale_up" or "scale_down"


@dataclass
class LoadImpact:
    """Impact of load changes on service metrics."""

    resource_id: str
    scaling_event: ScalingEvent
    baseline: LoadBaseline
    cpu_change_pct: float
    memory_change_pct: float
    request_rate_change_pct: float
    latency_change_pct: float
    error_rate_change_pct: float
    overall_impact: str  # "minimal", "moderate", "significant", "critical"
    recommendations: list[str]
    time_to_stabilize_minutes: float | None


@dataclass
class LoadPrediction:
    """Prediction of load impact based on historical patterns."""

    resource_id: str
    predicted_pod_count: int
    predicted_cpu_usage: float
    predicted_memory_usage: float
    predicted_request_rate: float
    predicted_latency_p95: float
    predicted_error_rate: float
    confidence: float  # 0.0 to 1.0
    based_on_events: list[ScalingEvent]
    recommendations: list[str]


class LoadChangeDetector:
    """
    Detects and analyzes load changes in services.

    Monitors Prometheus metrics to:
    1. Detect when new pods/services are added
    2. Measure the impact on load (CPU, memory, latency, errors)
    3. Correlate load increases with scaling events
    4. Predict future load based on historical patterns
    """

    def __init__(self, prometheus_collector: PrometheusCollector):
        """
        Initialize load change detector.

        Args:
            prometheus_collector: PrometheusCollector instance for metrics
        """
        self.prometheus = prometheus_collector
        self.scaling_event_cache: dict[str, list[ScalingEvent]] = {}

    async def detect_scaling_events(
        self, resource_id: str, lookback_hours: int = 24
    ) -> list[ScalingEvent]:
        """
        Detect pod/service scaling events from Prometheus metrics.

        Args:
            resource_id: Resource to monitor
            lookback_hours: How far back to look for events

        Returns:
            List of detected scaling events
        """
        logger.info("detect_scaling_events", resource_id=resource_id, lookback_hours=lookback_hours)

        end = datetime.now(UTC)
        start = end - timedelta(hours=lookback_hours)

        # Query pod count over time
        # This assumes metrics like kube_deployment_status_replicas exist
        query = f'kube_deployment_status_replicas{{deployment=~".*{resource_id}.*"}}'
        results = await self.prometheus.query_range(query, start, end, "5m")

        scaling_events = []

        if not results:
            logger.info("no_scaling_data", resource_id=resource_id)
            return scaling_events

        # Analyze pod count changes
        for result in results:
            values = result.get("values", [])

            if len(values) < 2:
                continue

            # Look for significant changes in pod count
            for i in range(1, len(values)):
                prev_timestamp, prev_count = values[i - 1]
                curr_timestamp, curr_count = values[i]

                prev_count = int(float(prev_count))
                curr_count = int(float(curr_count))

                # Detect change in pod count
                if prev_count != curr_count:
                    scaling_type = "scale_up" if curr_count > prev_count else "scale_down"

                    event = ScalingEvent(
                        resource_id=resource_id,
                        timestamp=datetime.fromtimestamp(curr_timestamp, UTC),
                        pod_count_before=prev_count,
                        pod_count_after=curr_count,
                        scaling_type=scaling_type,
                    )
                    scaling_events.append(event)

                    logger.info(
                        "scaling_event_detected",
                        resource_id=resource_id,
                        from_pods=prev_count,
                        to_pods=curr_count,
                        type=scaling_type,
                    )

        # Cache for later use
        self.scaling_event_cache[resource_id] = scaling_events

        return scaling_events

    async def get_load_baseline(
        self, resource_id: str, at_time: datetime | None = None
    ) -> LoadBaseline:
        """
        Get baseline load metrics for a resource.

        Args:
            resource_id: Resource to analyze
            at_time: Time point to measure baseline (default: now)

        Returns:
            LoadBaseline with current or historical metrics
        """
        if at_time is None:
            at_time = datetime.now(UTC)

        logger.info("get_load_baseline", resource_id=resource_id, at_time=at_time)

        # Get metrics around the specified time
        start = at_time - timedelta(minutes=15)
        end = at_time

        # Query multiple metrics
        metrics = {}

        # Pod count
        pod_query = f'kube_deployment_status_replicas{{deployment=~".*{resource_id}.*"}}'
        pod_results = await self.prometheus.query_range(pod_query, start, end, "1m")

        # CPU usage
        cpu_query = f'rate(container_cpu_usage_seconds_total{{pod=~".*{resource_id}.*"}}[5m])'
        cpu_results = await self.prometheus.query_range(cpu_query, start, end, "1m")

        # Memory usage
        memory_query = f'container_memory_usage_bytes{{pod=~".*{resource_id}.*"}}'
        memory_results = await self.prometheus.query_range(memory_query, start, end, "1m")

        # Request rate
        request_query = f'rate(http_requests_total{{pod=~".*{resource_id}.*"}}[5m])'
        request_results = await self.prometheus.query_range(request_query, start, end, "1m")

        # Latency
        latency_query = f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{pod=~".*{resource_id}.*"}}[5m]))'
        latency_results = await self.prometheus.query_range(latency_query, start, end, "1m")

        # Error rate
        error_query = f'rate(http_requests_total{{pod=~".*{resource_id}.*", status=~"5.."}}[5m]) / rate(http_requests_total{{pod=~".*{resource_id}.*"}}[5m])'
        error_results = await self.prometheus.query_range(error_query, start, end, "1m")

        # Calculate averages from results
        pod_count = self._extract_avg_value(pod_results, default=1)
        avg_cpu = self._extract_avg_value(cpu_results, default=0.5)
        avg_memory = self._extract_avg_value(memory_results, default=1024 * 1024 * 512)  # 512MB
        avg_request_rate = self._extract_avg_value(request_results, default=100.0)
        avg_latency = self._extract_avg_value(latency_results, default=0.2)
        avg_error_rate = self._extract_avg_value(error_results, default=0.01)

        return LoadBaseline(
            resource_id=resource_id,
            timestamp=at_time,
            pod_count=int(pod_count),
            avg_cpu_usage=avg_cpu,
            avg_memory_usage=avg_memory,
            avg_request_rate=avg_request_rate,
            avg_latency_p95=avg_latency,
            avg_error_rate=avg_error_rate,
        )

    async def analyze_load_impact(
        self, resource_id: str, scaling_event: ScalingEvent
    ) -> LoadImpact:
        """
        Analyze the impact of a scaling event on load metrics.

        Args:
            resource_id: Resource that was scaled
            scaling_event: The scaling event to analyze

        Returns:
            LoadImpact with detailed analysis
        """
        logger.info("analyze_load_impact", resource_id=resource_id, scaling_event_timestamp=scaling_event.timestamp)

        # Get baseline before scaling
        baseline = await self.get_load_baseline(
            resource_id, at_time=scaling_event.timestamp - timedelta(minutes=5)
        )

        # Get metrics after scaling (allow time to stabilize)
        post_scaling_time = scaling_event.timestamp + timedelta(minutes=10)
        post_baseline = await self.get_load_baseline(resource_id, at_time=post_scaling_time)

        # Calculate percentage changes
        cpu_change = self._calculate_pct_change(baseline.avg_cpu_usage, post_baseline.avg_cpu_usage)
        memory_change = self._calculate_pct_change(
            baseline.avg_memory_usage, post_baseline.avg_memory_usage
        )
        request_change = self._calculate_pct_change(
            baseline.avg_request_rate, post_baseline.avg_request_rate
        )
        latency_change = self._calculate_pct_change(
            baseline.avg_latency_p95, post_baseline.avg_latency_p95
        )
        error_change = self._calculate_pct_change(
            baseline.avg_error_rate, post_baseline.avg_error_rate
        )

        # Determine overall impact
        impact_level = self._determine_impact_level(
            cpu_change, memory_change, latency_change, error_change
        )

        # Calculate stabilization time
        stabilization_time = await self._estimate_stabilization_time(resource_id, scaling_event)

        # Generate recommendations
        recommendations = self._generate_load_recommendations(
            scaling_event, cpu_change, memory_change, latency_change, error_change, impact_level
        )

        return LoadImpact(
            resource_id=resource_id,
            scaling_event=scaling_event,
            baseline=baseline,
            cpu_change_pct=cpu_change,
            memory_change_pct=memory_change,
            request_rate_change_pct=request_change,
            latency_change_pct=latency_change,
            error_rate_change_pct=error_change,
            overall_impact=impact_level,
            recommendations=recommendations,
            time_to_stabilize_minutes=stabilization_time,
        )

    async def predict_load_impact(
        self, resource_id: str, target_pod_count: int, lookback_days: int = 30
    ) -> LoadPrediction:
        """
        Predict load impact based on historical scaling patterns.

        Args:
            resource_id: Resource to predict for
            target_pod_count: Desired pod count
            lookback_days: How far back to look for historical patterns

        Returns:
            LoadPrediction with forecasted metrics
        """
        logger.info(
            "predict_load_impact",
            resource_id=resource_id,
            target_pod_count=target_pod_count,
            lookback_days=lookback_days,
        )

        # Get historical scaling events
        scaling_events = await self.detect_scaling_events(
            resource_id, lookback_hours=lookback_days * 24
        )

        if not scaling_events:
            logger.warning("no_historical_data", resource_id=resource_id)
            # Return prediction based on current baseline
            baseline = await self.get_load_baseline(resource_id)
            return await self._predict_from_baseline(baseline, target_pod_count)

        # Find similar scaling events (similar pod count changes)
        current_baseline = await self.get_load_baseline(resource_id)
        current_pods = current_baseline.pod_count
        pod_change = target_pod_count - current_pods

        relevant_events = [
            event
            for event in scaling_events
            if abs((event.pod_count_after - event.pod_count_before) - pod_change) <= 2
        ]

        if not relevant_events:
            # Use all events if no similar ones found
            relevant_events = scaling_events

        # Analyze historical impacts
        impacts = []
        for event in relevant_events[:5]:  # Limit to last 5 relevant events
            impact = await self.analyze_load_impact(resource_id, event)
            impacts.append(impact)

        # Calculate average impact
        avg_cpu_change = sum(i.cpu_change_pct for i in impacts) / len(impacts)
        avg_memory_change = sum(i.memory_change_pct for i in impacts) / len(impacts)
        avg_request_change = sum(i.request_rate_change_pct for i in impacts) / len(impacts)
        avg_latency_change = sum(i.latency_change_pct for i in impacts) / len(impacts)
        avg_error_change = sum(i.error_rate_change_pct for i in impacts) / len(impacts)

        # Apply average changes to current baseline
        predicted_cpu = current_baseline.avg_cpu_usage * (1 + avg_cpu_change / 100)
        predicted_memory = current_baseline.avg_memory_usage * (1 + avg_memory_change / 100)
        predicted_request_rate = current_baseline.avg_request_rate * (
            1 + avg_request_change / 100
        )
        predicted_latency = current_baseline.avg_latency_p95 * (1 + avg_latency_change / 100)
        predicted_error_rate = current_baseline.avg_error_rate * (1 + avg_error_change / 100)

        # Calculate confidence based on number of similar events
        confidence = min(1.0, len(relevant_events) / 5.0)  # Higher with more data points

        # Generate recommendations
        recommendations = self._generate_prediction_recommendations(
            current_pods,
            target_pod_count,
            predicted_cpu,
            predicted_latency,
            predicted_error_rate,
        )

        return LoadPrediction(
            resource_id=resource_id,
            predicted_pod_count=target_pod_count,
            predicted_cpu_usage=predicted_cpu,
            predicted_memory_usage=predicted_memory,
            predicted_request_rate=predicted_request_rate,
            predicted_latency_p95=predicted_latency,
            predicted_error_rate=predicted_error_rate,
            confidence=confidence,
            based_on_events=relevant_events,
            recommendations=recommendations,
        )

    async def detect_high_load_patterns(
        self, resource_id: str, lookback_hours: int = 24
    ) -> dict[str, Any]:
        """
        Detect patterns of high load over time.

        Args:
            resource_id: Resource to analyze
            lookback_hours: Time window to analyze

        Returns:
            Dictionary with load patterns and insights
        """
        logger.info("detect_high_load_patterns", resource_id=resource_id)

        scaling_events = await self.detect_scaling_events(resource_id, lookback_hours)

        # Get current baseline
        current_baseline = await self.get_load_baseline(resource_id)

        # Check for sustained high load
        is_high_cpu = current_baseline.avg_cpu_usage > 0.8
        is_high_memory = current_baseline.avg_memory_usage > (1024 * 1024 * 1024 * 0.8)  # >80%
        is_high_latency = current_baseline.avg_latency_p95 > 1.0  # >1 second
        is_high_errors = current_baseline.avg_error_rate > 0.05  # >5%

        patterns = {
            "resource_id": resource_id,
            "current_baseline": current_baseline,
            "scaling_events_count": len(scaling_events),
            "recent_scaling_events": scaling_events[:5],  # Last 5 events
            "high_load_indicators": {
                "high_cpu": is_high_cpu,
                "high_memory": is_high_memory,
                "high_latency": is_high_latency,
                "high_errors": is_high_errors,
            },
            "needs_scaling": is_high_cpu or is_high_memory or is_high_latency or is_high_errors,
            "insights": [],
        }

        # Generate insights
        if is_high_cpu:
            patterns["insights"].append(
                f"CPU usage is high ({current_baseline.avg_cpu_usage*100:.1f}%). "
                "Consider scaling up or optimizing CPU-intensive operations."
            )

        if is_high_latency:
            patterns["insights"].append(
                f"Latency is high (P95: {current_baseline.avg_latency_p95*1000:.0f}ms). "
                "This may indicate capacity issues or inefficient queries."
            )

        if is_high_errors:
            patterns["insights"].append(
                f"Error rate is high ({current_baseline.avg_error_rate*100:.1f}%). "
                "This may indicate system instability or capacity limits."
            )

        if len(scaling_events) > 0:
            patterns["insights"].append(
                f"Detected {len(scaling_events)} scaling events in the last {lookback_hours} hours. "
                "Service has been experiencing load changes."
            )

        return patterns

    # Helper methods

    def _extract_avg_value(
        self, results: list[dict[str, Any]], default: float = 0.0
    ) -> float:
        """Extract average value from Prometheus query results."""
        if not results:
            return default

        all_values = []
        for result in results:
            values = result.get("values", [])
            for _, value in values:
                try:
                    all_values.append(float(value))
                except (ValueError, TypeError):
                    continue

        if not all_values:
            return default

        return sum(all_values) / len(all_values)

    def _calculate_pct_change(self, before: float, after: float) -> float:
        """Calculate percentage change."""
        if before == 0:
            return 0.0 if after == 0 else 100.0

        return ((after - before) / before) * 100

    def _determine_impact_level(
        self,
        cpu_change: float,
        memory_change: float,
        latency_change: float,
        error_change: float,
    ) -> str:
        """Determine overall impact level from metric changes."""
        # Consider absolute values of changes
        max_change = max(abs(cpu_change), abs(memory_change), abs(latency_change), abs(error_change))

        if max_change > 50 or abs(error_change) > 20:
            return "critical"
        elif max_change > 25:
            return "significant"
        elif max_change > 10:
            return "moderate"
        else:
            return "minimal"

    async def _estimate_stabilization_time(
        self, resource_id: str, scaling_event: ScalingEvent
    ) -> float | None:
        """Estimate time for metrics to stabilize after scaling."""
        # Look at metrics in windows after the event
        windows = [5, 10, 15, 20, 30]  # minutes

        baseline_before = await self.get_load_baseline(
            resource_id, at_time=scaling_event.timestamp - timedelta(minutes=5)
        )

        for window_minutes in windows:
            check_time = scaling_event.timestamp + timedelta(minutes=window_minutes)
            current = await self.get_load_baseline(resource_id, at_time=check_time)

            # Check if metrics have stabilized (low variance)
            cpu_diff = abs(current.avg_cpu_usage - baseline_before.avg_cpu_usage)
            latency_diff = abs(current.avg_latency_p95 - baseline_before.avg_latency_p95)

            # If both are relatively stable, consider it stabilized
            if cpu_diff < 0.05 and latency_diff < 0.1:
                return float(window_minutes)

        return None  # Not stabilized within 30 minutes

    def _generate_load_recommendations(
        self,
        event: ScalingEvent,
        cpu_change: float,
        memory_change: float,
        latency_change: float,
        error_change: float,
        impact_level: str,
    ) -> list[str]:
        """Generate recommendations based on load impact."""
        recommendations = []

        if impact_level == "critical":
            recommendations.append(
                "⚠️ CRITICAL: Load impact is severe. Consider immediate rollback or further scaling."
            )

        if event.scaling_type == "scale_up":
            if cpu_change < -20:
                recommendations.append(
                    "✅ CPU usage decreased significantly after scaling up. Good result."
                )
            elif cpu_change > 10:
                recommendations.append(
                    "⚠️ CPU usage increased after scaling up. Investigate resource contention."
                )

            if latency_change < -20:
                recommendations.append("✅ Latency improved after scaling up. Good result.")
            elif latency_change > 20:
                recommendations.append(
                    "⚠️ Latency increased after scaling up. May indicate database bottleneck or "
                    "external dependency issues."
                )

        if error_change > 10:
            recommendations.append(
                f"⚠️ Error rate increased by {error_change:.1f}%. "
                "Investigate logs for connection errors or resource exhaustion."
            )

        if not recommendations:
            recommendations.append("✅ Load impact is within acceptable ranges. Continue monitoring.")

        return recommendations

    def _generate_prediction_recommendations(
        self,
        current_pods: int,
        target_pods: int,
        predicted_cpu: float,
        predicted_latency: float,
        predicted_error_rate: float,
    ) -> list[str]:
        """Generate recommendations for predicted load."""
        recommendations = []

        scaling_factor = target_pods / current_pods if current_pods > 0 else 1

        if scaling_factor > 2:
            recommendations.append(
                f"⚠️ Large scaling change ({current_pods} → {target_pods} pods). "
                "Consider scaling gradually to monitor impact."
            )

        if predicted_cpu > 0.8:
            recommendations.append(
                f"⚠️ Predicted CPU usage is high ({predicted_cpu*100:.1f}%). "
                "Consider scaling to more pods or optimizing application."
            )

        if predicted_latency > 1.0:
            recommendations.append(
                f"⚠️ Predicted latency is high ({predicted_latency*1000:.0f}ms). "
                "May need additional capacity or optimization."
            )

        if predicted_error_rate > 0.05:
            recommendations.append(
                f"⚠️ Predicted error rate is high ({predicted_error_rate*100:.1f}%). "
                "System may be near capacity limits."
            )

        if (
            predicted_cpu < 0.7
            and predicted_latency < 0.5
            and predicted_error_rate < 0.01
        ):
            recommendations.append(
                "✅ Predicted metrics look healthy. This scaling change should be safe."
            )

        return recommendations

    async def _predict_from_baseline(
        self, baseline: LoadBaseline, target_pod_count: int
    ) -> LoadPrediction:
        """Predict metrics from baseline when no historical data available."""
        # Use simple linear scaling assumption
        scaling_factor = target_pod_count / baseline.pod_count if baseline.pod_count > 0 else 1

        # Assume inverse relationship (more pods = lower per-pod metrics)
        predicted_cpu = baseline.avg_cpu_usage / scaling_factor
        predicted_memory = baseline.avg_memory_usage / scaling_factor
        predicted_request_rate = baseline.avg_request_rate * scaling_factor
        predicted_latency = baseline.avg_latency_p95 / scaling_factor
        predicted_error_rate = baseline.avg_error_rate / scaling_factor

        recommendations = [
            "⚠️ No historical scaling data available. Predictions are based on linear scaling "
            "assumptions and may not be accurate. Proceed with caution and monitor closely."
        ]

        return LoadPrediction(
            resource_id=baseline.resource_id,
            predicted_pod_count=target_pod_count,
            predicted_cpu_usage=predicted_cpu,
            predicted_memory_usage=predicted_memory,
            predicted_request_rate=predicted_request_rate,
            predicted_latency_p95=predicted_latency,
            predicted_error_rate=predicted_error_rate,
            confidence=0.3,  # Low confidence without historical data
            based_on_events=[],
            recommendations=recommendations,
        )
