"""Angular scanner for UI workflow detection."""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseScanner
from models import (
    WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowType, CodeLocation
)


class AngularScanner(BaseScanner):
    """Scanner for Angular/TypeScript UI workflows."""

    # Angular Event Binding Patterns (Angular uses parentheses for events)
    EVENT_HANDLER_PATTERNS = [
        (r'\(click\)\s*=\s*"([^"]+)"', 'ui_click'),           # (click)="handleClick()"
        (r'\(submit\)\s*=\s*"([^"]+)"', 'ui_submit'),         # (submit)="onSubmit()"
        (r'\(ngSubmit\)\s*=\s*"([^"]+)"', 'ui_submit'),       # (ngSubmit)="onSubmit()"
        (r'\(change\)\s*=\s*"([^"]+)"', 'ui_change'),         # (change)="onChange()"
        (r'\(input\)\s*=\s*"([^"]+)"', 'ui_change'),          # (input)="onInput()"
        (r'\(mousedown\)\s*=\s*"([^"]+)"', 'ui_click'),       # (mousedown)="onMouseDown()"
        (r'\(keyup\)\s*=\s*"([^"]+)"', 'ui_keypress'),        # (keyup)="onKeyUp()"
    ]

    # Angular HTTP Client Patterns
    HTTP_PATTERNS = [
        (r'this\.http\.get\s*<[^>]+>\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'GET'),
        (r'this\.http\.post\s*<[^>]+>\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'POST'),
        (r'this\.http\.put\s*<[^>]+>\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'PUT'),
        (r'this\.http\.delete\s*<[^>]+>\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'DELETE'),
        (r'this\.http\.patch\s*<[^>]+>\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'PATCH'),
        # Without type parameter
        (r'this\.http\.get\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'GET'),
        (r'this\.http\.post\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'POST'),
        (r'this\.http\.put\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'PUT'),
        (r'this\.http\.delete\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'DELETE'),
        (r'this\.http\.patch\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'PATCH'),
    ]

    # Angular Component Detection
    COMPONENT_PATTERNS = [
        r'@Component\s*\(\s*\{[^}]*selector\s*:\s*[\'"]([^\'"]+)[\'"]',  # @Component({ selector: 'app-name' })
        r'export\s+class\s+(\w+)Component',  # export class MyComponent
    ]

    # Angular Route Detection
    ROUTE_PATTERNS = [
        r'path\s*:\s*[\'"]([^\'"]+)[\'"]',           # { path: '/checkout' }
        r'RouterModule\.forRoot\s*\([^)]*\)',         # RouterModule.forRoot([...])
        r'this\.router\.navigate\s*\(\s*\[[\'"]([^\'"]+)[\'"]', # this.router.navigate(['/path'])
    ]

    def can_scan(self, file_path: str) -> bool:
        """Check if file is an Angular TypeScript or HTML file."""
        return file_path.endswith(('.ts', '.html', '.component.ts', '.component.html'))

    def scan_file(self, file_path: str, schema_registry: dict = None) -> WorkflowGraph:
        """Scan Angular file for UI workflows."""
        self.graph = WorkflowGraph()
        content = self.read_file(file_path)

        # Determine file type
        is_template = file_path.endswith('.html')
        is_typescript = file_path.endswith('.ts')

        if is_template:
            # Scan HTML template for event bindings
            component_name = self._detect_component_name_from_path(file_path)
            url = self._detect_url(content)
            ui_triggers = self._detect_ui_triggers_from_template(file_path, content, component_name, url)

        elif is_typescript:
            # Scan TypeScript file for component and HTTP calls
            component_name = self._detect_component_name(content, file_path)
            url = self._detect_url(content)

            # Check if this is a component file (has @Component decorator)
            if '@Component' in content:
                # Look for corresponding template file for UI triggers
                template_content = self._try_load_template(file_path, content)
                if template_content:
                    ui_triggers = self._detect_ui_triggers_from_template(file_path, template_content, component_name, url)
                else:
                    ui_triggers = []
            else:
                ui_triggers = []

            # Detect HTTP calls in TypeScript
            http_calls = self._detect_http_calls(file_path, content)

            # Build workflow chains
            self._build_ui_workflows(ui_triggers, http_calls)

        return self.graph

    def _detect_component_name(self, content: str, file_path: str) -> str:
        """Extract component name from TypeScript file."""
        # Try @Component selector
        for pattern in self.COMPONENT_PATTERNS:
            match = re.search(pattern, content)
            if match:
                name = match.group(1)
                # Clean up selector (remove 'app-' prefix if present)
                if name.startswith('app-'):
                    name = name[4:]
                return name.replace('-', ' ').title()

        # Fallback to filename
        return self._detect_component_name_from_path(file_path)

    def _detect_component_name_from_path(self, file_path: str) -> str:
        """Extract component name from file path."""
        stem = Path(file_path).stem
        # Remove .component suffix if present
        if stem.endswith('.component'):
            stem = stem[:-10]
        return stem.replace('-', ' ').title()

    def _detect_url(self, content: str) -> Optional[str]:
        """Detect the URL/route this component belongs to."""
        for pattern in self.ROUTE_PATTERNS:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return None

    def _try_load_template(self, ts_file_path: str, ts_content: str) -> Optional[str]:
        """Try to load the associated HTML template file."""
        # Method 1: Check for templateUrl in @Component
        template_match = re.search(r'templateUrl\s*:\s*[\'"]([^\'"]+)[\'"]', ts_content)
        if template_match:
            template_filename = template_match.group(1)
            # Resolve relative path
            ts_dir = Path(ts_file_path).parent
            template_path = ts_dir / template_filename
            if template_path.exists():
                try:
                    with open(template_path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                except:
                    pass

        # Method 2: Look for .component.html file with same base name
        base_path = ts_file_path.replace('.component.ts', '.component.html').replace('.ts', '.html')
        if Path(base_path).exists():
            try:
                with open(base_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except:
                pass

        return None

    def _detect_ui_triggers_from_template(self, file_path: str, template_content: str, component: str, url: Optional[str]) -> List:
        """Find Angular event bindings in HTML template."""
        triggers = []
        lines = template_content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern, trigger_type in self.EVENT_HANDLER_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    handler = match.group(1).strip()
                    # Clean up handler name (remove () if present)
                    handler = handler.replace('()', '').replace('($event)', '')

                    # Create a workflow node for the UI trigger
                    trigger_node = WorkflowNode(
                        id=f"{file_path}:ui_trigger:{i}",
                        type=WorkflowType.DATA_TRANSFORM,  # Using DATA_TRANSFORM as placeholder for UI events
                        name=f"Angular: {trigger_type.replace('ui_', '').title()}",
                        description=f"Angular event binding in {component}",
                        location=CodeLocation(file_path, i),
                        code_snippet=self.extract_code_snippet(template_content, i),
                        metadata={
                            'trigger_type': trigger_type,
                            'component': component,
                            'handler': handler,
                            'url': url,
                            'is_ui_trigger': True,
                            'framework': 'Angular'
                        }
                    )
                    self.graph.add_node(trigger_node)

                    # Store trigger for later workflow building
                    class UITrigger:
                        pass
                    trigger_obj = UITrigger()
                    trigger_obj.trigger_type = trigger_type
                    trigger_obj.component = component
                    trigger_obj.handler = handler
                    trigger_obj.location = CodeLocation(file_path, i)
                    trigger_obj.url = url
                    triggers.append(trigger_obj)

        return triggers

    def _detect_http_calls(self, file_path: str, content: str) -> List:
        """Find Angular HttpClient calls in TypeScript."""
        http_calls = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern, method in self.HTTP_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    endpoint = match.group(1)

                    # Create workflow node for HTTP call
                    http_node = WorkflowNode(
                        id=f"{file_path}:http:{i}",
                        type=WorkflowType.API_CALL,
                        name=f"Angular HTTP {method}",
                        description=f"Angular HttpClient call to {endpoint}",
                        location=CodeLocation(file_path, i),
                        endpoint=endpoint,
                        method=method,
                        code_snippet=self.extract_code_snippet(content, i),
                        metadata={
                            'library': 'HttpClient',
                            'is_frontend_call': True,
                            'framework': 'Angular'
                        }
                    )
                    self.graph.add_node(http_node)

                    # Store for workflow building
                    class HTTPCall:
                        pass
                    http_call = HTTPCall()
                    http_call.method = method
                    http_call.endpoint = endpoint
                    http_call.location = CodeLocation(file_path, i)
                    http_calls.append(http_call)

        return http_calls

    def _build_ui_workflows(self, ui_triggers: List, http_calls: List):
        """Build workflow chains connecting UI triggers to HTTP calls."""
        # For each UI trigger, find HTTP calls that are likely related
        for trigger in ui_triggers:
            # Match by handler name (method name in TypeScript)
            handler_name = trigger.handler.split('(')[0]  # Remove any parameters

            # Find HTTP calls within the same file or close proximity
            for http_call in http_calls:
                # Calculate line distance
                line_distance = abs(http_call.location.line_number - trigger.location.line_number)

                # If HTTP call is close to the trigger (within 100 lines in Angular components)
                # Angular components tend to be larger, so increase proximity range
                if line_distance <= 100 or trigger.location.file_path == http_call.location.file_path:
                    # Create edge from UI trigger to HTTP call
                    trigger_node_id = f"{trigger.location.file_path}:ui_trigger:{trigger.location.line_number}"
                    http_node_id = f"{http_call.location.file_path}:http:{http_call.location.line_number}"

                    edge = WorkflowEdge(
                        source=trigger_node_id,
                        target=http_node_id,
                        label="Angular Event → HTTP Call",
                        metadata={
                            'workflow_type': 'angular_ui_to_api',
                            'trigger_type': trigger.trigger_type,
                            'url': trigger.url,
                            'framework': 'Angular'
                        }
                    )
                    self.graph.add_edge(edge)
