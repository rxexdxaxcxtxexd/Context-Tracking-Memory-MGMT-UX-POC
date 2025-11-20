# API Documentation Agent - Project Memory

## Project Overview
This project creates an automated API documentation system using Claude Code to orchestrate open source tools for SDK generation, testing, and documentation creation.

---

## Instructions for Claude Code

**IMPORTANT:** These instructions are for Claude to follow during sessions. Read and follow these at session start.

### Session Start Protocol

**When user requests substantial work:**
1. **Ask**: "Would you like me to track this session for continuity?"
2. **If yes**: Initialize SessionLogger and track progress automatically
3. **If no**: Proceed without session tracking

**What qualifies as "substantial work":**
- Multiple related tasks (3+ steps)
- Feature implementation or refactoring
- Debugging investigations requiring multiple attempts
- Architecture decisions
- Work spanning multiple files
- Any work that would benefit from resuming later

**What does NOT need tracking:**
- Simple one-off questions
- Single file edits
- Quick information lookups
- Trivial bug fixes
- Explanatory responses

### During Work (When Tracking Enabled)

**1. Initialize logger at start:**
```python
# Import and initialize
import sys, os, importlib.util
spec = importlib.util.spec_from_file_location("session_logger",
    os.path.join(os.path.dirname(__file__), "scripts/session-logger.py"))
session_logger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(session_logger)
logger = session_logger.SessionLogger()

# Start session with description
logger.start_session("Feature: Dark mode toggle", context={
    "project": "api-documentation-agent",
    "type": "feature",
    "priority": "high"
})
```

**2. Log as you work:**
- `logger.add_task("Task description", "pending")` - When starting new tasks
- `logger.update_current_task("Task description")` - When switching tasks
- `logger.complete_task("Task description", "Notes")` - When finishing
- `logger.log_decision(question, decision, rationale, alternatives)` - For architectural choices
- `logger.log_file_change(file_path, action, description)` - After file modifications
- `logger.add_problem("Problem description")` - When encountering blockers

**3. Provide visibility:**
Show user progress markers like "✓ Task completed: Design toggle component"

### Session End Protocol

**If significant work was completed** (4+ tasks, important decisions, or multiple files changed):

1. **Remind user:**
   - "I've completed [X] tasks with [Y] key decisions. Shall I create a session checkpoint?"

2. **If user agrees, run end-of-session sequence:**
```python
# Add resume points
logger.add_resume_point("Continue with state management implementation")
logger.add_resume_point("Update existing components to use theme context")

# Add next steps
logger.add_next_step("Complete Context API setup")
logger.add_next_step("Test dark mode in all components")

# End session (creates checkpoint and log)
logger.end_session()
```

3. **Suggest automated collection:**
   - "You can also run `python scripts/save-session.py` to capture any details I may have missed"

### Context Window Awareness

**Monitor context usage and warn proactively:**

- **At ~150K tokens (75% full):**
  - "ℹ️ Context window is 75% full. Consider checkpointing soon to preserve our work."

- **At ~175K tokens (87% full):**
  - "⚠️ Context window is 87% full. I recommend creating a checkpoint now before we lose context."
  - Offer: "Shall I create a checkpoint of our progress?"

- **At ~190K tokens (95% full):**
  - "🚨 Context window is 95% full. Please run `python scripts/save-session.py` immediately to preserve work."
  - "We should start a fresh session after checkpointing."

**Recommended user action:**
1. Run: `python scripts/save-session.py` (auto-collects session data)
2. Start fresh Claude Code session
3. Resume with: `python scripts/resume-session.py`

### Best Practices

1. **Be proactive but not intrusive:**
   - Ask about tracking once at start
   - Don't repeatedly ask or mention it during work
   - Remind about checkpointing when appropriate

2. **Provide clear markers:**
   - Show completed task notifications
   - Mention when decisions are logged
   - Summarize progress at end

3. **Respect user preferences:**
   - If user declines tracking, don't bring it up again
   - If user wants minimal interruption, track silently
   - If user wants visibility, provide status updates

