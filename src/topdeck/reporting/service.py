"""
Reporting Service.

Provides business logic for generating comprehensive reports with charts
and analysis showing resource health, changes, errors, and correlations.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from topdeck.reporting.chart_generator import ChartGenerator
from topdeck.reporting.models import (
    Report,
    ReportConfig,
    ReportFormat,
    ReportMetadata,
    ReportSection,
    ReportStatus,
    ReportType,
)
from topdeck.reporting.pdf_generator import PDFGenerator
from topdeck.reporting.utils import parse_timestamp
from topdeck.storage.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class ReportingService:
    """Service for generating comprehensive reports."""

    def __init__(self, neo4j_client: Neo4jClient) -> None:
        """
        Initialize reporting service.

        Args:
            neo4j_client: Neo4j client for querying topology and events
        """
        self.neo4j_client = neo4j_client
        self.pdf_generator = PDFGenerator()

    def generate_report(
        self,
        report_type: ReportType,
        report_format: ReportFormat = ReportFormat.JSON,
        config: ReportConfig | None = None,
    ) -> Report:
        """
        Generate a report based on the specified type.

        Args:
            report_type: Type of report to generate
            report_format: Output format for the report
            config: Configuration for report generation

        Returns:
            Generated Report object
        """
        if config is None:
            config = ReportConfig()

        report_id = str(uuid4())
        metadata = ReportMetadata(
            report_id=report_id,
            report_type=report_type,
            report_format=report_format,
            generated_at=datetime.now(UTC),
            resource_id=config.resource_id,
            time_range_start=datetime.now(UTC) - timedelta(hours=config.time_range_hours),
            time_range_end=datetime.now(UTC),
        )

        try:
            if report_type == ReportType.RESOURCE_HEALTH:
                return self._generate_resource_health_report(metadata, config)
            elif report_type == ReportType.CHANGE_IMPACT:
                return self._generate_change_impact_report(metadata, config)
            elif report_type == ReportType.ERROR_TIMELINE:
                return self._generate_error_timeline_report(metadata, config)
            elif report_type == ReportType.CODE_DEPLOYMENT_CORRELATION:
                return self._generate_deployment_correlation_report(metadata, config)
            elif report_type == ReportType.COMPREHENSIVE:
                return self._generate_comprehensive_report(metadata, config)
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
        except Exception as e:
            logger.error(f"Failed to generate report: {e}", exc_info=True)
            return Report(
                metadata=metadata,
                title=f"{report_type.value.replace('_', ' ').title()} Report",
                summary="Report generation failed",
                status=ReportStatus.FAILED,
                error_message=str(e),
            )

    def export_report_as_pdf(self, report: Report) -> bytes:
        """
        Export a report as PDF.

        Args:
            report: Report object to export

        Returns:
            PDF document as bytes
        """
        return self.pdf_generator.generate_pdf(report)

    def _generate_resource_health_report(
        self, metadata: ReportMetadata, config: ReportConfig
    ) -> Report:
        """Generate a resource health report."""
        sections: list[ReportSection] = []

        # Fetch resource information
        resource = self._get_resource_info(config.resource_id)
        if not resource:
            return Report(
                metadata=metadata,
                title="Resource Health Report",
                summary="Resource not found",
                status=ReportStatus.FAILED,
                error_message=f"Resource {config.resource_id} not found",
            )

        # Summary section
        summary_text = (
            f"Health report for {resource.get('name', 'Unknown Resource')} "
            f"covering the last {config.time_range_hours} hours."
        )

        sections.append(
            ReportSection(
                title="Overview",
                content=self._generate_resource_overview(resource),
                section_type="text",
                data={"resource": resource},
                order=1,
            )
        )

        # Get health metrics
        health_metrics = self._get_resource_health_metrics(
            config.resource_id, config.time_range_hours
        )

        if config.include_charts and health_metrics:
            health_chart = ChartGenerator.generate_resource_health_chart(health_metrics)
            sections.append(
                ReportSection(
                    title="Health Metrics Over Time",
                    content="Resource health metrics showing CPU, memory, and performance indicators.",
                    section_type="chart",
                    data={"metrics": health_metrics},
                    charts=[health_chart],
                    order=2,
                )
            )

        # Get errors for this resource
        if config.include_error_details:
            errors = self._get_resource_errors(config.resource_id, config.time_range_hours)
            if errors:
                sections.append(
                    ReportSection(
                        title="Error Summary",
                        content=self._generate_error_summary(errors),
                        section_type="text",
                        data={"errors": errors[: config.max_errors]},
                        order=3,
                    )
                )

        return Report(
            metadata=metadata,
            title=f"Health Report: {resource.get('name', 'Resource')}",
            summary=summary_text,
            sections=sections,
            status=ReportStatus.COMPLETED,
        )

    def _generate_change_impact_report(
        self, metadata: ReportMetadata, config: ReportConfig
    ) -> Report:
        """Generate a change impact report."""
        sections: list[ReportSection] = []

        # Get changes affecting the resource or service
        changes = self._get_changes(config.resource_id, config.time_range_hours)

        summary_text = (
            f"Change impact analysis showing {len(changes)} changes "
            f"in the last {config.time_range_hours} hours."
        )

        # Changes overview
        sections.append(
            ReportSection(
                title="Changes Overview",
                content=self._generate_changes_overview(changes),
                section_type="text",
                data={"changes": changes[: config.max_changes]},
                order=1,
            )
        )

        # Change impact chart
        if config.include_charts and changes:
            change_chart = ChartGenerator.generate_change_impact_chart(changes)
            sections.append(
                ReportSection(
                    title="Change Distribution",
                    content="Distribution of changes by type and risk level.",
                    section_type="chart",
                    charts=[change_chart],
                    order=2,
                )
            )

        # Impact analysis per change
        if config.include_change_details and changes:
            sections.append(
                ReportSection(
                    title="Detailed Change Analysis",
                    content=self._generate_change_details(changes[: config.max_changes]),
                    section_type="text",
                    data={"detailed_changes": changes[: config.max_changes]},
                    order=3,
                )
            )

        return Report(
            metadata=metadata,
            title="Change Impact Report",
            summary=summary_text,
            sections=sections,
            status=ReportStatus.COMPLETED,
        )

    def _generate_error_timeline_report(
        self, metadata: ReportMetadata, config: ReportConfig
    ) -> Report:
        """Generate an error timeline report."""
        sections: list[ReportSection] = []

        # Get errors
        errors = self._get_resource_errors(config.resource_id, config.time_range_hours)

        summary_text = (
            f"Error timeline showing {len(errors)} errors "
            f"in the last {config.time_range_hours} hours."
        )

        # Error summary
        sections.append(
            ReportSection(
                title="Error Summary",
                content=self._generate_error_summary(errors),
                section_type="text",
                data={"errors": errors[: config.max_errors]},
                order=1,
            )
        )

        # Error timeline chart
        if config.include_charts and errors:
            error_chart = ChartGenerator.generate_error_timeline_chart(errors)
            sections.append(
                ReportSection(
                    title="Error Timeline",
                    content="Timeline showing when errors occurred and their severity.",
                    section_type="chart",
                    charts=[error_chart],
                    order=2,
                )
            )

        # Detailed error list
        if config.include_error_details and errors:
            sections.append(
                ReportSection(
                    title="Error Details",
                    content=self._generate_error_details(errors[: config.max_errors]),
                    section_type="table",
                    data={"detailed_errors": errors[: config.max_errors]},
                    order=3,
                )
            )

        return Report(
            metadata=metadata,
            title="Error Timeline Report",
            summary=summary_text,
            sections=sections,
            status=ReportStatus.COMPLETED,
        )

    def _generate_deployment_correlation_report(
        self, metadata: ReportMetadata, config: ReportConfig
    ) -> Report:
        """Generate a code deployment correlation report."""
        sections: list[ReportSection] = []

        # Get deployments and code changes
        deployments = self._get_deployments(config.resource_id, config.time_range_hours)
        errors = self._get_resource_errors(config.resource_id, config.time_range_hours)

        summary_text = (
            f"Deployment correlation showing {len(deployments)} deployments "
            f"and {len(errors)} errors in the last {config.time_range_hours} hours."
        )

        # Deployments overview
        sections.append(
            ReportSection(
                title="Deployments Overview",
                content=self._generate_deployments_overview(deployments),
                section_type="text",
                data={"deployments": deployments},
                order=1,
            )
        )

        # Correlation chart
        if config.include_charts and (deployments or errors):
            correlation_chart = ChartGenerator.generate_deployment_correlation_chart(
                deployments, errors
            )
            sections.append(
                ReportSection(
                    title="Deployment and Error Correlation",
                    content="Chart showing the relationship between deployments and error rates.",
                    section_type="chart",
                    charts=[correlation_chart],
                    order=2,
                )
            )

        # Code changes details
        if config.include_code_changes and deployments:
            sections.append(
                ReportSection(
                    title="Code Changes",
                    content=self._generate_code_changes_details(deployments),
                    section_type="text",
                    data={"code_changes": deployments},
                    order=3,
                )
            )

        # Stability analysis
        sections.append(
            ReportSection(
                title="Stability Analysis",
                content=self._generate_stability_analysis(deployments, errors),
                section_type="text",
                data={"stability_metrics": self._calculate_stability_metrics(deployments, errors)},
                order=4,
            )
        )

        return Report(
            metadata=metadata,
            title="Code Deployment Correlation Report",
            summary=summary_text,
            sections=sections,
            status=ReportStatus.COMPLETED,
        )

    def _generate_comprehensive_report(
        self, metadata: ReportMetadata, config: ReportConfig
    ) -> Report:
        """Generate a comprehensive report combining all report types."""
        sections: list[ReportSection] = []

        # Get all data
        resource = self._get_resource_info(config.resource_id)
        changes = self._get_changes(config.resource_id, config.time_range_hours)
        errors = self._get_resource_errors(config.resource_id, config.time_range_hours)
        deployments = self._get_deployments(config.resource_id, config.time_range_hours)
        health_metrics = self._get_resource_health_metrics(
            config.resource_id, config.time_range_hours
        )

        summary_text = (
            f"Comprehensive report covering resource health, "
            f"{len(changes)} changes, {len(errors)} errors, "
            f"and {len(deployments)} deployments in the last {config.time_range_hours} hours."
        )

        # Resource overview
        if resource:
            sections.append(
                ReportSection(
                    title="Resource Overview",
                    content=self._generate_resource_overview(resource),
                    section_type="text",
                    data={"resource": resource},
                    order=1,
                )
            )

        # Health metrics
        if health_metrics and config.include_charts:
            health_chart = ChartGenerator.generate_resource_health_chart(health_metrics)
            sections.append(
                ReportSection(
                    title="Health Metrics",
                    content="Resource health metrics over time.",
                    section_type="chart",
                    charts=[health_chart],
                    order=2,
                )
            )

        # Changes
        if changes:
            sections.append(
                ReportSection(
                    title="Changes",
                    content=self._generate_changes_overview(changes),
                    section_type="text",
                    data={"changes": changes[: config.max_changes]},
                    order=3,
                )
            )

        # Errors
        if errors:
            sections.append(
                ReportSection(
                    title="Errors",
                    content=self._generate_error_summary(errors),
                    section_type="text",
                    data={"errors": errors[: config.max_errors]},
                    order=4,
                )
            )

            if config.include_charts:
                error_chart = ChartGenerator.generate_error_timeline_chart(errors)
                sections.append(
                    ReportSection(
                        title="Error Timeline",
                        content="Timeline of errors by severity.",
                        section_type="chart",
                        charts=[error_chart],
                        order=5,
                    )
                )

        # Deployment correlation
        if deployments and config.include_charts:
            correlation_chart = ChartGenerator.generate_deployment_correlation_chart(
                deployments, errors
            )
            sections.append(
                ReportSection(
                    title="Deployment Correlation",
                    content="Correlation between deployments and errors.",
                    section_type="chart",
                    charts=[correlation_chart],
                    order=6,
                )
            )

        # Stability analysis
        sections.append(
            ReportSection(
                title="Stability Analysis",
                content=self._generate_stability_analysis(deployments, errors),
                section_type="text",
                data={"stability_metrics": self._calculate_stability_metrics(deployments, errors)},
                order=7,
            )
        )

        return Report(
            metadata=metadata,
            title=f"Comprehensive Report: {resource.get('name', 'Resource') if resource else 'System'}",
            summary=summary_text,
            sections=sections,
            status=ReportStatus.COMPLETED,
        )

    # Helper methods for data retrieval and formatting

    def _get_resource_info(self, resource_id: str | None) -> dict[str, Any] | None:
        """Get resource information from Neo4j."""
        if not resource_id:
            return None

        try:
            query = """
            MATCH (r:Resource {id: $resource_id})
            RETURN r.id as id, r.name as name, r.type as type, 
                   r.status as status, r.region as region,
                   r.properties as properties
            LIMIT 1
            """
            result = self.neo4j_client.execute_query(query, {"resource_id": resource_id})
            if result and len(result) > 0:
                return dict(result[0])
            return None
        except Exception as e:
            logger.error(f"Failed to get resource info: {e}")
            return None

    def _get_resource_health_metrics(
        self, resource_id: str | None, hours: int
    ) -> list[dict[str, Any]]:
        """
        Get health metrics for a resource.

        TODO: This is a placeholder that should integrate with monitoring systems
        (Prometheus, Azure Monitor, CloudWatch, etc.) to fetch actual health metrics
        like CPU usage, memory usage, latency, and error rates.

        Args:
            resource_id: ID of the resource
            hours: Number of hours to look back

        Returns:
            List of health metric snapshots (currently empty)
        """
        # Log warning that this is not yet implemented
        logger.warning(
            "Health metrics integration not yet implemented. "
            "Reports will not include health metric charts. "
            "Integrate with Prometheus/monitoring systems to enable this feature."
        )

        # Placeholder - integrate with Prometheus/monitoring systems
        # Example structure:
        # [
        #   {
        #     "timestamp": datetime.now(UTC),
        #     "cpu_usage": 45.5,
        #     "memory_usage": 60.2,
        #     "error_rate": 0.01,
        #     "latency_p95": 250.0
        #   }
        # ]
        return []

    def _get_resource_errors(
        self, resource_id: str | None, hours: int
    ) -> list[dict[str, Any]]:
        """Get errors for a resource."""
        try:
            start_time = datetime.now(UTC) - timedelta(hours=hours)
            query = """
            MATCH (e:Error)
            WHERE ($resource_id IS NULL OR e.resource_id = $resource_id)
              AND e.timestamp >= $start_time
            RETURN e.error_id as error_id, e.timestamp as timestamp,
                   e.severity as severity, e.message as message,
                   e.error_type as error_type, e.resource_id as resource_id
            ORDER BY e.timestamp DESC
            """
            result = self.neo4j_client.execute_query(
                query, {"resource_id": resource_id, "start_time": start_time.isoformat()}
            )
            return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to get errors: {e}")
            return []

    def _get_changes(self, resource_id: str | None, hours: int) -> list[dict[str, Any]]:
        """Get changes affecting a resource."""
        try:
            start_time = datetime.now(UTC) - timedelta(hours=hours)
            query = """
            MATCH (c:Change)
            WHERE ($resource_id IS NULL OR $resource_id IN c.affected_resources)
              AND c.created_at >= $start_time
            RETURN c.id as id, c.title as title, c.change_type as change_type,
                   c.risk_level as risk_level, c.status as status,
                   c.created_at as created_at, c.scheduled_start as scheduled_start
            ORDER BY c.created_at DESC
            """
            result = self.neo4j_client.execute_query(
                query, {"resource_id": resource_id, "start_time": start_time.isoformat()}
            )
            return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to get changes: {e}")
            return []

    def _get_deployments(self, resource_id: str | None, hours: int) -> list[dict[str, Any]]:
        """Get deployments to a resource."""
        try:
            start_time = datetime.now(UTC) - timedelta(hours=hours)
            query = """
            MATCH (d:Deployment)
            WHERE ($resource_id IS NULL OR d.target_resource = $resource_id)
              AND d.timestamp >= $start_time
            RETURN d.id as id, d.timestamp as timestamp, d.version as version,
                   d.commit_sha as commit_sha, d.status as status,
                   d.repository as repository
            ORDER BY d.timestamp DESC
            """
            result = self.neo4j_client.execute_query(
                query, {"resource_id": resource_id, "start_time": start_time.isoformat()}
            )
            return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to get deployments: {e}")
            return []

    def _generate_resource_overview(self, resource: dict[str, Any]) -> str:
        """Generate resource overview text."""
        return f"""
