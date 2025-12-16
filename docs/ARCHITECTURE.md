# System Architecture: claude-mem + Code Context Hybrid

**Version:** 2.0 (Post-Migration)
**Date:** 2025-12-15
**Status:** Production

---

## Overview

The session continuity system uses a **hybrid architecture** combining two complementary layers:

1. **claude-mem (Semantic Layer)** - Long-term memory with semantic search
2. **Code Context Layer** - Short-term technical snapshot with dependencies

This architecture provides both **semantic understanding** (what did I do?) and **technical precision** (which files changed, what are the dependencies?).

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      CLAUDE CODE                            │
│  (Main application with claude-mem plugin enabled)          │
└────────────────┬──────────────────────┬─────────────────────┘
                 │                      │
       ┌─────────▼────────┐   ┌────────▼──────────┐
       │ SessionStart Hook│   │ SessionEnd Hook   │
       │ (Lightweight)     │   │ (Lightweight)     │
       └─────────┬────────┘   └────────┬──────────┘
                 │                      │
       ┌─────────▼───────────────────────▼──────────┐
       │    session_start_bridge.py                 │
       │    - Display recent code context           │
       │    - Remind about /mem-search              │
       │                                             │
       │    session_end_bridge.py                   │
       │    - Generate context for uncommitted      │
       │    - Log session end                       │
       └─────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     USER WORKFLOW                           │
└────────────────┬────────────────────────────────────────────┘
                 │
       ┌─────────▼──────────┐
       │ git commit -m "..." │
       └─────────┬───────────┘
                 │
       ┌─────────▼─────────────────────────────────────────────┐
       │        Git Post-Commit Hook                           │
       │        (.git/hooks/post-commit)                       │
       └─────────┬─────────────────────────────────────────────┘
                 │
       ┌─────────▼─────────────────────────────────────────────┐
       │    post-commit-handler.py                             │
       │    1. Create checkpoint JSON                          │
       │    2. Call generate_code_context.py                   │
       └─────────┬─────────────────────────────────────────────┘
                 │
       ┌─────────▼─────────────────────────────────────────────┐
       │    generate_code_context.py                           │
       │    1. Get git metadata                                │
       │    2. Get changed files                               │
       │    3. Run dependency_analyzer.py                      │
       │    4. Generate .claude-code-context.md                │
       └─────────┬─────────────────────────────────────────────┘
                 │
       ┌─────────▼─────────────────────────────────────────────┐
       │    dependency_analyzer.py                             │
       │    - AST-based Python import analysis                 │
       │    - Impact scoring (0-100)                           │
       │    - Test coverage detection                          │
       │    - Intelligent caching (mtime-based)                │
       └───────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    STORAGE LAYERS                           │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┐  ┌──────────────────────────┐
│  claude-mem (Semantic Layer)     │  │  Code Context Layer      │
│                                  │  │                          │
│  Location: ~/.claude/mem/        │  │  Location: (project root)│
│  Format: SQLite + Chroma vector  │  │  File: .claude-code-     │
│  Content: Observations           │  │        context.md        │
│  Search: /mem-search <query>     │  │  Content: Technical      │
│  Capture: Automatic during       │  │           snapshot       │
│           conversations          │  │  Update: On every commit │
│                                  │  │  Format: Markdown        │
│  Purpose: Long-term semantic     │  │  Purpose: Short-term     │
│           memory                 │  │           technical      │
│                                  │  │           precision      │
└──────────────────────────────────┘  └──────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    ARCHIVE LAYER                            │
│                                                             │
│  Historical Context: ~/.claude/historical-context/         │
│  - Markdown summaries of old checkpoints                   │
│  - Organized by project                                    │
│  - Searchable, referenceable                               │
│                                                             │
│  Original Checkpoints: ~/.claude-sessions-archive/         │
│  - 1,921 original checkpoint JSON files                    │
│  - Preserved for rollback                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1: claude-mem (Semantic Layer)

### Purpose
Long-term semantic memory with natural language search across all sessions.

### Technology
- **Storage:** SQLite database + Chroma vector database
- **Location:** `~/.claude/mem/`
- **Capture:** Automatic during Claude Code conversations
- **Search:** `/mem-search <query>` command

### What It Stores
- **Observations:** High-level discussions, decisions, explanations
- **Semantic context:** "Why did we choose Redis?" "How does auth work?"
- **Architectural decisions:** Design choices and rationale
- **Problem discussions:** Issues encountered and solutions

### Retrieval
```bash
/mem-search authentication implementation
/mem-search why did we choose Redis over in-memory cache?
/mem-search what was the solution for the CORS error?
```

**Search Type:** Semantic similarity (not keyword matching)
**Result:** Relevant past observations with context

