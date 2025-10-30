"""Workflow graph renderer - creates visualizations in multiple formats."""

import json
import os
from pathlib import Path
from typing import Dict, Any, List

import networkx as nx
from ..models import WorkflowGraph, WorkflowType, ScanResult


class WorkflowRenderer:
    """Renders workflow graphs to various output formats."""

    # Color scheme for different workflow types
    TYPE_COLORS = {
        WorkflowType.DATABASE_READ: '#4CAF50',      # Green
        WorkflowType.DATABASE_WRITE: '#FF9800',     # Orange
        WorkflowType.API_CALL: '#2196F3',           # Blue
        WorkflowType.FILE_READ: '#9C27B0',          # Purple
        WorkflowType.FILE_WRITE: '#E91E63',         # Pink
        WorkflowType.MESSAGE_SEND: '#00BCD4',       # Cyan
        WorkflowType.MESSAGE_RECEIVE: '#009688',    # Teal
        WorkflowType.DATA_TRANSFORM: '#FFEB3B',     # Yellow
        WorkflowType.CACHE_READ: '#795548',         # Brown
        WorkflowType.CACHE_WRITE: '#607D8B',        # Blue Grey
    }

    def __init__(self, config: Dict[str, Any]):
        """Initialize renderer.

        Args:
            config: Output configuration
        """
        self.config = config
        self.output_dir = config.get('output', {}).get('directory', './output')
        os.makedirs(self.output_dir, exist_ok=True)

    def render(self, result: ScanResult, formats: List[str] = None) -> Dict[str, str]:
        """Render workflow graph in multiple formats.

        Args:
            result: Scan result containing workflow graph
            formats: List of formats to render (html, png, svg, json, markdown)

        Returns:
            Dictionary mapping format to output file path
        """
        if formats is None:
            formats = self.config.get('output', {}).get('formats', ['html', 'json'])

        output_files = {}

        # Convert to NetworkX graph for easier manipulation
        nx_graph = self._to_networkx(result.graph)

        for fmt in formats:
            try:
                if fmt == 'html':
                    output_files['html'] = self._render_html(result, nx_graph)
                elif fmt == 'png':
                    output_files['png'] = self._render_image(nx_graph, 'png')
                elif fmt == 'svg':
                    output_files['svg'] = self._render_image(nx_graph, 'svg')
                elif fmt == 'json':
                    output_files['json'] = self._render_json(result)
                elif fmt == 'markdown':
                    output_files['markdown'] = self._render_markdown(result)
                else:
                    print(f"Warning: Unknown format '{fmt}'")
            except Exception as e:
                print(f"Error rendering {fmt}: {str(e)}")

        return output_files

    def _to_networkx(self, graph: WorkflowGraph) -> nx.DiGraph:
        """Convert WorkflowGraph to NetworkX directed graph.

        Args:
            graph: Workflow graph

        Returns:
            NetworkX DiGraph
        """
        G = nx.DiGraph()

        # Add nodes
        for node in graph.nodes:
            G.add_node(
                node.id,
                label=node.name,
                type=node.type.value,
                color=self.TYPE_COLORS.get(node.type, '#999999'),
                location=str(node.location),
                description=node.description,
                code_snippet=node.code_snippet or '',
            )

        # Add edges
        for edge in graph.edges:
            G.add_edge(
                edge.source,
                edge.target,
                label=edge.label or ''
            )

        return G

    def _render_html(self, result: ScanResult, nx_graph: nx.DiGraph) -> str:
        """Render interactive HTML visualization using Plotly.

        Args:
            result: Scan result
            nx_graph: NetworkX graph

        Returns:
            Path to output HTML file
        """
        import plotly.graph_objects as go

        # Use spring layout for positioning
        pos = nx.spring_layout(nx_graph, k=2, iterations=50)

        # Create edge traces
        edge_trace = go.Scatter(
            x=[],
            y=[],
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        for edge in nx_graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += tuple([x0, x1, None])
            edge_trace['y'] += tuple([y0, y1, None])

        # Create node traces
        node_trace = go.Scatter(
            x=[],
            y=[],
            mode='markers+text',
            hoverinfo='text',
            marker=dict(
                showscale=False,
                size=20,
                color=[],
                line=dict(width=2, color='white')
            ),
            text=[],
            textposition="top center",
            hovertext=[]
        )

        for node in nx_graph.nodes():
            x, y = pos[node]
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])

            node_data = nx_graph.nodes[node]
            node_trace['marker']['color'] += tuple([node_data.get('color', '#999')])

            # Node label
            label = node_data.get('label', node)
            if len(label) > 30:
                label = label[:27] + '...'
            node_trace['text'] += tuple([label])

            # Hover text
            hover_text = f"<b>{node_data.get('label')}</b><br>"
            hover_text += f"Type: {node_data.get('type')}<br>"
            hover_text += f"Location: {node_data.get('location')}<br>"
            hover_text += f"<br>{node_data.get('description')}"

            if node_data.get('code_snippet'):
                snippet = node_data['code_snippet'][:200]
                hover_text += f"<br><br><code>{snippet}</code>"

            node_trace['hovertext'] += tuple([hover_text])

        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(
                    text=f"Workflow Graph - {result.repository_path}<br>" +
                         f"<sub>{len(result.graph.nodes)} nodes, {len(result.graph.edges)} edges</sub>",
                    x=0.5,
                    xanchor='center'
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=80),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=800,
            )
        )

        # Save to file
        output_path = os.path.join(self.output_dir, 'workflow_graph.html')
        fig.write_html(output_path)

        print(f"HTML visualization saved to: {output_path}")
        return output_path

    def _render_image(self, nx_graph: nx.DiGraph, format: str = 'png') -> str:
        """Render static image using Graphviz.

        Args:
            nx_graph: NetworkX graph
            format: Output format (png or svg)

        Returns:
            Path to output file
        """
        try:
            from networkx.drawing.nx_agraph import to_agraph

            # Convert to Graphviz AGraph
            A = to_agraph(nx_graph)
            A.graph_attr['rankdir'] = 'TB'  # Top to bottom
            A.graph_attr['splines'] = 'ortho'  # Orthogonal edges
            A.node_attr['shape'] = 'box'
            A.node_attr['style'] = 'rounded,filled'
            A.node_attr['fontname'] = 'Arial'
            A.node_attr['fontsize'] = '10'

            # Style nodes
            for node in A.nodes():
                node_data = nx_graph.nodes[node]
                node.attr['fillcolor'] = node_data.get('color', '#999999')
                node.attr['label'] = node_data.get('label', node)

            # Save to file
            output_path = os.path.join(self.output_dir, f'workflow_graph.{format}')
            A.draw(output_path, format=format, prog='dot')

            print(f"{format.upper()} image saved to: {output_path}")
            return output_path

        except ImportError:
            print(f"Warning: pygraphviz not available. Skipping {format} rendering.")
            print("Install with: pip install pygraphviz")
            return None

    def _render_json(self, result: ScanResult) -> str:
        """Render graph data as JSON.

        Args:
            result: Scan result

        Returns:
            Path to output JSON file
        """
        data = {
            'repository': result.repository_path,
            'scan_time_seconds': result.scan_time_seconds,
            'files_scanned': result.files_scanned,
            'nodes': [
                {
                    'id': node.id,
                    'type': node.type.value,
                    'name': node.name,
                    'description': node.description,
                    'location': {
                        'file': node.location.file_path,
                        'line': node.location.line_number,
                    },
                    'table_name': node.table_name,
                    'endpoint': node.endpoint,
                    'method': node.method,
                    'file_path': node.file_path,
                    'queue_name': node.queue_name,
                    'metadata': node.metadata,
                }
                for node in result.graph.nodes
            ],
            'edges': [
                {
                    'source': edge.source,
                    'target': edge.target,
                    'label': edge.label,
                    'metadata': edge.metadata,
                }
                for edge in result.graph.edges
            ],
            'errors': result.errors,
            'warnings': result.warnings,
        }

        output_path = os.path.join(self.output_dir, 'workflow_graph.json')
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"JSON data saved to: {output_path}")
        return output_path

    def _render_markdown(self, result: ScanResult) -> str:
        """Render workflow documentation as Markdown.

        Args:
            result: Scan result

        Returns:
            Path to output Markdown file
        """
        lines = []

        # Header
        lines.append("# Workflow Documentation\n")
        lines.append(f"**Repository:** `{result.repository_path}`\n")
        lines.append(f"**Scan Date:** {self._get_current_date()}\n")
        lines.append(f"**Files Scanned:** {result.files_scanned}\n")
        lines.append(f"**Nodes Found:** {len(result.graph.nodes)}\n")
        lines.append(f"**Edges Found:** {len(result.graph.edges)}\n")
        lines.append("")

        # Group nodes by type
        from collections import defaultdict
        nodes_by_type = defaultdict(list)

        for node in result.graph.nodes:
            nodes_by_type[node.type].append(node)

        # Document each type
        for workflow_type, nodes in sorted(nodes_by_type.items(), key=lambda x: x[0].value):
            lines.append(f"## {workflow_type.value.replace('_', ' ').title()}\n")
            lines.append(f"Found {len(nodes)} operations of this type.\n")

            for node in sorted(nodes, key=lambda n: n.location.file_path):
                lines.append(f"### {node.name}\n")
                lines.append(f"**Location:** `{node.location}`\n")
                lines.append(f"**Description:** {node.description}\n")

                if node.table_name:
                    lines.append(f"**Table:** `{node.table_name}`\n")
                if node.endpoint:
                    lines.append(f"**Endpoint:** `{node.endpoint}`\n")
                if node.method:
                    lines.append(f"**Method:** `{node.method}`\n")
                if node.queue_name:
                    lines.append(f"**Queue:** `{node.queue_name}`\n")

                if node.code_snippet:
                    lines.append("\n**Code:**\n```")
                    lines.append(node.code_snippet)
                    lines.append("```\n")

                lines.append("")

        output_path = os.path.join(self.output_dir, 'workflow_documentation.md')
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))

        print(f"Markdown documentation saved to: {output_path}")
        return output_path

    def _get_current_date(self) -> str:
        """Get current date as string."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
