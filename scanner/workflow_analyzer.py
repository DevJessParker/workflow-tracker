"""
UI Workflow Analyzer - Traces user interactions through the system

This module identifies UI entry points and traces their execution paths to create
user-friendly workflow stories for developers and non-technical stakeholders.
"""

from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

from models import WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowType


@dataclass
class UIInteraction:
    """Represents a UI interaction (button click, form submit, etc.)"""
    id: str
    name: str  # User-friendly name like "Save Customer Button"
    component: str  # Component name (e.g., "CustomerForm", "SaveButton")
    interaction_type: str  # "button_click", "form_submit", "page_load", etc.
    location: str  # File path
    description: str  # What the user sees/does
    node: WorkflowNode


@dataclass
class WorkflowStep:
    """A single step in a UI workflow"""
    step_number: int
    title: str  # User-friendly title
    description: str  # Plain language description
    technical_details: str  # For developers
    node: WorkflowNode
    icon: str  # Emoji or icon for visual representation


@dataclass
class UIWorkflow:
    """Complete workflow from user action to response"""
    id: str
    name: str  # User-friendly name like "Save Customer Information"
    trigger: UIInteraction  # What starts this workflow
    steps: List[WorkflowStep] = field(default_factory=list)
    summary: str = ""  # Plain language summary for non-technical users
    outcome: str = ""  # What the user sees/gets at the end

    def to_story(self) -> str:
        """Generate a narrative story of the workflow"""
        story_parts = [
            f"# {self.name}\n",
            f"\n**What happens:** {self.summary}\n",
            f"\n**User action:** {self.trigger.description}\n",
            f"\n## Workflow Steps:\n"
        ]

        for step in self.steps:
            story_parts.append(f"\n{step.icon} **Step {step.step_number}: {step.title}**")
            story_parts.append(f"\n{step.description}")
            story_parts.append(f"\n_Technical: {step.technical_details}_\n")

        story_parts.append(f"\n**Result:** {self.outcome}\n")

        return "\n".join(story_parts)


