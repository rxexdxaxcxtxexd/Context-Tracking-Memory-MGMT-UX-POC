# Context Tracking & Memory Management - Development Workspace

> **Seamless session continuity for Claude Code** - Never lose context again!

## 🎯 Overview

This workspace demonstrates an automated system for maintaining context and progress across Claude Code sessions. The repository provides:
- **Session Continuity System**: Intelligent tracking, automated checkpointing, and seamless resumption
- **Organized Workspace**: Clean project structure with session management at the root
- **Multi-Project Support**: Work across multiple projects with automatic context switching

## ✨ Key Features

- 🤖 **Git Hook Automation** - Automatic checkpoints on every commit
- 💾 **Smart Session Capture** - Detects file changes, decisions, and next steps
- 🔍 **Multi-Project Tracking** - Session index tracks all projects in workspace
- 📊 **Hybrid Format** - Human-readable Markdown logs + machine-readable JSON checkpoints
- 🔄 **Seamless Resumption** - Start new sessions with full context from previous work
- ⚠️ **Context Awareness** - Warns when context window fills up (75%, 87%, 95%)
- 📝 **Decision Logging** - Tracks architectural decisions with rationale and alternatives
- 🔗 **Dependency Analysis** - Cross-file dependency tracking with impact scoring

## 🚀 Quick Start

### Save Your Current Session

```bash
python scripts/checkpoint.py --quick
```

This automatically:
- ✅ Detects all file changes (git + filesystem)
- ✅ Analyzes dependencies and impact
- ✅ Generates session description
- ✅ Suggests resume points and next steps
- ✅ Creates checkpoint + log files
- ✅ Updates CLAUDE.md

### Resume in New Session

```bash
python scripts/resume-session.py
```

This displays:
- Previous session summary
- What was completed
- Where to resume
- Next steps to take

### Check Context Usage

```bash
python scripts/context-monitor.py
```

Monitors your conversation and warns before hitting context limits.

### Install Git Hooks (One-Time)

```bash
python scripts/install-hooks.py
```

Enables automatic checkpoint creation after every commit.

## 📁 Directory Structure

### Projects/
Active development projects organized by purpose:

