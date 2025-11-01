"""
Model calibration based on accuracy feedback.

Adjusts prediction thresholds and confidence levels based on historical
accuracy to improve future predictions.
"""

from datetime import datetime, timezone, timedelta
from typing import Any

import structlog

from topdeck.storage.neo4j_client import Neo4jClient
from .models import PredictionOutcome
from .prediction_tracker import PredictionTracker

logger = structlog.get_logger(__name__)


class PredictionCalibrator:
    """
    Calibrates prediction models based on historical accuracy.
    
    Uses accuracy feedback to:
    1. Adjust failure probability thresholds
    2. Recalibrate confidence levels
    3. Identify systematic biases
    4. Recommend feature weight adjustments
    """

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize calibrator.
        
        Args:
            neo4j_client: Neo4j client for storage
        """
        self.neo4j = neo4j_client
        self.tracker = PredictionTracker(neo4j_client)

    async def calibrate_thresholds(
        self, target_precision: float = 0.85, time_range_days: int = 30
    ) -> dict[str, float]:
        """
        Calibrate failure probability thresholds to achieve target precision.
        
        Analyzes false positive rate and adjusts the threshold where we
        classify a prediction as "will fail" vs "won't fail".
        
        Args:
            target_precision: Desired precision (default: 0.85)
            time_range_days: Time range for analysis
            
        Returns:
            Dictionary with recommended thresholds
        """
        # Get current accuracy metrics
        start_date = datetime.now(timezone.utc) - timedelta(days=time_range_days)
        result = await self.tracker.get_accuracy_metrics(start_date=start_date)
        
        current_precision = result.metrics.precision
        current_recall = result.metrics.recall
        
        # Calculate optimal threshold adjustment
        # If precision is too low, increase threshold (be more conservative)
        # If precision is too high and recall is low, decrease threshold
        
        current_threshold = 0.5  # Default threshold
        
        if current_precision < target_precision:
            # Too many false positives, increase threshold
            adjustment_factor = target_precision / max(current_precision, 0.01)
            new_threshold = min(0.9, current_threshold * adjustment_factor)
            recommendation = "increase"
        elif current_precision > target_precision + 0.05 and current_recall < 0.8:
            # Precision is good but missing too many failures, decrease threshold
            adjustment_factor = current_recall / 0.9
            new_threshold = max(0.3, current_threshold * adjustment_factor)
            recommendation = "decrease"
        else:
            # Balanced, keep current threshold
            new_threshold = current_threshold
            recommendation = "maintain"
        
        logger.info(
            "calibrated_threshold",
            current_precision=current_precision,
            current_recall=current_recall,
            current_threshold=current_threshold,
            new_threshold=new_threshold,
            recommendation=recommendation,
        )
        
        return {
            "current_threshold": current_threshold,
            "recommended_threshold": new_threshold,
            "current_precision": current_precision,
            "current_recall": current_recall,
            "target_precision": target_precision,
            "recommendation": recommendation,
            "adjustment_needed": abs(new_threshold - current_threshold) > 0.05,
        }

    async def analyze_systematic_errors(
        self, time_range_days: int = 30
    ) -> dict[str, Any]:
        """
        Analyze systematic errors in predictions.
        
        Identifies patterns in false positives and false negatives to
        understand where the model is failing.
        
        Args:
            time_range_days: Time range for analysis
            
        Returns:
            Dictionary with error analysis
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=time_range_days)
        
        # Get predictions by outcome and resource type
        query = """
        MATCH (p:Prediction)
        WHERE datetime(p.predicted_at) >= datetime($start_date)
          AND p.outcome_type <> $pending
        RETURN 
            p.outcome_type as outcome,
            p.metadata.resource_type as resource_type,
            p.confidence as confidence,
            p.failure_probability as probability,
            count(*) as count
        """
        
        results = await self.neo4j.execute_query(
            query,
            {
                "start_date": start_date.isoformat(),
                "pending": PredictionOutcome.PENDING.value,
            },
        )
        
        # Analyze patterns
        false_positives_by_type = {}
        false_negatives_by_type = {}
        errors_by_confidence = {"high": 0, "medium": 0, "low": 0}
        
        for row in results:
            outcome = PredictionOutcome(row["outcome"])
            resource_type = row.get("resource_type", "unknown")
            confidence = row.get("confidence", "unknown")
            count = row["count"]
            
            if outcome == PredictionOutcome.FALSE_POSITIVE:
                false_positives_by_type[resource_type] = (
                    false_positives_by_type.get(resource_type, 0) + count
                )
                if confidence in errors_by_confidence:
                    errors_by_confidence[confidence] += count
            elif outcome == PredictionOutcome.FALSE_NEGATIVE:
                false_negatives_by_type[resource_type] = (
                    false_negatives_by_type.get(resource_type, 0) + count
                )
                if confidence in errors_by_confidence:
                    errors_by_confidence[confidence] += count
        
        # Identify problematic resource types
        most_fp = max(false_positives_by_type.items(), key=lambda x: x[1])[0] if false_positives_by_type else None
        most_fn = max(false_negatives_by_type.items(), key=lambda x: x[1])[0] if false_negatives_by_type else None
        
        analysis = {
            "false_positives_by_type": false_positives_by_type,
            "false_negatives_by_type": false_negatives_by_type,
            "errors_by_confidence": errors_by_confidence,
            "most_false_positives": most_fp,
            "most_false_negatives": most_fn,
            "recommendations": [],
        }
        
        # Generate recommendations
        if most_fp:
            analysis["recommendations"].append(
                f"Review predictions for {most_fp} - high false positive rate. "
                f"Consider increasing threshold or improving features."
            )
        
        if most_fn:
            analysis["recommendations"].append(
                f"Review predictions for {most_fn} - high false negative rate. "
                f"Consider decreasing threshold or adding more sensitive features."
            )
        
        if errors_by_confidence.get("high", 0) > 5:
            analysis["recommendations"].append(
                "High-confidence predictions have errors. Review confidence calculation."
            )
        
        return analysis

    async def calibrate_confidence_levels(
        self, time_range_days: int = 30
    ) -> dict[str, Any]:
        """
        Calibrate confidence levels based on actual accuracy.
        
        Ensures that predictions with "high" confidence are actually more
        accurate than "medium" or "low" confidence predictions.
        
        Args:
            time_range_days: Time range for analysis
            
        Returns:
            Dictionary with confidence calibration results
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=time_range_days)
        
        # Get accuracy by confidence level
        query = """
        MATCH (p:Prediction)
        WHERE datetime(p.predicted_at) >= datetime($start_date)
          AND p.outcome_type <> $pending
        WITH p.confidence as confidence,
             p.outcome_type as outcome,
             count(*) as count
        RETURN confidence, outcome, count
        """
        
        results = await self.neo4j.execute_query(
            query,
            {
                "start_date": start_date.isoformat(),
                "pending": PredictionOutcome.PENDING.value,
            },
        )
        
        # Calculate accuracy by confidence level
        confidence_metrics = {}
        
        for confidence in ["high", "medium", "low"]:
            tp = sum(
                row["count"]
                for row in results
                if row["confidence"] == confidence
                and PredictionOutcome(row["outcome"]) == PredictionOutcome.TRUE_POSITIVE
            )
            tn = sum(
                row["count"]
                for row in results
                if row["confidence"] == confidence
                and PredictionOutcome(row["outcome"]) == PredictionOutcome.TRUE_NEGATIVE
            )
            fp = sum(
                row["count"]
                for row in results
                if row["confidence"] == confidence
                and PredictionOutcome(row["outcome"]) == PredictionOutcome.FALSE_POSITIVE
            )
            fn = sum(
                row["count"]
                for row in results
                if row["confidence"] == confidence
                and PredictionOutcome(row["outcome"]) == PredictionOutcome.FALSE_NEGATIVE
            )
            
            total = tp + tn + fp + fn
            if total > 0:
                accuracy = (tp + tn) / total
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                
                confidence_metrics[confidence] = {
                    "accuracy": accuracy,
                    "precision": precision,
                    "total_predictions": total,
                    "correct": tp + tn,
                    "incorrect": fp + fn,
                }
        
        # Check if confidence levels are calibrated
        is_calibrated = True
        issues = []
        
        if "high" in confidence_metrics and "medium" in confidence_metrics:
            if confidence_metrics["high"]["accuracy"] < confidence_metrics["medium"]["accuracy"]:
                is_calibrated = False
                issues.append("High confidence predictions are less accurate than medium")
        
        if "medium" in confidence_metrics and "low" in confidence_metrics:
            if confidence_metrics["medium"]["accuracy"] < confidence_metrics["low"]["accuracy"]:
                is_calibrated = False
                issues.append("Medium confidence predictions are less accurate than low")
        
        return {
            "is_calibrated": is_calibrated,
            "confidence_metrics": confidence_metrics,
            "issues": issues,
            "recommendation": (
                "Confidence levels are well calibrated"
                if is_calibrated
                else "Review confidence calculation - levels not properly ordered"
            ),
        }

    async def generate_improvement_report(self) -> dict[str, Any]:
        """
        Generate comprehensive improvement report.
        
        Combines all calibration analyses to provide actionable recommendations
        for improving prediction accuracy.
        
        Returns:
            Dictionary with complete improvement report
        """
        # Get all analyses
        threshold_calibration = await self.calibrate_thresholds()
        error_analysis = await self.analyze_systematic_errors()
        confidence_calibration = await self.calibrate_confidence_levels()
        
        # Get current metrics
        metrics_result = await self.tracker.get_accuracy_metrics()
        
        # Generate summary
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_metrics": {
                "precision": metrics_result.metrics.precision,
                "recall": metrics_result.metrics.recall,
                "f1_score": metrics_result.metrics.f1_score,
                "accuracy": metrics_result.metrics.accuracy,
            },
            "threshold_calibration": threshold_calibration,
            "error_analysis": error_analysis,
            "confidence_calibration": confidence_calibration,
            "priority_actions": [],
        }
        
        # Determine priority actions
        if threshold_calibration["adjustment_needed"]:
            report["priority_actions"].append({
                "priority": "high",
                "action": "adjust_threshold",
                "details": (
                    f"Adjust failure threshold from {threshold_calibration['current_threshold']:.2f} "
                    f"to {threshold_calibration['recommended_threshold']:.2f}"
                ),
            })
        
        if not confidence_calibration["is_calibrated"]:
            report["priority_actions"].append({
                "priority": "high",
                "action": "recalibrate_confidence",
                "details": "Confidence levels not properly ordered - review calculation",
            })
        
        if error_analysis.get("most_false_positives"):
            report["priority_actions"].append({
                "priority": "medium",
                "action": "review_resource_type",
                "details": f"Review predictions for {error_analysis['most_false_positives']}",
            })
        
        logger.info("generated_improvement_report", actions_count=len(report["priority_actions"]))
        
        return report