class WorkflowAnalyzer:
    """Analyzes workflow graphs to extract user-centric workflow stories"""

    def __init__(self, graph: WorkflowGraph):
        self.graph = graph
        self.ui_interactions = []
        self.workflows = []

    def analyze(self) -> List[UIWorkflow]:
        """Analyze graph and extract UI workflows"""
        print("\n" + "="*60)
        print("ANALYZING UI WORKFLOWS")
        print("="*60)

        # Step 1: Identify UI interaction entry points
        self.ui_interactions = self._identify_ui_interactions()
        print(f"✓ Found {len(self.ui_interactions)} UI interactions")

        # Step 2: Build workflow chains from each UI interaction
        for interaction in self.ui_interactions:
            workflow = self._build_workflow_chain(interaction)
            if workflow and len(workflow.steps) > 0:
                self.workflows.append(workflow)

        print(f"✓ Built {len(self.workflows)} complete workflows")
        print("="*60 + "\n")

        return self.workflows

    def _identify_ui_interactions(self) -> List[UIInteraction]:
        """Identify UI entry points in the graph"""
        interactions = []

        for node in self.graph.nodes:
            # Look for UI-related patterns in metadata
            metadata = node.metadata or {}

            # Check if node represents a UI interaction
            if self._is_ui_interaction(node):
                interaction = self._create_ui_interaction(node)
                if interaction:
                    interactions.append(interaction)

        return interactions

    def _is_ui_interaction(self, node: WorkflowNode) -> bool:
        """Check if a node represents a UI interaction"""
        # Check node name for UI patterns
        ui_keywords = [
            'onclick', 'onsubmit', 'button', 'click', 'submit',
            'handlesubmit', 'handleclick', 'onsave', 'onload',
            'eventhandler', 'command', 'action'
        ]

        name_lower = node.name.lower()
        return any(keyword in name_lower for keyword in ui_keywords)

    def _create_ui_interaction(self, node: WorkflowNode) -> Optional[UIInteraction]:
        """Create a UI interaction from a node"""
        # Extract user-friendly name
        name = self._humanize_node_name(node.name)

        # Determine interaction type
        name_lower = node.name.lower()
        if 'submit' in name_lower:
            interaction_type = 'form_submit'
            description = f"User submits {name}"
        elif 'save' in name_lower:
            interaction_type = 'button_click'
            description = f"User clicks {name}"
        elif 'load' in name_lower:
            interaction_type = 'page_load'
            description = f"User navigates to {name}"
        elif 'delete' in name_lower:
            interaction_type = 'button_click'
            description = f"User clicks {name}"
        else:
            interaction_type = 'button_click'
            description = f"User interacts with {name}"

        return UIInteraction(
            id=node.id,
            name=name,
            component=self._extract_component_name(node),
            interaction_type=interaction_type,
            location=node.location.file_path,
            description=description,
            node=node
        )

    def _build_workflow_chain(self, interaction: UIInteraction) -> Optional[UIWorkflow]:
        """Build a complete workflow chain from a UI interaction"""
        workflow = UIWorkflow(
            id=f"workflow_{interaction.id}",
            name=interaction.name,
            trigger=interaction
        )

        # Traverse graph from this node
        visited = set()
        step_number = 1

        # Get all nodes reachable from this interaction
        reachable_nodes = self._get_reachable_nodes(interaction.node, visited)

        # Sort by line number to get execution order
        reachable_nodes.sort(key=lambda n: (n.location.file_path, n.location.line_number))

        # Convert nodes to workflow steps
        for node in reachable_nodes:
            step = self._create_workflow_step(node, step_number)
            workflow.steps.append(step)
            step_number += 1

        # Generate summary and outcome
        workflow.summary = self._generate_workflow_summary(workflow)
        workflow.outcome = self._determine_workflow_outcome(workflow)

        return workflow

    def _get_reachable_nodes(self, start_node: WorkflowNode, visited: set) -> List[WorkflowNode]:
        """Get all nodes reachable from start node"""
        reachable = []
        queue = [start_node]

        while queue:
            current = queue.pop(0)

            if current.id in visited:
                continue

            visited.add(current.id)
            reachable.append(current)

            # Get outgoing edges
            outgoing = self.graph.get_outgoing_edges(current.id)

            # Add target nodes to queue
            for edge in outgoing:
                target = self.graph.get_node(edge.target)
                if target and target.id not in visited:
                    queue.append(target)

        return reachable

    def _create_workflow_step(self, node: WorkflowNode, step_number: int) -> WorkflowStep:
        """Create a user-friendly workflow step from a node"""
        # Determine icon based on type
        icon_map = {
            WorkflowType.DATABASE_READ: "📖",
            WorkflowType.DATABASE_WRITE: "💾",
            WorkflowType.API_CALL: "🌐",
            WorkflowType.FILE_READ: "📄",
            WorkflowType.FILE_WRITE: "📝",
            WorkflowType.MESSAGE_SEND: "📤",
            WorkflowType.MESSAGE_RECEIVE: "📥",
            WorkflowType.DATA_TRANSFORM: "⚙️",
            WorkflowType.CACHE_READ: "🔍",
            WorkflowType.CACHE_WRITE: "💿",
        }

        icon = icon_map.get(node.type, "•")

        # Create user-friendly title and description
        if node.type == WorkflowType.DATABASE_WRITE:
            title = f"Save data to {node.table_name or 'database'}"
            description = f"The system saves the information to the {node.table_name or 'database'} table."
            technical = f"Database INSERT/UPDATE: {node.table_name}"

        elif node.type == WorkflowType.DATABASE_READ:
            title = f"Retrieve data from {node.table_name or 'database'}"
            description = f"The system looks up existing information from the {node.table_name or 'database'} table."
            technical = f"Database SELECT: {node.table_name}"

        elif node.type == WorkflowType.API_CALL:
            title = f"Call {node.method or 'API'} {self._humanize_endpoint(node.endpoint)}"
            description = f"The system communicates with an external service at {node.endpoint or 'an external endpoint'}."
            technical = f"API {node.method}: {node.endpoint}"

        elif node.type == WorkflowType.DATA_TRANSFORM:
            title = "Process and transform data"
            description = "The system transforms the data into the required format."
            technical = f"Data transformation: {node.name}"

        elif node.type == WorkflowType.FILE_WRITE:
            title = f"Write to file"
            description = f"The system saves information to a file."
            technical = f"File write: {node.file_path or 'unknown'}"

        elif node.type == WorkflowType.FILE_READ:
            title = f"Read from file"
            description = f"The system reads information from a file."
            technical = f"File read: {node.file_path or 'unknown'}"

        else:
            title = self._humanize_node_name(node.name)
            description = node.description or "The system performs an operation."
            technical = f"{node.type.value}: {node.name}"

        return WorkflowStep(
            step_number=step_number,
            title=title,
            description=description,
            technical_details=technical,
            node=node,
            icon=icon
        )

    def _generate_workflow_summary(self, workflow: UIWorkflow) -> str:
        """Generate a plain language summary of the workflow"""
        if not workflow.steps:
            return "This workflow performs a simple operation."

        # Count operation types
        db_writes = sum(1 for s in workflow.steps if s.node.type == WorkflowType.DATABASE_WRITE)
        db_reads = sum(1 for s in workflow.steps if s.node.type == WorkflowType.DATABASE_READ)
        api_calls = sum(1 for s in workflow.steps if s.node.type == WorkflowType.API_CALL)

        parts = []

        if db_reads > 0:
            parts.append(f"retrieves data from {db_reads} database table(s)")

        if api_calls > 0:
            parts.append(f"calls {api_calls} external service(s)")

        if db_writes > 0:
            parts.append(f"saves data to {db_writes} database table(s)")

        if parts:
            return "This workflow " + ", then ".join(parts) + "."

        return f"This workflow performs {len(workflow.steps)} operation(s)."

    def _determine_workflow_outcome(self, workflow: UIWorkflow) -> str:
        """Determine what the user sees/gets at the end"""
        if not workflow.steps:
            return "The action completes."

        last_step = workflow.steps[-1]

        if last_step.node.type == WorkflowType.DATABASE_WRITE:
            return "The data is saved and the user sees a success confirmation."

        elif last_step.node.type == WorkflowType.DATABASE_READ:
            return "The data is retrieved and displayed to the user."

        elif last_step.node.type == WorkflowType.API_CALL:
            return "The external service responds and the result is shown to the user."

        else:
            return "The action completes and the user sees the result."

    def _humanize_node_name(self, name: str) -> str:
        """Convert technical node name to user-friendly name"""
        # Remove common prefixes
        name = name.replace('handle', '').replace('on', '')

        # Convert camelCase to Title Case
        import re
        name = re.sub('([A-Z])', r' \1', name).strip()

        # Capitalize
        return name.title()

    def _humanize_endpoint(self, endpoint: Optional[str]) -> str:
        """Convert API endpoint to user-friendly name"""
        if not endpoint:
            return "service"

        # Extract meaningful part
        parts = endpoint.split('/')
        meaningful = [p for p in parts if p and not p.startswith('{')]

        if meaningful:
            return ' '.join(meaningful[-2:]).replace('-', ' ').title()

        return "service"

    def _extract_component_name(self, node: WorkflowNode) -> str:
        """Extract component name from file path"""
        import os
        filename = os.path.basename(node.location.file_path)
        # Remove extension
        return os.path.splitext(filename)[0]

    def generate_user_friendly_diagram(self, workflow: UIWorkflow) -> str:
        """Generate a Mermaid diagram optimized for non-technical users"""
        lines = [
            "graph TD",
            "    classDef userAction fill:#4CAF50,stroke:#45a049,stroke-width:3px,color:#fff",
            "    classDef database fill:#2196F3,stroke:#1976D2,stroke-width:2px,color:#fff",
            "    classDef api fill:#FF9800,stroke:#F57C00,stroke-width:2px,color:#fff",
            "    classDef process fill:#9C27B0,stroke:#7B1FA2,stroke-width:2px,color:#fff",
            "    classDef result fill:#4CAF50,stroke:#45a049,stroke-width:2px,color:#fff",
            ""
        ]

        # Add trigger node
        trigger_id = "start"
        lines.append(f'    {trigger_id}["{workflow.trigger.description}"]:::userAction')

        # Add workflow steps
        prev_id = trigger_id
        for step in workflow.steps:
            step_id = f"step{step.step_number}"
            label = f"{step.icon} {step.title}"

            # Determine class based on type
            if step.node.type in [WorkflowType.DATABASE_READ, WorkflowType.DATABASE_WRITE]:
                node_class = "database"
            elif step.node.type == WorkflowType.API_CALL:
                node_class = "api"
            else:
                node_class = "process"

            lines.append(f'    {step_id}["{label}"]:::{node_class}')
            lines.append(f'    {prev_id} --> {step_id}')
            prev_id = step_id

        # Add result node
        result_id = "result"
        lines.append(f'    {result_id}["{workflow.outcome}"]:::result')
        lines.append(f'    {prev_id} --> {result_id}')

        return "\n".join(lines)
