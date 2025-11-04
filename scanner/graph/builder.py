"""Workflow graph builder - orchestrates scanning and graph construction."""

import os
import time
from pathlib import Path
from typing import List, Dict, Any

from models import WorkflowGraph, WorkflowNode, WorkflowEdge, ScanResult
from scanner import CSharpScanner, TypeScriptScanner, ReactScanner, AngularScanner, WPFScanner


class WorkflowGraphBuilder:
    """Builds workflow graphs from repository scanning."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize graph builder.

        Args:
            config: Scanner configuration
        """
        self.config = config
        self.scanners = self._initialize_scanners()

    def _initialize_scanners(self) -> List:
        """Initialize all available scanners."""
        scanner_config = self.config.get('scanner', {})

        scanners = [
            CSharpScanner(scanner_config),       # C# backend code
            TypeScriptScanner(scanner_config),   # TypeScript/JavaScript
            ReactScanner(scanner_config),        # React UI workflows
            AngularScanner(scanner_config),      # Angular UI workflows
            WPFScanner(scanner_config),          # WPF desktop UI workflows
        ]

        return scanners

    def build(self, repository_path: str, progress_callback=None) -> ScanResult:
        """Build workflow graph from repository.

        Args:
            repository_path: Path to repository to scan
            progress_callback: Optional callback function(current, total, message) for progress updates

        Returns:
            ScanResult containing the workflow graph
        """
        start_time = time.time()

        result = ScanResult(
            repository_path=repository_path,
            graph=WorkflowGraph()
        )

        # Get scanner configuration
        scanner_config = self.config.get('scanner', {})
        include_extensions = scanner_config.get('include_extensions', ['.cs', '.ts', '.js'])
        exclude_dirs = scanner_config.get('exclude_dirs', [])

        print("\n" + "="*60)
        print("SCANNING CONFIGURATION")
        print("="*60)
        print(f"Repository: {repository_path}")
        print(f"File types: {', '.join(include_extensions)}")
        print(f"Excluding: {', '.join(exclude_dirs[:5])}{'...' if len(exclude_dirs) > 5 else ''}")
        print("="*60 + "\n")

        # Find all files to scan
        print("🔍 Discovering files...")
        files_to_scan = self._find_files(repository_path, include_extensions, exclude_dirs)

        print(f"✓ Found {len(files_to_scan):,} files to scan\n")

        # Notify callback of total files discovered
        if progress_callback:
            progress_callback(0, len(files_to_scan), f"Found {len(files_to_scan):,} files to scan")

        # FIRST PASS: Discover database schemas/models
        print("="*60)
        print("DISCOVERING DATABASE SCHEMAS")
        print("="*60)

        if progress_callback:
            progress_callback(0, len(files_to_scan), "Discovering database schemas...")

        self._discover_schemas(files_to_scan, result, progress_callback)

        print(f"✓ Found {len(result.schemas_discovered):,} database schemas\n")

        if progress_callback:
            progress_callback(0, len(files_to_scan), f"Schema discovery complete: {len(result.schemas_discovered):,} tables found")

        # SECOND PASS: Scan files for workflow operations
        print("="*60)
        print("SCANNING FILES")
        print("="*60)

        last_print_time = time.time()

        # Scan each file
        for file_path in files_to_scan:
            try:
                # Find appropriate scanner
                scanner = self._get_scanner_for_file(file_path)

                if scanner:
                    # Pass schema registry to scanner for enhanced table name detection
                    file_graph = scanner.scan_file(file_path, schema_registry=result.schemas_discovered)
                    # Merge file graph into result graph
                    self._merge_graphs(result.graph, file_graph)
                    result.files_scanned += 1

                    current_time = time.time()

                    # Print progress every 10 files OR every 5 seconds
                    if result.files_scanned % 10 == 0 or (current_time - last_print_time) >= 5:
                        elapsed = current_time - start_time
                        progress_pct = (result.files_scanned / len(files_to_scan)) * 100

                        # Calculate estimated time remaining
                        if result.files_scanned > 0:
                            avg_time_per_file = elapsed / result.files_scanned
                            remaining_files = len(files_to_scan) - result.files_scanned
                            eta_seconds = avg_time_per_file * remaining_files
                            eta_minutes = int(eta_seconds / 60)
                            eta_seconds_remainder = int(eta_seconds % 60)
                            eta_str = f"{eta_minutes}m {eta_seconds_remainder}s"
                        else:
                            eta_str = "calculating..."

                        # Get relative file path for display
                        display_path = file_path.replace(repository_path, '')
                        if len(display_path) > 50:
                            display_path = '...' + display_path[-47:]

                        progress_msg = (f"[{progress_pct:5.1f}%] {result.files_scanned:,}/{len(files_to_scan):,} files | "
                                       f"Nodes: {len(result.graph.nodes):,} | "
                                       f"ETA: {eta_str}")

                        print(progress_msg)

                        # Notify callback
                        if progress_callback:
                            progress_callback(result.files_scanned, len(files_to_scan), progress_msg)

                        last_print_time = current_time

            except Exception as e:
                error_msg = f"Error scanning {file_path}: {str(e)}"
                result.errors.append(error_msg)
                print(f"⚠️  WARNING: {error_msg}")

        print("="*60)
        print(f"✓ Scanning complete: {result.files_scanned:,} files processed\n")

        # Notify completion of file scanning
        if progress_callback:
            progress_callback(len(files_to_scan), len(files_to_scan),
                            f"File scanning complete: {result.files_scanned:,} files processed")

        # Analyze and create edges based on workflow patterns
        edge_inference_config = self.config.get('scanner', {}).get('edge_inference', {})
        if edge_inference_config.get('enabled', True):
            print("="*60)
            print("INFERRING WORKFLOW EDGES")
            print("="*60)

            # Notify callback about edge inference phase
            if progress_callback:
                progress_callback(len(files_to_scan), len(files_to_scan), "Analyzing workflow relationships...")

            self._infer_workflow_edges(result.graph, edge_inference_config, len(files_to_scan), progress_callback)
        else:
            print("\n⚠️  Skipping edge inference (disabled in config)")

        # API Routes Analysis
        print("\n" + "="*60)
        print("ANALYZING API ROUTES")
        print("="*60)
        if progress_callback:
            progress_callback(len(files_to_scan), len(files_to_scan), "Analyzing API routes and endpoints...")
        self._analyze_api_routes(result.graph, progress_callback)

        # Pages and Components Analysis
        print("\n" + "="*60)
        print("ANALYZING PAGES AND COMPONENTS")
        print("="*60)
        if progress_callback:
            progress_callback(len(files_to_scan), len(files_to_scan), "Analyzing UI pages and components...")
        self._analyze_pages_and_components(result.graph, progress_callback)

        # Dependency Analysis
        print("\n" + "="*60)
        print("ANALYZING DEPENDENCIES")
        print("="*60)
        if progress_callback:
            progress_callback(len(files_to_scan), len(files_to_scan), "Analyzing code dependencies...")
        self._analyze_dependencies(result.graph, progress_callback)

        result.scan_time_seconds = time.time() - start_time

        print("\n" + "="*60)
        print("SCAN COMPLETE")
        print("="*60)
        print(f"  Files scanned: {result.files_scanned}")
        print(f"  Nodes found: {len(result.graph.nodes)}")
        print(f"  Edges found: {len(result.graph.edges)}")
        print(f"  Scan time: {result.scan_time_seconds:.2f}s")

        if result.errors:
            print(f"  Errors: {len(result.errors)}")

        # Final completion message
        if progress_callback:
            progress_callback(len(files_to_scan), len(files_to_scan), "Scan completed successfully!")

        return result

    def _discover_schemas(self, files_to_scan: List[str], result, progress_callback=None):
        """Discover database schemas/models in the codebase.

        This performs a first pass to identify entity/model definitions
        before scanning for workflow operations.

        Args:
            files_to_scan: List of files to check for schemas
            result: ScanResult to store discovered schemas
            progress_callback: Optional callback for progress updates
        """
        from scanner import CSharpScanner

        # Only scan C# files for schema detection (can extend to TypeScript/etc later)
        csharp_scanner = CSharpScanner(self.config.get('scanner', {}))
        schemas_found = 0
        files_checked = 0
        last_update_time = time.time()

        # Count total C# files for accurate progress
        total_cs_files = sum(1 for f in files_to_scan if f.endswith('.cs'))
        print(f"  Scanning {total_cs_files} C# files for database schemas...")

        for file_path in files_to_scan:
            if file_path.endswith('.cs'):
                try:
                    schemas = csharp_scanner.detect_schemas(file_path)

                    for schema in schemas:
                        # Store by both entity name and table name for easy lookup
                        result.schemas_discovered[schema.entity_name] = schema
                        result.schemas_discovered[schema.table_name] = schema
                        schemas_found += 1

                    files_checked += 1

                    current_time = time.time()

                    # Send progress update every 10 files OR every 2 seconds (much more frequent!)
                    if progress_callback and (files_checked % 10 == 0 or (current_time - last_update_time) >= 2):
                        progress_pct = (files_checked / total_cs_files * 100) if total_cs_files > 0 else 0
                        progress_msg = f"Discovering database schemas... ({files_checked}/{total_cs_files} files, {len(result.schemas_discovered):,} schemas found)"

                        # Print to console for debugging
                        print(f"  [{progress_pct:5.1f}%] {progress_msg}")

                        # Notify frontend
                        progress_callback(files_checked, total_cs_files, progress_msg)
                        last_update_time = current_time

                except Exception as e:
                    # Don't fail the entire scan if schema detection fails
                    print(f"  ⚠️  Warning: Failed to detect schemas in {file_path}: {str(e)}")
                    pass

        print(f"  ✓ Checked {files_checked} C# files")
        print(f"  ✓ Discovered {len(result.schemas_discovered)} unique schemas")

    def _find_files(self, root_path: str, include_extensions: List[str], exclude_dirs: List[str]) -> List[str]:
        """Find all files to scan in the repository.

        Args:
            root_path: Root directory to search
            include_extensions: List of file extensions to include
            exclude_dirs: List of directory names to exclude

        Returns:
            List of file paths to scan
        """
        import fnmatch

        files = []
        exclude_patterns = self.config.get('scanner', {}).get('exclude_patterns', [])

        # Convert exclude_dirs to a set for O(1) lookup
        exclude_dirs_set = set(exclude_dirs)

        # Stats for reporting
        dirs_skipped = 0
        files_excluded_by_pattern = 0

        for root, dirs, filenames in os.walk(root_path):
            # Remove excluded directories from search (in-place modification to prevent os.walk from descending)
            original_dir_count = len(dirs)
            dirs[:] = [d for d in dirs if d not in exclude_dirs_set and not d.startswith('.')]
            dirs_skipped += original_dir_count - len(dirs)

            for filename in filenames:
                # Check if file matches any extension
                if not any(filename.endswith(ext) for ext in include_extensions):
                    continue

                # Check if file matches any exclude pattern
                if any(fnmatch.fnmatch(filename, pattern) for pattern in exclude_patterns):
                    files_excluded_by_pattern += 1
                    continue

                file_path = os.path.join(root, filename)
                files.append(file_path)

        # Report what was filtered out
        if dirs_skipped > 0 or files_excluded_by_pattern > 0:
            print(f"  Filtered: {dirs_skipped} directories, {files_excluded_by_pattern} files (minified/generated)")

        return files

    def _get_scanner_for_file(self, file_path: str):
        """Get appropriate scanner for a file.

        Args:
            file_path: Path to the file

        Returns:
            Scanner instance or None
        """
        for scanner in self.scanners:
            if scanner.can_scan(file_path):
                return scanner
        return None

    def _merge_graphs(self, target: WorkflowGraph, source: WorkflowGraph):
        """Merge source graph into target graph.

        Args:
            target: Target graph to merge into
            source: Source graph to merge from
        """
        for node in source.nodes:
            target.add_node(node)

        for edge in source.edges:
            target.add_edge(edge)

    def _infer_workflow_edges(self, graph: WorkflowGraph, config: Dict[str, Any] = None,
                             total_files: int = 0, progress_callback = None):
        """Infer edges between nodes based on workflow patterns.

        This creates connections between related workflow steps, such as:
        - API calls followed by database writes
        - Database reads followed by data transforms
        - File reads followed by processing

        Args:
            graph: Workflow graph to analyze
            config: Edge inference configuration
            total_files: Total number of files scanned (for progress calculation)
            progress_callback: Optional callback for progress updates
        """
        if config is None:
            config = {}

        # Create proximity edges (nodes close together in same file)
        if config.get('proximity_edges', True):
            print("  Creating proximity edges...")
            max_distance = config.get('max_line_distance', 20)
            nodes_by_file = {}

            # Group nodes by file
            for node in graph.nodes:
                file_path = node.location.file_path
                if file_path not in nodes_by_file:
                    nodes_by_file[file_path] = []
                nodes_by_file[file_path].append(node)

            edge_count = 0
            files_processed = 0
            total_file_count = len(nodes_by_file)

            # Create edges within each file based on line number proximity
            for file_path, nodes in nodes_by_file.items():
                # Sort nodes by line number
                sorted_nodes = sorted(nodes, key=lambda n: n.location.line_number)

                # Connect adjacent workflow operations
                for i in range(len(sorted_nodes) - 1):
                    current = sorted_nodes[i]
                    next_node = sorted_nodes[i + 1]

                    line_distance = next_node.location.line_number - current.location.line_number

                    if line_distance <= max_distance:
                        edge = WorkflowEdge(
                            source=current.id,
                            target=next_node.id,
                            label=f"Sequential ({line_distance} lines)",
                            metadata={'distance': line_distance}
                        )
                        graph.add_edge(edge)
                        edge_count += 1

                files_processed += 1

                # Send progress update every 50 files
                if progress_callback and files_processed % 50 == 0:
                    progress_msg = f"Creating proximity edges... ({files_processed}/{total_file_count} files, {edge_count:,} edges)"
                    progress_callback(total_files, total_files, progress_msg)

            print(f"    Added {edge_count} proximity edges")

            if progress_callback:
                progress_msg = f"Proximity edges complete: {edge_count:,} edges created"
                progress_callback(total_files, total_files, progress_msg)

        # Create edges based on data flow patterns
        if config.get('data_flow_edges', True):
            self._infer_data_flow_edges(graph, total_files, progress_callback)

    def _infer_data_flow_edges(self, graph: WorkflowGraph, total_files: int = 0, progress_callback = None):
        """Infer edges based on common data flow patterns.

        For example:
        - API call -> Database write (data ingestion)
        - Database read -> API call (data retrieval)
        - Database read -> Transform -> API call (data processing)

        Args:
            graph: Workflow graph to analyze
            total_files: Total number of files scanned (for progress calculation)
            progress_callback: Optional callback for progress updates
        """
        from models import WorkflowType
        from collections import defaultdict
        import bisect

        print("  Inferring data flow edges...")

        if progress_callback:
            progress_callback(total_files, total_files, "Analyzing data flow patterns...")

        # Create a set of existing edges for O(1) lookup
        existing_edges = {(e.source, e.target) for e in graph.edges}

        # Group nodes by file and type for efficient lookup
        nodes_by_file_and_type = defaultdict(lambda: defaultdict(list))
        for node in graph.nodes:
            nodes_by_file_and_type[node.location.file_path][node.type].append(node)

        # Sort nodes by line number within each file/type for binary search optimization
        for file_path, types_dict in nodes_by_file_and_type.items():
            for node_type, nodes in types_dict.items():
                nodes.sort(key=lambda n: n.location.line_number)

        total_edge_count = 0
        files_processed = 0
        total_file_count = len(nodes_by_file_and_type)

        # Pattern: API call followed by DB write (data ingestion)
        edge_count = 0
        for file_path, types_dict in nodes_by_file_and_type.items():
            api_calls = types_dict.get(WorkflowType.API_CALL, [])
            db_writes = types_dict.get(WorkflowType.DATABASE_WRITE, [])

            # OPTIMIZATION: Use sorted list and binary search instead of nested loops
            for api_node in api_calls:
                # Find db_writes that are within 50 lines after this API call
                # Using binary search to find the starting position
                min_line = api_node.location.line_number
                max_line = api_node.location.line_number + 50

                # Find first db_write at or after api_node line
                start_idx = bisect.bisect_left(db_writes, min_line,
                                              key=lambda n: n.location.line_number)

                # Check only db_writes within range (much faster than checking all)
                for i in range(start_idx, len(db_writes)):
                    db_node = db_writes[i]

                    # Early termination: if we're past the range, stop
                    if db_node.location.line_number > max_line:
                        break

                    if db_node.location.line_number > min_line:
                        # Check if edge doesn't already exist (O(1) lookup)
                        if (api_node.id, db_node.id) not in existing_edges:
                            edge = WorkflowEdge(
                                source=api_node.id,
                                target=db_node.id,
                                label="Data Ingestion",
                                metadata={'pattern': 'api_to_db'}
                            )
                            graph.add_edge(edge)
                            existing_edges.add((api_node.id, db_node.id))
                            edge_count += 1
                            total_edge_count += 1

            files_processed += 1

            # Send progress update every 25 files
            if progress_callback and files_processed % 25 == 0:
                progress_msg = f"Data flow analysis... ({files_processed}/{total_file_count} files, {total_edge_count:,} edges)"
                progress_callback(total_files, total_files, progress_msg)

        print(f"    Added {edge_count} data ingestion edges")

        # Pattern: DB read followed by transform
        edge_count = 0
        for file_path, types_dict in nodes_by_file_and_type.items():
            db_reads = types_dict.get(WorkflowType.DATABASE_READ, [])
            transforms = types_dict.get(WorkflowType.DATA_TRANSFORM, [])

            # OPTIMIZATION: Use sorted list and binary search
            for db_node in db_reads:
                min_line = db_node.location.line_number
                max_line = db_node.location.line_number + 30

                # Find first transform at or after db_node line
                start_idx = bisect.bisect_left(transforms, min_line,
                                              key=lambda n: n.location.line_number)

                # Check only transforms within range
                for i in range(start_idx, len(transforms)):
                    transform_node = transforms[i]

                    # Early termination
                    if transform_node.location.line_number > max_line:
                        break

                    if transform_node.location.line_number > min_line:
                        if (db_node.id, transform_node.id) not in existing_edges:
                            edge = WorkflowEdge(
                                source=db_node.id,
                                target=transform_node.id,
                                label="Data Processing",
                                metadata={'pattern': 'db_to_transform'}
                            )
                            graph.add_edge(edge)
                            existing_edges.add((db_node.id, transform_node.id))
                            edge_count += 1
                            total_edge_count += 1

        print(f"    Added {edge_count} data processing edges")

        if progress_callback:
            progress_msg = f"Data flow analysis complete: {total_edge_count:,} edges created"
            progress_callback(total_files, total_files, progress_msg)

    def _analyze_api_routes(self, graph: WorkflowGraph, progress_callback=None):
        """Analyze API routes and endpoints in the workflow graph.

        This identifies:
        - Unique API endpoints
        - HTTP methods used
        - Frequency of API calls
        - API call patterns
        """
        from models import WorkflowType
        from collections import defaultdict

        print("  Analyzing API endpoints...")

        # Extract all API-related nodes
        api_nodes = [node for node in graph.nodes if node.type == WorkflowType.API_CALL]

        if not api_nodes:
            print("  ✓ No API endpoints found")
            if progress_callback:
                progress_callback(1, 1, "API analysis complete: No endpoints found")
            return

        # Group by endpoint
        endpoint_stats = defaultdict(lambda: {"methods": set(), "count": 0, "files": set()})

        for node in api_nodes:
            endpoint = node.endpoint or "unknown"
            method = node.method or "UNKNOWN"

            endpoint_stats[endpoint]["methods"].add(method)
            endpoint_stats[endpoint]["count"] += 1
            endpoint_stats[endpoint]["files"].add(node.location.file_path)

        # Report findings
        print(f"  ✓ Found {len(endpoint_stats)} unique API endpoints")
        print(f"  ✓ Total API calls: {len(api_nodes)}")

        # Show top 5 most used endpoints
        sorted_endpoints = sorted(endpoint_stats.items(), key=lambda x: x[1]["count"], reverse=True)
        if sorted_endpoints:
            print("  Top API endpoints:")
            for endpoint, stats in sorted_endpoints[:5]:
                methods_str = ", ".join(sorted(stats["methods"]))
                print(f"    • {endpoint} ({methods_str}): {stats['count']} calls in {len(stats['files'])} files")

        if progress_callback:
            progress_callback(1, 1, f"API analysis complete: {len(endpoint_stats)} endpoints, {len(api_nodes)} calls")

    def _analyze_pages_and_components(self, graph: WorkflowGraph, progress_callback=None):
        """Analyze UI pages and components in the workflow graph.

        This identifies:
        - UI interaction points
        - Component hierarchies
        - Page workflows
        """
        from models import WorkflowType
        from collections import defaultdict

        print("  Analyzing UI components and pages...")

        # Extract all UI-related nodes
        ui_nodes = [node for node in graph.nodes
                   if node.type in [WorkflowType.UI_INTERACTION, WorkflowType.UI_RENDER]]

        if not ui_nodes:
            print("  ✓ No UI components found")
            if progress_callback:
                progress_callback(1, 1, "UI analysis complete: No components found")
            return

        # Group by file (each file is likely a component or page)
        file_components = defaultdict(list)
        for node in ui_nodes:
            file_path = node.location.file_path
            file_components[file_path].append(node)

        # Identify component types
        component_types = defaultdict(int)
        for node in ui_nodes:
            # Categorize by file extension or node type
            if node.location.file_path.endswith('.tsx') or node.location.file_path.endswith('.jsx'):
                component_types['React'] += 1
            elif node.location.file_path.endswith('.xaml'):
                component_types['WPF'] += 1
            elif node.location.file_path.endswith('.html'):
                component_types['Angular'] += 1
            else:
                component_types['Other'] += 1

        # Report findings
        print(f"  ✓ Found {len(file_components)} component files")
        print(f"  ✓ Total UI interactions: {len(ui_nodes)}")

        if component_types:
            print("  Component breakdown:")
            for comp_type, count in sorted(component_types.items(), key=lambda x: x[1], reverse=True):
                print(f"    • {comp_type}: {count} interactions")

        # Show files with most UI interactions
        sorted_files = sorted(file_components.items(), key=lambda x: len(x[1]), reverse=True)
        if sorted_files:
            print("  Most interactive components:")
            for file_path, nodes in sorted_files[:5]:
                file_name = file_path.split('/')[-1]
                print(f"    • {file_name}: {len(nodes)} interactions")

        if progress_callback:
            progress_callback(1, 1, f"UI analysis complete: {len(file_components)} components, {len(ui_nodes)} interactions")

    def _analyze_dependencies(self, graph: WorkflowGraph, progress_callback=None):
        """Analyze code dependencies and relationships in the workflow graph.

        This identifies:
        - Files with most dependencies
        - Highly connected workflow nodes
        - Potential architectural insights
        """
        from collections import defaultdict

        print("  Analyzing code dependencies...")

        # Count dependencies by file
        file_dependencies = defaultdict(lambda: {"incoming": 0, "outgoing": 0, "nodes": 0})

        # Count nodes per file
        for node in graph.nodes:
            file_path = node.location.file_path
            file_dependencies[file_path]["nodes"] += 1

        # Count edges (dependencies) per file
        node_to_file = {node.id: node.location.file_path for node in graph.nodes}

        for edge in graph.edges:
            source_file = node_to_file.get(edge.source)
            target_file = node_to_file.get(edge.target)

            if source_file and target_file:
                if source_file != target_file:
                    # Cross-file dependency
                    file_dependencies[source_file]["outgoing"] += 1
                    file_dependencies[target_file]["incoming"] += 1

        # Report findings
        total_files = len(file_dependencies)
        total_cross_file_edges = sum(stats["outgoing"] for stats in file_dependencies.values())

        print(f"  ✓ Analyzed {total_files} files")
        print(f"  ✓ Found {total_cross_file_edges} cross-file dependencies")

        # Find most connected files (hubs)
        if file_dependencies:
            sorted_by_connections = sorted(
                file_dependencies.items(),
                key=lambda x: x[1]["incoming"] + x[1]["outgoing"],
                reverse=True
            )

            if sorted_by_connections:
                print("  Most connected files (dependency hubs):")
                for file_path, stats in sorted_by_connections[:5]:
                    file_name = file_path.split('/')[-1]
                    total_connections = stats["incoming"] + stats["outgoing"]
                    print(f"    • {file_name}: {total_connections} connections "
                          f"({stats['incoming']} in, {stats['outgoing']} out, {stats['nodes']} nodes)")

            # Find files with high outgoing dependencies (potential service layers)
            sorted_by_outgoing = sorted(
                file_dependencies.items(),
                key=lambda x: x[1]["outgoing"],
                reverse=True
            )

            if sorted_by_outgoing and sorted_by_outgoing[0][1]["outgoing"] > 0:
                print("  Files with most outgoing dependencies (potential service/utility layers):")
                for file_path, stats in sorted_by_outgoing[:5]:
                    if stats["outgoing"] == 0:
                        break
                    file_name = file_path.split('/')[-1]
                    print(f"    • {file_name}: {stats['outgoing']} outgoing dependencies")

        if progress_callback:
            progress_callback(1, 1, f"Dependency analysis complete: {total_files} files, {total_cross_file_edges} cross-file links")
