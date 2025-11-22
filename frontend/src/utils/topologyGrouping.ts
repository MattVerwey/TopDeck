/**
 * Utility functions for grouping topology nodes
 */

import type { Resource, TopologyGraph } from '../types';

export interface GroupedNode {
  id: string;
  label: string;
  nodes: Resource[];
  isGroup: true;
}

export interface NodeElement {
  data: {
    id: string;
    label: string;
    parent?: string;
    isGroup?: boolean;
    [key: string]: any;
  };
  classes?: string;
}

/**
 * Group nodes by a specific property
 */
export function groupNodesByProperty(
  nodes: Resource[],
  groupBy: 'cluster' | 'namespace' | 'resource_type' | 'cloud_provider'
): Map<string, Resource[]> {
  const groups = new Map<string, Resource[]>();

  nodes.forEach((node) => {
    let groupKey: string | undefined;

    switch (groupBy) {
      case 'cluster':
        groupKey = (node.properties?.cluster as string) || (node.metadata?.cluster as string) || 'ungrouped';
        break;
      case 'namespace':
        groupKey = (node.properties?.namespace as string) || (node.metadata?.namespace as string) || 'ungrouped';
        break;
      case 'resource_type':
        groupKey = node.resource_type || 'unknown';
        break;
      case 'cloud_provider':
        groupKey = node.cloud_provider || 'unknown';
        break;
    }

    if (groupKey) {
      if (!groups.has(groupKey)) {
        groups.set(groupKey, []);
      }
      groups.get(groupKey)!.push(node);
    }
  });

  return groups;
}

/**
 * Create Cytoscape compound node elements for groups
 */
export function createGroupElements(
  groups: Map<string, Resource[]>,
  groupBy: string
): NodeElement[] {
  const elements: NodeElement[] = [];

  groups.forEach((nodes, groupKey) => {
    // Create parent node for group
    elements.push({
      data: {
        id: `group-${groupKey}`,
        label: formatGroupLabel(groupKey, groupBy),
        isGroup: true,
        groupKey,
        nodeCount: nodes.length,
      },
      classes: 'group-node',
    });
  });

  return elements;
}

/**
 * Format group label for display
 */
function formatGroupLabel(key: string, groupBy: string): string {
  if (key === 'ungrouped' || key === 'unknown') {
    return `No ${groupBy.replace('_', ' ')}`;
  }

  // Capitalize and format
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Assign parent group to node data
 */
export function assignNodeParents(
  nodes: Resource[],
  groups: Map<string, Resource[]>,
  groupBy: 'cluster' | 'namespace' | 'resource_type' | 'cloud_provider'
): Map<string, string> {
  const parentMap = new Map<string, string>();

  groups.forEach((groupNodes, groupKey) => {
    groupNodes.forEach((node) => {
      parentMap.set(node.id, `group-${groupKey}`);
    });
  });

  return parentMap;
}

/**
 * Apply grouping to topology data for Cytoscape
 */
export function applyGroupingToElements(
  elements: any[],
  groupBy: 'cluster' | 'namespace' | 'resource_type' | 'cloud_provider' | undefined,
  nodes: Resource[]
): any[] {
  if (!groupBy) {
    return elements;
  }

  const groups = groupNodesByProperty(nodes, groupBy);
  const parentMap = assignNodeParents(nodes, groups, groupBy);
  const groupElements = createGroupElements(groups, groupBy);

  // Update node elements to include parent reference
  const updatedElements = elements.map((el) => {
    if (el.data.id && !el.data.id.startsWith('edge-') && !el.data.id.startsWith('group-')) {
      const parent = parentMap.get(el.data.id);
      if (parent) {
        return {
          ...el,
          data: {
            ...el.data,
            parent,
          },
        };
      }
    }
    return el;
  });

  // Add group elements before node elements
  return [...groupElements, ...updatedElements];
}
