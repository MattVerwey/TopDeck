# SRE ML Enhancements - Quick Start Guide

**For**: Development Team  
**Purpose**: Quick reference for implementing ML-based SRE enhancements

---

## Overview

This guide provides a quick-start roadmap for implementing the ML enhancements identified in the [SRE ML Enhancements Research](./SRE_ML_ENHANCEMENTS_RESEARCH.md) document.

---

## Priority Matrix

| Feature | Priority | Impact | Effort | Status |
|---------|----------|--------|--------|--------|
| **Change Risk Prediction** | 🔴 HIGH | Very High | Medium | Not Started |
| **Blast Radius Intelligence** | 🔴 HIGH | Very High | Medium | Not Started |
| **Pre-Change Validation** | 🟡 MEDIUM | High | Medium | Not Started |
| **Change-Incident Correlation** | 🟡 MEDIUM | High | Low | Not Started |
| **Change Conflict Detection** | 🟡 MEDIUM | Medium | Low | Not Started |
| **Stakeholder Impact Prediction** | 🟢 FUTURE | Medium | High | Not Started |
| **Multi-Change Orchestration** | 🟢 FUTURE | Medium | High | Not Started |

---

## Quick Implementation: Change Risk Prediction (Week 1-4)

### Step 1: Data Collection (Day 1-3)

**Create Change Outcome Tracker**

```python
# src/topdeck/change_management/outcome_tracker.py

from datetime import datetime
from enum import Enum
from typing import Optional

class ChangeOutcome(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    PARTIAL_SUCCESS = "partial_success"

class ChangeOutcomeRecord:
    """Track actual outcomes of changes for ML training"""
    
    def __init__(
        self,
        change_id: str,
        outcome: ChangeOutcome,
        incident_count: int = 0,
        rollback_time_minutes: Optional[int] = None,
        affected_user_count: int = 0,
        error_rate_increase: float = 0.0,
        latency_increase_pct: float = 0.0,
    ):
        self.change_id = change_id
        self.outcome = outcome
        self.incident_count = incident_count
        self.rollback_time_minutes = rollback_time_minutes
        self.affected_user_count = affected_user_count
        self.error_rate_increase = error_rate_increase
        self.latency_increase_pct = latency_increase_pct
        self.recorded_at = datetime.now()
```

**Extend Change Model**

```python
# src/topdeck/change_management/models.py

# Add to ChangeRequest class:

actual_outcome: Optional[ChangeOutcome] = None
actual_blast_radius: List[str] = []  # Actual affected resources
actual_incident_ids: List[str] = []
performance_impact: Dict[str, float] = {}
```

### Step 2: Feature Extraction (Day 4-7)

**Create ML Feature Extractor**