---

## Session Continuity Protocol

**Purpose:** Maintain context and progress across Claude Code sessions.

### For Claude at Session Start
1. **Read this file first** (automatically loaded via project instructions)
2. **Check for checkpoints:** Run `python scripts/resume-session.py` to see latest session state
3. **Review Current Session State** section below for active work
4. **Confirm with user** which resume point to continue from
5. **Update session state** as work progresses

### For Claude at Session End
1. **Create checkpoint:** Use `session-logger.py` to log progress
2. **Update this file:** Run `python scripts/update-session-state.py` to sync state
3. **Document resume points:** Clearly state where next session should continue
4. **Log decisions:** Record any architectural or implementation choices made
5. **List next steps:** Provide clear continuation path

### Session Handoff Checklist
- [ ] Checkpoint file created (`.claude-sessions/checkpoints/`)
- [ ] Session log written (`.claude-sessions/logs/`)
- [ ] CLAUDE.md Current Session State updated
- [ ] Resume points documented
- [ ] Next steps listed
- [ ] Decisions logged
- [ ] File changes recorded

---

## Current Session State

**Last Updated:** 2025-11-14 16:46:54
**Session ID:** 2ff71d3e

### Resume Points
1. --- Impact Analysis: Low-impact changes ---
2. --- Code-Level Resume Points ---
3. Verify configuration changes in .claude.json
4. Review 114 newly created file(s) for completeness

### Next Steps
- [ ] Run full test suite to ensure no regressions
- [ ] Review newly created files for completeness
- [ ] Verify all changes work as expected

### Recent Changes
- ➕ `vtt_to_text.py`
- ➕ `whisper_api_transcribe.py`
- ✏️ `AppData\LocalLow\71d60027aa32c9ce57308173361ee97337a80d0e4a325830ea0a0101a8ba86b2`
- ✏️ `AppData\LocalLow\f25770e46184dbdc54ad3f05b4a0935425f7965c22705361525b2dd8623bab6a`
- ✏️ `OneDrive - Cornerstone Solutions Group\Desktop\Comet.lnk`

## Integration Map

### Project Structure
The directory is now **cleanly organized** with session tracking at root and all projects under `Projects/`:

#### 1. Root Directory (`C:\Users\layden\`)
**Purpose:** Session continuity and workspace management only
**Key Files:**
- `CLAUDE.md` - This file, serving as persistent project memory
- `.claude-sessions/` - Session logs and checkpoints
- `.claude.json` - Claude workspace configuration
- `.gitignore` - Comprehensive ignore rules for system/personal files
- `scripts/` - Session management scripts (14 scripts)
  - `session-logger.py` - Create session logs and checkpoints
  - `update-session-state.py` - Sync CLAUDE.md with checkpoints
  - `resume-session.py` - Load and display session state
  - `project_tracker.py` - Multi-project tracking
  - `checkpoint_utils.py` - Checkpoint utilities
  - And more...
- Personal folders (Documents/, Music/, Videos/, etc.) - Ignored in git

#### 2. Projects Directory (`C:\Users\layden\Projects\`)
**Purpose:** All development projects, organized by project type

##### API Documentation Agent (`Projects/api-documentation-agent/`)
**Status:** Fully implemented and production-ready
**Structure:**
```
api-documentation-agent/
├── backend/              # FastAPI application with WebSocket support
├── frontend/             # React + TypeScript dashboard
├── src/                  # Core implementation (validators, generators, core modules)
├── config/               # Configuration files (pipeline.yaml, openapitools.json)
├── docker/               # Containerization configurations
├── monitoring/           # Prometheus + Grafana setup
├── docs/                 # Comprehensive documentation (NEW)
│   ├── architecture/     # Planning & design docs (10 files)
│   ├── testing/          # QA & testing guides (7 files)
│   └── session-system/   # Session continuity docs (10 files)
├── scripts/
│   └── workflows/        # PowerShell automation scripts (6 files)
├── test-data/            # Test files and artifacts
├── archive/              # Archived SDK builds
└── README.md             # Project README
```

