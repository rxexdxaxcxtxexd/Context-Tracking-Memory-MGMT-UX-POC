# Checkpoint to claude-mem Migration Mapping

**Generated:** 2025-12-15
**Purpose:** Define how checkpoint data maps to claude-mem observations

---

## Overview

This document defines the migration strategy for converting checkpoint JSON data to claude-mem observations. The goal is to preserve high-value historical data while discarding redundant or low-value information.

## Migration Principles

1. **Preserve Decisions:** All architectural and implementation decisions must be migrated
2. **Maintain Context:** Resume points and problem tracking provide valuable continuity
3. **Selective File Changes:** Only migrate significant file change events (>= 5 files or major features)
4. **Project Boundaries:** Respect project boundaries and track multi-project history
5. **Deduplication:** Avoid duplicate observations from overlapping checkpoints

---

## High-Value Fields (MUST MIGRATE)

### 1. Decisions → `observation` type: "decision"

**Checkpoint Schema:**
```json
{
  "decisions": [
    {
      "timestamp": "2025-11-12T17:03:31.998442",
      "question": "Which logging library to use?",
      "decision": "Use built-in logging module",
      "rationale": "Built-in module is sufficient for our needs",
      "alternatives_considered": ["loguru", "structlog"]
    }
  ]
}
```

**claude-mem Observation:**
```json
{
  "type": "decision",
  "content": "Decision: Use built-in logging module for logging. Rationale: Built-in module is sufficient for our needs. Alternatives considered: loguru, structlog.",
  "metadata": {
    "question": "Which logging library to use?",
    "decision": "Use built-in logging module",
    "alternatives": ["loguru", "structlog"],
    "source": "checkpoint_migration",
    "checkpoint_timestamp": "2025-11-12T17:03:31.998442"
  },
  "timestamp": "2025-11-12T17:03:31.998442"
}
```

**Migration Rules:**
- Combine question, decision, rationale into content field
- Preserve alternatives_considered in metadata
- Use original checkpoint timestamp

---

### 2. Resume Points → `observation` type: "resume_context"

**Checkpoint Schema:**
```json
{
  "resume_points": [
    "Continue with Task 2 implementation",
    "[!] payment.py is used by 12 files - test thoroughly"
  ]
}
```

**claude-mem Observation:**
```json
{
  "type": "resume_context",
  "content": "Resume Point: Continue with Task 2 implementation",
  "metadata": {
    "priority": "normal",
    "source": "checkpoint_migration",
    "checkpoint_session_id": "2a45e4b8"
  }
}
```

**Migration Rules:**
- Create one observation per resume point
- Detect priority markers: `[!]` = high priority
- Preserve session_id context for traceability
- Skip generic resume points (e.g., "Review newly created files")

---

### 3. Problems Encountered → `observation` type: "problem"

**Checkpoint Schema:**
```json
{
  "problems_encountered": [
    {
      "timestamp": "2025-11-12T18:00:00",
      "description": "API timeout issues with external service",
      "resolution": "Added retry logic with exponential backoff",
      "status": "resolved"
    }
  ]
}
```

**claude-mem Observation:**
```json
{
  "type": "problem",
  "content": "Problem: API timeout issues with external service. Resolution: Added retry logic with exponential backoff. Status: resolved",
  "metadata": {
    "status": "resolved",
    "source": "checkpoint_migration",
    "checkpoint_timestamp": "2025-11-12T18:00:00"
  }
}
```

**Migration Rules:**
- Combine description, resolution, status into content
- Only migrate resolved or documented problems (skip vague entries)
- Preserve problem status in metadata

---

### 4. Significant File Changes → `observation` type: "code_session"

**Checkpoint Schema:**
```json
{
  "file_changes": [
    {
      "file_path": "src/payment/processor.py",
      "action": "created",
      "timestamp": "2025-11-12T17:00:00",
      "description": "Implemented payment processing logic"
    },
    {
      "file_path": "src/payment/validator.py",
      "action": "created",
      "timestamp": "2025-11-12T17:05:00",
      "description": "Added payment validation"
    }
  ],
  "context": {
    "description": "Phase 2 complete: Payment module implemented"
  }
}
```

**claude-mem Observation:**
```json
{
  "type": "code_session",
  "content": "Phase 2 complete: Payment module implemented. Created 2 files: src/payment/processor.py (payment processing logic), src/payment/validator.py (payment validation)",
  "metadata": {
    "file_count": 2,
    "files_created": ["src/payment/processor.py", "src/payment/validator.py"],
    "source": "checkpoint_migration",
    "checkpoint_session_id": "2a45e4b8"
  }
}
```

