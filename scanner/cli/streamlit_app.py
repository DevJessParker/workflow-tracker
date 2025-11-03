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

# Add parent directory to path to enable importing scanner as a package
scanner_parent = str(Path(__file__).parent.parent.parent)  # /home/user/workflow-tracker
sys.path.insert(0, scanner_parent)
print(f"Added to sys.path: {scanner_parent}")

# Try importing with error handling - support both Docker (src.*) and standalone (scanner.*)
print("\nAttempting to import modules...")
IMPORTS_OK = False
IMPORT_ERROR = None

# Try Docker-style imports first (src.*)
try:
    from src.config_loader import Config
    from src.graph.builder import WorkflowGraphBuilder
    from src.graph.renderer import WorkflowRenderer
    from src.models import WorkflowType
    IMPORTS_OK = True
    print("✓ All modules imported successfully (Docker mode: src.*)")
except Exception as docker_error:
    print(f"✗ Docker-style imports failed: {docker_error}")
    print("Attempting standalone imports (scanner.*)...")

    # Try standalone imports (scanner.*)
    # The scanner directory must be importable as a package from scanner_parent
    try:
        from scanner.config_loader import Config
        from scanner.graph.builder import WorkflowGraphBuilder
        from scanner.graph.renderer import WorkflowRenderer
        from scanner.models import WorkflowType
        IMPORTS_OK = True
        print("✓ All modules imported successfully (Standalone mode: scanner.*)")
    except Exception as standalone_error:
        IMPORT_ERROR = f"Both import styles failed.\nDocker (src.*): {docker_error}\nStandalone (scanner.*): {standalone_error}"
        print(f"✗ ERROR: {IMPORT_ERROR}")
        print(f"\nCurrent sys.path: {sys.path[:3]}")
        traceback.print_exc()

print("=" * 60)