##### Other Projects
- **`Projects/screw-extraction/`** - Screw data extraction tools (Python scripts + Excel data + SCREWPOC git repo)
- **`Projects/video-transcription/`** - Video transcription utilities (7 Python/PowerShell scripts)
- **`Projects/web-demos/`** - Demo applications (uap-demo, uap-ui-demo, conversion-agents, sheepvader)
- **`Projects/context-tracking-memory/`** - Existing context tracking project

#### 3. Codebases Directory (`C:\Users\layden\Codebases\`)
**Purpose:** Reference codebases and API sources
- `CB Codebases/` - Cornerstone codebases
- `Web API/` - Web API projects

### When to Use Which
- **Root (C:\Users\layden\):** Only for CLAUDE.md, session tracking, and global scripts
- **Projects/api-documentation-agent/:** Primary working project - all implementation and documentation
- **Projects/[other]/:** Separate standalone projects
- **Codebases/:** Reference materials, not active development

### Recent Reorganization (2025-11-20)
All loose files from root have been organized into appropriate project directories:
- 27 markdown documentation files → `Projects/api-documentation-agent/docs/`
- 6 PowerShell scripts → `Projects/api-documentation-agent/scripts/workflows/`
- Test files and artifacts → `Projects/api-documentation-agent/test-data/`
- Separate projects moved to dedicated directories under `Projects/`
- Comprehensive .gitignore created to hide system/personal directories

---

## Decision Log

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

---


### Which CLAUDE.md location to use?
**Date:** 2025-11-13
**Decision:** Root directory (C:\Users\layden\CLAUDE.md)
**Rationale:** Keeps project memory close to working directory and separate from implementation details
**Alternatives Considered:**
- Projects directory
- Both locations


### What format for session logs?
**Date:** 2025-11-13
**Decision:** Hybrid approach - Markdown for humans, JSON for machines
**Rationale:** Provides best of both worlds: human-readable logs and machine-parseable checkpoints
**Alternatives Considered:**
- JSON only
- Markdown only


### How to manage session continuity?
**Date:** 2025-11-13
**Decision:** Script-based with manual/automated triggers
**Rationale:** Flexible, debuggable, can be integrated into workflows later
**Alternatives Considered:**
- Automated hooks
- Manual markdown updates


### How to handle Windows encoding issues?
**Date:** 2025-11-13
**Decision:** Disable rich output on Windows, use ASCII-friendly formatting
**Rationale:** Prevents UnicodeEncodeError with emoji characters in Windows console
**Alternatives Considered:**
- Force UTF-8
- Remove all special characters
## Architecture Principles
- **Hybrid Approach**: Combine AI efficiency with traditional tool reliability
- **Modularity**: Each tool serves a specific purpose with clear interfaces
- **Quality Gates**: Automated validation at every step
- **Scalability**: Design for enterprise deployment patterns
- **Session Continuity**: Maintain context across Claude Code sessions

---

## Tool Stack Configuration

### Primary Tools (Phase 1)
- **OpenAPI Generator**: SDK and client library generation
- **Redoc**: Interactive API documentation
- **Schemathesis**: Property-based API testing
- **Step CI**: Declarative integration testing

### Secondary Tools (Phase 2)
- **Kiota**: Strongly-typed client generation
- **RESTler**: Advanced stateful API fuzzing
- **Microcks**: Service virtualization and contract testing

### Session Management Tools
- **session-logger.py**: Create session checkpoints and logs
- **update-session-state.py**: Sync CLAUDE.md with session progress
- **resume-session.py**: Load and display previous session state

---

## Key Workflows

### Documentation Generation
1. Validate OpenAPI specification
2. Generate interactive docs with Redoc
3. Create SDK clients with OpenAPI Generator
4. Run property-based tests with Schemathesis
5. Execute integration tests with Step CI
6. Package and deploy artifacts

