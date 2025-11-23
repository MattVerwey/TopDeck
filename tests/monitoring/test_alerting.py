"""
Unit tests for the alerting engine.

Tests cover:
- Alert rule management
- Alert destination management
- Rule evaluation logic
- Alert triggering
- Notification sending
- Alert deduplication
- Alert acknowledgment and resolution
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from topdeck.monitoring.alerting import (
    Alert,
    AlertDestination,
    AlertDestinationType,
    AlertingEngine,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    TriggerType,
)


@pytest.fixture
def mock_diagnostics_service():
    """Mock Live Diagnostics Service."""
    service = AsyncMock()
    
    # Mock snapshot with healthy services
    mock_snapshot = MagicMock()
    mock_snapshot.services = [
        MagicMock(
            resource_id="service-1",
            resource_name="Service 1",
            health_score=95.0,
        ),
        MagicMock(
            resource_id="service-2",
            resource_name="Service 2",
            health_score=85.0,
        ),
    ]
    mock_snapshot.anomalies = []
    mock_snapshot.traffic_patterns = []
    
    service.get_live_snapshot = AsyncMock(return_value=mock_snapshot)
    
    return service


@pytest.fixture
def alerting_engine(mock_diagnostics_service):
    """Create an alerting engine instance."""
    return AlertingEngine(
        diagnostics_service=mock_diagnostics_service,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="alerts@example.com",
        smtp_password="password123",
        smtp_from_address="alerts@example.com",
    )


class TestAlertRuleManagement:
    """Test alert rule CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_add_rule(self, alerting_engine):
        """Test adding an alert rule."""
        rule = AlertRule(
            id="rule-1",
            name="Test Rule",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            threshold=50.0,
            severity=AlertSeverity.WARNING,
        )
        
        await alerting_engine.add_rule(rule)
        
        assert "rule-1" in alerting_engine.rules
        assert alerting_engine.rules["rule-1"].name == "Test Rule"
    
    @pytest.mark.asyncio
    async def test_update_rule(self, alerting_engine):
        """Test updating an existing alert rule."""
        rule = AlertRule(
            id="rule-1",
            name="Test Rule",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            threshold=50.0,
        )
        await alerting_engine.add_rule(rule)
        
        # Update the rule
        updated_rule = AlertRule(
            id="rule-1",
            name="Updated Rule",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            threshold=40.0,
        )
        await alerting_engine.add_rule(updated_rule)
        
        assert alerting_engine.rules["rule-1"].name == "Updated Rule"
        assert alerting_engine.rules["rule-1"].threshold == 40.0
    
    @pytest.mark.asyncio
    async def test_remove_rule(self, alerting_engine):
        """Test removing an alert rule."""
        rule = AlertRule(
            id="rule-1",
            name="Test Rule",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
        )
        await alerting_engine.add_rule(rule)
        
        await alerting_engine.remove_rule("rule-1")
        
        assert "rule-1" not in alerting_engine.rules
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_rule(self, alerting_engine):
        """Test removing a rule that doesn't exist."""
        # Should not raise an error
        await alerting_engine.remove_rule("nonexistent-rule")


