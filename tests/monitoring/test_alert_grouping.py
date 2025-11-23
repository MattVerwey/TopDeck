"""
Unit tests for alert grouping and aggregation.

Tests cover:
- Grouping by resource
- Grouping by severity
- Grouping by type
- Grouping by time window
- Grouping by rule
- Alert deduplication
- Digest creation
"""

from datetime import UTC, datetime, timedelta

import pytest

from topdeck.monitoring.alert_grouping import (
    AlertGroup,
    AlertGrouper,
    GroupingStrategy,
)
from topdeck.monitoring.alerting import (
    Alert,
    AlertSeverity,
    AlertStatus,
    TriggerType,
)


@pytest.fixture
def sample_alerts():
    """Create sample alerts for testing."""
    base_time = datetime.now(UTC)
    
    return [
        Alert(
            id="alert-1",
            rule_id="rule-1",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            title="Health Drop Service A",
            message="Service A health dropped",
            resource_id="service-a",
            triggered_at=base_time,
            metadata={"service_name": "Service A"},
        ),
        Alert(
            id="alert-2",
            rule_id="rule-1",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACTIVE,
            title="Health Drop Service A",
            message="Service A health critical",
            resource_id="service-a",
            triggered_at=base_time + timedelta(minutes=5),
            metadata={"service_name": "Service A"},
        ),
        Alert(
            id="alert-3",
            rule_id="rule-2",
            trigger_type=TriggerType.CRITICAL_ANOMALY,
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACKNOWLEDGED,
            title="Anomaly Service B",
            message="Critical anomaly in Service B",
            resource_id="service-b",
            triggered_at=base_time + timedelta(minutes=10),
            metadata={"service_name": "Service B"},
        ),
        Alert(
            id="alert-4",
            rule_id="rule-1",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.WARNING,
            status=AlertStatus.RESOLVED,
            title="Health Drop Service C",
            message="Service C health dropped",
            resource_id="service-c",
            triggered_at=base_time + timedelta(hours=2),
            metadata={"service_name": "Service C"},
        ),
    ]


@pytest.fixture
def grouper():
    """Create an alert grouper instance."""
    return AlertGrouper()


class TestGroupByResource:
    """Test grouping alerts by resource."""
    
    def test_group_by_resource(self, grouper, sample_alerts):
        """Test grouping alerts by resource ID."""
        groups = grouper.group_alerts(sample_alerts, GroupingStrategy.BY_RESOURCE)
        
        assert len(groups) == 3  # service-a, service-b, service-c
        
        # Check service-a group has 2 alerts
        service_a_groups = [g for g in groups if "Service A" in g.name]
        assert len(service_a_groups) == 1
        assert len(service_a_groups[0].alerts) == 2
    
    def test_group_metadata_includes_resource_id(self, grouper, sample_alerts):
        """Test that group metadata includes resource ID."""
        groups = grouper.group_alerts(sample_alerts, GroupingStrategy.BY_RESOURCE)
        
        for group in groups:
            assert "resource_id" in group.metadata
            assert group.metadata["resource_id"] in ["service-a", "service-b", "service-c"]


class TestGroupBySeverity:
    """Test grouping alerts by severity."""
    
    def test_group_by_severity(self, grouper, sample_alerts):
        """Test grouping alerts by severity level."""
        groups = grouper.group_alerts(sample_alerts, GroupingStrategy.BY_SEVERITY)
        
        # Should have WARNING and CRITICAL groups
        assert len(groups) >= 2
        
        # Find critical group
        critical_groups = [g for g in groups if g.highest_severity == AlertSeverity.CRITICAL]
        assert len(critical_groups) == 1
        assert len(critical_groups[0].alerts) == 2  # alerts 2 and 3
    
    def test_severity_groups_sorted(self, grouper, sample_alerts):
        """Test that severity groups are sorted by severity."""
        groups = grouper.group_alerts(sample_alerts, GroupingStrategy.BY_SEVERITY)
        
        # Critical should come before warning
        if len(groups) >= 2:
            severity_order = [g.highest_severity for g in groups]
            assert severity_order[0] == AlertSeverity.CRITICAL or len(groups) == 1


