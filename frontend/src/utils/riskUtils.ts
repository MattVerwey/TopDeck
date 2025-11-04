/**
 * Risk utility functions
 * 
 * Shared utilities for risk analysis and calculations
 */

/**
 * Get risk level from a numeric risk score
 * @param score Risk score (0-100)
 * @returns Risk level string
 * 
 * Note: These thresholds match the backend RiskScorer thresholds in scoring.py
 */
export function getRiskLevelFromScore(score: number): string {
  if (score >= 75) return 'critical';
  if (score >= 50) return 'high';
  if (score >= 25) return 'medium';
  return 'low';
}

/**
 * Get color code for risk level
 * @param level Risk level
 * @returns Color code
 */
export function getRiskColor(level: string): 'error' | 'warning' | 'info' | 'success' {
  switch (level) {
    case 'critical':
      return 'error';
    case 'high':
      return 'warning';
    case 'medium':
      return 'info';
    default:
      return 'success';
  }
}

/**
 * Get impact level color
 * @param impactLevel Impact level (critical, high, medium, low)
 * @returns MUI color name
 */
export function getImpactColor(impactLevel: string): 'error' | 'warning' | 'info' | 'success' {
  switch (impactLevel) {
    case 'critical':
      return 'error';
    case 'high':
      return 'warning';
    case 'medium':
      return 'info';
    default:
      return 'success';
  }
}