st.set_page_config(
    page_title="Pinata Code",
    page_icon="🪅",
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

    # Initialize dark mode state
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False

    # Dark mode toggle in sidebar
    with st.sidebar:
        st.session_state.dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)

        # Apply dark mode styling
        if st.session_state.dark_mode:
            st.markdown("""
            <style>
            /* Dark mode styles */
            .stApp {
                background-color: #0e1117;
                color: #fafafa;
            }
            .stMarkdown, .stText, p, span, label {
                color: #fafafa !important;
            }
            .stTextInput > div > div > input {
                background-color: #262730;
                color: #fafafa;
            }
            .stSelectbox > div > div > div {
                background-color: #262730;
                color: #fafafa;
            }
            div[data-baseweb="select"] > div {
                background-color: #262730;
            }
            .stExpander {
                background-color: #262730;
                border: 1px solid #464646;
            }
            .stButton > button {
                background-color: #262730;
                color: #fafafa;
            }
            .stMetric {
                background-color: #262730;
                padding: 10px;
                border-radius: 5px;
            }
            </style>
            """, unsafe_allow_html=True)

    st.title("🪅 Pinata Code")
    st.markdown("*It's what's inside that counts*")
    st.markdown("---")
    st.markdown("Analyze and visualize data workflows in your codebase")

    # Remove blue background from title
    st.markdown("""
    <style>
    h1 {
        background-color: transparent !important;
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Show import errors if any
    if not IMPORTS_OK:
        print(f"WARNING: Displaying import error to user: {IMPORT_ERROR}")
        st.error("⚠️ Failed to load required modules!")
        st.code(IMPORT_ERROR)
        st.info("This usually means there's a configuration or dependency issue. Check Docker logs for details.")
        return

    # Show status indicator
    print("Imports OK - displaying GUI")

    # Initialize session state keys if they don't exist
    if 'scan_result' not in st.session_state:
        st.session_state.scan_result = None
    if 'output_files' not in st.session_state:
        st.session_state.output_files = None
    if 'generated_diagram' not in st.session_state:
        st.session_state.generated_diagram = None
    if 'scan_running' not in st.session_state:
        st.session_state.scan_running = False
    if 'stop_scan' not in st.session_state:
        st.session_state.stop_scan = False
    if 'scan_triggered' not in st.session_state:
        st.session_state.scan_triggered = False

    # Check if scan results exist (determines which tabs to show)
    has_results = st.session_state.scan_result is not None

    # Create tabbed interface
    if not has_results:
        # Only show scan tab if no results
        tab_scan = st.tabs(["📂 Scan Repository"])[0]
        with tab_scan:
            render_scan_tab()
    else:
        # Show all tabs once scan is complete
        tab_scan, tab_viz, tab_schema, tab_analysis = st.tabs([
            "📂 Scan Repository",
            "📊 Visualizations",
            "🗄️ Database Schema",
            "📈 Data Analysis"
        ])

        with tab_scan:
            render_scan_tab()

        with tab_viz:
            render_visualizations_tab()

        with tab_schema:
            render_database_schema_tab()

        with tab_analysis:
            render_analysis_tab()


def render_scan_tab():
    """Render the scan configuration and execution tab."""
    st.header("Repository Scanner")

    # Create 2/3 and 1/3 layout
    config_col, results_col = st.columns([2, 1])

    with config_col:
        # Configuration form
        with st.form("scan_config_form"):
            st.markdown("**Configure and run workflow analysis**")

            # Repository path
            default_repo = os.environ.get('WORKFLOW_TRACKER_REPO', '.')
            repo_path = st.text_input(
                "Repository Path",
                value=default_repo,
                help="Path to the repository to scan",
                key="repo_path_input"
            )

            # File extensions
            extensions = st.text_input(
                "File Extensions",
                value=".cs,.ts,.js",
                help="Comma-separated list of file extensions to scan",
                key="extensions_input"
            )

            st.markdown("**Detection Options**")
            col1, col2 = st.columns(2)
            with col1:
                detect_database = st.checkbox("Database Operations", value=True, key="detect_db_checkbox")
                detect_api = st.checkbox("API Calls", value=True, key="detect_api_checkbox")
                detect_files = st.checkbox("File I/O", value=True, key="detect_files_checkbox")
            with col2:
                detect_messages = st.checkbox("Message Queues", value=True, key="detect_msg_checkbox")
                detect_transforms = st.checkbox("Data Transforms", value=True, key="detect_transforms_checkbox")

            # Scan button inside form (disabled when scanning)
            submitted = st.form_submit_button(
                "🔍 Start Scan" if not st.session_state.scan_running else "⏳ Scanning...",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.scan_running
            )

        # Process scan when form is submitted
        if submitted and not st.session_state.scan_running:
            # Store scan parameters in session state
            st.session_state.scan_params = {
                'repo_path': repo_path,
                'extensions': extensions.split(','),
                'detect_database': detect_database,
                'detect_api': detect_api,
                'detect_files': detect_files,
                'detect_messages': detect_messages,
                'detect_transforms': detect_transforms
            }
            st.session_state.scan_running = True
            st.session_state.scan_triggered = True  # Flag that scan should start
            st.session_state.stop_scan = False
            st.rerun()

        # Progress section and scan execution (only when scan_triggered is True)
        if st.session_state.scan_running and st.session_state.scan_triggered:
            st.divider()
            st.markdown("### Scanning Progress")

            # Reset triggered flag to prevent re-execution on rerun
            st.session_state.scan_triggered = False

            # Stop button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("⏹️ Stop Scan", type="secondary", use_container_width=True, key="stop_scan_button"):
                    st.session_state.stop_scan = True

            # Run the scan with stored parameters
            if hasattr(st.session_state, 'scan_params'):
                params = st.session_state.scan_params
                scan_repository(
                    params['repo_path'],
                    params['extensions'],
                    params['detect_database'],
                    params['detect_api'],
                    params['detect_files'],
                    params['detect_messages'],
                    params['detect_transforms']
                )
        elif st.session_state.scan_running and not st.session_state.scan_triggered:
            # Scan is running but not triggered this cycle (shouldn't happen, but safety check)
            st.info("⏳ Scan in progress...")

    with results_col:
        # Show results summary if available
        if st.session_state.scan_result is not None:
            result = st.session_state.scan_result
            st.success("✅ Scan Complete!")

            st.metric("Files Scanned", f"{result.files_scanned:,}")
            st.metric("Workflow Nodes", f"{len(result.graph.nodes):,}")
            st.metric("Connections", f"{len(result.graph.edges):,}")
            st.metric("Scan Time", f"{result.scan_time_seconds:.1f}s")

            if result.errors:
                with st.expander(f"⚠️ Errors ({len(result.errors)})", expanded=False):
                    for error in result.errors[:10]:  # Show first 10
                        st.text(error)
        else:
            st.info("Run a scan to see results here")


def render_mermaid(mermaid_code, height=600):
    """Render Mermaid diagram using mermaid.js."""
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose',
                flowchart: {{
                    useMaxWidth: true,
                    htmlLabels: true,
                    curve: 'basis'
                }},
                er: {{
                    useMaxWidth: true
                }}
            }});
        </script>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                background: white;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}
            .mermaid {{
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="mermaid">
{mermaid_code}
        </div>
    </body>
    </html>
    """
    st.components.v1.html(html_template, height=height, scrolling=True)


def render_visualizations_tab():
    """Render the visualizations tab with diagram generation."""
    st.header("Workflow Visualizations")
    st.markdown("Generate and view workflow diagrams filtered by module, table, or endpoint")

    result = st.session_state.scan_result

    # Filter controls
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        filter_type = st.selectbox(
            "Filter By",
            ["Module/Directory", "Database Table", "API Endpoint"],
            key="viz_filter_type",
            help="Choose what to filter the diagram by"
        )

    # Cache filter options in session state to prevent recalculation on every interaction
    cache_key = f"filter_options_{filter_type}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = get_filter_options(result, filter_type)

    filter_options = st.session_state[cache_key]

    with col2:
        if not filter_options:
            st.warning(f"No {filter_type.lower()} found in scan results")
            filter_value = None
        else:
            filter_value = st.selectbox(
                "Select Filter",
                options=filter_options,
                key="viz_filter_value",
                help=f"Select from {len(filter_options)} available {filter_type.lower()}s"
            )

    with col3:
        max_nodes = st.number_input(
            "Max Nodes",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            help="Maximum nodes to include in diagram"
        )

    st.divider()

    # Generate button
    if st.button("🎨 Generate Diagram", type="primary", use_container_width=True):
        if filter_value:
            generate_and_render_diagram(result, filter_type, filter_value, max_nodes)
        else:
            st.error("Please select a filter value")

    # Display generated diagram if available
    if st.session_state.generated_diagram is not None:
        diagram_data = st.session_state.generated_diagram
        st.subheader(diagram_data['title'])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nodes", diagram_data['node_count'])
        with col2:
            st.metric("Connections", diagram_data['edge_count'])
        with col3:
            st.metric("Complexity", f"{diagram_data['edge_count'] / max(diagram_data['node_count'], 1):.1f}")

        st.divider()

        # Render Mermaid diagram
        st.subheader("Interactive Diagram")
        render_mermaid(diagram_data['code'], height=700)

        # Download options
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Mermaid Code",
                data=diagram_data['code'],
                file_name=f"workflow_diagram_{filter_value.replace('/', '_')}.mmd",
                mime="text/plain"
            )
        with col2:
            # Also provide markdown version
            markdown_content = f"# {diagram_data['title']}\n\n```mermaid\n{diagram_data['code']}\n```"
            st.download_button(
                label="📥 Download as Markdown",
                data=markdown_content,
                file_name=f"workflow_diagram_{filter_value.replace('/', '_')}.md",
                mime="text/markdown"
            )


