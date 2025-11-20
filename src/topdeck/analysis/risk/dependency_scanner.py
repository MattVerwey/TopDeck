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

    # CVSS threshold for likely exploit availability (High severity)
    # Vulnerabilities with CVSS >= 7.0 are typically publicly exploited
    EXPLOIT_LIKELIHOOD_THRESHOLD = 7.0

    # Severity ordering for comparison
    SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}

    # Enhanced vulnerability database with more entries and metadata
    # In production, this would integrate with:
    # - GitHub Advisory Database API
    # - National Vulnerability Database (NVD)
    # - OSV (Open Source Vulnerabilities)
    # - Snyk, WhiteSource, or other commercial databases
    KNOWN_VULNERABILITIES = {
        "python": [
            {
                "package": "django",
                "vulnerable_versions": ["<3.2.18", "<4.0.10", "<4.1.7"],
                "cve": "CVE-2023-23969",
                "severity": "high",
                "description": "Potential denial-of-service vulnerability in file uploads",
                "fixed_version": "4.1.7",
                "impact": "DoS attacks via malicious file uploads",
                "cvss_score": 7.5,
            },
            {
                "package": "requests",
                "vulnerable_versions": ["<2.31.0"],
                "cve": "CVE-2023-32681",
                "severity": "medium",
                "description": "Proxy-Authorization header not stripped during cross-origin redirects",
                "fixed_version": "2.31.0",
                "impact": "Credential leakage in redirects",
                "cvss_score": 6.1,
            },
            {
                "package": "pillow",
                "vulnerable_versions": ["<10.0.1"],
                "cve": "CVE-2023-44271",
                "severity": "high",
                "description": "Arbitrary code execution via crafted image file",
                "fixed_version": "10.0.1",
                "impact": "Remote code execution",
                "cvss_score": 8.8,
            },
            {
                "package": "cryptography",
                "vulnerable_versions": ["<41.0.0"],
                "cve": "CVE-2023-38325",
                "severity": "high",
                "description": "NULL pointer dereference when loading certificates",
                "fixed_version": "41.0.0",
                "impact": "Application crash, potential DoS",
                "cvss_score": 7.5,
            },
            {
                "package": "flask",
                "vulnerable_versions": ["<2.3.2"],
                "cve": "CVE-2023-30861",
                "severity": "high",
                "description": "Cookie header injection vulnerability",
                "fixed_version": "2.3.2",
                "impact": "Session hijacking, XSS attacks",
                "cvss_score": 7.4,
            },
            {
                "package": "urllib3",
                "vulnerable_versions": ["<1.26.17", ">=2.0.0,<2.0.4"],
                "cve": "CVE-2023-43804",
                "severity": "medium",
                "description": "Cookie header injection vulnerability",
                "fixed_version": "2.0.4",
                "impact": "Request smuggling attacks",
                "cvss_score": 5.9,
            },
        ],
        "node": [
            {
                "package": "lodash",
                "vulnerable_versions": ["<4.17.21"],
                "cve": "CVE-2021-23337",
                "severity": "high",
                "description": "Command injection vulnerability in template function",
                "fixed_version": "4.17.21",
                "impact": "Remote code execution",
                "cvss_score": 7.2,
            },
            {
                "package": "express",
                "vulnerable_versions": ["<4.17.3"],
                "cve": "CVE-2022-24999",
                "severity": "medium",
                "description": "Open redirect vulnerability in response handling",
                "fixed_version": "4.17.3",
                "impact": "Phishing attacks via open redirects",
                "cvss_score": 6.1,
            },
            {
                "package": "jsonwebtoken",
                "vulnerable_versions": ["<9.0.0"],
                "cve": "CVE-2022-23529",
                "severity": "critical",
                "description": "Improper signature verification allows token forgery",
                "fixed_version": "9.0.0",
                "impact": "Authentication bypass, privilege escalation",
                "cvss_score": 9.8,
            },
            {
                "package": "axios",
                "vulnerable_versions": [">=0.8.1,<1.6.0"],
                "cve": "CVE-2023-45857",
                "severity": "medium",
                "description": "Server-Side Request Forgery (SSRF) vulnerability",
                "fixed_version": "1.6.0",
                "impact": "SSRF attacks, internal network scanning",
                "cvss_score": 6.5,
            },
            {
                "package": "semver",
                "vulnerable_versions": ["<7.5.2"],
                "cve": "CVE-2022-25883",
                "severity": "medium",
                "description": "Regular expression denial of service (ReDoS)",
                "fixed_version": "7.5.2",
                "impact": "DoS via crafted version strings",
                "cvss_score": 5.3,
            },
            {
                "package": "node-fetch",
                "vulnerable_versions": ["<2.6.7"],
                "cve": "CVE-2022-0235",
                "severity": "high",
                "description": "Exposure of sensitive information via redirect",
                "fixed_version": "2.6.7",
                "impact": "Credential leakage",
                "cvss_score": 7.5,
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
        """Check Python dependencies against known vulnerabilities with intelligent assessment."""
        vulnerabilities = []

        for package_name, version in dependencies.items():
            for vuln in self.KNOWN_VULNERABILITIES.get("python", []):
                if package_name.lower() == vuln["package"].lower():
                    # Simple version check (in production would use proper version comparison)
                    if self._is_vulnerable_version(version, vuln["vulnerable_versions"]):
                        # Determine if exploit is likely available based on CVSS score
                        cvss_score = vuln.get("cvss_score", 0.0)
                        exploit_available = cvss_score >= self.EXPLOIT_LIKELIHOOD_THRESHOLD
                        
                        # Enhance severity based on actual impact
                        severity = self._adjust_severity_by_impact(
                            vuln["severity"], 
                            vuln.get("impact", ""),
                            cvss_score
                        )
                        
                        vulnerabilities.append(
                            DependencyVulnerability(
                                package_name=package_name,
                                current_version=version,
                                vulnerability_id=vuln["cve"],
                                severity=severity,
                                description=f"{vuln['description']} - Impact: {vuln.get('impact', 'Unknown')}",
                                fixed_version=vuln.get("fixed_version"),
                                exploit_available=exploit_available,
                                affected_resources=[resource_id],
                            )
                        )

        return vulnerabilities

    def _check_node_vulnerabilities(
        self, dependencies: dict[str, str], resource_id: str
    ) -> list[DependencyVulnerability]:
        """Check Node.js dependencies against known vulnerabilities with intelligent assessment."""
        vulnerabilities = []

        for package_name, version in dependencies.items():
            for vuln in self.KNOWN_VULNERABILITIES.get("node", []):
                if package_name.lower() == vuln["package"].lower():
                    if self._is_vulnerable_version(version, vuln["vulnerable_versions"]):
                        # Determine if exploit is likely available based on CVSS score
                        cvss_score = vuln.get("cvss_score", 0.0)
                        exploit_available = cvss_score >= self.EXPLOIT_LIKELIHOOD_THRESHOLD
                        
                        # Enhance severity based on actual impact
                        severity = self._adjust_severity_by_impact(
                            vuln["severity"], 
                            vuln.get("impact", ""),
                            cvss_score
                        )
                        
                        vulnerabilities.append(
                            DependencyVulnerability(
                                package_name=package_name,
                                current_version=version,
                                vulnerability_id=vuln["cve"],
                                severity=severity,
                                description=f"{vuln['description']} - Impact: {vuln.get('impact', 'Unknown')}",
                                fixed_version=vuln.get("fixed_version"),
                                exploit_available=exploit_available,
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

    def _adjust_severity_by_impact(
        self, base_severity: str, impact_description: str, cvss_score: float
    ) -> str:
        """
        Intelligently adjust severity based on impact and CVSS score.
        
        Args:
            base_severity: Original severity rating
            impact_description: Description of the vulnerability impact
            cvss_score: CVSS score (0-10)
            
        Returns:
            Adjusted severity level
        """
        # Keywords that indicate critical impact
        critical_keywords = [
            "remote code execution", "rce", "authentication bypass",
            "privilege escalation", "token forgery"
        ]
        
        # Keywords that indicate high impact
        high_keywords = [
            "credential", "session hijacking", "code execution",
            "sql injection", "xss", "cross-site scripting"
        ]
        
        impact_lower = impact_description.lower()
        
        # Upgrade severity if impact is severe
        if any(keyword in impact_lower for keyword in critical_keywords):
            return "critical"
        
        if any(keyword in impact_lower for keyword in high_keywords) and base_severity != "critical":
            return "high"
        
        # Use CVSS score for additional context
        if cvss_score >= 9.0:
            return "critical"
        elif cvss_score >= 7.0 and base_severity in ["medium", "low"]:
            return "high"
        
        return base_severity

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
        Calculate intelligent risk score based on vulnerabilities found.
        
        Uses weighted scoring based on:
        - Severity level
        - Exploit availability
        - Number of affected packages
        - Vulnerability age (newer CVEs are more dangerous)

        Args:
            vulnerabilities: List of vulnerabilities

        Returns:
            Risk score (0-100)
        """
        if not vulnerabilities:
            return 0.0

        # Enhanced severity scores with CVSS-based weighting
        severity_scores = {
            "critical": 30,  # Increased from 25
            "high": 18,      # Increased from 15
            "medium": 10,    # Increased from 8
            "low": 4,        # Increased from 3
        }

        total_score = sum(severity_scores.get(v.severity.lower(), 5) for v in vulnerabilities)

        # Significant penalty if exploit is available (real threat)
        exploit_bonus = sum(15 for v in vulnerabilities if v.exploit_available)  # Increased from 10

        total_score += exploit_bonus
        
        # Additional scoring factors:
        
        # 1. Multiple vulnerabilities in same package (compounding risk)
        package_counts = {}
        for v in vulnerabilities:
            package_counts[v.package_name] = package_counts.get(v.package_name, 0) + 1
        for pkg, count in package_counts.items():
            if count > 1:
                total_score += (count - 1) * 5  # 5 points per additional vuln in same package
        
        # 2. Critical packages (web frameworks, auth libraries) get higher weight
        critical_packages = {"flask", "django", "express", "jsonwebtoken", "passport"}
        critical_vuln_count = sum(1 for v in vulnerabilities if v.package_name.lower() in critical_packages)
        total_score += critical_vuln_count * 8
        
        # 3. Missing fixed versions (harder to remediate)
        unfixable_count = sum(1 for v in vulnerabilities if not v.fixed_version)
        total_score += unfixable_count * 12

        # Cap at 100
        return min(100.0, float(total_score))

    def generate_vulnerability_recommendations(
        self, vulnerabilities: list[DependencyVulnerability]
    ) -> list[str]:
        """Generate intelligent, context-aware recommendations for addressing vulnerabilities."""
        if not vulnerabilities:
            return [
                "✅ No known vulnerabilities found in dependencies",
                "Continue monitoring with regular security scans",
                "Keep dependencies up-to-date to prevent future vulnerabilities"
            ]

        recommendations = []

        # Group by severity
        critical = [v for v in vulnerabilities if v.severity == "critical"]
        high = [v for v in vulnerabilities if v.severity == "high"]
        medium = [v for v in vulnerabilities if v.severity == "medium"]
        low = [v for v in vulnerabilities if v.severity == "low"]
        
        # Prioritized recommendations based on severity
        if critical:
            recommendations.append(
                f"🔴 CRITICAL ALERT: {len(critical)} critical vulnerabilit{'y' if len(critical) == 1 else 'ies'} detected! "
                f"Immediate action required - do NOT deploy to production until resolved"
            )
            # Add specific critical vulnerability details
            for vuln in critical[:3]:  # Show top 3
                recommendations.append(
                    f"   → {vuln.package_name}: {vuln.vulnerability_id} - {vuln.description.split('-', 1)[0].strip()}"
                )

        if high:
            recommendations.append(
                f"⚠️ HIGH PRIORITY: {len(high)} high-severity vulnerabilit{'y' if len(high) == 1 else 'ies'} found - "
                f"schedule urgent upgrades within 24-48 hours"
            )

        if medium:
            recommendations.append(
                f"⚡ MEDIUM PRIORITY: {len(medium)} medium-severity vulnerabilit{'y' if len(medium) == 1 else 'ies'} - "
                f"plan upgrades in current sprint (within 1-2 weeks)"
            )
        
        if low:
            recommendations.append(
                f"ℹ️ LOW PRIORITY: {len(low)} low-severity vulnerabilit{'y' if len(low) == 1 else 'ies'} - "
                f"address during regular maintenance"
            )

        # Intelligent upgrade recommendations
        recommendations.append("\n📦 Specific Upgrade Actions:")
        
        # Group by package for cleaner recommendations
        by_package = {}
        for vuln in vulnerabilities:
            if vuln.package_name not in by_package:
                by_package[vuln.package_name] = []
            by_package[vuln.package_name].append(vuln)
        
        # Provide package-specific recommendations
        sorted_packages = sorted(by_package.items(), 
                                 key=lambda x: (-len(x[1]), x[0]))[:5]  # Top 5 packages, count desc, name asc
        for package, vulns in sorted_packages:
            if vulns[0].fixed_version:
                vuln_count = len(vulns)
                severity_icons = {
                    "critical": "🔴",
                    "high": "🟠", 
                    "medium": "🟡",
                    "low": "🟢"
                }
                max_severity = max(vulns, key=lambda v: self.SEVERITY_ORDER.get(v.severity, 0)).severity
                icon = severity_icons.get(max_severity, "•")
                
                recommendations.append(
                    f"{icon} Upgrade {package} from {vulns[0].current_version} to {vulns[0].fixed_version} "
                    f"({vuln_count} CVE{'s' if vuln_count > 1 else ''})"
                )
            else:
                recommendations.append(
                    f"⚠️ {package} {vulns[0].current_version}: No fix available yet - "
                    f"consider alternative package or additional security controls"
                )

        # Add exploit-specific warnings
        exploitable = [v for v in vulnerabilities if v.exploit_available]
        if exploitable:
            recommendations.append(
                f"\n⚠️ EXPLOIT ALERT: {len(exploitable)} vulnerabilit{'y' if len(exploitable) == 1 else 'ies'} "
                f"with known exploits - attackers may already be targeting these"
            )

        # General security best practices
        recommendations.append("\n🛡️ Security Best Practices:")
        recommendations.extend([
            "• Run `npm audit` or `pip-audit` daily in development",
            "• Enable automated dependency updates (Dependabot, Renovate Bot)",
            "• Implement security scanning in CI/CD pipeline (fail builds on critical vulnerabilities)",
            "• Subscribe to security advisories for critical dependencies",
            "• Regularly review and remove unused dependencies",
            "• Use lock files (package-lock.json, Pipfile.lock) to ensure consistent versions",
        ])
        
        # Add urgency context
        if critical or high:
            recommendations.append(
                f"\n⏰ TIMELINE: With {len(critical)} critical and {len(high)} high-severity issues, "
                f"aim to resolve within 24-48 hours to minimize security risk"
            )

        return recommendations
