#!/usr/bin/env python3
"""
Checkpoint Migration to Markdown Summaries

This script migrates historical checkpoint files into organized markdown summaries
that can be referenced in future sessions. Since claude-mem captures observations
naturally during conversations (no public API for direct insertion), this approach
creates accessible historical context.

Strategy:
1. Analyze last 90 days of checkpoints
2. Identify high-value older checkpoints (significant changes, decisions logged)
3. Generate markdown summaries organized by project and date range
4. Store in .claude/historical-context/ for easy reference

Usage:
    python migrate_checkpoints_to_summaries.py                # Full migration
    python migrate_checkpoints_to_summaries.py --days 90      # Last 90 days only
    python migrate_checkpoints_to_summaries.py --dry-run      # Preview only
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


class CheckpointMigrator:
    """Migrate checkpoint files to markdown summaries"""

    def __init__(self, checkpoints_dir: Path, output_dir: Path):
        self.checkpoints_dir = checkpoints_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_checkpoint(self, checkpoint_file: Path) -> Optional[Dict]:
        """Load a checkpoint JSON file"""
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Failed to load {checkpoint_file.name}: {e}")
            return None

    def is_high_value(self, checkpoint: Dict) -> bool:
        """Determine if checkpoint is high-value"""
        # High-value criteria:
        # 1. Has decisions logged (architectural/implementation decisions)
        # 2. Has many file changes (>= 10)
        # 3. Has detailed manual description (not auto-generated)
        # 4. Has problems/solutions documented

        decisions = len(checkpoint.get('decisions', []))
        file_changes = len(checkpoint.get('file_changes', []))
        problems = len(checkpoint.get('problems_encountered', []))
        description = checkpoint.get('context', {}).get('description', '')

        # High-value if any of:
        if decisions >= 1:  # Has architectural decisions
            return True
        if file_changes >= 10:  # Significant work session
            return True
        if problems >= 1:  # Documented problems/solutions
            return True
        if description and len(description) > 50 and 'auto-collected' not in description.lower():
            return True  # Detailed manual description

        return False

    def get_checkpoint_date(self, checkpoint: Dict) -> datetime:
        """Extract datetime from checkpoint"""
        timestamp_str = checkpoint.get('timestamp', '')
        try:
            return datetime.fromisoformat(timestamp_str)
        except:
            return datetime.min

    def filter_checkpoints(self, days: int = None, high_value_only: bool = False) -> List[Tuple[Path, Dict]]:
        """Filter checkpoints based on criteria"""
        checkpoints = []
        cutoff_date = None

        if days:
            cutoff_date = datetime.now() - timedelta(days=days)

        for checkpoint_file in self.checkpoints_dir.glob("checkpoint-*.json"):
            checkpoint = self.load_checkpoint(checkpoint_file)
            if not checkpoint:
                continue

            # Check date filter
            if cutoff_date:
                checkpoint_date = self.get_checkpoint_date(checkpoint)
                if checkpoint_date < cutoff_date:
                    continue

            # Check high-value filter
            if high_value_only and not self.is_high_value(checkpoint):
                continue

            checkpoints.append((checkpoint_file, checkpoint))

        # Sort by date (oldest first for summary)
        checkpoints.sort(key=lambda x: self.get_checkpoint_date(x[1]))

        return checkpoints

    def group_by_project(self, checkpoints: List[Tuple[Path, Dict]]) -> Dict[str, List[Tuple[Path, Dict]]]:
        """Group checkpoints by project"""
        by_project = defaultdict(list)

        for checkpoint_file, checkpoint in checkpoints:
            project = checkpoint.get('project', {})
            project_name = project.get('name', 'Unknown')
            project_remote = project.get('git_remote_url', 'No remote')

            # Use remote URL as primary key (more portable)
            if 'github.com' in project_remote:
                import re
                match = re.search(r'github\.com[:/](.+?)(?:\.git)?$', project_remote)
                if match:
                    project_key = match.group(1)
                else:
                    project_key = project_name
            else:
                project_key = project_name

            by_project[project_key].append((checkpoint_file, checkpoint))

        return by_project

    def generate_checkpoint_summary(self, checkpoint: Dict, include_files: bool = False) -> str:
        """Generate markdown summary for a single checkpoint"""
        lines = []

        # Header
        session_id = checkpoint.get('session_id', 'unknown')
        timestamp = checkpoint.get('timestamp', 'unknown')[:19]  # YYYY-MM-DD HH:MM:SS
        lines.append(f"### Session {session_id}")
        lines.append(f"**Date:** {timestamp}")

        # Description
        context = checkpoint.get('context', {})
        description = context.get('description', 'No description')
        lines.append(f"**Description:** {description}")

        # Git commit (if available)
        git_commit = checkpoint.get('git_commit_hash')
        if git_commit:
            git_branch = checkpoint.get('git_branch', 'unknown')
            lines.append(f"**Commit:** `{git_commit[:8]}` (branch: {git_branch})")

        # File changes summary
        file_changes = checkpoint.get('file_changes', [])
        if file_changes:
            lines.append(f"**Files changed:** {len(file_changes)}")
            if include_files and len(file_changes) <= 10:
                lines.append("")
                lines.append("**Changed files:**")
                for change in file_changes[:10]:
                    action = change.get('action', 'modified')
                    filepath = change.get('file_path', 'unknown')
                    lines.append(f"  - [{action}] `{filepath}`")

        # Decisions (high-value!)
        decisions = checkpoint.get('decisions', [])
        if decisions:
            lines.append("")
            lines.append(f"**Decisions made:** {len(decisions)}")
            for decision in decisions:
                question = decision.get('question', 'Unknown')
                chosen = decision.get('decision', 'Unknown')
                rationale = decision.get('rationale', 'No rationale')
                lines.append(f"  - **Q:** {question}")
                lines.append(f"    **A:** {chosen}")
                lines.append(f"    **Why:** {rationale}")

        # Problems encountered
        problems = checkpoint.get('problems_encountered', [])
        if problems:
            lines.append("")
            lines.append(f"**Problems encountered:**")
            for problem in problems:
                lines.append(f"  - {problem}")

        # Resume points
        resume_points = checkpoint.get('resume_points', [])
        if resume_points:
            lines.append("")
            lines.append(f"**Resume points:**")
            for point in resume_points:
                lines.append(f"  - {point}")

        lines.append("")
        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def generate_project_summary(self, project_key: str, checkpoints: List[Tuple[Path, Dict]]) -> str:
        """Generate markdown summary for a project"""
        lines = []

        # Get project metadata from first checkpoint
        first_checkpoint = checkpoints[0][1]
        project = first_checkpoint.get('project', {})
        project_name = project.get('name', project_key)
        project_remote = project.get('git_remote_url', 'No remote')

        # Header
        lines.append(f"# Historical Context: {project_name}")
        lines.append("")
        lines.append(f"**Project:** {project_key}")
        lines.append(f"**Remote:** {project_remote}")
        lines.append(f"**Sessions:** {len(checkpoints)}")
        lines.append("")

        # Date range
        first_date = self.get_checkpoint_date(checkpoints[0][1])
        last_date = self.get_checkpoint_date(checkpoints[-1][1])
        lines.append(f"**Date range:** {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
        lines.append("")

        lines.append("---")
        lines.append("")

        # Individual checkpoint summaries
        for checkpoint_file, checkpoint in checkpoints:
            summary = self.generate_checkpoint_summary(
                checkpoint,
                include_files=(len(checkpoint.get('file_changes', [])) <= 10)
            )
            lines.append(summary)

        # Footer
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*This summary was auto-generated from historical checkpoint files.*")
        lines.append("*Original checkpoints preserved in `~/.claude-sessions-archive/`*")
        lines.append("")

        return "\n".join(lines)

    def migrate(self, days: int = None, high_value_only: bool = False, dry_run: bool = False) -> Dict[str, int]:
        """Perform migration"""
        stats = {
            'total_checkpoints': 0,
            'migrated_checkpoints': 0,
            'projects': 0,
            'high_value': 0,
            'files_created': 0
        }

        print()
        print("=" * 70)
        print(" " * 15 + "CHECKPOINT MIGRATION TO SUMMARIES")
        print("=" * 70)
        print()

        # Filter checkpoints
        print("[1/4] Filtering checkpoints...")
        checkpoints = self.filter_checkpoints(days=days, high_value_only=high_value_only)
        stats['total_checkpoints'] = len(checkpoints)

        if high_value_only:
            stats['high_value'] = len(checkpoints)
        else:
            stats['high_value'] = sum(1 for _, cp in checkpoints if self.is_high_value(cp))

        print(f"  Found {stats['total_checkpoints']} checkpoint(s)")
        print(f"  High-value: {stats['high_value']} ({stats['high_value'] * 100 // max(stats['total_checkpoints'], 1)}%)")

        if not checkpoints:
            print()
            print("[!] No checkpoints found matching criteria")
            return stats

        # Group by project
        print()
        print("[2/4] Grouping by project...")
        by_project = self.group_by_project(checkpoints)
        stats['projects'] = len(by_project)
        print(f"  Found {stats['projects']} project(s)")

        # Generate summaries
        print()
        print("[3/4] Generating markdown summaries...")
        for project_key, project_checkpoints in by_project.items():
            print(f"  - {project_key}: {len(project_checkpoints)} session(s)")

            if dry_run:
                stats['migrated_checkpoints'] += len(project_checkpoints)
                continue

            # Generate project summary
            summary_content = self.generate_project_summary(project_key, project_checkpoints)

            # Write to file
            # Sanitize project key for filename
            safe_project_key = project_key.replace('/', '_').replace('\\', '_')
            output_file = self.output_dir / f"{safe_project_key}.md"

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary_content)

            stats['files_created'] += 1
            stats['migrated_checkpoints'] += len(project_checkpoints)

        # Create index file
        if not dry_run and stats['files_created'] > 0:
            print()
            print("[4/4] Creating index file...")
            self._create_index_file(by_project)

        print()
        print("=" * 70)
        if dry_run:
            print(" " * 20 + "DRY RUN COMPLETE")
        else:
            print(" " * 20 + "MIGRATION COMPLETE")
        print("=" * 70)
        print()

        return stats

    def _create_index_file(self, by_project: Dict[str, List[Tuple[Path, Dict]]]):
        """Create index.md with overview of all projects"""
        lines = []

        lines.append("# Historical Context Index")
        lines.append("")
        lines.append("This directory contains markdown summaries of historical checkpoint data,")
        lines.append("organized by project. These summaries provide searchable context for past")
        lines.append("work sessions.")
        lines.append("")
        lines.append("**Purpose:** Make historical checkpoint data accessible for reference")
        lines.append("without directly injecting into claude-mem (which captures observations")
        lines.append("naturally during conversations).")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Projects")
        lines.append("")

        for project_key, project_checkpoints in by_project.items():
            first_checkpoint = project_checkpoints[0][1]
            project = first_checkpoint.get('project', {})
            project_name = project.get('name', project_key)
            project_remote = project.get('git_remote_url', 'No remote')

            first_date = self.get_checkpoint_date(project_checkpoints[0][1])
            last_date = self.get_checkpoint_date(project_checkpoints[-1][1])

            safe_project_key = project_key.replace('/', '_').replace('\\', '_')

            lines.append(f"### {project_name}")
            lines.append(f"- **File:** [{safe_project_key}.md]({safe_project_key}.md)")
            lines.append(f"- **Remote:** {project_remote}")
            lines.append(f"- **Sessions:** {len(project_checkpoints)}")
            lines.append(f"- **Date range:** {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*Auto-generated by `migrate_checkpoints_to_summaries.py`*")
        lines.append("")

        index_file = self.output_dir / "index.md"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        print(f"  Created index: {index_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Migrate historical checkpoints to markdown summaries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate_checkpoints_to_summaries.py
      Migrate all checkpoints (last 90 days + high-value older)

  python migrate_checkpoints_to_summaries.py --days 90
      Migrate only last 90 days

  python migrate_checkpoints_to_summaries.py --high-value-only
      Migrate only high-value checkpoints (decisions, problems, significant work)

  python migrate_checkpoints_to_summaries.py --dry-run
      Preview what would be migrated without creating files
        """
    )

    parser.add_argument(
        '--days',
        type=int,
        help='Migrate checkpoints from last N days (default: all)'
    )

    parser.add_argument(
        '--high-value-only',
        action='store_true',
        help='Migrate only high-value checkpoints (decisions, significant changes)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview migration without creating files'
    )

    parser.add_argument(
        '--checkpoints-dir',
        type=str,
        default=str(Path.home() / '.claude-sessions' / 'checkpoints'),
        help='Checkpoint directory path (default: ~/.claude-sessions/checkpoints)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default=str(Path.home() / '.claude' / 'historical-context'),
        help='Output directory for summaries (default: ~/.claude/historical-context)'
    )

    args = parser.parse_args()

    # Validate checkpoints directory exists
    checkpoints_dir = Path(args.checkpoints_dir)
    if not checkpoints_dir.exists():
        print(f"[ERROR] Checkpoints directory not found: {checkpoints_dir}")
        print()
        print("Expected location: ~/.claude-sessions/checkpoints/")
        print("Have you created any checkpoints yet?")
        sys.exit(1)

    # Create migrator
    output_dir = Path(args.output_dir)
    migrator = CheckpointMigrator(checkpoints_dir, output_dir)

    # Perform migration
    stats = migrator.migrate(
        days=args.days,
        high_value_only=args.high_value_only,
        dry_run=args.dry_run
    )

    # Display summary
    print(f"Total checkpoints scanned:  {stats['total_checkpoints']}")
    print(f"High-value checkpoints:     {stats['high_value']}")
    print(f"Projects found:             {stats['projects']}")
    print(f"Checkpoints migrated:       {stats['migrated_checkpoints']}")
    print(f"Markdown files created:     {stats['files_created']}")
    print()

    if not args.dry_run and stats['files_created'] > 0:
        print("Output directory:")
        print(f"  {output_dir}")
        print()
        print("View summaries:")
        print(f"  cat {output_dir / 'index.md'}")
        print()
        print("Next steps:")
        print("  1. Review generated summaries in ~/.claude/historical-context/")
        print("  2. Reference these summaries in future conversations")
        print("  3. claude-mem will naturally capture relevant context")
        print()
    elif args.dry_run:
        print("Dry run complete - no files created")
        print()
        print("Run without --dry-run to perform actual migration:")
        print(f"  python {Path(__file__).name}")
        print()

    print("=" * 70)


if __name__ == "__main__":
    main()
