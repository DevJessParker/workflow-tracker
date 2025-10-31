#!/usr/bin/env python3
"""
Create focused workflow diagrams from scan results.

This script reads the workflow_graph.json and creates various
focused visualizations for specific workflows or modules.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Set
import sys


def load_workflow_data(json_path: str) -> dict:
    """Load workflow data from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def filter_by_module(data: dict, module_path: str) -> dict:
    """Filter workflows to a specific module/directory."""
    filtered_nodes = [
        node for node in data['nodes']
        if module_path in node['location']['file']
    ]

    node_ids = {node['id'] for node in filtered_nodes}

    filtered_edges = [
        edge for edge in data['edges']
        if edge['source'] in node_ids and edge['target'] in node_ids
    ]

    return {
        'nodes': filtered_nodes,
        'edges': filtered_edges,
        'metadata': {
            'filtered_by': f'module:{module_path}',
            'original_nodes': len(data['nodes']),
            'filtered_nodes': len(filtered_nodes)
        }
    }


def filter_by_type(data: dict, workflow_type: str) -> dict:
    """Filter workflows to a specific type (e.g., 'api_call', 'database_write')."""
    filtered_nodes = [
        node for node in data['nodes']
        if node['type'] == workflow_type
    ]

    return {
        'nodes': filtered_nodes,
        'edges': data['edges'],  # Keep all edges for context
        'metadata': {
            'filtered_by': f'type:{workflow_type}',
            'original_nodes': len(data['nodes']),
            'filtered_nodes': len(filtered_nodes)
        }
    }


def filter_by_table(data: dict, table_name: str) -> dict:
    """Filter workflows related to a specific database table."""
    # Find all nodes that interact with this table
    filtered_nodes = [
        node for node in data['nodes']
        if node.get('table_name') == table_name
    ]

    node_ids = {node['id'] for node in filtered_nodes}

    # Include connected nodes (within 1 hop)
    connected_ids = set(node_ids)
    for edge in data['edges']:
        if edge['source'] in node_ids:
            connected_ids.add(edge['target'])
        if edge['target'] in node_ids:
            connected_ids.add(edge['source'])

    # Get all connected nodes
    all_filtered_nodes = [
        node for node in data['nodes']
        if node['id'] in connected_ids
    ]

    filtered_edges = [
        edge for edge in data['edges']
        if edge['source'] in connected_ids and edge['target'] in connected_ids
    ]

    return {
        'nodes': all_filtered_nodes,
        'edges': filtered_edges,
        'metadata': {
            'filtered_by': f'table:{table_name}',
            'original_nodes': len(data['nodes']),
            'filtered_nodes': len(all_filtered_nodes)
        }
    }


def filter_by_endpoint(data: dict, endpoint_pattern: str) -> dict:
    """Filter workflows related to a specific API endpoint."""
    filtered_nodes = [
        node for node in data['nodes']
        if node.get('endpoint') and endpoint_pattern in node['endpoint']
    ]

    node_ids = {node['id'] for node in filtered_nodes}

    # Include connected nodes
    connected_ids = set(node_ids)
    for edge in data['edges']:
        if edge['source'] in node_ids:
            connected_ids.add(edge['target'])
        if edge['target'] in node_ids:
            connected_ids.add(edge['source'])

    all_filtered_nodes = [
        node for node in data['nodes']
        if node['id'] in connected_ids
    ]

    filtered_edges = [
        edge for edge in data['edges']
        if edge['source'] in connected_ids and edge['target'] in connected_ids
    ]

    return {
        'nodes': all_filtered_nodes,
        'edges': filtered_edges,
        'metadata': {
            'filtered_by': f'endpoint:{endpoint_pattern}',
            'original_nodes': len(data['nodes']),
            'filtered_nodes': len(all_filtered_nodes)
        }
    }


