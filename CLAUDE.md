# API Documentation Agent - Project Memory

## Project Overview
This project demonstrates an automated session continuity system for Claude Code, enabling seamless context preservation across sessions through intelligent checkpointing, automated change detection, and smart resume point generation.

The workspace also hosts the API Documentation Agent project and related tools in the `Projects/` directory.

## Session Protocol
For comprehensive instructions on session tracking and continuity, see [SESSION_PROTOCOL.md](SESSION_PROTOCOL.md).

**Quick workflow:**
```bash
# Work on code, then commit - that's it!
git add .
git commit -m "Your commit message"
# → Checkpoint + code context auto-generated via post-commit hook

# Search past sessions semantically
/mem-search authentication implementation

# View latest code context
cat .claude-code-context.md

# Check context usage
python scripts/context-monitor.py
```

**Migration:** The old checkpoint scripts (`checkpoint.py`, `resume-session.py`, `save-session.py`) are deprecated. See [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) for the new workflow.

---

## Current Session State

**Note:** This section is no longer auto-updated with the new claude-mem migration (Phase 3+).

**New Workflow:**
- Code context is auto-generated in `.claude-code-context.md` on every commit
- Session observations are automatically captured by claude-mem
- Use `/mem-search` to retrieve context from past sessions
- SessionStart hook displays recent context when Claude Code starts

**For latest code context:** See `.claude-code-context.md` (auto-updated on commit)
**For semantic search:** Use `/mem-search <query>` in Claude Code

## Integration Map

### Project Structure
This repository has **two layers**:

#### 1. Root Directory (`C:\Users\layden\`)
**Purpose:** Session continuity system and workspace management
**Key Files:**
- `CLAUDE.md` - This file, serving as persistent project memory
- `SESSION_PROTOCOL.md` - Comprehensive instructions for Claude Code
- `.claude-sessions/` - Session logs and checkpoints
- `scripts/` - Session management and automation tools
  - `checkpoint.py` - Unified checkpoint command
  - `session-logger.py` - Create session logs
  - `resume-session.py` - Load and display session state
  - `context-monitor.py` - Track context window usage
  - `dependency_analyzer.py` - Cross-file dependency tracking
  - Git hook automation scripts

#### 2. Projects Directory (`C:\Users\layden\Projects\`)
**Purpose:** Full implementations of various projects
**Status:** Contains multiple projects as separate git repositories
**Key Projects:**
- `api-documentation-agent/` - API documentation automation system
- Other projects tracked separately

### When to Use Which
- **Root CLAUDE.md:** For session continuity, planning, and project memory
- **SESSION_PROTOCOL.md:** Reference for Claude Code instructions
- **Projects directory:** For implementation details and running applications
- **Bridge between them:** This Integration Map section

---

## Decision Log

### Decision: Merge Unrelated Git Histories
**Date:** 2025-11-24
**Decision:** Merge workspace organization (local master) with session continuity system (origin/main)
**Rationale:** Both lines of work are valuable and complementary. Workspace org provides structure, session system provides automation.
**Resolution Strategy:**
- Scripts: Preserve local's bug fixes, adopt origin's new features
- CLAUDE.md: Manual merge combining workspace focus + session structure
- Documentation: Keep all files from both histories
**Alternatives Considered:**
- Force push (rejected: would lose session system work)
- Separate branches (rejected: features should be unified)

### Decision: Hybrid Logging Format
**Date:** 2025-11-12
**Decision:** Use both Markdown (human-readable) and JSON (machine-readable) for session logs
**Rationale:** Provides best of both worlds - humans can read logs naturally, machines can parse checkpoints for automation
**Alternatives Considered:**
- JSON only (harder for humans to read)
- Markdown only (harder for automation)

### Decision: Root vs Projects CLAUDE.md Location
**Date:** 2025-11-12
**Decision:** Maintain CLAUDE.md in root directory, not in Projects directory
**Rationale:** Root location keeps project memory close to working directory and separate from implementation details
**Alternatives Considered:**
- Projects directory (conflicts with implementation focus)
- Both locations (synchronization complexity)

### Decision: Script-Based Session Management
**Date:** 2025-11-12
**Decision:** Use Python scripts for session management instead of integrated automation
**Rationale:** Scripts provide flexibility, can be run manually or integrated later, easier to debug and customize
**Alternatives Considered:**
- Automated hooks (more complex, harder to debug)
- Manual markdown updates (error-prone, no checkpoints)

