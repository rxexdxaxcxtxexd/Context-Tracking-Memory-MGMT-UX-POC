#!/usr/bin/env python3
"""
Unit tests for dependency_analyzer.py

Tests the core functionality of cross-file dependency tracking including:
- Import extraction
- Reverse dependency mapping
- Impact scoring
- Caching mechanisms
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from dependency_analyzer import DependencyAnalyzer, FileDependency


class TestDependencyAnalyzer(unittest.TestCase):
    """Test cases for DependencyAnalyzer class"""

    def setUp(self):
        """Create temporary test directory"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.cache_dir = self.test_dir / ".claude-sessions" / "dependency_cache"

    def tearDown(self):
        """Clean up temporary test directory"""
        shutil.rmtree(self.test_dir)

    def create_test_file(self, rel_path: str, content: str):
        """Helper to create test Python file"""
        filepath = self.test_dir / rel_path
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding='utf-8')
        return filepath

    def test_basic_import_detection(self):
        """Test that basic imports are detected correctly"""
        # Create test files
        self.create_test_file('foo.py', 'def hello(): pass')
        self.create_test_file('bar.py', '''
import foo
def world():
    foo.hello()
''')

        analyzer = DependencyAnalyzer(
            base_dir=self.test_dir,
            changed_files=['bar.py'],
            use_cache=False
        )
        dependencies = analyzer.analyze_dependencies()

        self.assertIn('bar.py', dependencies)
        dep = dependencies['bar.py']
        self.assertEqual(len(dep.imports_from), 1)
        self.assertIn('foo.py', dep.imports_from)

    def test_impact_scoring(self):
        """Test impact score calculation"""
        # Create files with different usage patterns
        self.create_test_file('util.py', 'def helper(): pass')

        # Create multiple files that import util
        for i in range(5):
            self.create_test_file(f'user{i}.py', 'import util')

        analyzer = DependencyAnalyzer(
            base_dir=self.test_dir,
            changed_files=['util.py'],
            use_cache=False
        )
        dependencies = analyzer.analyze_dependencies()

        dep = dependencies['util.py']
        # Used by 5 files should have impact score in range 50-70
        self.assertGreaterEqual(dep.impact_score, 50)
        self.assertLessEqual(dep.impact_score, 70)

    def test_cache_functionality(self):
        """Test that caching works correctly"""
        self.create_test_file('cached.py', 'def test(): pass')

        # First analysis - cache miss
        analyzer1 = DependencyAnalyzer(
            base_dir=self.test_dir,
            changed_files=['cached.py'],
            use_cache=True
        )
        dependencies1 = analyzer1.analyze_dependencies()
        self.assertEqual(analyzer1.cache_misses, 1)
        self.assertEqual(analyzer1.cache_hits, 0)

        # Second analysis - cache hit
        analyzer2 = DependencyAnalyzer(
            base_dir=self.test_dir,
            changed_files=['cached.py'],
            use_cache=True
        )
        dependencies2 = analyzer2.analyze_dependencies()
        self.assertEqual(analyzer2.cache_hits, 1)
        self.assertEqual(analyzer2.cache_misses, 0)

        # Verify same results
        self.assertEqual(dependencies1['cached.py'].file_path,
                        dependencies2['cached.py'].file_path)

    def test_cache_invalidation_on_file_change(self):
        """Test that cache is invalidated when file changes"""
        filepath = self.create_test_file('modified.py', 'def v1(): pass')

        # First analysis
        analyzer1 = DependencyAnalyzer(
            base_dir=self.test_dir,
            changed_files=['modified.py'],
            use_cache=True
        )
        analyzer1.analyze_dependencies()
        self.assertEqual(analyzer1.cache_misses, 1)

        # Modify file
        import time
        time.sleep(0.1)  # Ensure mtime changes
        filepath.write_text('def v2(): pass', encoding='utf-8')

        # Second analysis - should be cache miss
        analyzer2 = DependencyAnalyzer(
            base_dir=self.test_dir,
            changed_files=['modified.py'],
            use_cache=True
        )
        analyzer2.analyze_dependencies()
        self.assertEqual(analyzer2.cache_misses, 1)

    def test_test_file_detection(self):
        """Test that test file detection works"""
        self.create_test_file('module.py', 'def function(): pass')
        self.create_test_file('test_module.py', 'import module')

        analyzer = DependencyAnalyzer(
            base_dir=self.test_dir,
            changed_files=['module.py'],
            use_cache=False
        )
        dependencies = analyzer.analyze_dependencies()

        dep = dependencies['module.py']
        self.assertTrue(dep.has_tests)

    def test_no_test_file(self):
        """Test files without tests are marked correctly"""
        self.create_test_file('no_tests.py', 'def function(): pass')

        analyzer = DependencyAnalyzer(
            base_dir=self.test_dir,
            changed_files=['no_tests.py'],
            use_cache=False
        )
        dependencies = analyzer.analyze_dependencies()

        dep = dependencies['no_tests.py']
        self.assertFalse(dep.has_tests)

    def test_empty_dependencies(self):
        """Test file with no imports"""
        self.create_test_file('isolated.py', '''
def standalone():
    return 42
''')

        analyzer = DependencyAnalyzer(
            base_dir=self.test_dir,
            changed_files=['isolated.py'],
            use_cache=False
        )
        dependencies = analyzer.analyze_dependencies()

        dep = dependencies['isolated.py']
        self.assertEqual(len(dep.imports_from), 0)
        self.assertEqual(dep.used_by_count, 0)
        # Isolated file should have low impact score
        self.assertEqual(dep.impact_score, 10)

    def test_syntax_error_handling(self):
        """Test that syntax errors are handled gracefully"""
        self.create_test_file('broken.py', '''
def broken(
    # Missing closing parenthesis
''')

        analyzer = DependencyAnalyzer(
            base_dir=self.test_dir,
            changed_files=['broken.py'],
            use_cache=False
        )
        # Should not raise exception
        dependencies = analyzer.analyze_dependencies()

        # File should still be analyzed (even if syntax error)
        self.assertIn('broken.py', dependencies)

    def test_skip_cache(self):
        """Test that use_cache=False disables caching"""
        self.create_test_file('nocache.py', 'def test(): pass')

        # First run with cache disabled
        analyzer1 = DependencyAnalyzer(
            base_dir=self.test_dir,
            changed_files=['nocache.py'],
            use_cache=False
        )
        analyzer1.analyze_dependencies()

        # Second run - should still be miss because cache disabled
        analyzer2 = DependencyAnalyzer(
            base_dir=self.test_dir,
            changed_files=['nocache.py'],
            use_cache=False
        )
        analyzer2.analyze_dependencies()

        # Both should be misses
        self.assertEqual(analyzer2.cache_hits, 0)


class TestFileDependency(unittest.TestCase):
    """Test cases for FileDependency dataclass"""

    def test_file_dependency_creation(self):
        """Test creating FileDependency object"""
        dep = FileDependency(
            file_path='test.py',
            imports_from=['foo.py', 'bar.py'],
            used_by=['baz.py'],
            used_by_count=1,
            function_calls_to=['foo.func'],
            has_tests=True,
            impact_score=50
        )

        self.assertEqual(dep.file_path, 'test.py')
        self.assertEqual(len(dep.imports_from), 2)
        self.assertEqual(dep.used_by_count, 1)
        self.assertTrue(dep.has_tests)
        self.assertEqual(dep.impact_score, 50)


def run_tests():
    """Run all tests"""
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
