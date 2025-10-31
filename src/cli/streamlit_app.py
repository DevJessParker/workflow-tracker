"""Streamlit GUI for Workflow Tracker."""

import streamlit as st
import os
import sys
import traceback
from pathlib import Path

# Startup diagnostic
print("=" * 60)
print("WORKFLOW TRACKER GUI - STARTING UP")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Script location: {__file__}")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
print(f"Added to sys.path: {str(Path(__file__).parent.parent.parent)}")

# Try importing with error handling
print("\nAttempting to import modules...")
try:
    from src.config_loader import Config
    from src.graph.builder import WorkflowGraphBuilder
    from src.graph.renderer import WorkflowRenderer
    from src.models import WorkflowType
    IMPORTS_OK = True
    IMPORT_ERROR = None
    print("✓ All modules imported successfully")
except Exception as e:
    IMPORTS_OK = False
    IMPORT_ERROR = str(e)
    print(f"✗ ERROR: Failed to import modules: {e}")
    traceback.print_exc()

print("=" * 60)


st.set_page_config(
    page_title="Workflow Tracker",
    page_icon="🔄",
    layout="wide"
)


def get_filter_options(result, filter_type):
    """Extract available filter options from scan results.

    Args:
        result: ScanResult object containing graph with nodes
        filter_type: One of "Module/Directory", "Database Table", "API Endpoint"

    Returns:
        Sorted list of unique values for the selected filter type
    """
    options = set()

    if filter_type == "Module/Directory":
        # Extract unique directory paths from file locations
        for node in result.graph.nodes:
            file_path = node.location.file_path
            # Get directory components (e.g., "src/services/UserService.cs" -> ["src", "src/services"])
            parts = file_path.split('/')
            for i in range(1, len(parts)):
                dir_path = '/'.join(parts[:i])
                if dir_path:
                    options.add(dir_path)
            # Also add the full file path without extension as an option
            if '.' in parts[-1]:
                file_without_ext = '/'.join(parts[:-1]) + '/' + parts[-1].rsplit('.', 1)[0]
                options.add(file_without_ext)

    elif filter_type == "Database Table":
        # Extract unique database table names
        for node in result.graph.nodes:
            if node.table_name:
                options.add(node.table_name)

    elif filter_type == "API Endpoint":
        # Extract unique API endpoints
        for node in result.graph.nodes:
            if node.endpoint:
                options.add(node.endpoint)

    # Return sorted list
    return sorted(list(options))


def main():
    """Main Streamlit app."""
    print("main() function called - rendering UI")

    st.title("🔄 Workflow Tracker")
    st.markdown("Analyze and visualize data workflows in your codebase")

    # Show import errors if any
    if not IMPORTS_OK:
        print(f"WARNING: Displaying import error to user: {IMPORT_ERROR}")
        st.error("⚠️ Failed to load required modules!")
        st.code(IMPORT_ERROR)
        st.info("This usually means there's a configuration or dependency issue. Check Docker logs for details.")
        return

    # Show status indicator
    print("Imports OK - displaying GUI")
    st.sidebar.success("✅ GUI Ready")

    # Sidebar configuration
    st.sidebar.header("Configuration")

    # Repository path
    default_repo = os.environ.get('WORKFLOW_TRACKER_REPO', '.')
    repo_path = st.sidebar.text_input(
        "Repository Path",
        value=default_repo,
        help="Path to the repository to scan"
    )

    # Scan options
    st.sidebar.subheader("Scan Options")

    detect_database = st.sidebar.checkbox("Database Operations", value=True)
    detect_api = st.sidebar.checkbox("API Calls", value=True)
    detect_files = st.sidebar.checkbox("File I/O", value=True)
    detect_messages = st.sidebar.checkbox("Message Queues", value=True)
    detect_transforms = st.sidebar.checkbox("Data Transforms", value=True)

    # File extensions
    extensions = st.sidebar.text_input(
        "File Extensions",
        value=".cs,.ts,.js",
        help="Comma-separated list of file extensions to scan"
    )

    # Scan button
    if st.sidebar.button("🔍 Scan Repository", type="primary"):
        scan_repository(
            repo_path,
            extensions.split(','),
            detect_database,
            detect_api,
            detect_files,
            detect_messages,
            detect_transforms
        )

    # Diagram generation section (only show if scan results exist)
    if 'scan_result' in st.session_state:
        st.sidebar.divider()
        st.sidebar.subheader("📊 Generate Diagrams")

        filter_type = st.sidebar.selectbox(
            "Filter By",
            ["Module/Directory", "Database Table", "API Endpoint"],
            help="Choose what to filter the diagram by"
        )

        # Get available filter options from scan results
        result = st.session_state.scan_result
        filter_options = get_filter_options(result, filter_type)

        if not filter_options:
            st.sidebar.warning(f"No {filter_type.lower()} found in scan results")
            filter_value = None
        else:
            filter_value = st.sidebar.selectbox(
                "Select Filter",
                options=filter_options,
                help=f"Select from {len(filter_options)} available {filter_type.lower()}s"
            )

        max_nodes = st.sidebar.slider(
            "Max Nodes",
            min_value=10,
            max_value=100,
            value=50,
            help="Maximum nodes to include in diagram"
        )

        if st.sidebar.button("🎨 Generate Diagram", type="secondary"):
            if filter_value:
                generate_diagram(
                    st.session_state.scan_result,
                    filter_type,
                    filter_value,
                    max_nodes
                )
            else:
                st.sidebar.error("Please select a filter value")

    # Display results if available
    if 'scan_result' in st.session_state:
        display_results(st.session_state.scan_result)


