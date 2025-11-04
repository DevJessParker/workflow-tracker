"""C# code scanner for workflow detection."""

import re
from typing import List, Dict, Any
from pathlib import Path

from .base import BaseScanner
from models import (
    WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowType, CodeLocation, TableSchema
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

    def scan_file(self, file_path: str, schema_registry: dict = None) -> WorkflowGraph:
        """Scan C# file for workflow patterns.

        Args:
            file_path: Path to the file to scan
            schema_registry: Optional dictionary mapping table/entity names to TableSchema objects
        """
        self.graph = WorkflowGraph()
        self.schema_registry = schema_registry or {}
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
        """Extract table/entity name from EF query.

        Uses the schema registry when available to map entity names to actual table names.
        """
        entity_name = None

        # Look for DbSet<EntityName> or _context.EntityName or _db.EntityName
        match = re.search(r'DbSet<(\w+)>|_context\.(\w+)|_db\.(\w+)', line)
        if match:
            entity_name = match.group(1) or match.group(2) or match.group(3)

        # Look backwards for context if not found yet
        if not entity_name:
            for i in range(max(0, line_num - 5), line_num):
                match = re.search(r'var\s+\w+\s*=\s*\w+\.(\w+)', all_lines[i])
                if match:
                    entity_name = match.group(1)
                    break

        # If we found an entity name, try to resolve it to actual table name using schema registry
        if entity_name and self.schema_registry:
            schema = self.schema_registry.get(entity_name)
            if schema:
                # Return the actual table name from the schema
                return schema.table_name

        # Fallback to entity name if no schema found
        return entity_name

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

    def detect_schemas(self, file_path: str) -> List[TableSchema]:
        """Detect database table/entity schemas in C# files.

        This identifies:
        - Entity Framework entity classes (POCOs)
        - DbContext DbSet properties
        - [Table] attributes

        Args:
            file_path: Path to the C# file

        Returns:
            List of TableSchema objects found in the file
        """
        schemas = []
        content = self.read_file(file_path)
        lines = content.split('\n')

        # Detect DbContext and its DbSet properties
        dbsets = self._detect_dbsets(file_path, lines)
        schemas.extend(dbsets)

        # Detect Entity classes (with [Table] attribute or typical entity patterns)
        entities = self._detect_entity_classes(file_path, lines)
        schemas.extend(entities)

        return schemas

    def _detect_dbsets(self, file_path: str, lines: List[str]) -> List[TableSchema]:
        """Detect DbSet properties in DbContext classes."""
        schemas = []
        in_dbcontext = False

        for i, line in enumerate(lines, 1):
            # Detect DbContext class
            if re.search(r'class\s+\w+\s*:\s*DbContext', line):
                in_dbcontext = True
                continue

            # Look for DbSet<EntityName> PropertyName
            if in_dbcontext:
                dbset_match = re.search(r'DbSet<(\w+)>\s+(\w+)', line)
                if dbset_match:
                    entity_name = dbset_match.group(1)
                    dbset_property = dbset_match.group(2)

                    # Table name is typically the DbSet property name (pluralized)
                    table_name = dbset_property

                    schema = TableSchema(
                        entity_name=entity_name,
                        table_name=table_name,
                        file_path=file_path,
                        line_number=i,
                        dbset_name=dbset_property,
                        metadata={'source': 'DbContext', 'detected_from': 'DbSet'}
                    )
                    schemas.append(schema)

            # Exit DbContext when we hit the closing brace (simplified)
            if in_dbcontext and line.strip() == '}':
                in_dbcontext = False

        return schemas

    def _detect_entity_classes(self, file_path: str, lines: List[str]) -> List[TableSchema]:
        """Detect Entity Framework entity classes."""
        schemas = []
        current_class = None
        current_line = 0
        table_attribute = None
        properties = []

        for i, line in enumerate(lines, 1):
            # Look for [Table("TableName")] attribute
            table_match = re.search(r'\[Table\("([^"]+)"\)\]', line)
            if table_match:
                table_attribute = table_match.group(1)
                continue

            # Detect class definition
            class_match = re.search(r'class\s+(\w+)', line)
            if class_match:
                # Save previous class if it looks like an entity
                if current_class and self._looks_like_entity(properties):
                    table_name = table_attribute or current_class  # Use attribute or class name
                    schema = TableSchema(
                        entity_name=current_class,
                        table_name=table_name,
                        file_path=file_path,
                        line_number=current_line,
                        properties=properties,
                        metadata={'source': 'Entity', 'has_table_attribute': table_attribute is not None}
                    )
                    schemas.append(schema)

                # Start tracking new class
                current_class = class_match.group(1)
                current_line = i
                properties = []
                table_attribute = None

            # Detect properties (simplified: public Type PropName { get; set; })
            if current_class:
                prop_match = re.search(r'public\s+\w+\??(\[\])?\s+(\w+)\s*\{\s*get;', line)
                if prop_match:
                    prop_name = prop_match.group(2)
                    properties.append(prop_name)

        # Don't forget the last class
        if current_class and self._looks_like_entity(properties):
            table_name = table_attribute or current_class
            schema = TableSchema(
                entity_name=current_class,
                table_name=table_name,
                file_path=file_path,
                line_number=current_line,
                properties=properties,
                metadata={'source': 'Entity', 'has_table_attribute': table_attribute is not None}
            )
            schemas.append(schema)

        return schemas

    def _looks_like_entity(self, properties: List[str]) -> bool:
        """Heuristic to determine if a class looks like a database entity.

        A class is likely an entity if it has:
        - At least 2 properties
        - Common entity property names like Id, Name, CreatedAt, etc.
        """
        if len(properties) < 2:
            return False

        # Check for common entity patterns
        common_props = {'Id', 'ID', 'Name', 'CreatedAt', 'UpdatedAt', 'Created', 'Modified'}
        has_common = any(prop in common_props for prop in properties)

        return has_common or len(properties) >= 3
