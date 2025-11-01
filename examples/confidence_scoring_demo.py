#!/usr/bin/env python
"""
Demonstration of Enhanced ML Confidence Scoring.

This example shows how the multi-factor confidence scoring system works
with different feature sets and quality levels.
"""
import asyncio
from datetime import datetime, timezone

from topdeck.analysis.prediction import Predictor
from topdeck.analysis.prediction.feature_extractor import FeatureExtractor
from topdeck.analysis.prediction.models import PredictionConfidence, RiskLevel


async def demo_confidence_scenarios():
    """Demonstrate confidence scoring with various scenarios."""
    predictor = Predictor(feature_extractor=FeatureExtractor())

    print("=" * 80)
    print("Enhanced ML Confidence Scoring Demonstration")
    print("=" * 80)

    # Scenario 1: Minimal Data (Low Confidence)
    print("\n📊 Scenario 1: Minimal Data")
    print("-" * 80)
    print("Context: Only 2 features available")

    prediction1 = await predictor.predict_failure(
        resource_id="minimal-data-service",
        resource_name="Service with Minimal Data",
        resource_type="web_app",
    )

    print(f"Confidence: {prediction1.confidence.value.upper()}")
    if prediction1.confidence_metrics:
        print(f"Overall Score: {prediction1.confidence_metrics.overall_score:.3f}")
        print(f"  - Completeness: {prediction1.confidence_metrics.feature_completeness:.3f}")
        print(f"  - Quality: {prediction1.confidence_metrics.feature_quality:.3f}")
        print(f"  - Recency: {prediction1.confidence_metrics.data_recency:.3f}")
        print(f"  - Consistency: {prediction1.confidence_metrics.prediction_consistency:.3f}")
        print(
            f"  - Features: {prediction1.confidence_metrics.valid_features}/"
            f"{prediction1.confidence_metrics.total_features} valid"
        )
    print("\n💡 Interpretation: Low confidence due to minimal feature data.")
    print("   Action: Gather more data before relying on this prediction.")

    # Scenario 2: Good Data (High Confidence)
    print("\n📊 Scenario 2: Well-Monitored Service")
    print("-" * 80)
    print("Context: Comprehensive monitoring with 20+ features")

    prediction2 = await predictor.predict_failure(
        resource_id="well-monitored-db",
        resource_name="Production Database",
        resource_type="database",
    )

    print(f"Confidence: {prediction2.confidence.value.upper()}")
    if prediction2.confidence_metrics:
        print(f"Overall Score: {prediction2.confidence_metrics.overall_score:.3f}")
        print(f"  - Completeness: {prediction2.confidence_metrics.feature_completeness:.3f}")
        print(f"  - Quality: {prediction2.confidence_metrics.feature_quality:.3f}")
        print(f"  - Recency: {prediction2.confidence_metrics.data_recency:.3f}")
        print(f"  - Consistency: {prediction2.confidence_metrics.prediction_consistency:.3f}")
        print(
            f"  - Features: {prediction2.confidence_metrics.valid_features}/"
            f"{prediction2.confidence_metrics.total_features} valid"
        )
    print(f"\nRisk Level: {prediction2.risk_level.value.upper()}")
    print(f"Failure Probability: {prediction2.failure_probability:.1%}")
    print("\n💡 Interpretation: High confidence with comprehensive data.")
    print("   Action: Can safely act on this prediction.")

    # Scenario 3: Understanding Factor Breakdown
    print("\n📊 Scenario 3: Factor Breakdown Analysis")
    print("-" * 80)
    print("Understanding what affects confidence:")

    print("\n1️⃣  Feature Completeness (30% weight)")
    print("   - Measures: How many features are available")
    print("   - Impact: More features = better predictions")
    print(f"   - Current: {prediction2.confidence_metrics.total_features} features")

    print("\n2️⃣  Feature Quality (30% weight)")
    print("   - Measures: Are feature values valid?")
    print("   - Impact: Invalid data reduces reliability")
    print(
        f"   - Current: {prediction2.confidence_metrics.valid_features}/"
        f"{prediction2.confidence_metrics.total_features} valid"
    )

    print("\n3️⃣  Data Recency (20% weight)")
    print("   - Measures: How recent is the data?")
    print("   - Impact: Recent patterns more relevant")
    print(f"   - Current Score: {prediction2.confidence_metrics.data_recency:.3f}")

    print("\n4️⃣  Prediction Consistency (20% weight)")
    print("   - Measures: Variance in metrics")
    print("   - Impact: Low variance = predictable patterns")
    print(f"   - Current Score: {prediction2.confidence_metrics.prediction_consistency:.3f}")

    # Scenario 4: Using Confidence in Decision Making
    print("\n📊 Scenario 4: Automated Decision Making")
    print("-" * 80)
    print("How to use confidence in automation:\n")

    prediction3 = await predictor.predict_failure(
        resource_id="api-gateway-prod",
        resource_name="API Gateway",
        resource_type="load_balancer",
    )

    print(f"Resource: {prediction3.resource_name}")
    print(f"Confidence: {prediction3.confidence.value.upper()}")
    print(f"Risk Level: {prediction3.risk_level.value.upper()}")
    print(f"Failure Probability: {prediction3.failure_probability:.1%}\n")

    # Decision logic based on confidence and risk
    if prediction3.confidence == PredictionConfidence.HIGH:
        if prediction3.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            print("✅ Decision: AUTOMATICALLY SCALE/ALERT")
            print("   Reason: High confidence + High risk = Act immediately")
        else:
            print("✅ Decision: CONTINUE MONITORING")
            print("   Reason: High confidence + Low risk = Normal operation")
    elif prediction3.confidence == PredictionConfidence.MEDIUM:
        if prediction3.failure_probability > 0.7:
            print("⚠️  Decision: ALERT OPS TEAM FOR REVIEW")
            print("   Reason: Medium confidence + High probability = Manual review")
        else:
            print("⚠️  Decision: MONITOR CLOSELY")
            print("   Reason: Medium confidence = Watch for changes")
    else:  # LOW confidence
        print("ℹ️  Decision: LOG AND MONITOR")
        print("   Reason: Low confidence = Need more data")

    print("\n" + "=" * 80)
    print("Summary: Enhanced Confidence Scoring Benefits")
    print("=" * 80)
    print("✅ Multi-factor analysis (completeness, quality, recency, consistency)")
    print("✅ Transparent breakdown of confidence factors")
    print("✅ Protection against false confidence with minimal data")
    print("✅ Actionable insights for improving predictions")
    print("✅ Better automated decision-making support")
    print("\n📖 For more details, see: docs/ML_CONFIDENCE_SCORING.md")


def main():
    """Run the demonstration."""
    asyncio.run(demo_confidence_scenarios())


if __name__ == "__main__":
    main()