### Cost Optimization
```json
{
  "env": {
    "CLAUDE_MEM_CONTEXT_OBSERVATIONS": "25"
  }
}
```

- **Default:** 50 observations per context window (~$38.25/month)
- **Optimized:** 25 observations per context window (~$11.25/month)
- **Trade-off:** Slightly less context but still very effective

### When It's Used
- **Automatically:** During every Claude Code conversation
- **On demand:** When using `/mem-search` command
- **Background:** Observations captured as you work

---

## Layer 2: Code Context Layer

### Purpose
Short-term technical snapshot with file-level precision and dependency analysis.

### Technology
- **Storage:** Markdown file (`.claude-code-context.md`)
- **Location:** Project root directory (gitignored)
- **Generation:** Automatic on every git commit
- **Update:** Also updated on SessionEnd if uncommitted changes

### What It Stores
- **Git metadata:** Commit hash, branch, remote URL, message
- **Changed files:** Full list with action (created/modified/deleted)
- **High-impact warnings:** Files used by many others (score >=70)
- **Dependencies:** Which files import which (AST-based)
- **Test recommendations:** Missing test files, tests to run
- **Date/time:** When context was generated

### Example Content
```markdown
# Code Context (Auto-generated)

**Last Updated:** 2025-12-15 20:23:18

## Last Commit
- **Hash:** `4aebaeed`
- **Branch:** `master`
- **Remote:** github.com/user/repo
- **Date:** 2025-12-15T20:22:51-06:00
- **Message:** Phase 2 Complete: Code Context Layer Integration

## Changed Files (3)
- [+] `.gitignore`
- [+] `scripts/generate_code_context.py`
- [M] `scripts/post-commit-handler.py`

## High-Impact Changes
[!] db/models.py (Impact: 85/100)
    Used by: 12 file(s)
    Used by: invoice.py, api.py, billing.py (+9 more)
    [!] No test file found -> Create test_models.py

## Dependencies
scripts/generate_code_context.py imports:
- scripts/dependency_analyzer.py
- pathlib.Path
- subprocess
- json

## Test Recommendations
- Run: test_generator.py
- Create: test_post_commit.py (missing)
```

### When It's Used
- **Automatically:** Generated on every git commit
- **SessionEnd:** Updated if uncommitted changes exist
- **SessionStart:** Displayed as recent context reminder
- **On demand:** Read `.claude-code-context.md` anytime

---

## Data Flow

### 1. User Makes Changes
```
User modifies files → Works on code
```

### 2. User Commits
```
git add .
git commit -m "Implement feature X"
↓
Post-commit hook triggered
↓
post-commit-handler.py runs
  ├─ Creates checkpoint JSON
  └─ Calls generate_code_context.py
     ├─ Gets git metadata
     ├─ Gets changed files
     ├─ Runs dependency_analyzer.py (AST analysis)
     └─ Generates .claude-code-context.md
```

### 3. Session End
```
User closes Claude Code
↓
SessionEnd hook triggered
↓
session_end_bridge.py runs
  ├─ Checks for uncommitted changes
  └─ If found: Generates code context for workspace state
```

### 4. Session Start (Next Session)
```
User starts Claude Code
↓
SessionStart hook triggered
↓
session_start_bridge.py runs
  ├─ Displays recent code context from .claude-code-context.md
  └─ Reminds about /mem-search for semantic queries
```

### 5. Semantic Search
```
User types: /mem-search authentication flow
↓
claude-mem searches vector database
↓
Returns relevant past observations with context
```

---

## Component Details

### Active Scripts (7 core + 5 supporting)

#### Core Functionality
1. **`generate_code_context.py`** (380 lines)
   - Generates `.claude-code-context.md` from git commits
   - Integrates with dependency analyzer
   - Fast (<2 seconds for typical commits)

2. **`dependency_analyzer.py`** (540 lines)
   - AST-based Python import analysis
   - Impact scoring (0-100 based on usage)
   - Intelligent caching (mtime-based, 75-85% hit rate)
   - Test coverage detection

3. **`post-commit-handler.py`** (Modified)
   - Git post-commit hook handler
   - Creates checkpoint JSON
   - Calls code context generator
   - Never blocks git workflow (errors logged, always succeeds)

4. **`session_start_bridge.py`** (99 lines)
   - Lightweight SessionStart hook
   - Displays recent code context
   - Reminds about /mem-search
   - Fast (<1 second)

5. **`session_end_bridge.py`** (154 lines)
   - Lightweight SessionEnd hook
   - Generates context for uncommitted changes
   - Logs session end
   - Fast (<2 seconds)

