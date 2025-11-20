# Development Workspace

## Overview
This is Layden's primary development workspace with organized project structure and automated session continuity.

## Directory Structure

### Projects/
Active development projects organized by purpose:

- **api-documentation-agent/** - Automated API documentation system (main project)
  - Backend: FastAPI application with WebSocket support
  - Frontend: React + TypeScript dashboard
  - Docs: Comprehensive documentation (architecture, testing, session system)
  - See `Projects/api-documentation-agent/README.md` for details

- **context-tracking-memory/** - Session continuity system for Claude Code
  - Git hook-based automatic checkpointing
  - Multi-project session tracking
  - See `Projects/context-tracking-memory/README.md` for details

- **screw-extraction/** - Data extraction utilities
- **video-transcription/** - Video processing tools
- **web-demos/** - Demo applications

### Scripts/
Global session management scripts (14 files):
- `resume-session.py` - Resume from last Claude session
- `save-session.py` - Create session checkpoint
- `session-logger.py` - Session logging utilities
- `update-session-state.py` - Sync CLAUDE.md with checkpoints
- `checkpoint_utils.py` - Reusable checkpoint utilities
- `post-commit-handler.py` - Git hook automation
- `install-hooks.py` - Git hook installation tool
- And more...

### .claude-sessions/
Session checkpoints and logs (managed automatically by context-tracking-memory)
- `checkpoints/` - JSON session checkpoints
- `logs/` - Markdown session logs
- `sessions.index` - Multi-project session index

### Codebases/
Reference codebases and archived projects

### CLAUDE.md
Project memory file for Claude Code - maintains context across sessions

## Quick Start

### Resume Previous Session
```bash
python scripts/resume-session.py
```

### API Documentation Agent
```bash
cd Projects/api-documentation-agent
# See README.md in that directory for setup
```

### Context Tracking System
```bash
cd Projects/context-tracking-memory
# See SESSION_PROTOCOL.md for usage
```

## Recent Changes (2025-11-20)

**Major Reorganization:**
- All project files moved from root into Projects/ subdirectories
- Documentation organized into docs/ folders
- Test files moved to test-data/ directories
- Comprehensive .gitignore created
- All hard-coded paths fixed for dynamic resolution

See `CLAUDE.md` Integration Map section for complete structure details.

## Environment Setup

### API Documentation Agent
Requires `ANTHROPIC_API_KEY` environment variable:
```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "your-key-here"

# Windows Command Prompt
set ANTHROPIC_API_KEY=your-key-here

# Linux/macOS
export ANTHROPIC_API_KEY="your-key-here"
```

See `Projects/api-documentation-agent/ENVIRONMENT_SETUP_QUICKSTART.md` for details.

## Git Repository

This workspace is tracked in git (branch: master)
- Personal folders ignored (Documents, Music, Videos, etc.)
- Cache directories ignored (.cache, .nuget, .docker, etc.)
- Environment files protected (.env)

## Backup & Safety

**Backup branch created:** `backup-pre-remediation-2025-11-20`
**Backup tag:** `reorganization-backup`

To restore if needed:
```bash
git checkout backup-pre-remediation-2025-11-20
```

## Project Features

### API Documentation Agent
- Automated OpenAPI documentation generation
- Multi-language SDK generation (Python, JavaScript, Java, 14+ languages)
- Property-based API testing with Schemathesis
- FastAPI backend with WebSocket support
- React + TypeScript dashboard with virtual scrolling
- Production-ready with Docker, PostgreSQL, Prometheus monitoring

### Context Tracking System
- Automatic session checkpointing via git hooks
- Multi-project session tracking
- Intelligent resume point generation
- Cross-file dependency analysis
- Context window monitoring
- Seamless Claude Code integration

## Common Commands

### Session Management
```bash
# Resume last session
python scripts/resume-session.py

# List all sessions
python scripts/resume-session.py list

# Quick summary
python scripts/resume-session.py summary

# Save current session
python scripts/save-session.py --quick

# Update CLAUDE.md
python scripts/update-session-state.py update
```

### API Documentation Agent
```bash
cd Projects/api-documentation-agent

# Start backend (simple mode, recommended)
cd backend && python start_backend.py

# Start frontend
cd frontend && npm run dev

# Run full pipeline
python -c "
import asyncio
from src.core.pipeline import APIDocumentationPipeline
from pathlib import Path

async def test():
    pipeline = APIDocumentationPipeline()
    success, results = await pipeline.execute_full_pipeline(
        spec_path=Path('specs/petstore.yaml'),
        output_dir=Path('output'),
        target_languages=['python']
    )
    print(f'Success: {success}')

asyncio.run(test())
"
```

## Development Principles

### Session Continuity
- Always create checkpoints before closing sessions
- Document architectural decisions with rationale
- Update CLAUDE.md with session progress
- Use git hooks for automatic checkpointing

### Code Organization
- Projects separated by purpose
- Documentation organized by category
- Tests colocated with source or in test-data/
- Scripts use dynamic path resolution (no hardcoded paths)

### Security Best Practices
- Environment variables for API keys (never hardcode)
- .gitignore protects sensitive files
- Input validation at multiple layers
- Security headers and rate limiting

## Troubleshooting

### Session Scripts Not Working
```bash
# Verify Python environment
python --version  # Should be 3.9+

# Check script location
ls scripts/resume-session.py
```

### API Documentation Agent Issues
See `Projects/api-documentation-agent/TROUBLESHOOTING_GUIDE.md` or `Projects/api-documentation-agent/docs/TROUBLESHOOTING_GUIDE.md`

### Context Tracking Issues
See `Projects/context-tracking-memory/README.md` or `Projects/context-tracking-memory/SESSION_PROTOCOL.md`

## Documentation

### Root Documentation
- `CLAUDE.md` - Project memory and session continuity
- `README.md` - This file (workspace overview)

### API Documentation Agent
- `Projects/api-documentation-agent/README.md` - Project overview
- `Projects/api-documentation-agent/ENVIRONMENT_SETUP_QUICKSTART.md` - Environment setup
- `Projects/api-documentation-agent/docs/` - Comprehensive documentation
  - `architecture/` - Architecture and design docs
  - `testing/` - Testing and QA guides
  - `session-system/` - Session continuity system docs
  - `production/` - Deployment and API docs

### Context Tracking System
- `Projects/context-tracking-memory/README.md` - Quick start guide
- `Projects/context-tracking-memory/SESSION_PROTOCOL.md` - Complete protocol
- `Projects/context-tracking-memory/docs/` - Phase documentation

## Contributing

When making changes:
1. Create feature branch from master
2. Update relevant documentation
3. Test changes thoroughly
4. Create checkpoint before committing
5. Submit pull request with clear description

## License

This workspace contains research projects exploring hybrid AI + open source development workflows.

---

**Built with Claude Code for seamless AI-assisted development**
