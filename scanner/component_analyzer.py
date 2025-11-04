"""
Component and Page Analyzer

Analyzes frontend components and pages to extract:
- Component definitions (React, Vue, Angular, etc.)
- Page definitions and routes
- Component usage relationships
- Event handlers
- Data models (props, state, form fields)
- Visual structure
"""

import os
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict


@dataclass
class EventHandler:
    """Represents an event handler in a component"""
    name: str
    event_type: str  # onClick, onChange, onSubmit, etc.
    line_number: Optional[int] = None


@dataclass
class DataField:
    """Represents a data field (prop, state, form field)"""
    name: str
    data_type: str
    source: str  # 'prop', 'state', 'form', 'context'
    required: bool = False
    default_value: Optional[str] = None


@dataclass
class ComponentUsage:
    """Represents usage of a component in another file"""
    used_in_file: str
    used_in_component: str
    line_number: Optional[int] = None


@dataclass
class ComponentAnalysis:
    """Analysis result for a single component"""
    name: str
    type: str  # 'functional', 'class', 'page', 'form', 'layout'
    file_path: str
    line_number: Optional[int] = None
    description: Optional[str] = None

    # Usage information
    used_in: List[ComponentUsage] = field(default_factory=list)
    uses_components: List[str] = field(default_factory=list)

    # Handlers and data
    handlers: List[EventHandler] = field(default_factory=list)
    data_fields: List[DataField] = field(default_factory=list)

    # Visual structure
    html_structure: Optional[str] = None
    has_form: bool = False

    # Metrics
    lines_of_code: int = 0
    complexity_score: int = 0  # Simple complexity based on handlers, hooks, etc.


@dataclass
class PageAnalysis:
    """Analysis result for a page/route"""
    name: str
    path: str  # URL path or route
    file_path: str
    line_number: Optional[int] = None

    # Components used on this page
    components: List[str] = field(default_factory=list)

    # Route information
    route_params: List[str] = field(default_factory=list)
    query_params: List[str] = field(default_factory=list)

    # Page metadata
    title: Optional[str] = None
    requires_auth: bool = False
    layout: Optional[str] = None

    # Metrics
    component_count: int = 0
    api_calls_count: int = 0
    database_queries_count: int = 0


