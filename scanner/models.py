"""Data models for workflow tracking."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum


class WorkflowType(Enum):
    """Types of workflow operations."""
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    API_CALL = "api_call"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    MESSAGE_SEND = "message_send"
    MESSAGE_RECEIVE = "message_receive"
    DATA_TRANSFORM = "data_transform"
    CACHE_READ = "cache_read"
    CACHE_WRITE = "cache_write"


@dataclass
class CodeLocation:
    """Represents a location in source code."""
    file_path: str
    line_number: int
    column: Optional[int] = None
    end_line: Optional[int] = None

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number}"


@dataclass
class WorkflowNode:
    """Represents a single workflow operation."""
    id: str
    type: WorkflowType
    name: str
    description: str
    location: CodeLocation
    metadata: Dict[str, any] = field(default_factory=dict)
    code_snippet: Optional[str] = None

    # For database operations
    table_name: Optional[str] = None
    query: Optional[str] = None

    # For API calls
    endpoint: Optional[str] = None
    method: Optional[str] = None

    # For file operations
    file_path: Optional[str] = None

    # For message queues
    queue_name: Optional[str] = None
    topic: Optional[str] = None

    def __hash__(self):
        return hash(self.id)


@dataclass
class WorkflowEdge:
    """Represents a connection between workflow nodes."""
    source: str  # Node ID
    target: str  # Node ID
    label: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.source, self.target))


@dataclass
class WorkflowGraph:
    """Represents a complete workflow graph."""
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)

    def add_node(self, node: WorkflowNode):
        """Add a node to the graph."""
        if node not in self.nodes:
            self.nodes.append(node)

    def add_edge(self, edge: WorkflowEdge):
        """Add an edge to the graph."""
        if edge not in self.edges:
            self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Get a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_nodes_by_type(self, workflow_type: WorkflowType) -> List[WorkflowNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes if node.type == workflow_type]

    def get_outgoing_edges(self, node_id: str) -> List[WorkflowEdge]:
        """Get all edges going out from a node."""
        return [edge for edge in self.edges if edge.source == node_id]

    def get_incoming_edges(self, node_id: str) -> List[WorkflowEdge]:
        """Get all edges coming into a node."""
        return [edge for edge in self.edges if edge.target == node_id]


@dataclass
class ScanResult:
    """Results from scanning a repository."""
    repository_path: str
    graph: WorkflowGraph
    files_scanned: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    scan_time_seconds: float = 0.0
