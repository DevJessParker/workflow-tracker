"""Confluence Cloud integration for publishing workflow documentation."""

import os
from typing import Dict, Any, Optional
from pathlib import Path

from atlassian import Confluence

from ..models import ScanResult


class ConfluencePublisher:
    """Publishes workflow documentation to Confluence Cloud."""

    def __init__(self, config: Dict[str, str]):
        """Initialize Confluence publisher.

        Args:
            config: Confluence configuration with keys:
                - url: Confluence instance URL
                - username: User email
                - api_token: API token
                - space_key: Space key to publish to
                - parent_page_id: Optional parent page ID
        """
        self.config = config
        self.confluence = None

        # Validate configuration
        required_keys = ['url', 'username', 'api_token', 'space_key']
        for key in required_keys:
            if not config.get(key):
                raise ValueError(f"Missing required Confluence configuration: {key}")

    def _connect(self):
        """Establish connection to Confluence."""
        if self.confluence is None:
            self.confluence = Confluence(
                url=self.config['url'],
                username=self.config['username'],
                password=self.config['api_token'],  # API token is used as password
                cloud=True
            )

    def publish(self, result: ScanResult, html_file: str = None, markdown_file: str = None, json_file: str = None, auto_generate_diagrams: bool = False) -> str:
        """Publish workflow documentation to Confluence.

        Args:
            result: Scan result with workflow graph
            html_file: Path to HTML visualization file
            markdown_file: Path to Markdown documentation file
            json_file: Path to JSON data file
            auto_generate_diagrams: If True, auto-generate and embed Mermaid diagrams

        Returns:
            URL of the created/updated Confluence page
        """
        self._connect()

        # Generate page title
        repo_name = os.path.basename(result.repository_path)
        page_title = f"Workflow Documentation - {repo_name}"

        # Build page content
        content = self._build_page_content(result, html_file, markdown_file, json_file, auto_generate_diagrams)

        # Check if page already exists
        space_key = self.config['space_key']
        existing_page = self._find_page(space_key, page_title)

        if existing_page:
            # Update existing page
            page_id = existing_page['id']
            print(f"Updating existing Confluence page: {page_title}")

            self.confluence.update_page(
                page_id=page_id,
                title=page_title,
                body=content,
                representation='storage'
            )

            page_url = f"{self.config['url']}/wiki/spaces/{space_key}/pages/{page_id}"

        else:
            # Create new page
            print(f"Creating new Confluence page: {page_title}")

            parent_page_id = self.config.get('parent_page_id')

            new_page = self.confluence.create_page(
                space=space_key,
                title=page_title,
                body=content,
                parent_id=parent_page_id,
                representation='storage'
            )

            page_id = new_page['id']
            page_url = f"{self.config['url']}/wiki/spaces/{space_key}/pages/{page_id}"

        # Attach files
        if html_file and os.path.exists(html_file):
            self._attach_file(page_id, html_file, 'workflow_graph.html')

        if json_file and os.path.exists(json_file):
            self._attach_file(page_id, json_file, 'workflow_graph.json')

        print(f"✓ Published to Confluence: {page_url}")
        return page_url

    def _find_page(self, space_key: str, title: str) -> Optional[Dict]:
        """Find existing page by title.

        Args:
            space_key: Space key
            title: Page title

        Returns:
            Page data or None if not found
        """
        try:
            result = self.confluence.get_page_by_title(
                space=space_key,
                title=title,
                expand='version'
            )
            return result
        except Exception:
            return None

    def _build_page_content(self, result: ScanResult, html_file: str = None, markdown_file: str = None, json_file: str = None, auto_generate_diagrams: bool = False) -> str:
        """Build Confluence page content in storage format (XHTML).

        Args:
            result: Scan result
            html_file: Path to HTML visualization
            markdown_file: Path to Markdown documentation
            json_file: Path to JSON data file
            auto_generate_diagrams: If True, auto-generate and embed Mermaid diagrams

        Returns:
            Confluence storage format content
        """
        from datetime import datetime

        content = []

        # Header
        content.append('<h1>Workflow Documentation</h1>')
        content.append(f'<p><strong>Repository:</strong> <code>{result.repository_path}</code></p>')
        content.append(f'<p><strong>Last Updated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>')
        content.append(f'<p><strong>Files Scanned:</strong> {result.files_scanned}</p>')
        content.append(f'<p><strong>Workflow Nodes:</strong> {len(result.graph.nodes)}</p>')
        content.append(f'<p><strong>Workflow Edges:</strong> {len(result.graph.edges)}</p>')
        content.append('<hr />')

        # Add links to attachments
        if html_file or json_file:
            content.append('<h2>Downloads</h2>')
            content.append('<p>The following files are attached to this page:</p>')
            content.append('<ul>')
            if html_file:
                content.append('<li><strong>workflow_graph.html</strong> - Interactive visualization (download and open in browser)</li>')
            if json_file:
                content.append('<li><strong>workflow_graph.json</strong> - Complete workflow data in JSON format</li>')
            content.append('</ul>')
            content.append('<hr />')

        # Summary statistics
        content.append('<h2>Summary</h2>')
        content.append(self._build_summary_table(result))
        content.append('<hr />')

        # Auto-generated diagrams (if enabled)
        if auto_generate_diagrams:
            diagrams_html = self._generate_diagrams(result)
            if diagrams_html:
                content.append('<h2>Workflow Diagrams</h2>')
                content.append(diagrams_html)
                content.append('<hr />')

        # Detailed workflow nodes (limited to avoid size issues)
        content.append('<h2>Workflow Operations (Sample)</h2>')

        # Add note about data size
        total_nodes = len(result.graph.nodes)
        if total_nodes > 1000:
            content.append(f'<ac:structured-macro ac:name="info">')
            content.append('<ac:rich-text-body>')
            content.append(f'<p>This repository contains <strong>{total_nodes:,}</strong> workflow nodes. ')
            content.append('To keep this page manageable, only a sample of operations is shown below. ')
            content.append('Download the <strong>workflow_graph.json</strong> attachment for complete details.</p>')
            content.append('</ac:rich-text-body>')
            content.append('</ac:structured-macro>')
            content.append('<br />')

        content.append(self._build_workflow_details(result))

        return ''.join(content)

    def _build_summary_table(self, result: ScanResult) -> str:
        """Build summary statistics table.

        Args:
            result: Scan result

        Returns:
            HTML table
        """
        from collections import Counter

        # Count nodes by type
        type_counts = Counter(node.type.value for node in result.graph.nodes)

        rows = []
        for workflow_type, count in sorted(type_counts.items()):
            type_display = workflow_type.replace('_', ' ').title()
            rows.append(f'<tr><td>{type_display}</td><td>{count}</td></tr>')

        table = f'''
        <table>
            <thead>
                <tr>
                    <th>Workflow Type</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        '''

        return table

    def _build_workflow_details(self, result: ScanResult, max_nodes_per_type: int = 50) -> str:
        """Build detailed workflow operation listings.

        Args:
            result: Scan result
            max_nodes_per_type: Maximum number of nodes to show per type (to avoid page size issues)

        Returns:
            HTML content
        """
        from collections import defaultdict

        # Group nodes by type
        nodes_by_type = defaultdict(list)
        for node in result.graph.nodes:
            nodes_by_type[node.type].append(node)

        content = []

        for workflow_type, nodes in sorted(nodes_by_type.items(), key=lambda x: x[0].value):
            type_display = workflow_type.value.replace('_', ' ').title()

            # Limit nodes to display
            nodes_to_show = sorted(nodes, key=lambda n: n.location.file_path)[:max_nodes_per_type]
            showing_all = len(nodes) <= max_nodes_per_type

            title = f'{type_display} ({len(nodes)} operations'
            if not showing_all:
                title += f', showing first {max_nodes_per_type}'
            title += ')'

            content.append(f'<h3>{title}</h3>')
            content.append('<ac:structured-macro ac:name="expand">')
            content.append('<ac:parameter ac:name="title">View Details</ac:parameter>')
            content.append('<ac:rich-text-body>')

            if not showing_all:
                content.append('<ac:structured-macro ac:name="info">')
                content.append('<ac:rich-text-body>')
                content.append(f'<p>Showing first {max_nodes_per_type} of {len(nodes)} operations. ')
                content.append('Download the JSON attachment for complete data.</p>')
                content.append('</ac:rich-text-body>')
                content.append('</ac:structured-macro>')

            # Create table for this type
            content.append('<table>')
            content.append('<thead><tr>')
            content.append('<th>Name</th>')
            content.append('<th>Location</th>')
            content.append('<th>Details</th>')
            content.append('</tr></thead>')
            content.append('<tbody>')

            for node in nodes_to_show:
                details = []

                if node.table_name:
                    details.append(f'Table: <code>{node.table_name}</code>')
                if node.endpoint:
                    details.append(f'Endpoint: <code>{node.endpoint}</code>')
                if node.method:
                    details.append(f'Method: <code>{node.method}</code>')
                if node.queue_name:
                    details.append(f'Queue: <code>{node.queue_name}</code>')

                details_html = '<br />'.join(details) if details else node.description

                content.append('<tr>')
                content.append(f'<td><strong>{node.name}</strong></td>')
                content.append(f'<td><code>{node.location}</code></td>')
                content.append(f'<td>{details_html}</td>')
                content.append('</tr>')

            content.append('</tbody></table>')
            content.append('</ac:rich-text-body>')
            content.append('</ac:structured-macro>')

        return ''.join(content)

    def _attach_file(self, page_id: str, file_path: str, attachment_name: str = None):
        """Attach a file to a Confluence page.

        Args:
            page_id: Page ID
            file_path: Path to file to attach
            attachment_name: Name for attachment (defaults to filename)
        """
        try:
            if attachment_name is None:
                attachment_name = os.path.basename(file_path)

            self.confluence.attach_file(
                filename=file_path,
                name=attachment_name,
                content_type=None,
                page_id=page_id,
                comment='Workflow visualization'
            )

            print(f"  ✓ Attached file: {attachment_name}")

        except Exception as e:
            print(f"  Warning: Could not attach file {attachment_name}: {str(e)}")

    def _generate_diagrams(self, result: ScanResult) -> str:
        """Generate Mermaid diagrams for configured modules, tables, and endpoints.

        Args:
            result: Scan result with workflow graph

        Returns:
            HTML content with embedded Mermaid diagrams
        """
        diagram_config = self.config.get('auto_diagrams', {})
        if not diagram_config:
            return ''

        modules = diagram_config.get('modules', [])
        tables = diagram_config.get('tables', [])
        endpoints = diagram_config.get('endpoints', [])
        max_nodes = diagram_config.get('max_nodes_per_diagram', 50)

        content = []

        # Add info about auto-generated diagrams
        content.append('<ac:structured-macro ac:name="info">')
        content.append('<ac:rich-text-body>')
        content.append('<p>These diagrams were auto-generated based on your configuration. ')
        content.append('They show focused views of specific workflows to help understand data flow.</p>')
        content.append('</ac:rich-text-body>')
        content.append('</ac:structured-macro>')
        content.append('<br />')

        # Generate diagrams for each module
        for module in modules:
            print(f"  Generating diagram for module: {module}")
            diagram_html = self._create_module_diagram(result, module, max_nodes)
            if diagram_html:
                content.append(diagram_html)

        # Generate diagrams for each table
        for table in tables:
            print(f"  Generating diagram for table: {table}")
            diagram_html = self._create_table_diagram(result, table, max_nodes)
            if diagram_html:
                content.append(diagram_html)

        # Generate diagrams for each endpoint
        for endpoint in endpoints:
            print(f"  Generating diagram for endpoint: {endpoint}")
            diagram_html = self._create_endpoint_diagram(result, endpoint, max_nodes)
            if diagram_html:
                content.append(diagram_html)

        if not content or len(content) == 2:  # Only info banner, no diagrams
            return ''

        return ''.join(content)

    def _create_module_diagram(self, result: ScanResult, module_path: str, max_nodes: int) -> str:
        """Create a Mermaid diagram for a specific module.

        Args:
            result: Scan result
            module_path: Module path to filter
            max_nodes: Maximum nodes to include

        Returns:
            HTML with Mermaid diagram
        """
        # Filter nodes to this module
        filtered_nodes = [
            node for node in result.graph.nodes
            if module_path in node.location.file_path
        ][:max_nodes]

        if not filtered_nodes:
            return ''

        node_ids = {node.id for node in filtered_nodes}
        filtered_edges = [
            edge for edge in result.graph.edges
            if edge.source in node_ids and edge.target in node_ids
        ]

        mermaid_code = self._build_mermaid_diagram(filtered_nodes, filtered_edges, f"Module: {module_path}")
        return self._wrap_mermaid_in_confluence(mermaid_code, f"Workflow: {module_path}")

    def _create_table_diagram(self, result: ScanResult, table_name: str, max_nodes: int) -> str:
        """Create a Mermaid diagram for a specific database table.

        Args:
            result: Scan result
            table_name: Table name to filter
            max_nodes: Maximum nodes to include

        Returns:
            HTML with Mermaid diagram
        """
        # Filter nodes that operate on this table
        filtered_nodes = [
            node for node in result.graph.nodes
            if node.table_name and table_name.lower() in node.table_name.lower()
        ][:max_nodes]

        if not filtered_nodes:
            return ''

        node_ids = {node.id for node in filtered_nodes}
        filtered_edges = [
            edge for edge in result.graph.edges
            if edge.source in node_ids and edge.target in node_ids
        ]

        mermaid_code = self._build_mermaid_diagram(filtered_nodes, filtered_edges, f"Table: {table_name}")
        return self._wrap_mermaid_in_confluence(mermaid_code, f"Database Table: {table_name}")

    def _create_endpoint_diagram(self, result: ScanResult, endpoint: str, max_nodes: int) -> str:
        """Create a Mermaid diagram for a specific API endpoint.

        Args:
            result: Scan result
            endpoint: Endpoint to filter
            max_nodes: Maximum nodes to include

        Returns:
            HTML with Mermaid diagram
        """
        # Filter nodes for this endpoint
        filtered_nodes = [
            node for node in result.graph.nodes
            if node.endpoint and endpoint in node.endpoint
        ][:max_nodes]

        if not filtered_nodes:
            return ''

        node_ids = {node.id for node in filtered_nodes}
        filtered_edges = [
            edge for edge in result.graph.edges
            if edge.source in node_ids and edge.target in node_ids
        ]

        mermaid_code = self._build_mermaid_diagram(filtered_nodes, filtered_edges, f"Endpoint: {endpoint}")
        return self._wrap_mermaid_in_confluence(mermaid_code, f"API Endpoint: {endpoint}")

    def _build_mermaid_diagram(self, nodes: list, edges: list, title: str) -> str:
        """Build Mermaid flowchart code.

        Args:
            nodes: List of workflow nodes
            edges: List of workflow edges
            title: Diagram title

        Returns:
            Mermaid code
        """
        lines = []
        lines.append("flowchart TD")

        # Color scheme by type
        type_colors = {
            'api_call': '#2196F3',
            'database_read': '#4CAF50',
            'database_write': '#8BC34A',
            'file_read': '#FF9800',
            'file_write': '#FF5722',
            'message_send': '#9C27B0',
            'message_receive': '#673AB7',
            'data_transform': '#FFEB3B'
        }

        # Create node definitions
        node_id_map = {}
        for i, node in enumerate(nodes):
            node_id = f"N{i}"
            node_id_map[node.id] = node_id

            # Create label (truncate if too long)
            label = node.name[:40]
            if node.table_name:
                label += f"<br/>{node.table_name}"
            elif node.endpoint:
                label += f"<br/>{node.endpoint[:30]}"

            lines.append(f'    {node_id}["{label}"]')

            # Add styling
            node_type = node.type.value if hasattr(node.type, 'value') else str(node.type)
            if node_type in type_colors:
                lines.append(f"    style {node_id} fill:{type_colors[node_type]}")

        # Create edges
        for edge in edges:
            source_id = node_id_map.get(edge.source)
            target_id = node_id_map.get(edge.target)
            if source_id and target_id:
                label = edge.edge_type[:20] if hasattr(edge, 'edge_type') else ''
                if label:
                    lines.append(f"    {source_id} -->|{label}| {target_id}")
                else:
                    lines.append(f"    {source_id} --> {target_id}")

        return '\n'.join(lines)

    def _wrap_mermaid_in_confluence(self, mermaid_code: str, title: str) -> str:
        """Wrap Mermaid code in Confluence macro format.

        Args:
            mermaid_code: Mermaid diagram code
            title: Diagram title

        Returns:
            Confluence storage format HTML
        """
        content = []
        content.append(f'<h3>{title}</h3>')
        content.append('<ac:structured-macro ac:name="code">')
        content.append('<ac:parameter ac:name="language">mermaid</ac:parameter>')
        content.append('<ac:parameter ac:name="theme">Midnight</ac:parameter>')
        content.append('<ac:plain-text-body><![CDATA[')
        content.append(mermaid_code)
        content.append(']]></ac:plain-text-body>')
        content.append('</ac:structured-macro>')
        content.append('<p><em>Note: Install the "Mermaid Diagrams" app in Confluence to render this diagram.</em></p>')
        content.append('<br />')
        return ''.join(content)