**Migration Rules:**
- **Threshold:** Only migrate if file_changes.length >= 5 OR has meaningful description
- Summarize file changes (don't list every file)
- Prioritize created/modified over filesystem noise
- Skip auto-generated files (.claude/, temp files, etc.)

---

## Medium-Value Fields (MIGRATE SELECTIVELY)

### 5. Completed Tasks → `observation` type: "achievement"

**Checkpoint Schema:**
```json
{
  "completed_tasks": [
    {
      "description": "Implement user authentication",
      "status": "completed",
      "completed_at": "2025-11-12T17:30:00",
      "notes": "OAuth2 integration complete"
    }
  ]
}
```

**claude-mem Observation:**
```json
{
  "type": "achievement",
  "content": "Completed: Implement user authentication. Notes: OAuth2 integration complete",
  "metadata": {
    "source": "checkpoint_migration",
    "completed_at": "2025-11-12T17:30:00"
  }
}
```

**Migration Rules:**
- Only migrate tasks with meaningful descriptions (not generic TODOs)
- Skip tasks without notes or context
- Combine with related file changes if possible

---

### 6. Pending Tasks → `observation` type: "todo"

**Checkpoint Schema:**
```json
{
  "pending_tasks": [
    {
      "description": "Write tests for payment module",
      "status": "pending",
      "created_at": "2025-11-12T17:00:00",
      "notes": "Focus on edge cases"
    }
  ]
}
```

**claude-mem Observation:**
```json
{
  "type": "todo",
  "content": "TODO: Write tests for payment module. Focus on edge cases",
  "metadata": {
    "status": "pending",
    "source": "checkpoint_migration",
    "created_at": "2025-11-12T17:00:00"
  }
}
```

**Migration Rules:**
- Only migrate if still relevant (check against newer checkpoints)
- Skip generic TODOs ("Run tests", "Review code")
- Prioritize tasks with specific context

---

### 7. Context Descriptions → Metadata Enhancement

**Checkpoint Schema:**
```json
{
  "context": {
    "project": {
      "name": "api-documentation-agent",
      "git_branch": "main",
      "git_remote_url": "https://github.com/..."
    },
    "description": "Phase 3: Implementing SDK generation pipeline"
  }
}
```

**Usage:**
- Attach to related observations as metadata
- Use for observation grouping/filtering
- Track project context across sessions

**Migration Rules:**
- Extract manual descriptions (not "Auto: Idle trigger")
- Link to file changes or decisions when possible

---

## Low-Value Fields (SKIP MIGRATION)

### 8. Session Metadata (Metadata Only)

**Skip these fields:**
- `session_id` - Only use in metadata for traceability
- `timestamp` - Use as observation timestamp, not separate observation
- `started_at` - Low value for long-term memory
- `current_task` - Transient, not historical value

### 9. Generic Next Steps (Skip)

**Skip these:**
```json
{
  "next_steps": [
    "Run full test suite to ensure no regressions",
    "Review newly created files for completeness",
    "Verify all changes work as expected"
  ]
}
```

**Reason:** Generic boilerplate with no specific context

### 10. Auto-Generated File Changes (Skip)

**Skip these file patterns:**
- `.claude/` - Internal tracking
- `AppData/` - System files
- `node_modules/` - Dependencies
- Temp files, lock files, cache files
- Files with "Auto-detected via filesystem" and no meaningful description

---

## Migration Workflow

### Phase 1: Priority 1 (Last 90 Days)
1. Parse all checkpoints from last 90 days
2. Extract high-value fields (decisions, problems, resume points)
3. Merge related observations (same session, similar content)
4. Deduplicate across checkpoints
5. Generate claude-mem observations

### Phase 2: Priority 2 (High-Value Older)
1. Parse high-value older checkpoints (file_changes >= 10, has decisions, etc.)
2. Apply same extraction rules as Priority 1
3. Focus on decisions and major milestones

### Phase 3: Validation
1. Check for duplicate observations
2. Verify project boundaries
3. Test observation retrieval

---

## Deduplication Strategy

### Problem: Multiple checkpoints may contain similar data

**Solution:**
1. **Session-based grouping:** Group checkpoints by session_id
2. **Content hashing:** Hash observation content to detect duplicates
3. **Timestamp windows:** Merge observations within 5-minute windows
4. **Priority rules:** Keep most detailed version when duplicates found

---

## Observation Schema Template

```json
{
  "type": "decision|resume_context|problem|code_session|achievement|todo",
  "content": "Human-readable summary combining relevant checkpoint fields",
  "metadata": {
    "source": "checkpoint_migration",
    "checkpoint_session_id": "2a45e4b8",
    "checkpoint_timestamp": "2025-11-12T17:03:31.998442",
    "project": {
      "name": "api-documentation-agent",
      "git_branch": "main"
    },
    "priority": "high|normal|low",
    // Type-specific metadata
    "decision": "...",
    "alternatives": ["..."],
    "status": "...",
    "file_count": 5
  },
  "timestamp": "2025-11-12T17:03:31.998442"
}
```

---

## Migration Metrics

**Target:**
- Priority 1 (90 days): ~150-200 checkpoints → ~300-500 observations
- Priority 2 (high-value): ~50 checkpoints → ~100-200 observations
- **Total:** ~400-700 observations

**Estimated reduction:** 1,810 checkpoints → 400-700 observations (60-80% reduction)

---

## Next Steps

1. Run `analyze_checkpoints.py` to generate statistics
2. Review sample checkpoints in `.claude/sample-checkpoints/`
3. Create migration script (`scripts/migrate_checkpoints.py`)
4. Test migration on Priority 1 checkpoints
5. Validate observations in claude-mem
6. Full migration of Priority 1 + Priority 2
7. Archive Priority 3 checkpoints

---

**End of Migration Mapping**
