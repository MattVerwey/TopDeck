"""
Risk Analysis Engine for TopDeck.

Provides risk assessment, impact analysis, and failure simulation
for infrastructure resources.
"""

from .analyzer import RiskAnalyzer
from .cost_impact import CostImpact, CostImpactAnalyzer
from .dependency import DependencyAnalyzer
from .dependency_scanner import DependencyScanner
from .impact import ImpactAnalyzer
from .models import (
    BlastRadius,
    DependencyVulnerability,
    FailureOutcome,
    FailureSimulation,
    FailureType,
    ImpactLevel,
    OutcomeType,
    PartialFailureScenario,
    RiskAssessment,
    RiskLevel,
    SinglePointOfFailure,
)
from .partial_failure import PartialFailureAnalyzer
from .scoring import RiskScorer
from .simulation import FailureSimulator
from .time_aware_scoring import TimeAwareRiskScorer, adjust_risk_score_for_timing
from .trend_analysis import RiskSnapshot, RiskTrend, RiskTrendAnalyzer

__all__ = [
    "RiskAnalyzer",
    "RiskAssessment",
    "BlastRadius",
    "FailureSimulation",
    "SinglePointOfFailure",
    "RiskLevel",
    "ImpactLevel",
    "FailureType",
    "OutcomeType",
    "FailureOutcome",
    "PartialFailureScenario",
    "DependencyVulnerability",
    "RiskScorer",
    "DependencyAnalyzer",
    "ImpactAnalyzer",
    "FailureSimulator",
    "PartialFailureAnalyzer",
    "DependencyScanner",
    "CostImpact",
    "CostImpactAnalyzer",
    "TimeAwareRiskScorer",
    "adjust_risk_score_for_timing",
    "RiskSnapshot",
    "RiskTrend",
    "RiskTrendAnalyzer",
]
