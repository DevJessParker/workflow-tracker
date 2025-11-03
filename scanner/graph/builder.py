"""Workflow graph builder - orchestrates scanning and graph construction."""

import os
import time
from pathlib import Path
from typing import List, Dict, Any

from ..models import WorkflowGraph, WorkflowNode, WorkflowEdge, ScanResult
from ..scanner import CSharpScanner, TypeScriptScanner, ReactScanner, AngularScanner, WPFScanner


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
                    file_graph = scanner.scan_file(file_path)
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
                progress_callback(len(files_to_scan), len(files_to_scan), "Inferring workflow edges...")

            self._infer_workflow_edges(result.graph, edge_inference_config)
        else:
            print("\n⚠️  Skipping edge inference (disabled in config)")

        result.scan_time_seconds = time.time() - start_time

        print(f"\nScan complete:")
        print(f"  Files scanned: {result.files_scanned}")
        print(f"  Nodes found: {len(result.graph.nodes)}")
        print(f"  Edges found: {len(result.graph.edges)}")
        print(f"  Scan time: {result.scan_time_seconds:.2f}s")

        if result.errors:
            print(f"  Errors: {len(result.errors)}")

        return result

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

    def _infer_workflow_edges(self, graph: WorkflowGraph, config: Dict[str, Any] = None):
        """Infer edges between nodes based on workflow patterns.

        This creates connections between related workflow steps, such as:
        - API calls followed by database writes
        - Database reads followed by data transforms
        - File reads followed by processing

        Args:
            graph: Workflow graph to analyze
            config: Edge inference configuration
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

            print(f"    Added {edge_count} proximity edges")

        # Create edges based on data flow patterns
        if config.get('data_flow_edges', True):
            self._infer_data_flow_edges(graph)

    def _infer_data_flow_edges(self, graph: WorkflowGraph):
        """Infer edges based on common data flow patterns.

        For example:
        - API call -> Database write (data ingestion)
        - Database read -> API call (data retrieval)
        - Database read -> Transform -> API call (data processing)

        Args:
            graph: Workflow graph to analyze
        """
        from ..models import WorkflowType
        from collections import defaultdict

        print("  Inferring data flow edges...")

        # Create a set of existing edges for O(1) lookup
        existing_edges = {(e.source, e.target) for e in graph.edges}

        # Group nodes by file and type for efficient lookup
        nodes_by_file_and_type = defaultdict(lambda: defaultdict(list))
        for node in graph.nodes:
            nodes_by_file_and_type[node.location.file_path][node.type].append(node)

        edge_count = 0

        # Pattern: API call followed by DB write (data ingestion)
        # Only check within the same file
        for file_path, types_dict in nodes_by_file_and_type.items():
            api_calls = types_dict.get(WorkflowType.API_CALL, [])
            db_writes = types_dict.get(WorkflowType.DATABASE_WRITE, [])

            for api_node in api_calls:
                for db_node in db_writes:
                    if (db_node.location.line_number > api_node.location.line_number and
                        db_node.location.line_number - api_node.location.line_number < 50):

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

        print(f"    Added {edge_count} data ingestion edges")

        # Pattern: DB read followed by transform
        edge_count = 0
        for file_path, types_dict in nodes_by_file_and_type.items():
            db_reads = types_dict.get(WorkflowType.DATABASE_READ, [])
            transforms = types_dict.get(WorkflowType.DATA_TRANSFORM, [])

            for db_node in db_reads:
                for transform_node in transforms:
                    if (transform_node.location.line_number > db_node.location.line_number and
                        transform_node.location.line_number - db_node.location.line_number < 30):

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

        print(f"    Added {edge_count} data processing edges")
