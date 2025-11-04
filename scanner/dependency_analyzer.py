"""
Dependency Analyzer

Analyzes project dependencies to provide:
- Current and latest versions
- Outdated dependencies
- Unused dependencies
- Redundant/conflicting dependencies
- Security and maintenance metrics
"""

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict


@dataclass
class DependencyInfo:
    """Information about a single dependency"""
    name: str
    current_version: str
    latest_version: Optional[str] = None
    package_file: str = None
    package_manager: str = None  # npm, pip, nuget, etc.

    # Usage information
    is_used: bool = False
    usage_count: int = 0
    used_in_files: List[str] = field(default_factory=list)

    # Version analysis
    is_outdated: bool = False
    versions_behind: int = 0
    major_update_available: bool = False
    minor_update_available: bool = False
    patch_update_available: bool = False

    # Dependency type
    is_dev_dependency: bool = False
    is_peer_dependency: bool = False

    # Issues
    has_security_warning: bool = False
    is_deprecated: bool = False
    has_conflict: bool = False
    conflict_details: Optional[str] = None

    # Additional metadata
    description: Optional[str] = None
    license: Optional[str] = None
    last_published: Optional[str] = None


@dataclass
class DependencyConflict:
    """Information about a dependency conflict"""
    package_name: str
    versions: List[str]
    locations: List[str]
    severity: str  # 'warning', 'error'


@dataclass
class DependencyMetrics:
    """Aggregate metrics for dependency health"""
    total_dependencies: int = 0
    outdated_count: int = 0
    unused_count: int = 0
    security_warnings: int = 0
    deprecated_count: int = 0
    conflict_count: int = 0

    major_updates_available: int = 0
    minor_updates_available: int = 0
    patch_updates_available: int = 0

    avg_versions_behind: float = 0.0
    health_score: float = 100.0  # 0-100


