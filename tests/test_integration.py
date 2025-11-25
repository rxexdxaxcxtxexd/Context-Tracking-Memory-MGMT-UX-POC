#!/usr/bin/env python3
"""
Integration tests for cross-file dependency tracking

Tests the complete end-to-end flow:
1. Create checkpoint with dependencies
2. Load checkpoint and verify dependencies
3. Resume session and verify display
"""

import unittest
import tempfile
import shutil
import json
import subprocess
import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestDependencyIntegration(unittest.TestCase):
    """Integration tests for dependency tracking"""

    def setUp(self):
        """Create temporary test project"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.scripts_dir = Path(__file__).parent.parent / 'scripts'

    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)

    def create_test_file(self, rel_path: str, content: str):
        """Helper to create test file"""
        filepath = self.test_dir / rel_path
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding='utf-8')
        return filepath

    def test_checkpoint_with_dependencies(self):
        """Test creating checkpoint with dependency analysis"""
        # Create test Python files
        self.create_test_file('main.py', '''
import utils
import database

def main():
    utils.helper()
    database.connect()
''')
        self.create_test_file('utils.py', 'def helper(): pass')
        self.create_test_file('database.py', 'def connect(): pass')

        # Create checkpoint with dependencies
        result = subprocess.run(
            [
                sys.executable,
                str(self.scripts_dir / 'save-session.py'),
                '--dry-run',
                '--quick',
                '--description', 'Integration test'
            ],
            cwd=self.test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn('Analyzing dependencies', result.stdout)

    def test_skip_dependencies_flag(self):
        """Test --skip-dependencies flag works"""
        self.create_test_file('test.py', 'def test(): pass')

        result = subprocess.run(
            [
                sys.executable,
                str(self.scripts_dir / 'save-session.py'),
                '--dry-run',
                '--quick',
                '--skip-dependencies'
            ],
            cwd=self.test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn('Skipping dependency analysis', result.stdout)
        self.assertNotIn('Analyzing dependencies', result.stdout)

    def test_cache_performance(self):
        """Test that cache improves performance on second run"""
        self.create_test_file('app.py', 'def app(): pass')

        # First run - builds cache
        result1 = subprocess.run(
            [
                sys.executable,
                str(self.scripts_dir / 'save-session.py'),
                '--dry-run',
                '--quick'
            ],
            cwd=self.test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertIn('Cache:', result1.stdout)
        self.assertIn('misses', result1.stdout)

        # Second run - uses cache
        result2 = subprocess.run(
            [
                sys.executable,
                str(self.scripts_dir / 'save-session.py'),
                '--dry-run',
                '--quick'
            ],
            cwd=self.test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertIn('Cache:', result2.stdout)
        self.assertIn('hits', result2.stdout)

    def test_dependency_validation(self):
        """Test that checkpoint schema validates dependencies"""
        from checkpoint_schema import validate_checkpoint

        checkpoint = {
            'session_id': 'test123',
            'timestamp': '2025-11-14T00:00:00',
            'description': 'Test',
            'file_changes': [],
            'completed_tasks': [],
            'pending_tasks': [],
            'next_steps': [],
            'resume_points': [],
            'dependencies': {
                'test.py': {
                    'file_path': 'test.py',
                    'imports_from': [],
                    'used_by': [],
                    'used_by_count': 0,
                    'function_calls_to': [],
                    'has_tests': False,
                    'impact_score': 10
                }
            }
        }

        is_valid, errors = validate_checkpoint(checkpoint)
        self.assertTrue(is_valid, f"Validation failed: {errors}")

    def test_invalid_dependency_structure(self):
        """Test that invalid dependency structure fails validation"""
        from checkpoint_schema import validate_checkpoint

        checkpoint = {
            'session_id': 'test123',
            'timestamp': '2025-11-14T00:00:00',
            'description': 'Test',
            'file_changes': [],
            'completed_tasks': [],
            'pending_tasks': [],
            'next_steps': [],
            'resume_points': [],
            'dependencies': {
                'test.py': {
                    'file_path': 'test.py',
                    # Missing required fields
                    'impact_score': 999  # Invalid range
                }
            }
        }

        is_valid, errors = validate_checkpoint(checkpoint)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


def run_tests():
    """Run all integration tests"""
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