def scan_repository(repo_path, extensions, detect_db, detect_api, detect_files, detect_msg, detect_transform):
    """Scan repository and store results."""
    if not os.path.exists(repo_path):
        st.error(f"Repository path not found: {repo_path}")
        return

    with st.spinner("Scanning repository..."):
        try:
            # Build configuration
            config = {
                'scanner': {
                    'include_extensions': [ext.strip() for ext in extensions],
                    'exclude_dirs': ['node_modules', 'bin', 'obj', '.git', 'dist', 'build'],
                    'detect': {
                        'database': detect_db,
                        'api_calls': detect_api,
                        'file_io': detect_files,
                        'message_queues': detect_msg,
                        'data_transforms': detect_transform,
                    }
                },
                'output': {
                    'directory': './output',
                    'formats': ['html', 'json']
                }
            }

            # Scan repository
            builder = WorkflowGraphBuilder(config)
            result = builder.build(repo_path)

            # Render visualizations
            renderer = WorkflowRenderer(config)
            output_files = renderer.render(result)

            # Store in session state
            st.session_state.scan_result = result
            st.session_state.output_files = output_files

            st.success(f"✓ Scan complete! Found {len(result.graph.nodes)} workflow nodes.")

        except Exception as e:
            st.error(f"Error during scan: {str(e)}")
            st.code(traceback.format_exc())


def generate_diagram(result, filter_type, filter_value, max_nodes):
    """Generate a Mermaid diagram based on filter."""
    try:
        # Filter nodes based on type
        if filter_type == "Module/Directory":
            filtered_nodes = [
                node for node in result.graph.nodes
                if filter_value in node.location.file_path
            ][:max_nodes]
            diagram_title = f"Module: {filter_value}"

        elif filter_type == "Database Table":
            filtered_nodes = [
                node for node in result.graph.nodes
                if node.table_name and filter_value.lower() in node.table_name.lower()
            ][:max_nodes]
            diagram_title = f"Table: {filter_value}"

        else:  # API Endpoint
            filtered_nodes = [
                node for node in result.graph.nodes
                if node.endpoint and filter_value in node.endpoint
            ][:max_nodes]
            diagram_title = f"Endpoint: {filter_value}"

        if not filtered_nodes:
            st.sidebar.warning(f"No nodes found matching '{filter_value}'")
            return

        # Filter edges
        node_ids = {node.id for node in filtered_nodes}
        filtered_edges = [
            edge for edge in result.graph.edges
            if edge.source in node_ids and edge.target in node_ids
        ]

        # Build Mermaid diagram
        mermaid_code = build_mermaid_diagram(filtered_nodes, filtered_edges, diagram_title)

        # Store in session state
        st.session_state.generated_diagram = {
            'code': mermaid_code,
            'title': diagram_title,
            'node_count': len(filtered_nodes),
            'edge_count': len(filtered_edges)
        }

        st.sidebar.success(f"✓ Generated diagram with {len(filtered_nodes)} nodes!")

    except Exception as e:
        st.sidebar.error(f"Error generating diagram: {str(e)}")
        st.sidebar.code(traceback.format_exc())


