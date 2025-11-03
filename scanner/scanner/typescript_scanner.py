"""TypeScript/Angular scanner for workflow detection."""

import re
from typing import List
from .base import BaseScanner
from scanner.models import (
    WorkflowGraph, WorkflowNode, WorkflowType, CodeLocation
)


class TypeScriptScanner(BaseScanner):
    """Scanner for TypeScript/Angular code to detect data workflows."""

    # HTTP client patterns (Angular HttpClient)
    HTTP_PATTERNS = [
        r'http\.get',
        r'http\.post',
        r'http\.put',
        r'http\.delete',
        r'http\.patch',
        r'fetch\s*\(',
        r'axios\.',
    ]

    # Local storage / cache patterns
    STORAGE_PATTERNS = [
        r'localStorage\.setItem',
        r'localStorage\.getItem',
        r'sessionStorage\.setItem',
        r'sessionStorage\.getItem',
        r'indexedDB',
    ]

    # File operations (if applicable)
    FILE_PATTERNS = [
        r'FileReader',
        r'\.readAsText',
        r'\.readAsDataURL',
        r'Blob',
    ]

    def can_scan(self, file_path: str) -> bool:
        """Check if file is a TypeScript/JavaScript file."""
        return file_path.endswith(('.ts', '.js', '.tsx', '.jsx'))

    def scan_file(self, file_path: str) -> WorkflowGraph:
        """Scan TypeScript file for workflow patterns."""
        self.graph = WorkflowGraph()
        content = self.read_file(file_path)

        # Scan for different workflow types
        if self.should_detect_type('api_calls'):
            self._scan_http_calls(file_path, content)

        if self.should_detect_type('file_io'):
            self._scan_file_operations(file_path, content)

        # Scan for cache/storage operations
        self._scan_storage_operations(file_path, content)

        # Scan for data transformations (RxJS pipes, map operations)
        if self.should_detect_type('data_transforms'):
            self._scan_data_transforms(file_path, content)

        return self.graph

    def _scan_http_calls(self, file_path: str, content: str):
        """Scan for HTTP/API calls."""
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern in self.HTTP_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    endpoint = self._extract_endpoint(line, lines, i)
                    method = self._extract_http_method(line)

                    node = WorkflowNode(
                        id=f"{file_path}:api:{i}",
                        type=WorkflowType.API_CALL,
                        name=f"API {method}: {endpoint or 'Unknown'}",
                        description=f"HTTP API call from Angular/TypeScript",
                        location=CodeLocation(file_path, i),
                        endpoint=endpoint,
                        method=method,
                        code_snippet=self.extract_code_snippet(content, i),
                    )
                    self.graph.add_node(node)
                    break

    def _scan_file_operations(self, file_path: str, content: str):
        """Scan for file operations."""
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern in self.FILE_PATTERNS:
                if re.search(pattern, line):
                    is_read = bool(re.search(r'read|Reader', line, re.IGNORECASE))

                    node = WorkflowNode(
                        id=f"{file_path}:file:{i}",
                        type=WorkflowType.FILE_READ if is_read else WorkflowType.FILE_WRITE,
                        name=f"File {'Read' if is_read else 'Write'}",
                        description=f"Browser file API operation",
                        location=CodeLocation(file_path, i),
                        code_snippet=self.extract_code_snippet(content, i),
                    )
                    self.graph.add_node(node)
                    break

    def _scan_storage_operations(self, file_path: str, content: str):
        """Scan for localStorage, sessionStorage, IndexedDB operations."""
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern in self.STORAGE_PATTERNS:
                if re.search(pattern, line):
                    is_read = bool(re.search(r'getItem|get', line))
                    storage_key = self._extract_storage_key(line)

                    node = WorkflowNode(
                        id=f"{file_path}:cache:{i}",
                        type=WorkflowType.CACHE_READ if is_read else WorkflowType.CACHE_WRITE,
                        name=f"Cache {'Read' if is_read else 'Write'}: {storage_key or 'Unknown'}",
                        description=f"Browser storage operation",
                        location=CodeLocation(file_path, i),
                        code_snippet=self.extract_code_snippet(content, i),
                        metadata={'key': storage_key}
                    )
                    self.graph.add_node(node)
                    break

    def _scan_data_transforms(self, file_path: str, content: str):
        """Scan for data transformation operations (RxJS, map, reduce, etc.)."""
        lines = content.split('\n')

        # RxJS operators
        rxjs_operators = [
            r'\.pipe\s*\(',
            r'\.map\s*\(',
            r'\.filter\s*\(',
            r'\.reduce\s*\(',
            r'\.switchMap\s*\(',
            r'\.mergeMap\s*\(',
            r'\.concatMap\s*\(',
        ]

        for i, line in enumerate(lines, 1):
            for pattern in rxjs_operators:
                if re.search(pattern, line):
                    operator = re.search(r'\.(pipe|map|filter|reduce|switchMap|mergeMap|concatMap)', line)
                    operator_name = operator.group(1) if operator else 'transform'

                    node = WorkflowNode(
                        id=f"{file_path}:transform:{i}",
                        type=WorkflowType.DATA_TRANSFORM,
                        name=f"Data Transform: {operator_name}",
                        description=f"Data transformation using {operator_name}",
                        location=CodeLocation(file_path, i),
                        code_snippet=self.extract_code_snippet(content, i),
                        metadata={'operator': operator_name}
                    )
                    self.graph.add_node(node)
                    break

    def _extract_endpoint(self, line: str, all_lines: List[str], line_num: int) -> str:
        """Extract API endpoint from HTTP call."""
        # Look for URL in string literals or template literals
        url_match = re.search(r'[\'"`](https?://[^\'"`]+|/[^\'"`]*)[\'"`]', line)
        if url_match:
            return url_match.group(1)

        # Look for template literals with ${...}
        template_match = re.search(r'`([^`]*)`', line)
        if template_match:
            return template_match.group(1)

        # Look in nearby lines
        for i in range(max(0, line_num - 3), min(len(all_lines), line_num + 1)):
            url_match = re.search(r'[\'"`](https?://[^\'"`]+|/api/[^\'"`]*)[\'"`]', all_lines[i])
            if url_match:
                return url_match.group(1)

        return None

    def _extract_http_method(self, line: str) -> str:
        """Extract HTTP method from call."""
        methods = {
            'get': 'GET',
            'post': 'POST',
            'put': 'PUT',
            'delete': 'DELETE',
            'patch': 'PATCH',
        }

        for method, http_method in methods.items():
            if re.search(rf'\.{method}\s*\(', line, re.IGNORECASE):
                return http_method

        return 'HTTP'

    def _extract_storage_key(self, line: str) -> str:
        """Extract storage key from localStorage/sessionStorage operation."""
        # Look for string literal as first parameter
        match = re.search(r'(?:getItem|setItem)\s*\(\s*[\'"]([^\'"]+)[\'"]', line)
        if match:
            return match.group(1)
        return None
