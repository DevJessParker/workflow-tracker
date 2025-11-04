"""
API Routes Analyzer - Analyzes API endpoints, payloads, headers, and middleware
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

from models import WorkflowGraph, WorkflowNode, WorkflowType


@dataclass
class HeaderRequirement:
    """API header requirement"""
    name: str
    required: bool
    description: Optional[str] = None
    example: Optional[str] = None


@dataclass
class PayloadField:
    """Field in request/response payload"""
    name: str
    data_type: str
    required: bool = True
    description: Optional[str] = None
    example: Optional[str] = None


@dataclass
class MiddlewareInfo:
    """Middleware applied to route"""
    name: str
    file_path: str
    order: int
    description: Optional[str] = None


@dataclass
class APIRouteAnalysis:
    """Complete analysis of an API route"""
    route_path: str
    http_method: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    handler_name: Optional[str] = None

    # Request details
    request_headers: List[HeaderRequirement] = field(default_factory=list)
    request_payload: Dict[str, PayloadField] = field(default_factory=dict)

    # Response details
    response_payload: Dict[str, PayloadField] = field(default_factory=dict)

    # Middleware
    middleware: List[MiddlewareInfo] = field(default_factory=list)

    # Metrics
    call_count: int = 0
    error_count: int = 0
    avg_response_time: Optional[float] = None

    # Metadata
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    authentication_required: bool = False
    rate_limited: bool = False


class APIRoutesAnalyzer:
    """Analyzes API routes from workflow graph and repository files"""

    def __init__(self, graph: WorkflowGraph, repository_path: str):
        self.graph = graph
        self.repository_path = repository_path
        self.routes: Dict[str, APIRouteAnalysis] = {}

    def analyze(self, progress_callback=None) -> Dict[str, APIRouteAnalysis]:
        """Perform complete API routes analysis

        Args:
            progress_callback: Optional callback function(step, total_steps, message) for progress updates
        """
        print("\n" + "="*60)
        print("ANALYZING API ROUTES")
        print("="*60)

        total_steps = 6

        # Step 1: Extract routes from workflow graph
        self._extract_routes_from_graph()
        print(f"✓ Found {len(self.routes)} API routes from graph")
        if progress_callback:
            progress_callback(1, total_steps, f"Found {len(self.routes)} API routes from graph")

        # Step 2: Find route definition files
        self._find_route_files()
        print(f"✓ Located route definition files")
        if progress_callback:
            progress_callback(2, total_steps, "Located route definition files")

        # Step 3: Parse route files to extract details
        self._parse_route_definitions()
        print(f"✓ Parsed route definitions")
        if progress_callback:
            progress_callback(3, total_steps, "Parsed route definitions")

        # Step 4: Find and parse middleware
        self._find_middleware()
        print(f"✓ Found middleware configurations")
        if progress_callback:
            progress_callback(4, total_steps, "Found middleware configurations")

        # Step 5: Extract payload schemas
        self._extract_payload_schemas()
        print(f"✓ Extracted payload schemas")
        if progress_callback:
            progress_callback(5, total_steps, "Extracted payload schemas")

        # Step 6: Calculate metrics
        self._calculate_metrics()
        print(f"✓ Calculated route metrics")
        if progress_callback:
            progress_callback(6, total_steps, "Calculated route metrics")

        print(f"✓ Analyzed {len(self.routes)} API routes")
        print("="*60 + "\n")

        return self.routes

    def _extract_routes_from_graph(self):
        """Extract API routes from workflow graph nodes"""
        for node in self.graph.nodes:
            if node.type == WorkflowType.API_CALL and node.endpoint:
                route_key = f"{node.method}:{node.endpoint}"

                if route_key not in self.routes:
                    self.routes[route_key] = APIRouteAnalysis(
                        route_path=node.endpoint,
                        http_method=node.method or 'GET',
                        file_path=node.location.file_path,
                        line_number=node.location.line_number,
                        handler_name=node.name
                    )

                # Count this as a call
                self.routes[route_key].call_count += 1

    def _find_route_files(self):
        """Find files containing route definitions"""
        route_patterns = [
            '**/routes/*.py',
            '**/routes/*.ts',
            '**/routes/*.js',
            '**/controllers/*.py',
            '**/controllers/*.ts',
            '**/controllers/*.cs',
            '**/api/*.py',
            '**/api/*.ts',
        ]

        repo_path = Path(self.repository_path)

        for route_key, analysis in self.routes.items():
            if analysis.file_path:
                continue  # Already has file path

            # Search for route definition
            for pattern in route_patterns:
                for file_path in repo_path.glob(pattern):
                    if self._file_contains_route(file_path, analysis.route_path):
                        analysis.file_path = str(file_path)
                        line_num = self._find_route_line(file_path, analysis.route_path)
                        if line_num:
                            analysis.line_number = line_num
                        break

                if analysis.file_path:
                    break

    def _file_contains_route(self, file_path: Path, route_path: str) -> bool:
        """Check if file contains the route definition"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Clean route path for regex
            route_pattern = route_path.replace('/', r'\/')

            patterns = [
                # FastAPI / Flask
                rf'@app\.(get|post|put|delete|patch)\([\'\"]{route_pattern}[\'"]',
                rf'@router\.(get|post|put|delete|patch)\([\'\"]{route_pattern}[\'"]',
                # Express.js
                rf'app\.(get|post|put|delete|patch)\([\'\"]{route_pattern}[\'"]',
                rf'router\.(get|post|put|delete|patch)\([\'\"]{route_pattern}[\'"]',
                # ASP.NET
                rf'\[Route\([\'\"]{route_pattern}[\'\"]\)\]',
                rf'\[Http(Get|Post|Put|Delete|Patch)\([\'\"]{route_pattern}[\'\"]\)\]',
            ]

            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

        return False

    def _find_route_line(self, file_path: Path, route_path: str) -> Optional[int]:
        """Find line number where route is defined"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if route_path in line and any(kw in line.lower() for kw in ['route', 'get', 'post', 'put', 'delete']):
                        return line_num
        except Exception:
            pass

        return None

    def _parse_route_definitions(self):
        """Parse route definition files to extract details"""
        for route_key, analysis in self.routes.items():
            if not analysis.file_path:
                continue

            try:
                with open(analysis.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Extract based on file type
                if analysis.file_path.endswith('.py'):
                    self._parse_python_route(content, analysis)
                elif analysis.file_path.endswith(('.ts', '.js')):
                    self._parse_typescript_route(content, analysis)
                elif analysis.file_path.endswith('.cs'):
                    self._parse_csharp_route(content, analysis)

            except Exception as e:
                print(f"Error parsing route {route_key}: {e}")

    def _parse_python_route(self, content: str, analysis: APIRouteAnalysis):
        """Parse Python (FastAPI/Flask) route"""
        # Look for Pydantic models or type hints

        # Find authentication decorators
        if '@require_auth' in content or '@jwt_required' in content:
            analysis.authentication_required = True

        # Look for rate limiting
        if '@limiter.limit' in content or 'rate_limit' in content.lower():
            analysis.rate_limited = True

        # Extract request model
        request_match = re.search(rf'def\s+\w+.*?\(\s*.*?:\s*(\w+)', content)
        if request_match:
            model_name = request_match.group(1)
            # Try to find model definition
            model_def = self._find_pydantic_model(content, model_name)
            if model_def:
                analysis.request_payload = model_def

        # Common headers for Python APIs
        if 'Authorization' in content or 'authorization' in content:
            analysis.request_headers.append(HeaderRequirement(
                name='Authorization',
                required=True,
                description='Bearer token for authentication',
                example='Bearer eyJ0eXAiOiJKV1QiLCJhbGc...'
            ))

    def _parse_typescript_route(self, content: str, analysis: APIRouteAnalysis):
        """Parse TypeScript/JavaScript route"""
        # Look for middleware
        middleware_matches = re.finditer(r'app\.(use|get|post|put|delete|patch)\((.*?),\s*(\w+)', content)
        for match in middleware_matches:
            middleware_name = match.group(3)
            if middleware_name and not middleware_name.startswith('('):
                analysis.middleware.append(MiddlewareInfo(
                    name=middleware_name,
                    file_path=analysis.file_path or '',
                    order=len(analysis.middleware) + 1
                ))

        # Look for authentication
        if 'authenticate' in content.lower() or 'requireAuth' in content:
            analysis.authentication_required = True

        # Common headers
        if 'req.headers' in content:
            analysis.request_headers.append(HeaderRequirement(
                name='Content-Type',
                required=True,
                description='Request content type',
                example='application/json'
            ))

    def _parse_csharp_route(self, content: str, analysis: APIRouteAnalysis):
        """Parse C# (ASP.NET) route"""
        # Look for [Authorize] attribute
        if '[Authorize]' in content:
            analysis.authentication_required = True

        # Look for request model
        match = re.search(rf'\[FromBody\]\s*(\w+)', content)
        if match:
            model_name = match.group(1)
            # Try to find model definition
            model_def = self._find_csharp_model(content, model_name)
            if model_def:
                analysis.request_payload = model_def

    def _find_pydantic_model(self, content: str, model_name: str) -> Dict[str, PayloadField]:
        """Find and parse Pydantic model definition"""
        fields = {}

        # Look for class definition
        class_match = re.search(rf'class\s+{model_name}\(.*?\):(.*?)(?=class\s|\Z)', content, re.DOTALL)
        if not class_match:
            return fields

        class_body = class_match.group(1)

        # Extract fields
        field_pattern = r'(\w+):\s*([\w\[\]]+)(?:\s*=\s*Field\((.*?)\))?'
        for match in re.finditer(field_pattern, class_body):
            field_name = match.group(1)
            field_type = match.group(2)
            field_args = match.group(3) if match.group(3) else ''

            # Check if required
            required = 'Optional' not in field_type and '=' not in field_args

            fields[field_name] = PayloadField(
                name=field_name,
                data_type=field_type.replace('Optional[', '').replace(']', ''),
                required=required
            )

        return fields

    def _find_csharp_model(self, content: str, model_name: str) -> Dict[str, PayloadField]:
        """Find and parse C# model definition"""
        fields = {}

        # Look for class definition
        class_match = re.search(rf'class\s+{model_name}\s*{{(.*?)}}', content, re.DOTALL)
        if not class_match:
            return fields

        class_body = class_match.group(1)

        # Extract properties
        prop_pattern = r'public\s+([\w<>]+\??)\s+(\w+)\s*{[\s\w;]+}'
        for match in re.finditer(prop_pattern, class_body):
            data_type = match.group(1)
            field_name = match.group(2)

            required = '?' not in data_type

            fields[field_name] = PayloadField(
                name=field_name,
                data_type=data_type.replace('?', ''),
                required=required
            )

        return fields

    def _find_middleware(self):
        """Find middleware configurations"""
        # This is a simplified version - would need more sophisticated parsing
        for route_key, analysis in self.routes.items():
            if not analysis.file_path:
                continue

            try:
                with open(analysis.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Common middleware patterns
                if 'cors' in content.lower():
                    analysis.middleware.append(MiddlewareInfo(
                        name='CORS',
                        file_path=analysis.file_path,
                        order=1,
                        description='Cross-Origin Resource Sharing'
                    ))

                if 'logger' in content.lower() or 'logging' in content.lower():
                    analysis.middleware.append(MiddlewareInfo(
                        name='Logger',
                        file_path=analysis.file_path,
                        order=len(analysis.middleware) + 1,
                        description='Request/Response logging'
                    ))

            except Exception:
                pass

    def _extract_payload_schemas(self):
        """Extract detailed payload schemas"""
        # Add common fields based on HTTP method
        for route_key, analysis in self.routes.items():
            if analysis.http_method in ['POST', 'PUT', 'PATCH']:
                # Common request fields for these methods
                if not analysis.request_payload:
                    analysis.request_payload = {
                        'data': PayloadField(
                            name='data',
                            data_type='object',
                            required=True,
                            description='Request payload data'
                        )
                    }

            # All routes typically return JSON
            if not analysis.response_payload:
                analysis.response_payload = {
                    'status': PayloadField(
                        name='status',
                        data_type='string',
                        required=True,
                        description='Response status',
                        example='success'
                    ),
                    'data': PayloadField(
                        name='data',
                        data_type='object',
                        required=False,
                        description='Response data'
                    )
                }

    def _calculate_metrics(self):
        """Calculate analytics metrics for routes"""
        for route_key, analysis in self.routes.items():
            # Error rate calculation (simplified - would need actual error tracking)
            if analysis.call_count > 0:
                # Estimate error rate based on common error patterns
                analysis.error_count = 0  # Would need actual error tracking

            # Add tags based on analysis
            if analysis.authentication_required:
                analysis.tags.append('authenticated')

            if analysis.rate_limited:
                analysis.tags.append('rate-limited')

            if analysis.call_count > 10:
                analysis.tags.append('high-traffic')

            if analysis.http_method in ['POST', 'PUT', 'DELETE']:
                analysis.tags.append('mutating')
            else:
                analysis.tags.append('read-only')

    def to_dict(self) -> Dict[str, dict]:
        """Convert analysis to dictionary for JSON serialization"""
        result = {}

        for route_key, analysis in self.routes.items():
            result[route_key] = {
                'route_path': analysis.route_path,
                'http_method': analysis.http_method,
                'file_path': analysis.file_path,
                'line_number': analysis.line_number,
                'handler_name': analysis.handler_name,
                'request_headers': [
                    {
                        'name': h.name,
                        'required': h.required,
                        'description': h.description,
                        'example': h.example
                    }
                    for h in analysis.request_headers
                ],
                'request_payload': {
                    field_name: {
                        'name': field.name,
                        'data_type': field.data_type,
                        'required': field.required,
                        'description': field.description,
                        'example': field.example
                    }
                    for field_name, field in analysis.request_payload.items()
                },
                'response_payload': {
                    field_name: {
                        'name': field.name,
                        'data_type': field.data_type,
                        'required': field.required,
                        'description': field.description,
                        'example': field.example
                    }
                    for field_name, field in analysis.response_payload.items()
                },
                'middleware': [
                    {
                        'name': m.name,
                        'file_path': m.file_path,
                        'order': m.order,
                        'description': m.description
                    }
                    for m in analysis.middleware
                ],
                'metrics': {
                    'call_count': analysis.call_count,
                    'error_count': analysis.error_count,
                    'avg_response_time': analysis.avg_response_time
                },
                'metadata': {
                    'description': analysis.description,
                    'tags': analysis.tags,
                    'authentication_required': analysis.authentication_required,
                    'rate_limited': analysis.rate_limited
                }
            }

        return result
