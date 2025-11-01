# Changelog

All notable changes to TopDeck will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Change Management Features (2024-11-01)
- **Change Request Tracking**: Full lifecycle management from draft to completion
- **Impact Assessment**: Automated blast radius calculation and risk scoring
- **Change Calendar**: View and manage scheduled changes
- **ServiceNow Integration**: Webhook receiver for change request sync
- **Jira Integration**: Webhook receiver for issue/change ticket sync
- **Approval Workflows**: Risk-based approval routing with multiple approvers
- **Change Metrics**: KPI tracking, success rates, and trend analysis
- **API Endpoints**: 
  - `POST /api/v1/changes` - Create change request
  - `POST /api/v1/changes/{id}/assess` - Assess impact
  - `GET /api/v1/changes/calendar` - View scheduled changes
  - `GET /api/v1/changes/metrics` - Get metrics and trends
  - `POST /api/v1/changes/{id}/approve` - Approve change
  - `POST /api/v1/changes/{id}/reject` - Reject change
  - `POST /api/v1/webhooks/servicenow` - ServiceNow webhook
  - `POST /api/v1/webhooks/jira` - Jira webhook
- **Frontend Enhancement**: Connected Change Impact page to real API
- **Documentation**: Comprehensive Change Management Guide and Quick Reference

### Added - Initial Release
- Initial project structure
- Comprehensive README with architecture overview
- Documentation structure (architecture, user guide, issues)
- GitHub issue templates (bug report, feature request, documentation)
- Contributing guidelines
- MIT License
- Docker Compose setup for development environment
- Environment configuration template (.env.example)
- Getting Started guide
- 7 detailed initial development issues

### Changed
- Enhanced Change Impact Analysis page to use real backend APIs
- Updated README with change management capabilities
- Improved API client with change management methods

### Deprecated
- Nothing yet

### Removed
- Nothing yet

### Fixed
- Nothing yet

### Security
- Nothing yet

---

## Version History

### [0.1.0] - TBD - Initial Release

First public release of TopDeck.

**Phase 1: Foundation**
- Technology stack selection
- Core data models
- Development environment setup

**Phase 2: Platform Integrations**
- Azure DevOps integration
- GitHub integration
- Deployment tracking and linking
- Topology visualization dashboard

**Phase 3: Analysis & Intelligence**
- Risk analysis engine
- Dependency graph builder
- Impact assessment
- Performance monitoring integration
- Error correlation

**Phase 4: Multi-Cloud Architecture**
- AWS resource discovery
- GCP resource discovery
- Multi-cloud abstraction layer
- Infrastructure deployment automation

---

## Release Notes Template

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing features

### Deprecated
- Features marked for removal

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security updates
```

---

## Contribution Guidelines

When adding to the changelog:

1. Add entries under the `[Unreleased]` section
2. Categorize changes appropriately
3. Include issue/PR references: `(#123)`
4. Use clear, concise descriptions
5. When releasing, move unreleased items to a new version section

Example:
```markdown
### Added
- Azure AKS cluster discovery (#42)
- Risk scoring algorithm (#45)
```
