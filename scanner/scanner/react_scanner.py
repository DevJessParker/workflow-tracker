"""React/TypeScript scanner for UI workflow detection."""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseScanner
from scanner.models import (
    WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowType, CodeLocation
)


class UITrigger:
    """Represents a UI interaction that starts a workflow."""
    def __init__(self, trigger_type: str, component: str, handler: str, location: CodeLocation, url: Optional[str] = None):
        self.trigger_type = trigger_type
        self.component = component
        self.handler = handler
        self.location = location
        self.url = url


class HTTPCall:
    """Represents a frontend HTTP call."""
    def __init__(self, method: str, endpoint: str, location: CodeLocation):
        self.method = method
        self.endpoint = endpoint
        self.location = location


class ReactScanner(BaseScanner):
    """Scanner for React/Next.js/TypeScript UI workflows."""

    # UI Event Handler Patterns
    EVENT_HANDLER_PATTERNS = [
        (r'onClick\s*=\s*\{([^\}]+)\}', 'ui_click'),           # onClick={handleClick}
        (r'onSubmit\s*=\s*\{([^\}]+)\}', 'ui_submit'),         # onSubmit={handleSubmit}
        (r'onChange\s*=\s*\{([^\}]+)\}', 'ui_change'),         # onChange={handleChange}
        (r'onLoad\s*=\s*\{([^\}]+)\}', 'page_load'),           # onLoad={handleLoad}
    ]

    # HTTP Call Patterns
    HTTP_PATTERNS = [
        (r'fetch\s*\(\s*[\'"]([^\'"]+)[\'"](?:.*?method\s*:\s*[\'"](\w+)[\'"])?', 'fetch'),
        (r'axios\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]', 'axios'),
        (r'http\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]', 'http'),
    ]

    # Component Detection
    COMPONENT_PATTERNS = [
        r'export\s+(?:default\s+)?(?:function|const)\s+(\w+)',
        r'const\s+(\w+)\s*[=:]\s*\([^)]*\)\s*(?:=>|:)',
        r'function\s+(\w+)\s*\([^)]*\)',
    ]

    # Route/URL Detection
    ROUTE_PATTERNS = [
        r'<Route\s+path\s*=\s*[\'"]([^\'"]+)[\'"]',
        r'path\s*:\s*[\'"]([^\'"]+)[\'"]',
        r'href\s*=\s*[\'"]([^\'"]+)[\'"]',
    ]

    def can_scan(self, file_path: str) -> bool:
        """Check if file is a React/TypeScript file."""
        return file_path.endswith(('.tsx', '.ts', '.jsx', '.js'))

    def scan_file(self, file_path: str) -> WorkflowGraph:
        """Scan React/TypeScript file for UI workflows."""
        self.graph = WorkflowGraph()
        content = self.read_file(file_path)

        # Detect component name
        component_name = self._detect_component_name(file_path, content)

        # Detect URL/route
        url = self._detect_url(content)

        # Detect UI event handlers (triggers)
        ui_triggers = self._detect_ui_triggers(file_path, content, component_name, url)

        # Detect HTTP calls
        http_calls = self._detect_http_calls(file_path, content)

        # Build workflow chains: UI trigger → HTTP call → (backend will be matched later)
        self._build_ui_workflows(ui_triggers, http_calls)

        return self.graph

    def _detect_component_name(self, file_path: str, content: str) -> str:
        """Extract component name from file."""
        # Try to get from export
        for pattern in self.COMPONENT_PATTERNS:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        # Fallback to filename
        return Path(file_path).stem

    def _detect_url(self, content: str) -> Optional[str]:
        """Detect the URL/route this component belongs to."""
        for pattern in self.ROUTE_PATTERNS:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return None

    def _detect_ui_triggers(self, file_path: str, content: str, component: str, url: Optional[str]) -> List[UITrigger]:
        """Find UI event handlers (onClick, onSubmit, etc.)."""
        triggers = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern, trigger_type in self.EVENT_HANDLER_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    handler = match.group(1).strip()
                    # Clean up handler name (remove () if present)
                    handler = handler.replace('()', '').replace('(', '').replace(')', '')

                    trigger = UITrigger(
                        trigger_type=trigger_type,
                        component=component,
                        handler=handler,
                        location=CodeLocation(file_path, i),
                        url=url
                    )
                    triggers.append(trigger)

                    # Create a workflow node for the UI trigger
                    trigger_node = WorkflowNode(
                        id=f"{file_path}:ui_trigger:{i}",
                        type=WorkflowType.DATA_TRANSFORM,  # Using DATA_TRANSFORM as placeholder for UI events
                        name=f"UI: {trigger_type.replace('ui_', '').title()}",
                        description=f"User interaction in {component}",
                        location=CodeLocation(file_path, i),
                        code_snippet=self.extract_code_snippet(content, i),
                        metadata={
                            'trigger_type': trigger_type,
                            'component': component,
                            'handler': handler,
                            'url': url,
                            'is_ui_trigger': True
                        }
                    )
                    self.graph.add_node(trigger_node)

        return triggers

    def _detect_http_calls(self, file_path: str, content: str) -> List[HTTPCall]:
        """Find HTTP calls (fetch, axios, etc.)."""
        http_calls = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check each HTTP pattern
            for pattern, lib_type in self.HTTP_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    if lib_type == 'fetch':
                        endpoint = match.group(1)
                        method = match.group(2) if match.lastindex >= 2 else self._extract_method_from_context(lines, i)
                        if not method:
                            method = 'GET'
                    elif lib_type in ['axios', 'http']:
                        method = match.group(1).upper()
                        endpoint = match.group(2)
                    else:
                        continue

                    http_call = HTTPCall(
                        method=method,
                        endpoint=endpoint,
                        location=CodeLocation(file_path, i)
                    )
                    http_calls.append(http_call)

                    # Create workflow node for HTTP call
                    http_node = WorkflowNode(
                        id=f"{file_path}:http:{i}",
                        type=WorkflowType.API_CALL,
                        name=f"HTTP {method}",
                        description=f"Frontend API call to {endpoint}",
                        location=CodeLocation(file_path, i),
                        endpoint=endpoint,
                        method=method,
                        code_snippet=self.extract_code_snippet(content, i),
                        metadata={
                            'library': lib_type,
                            'is_frontend_call': True
                        }
                    )
                    self.graph.add_node(http_node)

        return http_calls

    def _extract_method_from_context(self, lines: List[str], line_num: int) -> Optional[str]:
        """Extract HTTP method from surrounding context (for fetch calls)."""
        # Look at current line and a few lines around it
        context_lines = lines[max(0, line_num-3):min(len(lines), line_num+3)]
        context = ' '.join(context_lines)

        # Look for method: 'POST' pattern
        method_match = re.search(r'method\s*:\s*[\'"](\w+)[\'"]', context, re.IGNORECASE)
        if method_match:
            return method_match.group(1).upper()

        return None

    def _build_ui_workflows(self, ui_triggers: List[UITrigger], http_calls: List[HTTPCall]):
        """Build workflow chains connecting UI triggers to HTTP calls."""
        # For each UI trigger, find HTTP calls that are likely related
        # (within same function scope, close line numbers)

        for trigger in ui_triggers:
            # Find HTTP calls within ~50 lines of the trigger
            for http_call in http_calls:
                line_distance = abs(http_call.location.line_number - trigger.location.line_number)

                # If HTTP call is close to the trigger (likely related)
                if line_distance <= 50:
                    # Create edge from UI trigger to HTTP call
                    trigger_node_id = f"{trigger.location.file_path}:ui_trigger:{trigger.location.line_number}"
                    http_node_id = f"{http_call.location.file_path}:http:{http_call.location.line_number}"

                    edge = WorkflowEdge(
                        source=trigger_node_id,
                        target=http_node_id,
                        label="User Action → API Call",
                        metadata={
                            'workflow_type': 'ui_to_api',
                            'trigger_type': trigger.trigger_type,
                            'url': trigger.url
                        }
                    )
                    self.graph.add_edge(edge)