class DependencyAnalyzer:
    """Analyzes project dependencies"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.dependencies: Dict[str, DependencyInfo] = {}
        self.conflicts: List[DependencyConflict] = []
        self.metrics = DependencyMetrics()

    def analyze(self, progress_callback=None) -> Dict[str, DependencyInfo]:
        """Run complete dependency analysis

        Args:
            progress_callback: Optional callback function(step, total_steps, message) for progress updates
        """
        print("📦 Analyzing dependencies...")

        total_steps = 4

        # Step 1: Find and parse all package files
        self._find_and_parse_package_files()
        if progress_callback:
            progress_callback(1, total_steps, f"Parsed {len(self.dependencies)} dependencies")

        # Step 2: Check usage in codebase
        self._check_dependency_usage()
        if progress_callback:
            progress_callback(2, total_steps, "Checked dependency usage in codebase")

        # Step 3: Detect conflicts and redundancies
        self._detect_conflicts()
        if progress_callback:
            progress_callback(3, total_steps, "Detected conflicts and redundancies")

        # Step 4: Calculate metrics
        self._calculate_metrics()
        if progress_callback:
            progress_callback(4, total_steps, "Calculated dependency metrics")

        print(f"Found {len(self.dependencies)} dependencies")
        print(f"Outdated: {self.metrics.outdated_count}, Unused: {self.metrics.unused_count}, Conflicts: {self.metrics.conflict_count}")

        return self.dependencies

    def _find_and_parse_package_files(self):
        """Find and parse all package management files"""
        # JavaScript/TypeScript - package.json
        package_json_files = list(self.repo_path.glob('**/package.json'))
        for file in package_json_files:
            if 'node_modules' not in file.parts:
                self._parse_package_json(file)

        # Python - requirements.txt, setup.py, pyproject.toml
        for file in self.repo_path.glob('**/requirements*.txt'):
            if 'venv' not in file.parts and 'env' not in file.parts:
                self._parse_requirements_txt(file)

        for file in self.repo_path.glob('**/Pipfile'):
            self._parse_pipfile(file)

        for file in self.repo_path.glob('**/pyproject.toml'):
            self._parse_pyproject_toml(file)

        # C# - .csproj files
        for file in self.repo_path.glob('**/*.csproj'):
            self._parse_csproj(file)

        # Ruby - Gemfile
        for file in self.repo_path.glob('**/Gemfile'):
            self._parse_gemfile(file)

    def _parse_package_json(self, file_path: Path):
        """Parse package.json file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Regular dependencies
            for name, version in data.get('dependencies', {}).items():
                self._add_dependency(
                    name=name,
                    version=self._clean_version(version),
                    package_file=str(file_path.relative_to(self.repo_path)),
                    package_manager='npm',
                    is_dev=False
                )

            # Dev dependencies
            for name, version in data.get('devDependencies', {}).items():
                self._add_dependency(
                    name=name,
                    version=self._clean_version(version),
                    package_file=str(file_path.relative_to(self.repo_path)),
                    package_manager='npm',
                    is_dev=True
                )

            # Peer dependencies
            for name, version in data.get('peerDependencies', {}).items():
                dep = self._add_dependency(
                    name=name,
                    version=self._clean_version(version),
                    package_file=str(file_path.relative_to(self.repo_path)),
                    package_manager='npm',
                    is_dev=False
                )
                dep.is_peer_dependency = True

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    def _parse_requirements_txt(self, file_path: Path):
        """Parse requirements.txt file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Parse package==version or package>=version
                    match = re.match(r'([a-zA-Z0-9_\-\.]+)\s*([=><~!]+)\s*(.+)', line)
                    if match:
                        name = match.group(1)
                        version = match.group(3)
                        self._add_dependency(
                            name=name,
                            version=self._clean_version(version),
                            package_file=str(file_path.relative_to(self.repo_path)),
                            package_manager='pip',
                            is_dev='dev' in file_path.name.lower() or 'test' in file_path.name.lower()
                        )
                    else:
                        # Package without version specified
                        name = line.split('[')[0].strip()  # Handle extras like package[extra]
                        if name:
                            self._add_dependency(
                                name=name,
                                version='*',
                                package_file=str(file_path.relative_to(self.repo_path)),
                                package_manager='pip',
                                is_dev=False
                            )

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    def _parse_pipfile(self, file_path: Path):
        """Parse Pipfile"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple parsing for [packages] and [dev-packages] sections
            in_packages = False
            in_dev_packages = False

            for line in content.split('\n'):
                line = line.strip()

                if line == '[packages]':
                    in_packages = True
                    in_dev_packages = False
                    continue
                elif line == '[dev-packages]':
                    in_dev_packages = True
                    in_packages = False
                    continue
                elif line.startswith('['):
                    in_packages = False
                    in_dev_packages = False
                    continue

                if (in_packages or in_dev_packages) and '=' in line:
                    parts = line.split('=', 1)
                    name = parts[0].strip()
                    version = parts[1].strip().strip('"\'')

                    self._add_dependency(
                        name=name,
                        version=self._clean_version(version),
                        package_file=str(file_path.relative_to(self.repo_path)),
                        package_manager='pip',
                        is_dev=in_dev_packages
                    )

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    def _parse_pyproject_toml(self, file_path: Path):
        """Parse pyproject.toml file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple parsing for dependencies section
            in_dependencies = False
            for line in content.split('\n'):
                line = line.strip()

                if 'dependencies' in line and '=' in line:
                    in_dependencies = True
                    continue
                elif in_dependencies and ']' in line:
                    in_dependencies = False
                    continue

                if in_dependencies and line.startswith('"'):
                    # Parse "package==version" or "package>=version"
                    dep_str = line.strip('"\'",')
                    match = re.match(r'([a-zA-Z0-9_\-\.]+)\s*([=><~!]+)\s*(.+)', dep_str)
                    if match:
                        name = match.group(1)
                        version = match.group(3)
                        self._add_dependency(
                            name=name,
                            version=self._clean_version(version),
                            package_file=str(file_path.relative_to(self.repo_path)),
                            package_manager='pip',
                            is_dev=False
                        )

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    def _parse_csproj(self, file_path: Path):
        """Parse .csproj file for NuGet packages"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Find PackageReference elements
            for package_ref in root.findall('.//PackageReference'):
                name = package_ref.get('Include')
                version = package_ref.get('Version', '*')

                if name:
                    self._add_dependency(
                        name=name,
                        version=self._clean_version(version),
                        package_file=str(file_path.relative_to(self.repo_path)),
                        package_manager='nuget',
                        is_dev=False
                    )

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    def _parse_gemfile(self, file_path: Path):
        """Parse Ruby Gemfile"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Parse gem 'name', 'version'
                    match = re.match(r"gem\s+['\"]([^'\"]+)['\"](?:,\s*['\"]([^'\"]+)['\"])?", line)
                    if match:
                        name = match.group(1)
                        version = match.group(2) if match.group(2) else '*'
                        self._add_dependency(
                            name=name,
                            version=self._clean_version(version),
                            package_file=str(file_path.relative_to(self.repo_path)),
                            package_manager='gem',
                            is_dev=False
                        )

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    def _clean_version(self, version: str) -> str:
        """Clean version string to extract actual version number"""
        # Remove common prefixes
        version = version.lstrip('^~>=<')
        # Remove quotes
        version = version.strip('"\'')
        # Handle version ranges - take the first version
        if '||' in version:
            version = version.split('||')[0].strip()
        if ' - ' in version:
            version = version.split(' - ')[0].strip()

        return version or '*'

    def _add_dependency(self, name: str, version: str, package_file: str, package_manager: str, is_dev: bool) -> DependencyInfo:
        """Add or update a dependency"""
        key = f"{package_manager}:{name}"

        if key in self.dependencies:
            # Update existing dependency
            dep = self.dependencies[key]
            # Check for version conflicts
            if dep.current_version != version and version != '*':
                dep.has_conflict = True
                dep.conflict_details = f"Version conflict: {dep.current_version} in {dep.package_file} vs {version} in {package_file}"
        else:
            # Create new dependency
            dep = DependencyInfo(
                name=name,
                current_version=version,
                package_file=package_file,
                package_manager=package_manager,
                is_dev_dependency=is_dev
            )
            self.dependencies[key] = dep

        return dep

    def _check_dependency_usage(self):
        """Check if dependencies are actually used in the codebase"""
        # Find all source files
        source_patterns = ['**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx',
                          '**/*.py', '**/*.cs', '**/*.rb']

        for pattern in source_patterns:
            for file_path in self.repo_path.glob(pattern):
                # Skip node_modules, venv, etc.
                if any(ex in file_path.parts for ex in ['node_modules', 'venv', 'env', 'dist', 'build', '.next']):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Check for each dependency
                    for key, dep in self.dependencies.items():
                        # Look for import/require statements
                        patterns = [
                            f"import.*from.*['\"]({dep.name})['\"]",
                            f"import.*['\"]({dep.name})['\"]",
                            f"require\\(['\"]({dep.name})['\"]\\)",
                            f"using\\s+{dep.name}",  # C#
                            f"from\\s+{dep.name}\\s+import",  # Python
                        ]

                        for pattern in patterns:
                            if re.search(pattern, content):
                                dep.is_used = True
                                dep.usage_count += 1
                                rel_path = str(file_path.relative_to(self.repo_path))
                                if rel_path not in dep.used_in_files:
                                    dep.used_in_files.append(rel_path)
                                break

                except Exception as e:
                    pass  # Silently skip files that can't be read

    def _detect_conflicts(self):
        """Detect dependency conflicts and redundancies"""
        # Group by package name (ignoring package manager prefix)
        by_name = defaultdict(list)
        for key, dep in self.dependencies.items():
            by_name[dep.name].append(dep)

        # Check for conflicts
        for name, deps in by_name.items():
            if len(deps) > 1:
                # Multiple versions of same package
                versions = list(set(d.current_version for d in deps))
                if len(versions) > 1:
                    # Real conflict - different versions
                    conflict = DependencyConflict(
                        package_name=name,
                        versions=versions,
                        locations=[d.package_file for d in deps],
                        severity='warning' if any(d.is_dev_dependency for d in deps) else 'error'
                    )
                    self.conflicts.append(conflict)

                    # Mark all instances as conflicted
                    for dep in deps:
                        dep.has_conflict = True
                        dep.conflict_details = f"Multiple versions found: {', '.join(versions)}"

    def _calculate_metrics(self):
        """Calculate aggregate metrics"""
        self.metrics.total_dependencies = len(self.dependencies)

        # Count various issues
        for dep in self.dependencies.values():
            if not dep.is_used and not dep.is_dev_dependency:
                self.metrics.unused_count += 1

            if dep.is_outdated:
                self.metrics.outdated_count += 1

                if dep.major_update_available:
                    self.metrics.major_updates_available += 1
                elif dep.minor_update_available:
                    self.metrics.minor_updates_available += 1
                elif dep.patch_update_available:
                    self.metrics.patch_updates_available += 1

            if dep.has_security_warning:
                self.metrics.security_warnings += 1

            if dep.is_deprecated:
                self.metrics.deprecated_count += 1

        self.metrics.conflict_count = len(self.conflicts)

        # Calculate average versions behind
        versions_behind = [d.versions_behind for d in self.dependencies.values() if d.versions_behind > 0]
        if versions_behind:
            self.metrics.avg_versions_behind = sum(versions_behind) / len(versions_behind)

        # Calculate health score (100 = perfect, 0 = terrible)
        health_score = 100.0

        if self.metrics.total_dependencies > 0:
            # Deduct for outdated (up to -30 points)
            outdated_ratio = self.metrics.outdated_count / self.metrics.total_dependencies
            health_score -= outdated_ratio * 30

            # Deduct for unused (up to -20 points)
            unused_ratio = self.metrics.unused_count / self.metrics.total_dependencies
            health_score -= unused_ratio * 20

            # Deduct for security warnings (up to -30 points)
            security_ratio = self.metrics.security_warnings / self.metrics.total_dependencies
            health_score -= security_ratio * 30

            # Deduct for conflicts (up to -15 points)
            conflict_ratio = self.metrics.conflict_count / self.metrics.total_dependencies
            health_score -= conflict_ratio * 15

            # Deduct for deprecated (up to -5 points)
            deprecated_ratio = self.metrics.deprecated_count / self.metrics.total_dependencies
            health_score -= deprecated_ratio * 5

        self.metrics.health_score = max(0.0, health_score)

    def to_dict(self) -> Dict:
        """Convert analysis results to dictionary"""
        return {
            'dependencies': {
                key: asdict(dep) for key, dep in self.dependencies.items()
            },
            'conflicts': [asdict(c) for c in self.conflicts],
            'metrics': asdict(self.metrics)
        }