### Session Continuity Workflow
1. **Session Start:**
   - Check latest checkpoint with `resume-session.py`
   - Review Current Session State in this file
   - Confirm continuation point with user

2. **During Session:**
   - Log progress using `session-logger.py` APIs
   - Update Current Session State as work progresses
   - Document decisions in Decision Log

3. **Session End:**
   - Create checkpoint with `session-logger.py`
   - Update CLAUDE.md with `update-session-state.py`
   - Document resume points and next steps

### Quality Assurance
- Specification validation before processing
- Generated code quality checks
- Security vulnerability scanning
- Performance benchmarking
- Documentation accuracy verification

---

## Common Commands

### API Documentation Commands
- `generate full-docs from specs/api.yaml` - Complete documentation pipeline
- `create python-sdk from specs/api.yaml` - Generate Python SDK
- `run api-tests against https://api.example.com` - Execute test suite
- `validate spec specs/api.yaml` - Check OpenAPI specification
- `deploy docs to staging` - Deploy documentation

### Session Management Commands
```bash
# Resume from last session
python scripts/resume-session.py

# List all checkpoints
python scripts/resume-session.py list

# Get quick summary
python scripts/resume-session.py summary

# Update CLAUDE.md from latest checkpoint
python scripts/update-session-state.py update

# Clear session state
python scripts/update-session-state.py clear

# Example: Using session logger in Python
from scripts.session_logger import SessionLogger
logger = SessionLogger()
logger.start_session("Working on feature X")
logger.add_task("Implement feature", "in_progress")
logger.log_decision("Question?", "Answer", "Rationale")
logger.end_session()
```

---

## Common Resumption Scenarios

### Scenario 1: Continuing Implementation Work
**Context:** You were implementing a feature when the session ended
**Resume Steps:**
1. Run `python scripts/resume-session.py` to see what was being worked on
2. Review the "Current Task" and "Recent Changes"
3. Check "Problems Encountered" for any blockers
4. Continue from the documented resume point
5. Update session state as you progress

### Scenario 2: Starting New Feature
**Context:** Beginning work on a new feature or task
**Resume Steps:**
1. Review Decision Log for relevant past decisions
2. Check Integration Map to understand project structure
3. Create new session with `session-logger.py`
4. Document your plan and start implementation
5. Log decisions as you make architectural choices

### Scenario 3: Debugging Issues
**Context:** Investigating problems or bugs
**Resume Steps:**
1. Check "Problems Encountered" in latest checkpoint
2. Review relevant file changes to understand recent modifications
3. Use Decision Log to understand why things were implemented a certain way
4. Document findings and solutions as you debug
5. Update session with problem resolution

### Scenario 4: Long Break Return
**Context:** Returning after days/weeks away from the project
**Resume Steps:**
1. Read the entire CLAUDE.md to refresh context
2. Run `python scripts/resume-session.py list` to see recent sessions
3. Review Decision Log to understand recent choices
4. Check Current Session State for active work
5. Ask user for clarification on priorities before continuing

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

## Error Handling
- Invalid specs should be rejected with clear error messages
- Failed generations should not corrupt existing artifacts
- All operations should be reversible
- Detailed logging for debugging and auditing
- **Session Recovery:** Checkpoints enable recovery from interruptions
- **State Consistency:** Always sync CLAUDE.md with checkpoint data

---

## Development Guidelines
- Use TypeScript for Node.js components
- Use Python 3.9+ for processing scripts
- Follow OpenAPI specification best practices
- Implement comprehensive error handling
- Include detailed documentation for all modules
- **Session Management:** Use provided scripts for continuity
- **Context Preservation:** Document decisions and rationale clearly
- **Checkpoint Frequency:** Create checkpoints at major milestones and session ends

---

## CI/CD Integration
- GitHub Actions for automation
- Docker containers for consistent environments
- Automated testing on pull requests
- Staging deployments for validation
- Production deployments with approval gates
- **Session Logs:** Consider integrating checkpoint creation into CI/CD pipelines
- **Audit Trail:** Use session logs for compliance and debugging