def build_mermaid_diagram(nodes, edges, title):
    """Build Mermaid flowchart code."""
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
        label = node.name[:40].replace('"', "'")
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
            lines.append(f"    {source_id} --> {target_id}")

    return '\n'.join(lines)


def display_results(result):
    """Display scan results."""
    st.header("Scan Results")

    # Display generated diagram if available
    if 'generated_diagram' in st.session_state:
        st.subheader("📊 Generated Diagram")
        diagram = st.session_state.generated_diagram

        st.info(f"**{diagram['title']}** - {diagram['node_count']} nodes, {diagram['edge_count']} connections")

        # Display Mermaid code
        st.code(diagram['code'], language='mermaid')

        # Download button
        st.download_button(
            label="💾 Download Mermaid Code",
            data=diagram['code'],
            file_name=f"workflow_diagram_{diagram['title'].replace(':', '_').replace(' ', '_')}.mmd",
            mime='text/plain'
        )

        st.markdown("""
        **To use this diagram:**
        - Copy the code above and paste into [Mermaid Live Editor](https://mermaid.live/)
        - Add to Markdown files (GitHub, GitLab, etc.)
        - Install "Mermaid Diagrams" app in Confluence to use there
        """)

        st.divider()

    st.header("Scan Results")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Files Scanned", result.files_scanned)
    with col2:
        st.metric("Workflow Nodes", len(result.graph.nodes))
    with col3:
        st.metric("Connections", len(result.graph.edges))
    with col4:
        st.metric("Scan Time", f"{result.scan_time_seconds:.1f}s")

    # Workflow type breakdown
    st.subheader("Workflow Operations by Type")

    from collections import Counter
    type_counts = Counter(node.type.value for node in result.graph.nodes)

    if type_counts:
        import pandas as pd

        df = pd.DataFrame([
            {'Type': k.replace('_', ' ').title(), 'Count': v}
            for k, v in sorted(type_counts.items())
        ])

        st.bar_chart(df.set_index('Type'))

    # Interactive visualization
    st.subheader("Interactive Workflow Graph")

    if 'output_files' in st.session_state and 'html' in st.session_state.output_files:
        html_file = st.session_state.output_files['html']

        if os.path.exists(html_file):
            with open(html_file, 'r') as f:
                html_content = f.read()

            st.components.v1.html(html_content, height=800, scrolling=True)
        else:
            st.warning("HTML visualization file not found")

    # Detailed node listing
    st.subheader("Workflow Nodes")

    # Filter by type
    node_types = sorted(set(node.type.value for node in result.graph.nodes))
    selected_type = st.selectbox(
        "Filter by type",
        ['All'] + [t.replace('_', ' ').title() for t in node_types]
    )

    # Display nodes
    nodes_to_display = result.graph.nodes

    if selected_type != 'All':
        selected_type_value = selected_type.lower().replace(' ', '_')
        nodes_to_display = [
            node for node in result.graph.nodes
            if node.type.value == selected_type_value
        ]

    for node in sorted(nodes_to_display, key=lambda n: n.location.file_path)[:50]:  # Limit to 50
        with st.expander(f"{node.name} - {node.location}"):
            st.write(f"**Type:** {node.type.value.replace('_', ' ').title()}")
            st.write(f"**Description:** {node.description}")

            if node.table_name:
                st.write(f"**Table:** `{node.table_name}`")
            if node.endpoint:
                st.write(f"**Endpoint:** `{node.endpoint}`")
            if node.method:
                st.write(f"**Method:** `{node.method}`")
            if node.queue_name:
                st.write(f"**Queue:** `{node.queue_name}`")

            if node.code_snippet:
                st.code(node.code_snippet, language='csharp')

    if len(nodes_to_display) > 50:
        st.info(f"Showing first 50 of {len(nodes_to_display)} nodes")

    # Download options
    st.subheader("Download Results")

    if 'output_files' in st.session_state:
        cols = st.columns(len(st.session_state.output_files))

        for i, (fmt, file_path) in enumerate(st.session_state.output_files.items()):
            with cols[i]:
                if file_path and os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        st.download_button(
                            label=f"Download {fmt.upper()}",
                            data=f,
                            file_name=os.path.basename(file_path),
                            mime='application/octet-stream'
                        )


if __name__ == '__main__':
    print("\nExecuting main() function...")
    try:
        main()
        print("main() completed successfully")
    except Exception as e:
        print(f"FATAL ERROR in main(): {e}")
        traceback.print_exc()
        raise
