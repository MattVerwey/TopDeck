#!/usr/bin/env python3
"""
Demo script for enhanced topology and dependency analysis features.

This script demonstrates the new capabilities for understanding which resources
are attached to which and getting in-depth analysis.

Usage:
    python examples/enhanced_topology_demo.py --resource-id <id>
"""

import argparse
import json
import sys

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Install with: pip install httpx")
    sys.exit(1)


class TopologyDemo:
    """Demo class for enhanced topology and dependency analysis."""
    
    def __init__(self, base_url: str):
        """Initialize with API base URL."""
        self.base_url = base_url
    
    @staticmethod
    def print_header(title: str):
        """Print a formatted section header."""
        print("\n" + "=" * 80)
        print(f" {title}")
        print("=" * 80 + "\n")
    
    def get_resource_attachments(self, client: httpx.Client, resource_id: str, direction: str = "both"):
        """Get detailed attachment information for a resource."""
        self.print_header(f"Resource Attachments ({direction})")
        
        try:
            response = client.get(
                f"{self.base_url}/api/v1/topology/resources/{resource_id}/attachments",
                params={"direction": direction}
            )
            response.raise_for_status()
            attachments = response.json()
            
            if not attachments:
                print(f"No attachments found in {direction} direction.")
                return
            
            print(f"Found {len(attachments)} attachment(s):\n")
            
            for i, att in enumerate(attachments, 1):
                print(f"{i}. {att['source_name']} ({att['source_type']})")
                print(f"   → {att['target_name']} ({att['target_type']})")
                print(f"   Relationship: {att['relationship_type']}")
                print(f"   Category: {att['attachment_context'].get('relationship_category', 'N/A')}")
                print(f"   Critical: {att['attachment_context'].get('is_critical', False)}")
                
                if att['relationship_properties']:
                    print(f"   Properties: {json.dumps(att['relationship_properties'], indent=6)}")
                print()
            
        except httpx.HTTPStatusError as e:
            print(f"Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def get_dependency_chains(self, client: httpx.Client, resource_id: str, direction: str = "downstream"):
        """Get dependency chains for a resource."""
        self.print_header(f"Dependency Chains ({direction})")
        
        try:
            response = client.get(
                f"{self.base_url}/api/v1/topology/resources/{resource_id}/chains",
                params={"direction": direction, "max_depth": 5}
            )
            response.raise_for_status()
            chains = response.json()
            
            if not chains:
                print(f"No dependency chains found in {direction} direction.")
                return
            
            print(f"Found {len(chains)} chain(s):\n")
            
            for i, chain in enumerate(chains, 1):
                print(f"Chain {i} (length: {chain['chain_length']}):")
                
                # Build the chain visualization
                parts = []
                for j, name in enumerate(chain['resource_names']):
                    parts.append(f"{name} ({chain['resource_types'][j]})")
                    if j < len(chain['relationships']):
                        parts.append(f"[{chain['relationships'][j]}]")
                
                chain_str = " → ".join(parts)
                print(f"  {chain_str}")
                print()
            
        except httpx.HTTPStatusError as e:
            print(f"Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def get_attachment_analysis(self, client: httpx.Client, resource_id: str):
        """Get comprehensive attachment analysis."""
        self.print_header("Comprehensive Attachment Analysis")
        
        try:
            response = client.get(
                f"{self.base_url}/api/v1/topology/resources/{resource_id}/analysis"
            )
            response.raise_for_status()
            analysis = response.json()
            
            print(f"Resource: {analysis['resource_name']} ({analysis['resource_type']})")
            print(f"Resource ID: {analysis['resource_id']}\n")
            
            print("📊 SUMMARY")
            print(f"  Total Attachments: {analysis['total_attachments']}")
            print(f"  Critical Attachments: {len(analysis['critical_attachments'])}")
            print(f"  Impact Radius: {analysis['impact_radius']} resources")
            print(f"  Unique Relationship Types: {analysis['metadata']['unique_relationship_types']}")
            print(f"  Max Chain Length: {analysis['metadata']['max_chain_length']}\n")
            
            print("📈 ATTACHMENT BREAKDOWN BY TYPE")
            for rel_type, count in analysis['attachment_by_type'].items():
                strength = analysis['attachment_strength'].get(rel_type, 0.0)
                print(f"  {rel_type:25} Count: {count:3}  Strength: {strength:.2f}")
            print()
            
            if analysis['critical_attachments']:
                print("⚠️  CRITICAL ATTACHMENTS")
                for att in analysis['critical_attachments']:
                    print(f"  • {att['source_name']} → {att['target_name']}")
                    print(f"    Type: {att['relationship_type']}")
                    print(f"    Category: {att['attachment_context'].get('relationship_category', 'N/A')}")
                print()
            
            if analysis['dependency_chains']:
                print(f"🔗 DEPENDENCY CHAINS (showing first 3 of {len(analysis['dependency_chains'])})")
                for i, chain in enumerate(analysis['dependency_chains'][:3], 1):
                    print(f"  {i}. {' → '.join(chain['resource_names'][:4])}")
                    if len(chain['resource_names']) > 4:
                        print(f"     ... and {len(chain['resource_names']) - 4} more")
                print()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"Error: Resource '{resource_id}' not found.")
            else:
                print(f"Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def get_enhanced_dependencies(self, client: httpx.Client, resource_id: str):
        """Get enhanced dependencies (existing endpoint with new data)."""
        self.print_header("Enhanced Dependencies")
        
        try:
            response = client.get(
                f"{self.base_url}/api/v1/topology/resources/{resource_id}/dependencies",
                params={"depth": 3, "direction": "both"}
            )
            response.raise_for_status()
            deps = response.json()
            
            print(f"Resource: {deps['resource_name']}")
            print(f"Depth: {deps['depth']}\n")
            
            print(f"Upstream Dependencies: {len(deps['upstream'])}")
            for res in deps['upstream'][:5]:
                print(f"  • {res['name']} ({res['resource_type']})")
            if len(deps['upstream']) > 5:
                print(f"  ... and {len(deps['upstream']) - 5} more\n")
            else:
                print()
            
            print(f"Downstream Dependencies: {len(deps['downstream'])}")
            for res in deps['downstream'][:5]:
                print(f"  • {res['name']} ({res['resource_type']})")
            if len(deps['downstream']) > 5:
                print(f"  ... and {len(deps['downstream']) - 5} more\n")
            else:
                print()
            
            # Show new attachment details
            if deps.get('upstream_attachments'):
                print(f"📎 Upstream Attachment Details ({len(deps['upstream_attachments'])} total)")
                for att in deps['upstream_attachments'][:3]:
                    print(f"  • {att['relationship_type']}: {att['source_name']} → {att['target_name']}")
                if len(deps['upstream_attachments']) > 3:
                    print(f"  ... and {len(deps['upstream_attachments']) - 3} more")
                print()
            
            if deps.get('downstream_attachments'):
                print(f"📎 Downstream Attachment Details ({len(deps['downstream_attachments'])} total)")
                for att in deps['downstream_attachments'][:3]:
                    print(f"  • {att['relationship_type']}: {att['source_name']} → {att['target_name']}")
                if len(deps['downstream_attachments']) > 3:
                    print(f"  ... and {len(deps['downstream_attachments']) - 3} more")
                print()
            
        except httpx.HTTPStatusError as e:
            print(f"Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Demo script for enhanced topology and dependency analysis"
    )
    parser.add_argument(
        "--resource-id",
        required=True,
        help="Resource ID to analyze"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="TopDeck API URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--feature",
        choices=["all", "attachments", "chains", "analysis", "dependencies"],
        default="all",
        help="Which feature to demonstrate (default: all)"
    )
    
    args = parser.parse_args()
    
    # Create demo instance
    demo = TopologyDemo(args.api_url)
    
    print("\n" + "=" * 80)
    print(" Enhanced Topology and Dependency Analysis Demo")
    print("=" * 80)
    print(f"\nAnalyzing resource: {args.resource_id}")
    print(f"API URL: {args.api_url}")
    
    with httpx.Client() as client:
        try:
            # Test API connectivity
            response = client.get(f"{args.api_url}/api/v1/topology")
            response.raise_for_status()
        except Exception as e:
            print(f"\n❌ Error: Cannot connect to TopDeck API at {args.api_url}")
            print(f"   {str(e)}")
            print("\nMake sure TopDeck is running:")
            print("  1. Start Neo4j: docker-compose up -d")
            print("  2. Start API: make run")
            sys.exit(1)
        
        # Run requested features
        if args.feature in ["all", "analysis"]:
            demo.get_attachment_analysis(client, args.resource_id)
        
        if args.feature in ["all", "attachments"]:
            demo.get_resource_attachments(client, args.resource_id, direction="both")
        
        if args.feature in ["all", "chains"]:
            demo.get_dependency_chains(client, args.resource_id, direction="downstream")
            demo.get_dependency_chains(client, args.resource_id, direction="upstream")
        
        if args.feature in ["all", "dependencies"]:
            demo.get_enhanced_dependencies(client, args.resource_id)
    
    print("\n" + "=" * 80)
    print(" Demo Complete!")
    print("=" * 80)
    print("\nFor more information, see:")
    print("  - docs/ENHANCED_TOPOLOGY_ANALYSIS.md")
    print("  - docs/ENHANCED_TOPOLOGY_QUICK_REF.md")
    print()


if __name__ == "__main__":
    main()
