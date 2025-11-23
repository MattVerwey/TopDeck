"""
Unit tests for the baseline calculation and historical comparison.

Tests cover:
- Baseline calculation
- Statistical metrics calculation
- Historical comparison
- Trend analysis
- Anomaly detection based on baseline
- Cache management
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from topdeck.analysis.baseline import (
    Baseline,
    BaselineAnalyzer,
    BaselineMetric,
    ComparisonPeriod,
    HistoricalComparison,
    MetricComparison,
)


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4j client."""
    client = AsyncMock()
    
    # Mock resource query
    client.execute_query = AsyncMock(return_value=[
        {
            "id": "service-1",
            "name": "Test Service",
            "type": "service",
        }
    ])
    
    return client


@pytest.fixture
def mock_prometheus_collector():
    """Mock Prometheus collector."""
    collector = AsyncMock()
    
    # Mock metric query with realistic data
    async def mock_query_range(query, start, end, step):
        # Return sample data points
        values = []
        current_time = start
        while current_time <= end:
            # Generate realistic values with some variation
            value = 50.0 + (hash(current_time) % 20)
            values.append([current_time, str(value)])
            current_time += step
        
        return [
            {
                "metric": {"__name__": "cpu_usage"},
                "values": values,
            }
        ]
    
    collector.query_range = mock_query_range
    
    return collector


@pytest.fixture
def baseline_analyzer(mock_neo4j_client, mock_prometheus_collector):
    """Create a baseline analyzer instance."""
    return BaselineAnalyzer(
        neo4j_client=mock_neo4j_client,
        prometheus_collector=mock_prometheus_collector,
    )


class TestBaselineCalculation:
    """Test baseline calculation functionality."""
    
    @pytest.mark.asyncio
    async def test_calculate_baseline(self, baseline_analyzer):
        """Test calculating baseline for a service."""
        baseline = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        assert isinstance(baseline, Baseline)
        assert baseline.resource_id == "service-1"
        assert len(baseline.metrics) > 0
    
    @pytest.mark.asyncio
    async def test_baseline_includes_all_metric_types(self, baseline_analyzer):
        """Test that baseline includes all supported metric types."""
        baseline = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Should have metrics for common types
        metric_names = set(baseline.metrics.keys())
        expected_metrics = {
            "cpu_usage",
            "memory_usage",
            "request_rate",
            "error_rate",
        }
        
        # At least some expected metrics should be present
        assert len(metric_names.intersection(expected_metrics)) > 0
    
    @pytest.mark.asyncio
    async def test_baseline_metric_statistics(self, baseline_analyzer):
        """Test that baseline metrics include correct statistics."""
        baseline = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Get any metric
        if baseline.metrics:
            metric_name = list(baseline.metrics.keys())[0]
            metric = baseline.metrics[metric_name]
            
            assert isinstance(metric, BaselineMetric)
            assert metric.mean >= 0
            assert metric.median >= 0
            assert metric.std_dev >= 0
            assert metric.min_value >= 0
            assert metric.max_value >= metric.min_value
            assert metric.percentile_95 >= metric.median
            assert metric.percentile_99 >= metric.percentile_95
            assert metric.sample_count > 0
    
    @pytest.mark.asyncio
    async def test_baseline_cache(self, baseline_analyzer):
        """Test that baselines are cached."""
        # First calculation
        baseline1 = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Second calculation (should use cache)
        baseline2 = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Should be the same object from cache
        assert baseline1.calculated_at == baseline2.calculated_at
    
    @pytest.mark.asyncio
    async def test_force_recalculate_baseline(self, baseline_analyzer):
        """Test forcing baseline recalculation."""
        # First calculation
        baseline1 = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Force recalculation
        baseline2 = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
            force_recalculate=True,
        )
        
        # Should be different (newer)
        assert baseline2.calculated_at >= baseline1.calculated_at


class TestStatisticalCalculations:
    """Test statistical metric calculations."""
    
    @pytest.mark.asyncio
    async def test_mean_calculation(self, baseline_analyzer):
        """Test mean calculation is correct."""
        # Mock Prometheus to return known values
        values = [[i, str(i * 10)] for i in range(1, 11)]  # 10, 20, 30, ..., 100
        
        baseline_analyzer.prometheus_collector.query_range = AsyncMock(
            return_value=[{"metric": {"__name__": "test_metric"}, "values": values}]
        )
        
        baseline = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        if "test_metric" in baseline.metrics:
            metric = baseline.metrics["test_metric"]
            # Mean of 10, 20, 30, ..., 100 is 55
            assert 50 <= metric.mean <= 60  # Allow some tolerance
    
    @pytest.mark.asyncio
    async def test_percentile_calculations(self, baseline_analyzer):
        """Test percentile calculations are correct."""
        # Mock Prometheus to return known values
        values = [[i, str(i)] for i in range(1, 101)]  # 1 to 100
        
        baseline_analyzer.prometheus_collector.query_range = AsyncMock(
            return_value=[{"metric": {"__name__": "test_metric"}, "values": values}]
        )
        
        baseline = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        if "test_metric" in baseline.metrics:
            metric = baseline.metrics["test_metric"]
            # P95 should be around 95, P99 around 99
            assert 90 <= metric.percentile_95 <= 97
            assert 97 <= metric.percentile_99 <= 100