class TestGroupByType:
    """Test grouping alerts by trigger type."""
    
    def test_group_by_type(self, grouper, sample_alerts):
        """Test grouping alerts by trigger type."""
        groups = grouper.group_alerts(sample_alerts, GroupingStrategy.BY_TYPE)
        
        # Should have HEALTH_SCORE_DROP and CRITICAL_ANOMALY groups
        assert len(groups) == 2
        
        # Check health score drop group
        health_groups = [g for g in groups if "Health Score" in g.name]
        assert len(health_groups) == 1
        assert len(health_groups[0].alerts) == 3  # alerts 1, 2, 4
    
    def test_type_group_names_friendly(self, grouper, sample_alerts):
        """Test that type group names are human-friendly."""
        groups = grouper.group_alerts(sample_alerts, GroupingStrategy.BY_TYPE)
        
        for group in groups:
            # Should not contain underscores in name
            assert "_" not in group.name or "Health Score" in group.name


class TestGroupByTimeWindow:
    """Test grouping alerts by time window."""
    
    def test_group_by_time_window(self, grouper, sample_alerts):
        """Test grouping alerts by time window."""
        # Use 30-minute window
        groups = grouper.group_alerts(
            sample_alerts,
            GroupingStrategy.BY_TIME_WINDOW,
            time_window_minutes=30,
        )
        
        # First 3 alerts should be in one group, last alert in another
        assert len(groups) == 2
        assert len(groups[0].alerts) == 3
        assert len(groups[1].alerts) == 1
    
    def test_time_window_metadata(self, grouper, sample_alerts):
        """Test that time window groups include window metadata."""
        groups = grouper.group_alerts(
            sample_alerts,
            GroupingStrategy.BY_TIME_WINDOW,
            time_window_minutes=60,
        )
        
        for group in groups:
            assert "window_start" in group.metadata
            assert "window_end" in group.metadata


class TestGroupByRule:
    """Test grouping alerts by rule."""
    
    def test_group_by_rule(self, grouper, sample_alerts):
        """Test grouping alerts by rule ID."""
        groups = grouper.group_alerts(sample_alerts, GroupingStrategy.BY_RULE)
        
        # Should have rule-1 and rule-2 groups
        assert len(groups) == 2
        
        # Check rule-1 group
        rule1_groups = [g for g in groups if "rule-1" in g.id]
        assert len(rule1_groups) == 1
        assert len(rule1_groups[0].alerts) == 3  # alerts 1, 2, 4


class TestAlertGroupAggregation:
    """Test alert group aggregation features."""
    
    def test_alert_counts(self, grouper, sample_alerts):
        """Test that alert counts are aggregated correctly."""
        groups = grouper.group_alerts(sample_alerts, GroupingStrategy.BY_RESOURCE)
        
        # Find service-a group
        service_a = [g for g in groups if "Service A" in g.name][0]
        
        # Should have 2 active alerts (alert-1 and alert-2)
        assert service_a.active_count == 2
        assert service_a.acknowledged_count == 0
        assert service_a.resolved_count == 0
    
    def test_highest_severity(self, grouper, sample_alerts):
        """Test that highest severity is tracked correctly."""
        groups = grouper.group_alerts(sample_alerts, GroupingStrategy.BY_RESOURCE)
        
        # Find service-a group (has WARNING and CRITICAL)
        service_a = [g for g in groups if "Service A" in g.name][0]
        
        # Should show CRITICAL as highest severity
        assert service_a.highest_severity == AlertSeverity.CRITICAL
    
    def test_affected_resources(self, grouper, sample_alerts):
        """Test that affected resources are tracked."""
        groups = grouper.group_alerts(sample_alerts, GroupingStrategy.BY_SEVERITY)
        
        # Find critical group
        critical = [g for g in groups if g.highest_severity == AlertSeverity.CRITICAL][0]
        
        # Should track service-a and service-b
        assert len(critical.affected_resources) == 2
        assert "service-a" in critical.affected_resources
        assert "service-b" in critical.affected_resources


