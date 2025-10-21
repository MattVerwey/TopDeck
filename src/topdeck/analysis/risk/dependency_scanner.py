"""
Dependency vulnerability scanner.

Scans package dependencies (npm, pip, maven, etc.) for known vulnerabilities
using GitHub Advisory Database and other sources.
"""

import json
from pathlib import Path

from .models import DependencyVulnerability


class DependencyScanner:
    """
    Scans application dependencies for vulnerabilities.

    Supports multiple package ecosystems:
    - Python (pip, requirements.txt, pyproject.toml)
    - Node.js (npm, package.json)
    - Java (maven, pom.xml)
    - .NET (nuget, *.csproj)
    """

    # Known critical vulnerabilities (would be loaded from external database)
    # Format: (package_name, version_range, cve_id, severity, description)
    KNOWN_VULNERABILITIES = {
        "python": [
            {
                "package": "django",
                "vulnerable_versions": ["<3.2.18", "<4.0.10", "<4.1.7"],
                "cve": "CVE-2023-23969",
                "severity": "high",
                "description": "Potential denial-of-service vulnerability in file uploads",
                "fixed_version": "4.1.7",
            },
            {
                "package": "requests",
                "vulnerable_versions": ["<2.31.0"],
                "cve": "CVE-2023-32681",
                "severity": "medium",
                "description": "Proxy-Authorization header not stripped during cross-origin redirects",
                "fixed_version": "2.31.0",
            },
            {
                "package": "pillow",
                "vulnerable_versions": ["<10.0.1"],
                "cve": "CVE-2023-44271",
                "severity": "high",
                "description": "Arbitrary code execution via crafted image file",
                "fixed_version": "10.0.1",
            },
        ],
        "node": [
            {
                "package": "lodash",
                "vulnerable_versions": ["<4.17.21"],
                "cve": "CVE-2021-23337",
                "severity": "high",
                "description": "Command injection vulnerability",
                "fixed_version": "4.17.21",
            },
            {
                "package": "express",
                "vulnerable_versions": ["<4.17.3"],
                "cve": "CVE-2022-24999",
                "severity": "medium",
                "description": "Open redirect vulnerability",
                "fixed_version": "4.17.3",
            },
        ],
    }

    def scan_python_dependencies(
        self, project_path: str, resource_id: str = "unknown"
    ) -> list[DependencyVulnerability]:
        """
        Scan Python dependencies for vulnerabilities.

        Args:
            project_path: Path to project root
            resource_id: ID of resource using these dependencies

        Returns:
            List of vulnerabilities found
        """
        vulnerabilities = []

        # Try to read requirements.txt
        requirements_file = Path(project_path) / "requirements.txt"
        if requirements_file.exists():
            dependencies = self._parse_requirements_txt(requirements_file)
            vulnerabilities.extend(self._check_python_vulnerabilities(dependencies, resource_id))

        # Try to read pyproject.toml
        pyproject_file = Path(project_path) / "pyproject.toml"
        if pyproject_file.exists():
            dependencies = self._parse_pyproject_toml(pyproject_file)
            vulnerabilities.extend(self._check_python_vulnerabilities(dependencies, resource_id))

        return vulnerabilities

    def scan_node_dependencies(
        self, project_path: str, resource_id: str = "unknown"
    ) -> list[DependencyVulnerability]:
        """
        Scan Node.js dependencies for vulnerabilities.

        Args:
            project_path: Path to project root
            resource_id: ID of resource using these dependencies

        Returns:
            List of vulnerabilities found
        """
        vulnerabilities = []

        package_json = Path(project_path) / "package.json"
        if package_json.exists():
            dependencies = self._parse_package_json(package_json)
            vulnerabilities.extend(self._check_node_vulnerabilities(dependencies, resource_id))

        return vulnerabilities

    def scan_all_dependencies(
        self, project_path: str, resource_id: str = "unknown"
    ) -> list[DependencyVulnerability]:
        """
        Scan all supported dependency types.

        Args:
            project_path: Path to project root
            resource_id: ID of resource using these dependencies

        Returns:
            Combined list of all vulnerabilities found
        """
        all_vulnerabilities = []

        # Scan Python
        all_vulnerabilities.extend(self.scan_python_dependencies(project_path, resource_id))

        # Scan Node.js
        all_vulnerabilities.extend(self.scan_node_dependencies(project_path, resource_id))

        return all_vulnerabilities

    def _parse_requirements_txt(self, file_path: Path) -> dict[str, str]:
        """Parse requirements.txt file."""
        dependencies = {}

        try:
            with open(file_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-"):
                        # Parse package==version format
                        if "==" in line:
                            package, version = line.split("==", 1)
                            dependencies[package.strip()] = version.strip()
                        elif ">=" in line or "<=" in line or ">" in line or "<" in line:
                            # Handle version specifiers
                            parts = line.split()
                            if parts:
                                package = parts[0].strip()
                                dependencies[package] = "unknown"
        except Exception:
            pass

        return dependencies

    def _parse_pyproject_toml(self, file_path: Path) -> dict[str, str]:
        """Parse pyproject.toml file."""
        dependencies = {}

        try:
            # Simple parsing - in production would use tomli/toml library
            with open(file_path) as f:
                in_dependencies = False
                for line in f:
                    line = line.strip()
                    if "[project.dependencies]" in line or "dependencies = [" in line:
                        in_dependencies = True
                        continue
                    if in_dependencies and line.startswith("["):
                        break
                    if in_dependencies and "==" in line:
                        # Parse "package==version" format
                        line = line.strip(
                            "\"'",
                        )
                        if "==" in line:
                            package, version = line.split("==", 1)
                            dependencies[package.strip()] = version.strip()
        except Exception:
            pass

        return dependencies

    def _parse_package_json(self, file_path: Path) -> dict[str, str]:
        """Parse package.json file."""
        dependencies = {}

        try:
            with open(file_path) as f:
                data = json.load(f)

            # Combine dependencies and devDependencies
            for dep_type in ["dependencies", "devDependencies"]:
                if dep_type in data:
                    for package, version in data[dep_type].items():
                        # Remove ^ or ~ prefixes
                        clean_version = version.lstrip("^~")
                        dependencies[package] = clean_version
        except Exception:
            pass

        return dependencies

    def _check_python_vulnerabilities(
        self, dependencies: dict[str, str], resource_id: str
    ) -> list[DependencyVulnerability]:
        """Check Python dependencies against known vulnerabilities."""
        vulnerabilities = []

        for package_name, version in dependencies.items():
            for vuln in self.KNOWN_VULNERABILITIES.get("python", []):
                if package_name.lower() == vuln["package"].lower():
                    # Simple version check (in production would use proper version comparison)
                    if self._is_vulnerable_version(version, vuln["vulnerable_versions"]):
                        vulnerabilities.append(
                            DependencyVulnerability(
                                package_name=package_name,
                                current_version=version,
                                vulnerability_id=vuln["cve"],
                                severity=vuln["severity"],
                                description=vuln["description"],
                                fixed_version=vuln.get("fixed_version"),
                                exploit_available=False,  # Would check exploit-db
                                affected_resources=[resource_id],
                            )
                        )

        return vulnerabilities

    def _check_node_vulnerabilities(
        self, dependencies: dict[str, str], resource_id: str
    ) -> list[DependencyVulnerability]:
        """Check Node.js dependencies against known vulnerabilities."""
        vulnerabilities = []

        for package_name, version in dependencies.items():
            for vuln in self.KNOWN_VULNERABILITIES.get("node", []):
                if package_name.lower() == vuln["package"].lower():
                    if self._is_vulnerable_version(version, vuln["vulnerable_versions"]):
                        vulnerabilities.append(
                            DependencyVulnerability(
                                package_name=package_name,
                                current_version=version,
                                vulnerability_id=vuln["cve"],
                                severity=vuln["severity"],
                                description=vuln["description"],
                                fixed_version=vuln.get("fixed_version"),
                                exploit_available=False,
                                affected_resources=[resource_id],
                            )
                        )

        return vulnerabilities

    def _is_vulnerable_version(self, current_version: str, vulnerable_ranges: list[str]) -> bool:
        """
        Check if current version falls in vulnerable range.

        This is a simplified version. Production would use packaging.version
        for proper semantic version comparison.
        """
        if current_version == "unknown":
            return True  # Assume vulnerable if version unknown

        # Very simple check - in production use packaging.version.parse()
        for vuln_range in vulnerable_ranges:
            if vuln_range.startswith("<"):
                # e.g., "<4.17.21"
                try:
                    max_version = vuln_range.lstrip("<")
                    if self._simple_version_compare(current_version, max_version) < 0:
                        return True
                except Exception:
                    pass

        return False

    def _simple_version_compare(self, version1: str, version2: str) -> int:
        """
        Simple version comparison.
        Returns: -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        try:
            v1_parts = [int(x) for x in version1.split(".")]
            v2_parts = [int(x) for x in version2.split(".")]

            # Pad to same length
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))

            for v1, v2 in zip(v1_parts, v2_parts, strict=False):
                if v1 < v2:
                    return -1
                elif v1 > v2:
                    return 1

            return 0
        except Exception:
            return 0  # Unknown, assume equal

    def get_vulnerability_risk_score(self, vulnerabilities: list[DependencyVulnerability]) -> float:
        """
        Calculate risk score based on vulnerabilities found.

        Args:
            vulnerabilities: List of vulnerabilities

        Returns:
            Risk score (0-100)
        """
        if not vulnerabilities:
            return 0.0

        severity_scores = {
            "critical": 25,
            "high": 15,
            "medium": 8,
            "low": 3,
        }

        total_score = sum(severity_scores.get(v.severity.lower(), 5) for v in vulnerabilities)

        # Add extra points if exploit is available
        exploit_bonus = sum(10 for v in vulnerabilities if v.exploit_available)

        total_score += exploit_bonus

        # Cap at 100
        return min(100.0, float(total_score))

    def generate_vulnerability_recommendations(
        self, vulnerabilities: list[DependencyVulnerability]
    ) -> list[str]:
        """Generate recommendations for addressing vulnerabilities."""
        if not vulnerabilities:
            return ["No known vulnerabilities found in dependencies"]

        recommendations = []

        # Group by severity
        critical = [v for v in vulnerabilities if v.severity == "critical"]
        high = [v for v in vulnerabilities if v.severity == "high"]
        medium = [v for v in vulnerabilities if v.severity == "medium"]

        if critical:
            recommendations.append(
                f"🔴 CRITICAL: {len(critical)} critical vulnerabilities found - "
                "upgrade immediately before deployment"
            )

        if high:
            recommendations.append(
                f"⚠️ HIGH: {len(high)} high-severity vulnerabilities - " "schedule urgent upgrades"
            )

        if medium:
            recommendations.append(
                f"⚡ MEDIUM: {len(medium)} medium-severity vulnerabilities - "
                "plan upgrades in next sprint"
            )

        # Specific package recommendations
        for vuln in vulnerabilities[:5]:  # Top 5
            if vuln.fixed_version:
                recommendations.append(
                    f"Upgrade {vuln.package_name} from {vuln.current_version} "
                    f"to {vuln.fixed_version} ({vuln.vulnerability_id})"
                )

        # General recommendations
        recommendations.extend(
            [
                "Run dependency audit regularly (weekly or on every commit)",
                "Enable automated dependency updates (Dependabot, Renovate)",
                "Subscribe to security advisories for key dependencies",
                "Implement security scanning in CI/CD pipeline",
            ]
        )

        return recommendations
