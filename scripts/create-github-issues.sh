#!/bin/bash

# Script to create GitHub issues from the issue templates
# This script should be run manually by the repository owner
# Usage: ./scripts/create-github-issues.sh

set -e

REPO="MattVerwey/TopDeck"
DOCS_DIR="docs/issues"

echo "Creating GitHub issues from templates..."
echo "Repository: $REPO"
echo ""

# Function to create an issue from a template file
create_issue() {
    local issue_file=$1
    local issue_number=$2
    local title=$3
    local labels=$4
    local phase=$5
    
    echo "Creating Issue #${issue_number}: ${title}..."
    
    # Extract the body (skip the first 4 lines which contain title and labels)
    body=$(tail -n +5 "${DOCS_DIR}/${issue_file}")
    
    gh issue create \
        --repo "$REPO" \
        --title "$title" \
        --body "$body" \
        --label "$labels"
    
    echo "✓ Issue #${issue_number} created"
    echo ""
}

# Phase 1: Foundation
echo "=== Phase 1: Foundation ==="
create_issue "issue-001-technology-stack-decision.md" "1" "Technology Stack Decision" "enhancement,architecture,priority: high,phase-1"
create_issue "issue-002-core-data-models.md" "2" "Core Data Models" "enhancement,architecture,priority: high,phase-1"
create_issue "issue-003-azure-resource-discovery.md" "3" "Implement Azure Resource Discovery" "enhancement,cloud: azure,discovery,priority: high,phase-1"

# Phase 2: Multi-Cloud Architecture
echo "=== Phase 2: Multi-Cloud Architecture ==="
create_issue "issue-008-aws-resource-discovery.md" "8" "Implement AWS Resource Discovery" "enhancement,cloud: aws,discovery,priority: high,phase-2"
create_issue "issue-009-gcp-resource-discovery.md" "9" "Implement GCP Resource Discovery" "enhancement,cloud: gcp,discovery,priority: high,phase-2"

# Phase 3: Platform Integrations
echo "=== Phase 3: Platform Integrations ==="
create_issue "issue-004-azure-devops-integration.md" "4" "Implement Azure DevOps Integration" "enhancement,integration,priority: high,phase-3"
create_issue "issue-010-github-integration.md" "10" "Implement GitHub Integration" "enhancement,integration,priority: high,phase-3"
create_issue "issue-006-topology-visualization.md" "6" "Topology Visualization Dashboard" "enhancement,visualization,ui,priority: high,phase-3"

# Phase 4: Analysis & Intelligence
echo "=== Phase 4: Analysis & Intelligence ==="
create_issue "issue-005-risk-analysis-engine.md" "5" "Risk Analysis Engine" "enhancement,analysis,priority: high,phase-4"
create_issue "issue-007-performance-monitoring-integration.md" "7" "Performance Monitoring Integration" "enhancement,monitoring,priority: medium,phase-4"

echo ""
echo "✓ All issues created successfully!"
echo ""
echo "Next steps:"
echo "1. Review the created issues"
echo "2. Assign issues to team members"
echo "3. Add issues to project board"
echo "4. Set milestones for each phase"
