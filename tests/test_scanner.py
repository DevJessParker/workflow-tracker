"""Tests for code scanners."""

import pytest
from src.scanner.csharp_scanner import CSharpScanner
from src.scanner.typescript_scanner import TypeScriptScanner
from src.models import WorkflowType


class TestCSharpScanner:
    """Tests for C# scanner."""

    def test_can_scan_cs_files(self):
        """Test that scanner recognizes .cs files."""
        scanner = CSharpScanner({})
        assert scanner.can_scan("test.cs")
        assert scanner.can_scan("/path/to/UserService.cs")
        assert not scanner.can_scan("test.ts")
        assert not scanner.can_scan("test.py")

    def test_detect_entity_framework_query(self):
        """Test detection of Entity Framework queries."""
        scanner = CSharpScanner({'detect': {'database': True}})

        code = """
        public class UserService
        {
            public User GetUser(int id)
            {
                return _context.Users
                    .Where(u => u.Id == id)
                    .FirstOrDefault();
            }
        }
        """

        # Create a temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cs', delete=False) as f:
            f.write(code)
            f.flush()

            graph = scanner.scan_file(f.name)

            # Should detect database read operations
            db_reads = graph.get_nodes_by_type(WorkflowType.DATABASE_READ)
            assert len(db_reads) > 0

    def test_detect_http_client_call(self):
        """Test detection of HttpClient API calls."""
        scanner = CSharpScanner({'detect': {'api_calls': True}})

        code = """
        public async Task<string> GetDataAsync(string url)
        {
            var client = new HttpClient();
            var response = await client.GetAsync(url);
            return await response.Content.ReadAsStringAsync();
        }
        """

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cs', delete=False) as f:
            f.write(code)
            f.flush()

            graph = scanner.scan_file(f.name)

            # Should detect API call
            api_calls = graph.get_nodes_by_type(WorkflowType.API_CALL)
            assert len(api_calls) > 0


class TestTypeScriptScanner:
    """Tests for TypeScript scanner."""

    def test_can_scan_ts_files(self):
        """Test that scanner recognizes TypeScript files."""
        scanner = TypeScriptScanner({})
        assert scanner.can_scan("test.ts")
        assert scanner.can_scan("component.tsx")
        assert scanner.can_scan("script.js")
        assert not scanner.can_scan("test.cs")

    def test_detect_http_client(self):
        """Test detection of Angular HttpClient calls."""
        scanner = TypeScriptScanner({'detect': {'api_calls': True}})

        code = """
        export class UserService {
            constructor(private http: HttpClient) {}

            getUsers(): Observable<User[]> {
                return this.http.get<User[]>('/api/users');
            }
        }
        """

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(code)
            f.flush()

            graph = scanner.scan_file(f.name)

            # Should detect API call
            api_calls = graph.get_nodes_by_type(WorkflowType.API_CALL)
            assert len(api_calls) > 0

    def test_detect_local_storage(self):
        """Test detection of localStorage operations."""
        scanner = TypeScriptScanner({})

        code = """
        export class StorageService {
            saveToken(token: string): void {
                localStorage.setItem('auth_token', token);
            }

            getToken(): string {
                return localStorage.getItem('auth_token');
            }
        }
        """

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(code)
            f.flush()

            graph = scanner.scan_file(f.name)

            # Should detect cache operations
            cache_ops = (
                graph.get_nodes_by_type(WorkflowType.CACHE_READ) +
                graph.get_nodes_by_type(WorkflowType.CACHE_WRITE)
            )
            assert len(cache_ops) > 0


class TestGraphBuilder:
    """Tests for graph builder."""

    def test_infer_workflow_edges(self):
        """Test that edges are inferred between related operations."""
        from src.graph.builder import WorkflowGraphBuilder

        config = {
            'scanner': {
                'include_extensions': ['.cs'],
                'exclude_dirs': ['node_modules', 'bin', 'obj'],
                'detect': {
                    'database': True,
                    'api_calls': True,
                }
            }
        }

        builder = WorkflowGraphBuilder(config)

        # Test with a sample file
        code = """
        public async Task ProcessData(string url)
        {
            // Fetch from API
            var data = await _httpClient.GetAsync(url);

            // Save to database
            _context.Items.Add(new Item { Data = data });
            await _context.SaveChangesAsync();
        }
        """

        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, 'test.cs')
            with open(file_path, 'w') as f:
                f.write(code)

            result = builder.build(tmpdir)

            # Should detect both API call and database write
            assert len(result.graph.nodes) >= 2

            # Should create edge between them
            assert len(result.graph.edges) > 0