def render_database_schema_tab():
    """Render the database schema analysis tab."""
    st.header("Database Schema Analysis")
    st.markdown("Explore database tables, relationships, and detected operations")

    result = st.session_state.scan_result

    # Extract database-related nodes
    db_nodes = [
        node for node in result.graph.nodes
        if node.type in [WorkflowType.DATABASE_READ, WorkflowType.DATABASE_WRITE]
    ]

    if not db_nodes:
        st.warning("No database operations detected in the scan.")
        st.info("Make sure 'Database Operations' detection was enabled during scanning.")
        return

    # Analyze database schema
    schema_info = analyze_database_schema(db_nodes, result.graph.edges)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tables Detected", len(schema_info['tables']))
    with col2:
        st.metric("Read Operations", schema_info['total_reads'])
    with col3:
        st.metric("Write Operations", schema_info['total_writes'])
    with col4:
        st.metric("Table Relationships", len(schema_info['relationships']))

    st.divider()

    # Search bar for filtering tables
    st.subheader("Tables & Operations")

    col_search, col_checkbox = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Tables", placeholder="Type to filter tables...", key="table_search")
    with col_checkbox:
        include_related = st.checkbox("Include related tables", value=False, key="include_related")

    # Filter tables based on search
    filtered_tables = {}
    if search_query:
        # First, get directly matching tables
        direct_matches = {
            name: data for name, data in schema_info['tables'].items()
            if search_query.lower() in name.lower()
        }
        filtered_tables.update(direct_matches)

        # If include_related is checked, add related tables
        if include_related:
            related_tables = set()
            for table_name, table_data in direct_matches.items():
                # Add tables this table relates to
                for rel in table_data.get('related_tables', []):
                    related_tables.add(rel['table'])

                # Add tables that relate to this table (reverse lookup)
                for other_name, other_data in schema_info['tables'].items():
                    for rel in other_data.get('related_tables', []):
                        if rel['table'] == table_name:
                            related_tables.add(other_name)

            # Add related tables to filtered results
            for related_name in related_tables:
                if related_name in schema_info['tables'] and related_name not in filtered_tables:
                    filtered_tables[related_name] = schema_info['tables'][related_name]
    else:
        # No search query - show all tables
        filtered_tables = schema_info['tables']

    if not filtered_tables:
        st.warning(f"No tables found matching '{search_query}'")
    else:
        if search_query:
            st.caption(f"Showing {len(filtered_tables)} of {len(schema_info['tables'])} tables")
        else:
            st.caption(f"Showing all {len(filtered_tables)} tables")

    for table_name, table_data in sorted(filtered_tables.items()):
        with st.expander(f"📊 {table_name}", expanded=False):
            # Operations Breakdown - Styled Circles
            st.markdown("### Operations Breakdown")

            # Create three circles with counts (rainbow theme colors)
            circle_html = f"""
            <div style="display: flex; justify-content: center; gap: 40px; margin: 20px 0;">
                <div style="text-align: center;">
                    <div style="
                        width: 100px;
                        height: 100px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #48dbfb, #0abde3);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 28px;
                        font-weight: bold;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                    ">{table_data['read_count']}</div>
                    <div style="margin-top: 10px; font-weight: 500; color: #0abde3;">Reads</div>
                </div>
                <div style="text-align: center;">
                    <div style="
                        width: 100px;
                        height: 100px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #f5576c, #feca57);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 28px;
                        font-weight: bold;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                    ">{table_data['write_count']}</div>
                    <div style="margin-top: 10px; font-weight: 500; color: #f5576c;">Writes</div>
                </div>
                <div style="text-align: center;">
                    <div style="
                        width: 100px;
                        height: 100px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 28px;
                        font-weight: bold;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                    ">{table_data['total_operations']}</div>
                    <div style="margin-top: 10px; font-weight: 500; color: #764ba2;">Total</div>
                </div>
            </div>
            """
            st.markdown(circle_html, unsafe_allow_html=True)

            # Model/Schema Definition Path
            if table_data.get('model_path'):
                st.markdown("### Model Definition")
                st.code(table_data['model_path'], language="text")

            # Table Structure (JSON)
            if table_data.get('columns'):
                st.markdown("### Table Structure")
                import json
                structure = {
                    "table": table_name,
                    "columns": table_data['columns'],
                    "relationships": table_data.get('relationships', [])
                }
                st.json(structure)

            # Related Tables
            if table_data.get('related_tables'):
                st.markdown("### Related Tables")
                for rel in table_data['related_tables']:
                    rel_type_icon = "🔗" if rel['type'] == "belongs_to" else "📊" if rel['type'] == "has_many" else "🔄"
                    st.write(f"{rel_type_icon} **{rel['type'].replace('_', ' ').title()}**: {rel['table']}")

            # Sample Operations - Actual Source Code
            if table_data['sample_operations']:
                st.markdown("### Sample Operations from Source Code")
                for i, op in enumerate(table_data['sample_operations'][:5], 1):
                    st.markdown(f"**Operation {i}** - `{op['location']}`")
                    st.code(op['code'], language="csharp")

            # File Locations
            st.markdown("### Access Locations")
            for loc in table_data['locations'][:10]:
                st.text(f"📄 {loc}")
            if len(table_data['locations']) > 10:
                st.text(f"   ... and {len(table_data['locations']) - 10} more")

    # Relationship diagram
    if schema_info['relationships']:
        st.divider()
        st.subheader("Table Relationships")
        st.markdown("Detected relationships based on workflow patterns")

        # Generate ER diagram
        er_diagram = generate_er_diagram(schema_info)
        render_mermaid(er_diagram, height=500)