```python
# src/topdeck/analysis/prediction/change_features.py

from typing import Dict, Any, List
import structlog

logger = structlog.get_logger(__name__)

class ChangeFeatureExtractor:
    """Extract features from changes for ML prediction"""
    
    def __init__(self, topology_service, prometheus):
        self.topology_service = topology_service
        self.prometheus = prometheus
    
    async def extract_features(
        self,
        change_id: str,
        resource_id: str,
        change_type: str
    ) -> Dict[str, Any]:
        """
        Extract all features for a change.
        
        Returns dict with:
        - Static features (resource properties)
        - Temporal features (time patterns)
        - Historical features (past changes)
        - System state features (current health)
        """
        
        features = {}
        
        # 1. Static features
        features.update(await self._extract_resource_features(resource_id))
        
        # 2. Temporal features
        features.update(self._extract_temporal_features(change_id))
        
        # 3. Historical features
        features.update(await self._extract_historical_features(resource_id))
        
        # 4. System state features
        features.update(await self._extract_system_state_features(resource_id))
        
        return features
    
    async def _extract_resource_features(self, resource_id: str) -> Dict:
        """Resource-specific features"""
        # Get from Neo4j
        resource = await self.topology_service.get_resource(resource_id)
        
        return {
            "resource_type": resource.type,
            "criticality_score": resource.criticality_score or 0,
            "dependency_count": len(resource.dependencies),
            "dependent_count": len(resource.dependents),
            "has_redundancy": resource.replica_count > 1,
            "age_days": (datetime.now() - resource.created_at).days,
        }
    
    def _extract_temporal_features(self, change_id: str) -> Dict:
        """Time-based features"""
        # TODO: Get scheduled_time from change object
        scheduled_time = datetime.now()  # Placeholder until implementation
        
        return {
            "day_of_week": scheduled_time.weekday(),
            "hour_of_day": scheduled_time.hour,
            "is_weekend": scheduled_time.weekday() >= 5,
            "is_business_hours": 9 <= scheduled_time.hour <= 17,
        }
    
    async def _extract_historical_features(self, resource_id: str) -> Dict:
        """Historical change patterns"""
        # Query past 90 days of changes
        past_changes = await self.get_recent_changes(resource_id, days=90)
        
        return {
            "changes_last_30_days": len([c for c in past_changes if c.age_days <= 30]),
            "failure_rate_90_days": self._calculate_failure_rate(past_changes),
            "avg_time_between_changes": self._avg_time_between(past_changes),
            "last_incident_days_ago": self._days_since_last_incident(resource_id),
        }
    
    async def get_recent_changes(self, resource_id: str, days: int):
        """Get recent changes for a resource - to be implemented"""
        # TODO: Implement change history retrieval
        return []
    
    def _calculate_failure_rate(self, changes):
        """Calculate failure rate from change history - to be implemented"""
        # TODO: Implement failure rate calculation
        if not changes:
            return 0.0
        failed = [c for c in changes if getattr(c, 'failed', False)]
        return len(failed) / len(changes)
    
    def _avg_time_between(self, changes):
        """Calculate average time between changes - to be implemented"""
        # TODO: Implement average time calculation
        return 0
    
    def _days_since_last_incident(self, resource_id: str):
        """Get days since last incident - to be implemented"""
        # TODO: Implement incident history lookup
        return 999
    
    async def _extract_system_state_features(self, resource_id: str) -> Dict:
        """Current system health"""
        # Get from Prometheus
        metrics = await self.prometheus.get_current_metrics(resource_id)
        
        return {
            "current_error_rate": metrics.get("error_rate", 0),
            "current_cpu_usage": metrics.get("cpu_usage", 0),
            "current_memory_usage": metrics.get("memory_usage", 0),
            "slo_burn_rate": metrics.get("slo_burn_rate", 0),
            "error_budget_remaining": metrics.get("error_budget_pct", 100),
        }
```

### Step 3: ML Model (Day 8-14)

**Implement Change Risk Model**

```python
# src/topdeck/analysis/prediction/change_risk_model.py

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import numpy as np

class ChangeRiskModel:
    """ML model for predicting change risk"""
    
    def __init__(self, model_path: str = "/data/models/change_risk"):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        
    def train(self, X, y):
        """
        Train the model on historical changes.
        
        Args:
            X: Feature matrix (changes x features)
            y: Target labels (0=success, 1=failure/rollback)
        """
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Use Gradient Boosting for better accuracy
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        self.model.fit(X_scaled, y)
        
        # Save model
        self._save_model()
    
    def predict_risk(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict risk for a new change.
        
        Returns:
            {
                "risk_score": 0-100,
                "failure_probability": 0-1,
                "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
                "confidence": 0-1,
                "top_risk_factors": [...]
            }
        """
        if self.model is None:
            self._load_model()
        
        # Convert features to array
        X = self._features_to_array(features)
        X_scaled = self.scaler.transform(X)
        
        # Get probability
        prob = self.model.predict_proba(X_scaled)[0]
        failure_prob = prob[1]  # Probability of failure class
        
        # Calculate risk score (0-100)
        risk_score = int(failure_prob * 100)
        
        # Determine risk level
        if risk_score < 25:
            risk_level = "LOW"
        elif risk_score < 50:
            risk_level = "MEDIUM"
        elif risk_score < 75:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        # Get feature importance
        importance = self.model.feature_importances_
        top_factors = self._get_top_risk_factors(features, importance)
        
        return {
            "risk_score": risk_score,
            "failure_probability": float(failure_prob),
            "risk_level": risk_level,
            "confidence": self._calculate_confidence(X_scaled),
            "top_risk_factors": top_factors
        }
    
    def _get_top_risk_factors(self, features: Dict, importance: np.ndarray, top_n: int = 5):
        """Identify top contributing risk factors"""
        factor_scores = []
        
        for i, feature_name in enumerate(self.feature_names):
            factor_scores.append({
                "factor": feature_name,
                "value": features.get(feature_name, 0),
                "importance": float(importance[i]),
                "impact": int(importance[i] * 100)
            })
        
        # Sort by importance
        factor_scores.sort(key=lambda x: x["importance"], reverse=True)
        return factor_scores[:top_n]
```