def create_mermaid_diagram(filtered_data: dict, output_path: str):
    """Create a Mermaid flowchart."""
    lines = []
    lines.append("```mermaid")
    lines.append("flowchart TD")
    lines.append("")

    # Create node definitions
    type_colors = {
        'database_read': '#4CAF50',
        'database_write': '#FF9800',
        'api_call': '#2196F3',
        'file_read': '#9C27B0',
        'file_write': '#E91E63',
        'data_transform': '#FFEB3B'
    }

    node_labels = {}
    for i, node in enumerate(filtered_data['nodes'][:50]):  # Limit to 50 for readability
        node_id = f"N{i}"
        node_labels[node['id']] = node_id

        # Create short label
        label = node['name'][:30]
        if node.get('table_name'):
            label = f"{label}<br/>{node['table_name']}"
        if node.get('endpoint'):
            endpoint = node['endpoint'][:30]
            label = f"{label}<br/>{endpoint}"

        lines.append(f"    {node_id}[\"{label}\"]")

        # Add styling
        node_type = node['type']
        if node_type in type_colors:
            lines.append(f"    style {node_id} fill:{type_colors[node_type]}")

    lines.append("")

    # Create edges
    for edge in filtered_data['edges']:
        source_id = node_labels.get(edge['source'])
        target_id = node_labels.get(edge['target'])

        if source_id and target_id:
            label = edge.get('label', '')
            if label:
                lines.append(f"    {source_id} -->|{label}| {target_id}")
            else:
                lines.append(f"    {source_id} --> {target_id}")

    lines.append("```")

    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"✓ Created Mermaid diagram: {output_path}")
    print(f"  Nodes: {len(filtered_data['nodes'])} (showing first 50)")
    print(f"  Edges: {len(filtered_data['edges'])}")
    print(f"\nTo render:")
    print(f"  1. Copy content to https://mermaid.live/")
    print(f"  2. Or use in Markdown (GitHub, GitLab, etc.)")


def create_graphviz_dot(filtered_data: dict, output_path: str):
    """Create a Graphviz DOT file."""
    lines = []
    lines.append("digraph Workflow {")
    lines.append("    rankdir=TB;")
    lines.append("    node [shape=box, style=rounded];")
    lines.append("")

    # Node definitions
    for i, node in enumerate(filtered_data['nodes'][:100]):  # Limit to 100
        node_id = f"N{i}"
        label = node['name'].replace('"', '\\"')

        # Add details
        details = []
        if node.get('table_name'):
            details.append(f"Table: {node['table_name']}")
        if node.get('endpoint'):
            details.append(f"API: {node['endpoint'][:30]}")

        if details:
            label += "\\n" + "\\n".join(details)

        # Color by type
        color = {
            'database_read': 'lightgreen',
            'database_write': 'orange',
            'api_call': 'lightblue',
            'file_read': 'plum',
            'file_write': 'pink',
            'data_transform': 'yellow'
        }.get(node['type'], 'white')

        lines.append(f'    N{i} [label="{label}", fillcolor="{color}", style="filled,rounded"];')

    lines.append("")

    # Edge definitions
    node_to_id = {node['id']: f"N{i}" for i, node in enumerate(filtered_data['nodes'][:100])}

    for edge in filtered_data['edges']:
        source_id = node_to_id.get(edge['source'])
        target_id = node_to_id.get(edge['target'])

        if source_id and target_id:
            label = edge.get('label', '')
            if label:
                lines.append(f'    {source_id} -> {target_id} [label="{label}"];')
            else:
                lines.append(f'    {source_id} -> {target_id};')

    lines.append("}")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"✓ Created Graphviz DOT file: {output_path}")
    print(f"  Nodes: {len(filtered_data['nodes'])} (showing first 100)")
    print(f"  Edges: {len(filtered_data['edges'])}")
    print(f"\nTo render:")
    print(f"  dot -Tpng {output_path} -o diagram.png")
    print(f"  dot -Tsvg {output_path} -o diagram.svg")


