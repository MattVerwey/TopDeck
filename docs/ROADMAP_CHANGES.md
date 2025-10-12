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
- **Multi-Cloud Architecture**
  - Architect and implement AWS resource discovery using Terraform
  - Architect and implement GCP resource discovery using Terraform
  - Build unified multi-cloud resource abstraction layer
  - Create infrastructure deployment automation

**Phase 3** (Months 5-6) now includes:
- **Platform Integrations**
  - Build Azure DevOps pipeline integration
  - Add GitHub Actions and repository integration
  - Implement deployment tracking and linking
  - Create basic topology visualization

**Phase 4** (Months 7-8) has been consolidated to:
- **Analysis & Intelligence**
  - Develop dependency graph builder
  - Implement risk analysis engine
  - Build change impact assessment
  - Integrate performance metrics and monitoring
  - Add error correlation and alerting

## Rationale

### Why This Change Makes Sense

1. **Terraform Foundation**: Since the project uses Terraform for infrastructure as code, extending from Azure to AWS and GCP should be straightforward. The patterns and modules can be reused across clouds.

2. **Architectural Consistency**: By completing multi-cloud discovery in Phase 2, we establish a consistent architecture early. This allows Phase 3 integrations to work uniformly across all cloud providers.

3. **Platform Integration Complexity**: Azure DevOps and GitHub integrations are more complex than initially thought. They require:
   - Parsing diverse pipeline definitions
   - Linking deployments to resources across multiple clouds
   - Understanding various deployment patterns
   - Tracking deployment history

   Moving these to Phase 3 allows us to integrate with all three cloud providers simultaneously.

4. **Better Separation of Concerns**:
   - Phase 1: Foundation (Azure only)
   - Phase 2: Multi-cloud infrastructure
   - Phase 3: Platform integrations and linking
   - Phase 4: Analysis and intelligence features

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

1. **Faster Multi-Cloud Support**: By focusing Phase 2 on multi-cloud architecture, we can support AWS and GCP much earlier in the development cycle.

2. **Terraform Leverage**: Using Terraform makes it easier to:
   - Generate infrastructure configurations from discovered resources
   - Import existing infrastructure
   - Automate deployments
   - Maintain consistency across clouds

3. **Complete Integration**: Phase 3 integrations can now work with all three cloud providers from day one, rather than being limited to Azure initially.

4. **Parallel Development**: Teams can work on:
   - AWS discovery (Issue #8)
   - GCP discovery (Issue #9)
   - In parallel, while maintaining consistency

## Migration Notes

If you've already started work based on the old roadmap:

- **Azure DevOps Integration** (Issue #4): Now in Phase 3, no changes to the issue itself
- **Risk Analysis** (Issue #5): Now in Phase 4, no changes to the issue itself
- **Topology Visualization** (Issue #6): Now in Phase 3, no changes to the issue itself
- **Monitoring Integration** (Issue #7): Now in Phase 4, no changes to the issue itself

## Timeline Impact

The overall timeline remains **Months 1-10** for v1.0, with no delays:

- **Phase 1**: Months 1-2 (Foundation)
- **Phase 2**: Months 3-4 (Multi-Cloud Architecture)
- **Phase 3**: Months 5-6 (Platform Integrations)
- **Phase 4**: Months 7-8 (Analysis & Intelligence)
- **Phase 5**: Months 9-10 (Production Ready)

## Next Steps

1. **Review and approve** these changes
2. **Create GitHub issues** using the script: `./scripts/create-github-issues.sh`
3. **Begin Phase 1** work:
   - Issue #1: Technology Stack Decision
   - Issue #2: Core Data Models
   - Issue #3: Azure Resource Discovery
4. **Plan Phase 2** work for AWS and GCP discovery

## Questions or Feedback?

If you have questions about these changes:
- Open a discussion in GitHub Discussions
- Comment on the relevant issues
- Contact the project maintainers

---

**Updated**: 2025-10-12  
**Status**: ✅ Roadmap reorganized and new issues created