- **api-documentation-agent/** - Automated API documentation system
  - Backend: FastAPI application with WebSocket support
  - Frontend: React + TypeScript dashboard
  - Docs: Comprehensive documentation
  - See `Projects/api-documentation-agent/README.md` for details

- **Other projects** tracked as separate git repositories

### Scripts/
Session management and automation tools:

**Core Tools:**
- `checkpoint.py` - Unified checkpoint command (use this!)
- `resume-session.py` - Resume from last Claude session
- `context-monitor.py` - Track context window usage
- `session-logger.py` - Session logging utilities

**Automation:**
- `install-hooks.py` - Git hook installation
- `post-commit-handler.py` - Auto-checkpoint on commit
- `setup-automation.ps1` - Configure Claude Code hooks
- `setup-task-scheduler.ps1` - Periodic safety net checkpoints

**Analysis:**
- `dependency_analyzer.py` - Cross-file dependency tracking
- `resume_point_generator.py` - Smart resume point generation
- `project_tracker.py` - Multi-project session tracking

**Utilities:**
- `save-session.py` - Manual session capture
- `update-session-state.py` - Sync CLAUDE.md with checkpoints
- `checkpoint_utils.py` - Reusable checkpoint utilities
- `checkpoint_schema.py` - Checkpoint validation
- `session_index.py` - Multi-project session index
- `path_resolver.py` - Cross-platform path resolution
- `migrate-checkpoints.py` - Checkpoint format migration

### .claude-sessions/
Session checkpoints and logs (managed automatically):
- `checkpoints/` - JSON session checkpoints
- `logs/` - Markdown session logs
- `dependency_cache/` - Cached dependency analysis
- `sessions.index` - Multi-project session index
- `README.md` - Session system documentation

### Codebases/
Reference codebases and archived projects (not tracked in git)

### Root Configuration Files
- **CLAUDE.md** - Project memory file for Claude Code
- **SESSION_PROTOCOL.md** - Comprehensive instructions for Claude
- **.gitignore** - Excludes system directories, Projects/, Codebases/
- **.claude/settings.json** - Claude Code hook configuration

## 📚 Documentation

### Quick References
- **QUICK_STATUS.md** - 3-minute overview of recent workspace organization
- **NEXT_STEPS.txt** - Immediate action items
- **EXECUTIVE_FINAL_REPORT.md** - Comprehensive remediation report

### Session System Docs
- **SESSION_PROTOCOL.md** - Full instructions for Claude Code
- **MULTI_PROJECT_SESSION_TRACKING_COMPLETE.md** - Multi-project feature details
- **GIT_HOOK_WORKFLOW.md** - Git hook automation explained
- **SESSION_CONTINUITY_IMPLEMENTATION_COMPLETE.md** - Implementation details

### Phase Documentation
- **PHASE1_PROJECT_IDENTITY_COMPLETE.md** - Project detection system
- **PHASE2_PROJECT_SWITCH_DETECTION_COMPLETE.md** - Context switching
- **PHASE3_SESSION_INDEX_COMPLETE.md** - Global session index

### Advanced Features
- **docs/DEPENDENCY_TRACKING.md** - Cross-file dependency analysis
- **docs/AUTOMATION.md** - Automation setup and configuration
- **docs/AI_DRIVEN_DEVELOPMENT_CONTINUITY.md** - System architecture
- **docs/EXECUTIVE_SUMMARY.md** - Feature overview and roadmap

## 🛠️ Advanced Usage

### Automated Session Continuity

Set up once for zero-manual-work experience:

```bash
# Windows
.\scripts\setup-automation.ps1

# Unix/Mac
./scripts/setup.sh
```

This configures:
- **SessionStart hook** → Auto-runs `resume-session.py` when Claude starts
- **SessionEnd hook** → Auto-runs `checkpoint.py` when Claude exits
- **Git post-commit hook** → Auto-creates checkpoint after each commit

### Multi-Project Workflow

The system automatically detects which project you're working in:

```bash
# List all sessions across all projects
python scripts/resume-session.py list

# Resume last session for current project
python scripts/resume-session.py

# View session index
cat .claude-sessions/sessions.index
```

### Dependency Analysis

Analyze cross-file dependencies with impact scoring:

```bash
# Full dependency analysis (default)
python scripts/checkpoint.py --quick

# Skip dependencies for speed
python scripts/checkpoint.py --quick --skip-dependencies

# Analyze specific files
python scripts/dependency_analyzer.py path/to/file.py
```

### Context Window Monitoring

Stay aware of context usage to avoid losing work:

```bash
# Check current context usage
python scripts/context-monitor.py

# Set up monitoring daemon (advanced)
python scripts/auto-checkpoint-daemon.py
```

## 🔧 System Requirements

- Python 3.9+
- Git
- Windows PowerShell (for `.ps1` scripts) or Bash (for `.sh` scripts)
- Claude Code (for session continuity features)

## 📊 Project Status

**Status:** ✅ Production Ready

- 100% test pass rate (68 comprehensive tests)
- Git hooks operational
- Multi-project tracking functional
- Dependency analysis implemented
- Documentation complete

## 🤝 How Claude Code Uses This

When Claude Code starts in this workspace:
1. Reads `CLAUDE.md` for project memory and current state
2. Can run `resume-session.py` to load previous session details
3. Uses `SESSION_PROTOCOL.md` as reference for best practices
4. Automatically creates checkpoints via git hooks
5. Tracks decisions and progress in session logs

## 📝 Recent Updates

**November 2025:**
- Merged workspace organization with session continuity system
- Resolved script conflicts (preserved critical bug fixes)
- Added comprehensive documentation
- Implemented git hook-based automation
- Achieved 100% test pass rate

## 🔗 Related Projects

This workspace contains multiple projects:
- **Context Tracking System** (this repo) - Session continuity
- **API Documentation Agent** (Projects/) - API automation tools
- See individual project READMEs for details

## 📄 License

See individual project directories for licensing information.

---

**Questions?** Check `CLAUDE.md` for project memory or `SESSION_PROTOCOL.md` for detailed instructions.