6. **`migrate_checkpoints_to_summaries.py`** (540 lines)
   - Migrates historical checkpoints to markdown
   - Groups by project
   - Filters by date/high-value
   - One-time migration utility

7. **`install-hooks.py`**
   - Git hook installation utility
   - Sets up post-commit hook

#### Supporting Modules
1. **`checkpoint_utils.py`** - Shared utility functions
2. **`session_index.py`** - Session index management
3. **`resume_point_generator.py`** - Generate resume suggestions
4. **`project_tracker.py`** - Multi-project tracking
5. **`context-monitor.py`** - Context window usage tracking

### Deprecated Scripts (Moved to scripts/deprecated/)
- `checkpoint.py` (303 lines) - Manual checkpoint creation
- `save-session.py` (1,126 lines) - Session data collection
- `resume-session.py` (647 lines) - Session resume/display
- `session-logger.py` (500+ lines) - Checkpoint file creation
- `update-session-state.py` (200+ lines) - CLAUDE.md auto-updater
- `create_this_session_checkpoint.py`

**Total deprecated:** ~2,800 lines
**Total active:** ~800 lines core + ~500 lines supporting
**Reduction:** 60% code reduction

---

## Configuration

### .claude/settings.json
```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python scripts/session_start_bridge.py",
        "timeout": 10000
      }]
    }],
    "SessionEnd": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python scripts/session_end_bridge.py",
        "timeout": 30000
      }]
    }]
  },
  "enabledPlugins": {
    "claude-mem@anthropic": true
  },
  "env": {
    "CLAUDE_MEM_CONTEXT_OBSERVATIONS": "25"
  }
}
```

### .git/hooks/post-commit
```bash
#!/bin/bash
python "C:\Users\layden\scripts\post-commit-handler.py"
exit 0  # Always succeed
```

### .gitignore
```
.claude-code-context.md
.claude-sessions/
```

---

## Performance

### Code Context Generation
- **Typical commit (10-20 files):** <2 seconds
- **Large commit (50+ files):** 3-5 seconds
- **Cache hit rate:** 75-85% (dependency analysis)

### Session Hooks
- **SessionStart:** <1 second
- **SessionEnd:** <2 seconds (with uncommitted changes)

### Git Workflow
- **Post-commit hook:** Adds <2 seconds to commit time
- **Never blocks:** Errors logged but commit always succeeds

---

## Comparison: Old vs New

| Aspect | Old System | New System |
|--------|-----------|------------|
| **Manual work** | High (remember to checkpoint) | Zero (automatic) |
| **Scripts** | 20+ scripts, 8,000+ LOC | 7 core + 5 supporting, ~1,300 LOC |
| **Search** | Keyword search through JSON | Semantic search with /mem-search |
| **Context** | Single checkpoint file (mixed) | Hybrid (semantic + technical) |
| **Performance** | Heavy (checkpoint.py: 303 lines) | Lightweight (bridge: 99 lines) |
| **Session start** | 3-5 seconds (resume-session.py) | <1 second (bridge) |
| **Session end** | 5-10 seconds (checkpoint.py) | <2 seconds (bridge) |
| **Maintenance** | Complex (20+ scripts) | Simple (7 core scripts) |

---

## Design Principles

### 1. Progressive Disclosure
- **Light on session start:** Brief reminder, not overwhelming
- **Deep on demand:** `/mem-search` for specific queries
- **Technical precision:** Code context file for details

### 2. Fail-Safe Operation
- **Git workflow never blocked:** Hook errors logged, always succeed
- **Graceful degradation:** If context generation fails, commit still works
- **No data loss:** Original checkpoints archived, not deleted

### 3. Separation of Concerns
- **claude-mem:** Semantic, long-term, conversational
- **Code context:** Technical, short-term, file-level
- **Archive:** Historical, reference-only

### 4. Zero-Friction Automation
- **No manual commands:** Everything automatic via hooks
- **Invisible when working:** Only see output when useful
- **Fast execution:** All operations <2 seconds

---

## Future Considerations

### Potential Enhancements
1. **Multi-language support:** Extend dependency analysis beyond Python
2. **Visual dependency graphs:** Generate diagrams from dependency data
3. **Predictive test suggestions:** ML-based test file recommendations
4. **Cross-project context:** Link related work across projects
5. **Cost monitoring:** Track claude-mem API usage automatically

### Scalability
- **Large repos (1000+ files):** Dependency analysis may need optimization
- **Many concurrent projects:** Session index scales well
- **Long-running sessions:** claude-mem handles gracefully

---

## Rollback Procedures

See `docs/MIGRATION_GUIDE.md` for complete rollback procedures if needed.

---

**Last Updated:** 2025-12-15
**Version:** 2.0 (claude-mem + Code Context Hybrid)
**Status:** Production
