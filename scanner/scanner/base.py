"""Base scanner class for code analysis."""

from abc import ABC, abstractmethod
from typing import List, Set
from pathlib import Path

from ..models import WorkflowGraph, WorkflowNode, CodeLocation


class BaseScanner(ABC):
    """Abstract base class for language-specific scanners."""

    def __init__(self, config: dict):
        """Initialize scanner with configuration.

        Args:
            config: Scanner configuration dictionary
        """
        self.config = config
        self.graph = WorkflowGraph()

    @abstractmethod
    def can_scan(self, file_path: str) -> bool:
        """Check if this scanner can handle the given file.

        Args:
            file_path: Path to the file

        Returns:
            True if this scanner can handle the file
        """
        pass

    @abstractmethod
    def scan_file(self, file_path: str) -> WorkflowGraph:
        """Scan a single file and extract workflow information.

        Args:
            file_path: Path to the file to scan

        Returns:
            WorkflowGraph containing discovered workflows
        """
        pass

    def read_file(self, file_path: str) -> str:
        """Read file contents.

        Args:
            file_path: Path to the file

        Returns:
            File contents as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

    def extract_code_snippet(self, content: str, line_number: int, context_lines: int = 2) -> str:
        """Extract a code snippet around a line number.

        Args:
            content: Full file content
            line_number: Target line number (1-indexed)
            context_lines: Number of lines before/after to include

        Returns:
            Code snippet as string
        """
        lines = content.split('\n')
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)

        snippet_lines = lines[start:end]
        return '\n'.join(snippet_lines)

    def should_detect_type(self, workflow_type: str) -> bool:
        """Check if we should detect a specific workflow type.

        Args:
            workflow_type: Type of workflow (e.g., 'database', 'api_calls')

        Returns:
            True if detection is enabled for this type
        """
        detect_config = self.config.get('detect', {})
        return detect_config.get(workflow_type, True)

    def get_relative_path(self, file_path: str, base_path: str = None) -> str:
        """Get relative path from base path.

        Args:
            file_path: Full file path
            base_path: Base path to calculate relative from

        Returns:
            Relative path
        """
        if base_path:
            try:
                return str(Path(file_path).relative_to(base_path))
            except ValueError:
                return file_path
        return file_path


class TreeSitterScanner(BaseScanner):
    """Base class for tree-sitter based scanners."""

    def __init__(self, config: dict, language_name: str):
        """Initialize tree-sitter scanner.

        Args:
            config: Scanner configuration
            language_name: Language identifier for tree-sitter
        """
        super().__init__(config)
        self.language_name = language_name
        self._parser = None
        self._language = None

    def _init_parser(self):
        """Initialize tree-sitter parser (lazy loading)."""
        if self._parser is not None:
            return

        try:
            import tree_sitter
            from tree_sitter import Language, Parser

            # This will be overridden in subclasses
            self._language = self._load_language()
            self._parser = Parser()
            self._parser.set_language(self._language)
        except ImportError:
            raise ImportError(
                "tree-sitter is required for code parsing. "
                "Install with: pip install tree-sitter"
            )

    @abstractmethod
    def _load_language(self):
        """Load tree-sitter language. Must be implemented by subclasses."""
        pass

    def parse_file(self, file_path: str) -> any:
        """Parse file using tree-sitter.

        Args:
            file_path: Path to file

        Returns:
            Tree-sitter tree object
        """
        self._init_parser()
        content = self.read_file(file_path)
        tree = self._parser.parse(bytes(content, 'utf-8'))
        return tree

    def query_code(self, tree: any, query_string: str) -> List:
        """Query parsed code using tree-sitter query syntax.

        Args:
            tree: Parsed tree-sitter tree
            query_string: Tree-sitter query string

        Returns:
            List of query matches
        """
        from tree_sitter import Query

        query = Query(self._language, query_string)
        return query.captures(tree.root_node)
