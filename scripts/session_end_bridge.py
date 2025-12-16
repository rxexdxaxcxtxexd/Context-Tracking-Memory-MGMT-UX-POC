#!/usr/bin/env python3
"""
Session End Bridge - Lightweight replacement for checkpoint.py

This script runs at session end after migrating to claude-mem.
It ensures code context is up-to-date for workspace changes.

What it does:
- Generates code context if there are uncommitted changes
- Fast execution (<2 seconds)
- Logs session end for debugging

What it DOESN'T do:
- No checkpoint file creation (handled by post-commit hook)
- No heavy session data collection
- No CLAUDE.md updates (deprecated)

Usage:
    Called automatically by SessionEnd hook in .claude/settings.json
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def has_uncommitted_changes() -> bool:
    """Check if there are uncommitted changes in the workspace"""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=5
        )
        # If output is not empty, there are changes
        return bool(result.stdout.strip())
    except Exception:
        return False


def generate_code_context_from_workspace():
    """Generate code context for uncommitted workspace state"""
    try:
        # Get list of modified/untracked files
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return False

        changed_files = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Parse git status format: "XY filename"
                status = line[:2]
                filename = line[3:].strip()
                changed_files.append(filename)

        if not changed_files:
            return False

        # Call generate_code_context with changed files
        context_script = Path(__file__).parent / 'generate_code_context.py'
        cmd = [
            sys.executable,
            str(context_script),
            '--auto',
            '--changed-files'
        ] + changed_files

        result = subprocess.run(
            cmd,
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("[OK] Code context updated for workspace changes")
            return True
        else:
            print(f"[!] Code context update failed: {result.stderr}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"[!] Error updating code context: {e}", file=sys.stderr)
        return False


def log_session_end():
    """Log session end for debugging (temporary during migration)"""
    try:
        log_dir = Path.home() / '.claude-sessions' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / 'session-end.log'
        with open(log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp} - Session ended\n")
    except Exception:
        # Don't fail session end if logging fails
        pass


def main():
    """Entry point"""
    try:
        print()
        print("=" * 70)
        print(" " * 20 + "SESSION ENDING")
        print("=" * 70)
        print()

        # Check for uncommitted changes
        if has_uncommitted_changes():
            print("[UNCOMMITTED CHANGES DETECTED]")
            print("  Updating code context for workspace state...")
            generate_code_context_from_workspace()
        else:
            print("[NO UNCOMMITTED CHANGES]")
            print("  Code context is up-to-date from last commit")

        print()

        # Log for debugging
        log_session_end()

        # claude-mem handles observation capture automatically
        print("[MEMORY PRESERVED]")
        print("  Session observations captured by claude-mem")
        print("  Use /mem-search in next session to retrieve context")
        print()

        print("=" * 70)
        print()

        return 0

    except Exception as e:
        # Don't fail session end on errors
        print(f"[!] Session end error: {e}", file=sys.stderr)
        return 0


if __name__ == '__main__':
    sys.exit(main())