class TestAlertDestinationManagement:
    """Test alert destination CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_add_destination(self, alerting_engine):
        """Test adding an alert destination."""
        destination = AlertDestination(
            id="dest-1",
            name="Email Destination",
            type=AlertDestinationType.EMAIL,
            config={"recipients": ["admin@example.com"]},
        )
        
        await alerting_engine.add_destination(destination)
        
        assert "dest-1" in alerting_engine.destinations
        assert alerting_engine.destinations["dest-1"].name == "Email Destination"
    
    @pytest.mark.asyncio
    async def test_update_destination(self, alerting_engine):
        """Test updating an existing destination."""
        destination = AlertDestination(
            id="dest-1",
            name="Email Destination",
            type=AlertDestinationType.EMAIL,
            config={"recipients": ["admin@example.com"]},
        )
        await alerting_engine.add_destination(destination)
        
        # Update the destination
        updated_destination = AlertDestination(
            id="dest-1",
            name="Updated Email",
            type=AlertDestinationType.EMAIL,
            config={"recipients": ["admin@example.com", "ops@example.com"]},
        )
        await alerting_engine.add_destination(updated_destination)
        
        assert alerting_engine.destinations["dest-1"].name == "Updated Email"
        assert len(alerting_engine.destinations["dest-1"].config["recipients"]) == 2
    
    @pytest.mark.asyncio
    async def test_remove_destination(self, alerting_engine):
        """Test removing an alert destination."""
        destination = AlertDestination(
            id="dest-1",
            name="Email Destination",
            type=AlertDestinationType.EMAIL,
        )
        await alerting_engine.add_destination(destination)
        
        await alerting_engine.remove_destination("dest-1")
        
        assert "dest-1" not in alerting_engine.destinations


class TestRuleEvaluation:
    """Test alert rule evaluation logic."""
    
    @pytest.mark.asyncio
    async def test_health_score_drop_triggers(self, alerting_engine, mock_diagnostics_service):
        """Test that health score drop rule triggers correctly."""
        # Setup mock with low health score
        mock_snapshot = MagicMock()
        mock_snapshot.services = [
            MagicMock(
                resource_id="service-1",
                resource_name="Failing Service",
                health_score=30.0,
            ),
        ]
        mock_snapshot.anomalies = []
        mock_snapshot.traffic_patterns = []
        mock_diagnostics_service.get_live_snapshot = AsyncMock(return_value=mock_snapshot)
        
        rule = AlertRule(
            id="rule-1",
            name="Health Score Drop",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            threshold=50.0,
            severity=AlertSeverity.WARNING,
        )
        await alerting_engine.add_rule(rule)
        
        alerts = await alerting_engine.evaluate_rules(duration_hours=1)
        
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.WARNING
        assert "service-1" in alerts[0].message
    
    @pytest.mark.asyncio
    async def test_health_score_drop_no_trigger(self, alerting_engine, mock_diagnostics_service):
        """Test that rule doesn't trigger when health is good."""
        # Mock shows healthy services
        mock_snapshot = MagicMock()
        mock_snapshot.services = [
            MagicMock(
                resource_id="service-1",
                resource_name="Healthy Service",
                health_score=95.0,
            ),
        ]
        mock_snapshot.anomalies = []
        mock_snapshot.traffic_patterns = []
        mock_diagnostics_service.get_live_snapshot = AsyncMock(return_value=mock_snapshot)
        
        rule = AlertRule(
            id="rule-1",
            name="Health Score Drop",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            threshold=50.0,
        )
        await alerting_engine.add_rule(rule)
        
        alerts = await alerting_engine.evaluate_rules(duration_hours=1)
        
        assert len(alerts) == 0
    
    @pytest.mark.asyncio
    async def test_critical_anomaly_triggers(self, alerting_engine, mock_diagnostics_service):
        """Test that critical anomaly rule triggers correctly."""
        mock_snapshot = MagicMock()
        mock_snapshot.services = []
        mock_snapshot.anomalies = [
            MagicMock(
                resource_id="service-1",
                resource_name="Service 1",
                metric_name="error_rate",
                severity="critical",
                deviation=5.0,
            ),
        ]
        mock_snapshot.traffic_patterns = []
        mock_diagnostics_service.get_live_snapshot = AsyncMock(return_value=mock_snapshot)
        
        rule = AlertRule(
            id="rule-1",
            name="Critical Anomaly",
            trigger_type=TriggerType.CRITICAL_ANOMALY,
            severity=AlertSeverity.CRITICAL,
        )
        await alerting_engine.add_rule(rule)
        
        alerts = await alerting_engine.evaluate_rules(duration_hours=1)
        
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.CRITICAL
    
    @pytest.mark.asyncio
    async def test_disabled_rule_not_evaluated(self, alerting_engine, mock_diagnostics_service):
        """Test that disabled rules are not evaluated."""
        mock_snapshot = MagicMock()
        mock_snapshot.services = [
            MagicMock(
                resource_id="service-1",
                resource_name="Failing Service",
                health_score=10.0,
            ),
        ]
        mock_snapshot.anomalies = []
        mock_snapshot.traffic_patterns = []
        mock_diagnostics_service.get_live_snapshot = AsyncMock(return_value=mock_snapshot)
        
        rule = AlertRule(
            id="rule-1",
            name="Health Score Drop",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            threshold=50.0,
            enabled=False,  # Disabled
        )
        await alerting_engine.add_rule(rule)
        
        alerts = await alerting_engine.evaluate_rules(duration_hours=1)
        
        assert len(alerts) == 0


