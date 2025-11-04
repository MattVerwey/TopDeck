#!/usr/bin/env python3
"""
Demonstration of misconfiguration detection in risk analysis.

This script shows how the new misconfiguration detector identifies
infrastructure issues like missing availability zones, no backups,
no firewall rules, etc.
"""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from topdeck.analysis.risk.misconfiguration import MisconfigurationDetector


def demonstrate_misconfiguration_detection():
    """
    Demonstrate misconfiguration detection on various resource types.
    """
    detector = MisconfigurationDetector()
    
    print("=" * 80)
    print("Misconfiguration Detection Demonstration")
    print("=" * 80)
    print()
    
    # Example 1: Database with no backups or replication
    print("Example 1: Database with Multiple Misconfigurations")
    print("-" * 80)
    
    db_properties = {
        "name": "production-db",
        "resource_type": "database",
        "region": "eastus",
        # Missing: backup_enabled, replication_enabled, availability_zones
        # Missing: firewall_rules, encryption_enabled
    }
    
    db_report = detector.detect_misconfigurations(
        resource_id="db-001",
        resource_name="production-db",
        resource_type="database",
        properties=db_properties,
    )
    
    print(f"Resource: {db_report.resource_name} ({db_report.resource_type})")
    print(f"Issues Found: {len(db_report.issues)}")
    print(f"Risk Score Impact: +{db_report.risk_score_impact:.1f} points")
    print()
    print("Severity Breakdown:")
    for severity, count in db_report.severity_counts.items():
        if count > 0:
            print(f"  {severity.upper()}: {count}")
    print()
    print("Issues Detected:")
    for i, issue in enumerate(db_report.issues, 1):
        print(f"\n  {i}. {issue.title} [{issue.severity.upper()}]")
        print(f"     {issue.description}")
        print(f"     Fix: {issue.recommendation}")
    print()
    
    # Example 2: Well-configured database
    print("\nExample 2: Well-Configured Database")
    print("-" * 80)
    
    good_db_properties = {
        "name": "production-db-secure",
        "resource_type": "database",
        "region": "eastus",
        "backup_enabled": True,
        "backup_retention_days": 30,
        "replication_enabled": True,
        "geo_redundant": "GRS",
        "availability_zones": ["1", "2", "3"],
        "firewall_rules": [
            {"name": "AllowApp", "start_ip": "10.0.0.0", "end_ip": "10.0.255.255"}
        ],
        "encryption_enabled": True,
        "monitoring_enabled": True,
    }
    
    good_db_report = detector.detect_misconfigurations(
        resource_id="db-002",
        resource_name="production-db-secure",
        resource_type="database",
        properties=good_db_properties,
    )
    
    print(f"Resource: {good_db_report.resource_name} ({good_db_report.resource_type})")
    print(f"Issues Found: {len(good_db_report.issues)}")
    print(f"Risk Score Impact: +{good_db_report.risk_score_impact:.1f} points")
    if len(good_db_report.issues) == 0:
        print("✅ No misconfigurations detected! This is a well-configured resource.")
    else:
        print("\nMinor issues:")
        for issue in good_db_report.issues:
            print(f"  - {issue.title} [{issue.severity.upper()}]")
    print()
    
    # Example 3: Web app with no firewall
    print("\nExample 3: Web Application Without Firewall")
    print("-" * 80)
    
    webapp_properties = {
        "name": "api-service",
        "resource_type": "web_app",
        "region": "westus",
        "monitoring_enabled": True,
        # Missing: firewall_rules, network_security_group
    }
    
    webapp_report = detector.detect_misconfigurations(
        resource_id="app-001",
        resource_name="api-service",
        resource_type="web_app",
        properties=webapp_properties,
    )
    
    print(f"Resource: {webapp_report.resource_name} ({webapp_report.resource_type})")
    print(f"Issues Found: {len(webapp_report.issues)}")
    print(f"Risk Score Impact: +{webapp_report.risk_score_impact:.1f} points")
    print()
    for issue in webapp_report.issues:
        print(f"  ⚠️  {issue.title} [{issue.severity.upper()}]")
        print(f"      {issue.description}")
    print()
    
    # Example 4: Storage account without encryption
    print("\nExample 4: Storage Account Without Encryption")
    print("-" * 80)
    
    storage_properties = {
        "name": "company-storage",
        "resource_type": "storage_account",
        "region": "centralus",
        "backup_enabled": True,
        "firewall_rules": ["10.0.0.0/16"],
        # Missing: encryption_enabled, replication
    }
    
    storage_report = detector.detect_misconfigurations(
        resource_id="stor-001",
        resource_name="company-storage",
        resource_type="storage_account",
        properties=storage_properties,
    )
    
    print(f"Resource: {storage_report.resource_name} ({storage_report.resource_type})")
    print(f"Issues Found: {len(storage_report.issues)}")
    print(f"Risk Score Impact: +{storage_report.risk_score_impact:.1f} points")
    print()
    for issue in storage_report.issues:
        severity_icon = "🔴" if issue.severity == "critical" else "🟡" if issue.severity == "high" else "🟢"
        print(f"  {severity_icon} {issue.title} [{issue.severity.upper()}]")
        print(f"      Recommendation: {issue.recommendation}")
    print()
    
    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("The misconfiguration detector identifies:")
    print("  • Missing availability zones (high risk)")
    print("  • No replication configured (high risk)")
    print("  • Missing backups (critical risk)")
    print("  • No firewall rules (critical risk)")
    print("  • Encryption not enabled (high risk)")
    print("  • No redundancy (medium risk)")
    print("  • Monitoring not configured (medium risk)")
    print()
    print("Each misconfiguration adds to the resource's risk score:")
    print("  • Critical issues: +25 points")
    print("  • High issues: +15 points")
    print("  • Medium issues: +8 points")
    print("  • Low issues: +3 points")
    print()
    print("Impact on Risk Score Examples:")
    print(f"  • Database with 5 issues: +{db_report.risk_score_impact:.1f} points")
    print(f"  • Well-configured database: +{good_db_report.risk_score_impact:.1f} points")
    print(f"  • Web app with firewall issue: +{webapp_report.risk_score_impact:.1f} points")
    print(f"  • Storage without encryption: +{storage_report.risk_score_impact:.1f} points")
    print()
    print("This ensures that resources show DIFFERENT vulnerabilities based on")
    print("their actual configuration, not just generic demo data!")
    print()


if __name__ == "__main__":
    demonstrate_misconfiguration_detection()
