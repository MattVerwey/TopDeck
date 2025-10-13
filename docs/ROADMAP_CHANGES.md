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

## Progress Update (2025-10-13)

Since the roadmap reorganization, we've made significant technical progress but need to **refocus on core value delivery**.

### ✅ Completed - Strong Foundation
- **Phase 1** (100% Complete)
  - Issue #1: Technology Stack Decision ✅
  - Issue #2: Core Data Models ✅
  - Issue #3: Azure Resource Discovery ✅
  
- **Phase 2** (100% Complete)
  - Azure DevOps integration ✅
  - GitHub integration ✅
  - Topology API endpoints ✅

- **Multi-Cloud Foundation** (70% Complete)
  - AWS resource mapper ✅
  - GCP resource mapper ✅
  - Multi-cloud abstraction layer ✅
  - Orchestrator implementation pending

### 🎯 Critical Focus Now - Core Value Delivery

**Phase 3: Risk Analysis & Intelligence** (30% Complete) ⚠️ **TOP PRIORITY**

**What's Missing (And Why It Matters)**:
- **Risk Analysis Engine** - This is TopDeck's entire value proposition
  - Without this, we can discover resources but can't answer "What breaks if this changes?"
  - Users need risk assessment, not just topology mapping
  - This is what distinguishes TopDeck from simple discovery tools

**The Problem**: We've built excellent infrastructure (discovery, storage, integrations) but haven't delivered the **analysis features users actually need**. Time to focus.

## Next Steps - Refocused

1. ✅ **Phase 1 Complete** - Foundation solid
2. ✅ **Phase 2 Complete** - Platform integrations working
3. 🎯 **Phase 3 Priority** - **Implement Risk Analysis Engine (Issue #5)** ⚠️ **CRITICAL**
4. 🎯 **Phase 3 Priority** - Enhance visualization with risk data (Issue #6)
5. 🔜 **Phase 4** - Multi-cloud expansion (after Phase 3 delivers value)

**Critical Insight**: We need to **finish Phase 3** before expanding further. The risk analysis engine is TopDeck's core differentiator.

**Current Focus**: Implement risk analysis algorithms - dependency impact, blast radius, risk scoring.

For detailed progress tracking, see [PROGRESS.md](../PROGRESS.md).

## Lessons Learned

**What Went Well**:
- Strong technical foundation
- Clean architecture and data models
- Good test coverage

**What Needs Adjustment**:
- **Too much horizontal progress** (discovery for 3 clouds, integrations, monitoring)
- **Not enough vertical progress** (core value delivery - risk analysis)
- Need to **focus on one complete use case** before expanding

**Going Forward**:
- Complete Phase 3 risk analysis before expanding to more clouds
- Deliver one full user journey end-to-end
- Focus on value, not just technical capabilities

---

**Updated**: 2025-10-13  
**Status**: 🎯 Refocused on Core Value Delivery (Risk Analysis Engine)
