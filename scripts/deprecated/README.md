# Deprecated Scripts

**Date Deprecated:** 2025-12-15 (Phase 5 of claude-mem migration)
**Reason:** Replaced by automated hybrid system (claude-mem + code context layer)

---

## Overview

This directory contains scripts from the **old file-based checkpoint system** that have been deprecated and replaced with a fully automated workflow.

**Migration:** See `docs/MIGRATION_GUIDE.md` for command mappings and new workflow.

---

## Deprecated Scripts

### checkpoint.py
**Status:** Deprecated (Phase 3B)
**Replaced by:** Git commits trigger automatic checkpoint + code context generation
**Old usage:** `python checkpoint.py --quick`
**New workflow:** `git commit -m "message"` (automatic)

### save-session.py
**Status:** Deprecated (Phase 3B)
**Replaced by:** Git post-commit hook + SessionEnd hook
**Old usage:** `python save-session.py --quick`
**New workflow:** `git commit -m "message"` (automatic)

### resume-session.py
**Status:** Deprecated (Phase 3B)
**Replaced by:** SessionStart hook + /mem-search
**Old usage:** `python resume-session.py`
**New workflow:** Start Claude Code (auto-displays context) or `/mem-search <query>`

### session-logger.py
**Status:** Deprecated (Phase 5A)
**Replaced by:** Integrated into post-commit-handler.py
**Old usage:** Called by other scripts to create checkpoints
**New workflow:** Automatic checkpoint creation on commit

### update-session-state.py
**Status:** Deprecated (Phase 5A)
**Replaced by:** Code context layer (.claude-code-context.md)
**Old usage:** `python update-session-state.py update`
**New workflow:** CLAUDE.md no longer auto-updated; see .claude-code-context.md instead

---

## Why Deprecated?

The old checkpoint system had several issues:

1. **Manual intervention required** - Had to remember to checkpoint
2. **Heavy scripts** - checkpoint.py (300+ lines), resume-session.py (647 lines)
3. **Cognitive load** - Multiple commands to remember
4. **No semantic search** - Only keyword search through JSON files
5. **Complex architecture** - 20+ scripts, 8,000+ lines of code

## New System Benefits

1. **Zero manual work** - Everything automatic via git hooks
2. **Lightweight** - Bridge scripts are <200 lines total
3. **Semantic search** - `/mem-search` finds anything from past sessions
4. **Better context** - Hybrid approach (claude-mem + code context)
5. **Simpler** - 7 active scripts vs 20+ deprecated

---

## Active Scripts (Still Used)

These scripts remain active in the parent `scripts/` directory:

### Core Functionality
- **`dependency_analyzer.py`** - AST-based Python dependency analysis
- **`generate_code_context.py`** - Generates .claude-code-context.md on commits
- **`post-commit-handler.py`** - Git post-commit hook handler
- **`session_start_bridge.py`** - Lightweight SessionStart hook
- **`session_end_bridge.py`** - Lightweight SessionEnd hook

### Migration & Utilities
- **`migrate_checkpoints_to_summaries.py`** - Migrates old checkpoints to markdown
- **`install-hooks.py`** - Git hook installation utility
- **`context-monitor.py`** - Context window usage tracking
- **`project_tracker.py`** - Multi-project session tracking

### Supporting Modules
- **`checkpoint_utils.py`** - Shared utility functions
- **`session_index.py`** - Session index management
- **`resume_point_generator.py`** - Generate resume suggestions

---

## If You Need to Use Old Scripts

**Not recommended**, but if you must:

1. **They still work** - Pressing 'y' at deprecation warning allows use
2. **No integration** - Won't work with claude-mem or code context layer
3. **Manual only** - No automation, must run explicitly

**Better approach:** Transition to new workflow (see `docs/MIGRATION_GUIDE.md`)

---

## Restoration (Emergency)

If the new system fails and you need to restore the old checkpoint system:

```bash
# 1. Copy scripts back to parent directory
cp scripts/deprecated/*.py scripts/

# 2. Restore old hooks in .claude/settings.json
# (see .claude/settings.json.pre-migration if you backed it up)

# 3. Disable claude-mem plugin in settings.json

# 4. Restart Claude Code
```

See `docs/MIGRATION_GUIDE.md` for complete rollback procedures.

---

## File Manifest

Scripts moved to this directory during Phase 5:

- checkpoint.py (303 lines) - Unified checkpoint command
- save-session.py (1,126 lines) - Session data collection
- resume-session.py (647 lines) - Session resume and display
- session-logger.py (500+ lines) - Checkpoint file creation
- update-session-state.py (200+ lines) - CLAUDE.md auto-updater

**Total:** ~2,800 lines of deprecated code
**Replaced by:** ~800 lines of active code (60% reduction)

---

## Timeline

- **2024-11-12** - Original checkpoint system implemented
- **2025-12-15** - Phase 1-4: Migration to claude-mem + code context
- **2025-12-15** - Phase 5: Scripts deprecated and moved here

---

**For current workflow documentation:**
- See `docs/MIGRATION_GUIDE.md`
- See `CLAUDE.md` (Quick Reference section)
- See `SESSION_PROTOCOL.md` (updated for new workflow)
