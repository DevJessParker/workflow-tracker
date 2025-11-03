"""WPF/XAML scanner for desktop UI workflow detection."""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseScanner
from scanner.models import (
    WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowType, CodeLocation
)


class WPFScanner(BaseScanner):
    """Scanner for WPF/XAML desktop application UI workflows."""

    # XAML Event Handler Patterns
    XAML_EVENT_PATTERNS = [
        (r'Click\s*=\s*"([^"]+)"', 'ui_click'),                      # Click="Button_Click"
        (r'MouseDown\s*=\s*"([^"]+)"', 'ui_click'),                  # MouseDown="OnMouseDown"
        (r'MouseUp\s*=\s*"([^"]+)"', 'ui_click'),                    # MouseUp="OnMouseUp"
        (r'SelectionChanged\s*=\s*"([^"]+)"', 'ui_change'),          # SelectionChanged="OnSelectionChanged"
        (r'TextChanged\s*=\s*"([^"]+)"', 'ui_change'),               # TextChanged="OnTextChanged"
        (r'KeyDown\s*=\s*"([^"]+)"', 'ui_keypress'),                 # KeyDown="OnKeyDown"
        (r'KeyUp\s*=\s*"([^"]+)"', 'ui_keypress'),                   # KeyUp="OnKeyUp"
        (r'Loaded\s*=\s*"([^"]+)"', 'page_load'),                    # Loaded="Window_Loaded"
        (r'PreviewMouseDown\s*=\s*"([^"]+)"', 'ui_click'),          # PreviewMouseDown="OnPreviewMouseDown"
    ]

    # C# Event Handler Method Patterns (in code-behind)
    EVENT_HANDLER_METHOD_PATTERNS = [
        r'private\s+(?:async\s+)?void\s+(\w+)\s*\(\s*object\s+sender\s*,\s*(?:Routed)?EventArgs\s+\w+\s*\)',
        r'private\s+(?:async\s+)?void\s+(\w+)\s*\(\s*object\s+sender\s*,\s*\w+EventArgs\s+\w+\s*\)',
    ]

    # HTTP Client Patterns (C#)
    HTTP_PATTERNS = [
        (r'HttpClient\s*\(\s*\)', 'HttpClient'),                     # new HttpClient()
        (r'\.GetAsync\s*\(\s*[\'"]([^\'"]+)[\'"]', 'GET'),
        (r'\.PostAsync\s*\(\s*[\'"]([^\'"]+)[\'"]', 'POST'),
        (r'\.PutAsync\s*\(\s*[\'"]([^\'"]+)[\'"]', 'PUT'),
        (r'\.DeleteAsync\s*\(\s*[\'"]([^\'"]+)[\'"]', 'DELETE'),
        (r'WebClient\s*\(\s*\)', 'WebClient'),                       # new WebClient()
        (r'\.DownloadString\s*\(\s*[\'"]([^\'"]+)[\'"]', 'GET'),
        (r'\.UploadString\s*\(\s*[\'"]([^\'"]+)[\'"]', 'POST'),
    ]

    # WPF Window/Page Detection
    WINDOW_PATTERNS = [
        r'<Window\s+x:Class\s*=\s*"([^"]+)"',                        # <Window x:Class="MyApp.MainWindow">
        r'<Page\s+x:Class\s*=\s*"([^"]+)"',                          # <Page x:Class="MyApp.HomePage">
        r'<UserControl\s+x:Class\s*=\s*"([^"]+)"',                   # <UserControl x:Class="MyApp.MyControl">
        r'public\s+partial\s+class\s+(\w+)\s*:\s*Window',            # public partial class MainWindow : Window
        r'public\s+partial\s+class\s+(\w+)\s*:\s*Page',              # public partial class HomePage : Page
        r'public\s+partial\s+class\s+(\w+)\s*:\s*UserControl',       # public partial class MyControl : UserControl
    ]

    # Navigation Patterns
    NAVIGATION_PATTERNS = [
        r'NavigationService\.Navigate\s*\(\s*new\s+(\w+)\s*\(',     # NavigationService.Navigate(new Page())
        r'Frame\.Navigate\s*\(\s*new\s+(\w+)\s*\(',                 # Frame.Navigate(new Page())
        r'this\.NavigationService\.Navigate',                        # this.NavigationService.Navigate
    ]

    def can_scan(self, file_path: str) -> bool:
        """Check if file is a WPF XAML or code-behind file."""
        return file_path.endswith(('.xaml', '.xaml.cs'))

    def scan_file(self, file_path: str) -> WorkflowGraph:
        """Scan WPF file for UI workflows."""
        self.graph = WorkflowGraph()
        content = self.read_file(file_path)

        is_xaml = file_path.endswith('.xaml')
        is_codebehind = file_path.endswith('.xaml.cs')

        if is_xaml:
            # Scan XAML for event handlers
            window_name = self._detect_window_name(content, file_path)
            ui_triggers = self._detect_ui_triggers_from_xaml(file_path, content, window_name)

            # Try to load code-behind to find event handler implementations
            codebehind_content = self._try_load_codebehind(file_path)
            if codebehind_content:
                http_calls = self._detect_http_calls(file_path + '.cs', codebehind_content)
                self._build_ui_workflows(ui_triggers, http_calls)

        elif is_codebehind:
            # Scan code-behind for HTTP calls and event handlers
            window_name = self._detect_window_name(content, file_path)
            event_handlers = self._detect_event_handler_methods(file_path, content, window_name)
            http_calls = self._detect_http_calls(file_path, content)

            # Try to load XAML to find UI event bindings
            xaml_path = file_path.replace('.xaml.cs', '.xaml')
            if Path(xaml_path).exists():
                try:
                    with open(xaml_path, 'r', encoding='utf-8', errors='ignore') as f:
                        xaml_content = f.read()
                    ui_triggers = self._detect_ui_triggers_from_xaml(xaml_path, xaml_content, window_name)
                    self._build_ui_workflows(ui_triggers, http_calls, event_handlers)
                except:
                    pass

        return self.graph

    def _detect_window_name(self, content: str, file_path: str) -> str:
        """Extract window/page name from XAML or C# file."""
        for pattern in self.WINDOW_PATTERNS:
            match = re.search(pattern, content)
            if match:
                name = match.group(1)
                # Extract just the class name if it's a full namespace
                if '.' in name:
                    name = name.split('.')[-1]
                return name

        # Fallback to filename
        return Path(file_path).stem.replace('.xaml', '').replace('.cs', '')

    def _detect_ui_triggers_from_xaml(self, file_path: str, xaml_content: str, window_name: str) -> List:
        """Find WPF event handlers in XAML."""
        triggers = []
        lines = xaml_content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern, trigger_type in self.XAML_EVENT_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    handler = match.group(1).strip()

                    # Create a workflow node for the UI trigger
                    trigger_node = WorkflowNode(
                        id=f"{file_path}:ui_trigger:{i}",
                        type=WorkflowType.DATA_TRANSFORM,  # Using DATA_TRANSFORM as placeholder
                        name=f"WPF: {trigger_type.replace('ui_', '').title()}",
                        description=f"WPF event binding in {window_name}",
                        location=CodeLocation(file_path, i),
                        code_snippet=self.extract_code_snippet(xaml_content, i),
                        metadata={
                            'trigger_type': trigger_type,
                            'window': window_name,
                            'handler': handler,
                            'is_ui_trigger': True,
                            'framework': 'WPF'
                        }
                    )
                    self.graph.add_node(trigger_node)

                    # Store trigger for later workflow building
                    class UITrigger:
                        pass
                    trigger_obj = UITrigger()
                    trigger_obj.trigger_type = trigger_type
                    trigger_obj.window = window_name
                    trigger_obj.handler = handler
                    trigger_obj.location = CodeLocation(file_path, i)
                    triggers.append(trigger_obj)

        return triggers

    def _detect_event_handler_methods(self, file_path: str, content: str, window_name: str) -> Dict[str, CodeLocation]:
        """Find event handler method definitions in code-behind."""
        handlers = {}
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern in self.EVENT_HANDLER_METHOD_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    handler_name = match.group(1)
                    handlers[handler_name] = CodeLocation(file_path, i)

        return handlers

    def _try_load_codebehind(self, xaml_path: str) -> Optional[str]:
        """Try to load the associated code-behind .cs file."""
        codebehind_path = xaml_path + '.cs'
        if Path(codebehind_path).exists():
            try:
                with open(codebehind_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except:
                pass
        return None

    def _detect_http_calls(self, file_path: str, content: str) -> List:
        """Find HTTP calls in C# code-behind."""
        http_calls = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern, method_or_type in self.HTTP_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    # Determine method and endpoint
                    if method_or_type in ['HttpClient', 'WebClient']:
                        # Just instantiation, not an actual call
                        continue

                    method = method_or_type
                    endpoint = match.group(1) if match.lastindex >= 1 else 'unknown'

                    # Create workflow node for HTTP call
                    http_node = WorkflowNode(
                        id=f"{file_path}:http:{i}",
                        type=WorkflowType.API_CALL,
                        name=f"WPF HTTP {method}",
                        description=f"WPF HTTP call to {endpoint}",
                        location=CodeLocation(file_path, i),
                        endpoint=endpoint,
                        method=method,
                        code_snippet=self.extract_code_snippet(content, i),
                        metadata={
                            'library': 'HttpClient/WebClient',
                            'is_frontend_call': True,
                            'framework': 'WPF'
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

    def _build_ui_workflows(self, ui_triggers: List, http_calls: List, event_handlers: Dict[str, CodeLocation] = None):
        """Build workflow chains connecting XAML events to code-behind HTTP calls."""
        if event_handlers is None:
            event_handlers = {}

        for trigger in ui_triggers:
            handler_name = trigger.handler

            # Check if we have this event handler method
            if handler_name in event_handlers:
                handler_location = event_handlers[handler_name]

                # Find HTTP calls within this handler (within ~50 lines)
                for http_call in http_calls:
                    line_distance = abs(http_call.location.line_number - handler_location.line_number)

                    if line_distance <= 50:
                        # Create edge from UI trigger to HTTP call
                        trigger_node_id = f"{trigger.location.file_path}:ui_trigger:{trigger.location.line_number}"
                        http_node_id = f"{http_call.location.file_path}:http:{http_call.location.line_number}"

                        edge = WorkflowEdge(
                            source=trigger_node_id,
                            target=http_node_id,
                            label="WPF Event → HTTP Call",
                            metadata={
                                'workflow_type': 'wpf_ui_to_api',
                                'trigger_type': trigger.trigger_type,
                                'handler': handler_name,
                                'framework': 'WPF'
                            }
                        )
                        self.graph.add_edge(edge)
            else:
                # Handler not found in code-behind, still try proximity matching
                for http_call in http_calls:
                    # If HTTP call is in the code-behind file (same base name)
                    if trigger.location.file_path.replace('.xaml', '.xaml.cs') == http_call.location.file_path:
                        # Create edge (less certain connection)
                        trigger_node_id = f"{trigger.location.file_path}:ui_trigger:{trigger.location.line_number}"
                        http_node_id = f"{http_call.location.file_path}:http:{http_call.location.line_number}"

                        edge = WorkflowEdge(
                            source=trigger_node_id,
                            target=http_node_id,
                            label="WPF Event → HTTP Call (proximity)",
                            metadata={
                                'workflow_type': 'wpf_ui_to_api_proximity',
                                'trigger_type': trigger.trigger_type,
                                'handler': handler_name,
                                'framework': 'WPF'
                            }
                        )
                        self.graph.add_edge(edge)
