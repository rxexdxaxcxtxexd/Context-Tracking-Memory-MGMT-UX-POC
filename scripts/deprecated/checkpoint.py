#!/usr/bin/env python3
"""
Unified Checkpoint Command
Combines: save-session.py + update-session-state.py + display

⚠️  DEPRECATION WARNING ⚠️
This script is deprecated as of Phase 3 of the claude-mem migration.

NEW WORKFLOW:
  - Session checkpoints: Automatic via git post-commit hook
  - Code context: Auto-generated in .claude-code-context.md
  - Semantic search: Use /mem-search in Claude Code
  - Memory: Automatic via claude-mem plugin

See docs/MIGRATION_GUIDE.md for details on the new workflow.

Usage:
    python checkpoint.py --quick                    # Quick checkpoint
    python checkpoint.py                            # Interactive mode
    python checkpoint.py --description "message"    # With description
    python checkpoint.py --dry-run                  # Preview only
"""

import sys
import subprocess
import argparse
from pathlib import Path


def print_deprecation_warning():
    """Print deprecation warning and prompt user"""
    print()
    print("=" * 70)
    print(" " * 20 + "⚠️  DEPRECATION WARNING ⚠️")
    print("=" * 70)
    print()
    print("This script (checkpoint.py) is deprecated.")
    print()
    print("REASON:")
    print("  The system has migrated to claude-mem for automatic memory capture.")
    print()
    print("NEW WORKFLOW:")
    print("  1. Make changes and commit with git")
    print("  2. Checkpoint + code context generated automatically")
    print("  3. Use /mem-search to retrieve context across sessions")
    print()
    print("BENEFITS:")
    print("  - Zero manual work (fully automated)")
    print("  - Semantic search across all sessions")
    print("  - Better context preservation")
    print()
    print("See: docs/MIGRATION_GUIDE.md for migration details")
    print("See: .claude-code-context.md for current code context")
    print()
    print("=" * 70)
    print()

    response = input("Continue with deprecated checkpoint anyway? (y/N): ")
    if response.lower() != 'y':
        print()
        print("Aborting. Use the new workflow instead:")
        print("  1. Commit your changes: git add . && git commit -m 'message'")
        print("  2. Context auto-generated on commit")
        print()
        sys.exit(0)
    print()
    print("Continuing with deprecated checkpoint...")
    print()


def run_command(command: list, description: str, can_fail: bool = False) -> bool:
    """Run a command and display results

    Args:
        command: Command to run
        description: What the command does
        can_fail: If True, continue on error; if False, exit on error

    Returns:
        True if successful, False if failed
    """
    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        if can_fail:
            print(f"[WARNING] {description} failed:")
            print(f"  {result.stderr}")
            return False
        else:
            print(f"[ERROR] {description} failed:")
            print(f"  {result.stderr}")
            sys.exit(1)

    # Show output
    if result.stdout:
        print(result.stdout)

    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Unified checkpoint command for session continuity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python checkpoint.py --quick
      Quick checkpoint with auto-detected description

  python checkpoint.py --description "Implemented auth system"
      Checkpoint with custom description

  python checkpoint.py --dry-run
      Preview what would be checkpointed without saving

  python checkpoint.py
      Interactive mode with prompts for details
        """
    )

    # Main options
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick checkpoint (no prompts, auto-detect everything)'
    )

    parser.add_argument(
        '--description',
        type=str,
        help='Custom session description'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview checkpoint without creating files'
    )

    parser.add_argument(
        '--since-minutes',
        type=int,
        default=240,
        help='Look for changes in last N minutes (default: 240)'
    )

    parser.add_argument(
        '--project-path',
        type=str,
        help='Project directory path (bypasses auto-detection)'
    )

    parser.add_argument(
        '--force-home',
        action='store_true',
        help='Allow checkpointing from home directory (for automated monitoring)'
    )

    # Advanced options
    parser.add_argument(
        '--skip-update',
        action='store_true',
        help='Skip CLAUDE.md update (advanced)'
    )

    parser.add_argument(
        '--skip-display',
        action='store_true',
        help='Skip summary display (advanced)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress'
    )

    args = parser.parse_args()

    # Show deprecation warning (unless --dry-run)
    if not args.dry_run:
        print_deprecation_warning()

    # Get scripts directory
    scripts_dir = Path(__file__).parent

    # Print header
    print()
    print("="*70)
    print(" "*20 + "UNIFIED CHECKPOINT")
    print("="*70)

    if args.dry_run:
        print("[DRY RUN MODE - No files will be created]")

    print()

    # Step 1: Save session
    print("[1/3] Collecting and saving session data...")
    print()

    save_cmd = [sys.executable, str(scripts_dir / 'save-session.py')]

    if args.quick:
        save_cmd.append('--quick')

    if args.description:
        save_cmd.extend(['--description', args.description])

    if args.dry_run:
        save_cmd.append('--dry-run')

    if args.project_path:
        save_cmd.extend(['--project-path', args.project_path])

    if args.force_home:
        save_cmd.append('--force-home')

    save_cmd.extend(['--since-minutes', str(args.since_minutes)])

    success = run_command(
        save_cmd,
        "Save session",
        can_fail=False
    )

    # If dry-run, stop here
    if args.dry_run:
        print()
        print("="*70)
        print("DRY RUN COMPLETE - No files were created")
        print("="*70)
        return 0

    # Step 2: Update CLAUDE.md (unless skipped)
    if not args.skip_update:
        print()
        print("[2/3] Updating CLAUDE.md...")

        update_cmd = [
            sys.executable,
            str(scripts_dir / 'update-session-state.py'),
            'update'
        ]

        success = run_command(
            update_cmd,
            "Update CLAUDE.md",
            can_fail=True  # Can continue if this fails
        )

        if success:
            print("[OK] CLAUDE.md synchronized with checkpoint")
    else:
        if args.verbose:
            print("\n[2/3] Skipping CLAUDE.md update (--skip-update)")

    # Step 3: Display summary (unless skipped)
    if not args.skip_display:
        print()
        print("[3/3] Session summary:")
        print("-" * 70)

        summary_cmd = [
            sys.executable,
            str(scripts_dir / 'resume-session.py'),
            'summary'
        ]

        run_command(
            summary_cmd,
            "Display summary",
            can_fail=True  # Can continue if this fails
        )
    else:
        if args.verbose:
            print("\n[3/3] Skipping summary display (--skip-display)")

    # Final message
    print()
    print("="*70)
    print(" "*23 + "CHECKPOINT COMPLETE")
    print("="*70)
    print()
    print("To resume in a new session:")
    print("  python scripts/resume-session.py")
    print()
    print("To check context usage:")
    print("  python scripts/context-monitor.py")
    print()
    print("="*70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
