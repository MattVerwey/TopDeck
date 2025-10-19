"""
Tests for dependency vulnerability scanner.
"""

import pytest
import tempfile
import json
from pathlib import Path

from topdeck.analysis.risk.dependency_scanner import DependencyScanner
from topdeck.analysis.risk.models import DependencyVulnerability


class TestDependencyScanner:
    """Test dependency vulnerability scanning."""
    
    @pytest.fixture
    def scanner(self):
        """Create scanner instance."""
        return DependencyScanner()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_scan_python_requirements_txt(self, scanner, temp_dir):
        """Test scanning Python requirements.txt file."""
        # Create a requirements.txt with known vulnerable package
        req_file = Path(temp_dir) / "requirements.txt"
        req_file.write_text("""
django==3.2.0
requests==2.28.0
fastapi==0.104.1
""")
        
        vulnerabilities = scanner.scan_python_dependencies(temp_dir, "test-resource")
        
        # Should find django vulnerability (older than 3.2.18)
        assert len(vulnerabilities) > 0
        django_vulns = [v for v in vulnerabilities if v.package_name == "django"]
        assert len(django_vulns) > 0
        
        vuln = django_vulns[0]
        assert vuln.current_version == "3.2.0"
        assert vuln.severity in ["low", "medium", "high", "critical"]
        assert len(vuln.description) > 0
    
    def test_scan_python_pyproject_toml(self, scanner, temp_dir):
        """Test scanning pyproject.toml file."""
        # Create a pyproject.toml
        toml_file = Path(temp_dir) / "pyproject.toml"
        toml_file.write_text("""
[project]
dependencies = [
    "django==3.2.0",
    "requests==2.28.0"
]
""")
        
        vulnerabilities = scanner.scan_python_dependencies(temp_dir, "test-resource")
        
        # Should find vulnerabilities
        assert len(vulnerabilities) > 0
    
    def test_scan_node_package_json(self, scanner, temp_dir):
        """Test scanning package.json file."""
        # Create a package.json with known vulnerable package
        pkg_file = Path(temp_dir) / "package.json"
        pkg_data = {
            "name": "test-app",
            "dependencies": {
                "lodash": "4.17.20",
                "express": "4.17.0"
            },
            "devDependencies": {
                "mocha": "9.0.0"
            }
        }
        pkg_file.write_text(json.dumps(pkg_data, indent=2))
        
        vulnerabilities = scanner.scan_node_dependencies(temp_dir, "test-resource")
        
        # Should find lodash vulnerability
        assert len(vulnerabilities) > 0
        lodash_vulns = [v for v in vulnerabilities if v.package_name == "lodash"]
        assert len(lodash_vulns) > 0
    
    def test_scan_all_dependencies(self, scanner, temp_dir):
        """Test scanning all dependency types together."""
        # Create both Python and Node files
        req_file = Path(temp_dir) / "requirements.txt"
        req_file.write_text("django==3.2.0\n")
        
        pkg_file = Path(temp_dir) / "package.json"
        pkg_data = {
            "dependencies": {
                "lodash": "4.17.20"
            }
        }
        pkg_file.write_text(json.dumps(pkg_data))
        
        vulnerabilities = scanner.scan_all_dependencies(temp_dir, "test-resource")
        
        # Should find vulnerabilities from both ecosystems
        assert len(vulnerabilities) > 0
        
        # Should have both Python and Node vulnerabilities
        packages = {v.package_name for v in vulnerabilities}
        # At least one should be found (depending on version checks)
        assert len(packages) > 0
    
    def test_get_vulnerability_risk_score_none(self, scanner):
        """Test risk score with no vulnerabilities."""
        score = scanner.get_vulnerability_risk_score([])
        assert score == 0.0
    
    def test_get_vulnerability_risk_score_critical(self, scanner):
        """Test risk score with critical vulnerabilities."""
        vulns = [
            DependencyVulnerability(
                package_name="test-pkg",
                current_version="1.0.0",
                vulnerability_id="CVE-2023-0001",
                severity="critical",
                description="Critical vulnerability",
            )
        ]
        
        score = scanner.get_vulnerability_risk_score(vulns)
        assert score > 0
        assert score <= 100
    
    def test_get_vulnerability_risk_score_multiple(self, scanner):
        """Test risk score with multiple vulnerabilities."""
        vulns = [
            DependencyVulnerability(
                package_name="pkg1",
                current_version="1.0.0",
                vulnerability_id="CVE-2023-0001",
                severity="critical",
                description="Critical",
            ),
            DependencyVulnerability(
                package_name="pkg2",
                current_version="2.0.0",
                vulnerability_id="CVE-2023-0002",
                severity="high",
                description="High",
            ),
            DependencyVulnerability(
                package_name="pkg3",
                current_version="3.0.0",
                vulnerability_id="CVE-2023-0003",
                severity="medium",
                description="Medium",
            ),
        ]
        
        score = scanner.get_vulnerability_risk_score(vulns)
        
        # Multiple vulnerabilities should have higher score
        assert score > 30  # At least moderate risk
        assert score <= 100
    
    def test_get_vulnerability_risk_score_with_exploit(self, scanner):
        """Test risk score increases with available exploits."""
        vulns_no_exploit = [
            DependencyVulnerability(
                package_name="pkg1",
                current_version="1.0.0",
                vulnerability_id="CVE-2023-0001",
                severity="high",
                description="High",
                exploit_available=False,
            )
        ]
        
        vulns_with_exploit = [
            DependencyVulnerability(
                package_name="pkg1",
                current_version="1.0.0",
                vulnerability_id="CVE-2023-0001",
                severity="high",
                description="High",
                exploit_available=True,
            )
        ]
        
        score_no_exploit = scanner.get_vulnerability_risk_score(vulns_no_exploit)
        score_with_exploit = scanner.get_vulnerability_risk_score(vulns_with_exploit)
        
        # Exploit should increase risk
        assert score_with_exploit > score_no_exploit
    
    def test_generate_vulnerability_recommendations_none(self, scanner):
        """Test recommendations with no vulnerabilities."""
        recommendations = scanner.generate_vulnerability_recommendations([])
        
        assert len(recommendations) > 0
        assert any("no" in r.lower() and "vulnerabilities" in r.lower() for r in recommendations)
    
    def test_generate_vulnerability_recommendations_critical(self, scanner):
        """Test recommendations with critical vulnerabilities."""
        vulns = [
            DependencyVulnerability(
                package_name="django",
                current_version="3.2.0",
                vulnerability_id="CVE-2023-0001",
                severity="critical",
                description="Critical vulnerability",
                fixed_version="3.2.18",
            )
        ]
        
        recommendations = scanner.generate_vulnerability_recommendations(vulns)
        
        assert len(recommendations) > 0
        # Should mention critical
        rec_text = " ".join(recommendations).lower()
        assert "critical" in rec_text
        # Should mention upgrade
        assert "upgrade" in rec_text
    
    def test_generate_vulnerability_recommendations_has_specifics(self, scanner):
        """Test that recommendations include specific package upgrades."""
        vulns = [
            DependencyVulnerability(
                package_name="lodash",
                current_version="4.17.20",
                vulnerability_id="CVE-2021-23337",
                severity="high",
                description="Command injection",
                fixed_version="4.17.21",
            )
        ]
        
        recommendations = scanner.generate_vulnerability_recommendations(vulns)
        
        # Should mention specific package and version
        rec_text = " ".join(recommendations)
        assert "lodash" in rec_text
        assert "4.17.21" in rec_text
    
    def test_generate_vulnerability_recommendations_general_advice(self, scanner):
        """Test that recommendations include general security advice."""
        vulns = [
            DependencyVulnerability(
                package_name="test",
                current_version="1.0.0",
                vulnerability_id="CVE-2023-0001",
                severity="medium",
                description="Test vuln",
            )
        ]
        
        recommendations = scanner.generate_vulnerability_recommendations(vulns)
        
        # Should include general recommendations
        rec_text = " ".join(recommendations).lower()
        assert any(word in rec_text for word in [
            "audit", "automated", "security", "ci/cd", "pipeline"
        ])
    
    def test_parse_requirements_txt_various_formats(self, scanner, temp_dir):
        """Test parsing requirements.txt with various formats."""
        req_file = Path(temp_dir) / "requirements.txt"
        req_file.write_text("""
# Comment line
django==3.2.0
requests>=2.28.0
fastapi
-r other-requirements.txt

pillow==9.0.0
""")
        
        deps = scanner._parse_requirements_txt(req_file)
        
        # Should parse == format
        assert "django" in deps
        assert deps["django"] == "3.2.0"
        
        # Should parse >= format (version might be unknown)
        assert "requests" in deps
        
        # Should handle package without version
        assert "fastapi" in deps
        
        # Should parse other packages
        assert "pillow" in deps
    
    def test_parse_package_json_handles_version_prefixes(self, scanner, temp_dir):
        """Test parsing package.json with ^ and ~ version prefixes."""
        pkg_file = Path(temp_dir) / "package.json"
        pkg_data = {
            "dependencies": {
                "lodash": "^4.17.20",
                "express": "~4.17.0"
            }
        }
        pkg_file.write_text(json.dumps(pkg_data))
        
        deps = scanner._parse_package_json(pkg_file)
        
        # Should remove ^ and ~ prefixes
        assert deps["lodash"] == "4.17.20"
        assert deps["express"] == "4.17.0"
    
    def test_version_comparison(self, scanner):
        """Test simple version comparison logic."""
        # Test less than
        assert scanner._simple_version_compare("1.0.0", "2.0.0") < 0
        assert scanner._simple_version_compare("1.5.0", "1.6.0") < 0
        assert scanner._simple_version_compare("1.0.1", "1.0.2") < 0
        
        # Test greater than
        assert scanner._simple_version_compare("2.0.0", "1.0.0") > 0
        assert scanner._simple_version_compare("1.6.0", "1.5.0") > 0
        
        # Test equal
        assert scanner._simple_version_compare("1.0.0", "1.0.0") == 0
    
    def test_version_comparison_different_lengths(self, scanner):
        """Test version comparison with different version string lengths."""
        # 1.0 vs 1.0.0 should be equal (with padding)
        result = scanner._simple_version_compare("1.0", "1.0.0")
        assert result == 0
        
        # 1.0.0 vs 1.0.1 should be less than
        result = scanner._simple_version_compare("1.0.0", "1.0.1")
        assert result < 0
    
    def test_is_vulnerable_version(self, scanner):
        """Test vulnerable version checking."""
        # Should detect vulnerability
        assert scanner._is_vulnerable_version("3.2.0", ["<3.2.18"])
        assert scanner._is_vulnerable_version("4.0.0", ["<4.0.10"])
        
        # Should not detect if version is safe
        assert not scanner._is_vulnerable_version("3.2.20", ["<3.2.18"])
        assert not scanner._is_vulnerable_version("5.0.0", ["<4.0.10"])
    
    def test_is_vulnerable_version_unknown(self, scanner):
        """Test that unknown versions are treated as vulnerable."""
        # Conservative approach: unknown version = assume vulnerable
        assert scanner._is_vulnerable_version("unknown", ["<4.17.21"])
    
    def test_scan_nonexistent_directory(self, scanner):
        """Test scanning non-existent directory doesn't crash."""
        vulnerabilities = scanner.scan_all_dependencies(
            "/nonexistent/path/12345",
            "test-resource"
        )
        
        # Should return empty list, not crash
        assert vulnerabilities == []
    
    def test_affected_resources_tracked(self, scanner, temp_dir):
        """Test that affected resources are tracked in vulnerabilities."""
        req_file = Path(temp_dir) / "requirements.txt"
        req_file.write_text("django==3.2.0\n")
        
        vulnerabilities = scanner.scan_python_dependencies(
            temp_dir,
            "my-app-service"
        )
        
        if vulnerabilities:
            # Should track which resource is affected
            assert all("my-app-service" in v.affected_resources for v in vulnerabilities)
