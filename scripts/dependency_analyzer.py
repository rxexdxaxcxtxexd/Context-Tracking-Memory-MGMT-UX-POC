#!/usr/bin/env python3
"""
Dependency Analyzer - Cross-file dependency tracking for session continuity

This module analyzes Python codebases to identify:
- Import relationships between files
- Function call dependencies
- Reverse dependencies (who uses this file)
- Impact scores (how critical is this file)

Used by save-session.py to generate smarter resume points and impact warnings.
"""

import ast
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class FileDependency:
    """Dependency information for a single file"""
    file_path: str
    imports_from: List[str]  # Files this file imports
    used_by: List[str]  # Files that import this file
    used_by_count: int  # Number of files depending on this
    function_calls_to: List[str]  # External functions called
    has_tests: bool  # Whether test file exists
    impact_score: int  # 0-100, higher = more critical


class DependencyAnalyzer:
    """Analyzes cross-file dependencies in Python codebases"""

    def __init__(self, base_dir: Path, changed_files: List[str], use_cache: bool = True):
        """
        Initialize dependency analyzer

        Args:
            base_dir: Project root directory
            changed_files: List of file paths that changed (relative to base_dir)
            use_cache: Whether to use dependency caching (default: True)
        """
        self.base_dir = Path(base_dir)
        self.changed_files = [self.base_dir / f for f in changed_files]
        self.use_cache = use_cache

        # Cache directory
        self.cache_dir = Path.home() / ".claude-sessions" / "dependency_cache"
        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Dependency graph
        self.imports: Dict[str, Set[str]] = defaultdict(set)  # file -> imports
        self.importers: Dict[str, Set[str]] = defaultdict(set)  # file -> who imports it
        self.function_calls: Dict[str, Set[str]] = defaultdict(set)  # file -> function calls

        # Performance tracking
        self.files_analyzed = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = []

    def _get_cache_key(self, filepath: Path) -> str:
        """Generate cache key for a file

        Args:
            filepath: Absolute path to file

        Returns:
            Cache key (hex hash of relative path)
        """
        rel_path = str(filepath.relative_to(self.base_dir))
        # Use hash to avoid filesystem issues with special characters
        return hashlib.md5(rel_path.encode()).hexdigest()

    def _get_cache_path(self, filepath: Path) -> Path:
        """Get cache file path for a source file

        Args:
            filepath: Absolute path to file

        Returns:
            Path to cache file
        """
        cache_key = self._get_cache_key(filepath)
        return self.cache_dir / f"{cache_key}.json"

    def _load_cached_dependency(self, filepath: Path) -> Optional[FileDependency]:
        """Load cached dependency if still valid

        Args:
            filepath: Absolute path to file

        Returns:
            FileDependency if cache valid, None otherwise
        """
        if not self.use_cache:
            return None

        cache_path = self._get_cache_path(filepath)

        if not cache_path.exists():
            return None

        try:
            # Check if source file is newer than cache
            source_mtime = filepath.stat().st_mtime
            cache_mtime = cache_path.stat().st_mtime

            if source_mtime > cache_mtime:
                # Source file modified after cache was created
                return None

            # Load cached data
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Validate cache has required fields
            required_fields = ['file_path', 'imports_from', 'used_by', 'used_by_count',
                             'function_calls_to', 'has_tests', 'impact_score', 'mtime']

            if not all(field in cache_data for field in required_fields):
                return None

            # Check if mtime matches (additional validation)
            if cache_data['mtime'] != source_mtime:
                return None

            # Convert to FileDependency (remove mtime field)
            del cache_data['mtime']
            return FileDependency(**cache_data)

        except Exception:
            # Cache corrupted or unreadable, ignore
            return None

    def _save_cached_dependency(self, filepath: Path, dependency: FileDependency):
        """Save dependency to cache

        Args:
            filepath: Absolute path to file
            dependency: FileDependency object to cache
        """
        if not self.use_cache:
            return

        try:
            cache_path = self._get_cache_path(filepath)

            # Add mtime for validation
            cache_data = asdict(dependency)
            cache_data['mtime'] = filepath.stat().st_mtime

            # Save to cache
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)

        except Exception:
            # Failed to cache, not critical
            pass

    def analyze_dependencies(self) -> Dict[str, FileDependency]:
        """
        Main entry point - analyze all dependencies

        Returns:
            Dict mapping file paths to FileDependency objects
        """
        dependencies = {}

        # Step 1: Try to load from cache or analyze changed files
        files_to_analyze = []
        for filepath in self.changed_files:
            if not filepath.exists() or not filepath.suffix == '.py':
                continue

            # Try cache first
            cached_dep = self._load_cached_dependency(filepath)
            if cached_dep is not None:
                self.cache_hits += 1
                rel_path = str(filepath.relative_to(self.base_dir))
                dependencies[rel_path] = cached_dep
                # Still need to track imports for reverse dependencies
                self.imports[str(filepath)] = set(cached_dep.imports_from)
            else:
                self.cache_misses += 1
                files_to_analyze.append(filepath)

        # Step 2: Analyze files not in cache
        for filepath in files_to_analyze:
            try:
                self._analyze_file(filepath)
            except Exception as e:
                self.errors.append({
                    'file': str(filepath),
                    'error': str(e)
                })

        # Step 3: Analyze files that import changed files (reverse deps)
        self._find_reverse_dependencies()

        # Step 4: Build FileDependency objects for newly analyzed files
        for filepath in files_to_analyze:
            if filepath.exists() and filepath.suffix == '.py':
                dep = self._build_file_dependency(filepath)
                rel_path = str(filepath.relative_to(self.base_dir))
                dependencies[rel_path] = dep
                # Save to cache
                self._save_cached_dependency(filepath, dep)

        return dependencies

    def _analyze_file(self, filepath: Path):
        """
        Analyze a single Python file for dependencies

        Args:
            filepath: Absolute path to Python file
        """
        self.files_analyzed += 1

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
        except Exception:
            return  # Skip unreadable files

        try:
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError:
            # File has syntax errors, skip
            return

        # Extract imports
        imports = self._extract_imports(tree, filepath)
        self.imports[str(filepath)] = imports

        # Extract function calls
        func_calls = self._extract_function_calls(tree)
        self.function_calls[str(filepath)] = func_calls

    def _extract_imports(self, tree: ast.AST, filepath: Path) -> Set[str]:
        """
        Extract import statements from AST

        Args:
            tree: Parsed AST
            filepath: File being analyzed (for resolving relative imports)

        Returns:
            Set of imported module file paths
        """
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # import foo.bar -> foo/bar.py
                    module_path = self._resolve_module_path(alias.name, filepath)
                    if module_path:
                        imports.add(module_path)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # from foo.bar import baz -> foo/bar.py
                    module_path = self._resolve_module_path(node.module, filepath)
                    if module_path:
                        imports.add(module_path)

        return imports

    def _resolve_module_path(self, module_name: str, filepath: Path) -> Optional[str]:
        """
        Resolve module name to file path

        Args:
            module_name: Module name like 'foo.bar' or 'scripts.checkpoint'
            filepath: File doing the import (for relative resolution)

        Returns:
            Absolute file path string, or None if not found
        """
        # Convert module name to path: foo.bar -> foo/bar.py
        parts = module_name.split('.')

        # Try relative to base_dir
        candidate = self.base_dir / '/'.join(parts)

        # Check .py file
        if candidate.with_suffix('.py').exists():
            return str(candidate.with_suffix('.py'))

        # Check __init__.py in directory
        init_file = candidate / '__init__.py'
        if init_file.exists():
            return str(init_file)

        # Not found in project
        return None

    def _extract_function_calls(self, tree: ast.AST) -> Set[str]:
        """
        Extract function calls that might be cross-file

        Args:
            tree: Parsed AST

        Returns:
            Set of function call names (e.g., 'module.function')
        """
        func_calls = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Get function name
                func_name = self._get_call_name(node.func)
                if func_name and '.' in func_name:
                    # Cross-module call like 'module.function()'
                    func_calls.add(func_name)

        return func_calls

    def _get_call_name(self, node: ast.AST) -> Optional[str]:
        """
        Get the name of a function call

        Args:
            node: AST node (Name or Attribute)

        Returns:
            Function name string, or None
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # foo.bar() -> get 'foo.bar'
            value_name = self._get_call_name(node.value)
            if value_name:
                return f"{value_name}.{node.attr}"
            return node.attr
        return None

    def _find_reverse_dependencies(self):
        """
        Find reverse dependencies (who imports changed files)

        Scans project for files that import our changed files.
        Populates self.importers dict.
        """
        # Scan project for Python files
        python_files = list(self.base_dir.rglob('*.py'))

        # Limit scan to reasonable number
        if len(python_files) > 500:
            python_files = python_files[:500]

        for filepath in python_files:
            # Skip if already analyzed
            if str(filepath) in self.imports:
                continue

            # Quick scan for imports
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    source = f.read()

                tree = ast.parse(source)
                imports = self._extract_imports(tree, filepath)

                # Check if imports any changed files
                for imported_file in imports:
                    self.importers[imported_file].add(str(filepath))

            except Exception:
                # Skip files with errors
                continue

    def _build_file_dependency(self, filepath: Path) -> FileDependency:
        """
        Build FileDependency object for a file

        Args:
            filepath: Absolute path to file

        Returns:
            FileDependency with all dependency information
        """
        filepath_str = str(filepath)
        rel_path = str(filepath.relative_to(self.base_dir))

        # Get imports
        imports_from = [
            str(Path(imp).relative_to(self.base_dir))
            for imp in self.imports.get(filepath_str, set())
        ]

        # Get reverse dependencies
        used_by = [
            str(Path(imp).relative_to(self.base_dir))
            for imp in self.importers.get(filepath_str, set())
        ]
        used_by_count = len(used_by)

        # Get function calls
        func_calls = list(self.function_calls.get(filepath_str, set()))

        # Check if has tests
        has_tests = self._check_has_tests(filepath)

        # Calculate impact score
        impact_score = self._calculate_impact_score(
            used_by_count=used_by_count,
            has_tests=has_tests,
            imports_count=len(imports_from)
        )

        return FileDependency(
            file_path=rel_path,
            imports_from=imports_from[:10],  # Limit to 10
            used_by=used_by[:10],  # Limit to 10
            used_by_count=used_by_count,
            function_calls_to=func_calls[:10],  # Limit to 10
            has_tests=has_tests,
            impact_score=impact_score
        )

    def _check_has_tests(self, filepath: Path) -> bool:
        """
        Check if file has corresponding test file

        Args:
            filepath: File to check

        Returns:
            True if test file exists
        """
        # Common test patterns
        patterns = [
            f"test_{filepath.stem}.py",
            f"{filepath.stem}_test.py",
            f"tests/test_{filepath.stem}.py",
            f"test/test_{filepath.stem}.py",
        ]

        for pattern in patterns:
            test_file = filepath.parent / pattern
            if test_file.exists():
                return True

            # Check in tests directory at project root
            test_file = self.base_dir / 'tests' / f"test_{filepath.stem}.py"
            if test_file.exists():
                return True

        return False

    def _calculate_impact_score(self, used_by_count: int, has_tests: bool,
                                imports_count: int) -> int:
        """
        Calculate impact score (0-100) for a file

        Higher score = more critical file

        Args:
            used_by_count: Number of files importing this
            has_tests: Whether test file exists
            imports_count: Number of files this imports

        Returns:
            Impact score 0-100
        """
        score = 0

        # Base score from usage
        if used_by_count == 0:
            score = 10  # Leaf file, low impact
        elif used_by_count <= 2:
            score = 30
        elif used_by_count <= 5:
            score = 50
        elif used_by_count <= 10:
            score = 70
        else:
            score = 90  # High usage, high impact

        # Bonus for having tests (good practice, less risky)
        if has_tests:
            score = min(100, score + 10)

        # Penalty for many imports (complex, error-prone)
        if imports_count > 10:
            score = min(100, score + 5)

        return score


def get_dependencies_summary(dependencies: Dict[str, FileDependency]) -> Dict:
    """
    Generate summary statistics for dependencies

    Args:
        dependencies: Dict of file dependencies

    Returns:
        Summary dict with statistics
    """
    if not dependencies:
        return {
            'total_files': 0,
            'high_impact_count': 0,
            'files_with_tests': 0,
            'avg_impact_score': 0
        }

    high_impact = [d for d in dependencies.values() if d.impact_score >= 70]
    with_tests = [d for d in dependencies.values() if d.has_tests]
    avg_impact = sum(d.impact_score for d in dependencies.values()) / len(dependencies)

    return {
        'total_files': len(dependencies),
        'high_impact_count': len(high_impact),
        'files_with_tests': len(with_tests),
        'avg_impact_score': round(avg_impact, 1),
        'high_impact_files': [d.file_path for d in high_impact[:5]]
    }


# Utility function for converting to dict (for JSON serialization)
def dependencies_to_dict(dependencies: Dict[str, FileDependency]) -> Dict:
    """Convert FileDependency objects to dicts for JSON"""
    return {
        filepath: asdict(dep)
        for filepath, dep in dependencies.items()
    }