def create_plantuml(filtered_data: dict, output_path: str):
    """Create a PlantUML sequence diagram."""
    lines = []
    lines.append("@startuml")
    lines.append("!theme plain")
    lines.append("")

    # Group nodes by file
    files = {}
    for node in filtered_data['nodes'][:50]:
        file_path = node['location']['file']
        file_name = Path(file_path).name
        if file_name not in files:
            files[file_name] = []
        files[file_name].append(node)

    # Create participants
    for file_name in list(files.keys())[:10]:  # Limit to 10 files
        lines.append(f'participant "{file_name}" as {file_name.replace(".", "_")}')

    lines.append("")

    # Create sequence
    for edge in filtered_data['edges'][:50]:  # Limit to 50 interactions
        source_node = next((n for n in filtered_data['nodes'] if n['id'] == edge['source']), None)
        target_node = next((n for n in filtered_data['nodes'] if n['id'] == edge['target']), None)

        if source_node and target_node:
            source_file = Path(source_node['location']['file']).name.replace(".", "_")
            target_file = Path(target_node['location']['file']).name.replace(".", "_")
            label = edge.get('label', source_node['name'][:30])

            lines.append(f'{source_file} -> {target_file}: {label}')

    lines.append("")
    lines.append("@enduml")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"✓ Created PlantUML diagram: {output_path}")
    print(f"  Files: {len(files)}")
    print(f"  Interactions: {min(50, len(filtered_data['edges']))}")
    print(f"\nTo render:")
    print(f"  1. Install PlantUML: https://plantuml.com/")
    print(f"  2. Run: plantuml {output_path}")
    print(f"  3. Or use online: http://www.plantuml.com/plantuml/")


def main():
    parser = argparse.ArgumentParser(description='Create focused workflow diagrams')
    parser.add_argument('json_file', help='Path to workflow_graph.json')
    parser.add_argument('--module', help='Filter by module/directory path (e.g., "Services/User")')
    parser.add_argument('--type', help='Filter by type (api_call, database_read, database_write, etc.)')
    parser.add_argument('--table', help='Filter by database table name')
    parser.add_argument('--endpoint', help='Filter by API endpoint pattern')
    parser.add_argument('--format', choices=['mermaid', 'dot', 'plantuml', 'all'], default='mermaid',
                       help='Output format')
    parser.add_argument('--output', '-o', default='diagram', help='Output file prefix')

    args = parser.parse_args()

    # Load data
    print(f"Loading workflow data from {args.json_file}...")
    data = load_workflow_data(args.json_file)
    print(f"✓ Loaded {len(data['nodes'])} nodes, {len(data['edges'])} edges\n")

    # Apply filters
    filtered_data = data

    if args.module:
        print(f"Filtering by module: {args.module}")
        filtered_data = filter_by_module(data, args.module)
        print(f"✓ Filtered to {len(filtered_data['nodes'])} nodes\n")

    if args.type:
        print(f"Filtering by type: {args.type}")
        filtered_data = filter_by_type(filtered_data, args.type)
        print(f"✓ Filtered to {len(filtered_data['nodes'])} nodes\n")

    if args.table:
        print(f"Filtering by table: {args.table}")
        filtered_data = filter_by_table(filtered_data, args.table)
        print(f"✓ Filtered to {len(filtered_data['nodes'])} nodes\n")

    if args.endpoint:
        print(f"Filtering by endpoint: {args.endpoint}")
        filtered_data = filter_by_endpoint(filtered_data, args.endpoint)
        print(f"✓ Filtered to {len(filtered_data['nodes'])} nodes\n")

    if len(filtered_data['nodes']) == 0:
        print("⚠️  No nodes match the filter criteria!")
        sys.exit(1)

    # Create diagrams
    print("="*60)
    print("CREATING DIAGRAMS")
    print("="*60 + "\n")

    if args.format == 'mermaid' or args.format == 'all':
        create_mermaid_diagram(filtered_data, f"{args.output}.mmd")
        print()

    if args.format == 'dot' or args.format == 'all':
        create_graphviz_dot(filtered_data, f"{args.output}.dot")
        print()

    if args.format == 'plantuml' or args.format == 'all':
        create_plantuml(filtered_data, f"{args.output}.puml")
        print()

    print("✓ Diagram creation complete!")


if __name__ == '__main__':
    main()
