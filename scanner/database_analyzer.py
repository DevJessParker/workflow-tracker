"""
Database Table Analyzer - Analyzes database operations, schemas, and migrations
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

from models import WorkflowGraph, WorkflowNode, WorkflowType


@dataclass
class TableOperation:
    """Represents a database operation on a table"""
    operation_type: str  # 'read' or 'write'
    file_path: str
    line_number: int
    node_id: str


@dataclass
class MigrationInfo:
    """Information about a migration affecting a table"""
    file_path: str
    migration_name: str
    timestamp: str
    changes: List[str]  # List of changes made to the table


@dataclass
class ColumnInfo:
    """Information about a table column"""
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    default: Optional[str] = None


@dataclass
class TableAnalysis:
    """Complete analysis of a database table"""
    table_name: str
    read_count: int = 0
    write_count: int = 0
    schema_file: Optional[str] = None
    schema_line: Optional[int] = None
    migrations: List[MigrationInfo] = field(default_factory=list)
    columns: Dict[str, ColumnInfo] = field(default_factory=dict)
    indexes: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)


class DatabaseTableAnalyzer:
    """Analyzes database tables from workflow graph and repository files"""

    def __init__(self, graph: WorkflowGraph, repository_path: str):
        self.graph = graph
        self.repository_path = repository_path
        self.tables: Dict[str, TableAnalysis] = {}

    def analyze(self) -> Dict[str, TableAnalysis]:
        """Perform complete database table analysis"""
        print("\n" + "="*60)
        print("ANALYZING DATABASE TABLES")
        print("="*60)

        # Step 1: Count operations per table from workflow graph
        self._count_operations()
        print(f"✓ Counted operations for {len(self.tables)} tables")

        # Step 2: Find schema/model files for each table
        self._find_schema_files()
        print(f"✓ Found schema files")

        # Step 3: Parse schema files to extract column information
        self._parse_schemas()
        print(f"✓ Parsed table schemas")

        # Step 4: Find and parse migration files
        self._find_migrations()
        print(f"✓ Found migration files")

        # Step 5: Apply migrations to get current schema
        self._apply_migrations()
        print(f"✓ Applied migrations to schemas")

        print(f"✓ Analyzed {len(self.tables)} database tables")
        print("="*60 + "\n")

        return self.tables

    def _count_operations(self):
        """Count read and write operations per table from workflow graph"""
        for node in self.graph.nodes:
            if node.type in [WorkflowType.DATABASE_READ, WorkflowType.DATABASE_WRITE]:
                table_name = node.table_name
                if not table_name:
                    continue

                if table_name not in self.tables:
                    self.tables[table_name] = TableAnalysis(table_name=table_name)

                if node.type == WorkflowType.DATABASE_READ:
                    self.tables[table_name].read_count += 1
                else:
                    self.tables[table_name].write_count += 1

    def _find_schema_files(self):
        """Find schema/model files for each table"""
        # Common patterns for schema files
        schema_patterns = [
            '**/models/*.cs',      # C# Entity Framework
            '**/Models/*.cs',
            '**/entities/*.ts',    # TypeScript/Node.js
            '**/models/*.ts',
            '**/entity/*.ts',
            '**/models.py',        # Python
            '**/schema.py',
            '**/models/*.py',
        ]

        repo_path = Path(self.repository_path)

        for table_name in self.tables.keys():
            # Search for files that might contain this table's definition
            for pattern in schema_patterns:
                for file_path in repo_path.glob(pattern):
                    if self._file_contains_table_definition(file_path, table_name):
                        self.tables[table_name].schema_file = str(file_path)
                        # Find line number where table is defined
                        line_num = self._find_table_definition_line(file_path, table_name)
                        self.tables[table_name].schema_line = line_num
                        break

                if self.tables[table_name].schema_file:
                    break

    def _file_contains_table_definition(self, file_path: Path, table_name: str) -> bool:
        """Check if a file contains the table definition"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Pattern matching for different languages
            patterns = [
                # C# Entity Framework
                rf'class\s+{table_name}\s*:',
                rf'class\s+{table_name}\s*{{',
                rf'DbSet<{table_name}>',
                # TypeScript/Sequelize
                rf'sequelize\.define\([\'\"]{table_name}[\'"]',
                rf'@Entity\([\'\"]{table_name}[\'"]',
                # Python SQLAlchemy
                rf'__tablename__\s*=\s*[\'\"]{table_name.lower()}[\'"]',
                rf'class\s+{table_name}\(',
            ]

            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

        return False

    def _find_table_definition_line(self, file_path: Path, table_name: str) -> Optional[int]:
        """Find the line number where table is defined"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if re.search(rf'class\s+{table_name}\s*[(:{{]', line, re.IGNORECASE):
                        return line_num
                    if re.search(rf'__tablename__\s*=\s*[\'\"]{table_name.lower()}[\'"]', line, re.IGNORECASE):
                        return line_num
        except Exception:
            pass

        return None

    def _parse_schemas(self):
        """Parse schema files to extract column information"""
        for table_name, analysis in self.tables.items():
            if not analysis.schema_file:
                continue

            try:
                with open(analysis.schema_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Extract columns based on file type
                if analysis.schema_file.endswith('.cs'):
                    columns = self._parse_csharp_schema(content, table_name)
                elif analysis.schema_file.endswith('.ts'):
                    columns = self._parse_typescript_schema(content, table_name)
                elif analysis.schema_file.endswith('.py'):
                    columns = self._parse_python_schema(content, table_name)
                else:
                    columns = {}

                analysis.columns = columns

            except Exception as e:
                print(f"Error parsing schema for {table_name}: {e}")

    def _parse_csharp_schema(self, content: str, table_name: str) -> Dict[str, ColumnInfo]:
        """Parse C# Entity Framework schema"""
        columns = {}

        # Find class definition
        class_match = re.search(rf'class\s+{table_name}\s*[:\{{].*?^}}', content, re.MULTILINE | re.DOTALL)
        if not class_match:
            return columns

        class_body = class_match.group(0)

        # Extract properties
        property_pattern = r'public\s+(\w+(?:\?)?)\s+(\w+)\s*\{\s*get;\s*set;\s*\}'
        for match in re.finditer(property_pattern, class_body):
            data_type = match.group(1)
            column_name = match.group(2)

            nullable = '?' in data_type
            data_type = data_type.replace('?', '')

            # Check for [Key] attribute
            prop_context = class_body[:match.start()]
            is_pk = bool(re.search(r'\[Key\]', prop_context[-100:]))

            # Check for [ForeignKey] attribute
            fk_match = re.search(r'\[ForeignKey\([\'"](\w+)[\'"]\)\]', prop_context[-200:])
            foreign_key = fk_match.group(1) if fk_match else None

            columns[column_name] = ColumnInfo(
                name=column_name,
                data_type=data_type,
                nullable=nullable,
                primary_key=is_pk,
                foreign_key=foreign_key
            )

        return columns

    def _parse_typescript_schema(self, content: str, table_name: str) -> Dict[str, ColumnInfo]:
        """Parse TypeScript/Sequelize schema"""
        columns = {}

        # Look for Sequelize.define or decorator-based definitions
        # This is a simplified parser
        define_match = re.search(rf'define\([\'\"]{table_name}[\'"],\s*\{{(.*?)\}}', content, re.DOTALL)
        if define_match:
            schema_body = define_match.group(1)

            # Extract column definitions
            column_pattern = r'(\w+):\s*\{\s*type:\s*DataTypes\.(\w+)'
            for match in re.finditer(column_pattern, schema_body):
                column_name = match.group(1)
                data_type = match.group(2)

                columns[column_name] = ColumnInfo(
                    name=column_name,
                    data_type=data_type
                )

        return columns

    def _parse_python_schema(self, content: str, table_name: str) -> Dict[str, ColumnInfo]:
        """Parse Python SQLAlchemy schema"""
        columns = {}

        # Find class definition
        class_match = re.search(rf'class\s+{table_name}\(.*?\):(.*?)(?=class\s|\Z)', content, re.MULTILINE | re.DOTALL)
        if not class_match:
            return columns

        class_body = class_match.group(1)

        # Extract Column definitions
        column_pattern = r'(\w+)\s*=\s*Column\((.*?)\)'
        for match in re.finditer(column_pattern, class_body):
            column_name = match.group(1)
            column_def = match.group(2)

            # Parse data type
            type_match = re.search(r'(Integer|String|Boolean|DateTime|Float|Text|BigInteger|Numeric)', column_def)
            data_type = type_match.group(1) if type_match else 'Unknown'

            # Check for primary_key
            is_pk = 'primary_key=True' in column_def

            # Check for nullable
            nullable = 'nullable=False' not in column_def

            columns[column_name] = ColumnInfo(
                name=column_name,
                data_type=data_type,
                nullable=nullable,
                primary_key=is_pk
            )

        return columns

    def _find_migrations(self):
        """Find migration files affecting each table"""
        migration_patterns = [
            '**/migrations/*.cs',
            '**/Migrations/*.cs',
            '**/migrations/*.sql',
            '**/db/migrate/*.rb',
            '**/migrations/*.py',
            '**/migrations/*.ts',
            '**/migrations/*.js',
        ]

        repo_path = Path(self.repository_path)

        for table_name in self.tables.keys():
            migrations = []

            for pattern in migration_patterns:
                for file_path in repo_path.glob(pattern):
                    if self._migration_affects_table(file_path, table_name):
                        migration_info = self._parse_migration_file(file_path, table_name)
                        if migration_info:
                            migrations.append(migration_info)

            # Sort migrations by timestamp
            migrations.sort(key=lambda m: m.timestamp)
            self.tables[table_name].migrations = migrations

    def _migration_affects_table(self, file_path: Path, table_name: str) -> bool:
        """Check if migration file affects the table"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Look for table name in migration
            patterns = [
                rf'CreateTable.*{table_name}',
                rf'AlterTable.*{table_name}',
                rf'create_table.*{table_name.lower()}',
                rf'alter_table.*{table_name.lower()}',
                rf'CREATE TABLE.*{table_name}',
                rf'ALTER TABLE.*{table_name}',
            ]

            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True

        except Exception:
            pass

        return False

    def _parse_migration_file(self, file_path: Path, table_name: str) -> Optional[MigrationInfo]:
        """Parse migration file to extract changes"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Extract timestamp from filename
            timestamp_match = re.search(r'(\d{14}|\d{10})', file_path.name)
            timestamp = timestamp_match.group(1) if timestamp_match else '0'

            # Extract changes
            changes = []

            # Look for CREATE TABLE
            if re.search(rf'CREATE TABLE.*{table_name}', content, re.IGNORECASE):
                changes.append('Create table')

            # Look for ALTER TABLE
            alter_matches = re.finditer(rf'ALTER TABLE.*{table_name}.*?;', content, re.IGNORECASE | re.DOTALL)
            for match in alter_matches:
                change_text = match.group(0)
                if 'ADD COLUMN' in change_text.upper():
                    changes.append('Add column')
                elif 'DROP COLUMN' in change_text.upper():
                    changes.append('Drop column')
                elif 'MODIFY COLUMN' in change_text.upper():
                    changes.append('Modify column')
                elif 'ADD CONSTRAINT' in change_text.upper():
                    changes.append('Add constraint')

            if changes:
                return MigrationInfo(
                    file_path=str(file_path),
                    migration_name=file_path.stem,
                    timestamp=timestamp,
                    changes=changes
                )

        except Exception as e:
            print(f"Error parsing migration {file_path}: {e}")

        return None

    def _apply_migrations(self):
        """Apply migrations to get current schema state"""
        # This is a simplified version - in reality, you'd need to parse
        # each migration and apply the changes sequentially
        for table_name, analysis in self.tables.items():
            # If we have migrations, note that the schema is post-migration
            if analysis.migrations:
                # Mark that schema includes migrations
                analysis.relationships.append(f"Schema includes {len(analysis.migrations)} migration(s)")

    def to_dict(self) -> Dict[str, dict]:
        """Convert analysis to dictionary for JSON serialization"""
        result = {}

        for table_name, analysis in self.tables.items():
            result[table_name] = {
                'table_name': analysis.table_name,
                'read_count': analysis.read_count,
                'write_count': analysis.write_count,
                'schema_file': analysis.schema_file,
                'schema_line': analysis.schema_line,
                'migrations': [
                    {
                        'file_path': m.file_path,
                        'migration_name': m.migration_name,
                        'timestamp': m.timestamp,
                        'changes': m.changes
                    }
                    for m in analysis.migrations
                ],
                'schema': {
                    'columns': {
                        col_name: {
                            'name': col.name,
                            'data_type': col.data_type,
                            'nullable': col.nullable,
                            'primary_key': col.primary_key,
                            'foreign_key': col.foreign_key,
                            'default': col.default
                        }
                        for col_name, col in analysis.columns.items()
                    },
                    'indexes': analysis.indexes,
                    'relationships': analysis.relationships
                }
            }

        return result
