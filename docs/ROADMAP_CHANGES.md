# Roadmap Changes - October 2025

## Summary

The development roadmap has been reorganized to better reflect the architectural approach and prioritize multi-cloud support using Terraform.

## What Changed

### Previous Structure

**Phase 2** (Months 3-4) was originally:
- Discovery & Integration
  - Implement AWS and GCP resource discovery
  - Build Azure DevOps pipeline integration
  - Add GitHub repository integration
  - Create basic topology visualization

### New Structure

**Phase 2** (Months 3-4) is now focused on:
- **Platform Integrations**
  - Build Azure DevOps pipeline integration
  - Add GitHub Actions and repository integration
  - Implement deployment tracking and linking
  - Create basic topology visualization

**Phase 3** (Months 5-6) now includes:
- **Analysis & Intelligence**
  - Develop dependency graph builder
  - Implement risk analysis engine
  - Build change impact assessment
  - Integrate performance metrics and monitoring
  - Add error correlation and alerting

**Phase 4** (Months 7-8) has been consolidated to:
- **Multi-Cloud Architecture**
  - Architect and implement AWS resource discovery using Terraform
  - Architect and implement GCP resource discovery using Terraform
  - Build unified multi-cloud resource abstraction layer
  - Create infrastructure deployment automation

## Rationale

### Why This Change Makes Sense

1. **Core Functionality First**: By focusing on Platform Integrations in Phase 2, we get core functionality working earlier with Azure DevOps and GitHub integrations. This allows teams to start using the platform sooner.

2. **Build on Foundation**: Analysis & Intelligence in Phase 3 builds directly on the integrations from Phase 2, providing immediate value with risk analysis and monitoring for the existing Azure infrastructure.

3. **Multi-Cloud Expansion**: Once core functionality is proven with Azure, Platform Integrations, and Analysis features, Phase 4 extends the architecture to AWS and GCP using Terraform patterns established in Phase 1.

4. **Better Separation of Concerns**:
   - Phase 1: Foundation (Azure only)
   - Phase 2: Platform integrations and linking
   - Phase 3: Analysis and intelligence features
   - Phase 4: Multi-cloud infrastructure expansion

## New Issues Created

Three new issues have been created to support the reorganized roadmap:

### Issue #8: AWS Resource Discovery
- Implement AWS resource discovery (EKS, EC2, Lambda, RDS, etc.)
- Terraform integration for AWS infrastructure
- Multi-region and multi-account support
- Consistent interface with Azure discovery

### Issue #9: GCP Resource Discovery
- Implement GCP resource discovery (GKE, Compute Engine, Cloud Run, Cloud SQL, etc.)
- Terraform integration for GCP infrastructure
- Multi-region and multi-project support
- Consistent interface with Azure and AWS discovery

### Issue #10: GitHub Integration
- GitHub Actions workflow discovery and parsing
- Repository analysis and code-to-infrastructure linking
- Deployment tracking across all cloud providers
- Webhook support for real-time updates

## Benefits of This Approach

1. **Core Functionality Earlier**: By focusing Phase 2 on platform integrations, we get core functionality working sooner, allowing teams to start using TopDeck with Azure infrastructure.

2. **Incremental Value**: Phase 3 analysis features build directly on Phase 2 integrations, providing immediate value for risk assessment and monitoring before expanding to multiple clouds.

3. **Proven Architecture**: By the time we reach Phase 4, the architecture, integrations, and analysis features are proven with Azure, making multi-cloud expansion more confident and structured.

4. **Terraform Leverage**: Using Terraform makes it easier to:
   - Generate infrastructure configurations from discovered resources
   - Import existing infrastructure
   - Automate deployments
   - Maintain consistency across clouds when we expand in Phase 4

## Migration Notes

If you've already started work based on the old roadmap:

- **Azure DevOps Integration** (Issue #4): Now in Phase 2, no changes to the issue itself
- **GitHub Integration** (Issue #10): Now in Phase 2, no changes to the issue itself
- **Topology Visualization** (Issue #6): Now in Phase 2, no changes to the issue itself
- **Risk Analysis** (Issue #5): Now in Phase 3, no changes to the issue itself
- **Monitoring Integration** (Issue #7): Now in Phase 3, no changes to the issue itself
- **AWS Discovery** (Issue #8): Now in Phase 4, no changes to the issue itself
- **GCP Discovery** (Issue #9): Now in Phase 4, no changes to the issue itself

## Timeline Impact

The overall timeline remains **Months 1-10** for v1.0, with no delays:

- **Phase 1**: Months 1-2 (Foundation)
- **Phase 2**: Months 3-4 (Platform Integrations)
- **Phase 3**: Months 5-6 (Analysis & Intelligence)
- **Phase 4**: Months 7-8 (Multi-Cloud Architecture)
- **Phase 5**: Months 9-10 (Production Ready)

## Next Steps

1. **Review and approve** these changes
2. **Create GitHub issues** using the script: `./scripts/create-github-issues.sh`
3. **Begin Phase 1** work:
   - Issue #1: Technology Stack Decision
   - Issue #2: Core Data Models
   - Issue #3: Azure Resource Discovery
4. **Plan Phase 2** work for Platform Integrations (Azure DevOps and GitHub)

## Questions or Feedback?

If you have questions about these changes:
- Open a discussion in GitHub Discussions
- Comment on the relevant issues
- Contact the project maintainers

---

**Updated**: 2025-10-12  
**Status**: ✅ Roadmap reorganized and new issues created