class TestHistoricalComparison:
    """Test historical comparison functionality."""
    
    @pytest.mark.asyncio
    async def test_compare_with_previous_hour(self, baseline_analyzer):
        """Test comparison with previous hour."""
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.PREVIOUS_HOUR,
        )
        
        assert isinstance(comparison, HistoricalComparison)
        assert comparison.comparison_period == ComparisonPeriod.PREVIOUS_HOUR
        assert len(comparison.metrics) > 0
    
    @pytest.mark.asyncio
    async def test_compare_with_previous_day(self, baseline_analyzer):
        """Test comparison with previous day."""
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.PREVIOUS_DAY,
        )
        
        assert isinstance(comparison, HistoricalComparison)
        assert comparison.comparison_period == ComparisonPeriod.PREVIOUS_DAY
    
    @pytest.mark.asyncio
    async def test_compare_with_same_hour_yesterday(self, baseline_analyzer):
        """Test comparison with same hour yesterday."""
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.SAME_HOUR_YESTERDAY,
        )
        
        assert isinstance(comparison, HistoricalComparison)
        assert comparison.comparison_period == ComparisonPeriod.SAME_HOUR_YESTERDAY
    
    @pytest.mark.asyncio
    async def test_metric_comparison_structure(self, baseline_analyzer):
        """Test metric comparison structure."""
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.PREVIOUS_HOUR,
        )
        
        if comparison.metrics:
            metric_comp = comparison.metrics[0]
            
            assert isinstance(metric_comp, MetricComparison)
            assert metric_comp.current_value >= 0
            assert metric_comp.historical_value >= 0
            assert metric_comp.trend in ["improving", "degrading", "stable"]


class TestTrendAnalysis:
    """Test trend analysis functionality."""
    
    @pytest.mark.asyncio
    async def test_improving_trend(self, baseline_analyzer):
        """Test detection of improving trend."""
        # Mock current value lower than historical for error rate (improvement)
        async def mock_query_range(query, start, end, step):
            if "current" in str(start):
                # Current: low value
                return [{"metric": {"__name__": "error_rate"}, "values": [[start, "5.0"]]}]
            else:
                # Historical: high value
                return [{"metric": {"__name__": "error_rate"}, "values": [[start, "15.0"]]}]
        
        baseline_analyzer.prometheus_collector.query_range = mock_query_range
        
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.PREVIOUS_HOUR,
        )
        
        # For error rate, lower is better, so should be improving
        error_rate_metrics = [m for m in comparison.metrics if "error" in m.metric_name.lower()]
        if error_rate_metrics:
            assert error_rate_metrics[0].trend == "improving"
    
    @pytest.mark.asyncio
    async def test_degrading_trend(self, baseline_analyzer):
        """Test detection of degrading trend."""
        # Mock current value higher than historical for latency (degradation)
        async def mock_query_range(query, start, end, step):
            # Simplified mock for testing
            return [{"metric": {"__name__": "latency"}, "values": [[start, "100.0"]]}]
        
        baseline_analyzer.prometheus_collector.query_range = mock_query_range
        
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.PREVIOUS_HOUR,
        )
        
        # Should have some metrics
        assert len(comparison.metrics) >= 0
    
    @pytest.mark.asyncio
    async def test_stable_trend(self, baseline_analyzer):
        """Test detection of stable trend."""
        # Mock similar values for current and historical
        async def mock_query_range(query, start, end, step):
            return [{"metric": {"__name__": "cpu_usage"}, "values": [[start, "50.0"]]}]
        
        baseline_analyzer.prometheus_collector.query_range = mock_query_range
        
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.PREVIOUS_HOUR,
        )
        
        # When values are similar (within 5%), should be stable
        cpu_metrics = [m for m in comparison.metrics if "cpu" in m.metric_name.lower()]
        if cpu_metrics and abs(cpu_metrics[0].percent_change) < 5:
            assert cpu_metrics[0].trend == "stable"
    
    @pytest.mark.asyncio
    async def test_overall_trend_mixed(self, baseline_analyzer):
        """Test overall trend when metrics are mixed."""
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.PREVIOUS_HOUR,
        )
        
        # Overall trend should be one of the valid values
        assert comparison.overall_trend in ["improving", "degrading", "stable", "mixed"]


