# TopDeck Scripts

Utility scripts for project setup and management.

## Available Scripts

### create-github-issues.sh

Creates GitHub issues from the templates in `docs/issues/`.

**Prerequisites**:
- GitHub CLI (`gh`) must be installed
- You must be authenticated with `gh auth login`
- You must have write access to the repository

**Usage**:
```bash
./scripts/create-github-issues.sh
```

This will create all 10 issues from the templates:
- **Phase 1** (Issues #1-3): Foundation
- **Phase 2** (Issues #4, #6, #10): Platform Integrations
- **Phase 3** (Issues #5, #7): Analysis & Intelligence
- **Phase 4** (Issues #8-9): Multi-Cloud Architecture

**Labels Used**:
- `enhancement` - For new features
- `architecture` - For architectural decisions
- `discovery` - For resource discovery features
- `integration` - For CI/CD integrations
- `visualization` - For UI/dashboard features
- `analysis` - For risk analysis features
- `monitoring` - For monitoring integrations
- `ui` - For user interface work
- `cloud: azure` - Azure-specific work
- `cloud: aws` - AWS-specific work
- `cloud: gcp` - GCP-specific work
- `priority: high` - High priority items
- `priority: medium` - Medium priority items
- `phase-1` through `phase-4` - Development phases

**Note**: You may need to create these labels in your repository first if they don't exist.

## Manual Issue Creation

If you prefer to create issues manually:

1. Go to https://github.com/MattVerwey/TopDeck/issues/new
2. Copy the content from the relevant file in `docs/issues/`
3. Use the title from the first line (without the `#`)
4. Add the labels listed on line 3
5. Submit the issue

## Creating Labels

To create all necessary labels at once:

```bash
# Create priority labels
gh label create "priority: high" --color "d73a4a" --description "High priority"
gh label create "priority: medium" --color "fbca04" --description "Medium priority"
gh label create "priority: low" --color "0e8a16" --description "Low priority"

# Create phase labels
gh label create "phase-1" --color "1d76db" --description "Phase 1: Foundation"
gh label create "phase-2" --color "1d76db" --description "Phase 2: Platform Integrations"
gh label create "phase-3" --color "1d76db" --description "Phase 3: Analysis & Intelligence"
gh label create "phase-4" --color "1d76db" --description "Phase 4: Multi-Cloud Architecture"

# Create cloud provider labels
gh label create "cloud: azure" --color "0078d4" --description "Azure-specific"
gh label create "cloud: aws" --color "ff9900" --description "AWS-specific"
gh label create "cloud: gcp" --color "4285f4" --description "GCP-specific"

# Create component labels
gh label create "discovery" --color "bfdadc" --description "Resource discovery"
gh label create "integration" --color "bfdadc" --description "CI/CD integration"
gh label create "analysis" --color "bfdadc" --description "Risk analysis"
gh label create "visualization" --color "bfdadc" --description "Visualization"
gh label create "monitoring" --color "bfdadc" --description "Monitoring"
gh label create "ui" --color "bfdadc" --description "User interface"
gh label create "architecture" --color "bfdadc" --description "Architecture decisions"
```
