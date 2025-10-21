"""
Example script demonstrating ML-based prediction capabilities.

This script shows how to:
1. Predict resource failures
2. Forecast performance metrics
3. Detect anomalies
4. Integrate predictions with monitoring
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from topdeck.analysis.prediction import Predictor
from topdeck.analysis.prediction.feature_extractor import FeatureExtractor


async def example_failure_prediction():
    """Example: Predict resource failure."""
    print("=" * 60)
    print("EXAMPLE 1: Failure Prediction")
    print("=" * 60)
    
    feature_extractor = FeatureExtractor()
    predictor = Predictor(feature_extractor=feature_extractor)
    
    # Predict failure for a database
    prediction = await predictor.predict_failure(
        resource_id="sql-db-prod",
        resource_name="Production Database",
        resource_type="database"
    )
    
    print(f"\nResource: {prediction.resource_name}")
    print(f"Failure Probability: {prediction.failure_probability:.1%}")
    print(f"Risk Level: {prediction.risk_level.value.upper()}")
    print(f"Confidence: {prediction.confidence.value.upper()}")
    
    if prediction.time_to_failure_hours:
        print(f"Estimated Time to Failure: {prediction.time_to_failure_hours:.0f} hours")
    
    print("\nTop Contributing Factors:")
    for factor in prediction.contributing_factors[:3]:
        print(f"  - {factor.description}")
        print(f"    Importance: {factor.importance:.1%}")
        if factor.current_value and factor.threshold:
            print(f"    Current: {factor.current_value:.2f}, Threshold: {factor.threshold:.2f}")
    
    print("\nRecommendations:")
    for i, rec in enumerate(prediction.recommendations, 1):
        print(f"  {i}. {rec}")
    
    print()


async def example_performance_prediction():
    """Example: Predict performance degradation."""
    print("=" * 60)
    print("EXAMPLE 2: Performance Prediction")
    print("=" * 60)
    
    feature_extractor = FeatureExtractor()
    predictor = Predictor(feature_extractor=feature_extractor)
    
    # Predict latency for next 24 hours
    prediction = await predictor.predict_performance(
        resource_id="api-gateway",
        resource_name="API Gateway",
        metric_name="latency_p95",
        horizon_hours=24
    )
    
    print(f"\nResource: {prediction.resource_name}")
    print(f"Metric: {prediction.metric_name}")
    print(f"Current Value: {prediction.current_value:.1f}ms")
    print(f"Baseline: {prediction.baseline_value:.1f}ms")
    print(f"Trend: {prediction.trend.upper()}")
    print(f"Degradation Risk: {prediction.degradation_risk.value.upper()}")
    
    # Show first few predictions
    print(f"\nForecast (next 6 hours):")
    for pred in prediction.predictions[:6]:
        print(f"  {pred.timestamp.strftime('%H:%M')}: {pred.predicted_value:.1f}ms "
              f"(range: {pred.confidence_lower:.1f}-{pred.confidence_upper:.1f}ms)")
    
    print("\nRecommendations:")
    for i, rec in enumerate(prediction.recommendations, 1):
        print(f"  {i}. {rec}")
    
    print()


async def example_anomaly_detection():
    """Example: Detect anomalies."""
    print("=" * 60)
    print("EXAMPLE 3: Anomaly Detection")
    print("=" * 60)
    
    feature_extractor = FeatureExtractor()
    predictor = Predictor(feature_extractor=feature_extractor)
    
    # Detect anomalies in last 24 hours
    detection = await predictor.detect_anomalies(
        resource_id="webapp-prod",
        resource_name="Production Web App",
        window_hours=24
    )
    
    print(f"\nResource: {detection.resource_name}")
    print(f"Overall Anomaly Score: {detection.overall_anomaly_score:.2f}")
    print(f"Risk Level: {detection.risk_level.value.upper()}")
    
    if detection.anomalies:
        print(f"\nAnomalies Detected: {len(detection.anomalies)}")
        for anomaly in detection.anomalies[:3]:
            print(f"  - {anomaly.metric_name} at {anomaly.timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"    Expected: {anomaly.expected_value:.2f}, Actual: {anomaly.actual_value:.2f}")
            print(f"    Deviation: {anomaly.deviation_percentage:.1f}%")
    else:
        print("\nNo anomalies detected - system operating normally")
    
    if detection.affected_metrics:
        print(f"\nAffected Metrics: {', '.join(detection.affected_metrics)}")
    
    if detection.potential_causes:
        print("\nPotential Causes:")
        for cause in detection.potential_causes:
            print(f"  - {cause}")
    
    print("\nRecommendations:")
    for i, rec in enumerate(detection.recommendations, 1):
        print(f"  {i}. {rec}")
    
    print()


async def example_monitoring_integration():
    """Example: Integrate predictions with monitoring."""
    print("=" * 60)
    print("EXAMPLE 4: Monitoring Integration")
    print("=" * 60)
    
    feature_extractor = FeatureExtractor()
    predictor = Predictor(feature_extractor=feature_extractor)
    
    # List of critical resources to monitor
    critical_resources = [
        ("sql-db-prod", "Production Database", "database"),
        ("api-gateway", "API Gateway", "load_balancer"),
        ("webapp-prod", "Production Web App", "web_app"),
    ]
    
    print("\nMonitoring Critical Resources:")
    print("-" * 60)
    
    high_risk_resources = []
    
    for resource_id, resource_name, resource_type in critical_resources:
        prediction = await predictor.predict_failure(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_type=resource_type
        )
        
        status_icon = "🔴" if prediction.risk_level.value in ["high", "critical"] else \
                     "🟡" if prediction.risk_level.value == "medium" else "🟢"
        
        print(f"\n{status_icon} {resource_name}")
        print(f"   Risk Level: {prediction.risk_level.value.upper()}")
        print(f"   Failure Probability: {prediction.failure_probability:.1%}")
        
        if prediction.risk_level.value in ["high", "critical"]:
            high_risk_resources.append((resource_name, prediction))
            print(f"   ⚠️  ATTENTION NEEDED")
    
    # Alert on high-risk resources
    if high_risk_resources:
        print("\n" + "=" * 60)
        print("⚠️  HIGH RISK ALERTS")
        print("=" * 60)
        
        for resource_name, prediction in high_risk_resources:
            print(f"\n🚨 {resource_name}")
            print(f"   Failure Probability: {prediction.failure_probability:.1%}")
            if prediction.time_to_failure_hours:
                print(f"   Estimated Time to Failure: {prediction.time_to_failure_hours:.0f} hours")
            print(f"   Action Required:")
            for rec in prediction.recommendations[:3]:
                print(f"     • {rec}")
    else:
        print("\n✅ All systems operating normally")
    
    print()


async def example_batch_prediction():
    """Example: Batch predictions for multiple resources."""
    print("=" * 60)
    print("EXAMPLE 5: Batch Predictions")
    print("=" * 60)
    
    feature_extractor = FeatureExtractor()
    predictor = Predictor(feature_extractor=feature_extractor)
    
    resources = [
        ("db-1", "Database 1", "database"),
        ("db-2", "Database 2", "database"),
        ("api-1", "API Server 1", "web_app"),
        ("api-2", "API Server 2", "web_app"),
        ("lb-1", "Load Balancer", "load_balancer"),
    ]
    
    print("\nRunning batch predictions...")
    
    predictions = []
    for resource_id, resource_name, resource_type in resources:
        prediction = await predictor.predict_failure(
            resource_id=resource_id,
            resource_name=resource_name,
            resource_type=resource_type
        )
        predictions.append(prediction)
    
    # Sort by failure probability
    predictions.sort(key=lambda p: p.failure_probability, reverse=True)
    
    print("\nRisk Ranking (Highest to Lowest):")
    print("-" * 60)
    
    for i, pred in enumerate(predictions, 1):
        risk_bar = "█" * int(pred.failure_probability * 20)
        print(f"{i}. {pred.resource_name:20} [{risk_bar:<20}] {pred.failure_probability:.1%}")
    
    print()


async def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "TopDeck ML Prediction Examples" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    await example_failure_prediction()
    await asyncio.sleep(1)
    
    await example_performance_prediction()
    await asyncio.sleep(1)
    
    await example_anomaly_detection()
    await asyncio.sleep(1)
    
    await example_monitoring_integration()
    await asyncio.sleep(1)
    
    await example_batch_prediction()
    
    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nFor more information:")
    print("  - API Documentation: /api/docs")
    print("  - Research: docs/ML_PREDICTION_RESEARCH.md")
    print("  - Usage Guide: docs/ML_PREDICTION_GUIDE.md")
    print()


if __name__ == "__main__":
    asyncio.run(main())
