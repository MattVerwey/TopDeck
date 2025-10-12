# Roadmap Changes - October 2025

## Summary

The development roadmap has been reorganized to better reflect the architectural approach and prioritize multi-cloud support using Terraform.

## What Changed

### Previous Structure

**Phase 2** (Months 3-4) was originally:
- Multi-Cloud Architecture
  - Architect and implement AWS resource discovery using Terraform
  - Architect and implement GCP resource discovery using Terraform
  - Build unified multi-cloud resource abstraction layer
  - Create infrastructure deployment automation

**Phase 3** (Months 5-6) was originally:
- Platform Integrations
  - Build Azure DevOps pipeline integration
  - Add GitHub Actions and repository integration
  - Implement deployment tracking and linking
  - Create basic topology visualization

**Phase 4** (Months 7-8) was originally:
- Analysis & Intelligence
  - Develop dependency graph builder
  - Implement risk analysis engine
  - Build change impact assessment
  - Integrate performance metrics and monitoring
  - Add error correlation and alerting

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

1. **Foundation First**: By focusing Phase 2 on Platform Integrations with Azure (already implemented in Phase 1), we can establish CI/CD integration patterns early with a single cloud provider.

2. **Build on Success**: With Azure resource discovery complete and platform integrations working, we gain valuable insights before expanding to additional clouds.

3. **Analysis Before Expansion**: Phase 3 focuses on Analysis & Intelligence, allowing us to:
   - Perfect risk analysis and topology visualization on Azure
   - Establish patterns for dependency graphs and impact assessment
   - Build a solid foundation for monitoring integration

4. **Multi-Cloud Last**: By moving Multi-Cloud Architecture to Phase 4, we can:
   - Apply lessons learned from Azure implementation
   - Leverage established patterns for AWS and GCP
   - Use Terraform to accelerate multi-cloud support
   - Ensure platform integrations and analysis work across all clouds from day one

5. **Better Separation of Concerns**:
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

1. **Proven Patterns First**: By completing platform integrations in Phase 2, we establish patterns that work well with Azure before expanding to other clouds.

2. **Early Value Delivery**: Platform integrations and analysis features deliver immediate value for Azure-only users without waiting for multi-cloud support.

3. **Risk Reduction**: Building analysis and intelligence features in Phase 3 on a single cloud reduces complexity and allows for better testing and refinement.

4. **Terraform Leverage**: Moving multi-cloud to Phase 4 allows us to:
   - Apply proven patterns from Azure implementation
   - Use Terraform to accelerate AWS and GCP integration
   - Ensure consistency across all cloud providers
   - Leverage lessons learned from earlier phases

5. **Complete Feature Set**: By Phase 4, all platform integrations and analysis features are mature, ensuring multi-cloud users get the full TopDeck experience from day one across all clouds

## Migration Notes

If you've already started work based on the old roadmap:

- **Azure DevOps Integration** (Issue #4): Now in Phase 2, no changes to the issue itself
- **Risk Analysis** (Issue #5): Now in Phase 3, no changes to the issue itself
- **Topology Visualization** (Issue #6): Now in Phase 2, no changes to the issue itself
- **Monitoring Integration** (Issue #7): Now in Phase 3, no changes to the issue itself
- **AWS Resource Discovery** (Issue #8): Now in Phase 4, no changes to the issue itself
- **GCP Resource Discovery** (Issue #9): Now in Phase 4, no changes to the issue itself

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
4. **Plan Phase 2** work for platform integrations (Azure DevOps, GitHub)

## Questions or Feedback?

If you have questions about these changes:
- Open a discussion in GitHub Discussions
- Comment on the relevant issues
- Contact the project maintainers

---

**Updated**: 2025-10-12  
**Status**: ✅ Roadmap reorganized and new issues created