def render_analysis_tab():
    """Render the data analysis and insights tab."""
    st.header("Data Flow Analysis")
    st.markdown("Insights and patterns detected in your codebase")

    result = st.session_state.scan_result

    # Operation breakdown
    st.subheader("Operation Types")

    from collections import Counter
    type_counts = Counter(node.type for node in result.graph.nodes)

    # Create columns for metrics
    cols = st.columns(min(5, len(type_counts)))
    for col, (workflow_type, count) in zip(cols, type_counts.most_common()):
        with col:
            st.metric(
                workflow_type.value.replace('_', ' ').title(),
                f"{count:,}",
                help=f"{count} operations of this type detected"
            )

    st.divider()

    # Hot spots (files with most operations)
    st.subheader("🔥 Activity Hot Spots")
    st.markdown("Files with the most workflow operations")

    file_operation_counts = Counter(node.location.file_path for node in result.graph.nodes)

    hot_spots_data = []
    for file_path, count in file_operation_counts.most_common(20):
        # Shorten file path for display
        display_path = file_path if len(file_path) < 60 else "..." + file_path[-57:]
        hot_spots_data.append({
            "File": display_path,
            "Operations": count,
            "Full Path": file_path
        })

    if hot_spots_data:
        import pandas as pd
        df = pd.DataFrame(hot_spots_data)
        st.dataframe(
            df[["File", "Operations"]],
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # Workflow patterns
    st.subheader("📋 Common Workflow Patterns")

    patterns = analyze_workflow_patterns(result.graph)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**API → Database (Data Ingestion)**")
        st.metric("Occurrences", patterns['api_to_db'])

        st.markdown("**Database → API (Data Retrieval)**")
        st.metric("Occurrences", patterns['db_to_api'])

    with col2:
        st.markdown("**Database → Transform → API**")
        st.metric("Occurrences", patterns['db_transform_api'])

        st.markdown("**API → Transform → Database**")
        st.metric("Occurrences", patterns['api_transform_db'])

    # Most connected nodes
    st.divider()
    st.subheader("🔗 Most Connected Operations")
    st.markdown("Operations with the most connections (high integration points)")

    node_connections = {}
    for edge in result.graph.edges:
        node_connections[edge.source] = node_connections.get(edge.source, 0) + 1
        node_connections[edge.target] = node_connections.get(edge.target, 0) + 1

    top_connected = sorted(node_connections.items(), key=lambda x: x[1], reverse=True)[:10]

    for node_id, connection_count in top_connected:
        node = result.graph.get_node(node_id)
        if node:
            with st.expander(f"{node.name} ({connection_count} connections)", expanded=False):
                st.write(f"**Type:** {node.type.value}")
                st.write(f"**Location:** {node.location}")
                if node.code_snippet:
                    st.code(node.code_snippet)


def analyze_database_schema(db_nodes, edges):
    """Analyze database operations to extract schema information."""
    import re

    schema = {
        'tables': {},
        'total_reads': 0,
        'total_writes': 0,
        'relationships': []
    }

    # Track model file paths by scanning for DbSet declarations
    model_paths = {}
    file_contents_cache = {}

    for node in db_nodes:
        table_name = node.table_name or "Unknown"

        if table_name not in schema['tables']:
            schema['tables'][table_name] = {
                'read_count': 0,
                'write_count': 0,
                'total_operations': 0,
                'locations': set(),
                'sample_operations': [],
                'model_path': None,
                'columns': [],
                'related_tables': []
            }

        table_data = schema['tables'][table_name]

        # Count operations
        if node.type == WorkflowType.DATABASE_READ:
            table_data['read_count'] += 1
            schema['total_reads'] += 1
        elif node.type == WorkflowType.DATABASE_WRITE:
            table_data['write_count'] += 1
            schema['total_writes'] += 1

        table_data['total_operations'] += 1
        table_data['locations'].add(str(node.location))

        # Save sample code with location
        if node.code_snippet and len(table_data['sample_operations']) < 5:
            table_data['sample_operations'].append({
                'code': node.code_snippet.strip(),
                'location': str(node.location)
            })

        # Try to find model definition
        file_path = node.location.file_path

        # Check if this is a DbContext or model file
        if ('Context.cs' in file_path or 'DbContext' in file_path or
            f'{table_name}.cs' in file_path or 'Models' in file_path):

            if not table_data['model_path'] or 'Models' in file_path:
                table_data['model_path'] = file_path

            # Try to extract column information from the file
            if file_path not in file_contents_cache and os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_contents_cache[file_path] = f.read()
                except:
                    pass

            if file_path in file_contents_cache:
                content = file_contents_cache[file_path]

                # Extract properties (columns) from model class
                if f'class {table_name}' in content or f'DbSet<{table_name}>' in content:
                    # Find class definition
                    class_match = re.search(rf'class\s+{table_name}\s*(?::\s*[\w\s,<>]+)?\s*\{{([^}}]+)\}}', content, re.DOTALL)
                    if class_match:
                        class_body = class_match.group(1)
                        # Extract properties
                        prop_matches = re.finditer(r'public\s+(\w+(?:<[\w,\s]+>)?)\s+(\w+)\s*\{[^}]*\}', class_body)
                        for prop_match in prop_matches:
                            prop_type = prop_match.group(1)
                            prop_name = prop_match.group(2)

                            # Determine if it's a key or navigation property
                            is_key = 'Id' in prop_name or '[Key]' in class_body[:prop_match.start()]
                            is_nav = 'virtual' in class_body[max(0, prop_match.start()-50):prop_match.start()] or \
                                    'ICollection' in prop_type or 'List<' in prop_type

                            column_info = {
                                'name': prop_name,
                                'type': prop_type,
                                'is_key': is_key,
                                'is_navigation': is_nav
                            }

                            if column_info not in table_data['columns']:
                                table_data['columns'].append(column_info)

                            # Detect relationships from navigation properties
                            if is_nav:
                                # Extract related table name
                                related_match = re.search(r'ICollection<(\w+)>|List<(\w+)>|(\w+)\s+\w+\s*\{', prop_type + ' ' + prop_name)
                                if related_match:
                                    related_table = related_match.group(1) or related_match.group(2) or prop_type
                                    if related_table != table_name:
                                        rel_type = 'has_many' if 'ICollection' in prop_type or 'List<' in prop_type else 'belongs_to'
                                        rel_info = {'table': related_table, 'type': rel_type}
                                        if rel_info not in table_data['related_tables']:
                                            table_data['related_tables'].append(rel_info)

    # Convert sets to lists for JSON compatibility
    for table_data in schema['tables'].values():
        table_data['locations'] = sorted(list(table_data['locations']))

    # Detect relationships (tables that interact via edges)
    table_connections = set()
    node_to_table = {node.id: node.table_name for node in db_nodes if node.table_name}

    for edge in edges:
        source_table = node_to_table.get(edge.source)
        target_table = node_to_table.get(edge.target)

        if source_table and target_table and source_table != target_table:
            # Create ordered relationship
            rel = tuple(sorted([source_table, target_table]))
            table_connections.add(rel)

    schema['relationships'] = list(table_connections)

    return schema


def generate_er_diagram(schema_info):
    """Generate a Mermaid ER diagram from schema information."""
    lines = ["erDiagram"]

    # Add tables with their operation counts
    for table_name, table_data in sorted(schema_info['tables'].items()):
        # Clean table name for Mermaid
        clean_name = table_name.replace(' ', '_').replace('-', '_')
        lines.append(f"    {clean_name} {{")
        lines.append(f"        int reads PK \"Read ops: {table_data['read_count']}\"")
        lines.append(f"        int writes \"Write ops: {table_data['write_count']}\"")
        lines.append("    }")

    # Add relationships
    for table1, table2 in schema_info['relationships']:
        clean1 = table1.replace(' ', '_').replace('-', '_')
        clean2 = table2.replace(' ', '_').replace('-', '_')
        lines.append(f"    {clean1} ||--o{{ {clean2} : \"workflow\"")

    return '\n'.join(lines)


def analyze_workflow_patterns(graph):
    """Analyze the graph for common workflow patterns."""
    patterns = {
        'api_to_db': 0,
        'db_to_api': 0,
        'db_transform_api': 0,
        'api_transform_db': 0
    }

    # Build adjacency map for faster lookup
    adjacency = {}
    for edge in graph.edges:
        if edge.source not in adjacency:
            adjacency[edge.source] = []
        adjacency[edge.source].append(edge.target)

    # Create node type map
    node_types = {node.id: node.type for node in graph.nodes}

    # Detect patterns
    for node in graph.nodes:
        node_type = node_types.get(node.id)
        targets = adjacency.get(node.id, [])

        for target_id in targets:
            target_type = node_types.get(target_id)

            # API → Database
            if node_type == WorkflowType.API_CALL and target_type in [WorkflowType.DATABASE_WRITE, WorkflowType.DATABASE_READ]:
                patterns['api_to_db'] += 1

            # Database → API
            if node_type in [WorkflowType.DATABASE_READ, WorkflowType.DATABASE_WRITE] and target_type == WorkflowType.API_CALL:
                patterns['db_to_api'] += 1

            # Check for 3-step patterns
            for second_target_id in adjacency.get(target_id, []):
                second_target_type = node_types.get(second_target_id)

                # DB → Transform → API
                if (node_type == WorkflowType.DATABASE_READ and
                    target_type == WorkflowType.DATA_TRANSFORM and
                    second_target_type == WorkflowType.API_CALL):
                    patterns['db_transform_api'] += 1

                # API → Transform → DB
                if (node_type == WorkflowType.API_CALL and
                    target_type == WorkflowType.DATA_TRANSFORM and
                    second_target_type in [WorkflowType.DATABASE_WRITE, WorkflowType.DATABASE_READ]):
                    patterns['api_transform_db'] += 1

    return patterns


def generate_and_render_diagram(result, filter_type, filter_value, max_nodes):
    """Generate a Mermaid diagram based on filter and store in session state."""
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
            st.warning(f"No nodes found matching '{filter_value}'")
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

        st.success(f"✓ Generated diagram with {len(filtered_nodes)} nodes!")

    except Exception as e:
        st.error(f"Error generating diagram: {str(e)}")
        st.code(traceback.format_exc())


def scan_repository(repo_path, extensions, detect_db, detect_api, detect_files, detect_msg, detect_transform):
    """Scan repository and store results."""
    if not os.path.exists(repo_path):
        st.error(f"Repository path not found: {repo_path}")
        return

    # Clear cached filter options from previous scans
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith('filter_options_')]
    for key in keys_to_remove:
        del st.session_state[key]

    # Clear previous diagram
    st.session_state.generated_diagram = None

    # Create progress placeholders with custom styling
    # Add custom CSS for rainbow gradient progress bar
    st.markdown("""
    <style>
    div[data-testid="stProgress"] > div > div > div > div {
        background: linear-gradient(90deg,
            #667eea 0%,
            #764ba2 14%,
            #f093fb 28%,
            #f5576c 42%,
            #feca57 57%,
            #48dbfb 71%,
            #0abde3 85%,
            #00d2d3 100%
        ) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Compact progress display in a fixed container
    progress_placeholder = st.empty()
    status_placeholder = st.empty()

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

        # Progress callback for real-time updates
        def update_progress(current, total, message):
            """Update progress bar and status text with pinata indicator."""
            # Check if stop was requested
            if st.session_state.stop_scan:
                raise KeyboardInterrupt("Scan stopped by user")

            try:
                if total > 0:
                    progress = current / total
                    pinata_position = int(progress * 100)

                    # Create combined progress bar and pinata overlay
                    combined_html = f"""
                    <div style="position: relative; width: 100%; margin-bottom: 5px;">
                        <div style="
                            width: 100%;
                            height: 8px;
                            background: linear-gradient(90deg,
                                #667eea 0%,
                                #764ba2 14%,
                                #f093fb 28%,
                                #f5576c 42%,
                                #feca57 57%,
                                #48dbfb 71%,
                                #0abde3 85%,
                                #00d2d3 100%
                            );
                            border-radius: 4px;
                            overflow: hidden;
                            position: relative;
                        ">
                            <div style="
                                position: absolute;
                                right: 0;
                                width: {100 - pinata_position}%;
                                height: 100%;
                                background: #f0f0f0;
                                transition: width 0.3s ease-out;
                            "></div>
                        </div>
                        <div style="
                            position: absolute;
                            left: {pinata_position}%;
                            top: 4px;
                            transform: translateX(-50%) translateY(-50%) scaleX(-1);
                            font-size: 28px;
                            transition: left 0.3s ease-out;
                            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
                        ">🪅</div>
                    </div>
                    """
                    progress_placeholder.markdown(combined_html, unsafe_allow_html=True)

                # Show status in a more compact way
                status_placeholder.markdown(f"<small>{message}</small>", unsafe_allow_html=True)
            except Exception as e:
                # Silently ignore WebSocket errors during progress updates
                # These happen when the browser disconnects/reconnects
                pass

        # Scan repository with progress updates
        status_placeholder.markdown("<small>🔍 Starting repository scan...</small>", unsafe_allow_html=True)
        builder = WorkflowGraphBuilder(config)
        result = builder.build(repo_path, progress_callback=update_progress)

        # Render visualizations
        status_placeholder.markdown("<small>🎨 Rendering visualizations...</small>", unsafe_allow_html=True)
        renderer = WorkflowRenderer(config)
        output_files = renderer.render(result)

        # Store in session state
        st.session_state.scan_result = result
        st.session_state.output_files = output_files

        # Clear progress indicators
        progress_placeholder.empty()
        status_placeholder.empty()

        st.success(f"✅ Scan complete! Scanned {result.files_scanned:,} files and found {len(result.graph.nodes):,} workflow nodes!")

        # Show instruction to navigate to tabs
        st.info("📊 Navigate to the **Visualizations** tab above to view the workflow diagrams!")

        # Reset scan state - NO RERUN NEEDED
        # The tabs are already showing based on has_results = scan_result is not None
        st.session_state.scan_running = False
        st.session_state.scan_triggered = False

    except KeyboardInterrupt as e:
        # Graceful stop requested by user
        progress_placeholder.empty()
        status_placeholder.empty()
        st.session_state.scan_running = False
        st.warning(f"⏹️ Scan stopped by user")

    except Exception as e:
        progress_placeholder.empty()
        status_placeholder.empty()
        st.session_state.scan_running = False
        st.error(f"Error during scan: {str(e)}")
        st.code(traceback.format_exc())


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


if __name__ == '__main__':
    print("\nExecuting main() function...")
    try:
        main()
        print("main() completed successfully")
    except Exception as e:
        print(f"FATAL ERROR in main(): {e}")
        traceback.print_exc()
        raise
