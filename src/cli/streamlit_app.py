"""Streamlit GUI for Workflow Tracker."""

import streamlit as st
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config_loader import Config
from src.graph.builder import WorkflowGraphBuilder
from src.graph.renderer import WorkflowRenderer
from src.models import WorkflowType


st.set_page_config(
    page_title="Workflow Tracker",
    page_icon="🔄",
    layout="wide"
)


def main():
    """Main Streamlit app."""
    st.title("🔄 Workflow Tracker")
    st.markdown("Analyze and visualize data workflows in your codebase")

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


def display_results(result):
    """Display scan results."""
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
    main()