### Step 4: API Integration (Day 15-21)

**Add Prediction Endpoint**

```python
# src/topdeck/api/routes/ml_predictions.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/v1/ml", tags=["ml-predictions"])

class ChangeRiskRequest(BaseModel):
    change_type: str
    resource_id: str
    scheduled_time: str
    description: str
    affected_resources: List[str]

class RiskFactor(BaseModel):
    factor: str
    impact: int
    description: str

class ChangeRiskResponse(BaseModel):
    risk_score: int
    risk_level: str
    failure_probability: float
    confidence: float
    top_risk_factors: List[RiskFactor]
    recommendations: List[str]

@router.post("/change-risk-prediction", response_model=ChangeRiskResponse)
async def predict_change_risk(request: ChangeRiskRequest):
    """
    Predict the risk of a proposed change.
    
    Uses ML model trained on historical change outcomes.
    """
    try:
        # Extract features
        feature_extractor = ChangeFeatureExtractor()
        features = await feature_extractor.extract_features(
            change_id=None,  # New change, no ID yet
            resource_id=request.resource_id,
            change_type=request.change_type
        )
        
        # Get prediction
        model = ChangeRiskModel()
        prediction = model.predict_risk(features)
        
        # Generate recommendations
        recommendations = _generate_recommendations(prediction, features)
        
        return ChangeRiskResponse(
            risk_score=prediction["risk_score"],
            risk_level=prediction["risk_level"],
            failure_probability=prediction["failure_probability"],
            confidence=prediction["confidence"],
            top_risk_factors=[
                RiskFactor(
                    factor=f["factor"],
                    impact=f["impact"],
                    description=_describe_factor(f)
                )
                for f in prediction["top_risk_factors"]
            ],
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error("change_risk_prediction_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Quick Implementation: Blast Radius Intelligence (Week 5-8)

### Enhanced Blast Radius Prediction

**Key Difference from Current Implementation:**
- Current: Static graph traversal
- Enhanced: ML-based probability propagation

```python
# src/topdeck/analysis/prediction/blast_radius_ml.py

