"""Workflow graph builder - orchestrates scanning and graph construction."""

import os
import time
from pathlib import Path
from typing import List, Dict, Any

from ..models import WorkflowGraph, WorkflowNode, WorkflowEdge, ScanResult
from ..scanner import CSharpScanner, TypeScriptScanner


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
            CSharpScanner(scanner_config),
            TypeScriptScanner(scanner_config),
        ]

        return scanners

    def build(self, repository_path: str) -> ScanResult:
        """Build workflow graph from repository.

        Args:
            repository_path: Path to repository to scan

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

        # Find all files to scan
        files_to_scan = self._find_files(repository_path, include_extensions, exclude_dirs)

        print(f"Found {len(files_to_scan)} files to scan")

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

                    if result.files_scanned % 10 == 0:
                        print(f"Scanned {result.files_scanned}/{len(files_to_scan)} files...")

            except Exception as e:
                error_msg = f"Error scanning {file_path}: {str(e)}"
                result.errors.append(error_msg)
                print(f"WARNING: {error_msg}")

        # Analyze and create edges based on workflow patterns
        self._infer_workflow_edges(result.graph)

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
        files = []

        for root, dirs, filenames in os.walk(root_path):
            # Remove excluded directories from search
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

            for filename in filenames:
                if any(filename.endswith(ext) for ext in include_extensions):
                    file_path = os.path.join(root, filename)
                    files.append(file_path)

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

    def _infer_workflow_edges(self, graph: WorkflowGraph):
        """Infer edges between nodes based on workflow patterns.

        This creates connections between related workflow steps, such as:
        - API calls followed by database writes
        - Database reads followed by data transforms
        - File reads followed by processing

        Args:
            graph: Workflow graph to analyze
        """
        nodes_by_file = {}

        # Group nodes by file
        for node in graph.nodes:
            file_path = node.location.file_path
            if file_path not in nodes_by_file:
                nodes_by_file[file_path] = []
            nodes_by_file[file_path].append(node)

        # Create edges within each file based on line number proximity
        for file_path, nodes in nodes_by_file.items():
            # Sort nodes by line number
            sorted_nodes = sorted(nodes, key=lambda n: n.location.line_number)

            # Connect adjacent workflow operations (within 20 lines of each other)
            for i in range(len(sorted_nodes) - 1):
                current = sorted_nodes[i]
                next_node = sorted_nodes[i + 1]

                line_distance = next_node.location.line_number - current.location.line_number

                if line_distance <= 20:  # Configurable threshold
                    edge = WorkflowEdge(
                        source=current.id,
                        target=next_node.id,
                        label=f"Sequential ({line_distance} lines)",
                        metadata={'distance': line_distance}
                    )
                    graph.add_edge(edge)

        # Create edges based on data flow patterns
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

        # Find common patterns
        api_calls = graph.get_nodes_by_type(WorkflowType.API_CALL)
        db_writes = graph.get_nodes_by_type(WorkflowType.DATABASE_WRITE)
        db_reads = graph.get_nodes_by_type(WorkflowType.DATABASE_READ)
        transforms = graph.get_nodes_by_type(WorkflowType.DATA_TRANSFORM)

        # Pattern: API call followed by DB write (data ingestion)
        for api_node in api_calls:
            for db_node in db_writes:
                if (api_node.location.file_path == db_node.location.file_path and
                    db_node.location.line_number > api_node.location.line_number and
                    db_node.location.line_number - api_node.location.line_number < 50):

                    # Check if edge doesn't already exist
                    if not any(e.source == api_node.id and e.target == db_node.id for e in graph.edges):
                        edge = WorkflowEdge(
                            source=api_node.id,
                            target=db_node.id,
                            label="Data Ingestion",
                            metadata={'pattern': 'api_to_db'}
                        )
                        graph.add_edge(edge)

        # Pattern: DB read followed by transform followed by output
        for db_node in db_reads:
            for transform_node in transforms:
                if (db_node.location.file_path == transform_node.location.file_path and
                    transform_node.location.line_number > db_node.location.line_number and
                    transform_node.location.line_number - db_node.location.line_number < 30):

                    if not any(e.source == db_node.id and e.target == transform_node.id for e in graph.edges):
                        edge = WorkflowEdge(
                            source=db_node.id,
                            target=transform_node.id,
                            label="Data Processing",
                            metadata={'pattern': 'db_to_transform'}
                        )
                        graph.add_edge(edge)
