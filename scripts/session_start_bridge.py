#!/usr/bin/env python3
"""
Session Start Bridge - Lightweight replacement for resume-session.py

This script runs at session start after migrating to claude-mem.
It provides a minimal context reminder without heavy checkpoint processing.

What it does:
- Displays recent code context from .claude-code-context.md
- Reminds about /mem-search for semantic context retrieval
- Fast execution (<1 second)

What it DOESN'T do:
- No checkpoint file parsing
- No session index lookups
- No heavy dependency analysis

Usage:
    Called automatically by SessionStart hook in .claude/settings.json
"""

import sys
from pathlib import Path
from datetime import datetime


def display_session_start():
    """Display session start context"""
    print()
    print("=" * 70)
    print(" " * 20 + "SESSION STARTING")
    print("=" * 70)
    print()

    # Try to read code context file
    context_file = Path.cwd() / '.claude-code-context.md'

    if context_file.exists():
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract key info from context file
            lines = content.split('\n')

            # Find last commit info
            in_commit_section = False
            commit_info = []
            for line in lines:
                if line.startswith('## Last Commit'):
                    in_commit_section = True
                    continue
                elif line.startswith('##') and in_commit_section:
                    break
                elif in_commit_section and line.strip().startswith('-'):
                    commit_info.append(line.strip())

            if commit_info:
                print("[RECENT CODE CONTEXT]")
                for info in commit_info[:4]:  # First 4 lines (hash, branch, remote, date)
                    print(f"  {info}")
                print()

            print("[CODE CONTEXT AVAILABLE]")
            print(f"  File: .claude-code-context.md")
            print(f"  See file for dependencies, test recommendations, and change details")
            print()

        except Exception as e:
            # Don't fail session start if we can't read context
            pass

    # Remind about claude-mem
    print("[SEMANTIC SEARCH]")
    print("  Use /mem-search <query> to search across sessions")
    print("  Examples:")
    print("    /mem-search authentication implementation")
    print("    /mem-search architectural decisions")
    print("    /mem-search database schema changes")
    print()

    print("=" * 70)
    print()


def main():
    """Entry point"""
    try:
        display_session_start()
        return 0
    except Exception as e:
        # Don't fail session start on errors
        print(f"[Warning] Session start display error: {e}", file=sys.stderr)
        return 0


if __name__ == '__main__':
    sys.exit(main())