### Decision: Windows Encoding Compatibility
**Date:** 2025-11-13
**Decision:** Disable rich output on Windows, use ASCII-friendly formatting
**Rationale:** Prevents UnicodeEncodeError with emoji characters in Windows console
**Alternatives Considered:**
- Force UTF-8 (doesn't work reliably on Windows)
- Remove all special characters (loses visual clarity)

### Decision: Workspace Reorganization Strategy
**Date:** 2025-11-20
**Decision:** Move all project files to Projects/ subdirectory, keep only session tracking at root
**Rationale:** Clean separation of concerns - root for workspace config, Projects/ for implementations
**Impact:**
- Removed exposed API keys
- Fixed 22+ hardcoded paths
- Organized 1,075+ project files
- Achieved 100% test pass rate
**Alternatives Considered:**
- Keep root as project workspace (rejected: too cluttered)
- Multiple reorganization approaches (selected comprehensive cleanup)

---

## Automated Session Continuity

**Status:** ✅ Migrated to claude-mem + Code Context Hybrid (Phase 3)

**How it works now:**
- **SessionStart hook** → Auto-displays recent code context from `.claude-code-context.md`
- **SessionEnd hook** → Auto-generates code context for uncommitted changes
- **Git post-commit hook** → Auto-creates checkpoint + code context with dependencies
- **claude-mem plugin** → Auto-captures session observations for semantic search

**Result:** Zero manual work - fully automated context preservation + semantic search!

**Configuration:**
- `.claude/settings.json` - SessionStart/End hooks + claude-mem plugin
- `.git/hooks/post-commit` - Code context generation
- `CLAUDE_MEM_CONTEXT_OBSERVATIONS=25` - Optimized for cost (~$11.25/month)

**New Workflow:**
```bash
# 1. Make changes and commit
git add .
git commit -m "Your message"
# → Checkpoint + code context auto-generated

# 2. Search past sessions
/mem-search <query>

# 3. View latest code context
cat .claude-code-context.md
```

**Migration:** See [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) for transitioning from old checkpoint scripts

---

## Cross-File Dependency Tracking

**Status:** ✅ Integrated into Code Context Layer (Phase 2)

The system automatically analyzes Python file dependencies and provides intelligent impact warnings in `.claude-code-context.md`:

### Features
- **Automatic Analysis:** Tracks which files import each other (via AST parsing)
- **Impact Scoring:** 0-100 score based on file usage (higher = more critical)
- **Smart Warnings:** Alerts when modifying high-impact files
- **Intelligent Caching:** 7-8x speedup with mtime-based cache validation
- **Test Coverage:** Detects missing test files

### How It Works
Dependency analysis runs automatically on every commit via the post-commit hook. Results are written to `.claude-code-context.md`.

### Output Example (in .claude-code-context.md)
```markdown
## High-Impact Changes
[!] db/models.py (Impact: 85/100)
    Used by: 12 file(s)
    Used by: invoice.py, api.py, billing.py (+9 more)
    [!] No test file found -> Create test_models.py

## Dependencies
auth/login.py imports:
- api/routes.py
- db/models.py
- utils/validators.py

## Test Recommendations
- Run: test_api.py, test_db.py
- Create: test_auth.py (missing)
```

**Full Documentation:** [docs/DEPENDENCY_TRACKING.md](docs/DEPENDENCY_TRACKING.md)

---

## Multi-Project Session Tracking

**Status:** ✅ Fully Implemented

The session continuity system works across all projects in your workspace:

### Features
- **Automatic Project Detection:** Identifies which project you're working in
- **Project-Specific Sessions:** Tracks sessions separately per project
- **Global Session Index:** Central registry of all sessions across projects
- **Smart Context Switching:** Detects when you switch projects mid-session

### How It Works
- Git repository detection for project identity
- Session index at workspace root tracks all projects
- Checkpoints include project context
- Resume automatically loads correct project state

**Full Documentation:** [docs/MULTI_PROJECT_SESSION_TRACKING.md](MULTI_PROJECT_SESSION_TRACKING_COMPLETE.md)

---

## Quick Reference

### New Workflow (Phase 3+)

#### Create Checkpoint (Automatic)
```bash
# Just commit! Checkpoint + code context auto-generated
git add .
git commit -m "Your commit message"
```

#### Search Past Sessions
```bash
# Semantic search across all sessions
/mem-search authentication implementation
/mem-search database schema changes
/mem-search why did we choose Redis?
```

#### View Latest Code Context
```bash
# View auto-generated code context
cat .claude-code-context.md    # Windows: type .claude-code-context.md
```

#### Check Context Usage
```bash
python scripts/context-monitor.py
```

#### Install Git Hooks (One-Time Setup)
```bash
python scripts/install-hooks.py
```

### Old Commands (Deprecated)
```bash
# These show deprecation warnings - use new workflow instead
python scripts/checkpoint.py --quick         # → Use: git commit
python scripts/resume-session.py             # → Use: /mem-search
python scripts/save-session.py               # → Use: git commit
```

**Migration Guide:** See [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) for complete command mappings

---

## Architecture Principles
- **Hybrid Approach**: Combine AI efficiency with traditional tool reliability
- **Modularity**: Each tool serves a specific purpose with clear interfaces
- **Quality Gates**: Automated validation at every step
- **Scalability**: Design for enterprise deployment patterns
- **Session Continuity**: Maintain context across Claude Code sessions
- **Cross-Project Support**: Work seamlessly across multiple projects

---

## Standards and Guidelines
- All OpenAPI specs must be valid OpenAPI 3.0+
- Generated SDKs must include comprehensive examples
- Documentation must be accessible and responsive
- Tests must achieve >90% code coverage
- All outputs must pass security scans
- **Session Continuity:** Always create checkpoints before context window closes
- **Decision Documentation:** Log all architectural and implementation decisions
- **Progress Tracking:** Update Current Session State regularly

---

**For complete documentation, workflows, and detailed instructions:**
→ See [SESSION_PROTOCOL.md](SESSION_PROTOCOL.md)
