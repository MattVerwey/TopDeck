# Network Topology Filtering and Grouping Guide

## Overview

The TopDeck Network Topology visualization has been enhanced with powerful filtering and grouping capabilities to help you focus on relevant resources and reduce visual clutter.

## Filtering Modes

TopDeck offers three filtering modes to control what gets displayed when you apply filters:

### 1. Strict Mode (Default)
**Best for: Reducing clutter and focusing on specific resources**

- Shows **only** resources that match your filter criteria
- No dependencies are automatically included
- Cleanest view with minimal nodes
- Perfect for answering "Show me all databases" without seeing everything connected to them

**Example:**
- Filter: Resource Type = "database"
- Result: Only database nodes are shown
- Hidden: All services, load balancers, and other resources that connect to databases

### 2. With Direct Dependencies
**Best for: Understanding immediate connections**

- Shows filtered resources **plus** their direct dependencies (1 level)
- Includes both upstream (what it depends on) and downstream (what depends on it)
- Balanced view showing context without overwhelming clutter
- Perfect for answering "What directly connects to these databases?"

**Example:**
- Filter: Resource Type = "database"
- Result: Databases + services that directly connect to them + storage they use
- Hidden: Services that connect through other services (2+ levels away)

### 3. Full Dependency Graph
**Best for: Complete dependency chain analysis**

- Shows filtered resources **plus** all transitive dependencies
- Follows the entire dependency chain to show the complete picture
- Most comprehensive but potentially cluttered with many resources
- Perfect for answering "Show me everything that could be affected by these databases"

**Example:**
- Filter: Resource Type = "database"
- Result: Databases + all connected services + all services those connect to + all their dependencies
- Hidden: Nothing - complete dependency graph is shown

## How to Use Filtering Modes

1. **Access Topology Page**: Navigate to Network Topology in the sidebar
2. **Select Filter Mode**: Choose from the three radio buttons at the top of the filter panel
3. **Apply Filters**: Use the filter dropdowns below (Cloud Provider, Resource Type, Cluster, Namespace)
4. **View Results**: The banner shows how many resources are displayed vs. total

## Visual Grouping

Group related resources together to organize your topology view.

### Enabling Grouping

1. **Toggle Grouping**: Click the "Enable Grouping" switch in the filter panel
2. **Select Group By**: Choose how to group resources:
   - **Cluster**: Group by Kubernetes cluster or AKS cluster
   - **Namespace**: Group by Kubernetes namespace or Service Bus namespace
   - **Resource Type**: Group by type (databases, services, storage, etc.)
   - **Cloud Provider**: Group by Azure, AWS, GCP

### Group Features

- **Visual Containers**: Groups appear as dashed-border containers containing related nodes
- **Group Labels**: Each group shows its name at the top
- **Collapse/Expand**: Click on any group container to collapse or expand it
  - Collapsed: Hides all nodes in the group to reduce clutter
  - Expanded: Shows all nodes in the group
- **Node Count**: Group labels show "(click to collapse/expand)" hint

### Best Practices for Grouping

1. **Cluster Grouping**: Best for multi-cluster environments to see resources by cluster
2. **Namespace Grouping**: Perfect for microservices organized by namespace
3. **Resource Type Grouping**: Great for seeing all databases, services, storage together
4. **Cloud Provider Grouping**: Useful for multi-cloud deployments

## Combining Filters and Grouping

You can use filtering modes and grouping together for powerful visualizations:

### Example 1: Focus on Production Databases by Cluster
```
Filter Mode: Strict
Filters: Resource Type = "sql_database", Cluster = "prod-cluster"
Grouping: Enabled, Group By = "cluster"
Result: Only SQL databases in prod cluster, grouped by cluster
```

### Example 2: Service Dependencies with Namespace Organization
```
Filter Mode: With Direct Dependencies
Filters: Resource Type = "service"
Grouping: Enabled, Group By = "namespace"
Result: All services + direct dependencies, organized by namespace
```

### Example 3: Complete Application Topology by Type
```
Filter Mode: Full Dependency Graph
Filters: Cloud Provider = "azure"
Grouping: Enabled, Group By = "resource_type"
Result: All Azure resources with full dependencies, grouped by type
```

## Filter Status Banner

The filter status banner appears when filters are active:

- **Mode Indicator**: Shows which filter mode is active
- **Resource Count**: Displays "Showing X of Y total resources"
- **Active Filters**: Shows chips for each active filter
- **Clear Filters**: Click "Clear" to reset all filters

## Resource Selection

For even more focused analysis:

1. Click **"Select Resources"** button
2. Choose specific resources from the dialog
3. View only those resources and their dependencies (based on filter mode)
4. Combine with grouping to organize the selected resources

## Tips and Tricks

### Reducing Clutter
- Use **Strict Mode** when you have many resources and only want to see specific types
- Enable **Grouping** and collapse groups you're not interested in
- Use **Resource Selection** to focus on just a few critical resources

### Understanding Dependencies
- Use **With Direct Dependencies** as a starting point
- Switch to **Full Dependency Graph** if you need complete impact analysis
- Group by **resource_type** to see how different layers connect

### Multi-Cloud Environments
- Group by **cloud_provider** to see resources by cloud
- Use **Strict Mode** with cloud provider filter to analyze one cloud at a time
- Switch between providers while keeping grouping enabled

### Performance
- For large topologies (100+ resources), use **Strict Mode** to keep the graph responsive
- Collapse groups you're not actively analyzing
- Apply multiple filters to narrow down the view

## Keyboard Shortcuts

- **Click Background**: Deselect all nodes and clear highlights
- **Click Node**: Select node and show details (or collapse/expand if group)
- **Scroll**: Zoom in/out
- **Click + Drag**: Pan the view

## Related Documentation

- [Enhanced Topology Analysis Guide](./features/ENHANCED_TOPOLOGY_ANALYSIS.md)
- [Network Flow Diagrams](./architecture/network-flow-diagrams.md)
- [Topology API Reference](./api/TOPOLOGY_API.md)
