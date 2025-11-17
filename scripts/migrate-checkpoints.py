#!/usr/bin/env python3
"""
Checkpoint Migration Script - Add project metadata to old checkpoints

This script:
1. Scans all existing checkpoints
2. Identifies checkpoints without project metadata
3. Attempts to infer project information from checkpoint content
4. Updates checkpoints with project metadata
5. Registers updated checkpoints in session index
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import importlib.util

# Import session index
spec_index = importlib.util.spec_from_file_location("session_index",
    os.path.join(os.path.dirname(__file__), "session_index.py"))
session_index = importlib.util.module_from_spec(spec_index)
spec_index.loader.exec_module(session_index)
SessionIndex = session_index.SessionIndex


class CheckpointMigrator:
    """Migrate old checkpoints to include project metadata"""

    def __init__(self, checkpoints_dir: Optional[Path] = None):
        """Initialize the migrator"""
        if checkpoints_dir is None:
            checkpoints_dir = Path.home() / ".claude-sessions" / "checkpoints"

        self.checkpoints_dir = Path(checkpoints_dir)
        self.migrated_count = 0
        self.skipped_count = 0
        self.failed_count = 0
        self.errors: List[str] = []

    def _get_git_info(self, project_path: Path) -> Optional[Dict[str, str]]:
        """
        Get git information for a project directory.

        Args:
            project_path: Path to project directory

        Returns:
            Dict with remote_url, branch, head_hash, or None if not a git repo
        """
        try:
            # Check if it's a git repo
            result = subprocess.run(
                ['git', 'rev-parse', '--is-inside-work-tree'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return None

            git_info = {}

            # Get remote URL
            remote_result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if remote_result.returncode == 0:
                git_info['remote_url'] = remote_result.stdout.strip()

            # Get current branch
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if branch_result.returncode == 0:
                git_info['branch'] = branch_result.stdout.strip()

            # Get HEAD hash
            hash_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if hash_result.returncode == 0:
                git_info['head_hash'] = hash_result.stdout.strip()

            return git_info if git_info else None

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None

    def _infer_project_from_checkpoint(self, checkpoint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Attempt to infer project metadata from checkpoint content.

        Strategy:
        1. Check file_changes for common project path
        2. Use git_remote_url if present in checkpoint
        3. Fall back to context hints

        Args:
            checkpoint: Checkpoint data dict

        Returns:
            Inferred project metadata dict, or None if cannot infer
        """
        # Strategy 1: Extract common path from file changes
        file_changes = checkpoint.get('file_changes', [])
        if file_changes:
            # Get all file paths
            paths = [Path(fc['file_path']) for fc in file_changes if fc.get('file_path')]

            if paths:
                # Find common ancestor directory
                try:
                    # Convert to absolute paths and find common parent
                    abs_paths = [p.resolve() for p in paths if p.exists()]
                    if abs_paths:
                        # Find common parent directory
                        common_parent = abs_paths[0].parent
                        for p in abs_paths[1:]:
                            # Walk up until we find common ancestor
                            while not str(p).startswith(str(common_parent)):
                                common_parent = common_parent.parent
                                if common_parent == common_parent.parent:
                                    # Reached root, can't find common parent
                                    break

                        # Verify it's a reasonable project directory (not home or root)
                        if common_parent != Path.home() and common_parent != common_parent.parent:
                            project_metadata = {
                                'absolute_path': str(common_parent),
                                'name': common_parent.name
                            }

                            # Try to get git info for this directory
                            git_info = self._get_git_info(common_parent)
                            if git_info:
                                project_metadata['git_remote_url'] = git_info.get('remote_url')
                                project_metadata['git_branch'] = git_info.get('branch')
                                project_metadata['git_head_hash'] = git_info.get('head_hash')

                            return project_metadata
                except Exception:
                    pass

        # Strategy 2: Use existing git info in checkpoint (legacy format)
        if checkpoint.get('git_remote_url'):
            # We have git info but no project field
            # Try to find the project directory by scanning common locations
            return None  # Can't reliably infer path from just remote URL

        # Strategy 3: Check context for hints
        context = checkpoint.get('context', {})
        if context.get('project'):
            # Context has project name hint, but need full metadata
            return None

        return None

    def _migrate_checkpoint(self, checkpoint_file: Path, dry_run: bool = False) -> bool:
        """
        Migrate a single checkpoint file.

        Args:
            checkpoint_file: Path to checkpoint JSON file
            dry_run: If True, don't write changes

        Returns:
            True if migrated, False if skipped or failed
        """
        try:
            # Load checkpoint
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)

            # Check if already has project metadata
            if checkpoint.get('project'):
                print(f"  ✓ Skipping {checkpoint_file.name} (already has project metadata)")
                self.skipped_count += 1
                return False

            # Attempt to infer project metadata
            project_metadata = self._infer_project_from_checkpoint(checkpoint)

            if not project_metadata:
                print(f"  ⚠ Cannot infer project for {checkpoint_file.name}")
                self.failed_count += 1
                self.errors.append(f"{checkpoint_file.name}: Cannot infer project metadata")
                return False

            # Add project metadata to checkpoint
            checkpoint['project'] = project_metadata

            if not dry_run:
                # Write updated checkpoint
                with open(checkpoint_file, 'w', encoding='utf-8') as f:
                    json.dump(checkpoint, f, indent=2, ensure_ascii=False)

                # Register in session index
                try:
                    index = SessionIndex()
                    index.register_checkpoint(str(checkpoint_file), checkpoint)
                except Exception as e:
                    print(f"    Warning: Could not register in index: {e}")

            print(f"  ✓ Migrated {checkpoint_file.name}")
            print(f"    Project: {project_metadata['name']}")
            print(f"    Path: {project_metadata['absolute_path']}")
            self.migrated_count += 1
            return True

        except Exception as e:
            print(f"  ✗ Failed to migrate {checkpoint_file.name}: {e}")
            self.failed_count += 1
            self.errors.append(f"{checkpoint_file.name}: {str(e)}")
            return False

    def migrate_all(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Migrate all checkpoints in the checkpoints directory.

        Args:
            dry_run: If True, don't write changes (preview mode)

        Returns:
            Dict with migration statistics
        """
        if not self.checkpoints_dir.exists():
            print(f"Checkpoints directory does not exist: {self.checkpoints_dir}")
            return {'migrated': 0, 'skipped': 0, 'failed': 0}

        checkpoint_files = sorted(self.checkpoints_dir.glob("checkpoint-*.json"))

        if not checkpoint_files:
            print("No checkpoint files found.")
            return {'migrated': 0, 'skipped': 0, 'failed': 0}

        print("\n" + "="*70)
        print("CHECKPOINT MIGRATION")
        print("="*70)
        print(f"Found {len(checkpoint_files)} checkpoint file(s)")
        if dry_run:
            print("DRY RUN MODE - No changes will be written")
        print()

        for checkpoint_file in checkpoint_files:
            self._migrate_checkpoint(checkpoint_file, dry_run=dry_run)

        print("\n" + "="*70)
        print("MIGRATION SUMMARY")
        print("="*70)
        print(f"Migrated: {self.migrated_count}")
        print(f"Skipped:  {self.skipped_count} (already have project metadata)")
        print(f"Failed:   {self.failed_count}")

        if self.errors:
            print("\nErrors encountered:")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  • {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")

        print("="*70)

        return {
            'migrated': self.migrated_count,
            'skipped': self.skipped_count,
            'failed': self.failed_count
        }


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate old checkpoints to include project metadata"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Preview changes without writing (dry run mode)"
    )
    parser.add_argument(
        '--checkpoints-dir',
        type=str,
        default=None,
        help="Path to checkpoints directory (default: ~/.claude-sessions/checkpoints)"
    )

    args = parser.parse_args()

    # Determine checkpoints directory
    if args.checkpoints_dir:
        checkpoints_dir = Path(args.checkpoints_dir)
    else:
        checkpoints_dir = Path.home() / ".claude-sessions" / "checkpoints"

    # Run migration
    migrator = CheckpointMigrator(checkpoints_dir)
    stats = migrator.migrate_all(dry_run=args.dry_run)

    # Exit with appropriate code
    if stats['failed'] > 0:
        sys.exit(1)  # Errors occurred
    elif stats['migrated'] == 0 and stats['skipped'] == 0:
        sys.exit(2)  # No checkpoints found
    else:
        sys.exit(0)  # Success


if __name__ == "__main__":
    main()