class TestAlertDeduplication:
    """Test alert deduplication logic."""
    
    @pytest.mark.asyncio
    async def test_deduplication_prevents_duplicate(self, alerting_engine, mock_diagnostics_service):
        """Test that alerts are deduplicated within the duration window."""
        mock_snapshot = MagicMock()
        mock_snapshot.services = [
            MagicMock(
                resource_id="service-1",
                resource_name="Failing Service",
                health_score=30.0,
            ),
        ]
        mock_snapshot.anomalies = []
        mock_snapshot.traffic_patterns = []
        mock_diagnostics_service.get_live_snapshot = AsyncMock(return_value=mock_snapshot)
        
        rule = AlertRule(
            id="rule-1",
            name="Health Score Drop",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            threshold=50.0,
            duration_minutes=5,
        )
        await alerting_engine.add_rule(rule)
        
        # First evaluation - should trigger
        alerts1 = await alerting_engine.evaluate_rules(duration_hours=1)
        assert len(alerts1) == 1
        
        # Second evaluation immediately after - should not trigger
        alerts2 = await alerting_engine.evaluate_rules(duration_hours=1)
        assert len(alerts2) == 0
    
    @pytest.mark.asyncio
    async def test_deduplication_expires(self, alerting_engine, mock_diagnostics_service):
        """Test that deduplication expires after duration window."""
        mock_snapshot = MagicMock()
        mock_snapshot.services = [
            MagicMock(
                resource_id="service-1",
                resource_name="Failing Service",
                health_score=30.0,
            ),
        ]
        mock_snapshot.anomalies = []
        mock_snapshot.traffic_patterns = []
        mock_diagnostics_service.get_live_snapshot = AsyncMock(return_value=mock_snapshot)
        
        rule = AlertRule(
            id="rule-1",
            name="Health Score Drop",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            threshold=50.0,
            duration_minutes=5,
        )
        await alerting_engine.add_rule(rule)
        
        # First evaluation - should trigger
        alerts1 = await alerting_engine.evaluate_rules(duration_hours=1)
        assert len(alerts1) == 1
        
        # Manually expire the deduplication window
        alerting_engine.last_alert_times[rule.id] = (
            datetime.now(UTC) - timedelta(minutes=10)
        )
        
        # Second evaluation - should trigger again
        alerts2 = await alerting_engine.evaluate_rules(duration_hours=1)
        assert len(alerts2) == 1


class TestAlertAcknowledgment:
    """Test alert acknowledgment and resolution."""
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, alerting_engine):
        """Test acknowledging an alert."""
        alert = Alert(
            id="alert-1",
            rule_id="rule-1",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            title="Test Alert",
            message="Test message",
        )
        alerting_engine.alerts[alert.id] = alert
        alerting_engine.active_alerts[alert.id] = alert
        
        acknowledged = await alerting_engine.acknowledge_alert("alert-1", "admin")
        
        assert acknowledged is not None
        assert acknowledged.status == AlertStatus.ACKNOWLEDGED
        assert acknowledged.acknowledged_by == "admin"
        assert acknowledged.acknowledged_at is not None
    
    @pytest.mark.asyncio
    async def test_resolve_alert(self, alerting_engine):
        """Test resolving an alert."""
        alert = Alert(
            id="alert-1",
            rule_id="rule-1",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACKNOWLEDGED,
            title="Test Alert",
            message="Test message",
        )
        alerting_engine.alerts[alert.id] = alert
        alerting_engine.active_alerts[alert.id] = alert
        
        resolved = await alerting_engine.resolve_alert("alert-1")
        
        assert resolved is not None
        assert resolved.status == AlertStatus.RESOLVED
        assert resolved.resolved_at is not None
        assert "alert-1" not in alerting_engine.active_alerts
    
    @pytest.mark.asyncio
    async def test_acknowledge_nonexistent_alert(self, alerting_engine):
        """Test acknowledging an alert that doesn't exist."""
        result = await alerting_engine.acknowledge_alert("nonexistent", "admin")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_resolve_nonexistent_alert(self, alerting_engine):
        """Test resolving an alert that doesn't exist."""
        result = await alerting_engine.resolve_alert("nonexistent")
        assert result is None