class ComponentPageAnalyzer:
    """Analyzes components and pages from a codebase"""

    def __init__(self, graph, repo_path: str):
        self.graph = graph
        self.repo_path = Path(repo_path)
        self.components: Dict[str, ComponentAnalysis] = {}
        self.pages: Dict[str, PageAnalysis] = {}

    def analyze(self) -> tuple[Dict[str, ComponentAnalysis], Dict[str, PageAnalysis]]:
        """Run the complete analysis"""
        print("🔍 Analyzing components and pages...")

        # Find all component and page files
        component_files = self._find_component_files()
        page_files = self._find_page_files()

        print(f"Found {len(component_files)} component files")
        print(f"Found {len(page_files)} page files")

        # Analyze components
        for file_path in component_files:
            self._analyze_component_file(file_path)

        # Analyze pages
        for file_path in page_files:
            self._analyze_page_file(file_path)

        # Build usage relationships
        self._build_usage_relationships()

        # Enhance with workflow graph data
        self._enhance_with_graph_data()

        return self.components, self.pages

    def _find_component_files(self) -> List[Path]:
        """Find all component files in the repository"""
        component_files = []
        component_patterns = [
            '**/components/**/*.tsx',
            '**/components/**/*.jsx',
            '**/components/**/*.ts',
            '**/components/**/*.js',
            '**/components/**/*.vue',
            '**/*.component.ts',  # Angular
            '**/*.component.tsx',
        ]

        for pattern in component_patterns:
            component_files.extend(self.repo_path.glob(pattern))

        # Filter out node_modules, dist, build, etc.
        exclude_dirs = {'node_modules', 'dist', 'build', '.next', '__pycache__', 'coverage'}
        component_files = [
            f for f in component_files
            if not any(ex in f.parts for ex in exclude_dirs)
        ]

        return component_files

    def _find_page_files(self) -> List[Path]:
        """Find all page files in the repository"""
        page_files = []
        page_patterns = [
            '**/pages/**/*.tsx',
            '**/pages/**/*.jsx',
            '**/app/**/page.tsx',  # Next.js 13+ app directory
            '**/app/**/page.jsx',
            '**/views/**/*.vue',
            '**/views/**/*.tsx',
            '**/views/**/*.jsx',
            '**/routes/**/*.tsx',
            '**/routes/**/*.jsx',
        ]

        for pattern in page_patterns:
            page_files.extend(self.repo_path.glob(pattern))

        # Filter out excluded directories
        exclude_dirs = {'node_modules', 'dist', 'build', '.next', '__pycache__', 'coverage'}
        page_files = [
            f for f in page_files
            if not any(ex in f.parts for ex in exclude_dirs)
        ]

        return page_files

    def _analyze_component_file(self, file_path: Path):
        """Analyze a single component file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Determine component type
            if '.vue' in file_path.suffixes:
                components = self._parse_vue_component(content, file_path)
            elif '.component.ts' in file_path.name:
                components = self._parse_angular_component(content, file_path)
            else:
                components = self._parse_react_component(content, file_path)

            for component in components:
                self.components[component.name] = component

        except Exception as e:
            print(f"Error analyzing component {file_path}: {e}")

    def _parse_react_component(self, content: str, file_path: Path) -> List[ComponentAnalysis]:
        """Parse React/TSX component"""
        components = []

        # Find function components
        func_pattern = r'(?:export\s+)?(?:default\s+)?function\s+(\w+)\s*\([^)]*\)'
        for match in re.finditer(func_pattern, content):
            comp_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Skip if not a component (doesn't start with uppercase)
            if not comp_name[0].isupper():
                continue

            component = ComponentAnalysis(
                name=comp_name,
                type='functional',
                file_path=str(file_path.relative_to(self.repo_path)),
                line_number=line_num,
                lines_of_code=content.count('\n')
            )

            # Extract handlers
            component.handlers = self._extract_handlers(content)

            # Extract data fields
            component.data_fields = self._extract_react_data_fields(content)

            # Extract HTML structure
            component.html_structure = self._extract_jsx_structure(content)

            # Check if it's a form
            component.has_form = '<form' in content.lower() or 'onsubmit' in content.lower()

            # Calculate complexity
            component.complexity_score = self._calculate_complexity(content)

            # Extract used components
            component.uses_components = self._extract_used_components(content)

            components.append(component)

        # Find class components
        class_pattern = r'class\s+(\w+)\s+extends\s+(?:React\.)?Component'
        for match in re.finditer(class_pattern, content):
            comp_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            component = ComponentAnalysis(
                name=comp_name,
                type='class',
                file_path=str(file_path.relative_to(self.repo_path)),
                line_number=line_num,
                lines_of_code=content.count('\n')
            )

            component.handlers = self._extract_handlers(content)
            component.data_fields = self._extract_react_data_fields(content)
            component.html_structure = self._extract_jsx_structure(content)
            component.has_form = '<form' in content.lower()
            component.complexity_score = self._calculate_complexity(content)
            component.uses_components = self._extract_used_components(content)

            components.append(component)

        return components

    def _parse_vue_component(self, content: str, file_path: Path) -> List[ComponentAnalysis]:
        """Parse Vue component"""
        # Extract component name from file name
        comp_name = file_path.stem
        if comp_name.endswith('.component'):
            comp_name = comp_name[:-10]

        component = ComponentAnalysis(
            name=comp_name,
            type='functional',
            file_path=str(file_path.relative_to(self.repo_path)),
            line_number=1,
            lines_of_code=content.count('\n')
        )

        # Extract handlers from methods
        component.handlers = self._extract_vue_handlers(content)

        # Extract props and data
        component.data_fields = self._extract_vue_data_fields(content)

        # Extract template structure
        template_match = re.search(r'<template>(.*?)</template>', content, re.DOTALL)
        if template_match:
            component.html_structure = template_match.group(1)[:500]  # First 500 chars

        component.has_form = '<form' in content.lower()
        component.complexity_score = self._calculate_complexity(content)

        return [component]

    def _parse_angular_component(self, content: str, file_path: Path) -> List[ComponentAnalysis]:
        """Parse Angular component"""
        comp_name = file_path.stem.replace('.component', '')

        component = ComponentAnalysis(
            name=comp_name,
            type='class',
            file_path=str(file_path.relative_to(self.repo_path)),
            line_number=1,
            lines_of_code=content.count('\n')
        )

        # Extract handlers
        component.handlers = self._extract_angular_handlers(content)

        # Extract properties
        component.data_fields = self._extract_angular_data_fields(content)

        component.has_form = 'formgroup' in content.lower() or 'ngmodel' in content.lower()
        component.complexity_score = self._calculate_complexity(content)

        return [component]

    def _analyze_page_file(self, file_path: Path):
        """Analyze a single page file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Determine page name and path
            page_name = self._extract_page_name(file_path)
            page_path = self._extract_page_path(file_path)

            page = PageAnalysis(
                name=page_name,
                path=page_path,
                file_path=str(file_path.relative_to(self.repo_path)),
                line_number=1
            )

            # Extract components used
            page.components = self._extract_used_components(content)
            page.component_count = len(page.components)

            # Extract route params
            page.route_params = self._extract_route_params(page_path, content)

            # Check if auth is required
            page.requires_auth = self._check_auth_required(content)

            # Extract layout
            page.layout = self._extract_layout(content)

            self.pages[page_name] = page

        except Exception as e:
            print(f"Error analyzing page {file_path}: {e}")

    def _extract_page_name(self, file_path: Path) -> str:
        """Extract page name from file path"""
        # For Next.js app directory: /app/dashboard/page.tsx -> Dashboard
        if 'app' in file_path.parts:
            parts = list(file_path.parts)
            app_idx = parts.index('app')
            if app_idx + 1 < len(parts):
                # Get the directory name before page.tsx
                return parts[app_idx + 1].capitalize()

        # Default: use file stem
        return file_path.stem.replace('page', '').replace('_', ' ').title() or 'Home'

    def _extract_page_path(self, file_path: Path) -> str:
        """Extract URL path from file path"""
        # For Next.js app directory: /app/dashboard/page.tsx -> /dashboard
        if 'app' in file_path.parts:
            parts = list(file_path.parts)
            app_idx = parts.index('app')
            path_parts = parts[app_idx + 1:-1]  # Exclude 'app' and filename

            # Handle dynamic routes [id]
            path_parts = [
                f":{part[1:-1]}" if part.startswith('[') and part.endswith(']') else part
                for part in path_parts
            ]

            return '/' + '/'.join(path_parts) if path_parts else '/'

        # For pages directory
        if 'pages' in file_path.parts:
            parts = list(file_path.parts)
            pages_idx = parts.index('pages')
            path_parts = parts[pages_idx + 1:]
            path_parts[-1] = path_parts[-1].replace('.tsx', '').replace('.jsx', '').replace('.js', '')

            # Handle dynamic routes [id]
            path_parts = [
                f":{part[1:-1]}" if part.startswith('[') and part.endswith(']') else part
                for part in path_parts
            ]

            return '/' + '/'.join(path_parts)

        return '/unknown'

    def _extract_route_params(self, page_path: str, content: str) -> List[str]:
        """Extract route parameters from page path and content"""
        params = []

        # Extract from path (e.g., :id, :slug)
        param_pattern = r':(\w+)'
        params.extend(re.findall(param_pattern, page_path))

        # Extract from useParams or useRouter
        use_params_pattern = r'useParams\(\)\.(\w+)'
        params.extend(re.findall(use_params_pattern, content))

        return list(set(params))

    def _check_auth_required(self, content: str) -> bool:
        """Check if page requires authentication"""
        auth_patterns = [
            r'requireAuth',
            r'withAuth',
            r'protected\s*:?\s*true',
            r'middleware.*auth',
            r'getServerSideProps.*session',
        ]

        return any(re.search(pattern, content, re.IGNORECASE) for pattern in auth_patterns)

    def _extract_layout(self, content: str) -> Optional[str]:
        """Extract layout component name"""
        layout_patterns = [
            r'layout\s*:\s*["\'](\w+)["\']',
            r'<(\w*Layout)>',
            r'return\s*<(\w*Layout)',
        ]

        for pattern in layout_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return None

    def _extract_handlers(self, content: str) -> List[EventHandler]:
        """Extract event handlers from component"""
        handlers = []

        # Match onClick, onChange, onSubmit, etc.
        handler_pattern = r'(on[A-Z]\w+)=\{([^}]+)\}'
        for match in re.finditer(handler_pattern, content):
            event_type = match.group(1)
            handler_name = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1

            handlers.append(EventHandler(
                name=handler_name,
                event_type=event_type,
                line_number=line_num
            ))

        return handlers

    def _extract_vue_handlers(self, content: str) -> List[EventHandler]:
        """Extract event handlers from Vue component"""
        handlers = []

        # Match @click, @change, @submit, etc.
        handler_pattern = r'@(\w+)="([^"]+)"'
        for match in re.finditer(handler_pattern, content):
            event_type = f'on{match.group(1).capitalize()}'
            handler_name = match.group(2)

            handlers.append(EventHandler(
                name=handler_name,
                event_type=event_type
            ))

        return handlers

    def _extract_angular_handlers(self, content: str) -> List[EventHandler]:
        """Extract event handlers from Angular component"""
        handlers = []

        # Match (click), (change), (submit), etc.
        handler_pattern = r'\((\w+)\)="([^"]+)"'
        for match in re.finditer(handler_pattern, content):
            event_type = f'on{match.group(1).capitalize()}'
            handler_name = match.group(2)

            handlers.append(EventHandler(
                name=handler_name,
                event_type=event_type
            ))

        return handlers

    def _extract_react_data_fields(self, content: str) -> List[DataField]:
        """Extract props, state, and form fields from React component"""
        fields = []

        # Extract props from function params
        props_pattern = r'function\s+\w+\(\{\s*([^}]+)\s*\}'
        match = re.search(props_pattern, content)
        if match:
            prop_names = [p.strip().split(':')[0] for p in match.group(1).split(',')]
            for prop_name in prop_names:
                if prop_name:
                    fields.append(DataField(
                        name=prop_name.strip(),
                        data_type='any',
                        source='prop'
                    ))

        # Extract useState
        state_pattern = r'const\s+\[(\w+),\s*set\w+\]\s*=\s*useState'
        for match in re.finditer(state_pattern, content):
            fields.append(DataField(
                name=match.group(1),
                data_type='state',
                source='state'
            ))

        # Extract form fields (name attribute)
        form_field_pattern = r'name=["\'](\w+)["\']'
        for match in re.finditer(form_field_pattern, content):
            fields.append(DataField(
                name=match.group(1),
                data_type='string',
                source='form'
            ))

        return fields

    def _extract_vue_data_fields(self, content: str) -> List[DataField]:
        """Extract props and data from Vue component"""
        fields = []

        # Extract props
        props_pattern = r'props\s*:\s*\{([^}]+)\}'
        match = re.search(props_pattern, content)
        if match:
            prop_content = match.group(1)
            prop_names = re.findall(r'(\w+)\s*:', prop_content)
            for prop_name in prop_names:
                fields.append(DataField(
                    name=prop_name,
                    data_type='any',
                    source='prop'
                ))

        # Extract data
        data_pattern = r'data\s*\(\s*\)\s*\{[^}]*return\s*\{([^}]+)\}'
        match = re.search(data_pattern, content)
        if match:
            data_content = match.group(1)
            data_names = re.findall(r'(\w+)\s*:', data_content)
            for data_name in data_names:
                fields.append(DataField(
                    name=data_name,
                    data_type='any',
                    source='state'
                ))

        return fields

    def _extract_angular_data_fields(self, content: str) -> List[DataField]:
        """Extract properties from Angular component"""
        fields = []

        # Extract @Input properties
        input_pattern = r'@Input\(\)\s+(\w+)'
        for match in re.finditer(input_pattern, content):
            fields.append(DataField(
                name=match.group(1),
                data_type='any',
                source='prop'
            ))

        # Extract class properties
        prop_pattern = r'(?:public|private|protected)?\s+(\w+)\s*:\s*(\w+)'
        for match in re.finditer(prop_pattern, content):
            if match.group(1) not in ['constructor', 'ngOnInit', 'ngOnDestroy']:
                fields.append(DataField(
                    name=match.group(1),
                    data_type=match.group(2),
                    source='state'
                ))

        return fields

    def _extract_jsx_structure(self, content: str) -> Optional[str]:
        """Extract simplified JSX structure for visual preview"""
        # Find the return statement
        return_pattern = r'return\s*\((.*?)\);'
        match = re.search(return_pattern, content, re.DOTALL)

        if match:
            jsx = match.group(1).strip()
            # Simplify: keep only tag names and structure
            simplified = re.sub(r'\{[^}]+\}', '{...}', jsx)  # Replace expressions
            return simplified[:500]  # First 500 chars

        return None

    def _calculate_complexity(self, content: str) -> int:
        """Calculate a simple complexity score"""
        score = 0

        # Count hooks (useState, useEffect, etc.)
        score += len(re.findall(r'use[A-Z]\w+', content))

        # Count handlers
        score += len(re.findall(r'on[A-Z]\w+', content))

        # Count conditionals
        score += content.count('if (')
        score += content.count('? ')

        # Count loops
        score += content.count('.map(')
        score += content.count('for (')
        score += content.count('while (')

        return score

    def _extract_used_components(self, content: str) -> List[str]:
        """Extract list of components used in this file"""
        components = []

        # Find import statements
        import_pattern = r'import\s+(?:\{[^}]+\}|\w+)\s+from\s+["\']([^"\']+)["\']'
        for match in re.finditer(import_pattern, content):
            import_path = match.group(1)
            if any(keyword in import_path for keyword in ['component', 'Component', '@/']):
                # Extract component name from path
                comp_name = Path(import_path).stem
                if comp_name and comp_name[0].isupper():
                    components.append(comp_name)

        # Find JSX usage of components (uppercase tags)
        jsx_pattern = r'<([A-Z]\w+)'
        for match in re.finditer(jsx_pattern, content):
            comp_name = match.group(1)
            if comp_name not in components:
                components.append(comp_name)

        return components

    def _build_usage_relationships(self):
        """Build component usage relationships"""
        # For each component, find where it's used
        for comp_name, component in self.components.items():
            # Check all other components and pages
            for other_name, other_comp in self.components.items():
                if comp_name in other_comp.uses_components:
                    component.used_in.append(ComponentUsage(
                        used_in_file=other_comp.file_path,
                        used_in_component=other_name
                    ))

            # Check pages
            for page_name, page in self.pages.items():
                if comp_name in page.components:
                    component.used_in.append(ComponentUsage(
                        used_in_file=page.file_path,
                        used_in_component=page_name
                    ))

    def _enhance_with_graph_data(self):
        """Enhance analysis with data from workflow graph"""
        # Count API calls and database queries per page
        for node in self.graph.nodes:
            file_path = node.location.file_path if node.location else None
            if not file_path:
                continue

            # Find matching page
            for page_name, page in self.pages.items():
                if file_path in page.file_path:
                    if 'api' in node.type.value.lower():
                        page.api_calls_count += 1
                    if 'database' in node.type.value.lower():
                        page.database_queries_count += 1

    def to_dict(self) -> Dict:
        """Convert analysis results to dictionary"""
        return {
            'components': {
                name: asdict(comp) for name, comp in self.components.items()
            },
            'pages': {
                name: asdict(page) for name, page in self.pages.items()
            }
        }