class BlastRadiusPredictor:
    """ML-enhanced blast radius prediction"""
    
    async def predict_blast_radius(
        self,
        resource_id: str,
        failure_scenario: str = "complete_outage",
        current_system_state: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Predict blast radius using ML and graph analysis.
        
        Improvements over static analysis:
        1. Considers probability of propagation (not just topology)
        2. Uses historical failure patterns
        3. Accounts for circuit breakers and timeouts
        4. Estimates user and revenue impact
        """
        
        # 1. Get static topology
        static_deps = await self._get_topology_dependencies(resource_id)
        
        # 2. Load historical failure patterns
        failure_patterns = await self._get_historical_failures(resource_id)
        
        # 3. Predict probability of cascade for each dependent
        impact_predictions = []
        
        for dep in static_deps:
            cascade_prob = await self._predict_cascade_probability(
                source=resource_id,
                target=dep.id,
                failure_scenario=failure_scenario,
                historical_patterns=failure_patterns
            )
            
            if cascade_prob > 0.1:  # 10% threshold
                impact_predictions.append({
                    "resource_id": dep.id,
                    "resource_name": dep.name,
                    "probability": cascade_prob,
                    "delay_seconds": self._estimate_propagation_delay(dep),
                    "severity": self._calculate_severity(cascade_prob, dep),
                    "user_impact": await self._estimate_user_impact(dep.id),
                    "revenue_impact": await self._estimate_revenue_impact(dep.id)
                })
        
        # 4. Sort by probability and severity
        impact_predictions.sort(key=lambda x: x["probability"], reverse=True)
        
        return {
            "immediate_impact": [p for p in impact_predictions if p["delay_seconds"] < 60],
            "cascading_impact": [p for p in impact_predictions if p["delay_seconds"] >= 60],
            "total_user_impact": sum(p["user_impact"] for p in impact_predictions),
            "total_revenue_impact": sum(p["revenue_impact"] for p in impact_predictions),
            "mttr_estimate_minutes": self._estimate_mttr(impact_predictions)
        }
```

---

## Testing Strategy

### Unit Tests

```python
# tests/prediction/test_change_risk_model.py

import pytest
from topdeck.analysis.prediction import ChangeRiskModel

def test_risk_prediction_low_risk():
    """Test low-risk change prediction"""
    model = ChangeRiskModel()
    
    features = {
        "dependency_count": 2,
        "failure_rate_90_days": 0.0,
        "current_error_rate": 0.001,
        "changes_last_30_days": 1,
        "is_business_hours": False,
    }
    
    prediction = model.predict_risk(features)
    
    assert prediction["risk_level"] in ["LOW", "MEDIUM"]
    assert 0 <= prediction["risk_score"] <= 100
    assert len(prediction["top_risk_factors"]) > 0

def test_risk_prediction_high_risk():
    """Test high-risk change prediction"""
    model = ChangeRiskModel()
    
    features = {
        "dependency_count": 15,
        "failure_rate_90_days": 0.3,
        "current_error_rate": 0.05,
        "changes_last_30_days": 8,
        "is_business_hours": True,
        "error_budget_remaining": 10,
    }
    
    prediction = model.predict_risk(features)
    
    assert prediction["risk_level"] in ["HIGH", "CRITICAL"]
    assert prediction["risk_score"] > 50
```

### Integration Tests

```python
# tests/integration/test_ml_change_workflow.py

@pytest.mark.integration
async def test_end_to_end_change_risk_workflow():
    """Test complete workflow from change creation to risk prediction"""
    
    # 1. Create a change request
    change = await create_change_request(
        resource_id="api-gateway-prod",
        change_type="deployment"
    )
    
    # 2. Get risk prediction
    risk = await get_change_risk(change.id)
    
    # 3. Verify prediction structure
    assert "risk_score" in risk
    assert "recommendations" in risk
    
    # 4. If high risk, check recommendations are provided
    if risk["risk_level"] in ["HIGH", "CRITICAL"]:
        assert len(risk["recommendations"]) > 0
```

---

## Monitoring & Metrics

### Model Performance Tracking

```python
# src/topdeck/analysis/prediction/model_monitoring.py

class ModelMonitor:
    """Track ML model performance in production"""
    
    async def record_prediction(
        self,
        change_id: str,
        predicted_risk: float,
        predicted_level: str
    ):
        """Record a prediction for later evaluation"""
        await self.db.store_prediction(
            change_id=change_id,
            predicted_risk=predicted_risk,
            predicted_level=predicted_level,
            predicted_at=datetime.now()
        )
    
    async def evaluate_prediction(
        self,
        change_id: str,
        actual_outcome: ChangeOutcome
    ):
        """Evaluate prediction accuracy after change completes"""
        
        prediction = await self.db.get_prediction(change_id)
        
        # Calculate accuracy
        actual_failed = actual_outcome in [
            ChangeOutcome.FAILED,
            ChangeOutcome.ROLLED_BACK
        ]
        
        predicted_high_risk = prediction.predicted_risk > 0.5
        
        is_correct = actual_failed == predicted_high_risk
        
        # Store result
        await self.db.store_evaluation(
            change_id=change_id,
            predicted_risk=prediction.predicted_risk,
            actual_outcome=actual_outcome,
            is_correct=is_correct
        )
        
        # Update metrics
        await self._update_accuracy_metrics()
```

### Key Metrics Dashboard

```
ML Model Performance Metrics:

1. Prediction Accuracy: 87% (target: 85%+)
2. False Positive Rate: 8% (target: <10%)
3. False Negative Rate: 5% (target: <5%)
4. Model Confidence: 0.82 average (target: 0.80+)
5. Feature Importance Stability: 95% (target: 90%+)

Change Management Impact:

6. Incident Reduction: 42% (target: 40%+)
7. Auto-Approved Changes: 35% (target: 30%+)
8. Approval Time Reduction: 55% (target: 50%+)
9. Rollback Rate: 3.2% (target: <5%)
10. MTTR Improvement: 28% (target: 30%+)
```

---

## Rollout Plan

### Week 1-2: Silent Mode
- Deploy models but don't show predictions to users
- Collect predictions and actual outcomes
- Validate accuracy in production

### Week 3-4: Observation Mode
- Show predictions in UI but marked as "beta"
- Don't use for automated decisions
- Gather user feedback

### Week 5-6: Advisory Mode
- Use predictions to provide recommendations
- Still require manual approval for all changes
- Monitor user trust and adoption

### Week 7-8: Partial Automation
- Auto-approve low-risk changes (score < 25)
- Require approval for higher-risk changes
- Monitor false positive rate

### Week 9+: Full Automation
- Auto-approve up to medium-risk (score < 50)
- Fast-track approvals for medium-high (50-75)
- Manual review only for critical (75+)

---

## Quick Reference: API Endpoints

```bash
# Predict change risk
curl -X POST http://localhost:8000/api/v1/ml/change-risk-prediction \
  -H "Content-Type: application/json" \
  -d '{
    "change_type": "deployment",
    "resource_id": "api-gateway-prod",
    "scheduled_time": "2024-11-25T02:00:00Z",
    "description": "Deploy API v2.1.0",
    "affected_resources": ["api-gateway-prod"]
  }'

# Predict blast radius
curl -X POST http://localhost:8000/api/v1/ml/blast-radius-prediction \
  -H "Content-Type: application/json" \
  -d '{
    "resource_id": "sql-db-prod",
    "failure_scenario": "complete_outage",
    "current_load": 0.75
  }'

# Pre-change validation
curl -X POST http://localhost:8000/api/v1/ml/pre-change-validation \
  -H "Content-Type: application/json" \
  -d '{
    "change_id": "CHG-2024-5678",
    "resource_id": "payment-service",
    "scheduled_time": "2024-11-25T14:00:00Z"
  }'

# Change-incident correlation
curl -X POST http://localhost:8000/api/v1/ml/change-incident-correlation \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2024-9876",
    "time_window_hours": 24
  }'
```

---

## Next Steps

1. **Review Research**: Read [SRE_ML_ENHANCEMENTS_RESEARCH.md](./SRE_ML_ENHANCEMENTS_RESEARCH.md)
2. **Start Implementation**: Begin with Change Risk Prediction (Week 1-4)
3. **Gather Feedback**: Deploy to test environment and collect SRE feedback
4. **Iterate**: Improve models based on actual usage data
5. **Scale**: Roll out additional features in phases

---

## Support

For questions or issues:
- Review the full research document
- Check existing ML prediction implementation in `src/topdeck/analysis/prediction/`
- Refer to change management code in `src/topdeck/change_management/`

**Remember**: Start small, measure everything, iterate based on feedback.
