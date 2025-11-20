#!/usr/bin/env python3
"""
Path Resolver - Handle path resolution across machines and projects

This module provides utilities for:
1. Resolving relative paths to absolute paths within a project
2. Normalizing paths for cross-machine compatibility
3. Validating path existence and accessibility
4. Converting between relative and absolute paths
"""

import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class PathResolver:
    """Resolve and normalize file paths for session checkpoints"""

    def __init__(self, project_root: Path):
        """
        Initialize path resolver for a project.

        Args:
            project_root: Absolute path to project root directory
        """
        self.project_root = Path(project_root).resolve()

    def resolve_file_path(self, file_path: str) -> Optional[Path]:
        """
        Resolve a file path from a checkpoint to an absolute path.

        Handles both relative and absolute paths, attempting to find
        the file within the project if possible.

        Args:
            file_path: File path from checkpoint (relative or absolute)

        Returns:
            Resolved absolute Path, or None if cannot resolve
        """
        file_path_obj = Path(file_path)

        # If already absolute and exists, use it
        if file_path_obj.is_absolute():
            if file_path_obj.exists():
                return file_path_obj
            else:
                # Absolute path but doesn't exist, try to find in project
                # Extract the relative part and look for it
                pass

        # Try as relative to project root
        resolved = self.project_root / file_path
        if resolved.exists():
            return resolved.resolve()

        # Try as-is (for absolute paths that exist)
        if file_path_obj.exists():
            return file_path_obj.resolve()

        return None

    def make_relative(self, file_path: Path) -> str:
        """
        Convert absolute file path to relative path from project root.

        Args:
            file_path: Absolute file path

        Returns:
            Relative path string, or original if cannot make relative
        """
        try:
            file_path = Path(file_path).resolve()
            return str(file_path.relative_to(self.project_root))
        except ValueError:
            # Not under project root, return as-is
            return str(file_path)

    def validate_file_changes(self, file_changes: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Validate file changes from a checkpoint, resolving paths.

        Args:
            file_changes: List of file change dicts from checkpoint

        Returns:
            Tuple of (validated_changes, errors)
            - validated_changes: List with resolved absolute_path added
            - errors: List of error messages for unresolved files
        """
        validated = []
        errors = []

        for change in file_changes:
            file_path = change.get('file_path')
            if not file_path:
                errors.append("File change missing file_path")
                continue

            resolved = self.resolve_file_path(file_path)

            if resolved:
                # Add resolved absolute path to change dict
                validated_change = change.copy()
                validated_change['absolute_path'] = str(resolved)
                validated_change['exists'] = resolved.exists()
                validated.append(validated_change)
            else:
                # File not found, but still include with warning
                validated_change = change.copy()
                validated_change['absolute_path'] = None
                validated_change['exists'] = False
                validated.append(validated_change)
                errors.append(f"Cannot resolve path: {file_path}")

        return validated, errors

    def normalize_path(self, file_path: str) -> str:
        """
        Normalize a file path for cross-platform compatibility.

        Args:
            file_path: Path to normalize

        Returns:
            Normalized path string (forward slashes, no trailing slash)
        """
        # Convert to Path and back to string to normalize
        normalized = Path(file_path).as_posix()

        # Remove trailing slash
        if normalized.endswith('/'):
            normalized = normalized[:-1]

        return normalized

    def find_project_root(self, start_path: Optional[Path] = None) -> Optional[Path]:
        """
        Find project root by looking for .git directory.

        Args:
            start_path: Starting directory (defaults to current working dir)

        Returns:
            Project root Path, or None if not found
        """
        if start_path is None:
            start_path = Path.cwd()

        current = Path(start_path).resolve()

        # Walk up directory tree
        while current != current.parent:
            if (current / '.git').is_dir():
                return current
            current = current.parent

        return None

    def get_file_list(self, file_changes: List[Dict]) -> List[str]:
        """
        Extract list of file paths from file changes.

        Args:
            file_changes: List of file change dicts

        Returns:
            List of file paths (relative)
        """
        return [change['file_path'] for change in file_changes if change.get('file_path')]


def resolve_checkpoint_paths(checkpoint: Dict, project_root: Optional[Path] = None) -> Dict:
    """
    Resolve all file paths in a checkpoint.

    Args:
        checkpoint: Checkpoint data dict
        project_root: Project root path (if None, infers from checkpoint)

    Returns:
        Checkpoint dict with resolved paths added
    """
    # Infer project root from checkpoint if not provided
    if project_root is None:
        project_metadata = checkpoint.get('project')
        if project_metadata and project_metadata.get('absolute_path'):
            project_root = Path(project_metadata['absolute_path'])
        else:
            # Cannot resolve without project root
            return checkpoint

    resolver = PathResolver(project_root)

    # Validate and resolve file changes
    file_changes = checkpoint.get('file_changes', [])
    validated_changes, errors = resolver.validate_file_changes(file_changes)

    # Create enhanced checkpoint
    enhanced_checkpoint = checkpoint.copy()
    enhanced_checkpoint['file_changes'] = validated_changes

    if errors:
        enhanced_checkpoint['_path_resolution_errors'] = errors

    return enhanced_checkpoint


def make_checkpoint_portable(checkpoint: Dict, project_root: Path) -> Dict:
    """
    Ensure all paths in checkpoint are relative for portability.

    Args:
        checkpoint: Checkpoint data dict
        project_root: Project root path

    Returns:
        Checkpoint dict with relative paths
    """
    resolver = PathResolver(project_root)

    # Normalize file change paths
    file_changes = checkpoint.get('file_changes', [])
    portable_changes = []

    for change in file_changes:
        file_path = change.get('file_path')
        if file_path:
            # Ensure path is relative
            portable_change = change.copy()
            portable_change['file_path'] = resolver.normalize_path(
                resolver.make_relative(Path(file_path))
            )
            portable_changes.append(portable_change)

    enhanced_checkpoint = checkpoint.copy()
    enhanced_checkpoint['file_changes'] = portable_changes

    return enhanced_checkpoint


if __name__ == "__main__":
    # Simple CLI for testing
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python path_resolver.py <checkpoint-file>")
        sys.exit(1)

    checkpoint_file = Path(sys.argv[1])

    if not checkpoint_file.exists():
        print(f"Checkpoint file not found: {checkpoint_file}")
        sys.exit(1)

    with open(checkpoint_file, 'r', encoding='utf-8') as f:
        checkpoint = json.load(f)

    # Resolve paths
    resolved = resolve_checkpoint_paths(checkpoint)

    # Display results
    print(f"\n{'='*70}")
    print(f"PATH RESOLUTION RESULTS")
    print(f"{'='*70}")

    file_changes = resolved.get('file_changes', [])
    resolved_count = sum(1 for fc in file_changes if fc.get('exists'))
    unresolved_count = len(file_changes) - resolved_count

    print(f"Total files: {len(file_changes)}")
    print(f"Resolved: {resolved_count}")
    print(f"Unresolved: {unresolved_count}")

    errors = resolved.get('_path_resolution_errors', [])
    if errors:
        print(f"\nErrors:")
        for error in errors[:5]:
            print(f"  • {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")

    print(f"{'='*70}")