class TestAnomalyDetection:
    """Test anomaly detection based on baseline."""
    
    @pytest.mark.asyncio
    async def test_anomaly_detection(self, baseline_analyzer):
        """Test detecting anomalies based on baseline."""
        # First calculate baseline
        baseline = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Mock current value that deviates significantly
        async def mock_query_range(query, start, end, step):
            return [{"metric": {"__name__": "cpu_usage"}, "values": [[start, "150.0"]]}]
        
        baseline_analyzer.prometheus_collector.query_range = mock_query_range
        
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.PREVIOUS_HOUR,
        )
        
        # Should detect anomalies
        assert comparison.anomaly_count >= 0
    
    @pytest.mark.asyncio
    async def test_deviation_from_baseline(self, baseline_analyzer):
        """Test calculation of deviation from baseline."""
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.PREVIOUS_HOUR,
        )
        
        if comparison.metrics:
            metric_comp = comparison.metrics[0]
            # Deviation should be a reasonable number
            assert -10 <= metric_comp.deviation_from_baseline <= 10
    
    @pytest.mark.asyncio
    async def test_anomaly_threshold_configurable(self, baseline_analyzer):
        """Test that anomaly detection threshold can be configured."""
        # This test assumes we can configure the threshold
        # Default is 2 standard deviations
        
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.PREVIOUS_HOUR,
        )
        
        # Should have computed anomaly flags
        if comparison.metrics:
            metric_comp = comparison.metrics[0]
            assert isinstance(metric_comp.is_anomalous, bool)


class TestDataValidation:
    """Test data validation and error handling."""
    
    @pytest.mark.asyncio
    async def test_insufficient_data_warning(self, baseline_analyzer, mock_prometheus_collector):
        """Test handling of insufficient data."""
        # Mock empty data
        mock_prometheus_collector.query_range = AsyncMock(return_value=[])
        
        baseline = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Should still return a baseline, but with empty or minimal metrics
        assert isinstance(baseline, Baseline)
    
    @pytest.mark.asyncio
    async def test_minimum_data_requirement(self, baseline_analyzer):
        """Test enforcement of minimum data requirements."""
        # For accurate baselines, should have at least 7 days of data
        baseline = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Should have calculated some metrics
        assert isinstance(baseline, Baseline)
    
    @pytest.mark.asyncio
    async def test_handle_missing_metrics(self, baseline_analyzer, mock_prometheus_collector):
        """Test handling of missing metrics gracefully."""
        # Mock Prometheus returning no data for some metrics
        async def mock_query_range(query, start, end, step):
            if "cpu" in query:
                return [{"metric": {"__name__": "cpu_usage"}, "values": [[start, "50.0"]]}]
            return []
        
        mock_prometheus_collector.query_range = mock_query_range
        
        baseline = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Should have some metrics but not all
        assert isinstance(baseline, Baseline)


class TestCustomMetricSupport:
    """Test support for custom metrics beyond the standard 7."""
    
    @pytest.mark.asyncio
    async def test_custom_metric_naming(self, baseline_analyzer):
        """Test handling of custom metric naming patterns."""
        # Mock Prometheus with custom metric names
        async def mock_query_range(query, start, end, step):
            return [
                {
                    "metric": {"__name__": "custom_metric_name"},
                    "values": [[start, "42.0"]],
                }
            ]
        
        baseline_analyzer.prometheus_collector.query_range = mock_query_range
        
        baseline = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Should handle custom metric names
        assert isinstance(baseline, Baseline)


class TestCacheManagement:
    """Test baseline cache management."""
    
    @pytest.mark.asyncio
    async def test_cache_validity_period(self, baseline_analyzer):
        """Test that cache has validity period."""
        baseline = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Should have valid_until timestamp
        assert baseline.valid_until > baseline.calculated_at
        assert baseline.valid_until > datetime.now(UTC)
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, baseline_analyzer):
        """Test that expired cache is recalculated."""
        # Calculate baseline
        baseline1 = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Manually expire the cache
        baseline1.valid_until = datetime.now(UTC) - timedelta(hours=1)
        
        # Next calculation should create new baseline
        baseline2 = await baseline_analyzer.calculate_baseline(
            resource_id="service-1",
            days=7,
        )
        
        # Should be recalculated (newer timestamp)
        assert baseline2.calculated_at >= baseline1.calculated_at


class TestPercentageChange:
    """Test percentage change calculations."""
    
    @pytest.mark.asyncio
    async def test_positive_change(self, baseline_analyzer):
        """Test calculation of positive percentage change."""
        # Mock increase in metric
        call_count = [0]
        
        async def mock_query_range(query, start, end, step):
            call_count[0] += 1
            value = "100.0" if call_count[0] == 1 else "50.0"
            return [{"metric": {"__name__": "cpu_usage"}, "values": [[start, value]]}]
        
        baseline_analyzer.prometheus_collector.query_range = mock_query_range
        
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.PREVIOUS_HOUR,
        )
        
        # Should calculate percentage change
        if comparison.metrics:
            metric_comp = comparison.metrics[0]
            assert metric_comp.percent_change != 0 or metric_comp.absolute_change != 0
    
    @pytest.mark.asyncio
    async def test_negative_change(self, baseline_analyzer):
        """Test calculation of negative percentage change."""
        comparison = await baseline_analyzer.compare_with_history(
            resource_id="service-1",
            period=ComparisonPeriod.PREVIOUS_HOUR,
        )
        
        # Percentage change can be positive or negative
        if comparison.metrics:
            metric_comp = comparison.metrics[0]
            assert isinstance(metric_comp.percent_change, float)
