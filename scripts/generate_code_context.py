#!/usr/bin/env python3
"""
Code Context Generator - Creates .claude-code-context.md from git commits

This script generates a technical context file that supplements claude-mem with:
- Git commit metadata (hash, branch, message, remote)
- Changed files with actions (created, modified, deleted)
- High-impact file warnings (from dependency analysis)
- Import dependencies and reverse dependencies
- Test recommendations based on missing test files

Usage:
    python generate_code_context.py <commit_hash> [--changed-files file1 file2 ...]
    python generate_code_context.py HEAD
    python generate_code_context.py --auto  # Auto-detect from git log

Output:
    .claude-code-context.md - Markdown file with technical context
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import argparse

# Import dependency analyzer
sys.path.insert(0, str(Path(__file__).parent))
from dependency_analyzer import DependencyAnalyzer, FileDependency, get_dependencies_summary


class CodeContextGenerator:
    """Generates .claude-code-context.md from git commits and dependency analysis"""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.context_file = self.base_dir / '.claude-code-context.md'

    def generate_context(self, commit_hash: str = 'HEAD', changed_files: Optional[List[str]] = None):
        """Generate code context file

        Args:
            commit_hash: Git commit hash to analyze (default: HEAD)
            changed_files: Optional list of changed files (auto-detected if None)
        """
        print(f"Generating code context for commit: {commit_hash}")

        # Get git metadata
        git_info = self._get_git_info(commit_hash)
        if not git_info:
            print("ERROR: Could not retrieve git information")
            return False

        # Get changed files if not provided
        if changed_files is None:
            changed_files = self._get_changed_files(commit_hash)

        if not changed_files:
            print("No changed files detected, skipping context generation")
            return False

        print(f"  Detected {len(changed_files)} changed files")

        # Filter Python files for dependency analysis
        python_files = [f for f in changed_files if f.endswith('.py')]

        # Run dependency analysis on Python files only
        dependencies = {}
        high_impact_files = []

        if python_files:
            print(f"  Analyzing dependencies for {len(python_files)} Python files...")
            try:
                analyzer = DependencyAnalyzer(
                    base_dir=self.base_dir,
                    changed_files=python_files,
                    use_cache=True
                )
                dependencies = analyzer.analyze_dependencies()

                # Extract high-impact files (score >= 70)
                high_impact_files = [
                    dep for dep in dependencies.values()
                    if dep.impact_score >= 70
                ]

                print(f"    Found {len(high_impact_files)} high-impact file(s)")
            except Exception as e:
                print(f"  Warning: Dependency analysis failed: {e}")
                dependencies = {}

        # Generate markdown
        markdown = self._generate_markdown(
            git_info=git_info,
            changed_files=changed_files,
            dependencies=dependencies,
            high_impact_files=high_impact_files
        )

        # Write to file
        try:
            with open(self.context_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"[OK] Code context written to: {self.context_file}")
            return True
        except Exception as e:
            print(f"ERROR: Could not write context file: {e}")
            return False

    def _get_git_info(self, commit_hash: str) -> Optional[Dict[str, str]]:
        """Get git metadata for commit"""
        try:
            # Get commit hash
            hash_result = subprocess.run(
                ['git', 'rev-parse', commit_hash],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if hash_result.returncode != 0:
                return None

            commit_hash_full = hash_result.stdout.strip()

            # Get branch
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            branch = branch_result.stdout.strip() or 'detached HEAD'

            # Get remote URL
            remote_result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            remote_url = remote_result.stdout.strip() if remote_result.returncode == 0 else 'unknown'

            # Get commit message
            message_result = subprocess.run(
                ['git', 'log', '--format=%s', '-n', '1', commit_hash],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            message = message_result.stdout.strip()

            # Get commit date
            date_result = subprocess.run(
                ['git', 'log', '--format=%cI', '-n', '1', commit_hash],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            date = date_result.stdout.strip()

            return {
                'hash': commit_hash_full[:8],
                'hash_full': commit_hash_full,
                'branch': branch,
                'remote': remote_url,
                'message': message,
                'date': date
            }
        except Exception as e:
            print(f"Error getting git info: {e}")
            return None

    def _get_changed_files(self, commit_hash: str) -> List[str]:
        """Get list of changed files in commit"""
        try:
            # Get files changed in commit
            result = subprocess.run(
                ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
                return files
            return []
        except Exception as e:
            print(f"Error getting changed files: {e}")
            return []

    def _generate_markdown(self, git_info: Dict[str, str], changed_files: List[str],
                          dependencies: Dict[str, FileDependency],
                          high_impact_files: List[FileDependency]) -> str:
        """Generate markdown content for code context file"""

        lines = []

        # Header
        lines.append("# Code Context (Auto-generated)")
        lines.append("")
        lines.append(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Last Commit section
        lines.append("## Last Commit")
        lines.append("")
        lines.append(f"- **Hash:** `{git_info['hash']}`")
        lines.append(f"- **Branch:** `{git_info['branch']}`")
        lines.append(f"- **Remote:** {git_info['remote']}")
        lines.append(f"- **Date:** {git_info['date']}")
        lines.append(f"- **Message:** {git_info['message']}")
        lines.append("")

        # Changed Files section
        lines.append(f"## Changed Files ({len(changed_files)})")
        lines.append("")

        if len(changed_files) <= 20:
            # Show all files if <= 20
            for file_path in changed_files:
                # Detect action from file status (simplified)
                if file_path in dependencies:
                    icon = "[M]"  # Modified (has dependency info = existed before)
                else:
                    icon = "[+]"  # Assume created if no prior dependency

                lines.append(f"- {icon} `{file_path}`")
        else:
            # Summarize if > 20 files
            lines.append(f"**Total:** {len(changed_files)} files changed")
            lines.append("")

            # Group by extension
            by_ext = {}
            for file_path in changed_files:
                ext = Path(file_path).suffix or 'no extension'
                by_ext[ext] = by_ext.get(ext, 0) + 1

            lines.append("**By file type:**")
            for ext, count in sorted(by_ext.items(), key=lambda x: -x[1]):
                lines.append(f"- {ext}: {count} file(s)")

            lines.append("")
            lines.append("**Sample files:**")
            for file_path in changed_files[:10]:
                lines.append(f"- `{file_path}`")
            if len(changed_files) > 10:
                lines.append(f"- ... and {len(changed_files) - 10} more")

        lines.append("")

        # High-Impact Changes section
        if high_impact_files:
            lines.append("## High-Impact Changes")
            lines.append("")
            lines.append("[!] **The following files are used by multiple files. Test thoroughly!**")
            lines.append("")

            for dep in high_impact_files[:5]:  # Top 5
                lines.append(f"### `{dep.file_path}` (Impact: {dep.impact_score}/100)")
                lines.append(f"- **Used by:** {dep.used_by_count} file(s)")

                if dep.used_by:
                    lines.append(f"- **Importers:** {', '.join(f'`{f}`' for f in dep.used_by[:3])}")
                    if len(dep.used_by) > 3:
                        lines.append(f"  ... and {len(dep.used_by) - 3} more")

                if not dep.has_tests:
                    test_file = f"test_{Path(dep.file_path).stem}.py"
                    lines.append(f"- [!] **No test file found!** Consider creating `{test_file}`")

                lines.append("")

        # Dependencies section (for Python files)
        python_deps = {k: v for k, v in dependencies.items() if k.endswith('.py')}
        if python_deps:
            lines.append("## Dependencies")
            lines.append("")

            for file_path, dep in list(python_deps.items())[:10]:  # Top 10
                if dep.imports_from or dep.used_by:
                    lines.append(f"### `{file_path}`")

                    if dep.imports_from:
                        lines.append(f"**Imports:** {', '.join(f'`{f}`' for f in dep.imports_from[:5])}")
                        if len(dep.imports_from) > 5:
                            lines.append(f"... and {len(dep.imports_from) - 5} more")

                    if dep.used_by:
                        lines.append(f"**Used by:** {', '.join(f'`{f}`' for f in dep.used_by[:3])}")
                        if len(dep.used_by) > 3:
                            lines.append(f"... and {len(dep.used_by) - 3} more")

                    lines.append("")

        # Test Recommendations section
        missing_tests = [dep for dep in dependencies.values() if not dep.has_tests and dep.impact_score >= 50]
        if missing_tests:
            lines.append("## Test Recommendations")
            lines.append("")
            lines.append("The following files lack test coverage and should be prioritized:")
            lines.append("")

            for dep in missing_tests[:10]:
                test_file = f"test_{Path(dep.file_path).stem}.py"
                lines.append(f"- `{dep.file_path}` (Impact: {dep.impact_score}/100)")
                lines.append(f"  → Create: `{test_file}`")

            lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*This file is auto-generated by `scripts/generate_code_context.py`.*")
        lines.append("*Do not edit manually - changes will be overwritten on next commit.*")
        lines.append("")

        return '\n'.join(lines)


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description="Generate .claude-code-context.md from git commits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_code_context.py HEAD
      Generate context for HEAD commit

  python generate_code_context.py abc1234
      Generate context for specific commit

  python generate_code_context.py --auto
      Auto-detect latest commit and generate context
        """
    )

    parser.add_argument(
        'commit',
        nargs='?',
        default='HEAD',
        help='Git commit hash (default: HEAD)'
    )

    parser.add_argument(
        '--changed-files',
        nargs='+',
        help='Manually specify changed files (bypasses git detection)'
    )

    parser.add_argument(
        '--auto',
        action='store_true',
        help='Auto-detect latest commit'
    )

    parser.add_argument(
        '--base-dir',
        type=str,
        default='.',
        help='Base directory of git repository (default: current directory)'
    )

    args = parser.parse_args()

    # Determine base directory
    base_dir = Path(args.base_dir).resolve()

    if not (base_dir / '.git').exists():
        print(f"ERROR: Not a git repository: {base_dir}")
        return 1

    # Create generator
    generator = CodeContextGenerator(base_dir)

    # Generate context
    try:
        success = generator.generate_context(
            commit_hash=args.commit,
            changed_files=args.changed_files
        )
        return 0 if success else 1
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