class TestAlertDeduplication:
    """Test alert deduplication."""
    
    def test_deduplicate_alerts(self, grouper):
        """Test basic deduplication."""
        # Create duplicate alerts
        base_time = datetime.now(UTC)
        alerts = [
            Alert(
                id="alert-1",
                rule_id="rule-1",
                trigger_type=TriggerType.HEALTH_SCORE_DROP,
                severity=AlertSeverity.WARNING,
                status=AlertStatus.ACTIVE,
                title="Test Alert",
                message="Test",
                resource_id="service-a",
                triggered_at=base_time,
            ),
            Alert(
                id="alert-2",
                rule_id="rule-1",
                trigger_type=TriggerType.HEALTH_SCORE_DROP,
                severity=AlertSeverity.WARNING,
                status=AlertStatus.ACTIVE,
                title="Test Alert",
                message="Test",
                resource_id="service-a",
                triggered_at=base_time + timedelta(minutes=1),
            ),
        ]
        
        deduplicated = grouper.deduplicate_alerts(alerts)
        
        # Should keep only the most recent one
        assert len(deduplicated) == 1
        assert deduplicated[0].id == "alert-2"
    
    def test_deduplicate_different_resources(self, grouper):
        """Test that alerts for different resources are not deduplicated."""
        base_time = datetime.now(UTC)
        alerts = [
            Alert(
                id="alert-1",
                rule_id="rule-1",
                trigger_type=TriggerType.HEALTH_SCORE_DROP,
                severity=AlertSeverity.WARNING,
                status=AlertStatus.ACTIVE,
                title="Test Alert A",
                message="Test",
                resource_id="service-a",
                triggered_at=base_time,
            ),
            Alert(
                id="alert-2",
                rule_id="rule-1",
                trigger_type=TriggerType.HEALTH_SCORE_DROP,
                severity=AlertSeverity.WARNING,
                status=AlertStatus.ACTIVE,
                title="Test Alert B",
                message="Test",
                resource_id="service-b",
                triggered_at=base_time,
            ),
        ]
        
        deduplicated = grouper.deduplicate_alerts(alerts)
        
        # Should keep both
        assert len(deduplicated) == 2


class TestDigestCreation:
    """Test alert digest creation."""
    
    def test_create_digest(self, grouper, sample_alerts):
        """Test creating an alert digest."""
        digest = grouper.create_digest(sample_alerts, GroupingStrategy.BY_RESOURCE)
        
        assert "total_alerts" in digest
        assert digest["total_alerts"] == 4
        
        assert "total_groups" in digest
        assert digest["total_groups"] == 3
        
        assert "groups" in digest
        assert len(digest["groups"]) == 3
    
    def test_digest_summary(self, grouper, sample_alerts):
        """Test that digest includes summary statistics."""
        digest = grouper.create_digest(sample_alerts, GroupingStrategy.BY_SEVERITY)
        
        assert "summary" in digest
        summary = digest["summary"]
        
        assert "active" in summary
        assert "acknowledged" in summary
        assert "resolved" in summary
        assert "critical" in summary
        
        # Check counts
        assert summary["active"] == 2  # alerts 1 and 2
        assert summary["acknowledged"] == 1  # alert 3
        assert summary["resolved"] == 1  # alert 4
    
    def test_digest_includes_grouping_strategy(self, grouper, sample_alerts):
        """Test that digest includes grouping strategy."""
        digest = grouper.create_digest(sample_alerts, GroupingStrategy.BY_TYPE)
        
        assert digest["grouping_strategy"] == "by_type"


class TestAlertGroupMethods:
    """Test AlertGroup methods."""
    
    def test_get_summary(self):
        """Test AlertGroup summary generation."""
        group = AlertGroup(
            id="test-group",
            name="Test Group",
            grouping_strategy=GroupingStrategy.BY_RESOURCE,
        )
        
        # Add some test alerts
        for i in range(3):
            alert = Alert(
                id=f"alert-{i}",
                rule_id="rule-1",
                trigger_type=TriggerType.HEALTH_SCORE_DROP,
                severity=AlertSeverity.WARNING,
                status=AlertStatus.ACTIVE if i < 2 else AlertStatus.RESOLVED,
                title=f"Alert {i}",
                message="Test",
                resource_id="service-a",
            )
            group.add_alert(alert)
        
        summary = group.get_summary()
        
        assert "3 alert(s)" in summary
        assert "Active: 2" in summary
        assert "Resolved: 1" in summary
    
    def test_to_dict(self):
        """Test AlertGroup dictionary conversion."""
        group = AlertGroup(
            id="test-group",
            name="Test Group",
            grouping_strategy=GroupingStrategy.BY_RESOURCE,
        )
        
        alert = Alert(
            id="alert-1",
            rule_id="rule-1",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            title="Test Alert",
            message="Test",
            resource_id="service-a",
        )
        group.add_alert(alert)
        
        group_dict = group.to_dict()
        
        assert group_dict["id"] == "test-group"
        assert group_dict["name"] == "Test Group"
        assert group_dict["alert_count"] == 1
        assert group_dict["active_count"] == 1
        assert "summary" in group_dict
