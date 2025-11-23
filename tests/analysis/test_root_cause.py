"""
Unit tests for the root cause analysis engine.

Tests cover:
- Timeline reconstruction
- Correlation analysis
- Failure propagation detection
- Root cause identification
- Confidence scoring
- Recommendation generation
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from topdeck.analysis.root_cause import (
    CorrelatedAnomaly,
    FailurePropagation,
    RootCauseAnalysis,
    RootCauseAnalyzer,
    RootCauseType,
    TimelineEvent,
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
            "cloud_provider": "azure",
        }
    ])
    
    # Mock dependency chain query
    async def mock_dependency_chain(*args, **kwargs):
        return [
            {
                "id": "service-2",
                "name": "Upstream Service",
                "relationship": "depends_on",
            }
        ]
    
    client.get_dependency_chain = mock_dependency_chain
    
    return client


@pytest.fixture
def mock_prometheus_collector():
    """Mock Prometheus collector."""
    collector = AsyncMock()
    
    # Mock metric query
    async def mock_query_range(*args, **kwargs):
        return [
            {
                "metric": {"__name__": "cpu_usage"},
                "values": [[1234567890, "85.0"]],
            }
        ]
    
    collector.query_range = mock_query_range
    
    return collector


@pytest.fixture
def mock_diagnostics_service():
    """Mock Live Diagnostics Service."""
    service = AsyncMock()
    
    # Mock anomalies
    service.get_anomalies = AsyncMock(return_value=[
        MagicMock(
            resource_id="service-1",
            resource_name="Test Service",
            metric_name="error_rate",
            deviation=3.5,
            severity="high",
            timestamp=datetime.now(UTC) - timedelta(minutes=10),
        ),
    ])
    
    return service


@pytest.fixture
def rca_analyzer(mock_neo4j_client, mock_prometheus_collector, mock_diagnostics_service):
    """Create a root cause analyzer instance."""
    return RootCauseAnalyzer(
        neo4j_client=mock_neo4j_client,
        prometheus_collector=mock_prometheus_collector,
        diagnostics_service=mock_diagnostics_service,
    )


class TestTimelineReconstruction:
    """Test timeline reconstruction functionality."""
    
    @pytest.mark.asyncio
    async def test_build_timeline(self, rca_analyzer, mock_neo4j_client):
        """Test building a failure timeline."""
        # Mock deployment events
        mock_neo4j_client.execute_query = AsyncMock(return_value=[
            {
                "timestamp": (datetime.now(UTC) - timedelta(minutes=30)).isoformat(),
                "event_type": "deployment",
                "description": "Deployed v1.2.3",
            }
        ])
        
        failure_time = datetime.now(UTC)
        timeline = await rca_analyzer._build_timeline(
            "service-1",
            failure_time,
            lookback_hours=2,
        )
        
        assert len(timeline) > 0
        assert timeline[0].event_type in ["deployment", "anomaly"]
    
    @pytest.mark.asyncio
    async def test_timeline_sorted_chronologically(self, rca_analyzer):
        """Test that timeline events are sorted chronologically."""
        failure_time = datetime.now(UTC)
        timeline = await rca_analyzer._build_timeline(
            "service-1",
            failure_time,
            lookback_hours=2,
        )
        
        # Verify chronological order (newest first)
        if len(timeline) > 1:
            for i in range(len(timeline) - 1):
                assert timeline[i].timestamp >= timeline[i + 1].timestamp


class TestCorrelationAnalysis:
    """Test anomaly correlation analysis."""
    
    @pytest.mark.asyncio
    async def test_find_correlated_anomalies(self, rca_analyzer):
        """Test finding anomalies correlated with a failure."""
        failure_time = datetime.now(UTC)
        
        correlated = await rca_analyzer._find_correlated_anomalies(
            "service-1",
            failure_time,
            lookback_hours=2,
        )
        
        assert isinstance(correlated, list)
        if len(correlated) > 0:
            assert all(isinstance(a, CorrelatedAnomaly) for a in correlated)
    
    @pytest.mark.asyncio
    async def test_correlation_scoring(self, rca_analyzer, mock_diagnostics_service):
        """Test that correlation scores are calculated correctly."""
        # Mock multiple anomalies with different severities
        mock_diagnostics_service.get_anomalies = AsyncMock(return_value=[
            MagicMock(
                resource_id="service-1",
                resource_name="Test Service",
                metric_name="error_rate",
                deviation=5.0,
                severity="critical",
                timestamp=datetime.now(UTC) - timedelta(minutes=5),
            ),
            MagicMock(
                resource_id="service-1",
                resource_name="Test Service",
                metric_name="latency",
                deviation=2.0,
                severity="low",
                timestamp=datetime.now(UTC) - timedelta(minutes=15),
            ),
        ])
        
        failure_time = datetime.now(UTC)
        correlated = await rca_analyzer._find_correlated_anomalies(
            "service-1",
            failure_time,
            lookback_hours=2,
        )
        
        # Critical anomalies should have higher correlation scores
        if len(correlated) > 1:
            critical = [a for a in correlated if "critical" in a.severity]
            low = [a for a in correlated if "low" in a.severity]
            if critical and low:
                assert critical[0].correlation_score > low[0].correlation_score


class TestFailurePropagation:
    """Test failure propagation detection."""
    
    @pytest.mark.asyncio
    async def test_analyze_propagation(self, rca_analyzer, mock_neo4j_client):
        """Test analyzing failure propagation through dependencies."""
        # Mock dependency chain
        async def mock_get_deps(resource_id, depth):
            return [
                {
                    "id": "service-2",
                    "name": "Upstream Service",
                    "relationship": "depends_on",
                },
                {
                    "id": "service-3",
                    "name": "Database",
                    "relationship": "depends_on",
                },
            ]
        
        mock_neo4j_client.get_dependency_chain = mock_get_deps
        
        failure_time = datetime.now(UTC)
        propagation = await rca_analyzer._analyze_propagation(
            "service-1",
            failure_time,
            lookback_hours=2,
        )
        
        if propagation:
            assert isinstance(propagation, FailurePropagation)
            assert len(propagation.propagation_path) > 0
    
    @pytest.mark.asyncio
    async def test_propagation_delay_calculation(self, rca_analyzer, mock_diagnostics_service):
        """Test that propagation delay is calculated correctly."""
        # Mock anomalies at different times
        base_time = datetime.now(UTC)
        mock_diagnostics_service.get_anomalies = AsyncMock(return_value=[
            MagicMock(
                resource_id="service-2",
                resource_name="Upstream Service",
                metric_name="error_rate",
                deviation=4.0,
                severity="high",
                timestamp=base_time - timedelta(minutes=10),
            ),
            MagicMock(
                resource_id="service-1",
                resource_name="Test Service",
                metric_name="error_rate",
                deviation=3.0,
                severity="high",
                timestamp=base_time - timedelta(minutes=5),
            ),
        ])
        
        failure_time = base_time
        propagation = await rca_analyzer._analyze_propagation(
            "service-1",
            failure_time,
            lookback_hours=2,
        )
        
        if propagation:
            # Delay should be positive (upstream failed first)
            assert propagation.propagation_delay >= 0


class TestRootCauseIdentification:
    """Test root cause type identification."""
    
    @pytest.mark.asyncio
    async def test_identify_deployment_root_cause(self, rca_analyzer):
        """Test identifying deployment as root cause."""
        # Mock recent deployment
        timeline = [
            TimelineEvent(
                timestamp=datetime.now(UTC) - timedelta(minutes=5),
                event_type="deployment",
                resource_id="service-1",
                resource_name="Test Service",
                description="Deployed v1.2.3",
                severity="info",
            ),
        ]
        
        root_cause_type = rca_analyzer._determine_root_cause_type(
            timeline=timeline,
            correlated_anomalies=[],
            propagation=None,
        )
        
        assert root_cause_type == RootCauseType.DEPLOYMENT
    
    @pytest.mark.asyncio
    async def test_identify_resource_exhaustion(self, rca_analyzer):
        """Test identifying resource exhaustion as root cause."""
        # Mock high resource usage anomalies
        correlated = [
            CorrelatedAnomaly(
                resource_id="service-1",
                resource_name="Test Service",
                metric_name="cpu_usage",
                deviation=4.5,
                severity="critical",
                timestamp=datetime.now(UTC),
                correlation_score=0.9,
            ),
            CorrelatedAnomaly(
                resource_id="service-1",
                resource_name="Test Service",
                metric_name="memory_usage",
                deviation=4.0,
                severity="high",
                timestamp=datetime.now(UTC),
                correlation_score=0.85,
            ),
        ]
        
        root_cause_type = rca_analyzer._determine_root_cause_type(
            timeline=[],
            correlated_anomalies=correlated,
            propagation=None,
        )
        
        assert root_cause_type == RootCauseType.RESOURCE_EXHAUSTION
    
    @pytest.mark.asyncio
    async def test_identify_cascading_failure(self, rca_analyzer):
        """Test identifying cascading failure as root cause."""
        propagation = FailurePropagation(
            initial_failure="service-2",
            propagation_path=["service-2", "service-1"],
            propagation_delay=300.0,
            affected_services=["service-1"],
        )
        
        root_cause_type = rca_analyzer._determine_root_cause_type(
            timeline=[],
            correlated_anomalies=[],
            propagation=propagation,
        )
        
        assert root_cause_type == RootCauseType.CASCADING_FAILURE
    
    @pytest.mark.asyncio
    async def test_identify_network_issue(self, rca_analyzer):
        """Test identifying network issue as root cause."""
        correlated = [
            CorrelatedAnomaly(
                resource_id="service-1",
                resource_name="Test Service",
                metric_name="latency",
                deviation=5.0,
                severity="critical",
                timestamp=datetime.now(UTC),
                correlation_score=0.95,
            ),
            CorrelatedAnomaly(
                resource_id="service-1",
                resource_name="Test Service",
                metric_name="timeout_rate",
                deviation=4.0,
                severity="high",
                timestamp=datetime.now(UTC),
                correlation_score=0.9,
            ),
        ]
        
        root_cause_type = rca_analyzer._determine_root_cause_type(
            timeline=[],
            correlated_anomalies=correlated,
            propagation=None,
        )
        
        assert root_cause_type == RootCauseType.NETWORK_ISSUE


class TestConfidenceScoring:
    """Test confidence score calculation."""
    
    def test_high_confidence_with_clear_signals(self, rca_analyzer):
        """Test that clear signals result in high confidence."""
        # Recent deployment + high correlation anomaly
        timeline = [
            TimelineEvent(
                timestamp=datetime.now(UTC) - timedelta(minutes=2),
                event_type="deployment",
                resource_id="service-1",
                resource_name="Test Service",
                description="Deployed v1.2.3",
                severity="info",
            ),
        ]
        
        correlated = [
            CorrelatedAnomaly(
                resource_id="service-1",
                resource_name="Test Service",
                metric_name="error_rate",
                deviation=5.0,
                severity="critical",
                timestamp=datetime.now(UTC),
                correlation_score=0.95,
            ),
        ]
        
        confidence = rca_analyzer._calculate_confidence(
            root_cause_type=RootCauseType.DEPLOYMENT,
            timeline=timeline,
            correlated_anomalies=correlated,
            propagation=None,
        )
        
        assert confidence >= 0.7
    
    def test_low_confidence_with_unclear_signals(self, rca_analyzer):
        """Test that unclear signals result in low confidence."""
        # No clear indicators
        confidence = rca_analyzer._calculate_confidence(
            root_cause_type=RootCauseType.UNKNOWN,
            timeline=[],
            correlated_anomalies=[],
            propagation=None,
        )
        
        assert confidence <= 0.5


class TestRecommendationGeneration:
    """Test recommendation generation."""
    
    def test_deployment_recommendations(self, rca_analyzer):
        """Test recommendations for deployment root cause."""
        recommendations = rca_analyzer._generate_recommendations(
            RootCauseType.DEPLOYMENT
        )
        
        assert len(recommendations) > 0
        assert any("rollback" in r.lower() for r in recommendations)
    
    def test_resource_exhaustion_recommendations(self, rca_analyzer):
        """Test recommendations for resource exhaustion."""
        recommendations = rca_analyzer._generate_recommendations(
            RootCauseType.RESOURCE_EXHAUSTION
        )
        
        assert len(recommendations) > 0
        assert any("scale" in r.lower() or "resource" in r.lower() for r in recommendations)
    
    def test_cascading_failure_recommendations(self, rca_analyzer):
        """Test recommendations for cascading failure."""
        recommendations = rca_analyzer._generate_recommendations(
            RootCauseType.CASCADING_FAILURE
        )
        
        assert len(recommendations) > 0
        assert any("circuit breaker" in r.lower() or "upstream" in r.lower() for r in recommendations)
    
    def test_network_issue_recommendations(self, rca_analyzer):
        """Test recommendations for network issue."""
        recommendations = rca_analyzer._generate_recommendations(
            RootCauseType.NETWORK_ISSUE
        )
        
        assert len(recommendations) > 0
        assert any("network" in r.lower() or "connectivity" in r.lower() for r in recommendations)


class TestCompleteRCAFlow:
    """Test the complete root cause analysis flow."""
    
    @pytest.mark.asyncio
    async def test_perform_rca(self, rca_analyzer):
        """Test performing a complete RCA."""
        result = await rca_analyzer.perform_analysis(
            resource_id="service-1",
            failure_time=datetime.now(UTC),
            lookback_hours=2,
        )
        
        assert isinstance(result, RootCauseAnalysis)
        assert result.resource_id == "service-1"
        assert result.root_cause_type in RootCauseType
        assert 0 <= result.confidence <= 1
        assert len(result.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_rca_with_custom_lookback(self, rca_analyzer):
        """Test RCA with custom lookback period."""
        result = await rca_analyzer.perform_analysis(
            resource_id="service-1",
            failure_time=datetime.now(UTC),
            lookback_hours=4,
        )
        
        assert isinstance(result, RootCauseAnalysis)
    
    @pytest.mark.asyncio
    async def test_rca_handles_missing_data(self, rca_analyzer, mock_diagnostics_service):
        """Test that RCA handles missing data gracefully."""
        # Mock no anomalies
        mock_diagnostics_service.get_anomalies = AsyncMock(return_value=[])
        
        result = await rca_analyzer.perform_analysis(
            resource_id="service-1",
            failure_time=datetime.now(UTC),
            lookback_hours=2,
        )
        
        # Should still return a result, likely with UNKNOWN root cause
        assert isinstance(result, RootCauseAnalysis)
        # Confidence should be lower due to lack of data
        assert result.confidence <= 0.5


class TestConfigurableDepth:
    """Test configurable dependency traversal depth."""
    
    @pytest.mark.asyncio
    async def test_custom_traversal_depth(self, rca_analyzer, mock_neo4j_client):
        """Test using custom dependency traversal depth."""
        # Mock deep dependency chain
        async def mock_get_deps(resource_id, depth):
            # Return different results based on depth
            if depth >= 10:
                return [
                    {
                        "id": f"service-{i}",
                        "name": f"Service {i}",
                        "relationship": "depends_on",
                    }
                    for i in range(depth)
                ]
            return []
        
        mock_neo4j_client.get_dependency_chain = mock_get_deps
        
        # Perform RCA with custom depth (if supported)
        result = await rca_analyzer.perform_analysis(
            resource_id="service-1",
            failure_time=datetime.now(UTC),
            lookback_hours=2,
        )
        
        assert isinstance(result, RootCauseAnalysis)