class TestAlertHistory:
    """Test alert history tracking."""
    
    @pytest.mark.asyncio
    async def test_get_alerts(self, alerting_engine):
        """Test retrieving alerts."""
        alert1 = Alert(
            id="alert-1",
            rule_id="rule-1",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.WARNING,
            status=AlertStatus.RESOLVED,
            title="Test Alert 1",
            message="Test message 1",
            resource_id="service-1",
            triggered_at=datetime.now(UTC) - timedelta(hours=2),
        )
        alert2 = Alert(
            id="alert-2",
            rule_id="rule-1",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            title="Test Alert 2",
            message="Test message 2",
            resource_id="service-1",
            triggered_at=datetime.now(UTC) - timedelta(hours=1),
        )
        
        alerting_engine.alerts[alert1.id] = alert1
        alerting_engine.alerts[alert2.id] = alert2
        
        alerts = await alerting_engine.get_alerts(hours=24)
        
        assert len(alerts) == 2
        # Should be sorted by time (newest first)
        assert alerts[0].id == "alert-2"
        assert alerts[1].id == "alert-1"
    
    @pytest.mark.asyncio
    async def test_get_alerts_filtered_by_severity(self, alerting_engine):
        """Test retrieving alerts filtered by severity."""
        alert1 = Alert(
            id="alert-1",
            rule_id="rule-1",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.WARNING,
            status=AlertStatus.RESOLVED,
            title="Warning Alert",
            message="Warning message",
            resource_id="service-1",
        )
        alert2 = Alert(
            id="alert-2",
            rule_id="rule-2",
            trigger_type=TriggerType.CRITICAL_ANOMALY,
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACTIVE,
            title="Critical Alert",
            message="Critical message",
            resource_id="service-2",
        )
        
        alerting_engine.alerts[alert1.id] = alert1
        alerting_engine.alerts[alert2.id] = alert2
        
        alerts = await alerting_engine.get_alerts(
            hours=24,
            severity=AlertSeverity.CRITICAL,
        )
        
        assert len(alerts) == 1
        assert history[0].severity == AlertSeverity.CRITICAL


class TestNotificationSending:
    """Test notification sending to various channels."""
    
    @pytest.mark.asyncio
    async def test_send_email_notification(self, alerting_engine):
        """Test sending email notification."""
        destination = AlertDestination(
            id="dest-1",
            name="Email Destination",
            type=AlertDestinationType.EMAIL,
            config={"recipients": ["admin@example.com"]},
        )
        
        alert = Alert(
            id="alert-1",
            rule_id="rule-1",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            title="Test Alert",
            message="Test message",
        )
        
        with patch("aiosmtplib.send") as mock_send:
            mock_send.return_value = None
            
            await alerting_engine._send_email(destination, alert)
            
            assert mock_send.called
    
    @pytest.mark.asyncio
    async def test_send_slack_notification(self, alerting_engine):
        """Test sending Slack notification."""
        destination = AlertDestination(
            id="dest-1",
            name="Slack Destination",
            type=AlertDestinationType.SLACK,
            config={"webhook_url": "https://hooks.slack.com/services/TEST"},
        )
        
        alert = Alert(
            id="alert-1",
            rule_id="rule-1",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            title="Test Alert",
            message="Test message",
        )
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            await alerting_engine._send_slack(destination, alert)
            
            assert mock_post.called
    
    @pytest.mark.asyncio
    async def test_send_webhook_notification(self, alerting_engine):
        """Test sending webhook notification."""
        destination = AlertDestination(
            id="dest-1",
            name="Webhook Destination",
            type=AlertDestinationType.WEBHOOK,
            config={"url": "https://example.com/webhook"},
        )
        
        alert = Alert(
            id="alert-1",
            rule_id="rule-1",
            trigger_type=TriggerType.HEALTH_SCORE_DROP,
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            title="Test Alert",
            message="Test message",
        )
        
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            await alerting_engine._send_webhook(destination, alert)
            
            assert mock_post.called