**Resource Name**: {resource.get('name', 'Unknown')}
**Type**: {resource.get('type', 'Unknown')}
**Status**: {resource.get('status', 'Unknown')}
**Region**: {resource.get('region', 'Unknown')}
**Resource ID**: {resource.get('id', 'Unknown')}
"""

    def _generate_error_summary(self, errors: list[dict[str, Any]]) -> str:
        """Generate error summary text."""
        if not errors:
            return "No errors found in the specified time range."

        severity_counts: dict[str, int] = {}
        for error in errors:
            severity = error.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        summary = f"**Total Errors**: {len(errors)}\n\n"
        summary += "**By Severity**:\n"
        for severity, count in sorted(severity_counts.items()):
            summary += f"- {severity.title()}: {count}\n"

        return summary

    def _generate_error_details(self, errors: list[dict[str, Any]]) -> str:
        """Generate detailed error list."""
        if not errors:
            return "No errors to display."

        details = "| Time | Severity | Message | Type |\n"
        details += "|------|----------|---------|------|\n"

        for error in errors[:20]:  # Limit to 20 for readability
            timestamp = error.get("timestamp", "Unknown")
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            message = error.get('message', 'No message')
            truncated_message = f"{message[:50]}{'...' if len(message) > 50 else ''}"
            details += (
                f"| {timestamp} | {error.get('severity', 'Unknown')} | "
                f"{truncated_message} | "
                f"{error.get('error_type', 'Unknown')} |\n"
            )

        return details

    def _generate_changes_overview(self, changes: list[dict[str, Any]]) -> str:
        """Generate changes overview text."""
        if not changes:
            return "No changes found in the specified time range."

        type_counts: dict[str, int] = {}
        risk_counts: dict[str, int] = {}

        for change in changes:
            change_type = change.get("change_type", "unknown")
            type_counts[change_type] = type_counts.get(change_type, 0) + 1

            risk_level = change.get("risk_level", "unknown")
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1

        summary = f"**Total Changes**: {len(changes)}\n\n"
        summary += "**By Type**:\n"
        for change_type, count in sorted(type_counts.items()):
            summary += f"- {change_type.replace('_', ' ').title()}: {count}\n"

        summary += "\n**By Risk Level**:\n"
        for risk, count in sorted(risk_counts.items()):
            summary += f"- {risk.title()}: {count}\n"

        return summary

    def _generate_change_details(self, changes: list[dict[str, Any]]) -> str:
        """Generate detailed change list."""
        if not changes:
            return "No changes to display."

        details = ""
        for i, change in enumerate(changes[:10], 1):  # Limit to 10
            details += f"\n**{i}. {change.get('title', 'Untitled Change')}**\n"
            details += f"- Type: {change.get('change_type', 'Unknown')}\n"
            details += f"- Risk: {change.get('risk_level', 'Unknown')}\n"
            details += f"- Status: {change.get('status', 'Unknown')}\n"

            created_at = change.get("created_at")
            if isinstance(created_at, datetime):
                created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
            details += f"- Created: {created_at}\n"

        return details

    def _generate_deployments_overview(self, deployments: list[dict[str, Any]]) -> str:
        """Generate deployments overview text."""
        if not deployments:
            return "No deployments found in the specified time range."

        summary = f"**Total Deployments**: {len(deployments)}\n\n"

        status_counts: dict[str, int] = {}
        for deployment in deployments:
            status = deployment.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        summary += "**By Status**:\n"
        for status, count in sorted(status_counts.items()):
            summary += f"- {status.title()}: {count}\n"

        return summary

    def _generate_code_changes_details(self, deployments: list[dict[str, Any]]) -> str:
        """Generate code changes details."""
        if not deployments:
            return "No code changes to display."

        details = ""
        for i, deployment in enumerate(deployments[:10], 1):  # Limit to 10
            details += f"\n**{i}. Deployment {deployment.get('id', 'Unknown')}**\n"
            details += f"- Version: {deployment.get('version', 'Unknown')}\n"
            details += f"- Commit: {deployment.get('commit_sha', 'Unknown')}\n"
            details += f"- Repository: {deployment.get('repository', 'Unknown')}\n"
            details += f"- Status: {deployment.get('status', 'Unknown')}\n"

            timestamp = deployment.get("timestamp")
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            details += f"- Deployed: {timestamp}\n"

        return details

    def _generate_stability_analysis(
        self, deployments: list[dict[str, Any]], errors: list[dict[str, Any]]
    ) -> str:
        """Generate stability analysis text."""
        metrics = self._calculate_stability_metrics(deployments, errors)

        analysis = "**Stability Metrics**\n\n"
        analysis += f"- Deployment Success Rate: {metrics['deployment_success_rate']:.1f}%\n"
        analysis += f"- Errors Per Deployment: {metrics['errors_per_deployment']:.2f}\n"
        analysis += f"- Post-Deployment Error Rate: {metrics['post_deployment_error_rate']:.2f}\n"

        if metrics["unstable_periods"]:
            analysis += "\n**Unstable Periods Detected**:\n"
            for period in metrics["unstable_periods"][:5]:  # Top 5
                analysis += f"- {period}\n"
        else:
            analysis += "\n✅ No significant unstable periods detected.\n"

        return analysis

    def _calculate_stability_metrics(
        self, deployments: list[dict[str, Any]], errors: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate stability metrics."""
        total_deployments = len(deployments)
        total_errors = len(errors)

        # Calculate deployment success rate
        successful_deployments = sum(
            1 for d in deployments if d.get("status", "").lower() == "success"
        )
        deployment_success_rate = (
            (successful_deployments / total_deployments * 100) if total_deployments > 0 else 100.0
        )

        # Calculate errors per deployment
        errors_per_deployment = total_errors / total_deployments if total_deployments > 0 else 0.0

        # Analyze post-deployment errors
        post_deployment_errors = 0
        for deployment in deployments:
            deployment_time = parse_timestamp(deployment.get("timestamp"))
            if not deployment_time:
                continue

            # Count errors within 1 hour after deployment
            for error in errors:
                error_time = parse_timestamp(error.get("timestamp"))
                if not error_time:
                    continue

                if (
                    error_time > deployment_time
                    and error_time <= deployment_time + timedelta(hours=1)
                ):
                    post_deployment_errors += 1

        post_deployment_error_rate = (
            post_deployment_errors / total_deployments if total_deployments > 0 else 0.0
        )

        # Identify unstable periods (high error concentration)
        unstable_periods = []
        if errors:
            # Group errors by hour
            error_hours: dict[str, int] = {}
            for error in errors:
                error_time = parse_timestamp(error.get("timestamp"))
                if not error_time:
                    continue

                hour_key = error_time.strftime("%Y-%m-%d %H:00")
                error_hours[hour_key] = error_hours.get(hour_key, 0) + 1

            # Find hours with high error counts (threshold: > 5 errors)
            for hour, count in sorted(error_hours.items(), key=lambda x: x[1], reverse=True):
                if count > 5:
                    unstable_periods.append(f"{hour} ({count} errors)")

        return {
            "deployment_success_rate": deployment_success_rate,
            "errors_per_deployment": errors_per_deployment,
            "post_deployment_error_rate": post_deployment_error_rate,
            "unstable_periods": unstable_periods,
        }
