"""C# code scanner for workflow detection."""

import re
from typing import List, Dict, Any
from pathlib import Path

from .base import BaseScanner
from ..models import (
    WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowType, CodeLocation
)


class CSharpScanner(BaseScanner):
    """Scanner for C# code to detect data workflows."""

    # Common Entity Framework patterns
    EF_QUERY_PATTERNS = [
        r'\.Where\s*\(',
        r'\.Select\s*\(',
        r'\.FirstOrDefault\s*\(',
        r'\.ToList\s*\(',
        r'\.Include\s*\(',
        r'\.FromSql',
    ]

    # Database write patterns
    EF_WRITE_PATTERNS = [
        r'\.Add\s*\(',
        r'\.Update\s*\(',
        r'\.Remove\s*\(',
        r'\.SaveChanges',
        r'\.SaveChangesAsync',
    ]

    # HTTP client patterns
    HTTP_PATTERNS = [
        r'HttpClient',
        r'\.GetAsync\s*\(',
        r'\.PostAsync\s*\(',
        r'\.PutAsync\s*\(',
        r'\.DeleteAsync\s*\(',
        r'\.SendAsync\s*\(',
    ]

    # File I/O patterns
    FILE_IO_PATTERNS = [
        r'File\.ReadAllText',
        r'File\.WriteAllText',
        r'File\.ReadAllLines',
        r'File\.WriteAllLines',
        r'StreamReader',
        r'StreamWriter',
        r'FileStream',
    ]

    def can_scan(self, file_path: str) -> bool:
        """Check if file is a C# file."""
        return file_path.endswith('.cs')

    def scan_file(self, file_path: str) -> WorkflowGraph:
        """Scan C# file for workflow patterns."""
        self.graph = WorkflowGraph()
        content = self.read_file(file_path)

        # Scan for different workflow types
        if self.should_detect_type('database'):
            self._scan_database_operations(file_path, content)

        if self.should_detect_type('api_calls'):
            self._scan_http_calls(file_path, content)

        if self.should_detect_type('file_io'):
            self._scan_file_operations(file_path, content)

        if self.should_detect_type('message_queues'):
            self._scan_message_queues(file_path, content)

        return self.graph

    def _scan_database_operations(self, file_path: str, content: str):
        """Scan for database operations (Entity Framework, ADO.NET, Dapper)."""
        lines = content.split('\n')

        # Detect EF DbContext queries
        for i, line in enumerate(lines, 1):
            # Database reads
            for pattern in self.EF_QUERY_PATTERNS:
                if re.search(pattern, line):
                    table_name = self._extract_table_name(line, lines, i)
                    node = WorkflowNode(
                        id=f"{file_path}:db_read:{i}",
                        type=WorkflowType.DATABASE_READ,
                        name=f"DB Query: {table_name or 'Unknown'}",
                        description=f"Database query operation",
                        location=CodeLocation(file_path, i),
                        table_name=table_name,
                        code_snippet=self.extract_code_snippet(content, i),
                        metadata={'pattern': pattern}
                    )
                    self.graph.add_node(node)
                    break  # Only add once per line

            # Database writes
            for pattern in self.EF_WRITE_PATTERNS:
                if re.search(pattern, line):
                    table_name = self._extract_table_name(line, lines, i)
                    node = WorkflowNode(
                        id=f"{file_path}:db_write:{i}",
                        type=WorkflowType.DATABASE_WRITE,
                        name=f"DB Write: {table_name or 'Unknown'}",
                        description=f"Database write operation",
                        location=CodeLocation(file_path, i),
                        table_name=table_name,
                        code_snippet=self.extract_code_snippet(content, i),
                        metadata={'pattern': pattern}
                    )
                    self.graph.add_node(node)
                    break

            # Raw SQL queries
            if re.search(r'SqlCommand|SqlDataAdapter|ExecuteReader|ExecuteScalar', line):
                query = self._extract_sql_query(lines, i)
                node = WorkflowNode(
                    id=f"{file_path}:sql:{i}",
                    type=WorkflowType.DATABASE_READ,
                    name="SQL Query",
                    description="Raw SQL query execution",
                    location=CodeLocation(file_path, i),
                    query=query,
                    code_snippet=self.extract_code_snippet(content, i),
                )
                self.graph.add_node(node)

    def _scan_http_calls(self, file_path: str, content: str):
        """Scan for HTTP/API calls."""
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern in self.HTTP_PATTERNS:
                if re.search(pattern, line):
                    endpoint = self._extract_endpoint(line, lines, i)
                    method = self._extract_http_method(line)

                    node = WorkflowNode(
                        id=f"{file_path}:api:{i}",
                        type=WorkflowType.API_CALL,
                        name=f"API Call: {method or 'HTTP'}",
                        description=f"HTTP API call",
                        location=CodeLocation(file_path, i),
                        endpoint=endpoint,
                        method=method,
                        code_snippet=self.extract_code_snippet(content, i),
                    )
                    self.graph.add_node(node)
                    break

    def _scan_file_operations(self, file_path: str, content: str):
        """Scan for file I/O operations."""
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern in self.FILE_IO_PATTERNS:
                if re.search(pattern, line):
                    is_read = bool(re.search(r'Read|Reader', line))
                    file_target = self._extract_file_path(line)

                    node = WorkflowNode(
                        id=f"{file_path}:file:{i}",
                        type=WorkflowType.FILE_READ if is_read else WorkflowType.FILE_WRITE,
                        name=f"File {'Read' if is_read else 'Write'}",
                        description=f"File {'read' if is_read else 'write'} operation",
                        location=CodeLocation(file_path, i),
                        file_path=file_target,
                        code_snippet=self.extract_code_snippet(content, i),
                    )
                    self.graph.add_node(node)
                    break

    def _scan_message_queues(self, file_path: str, content: str):
        """Scan for message queue operations (Azure Service Bus, RabbitMQ, etc.)."""
        lines = content.split('\n')

        # Azure Service Bus patterns
        service_bus_patterns = [
            r'ServiceBusSender',
            r'ServiceBusReceiver',
            r'SendMessageAsync',
            r'ReceiveMessageAsync',
        ]

        # RabbitMQ patterns
        rabbitmq_patterns = [
            r'IModel\.BasicPublish',
            r'IModel\.BasicConsume',
            r'QueueDeclare',
        ]

        for i, line in enumerate(lines, 1):
            # Azure Service Bus
            for pattern in service_bus_patterns:
                if re.search(pattern, line):
                    is_send = bool(re.search(r'Send|Sender', line))
                    queue_name = self._extract_queue_name(line, lines, i)

                    node = WorkflowNode(
                        id=f"{file_path}:msg:{i}",
                        type=WorkflowType.MESSAGE_SEND if is_send else WorkflowType.MESSAGE_RECEIVE,
                        name=f"Message {'Send' if is_send else 'Receive'}",
                        description=f"Azure Service Bus message operation",
                        location=CodeLocation(file_path, i),
                        queue_name=queue_name,
                        code_snippet=self.extract_code_snippet(content, i),
                        metadata={'platform': 'Azure Service Bus'}
                    )
                    self.graph.add_node(node)
                    break

            # RabbitMQ
            for pattern in rabbitmq_patterns:
                if re.search(pattern, line):
                    is_publish = bool(re.search(r'Publish', line))
                    queue_name = self._extract_queue_name(line, lines, i)

                    node = WorkflowNode(
                        id=f"{file_path}:msg:{i}",
                        type=WorkflowType.MESSAGE_SEND if is_publish else WorkflowType.MESSAGE_RECEIVE,
                        name=f"Message {'Publish' if is_publish else 'Consume'}",
                        description=f"RabbitMQ message operation",
                        location=CodeLocation(file_path, i),
                        queue_name=queue_name,
                        code_snippet=self.extract_code_snippet(content, i),
                        metadata={'platform': 'RabbitMQ'}
                    )
                    self.graph.add_node(node)
                    break

    def _extract_table_name(self, line: str, all_lines: List[str], line_num: int) -> str:
        """Extract table/entity name from EF query."""
        # Look for DbSet<EntityName> or _context.EntityName
        match = re.search(r'DbSet<(\w+)>|_context\.(\w+)|_db\.(\w+)', line)
        if match:
            return match.group(1) or match.group(2) or match.group(3)

        # Look backwards for context
        for i in range(max(0, line_num - 5), line_num):
            match = re.search(r'var\s+\w+\s*=\s*\w+\.(\w+)', all_lines[i])
            if match:
                return match.group(1)

        return None

    def _extract_sql_query(self, lines: List[str], line_num: int) -> str:
        """Extract SQL query string from code."""
        # Look for string literals containing SQL keywords
        context = '\n'.join(lines[max(0, line_num-3):min(len(lines), line_num+3)])
        match = re.search(r'"(SELECT|INSERT|UPDATE|DELETE).*?"', context, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(0)
        return None

    def _extract_endpoint(self, line: str, all_lines: List[str], line_num: int) -> str:
        """Extract API endpoint from HTTP call."""
        # Look for URL in string literals
        url_match = re.search(r'"(https?://[^"]+|/[^"]*)"', line)
        if url_match:
            return url_match.group(1)

        # Look for URL in variable assignment nearby
        for i in range(max(0, line_num - 3), min(len(all_lines), line_num + 1)):
            url_match = re.search(r'"(https?://[^"]+|/api/[^"]*)"', all_lines[i])
            if url_match:
                return url_match.group(1)

        return None

    def _extract_http_method(self, line: str) -> str:
        """Extract HTTP method from call."""
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        for method in methods:
            if re.search(rf'{method}Async|\.{method}\(', line, re.IGNORECASE):
                return method
        return 'HTTP'

    def _extract_file_path(self, line: str) -> str:
        """Extract file path from file operation."""
        # Look for string literals that look like file paths
        match = re.search(r'"([^"]*\.[a-zA-Z]{2,4})"', line)
        if match:
            return match.group(1)
        return None

    def _extract_queue_name(self, line: str, all_lines: List[str], line_num: int) -> str:
        """Extract queue/topic name from message queue operation."""
        # Look for string literals
        match = re.search(r'"([^"]+)"', line)
        if match:
            return match.group(1)

        # Look nearby for queue declarations
        for i in range(max(0, line_num - 5), min(len(all_lines), line_num + 1)):
            match = re.search(r'queueName\s*=\s*"([^"]+)"|CreateQueue\("([^"]+)"', all_lines[i])
            if match:
                return match.group(1) or match.group(2)

        return None
