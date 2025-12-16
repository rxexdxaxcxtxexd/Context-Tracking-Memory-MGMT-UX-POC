# Migration Guide: File-Based Checkpoints → claude-mem + Code Context

**Date:** 2025-12-15
**Status:** Phase 3 - Active Migration
**Migration Type:** Old checkpoint scripts → Automated hybrid system

---

## Overview

The session continuity system has migrated from manual file-based checkpoints to a fully automated hybrid system:

- **claude-mem plugin** - Automatic semantic memory capture
- **Code context layer** - Auto-generated technical documentation
- **Git hooks** - Zero-friction automation

**Result:** Zero manual work, better context preservation, semantic search across sessions.

---

## What Changed and Why

### Old System (Deprecated)
❌ **Manual checkpoint creation** via `checkpoint.py`
❌ **Manual session resume** via `resume-session.py`
❌ **File-based storage** in `~/.claude-sessions/`
❌ **No semantic search** - only keyword search through files
❌ **Heavy manual intervention** - had to remember to checkpoint

### New System (Current)
✅ **Automatic checkpoints** - created on every git commit
✅ **Automatic session start** - context loaded when Claude starts
✅ **Hybrid storage** - claude-mem (semantic) + code context (technical)
✅ **Semantic search** - use `/mem-search` to find anything from past sessions
✅ **Zero manual work** - fully automated via hooks

### Why Migrate?
1. **Reduce friction** - No more manual checkpoint commands
2. **Better search** - Semantic search vs keyword search
3. **Better preservation** - Both semantic context + technical details
4. **Cost-effective** - Optimized to $11.25/month (vs $38.25 default)
5. **Simpler architecture** - 2 layers vs 20+ scripts

---

## Command Migration Reference

### Creating Checkpoints

#### Old Way (Deprecated)
```bash
# Manual checkpoint
python scripts/checkpoint.py --quick

# With description
python scripts/checkpoint.py --description "Implemented auth system"

# Dry run preview
python scripts/checkpoint.py --dry-run
```

#### New Way (Current)
```bash
# Just commit your changes - checkpoint auto-created!
git add .
git commit -m "Implemented auth system"

# That's it! Post-commit hook automatically:
# 1. Creates checkpoint JSON
# 2. Generates .claude-code-context.md with dependencies
# 3. Updates session index
```

**Migration Note:** The `checkpoint.py` script now shows a deprecation warning. If you run it, you'll be prompted to use the new workflow instead.

---

### Resuming Sessions

#### Old Way (Deprecated)
```bash
# Display latest checkpoint
python scripts/resume-session.py

# List all checkpoints
python scripts/resume-session.py list

# Show concise summary
python scripts/resume-session.py summary

# Show tracked projects
python scripts/resume-session.py projects
```

#### New Way (Current)
```bash
# Just start Claude Code - context auto-loaded!
# SessionStart hook automatically displays recent context

# For semantic search of past sessions:
/mem-search authentication implementation
/mem-search database schema changes
/mem-search architectural decisions

# For technical details of latest commit:
# Read .claude-code-context.md (auto-updated on every commit)
```

**Migration Note:** The `resume-session.py` script now shows a deprecation warning. Session context is automatically displayed when you start Claude Code.

---

### Saving Session State

#### Old Way (Deprecated)
```bash
# Interactive save
python scripts/save-session.py

# Quick save
python scripts/save-session.py --quick

# With custom description
python scripts/save-session.py --description "Fixed auth bug"

# Dry run
python scripts/save-session.py --dry-run
```

#### New Way (Current)
```bash
# Just commit! Session state is saved automatically
git add .
git commit -m "Fixed auth bug"

# If you have uncommitted changes at session end:
# SessionEnd hook auto-generates code context for workspace state
# (happens automatically when you close Claude Code)
```

**Migration Note:** The `save-session.py` script now shows a deprecation warning. Session state is saved automatically on commit.

---

## New Workflow Reference

### Daily Workflow

**Morning (Session Start):**
1. Start Claude Code
2. SessionStart hook automatically displays:
   - Recent code context from `.claude-code-context.md`
   - Reminder about `/mem-search` for semantic queries

**During Work:**
1. Make code changes
2. Commit when ready:
   ```bash
   git add .
   git commit -m "Descriptive message"
   ```
3. Post-commit hook automatically:
   - Creates checkpoint
   - Generates code context with dependencies
   - No manual intervention needed

**Evening (Session End):**
1. Close Claude Code
2. SessionEnd hook automatically:
   - Generates code context for uncommitted changes (if any)
   - Logs session end
   - claude-mem captures observations

### Semantic Search Examples

```bash
# Find past implementations
/mem-search how did I implement authentication?

# Find architectural decisions
/mem-search why did we choose Redis over in-memory cache?

# Find bug discussions
/mem-search what was the solution for the CORS error?

# Find test strategies
/mem-search how should I test the payment integration?

# Find API changes
/mem-search what breaking changes were made to the API?
```

### Code Context File

The `.claude-code-context.md` file is auto-generated on every commit and contains:

```markdown
# Code Context (Auto-generated)

## Last Commit
- Hash: abc1234
- Branch: master
- Message: Implement authentication system

## Changed Files (5)
- [+] auth/login.py
- [M] api/routes.py
- [M] db/models.py

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

**Location:** `.claude-code-context.md` (in project root, gitignored)
**When updated:** On every git commit + on session end (if uncommitted changes)
**Purpose:** Technical snapshot for immediate context

---

## Hook Configuration

The new system uses three hooks configured in `.claude/settings.json`:

### SessionStart Hook
```json
{
  "hooks": {
    "SessionStart": {
      "command": "python scripts/session_start_bridge.py",
      "timeout": 10000
    }
  }
}
```

**What it does:**
- Displays recent code context from `.claude-code-context.md`
- Reminds about `/mem-search` for semantic queries
- Fast (<1 second)

### SessionEnd Hook
```json
{
  "hooks": {
    "SessionEnd": {
      "command": "python scripts/session_end_bridge.py",
      "timeout": 30000
    }
  }
}
```

**What it does:**
- Generates code context if uncommitted changes exist
- Logs session end for debugging
- Fast (<2 seconds)

### Git Post-Commit Hook
`.git/hooks/post-commit`:
```bash
#!/bin/bash
python "C:\Users\layden\scripts\post-commit-handler.py"
exit 0
```

**What it does:**
- Creates checkpoint JSON in `~/.claude-sessions/checkpoints/`
- Generates `.claude-code-context.md` with dependencies
- Never blocks git workflow (errors logged, always succeeds)

---

## Migration Checklist

If you're actively using the old checkpoint system, follow this checklist:

### Phase 1: Install claude-mem
- [ ] Add `"anthropic@claude-mem": true` to `.claude/settings.json`
- [ ] Restart Claude Code
- [ ] Test `/mem-search` works
- [ ] Verify observations are being captured

### Phase 2: Verify Code Context Layer
- [ ] Make code changes and commit
- [ ] Check that `.claude-code-context.md` was generated
- [ ] Verify dependency analysis is working
- [ ] Confirm git commits still work normally

### Phase 3: Transition Hooks (Current Phase)
- [ ] Verify `.claude/settings.json` has SessionStart/End hooks
- [ ] Test session start (code context displayed)
- [ ] Test session end (uncommitted changes handled)
- [ ] Confirm no new checkpoint files in `~/.claude-sessions/`

### Phase 4: Stop Using Old Commands (In Progress)
- [x] `checkpoint.py` shows deprecation warning
- [x] `save-session.py` shows deprecation warning
- [x] `resume-session.py` shows deprecation warning
- [ ] Use git commits instead of manual checkpoints
- [ ] Use `/mem-search` instead of `resume-session.py`

### Phase 5: Historical Data Migration (Upcoming)
- [ ] Last 90 days of checkpoints migrated to claude-mem
- [ ] High-value older checkpoints migrated
- [ ] Original checkpoints archived (not deleted)

---

## Troubleshooting

### "My checkpoints aren't being created anymore"
**Solution:** This is expected! Checkpoints are now created automatically on git commits. Just commit your changes and the checkpoint will be created automatically.

### "I don't see the code context file"
**Check:**
1. Did you commit your changes? (Context generated on commit)
2. Is `.claude-code-context.md` in your `.gitignore`? (It should be)
3. Check post-commit hook is installed: `ls .git/hooks/post-commit`

### "SessionStart hook isn't running"
**Check:**
1. Is the hook configured in `.claude/settings.json`?
2. Does `scripts/session_start_bridge.py` exist?
3. Is the script executable? (Windows: should just work; Unix: `chmod +x`)

### "I want to keep using the old checkpoint.py"
**Not recommended, but:** The old scripts still work if you press 'y' at the deprecation warning. However, they won't integrate with claude-mem and you'll miss out on semantic search.

### "How do I search my old checkpoints?"
**Phase 4 will migrate them!** The last 90 days + high-value checkpoints will be migrated to claude-mem, making them searchable with `/mem-search`. Original files will be archived (not deleted).

### "The deprecation warnings are annoying"
**Good!** That means the migration is working. The warnings are intentional to help you transition to the new workflow. Once you stop using the old scripts, you won't see them anymore.

---

## Benefits of New System

### Automation
- **Old:** Manual `checkpoint.py` before closing Claude
- **New:** Automatic on every commit + session end
- **Benefit:** Never forget to checkpoint

### Search
- **Old:** Keyword search through JSON files
- **New:** Semantic search with `/mem-search`
- **Benefit:** Find things by meaning, not exact keywords

### Context
- **Old:** Single checkpoint file with all data mixed
- **New:** Hybrid - semantic memory + technical code context
- **Benefit:** Both high-level understanding + technical precision

### Performance
- **Old:** Loading large checkpoint files takes time
- **New:** Lightweight context files, fast semantic search
- **Benefit:** Faster session start, faster search

### Maintenance
- **Old:** 20+ Python scripts (8,000+ LOC)
- **New:** 7 active scripts + claude-mem plugin
- **Benefit:** Simpler system, less to maintain

---

## FAQ

### Q: Can I still use the old checkpoint.py?
**A:** Yes, but not recommended. It shows a deprecation warning and won't integrate with claude-mem. You'll miss semantic search and automatic context loading.

### Q: What happens to my old checkpoints?
**A:** They'll be migrated in Phase 4 (upcoming). Last 90 days + high-value checkpoints will be imported into claude-mem. Original files will be archived in `~/.claude-sessions-archive/`.

### Q: How do I search across sessions now?
**A:** Use `/mem-search <query>` in Claude Code. Example: `/mem-search database schema changes`

### Q: What if I have uncommitted changes at session end?
**A:** SessionEnd hook automatically generates code context for your workspace state. When you commit later, it'll update the context.

### Q: Does this work across multiple projects?
**A:** Yes! The system tracks which project you're in (via git remote URL) and provides project-specific context.

### Q: How much does claude-mem cost?
**A:** Optimized to ~$11.25/month with 25 observations per context window. See `.claude/settings.json` for `CLAUDE_MEM_CONTEXT_OBSERVATIONS` setting.

### Q: Can I disable the deprecation warnings?
**A:** Not recommended, but you can edit the scripts and remove the `print_deprecation_warning()` calls. However, you should transition to the new workflow instead.

### Q: What if the migration breaks something?
**A:** Full rollback procedures exist. Run `scripts/rollback-to-pre-migration.sh` to restore the pre-migration state. Original checkpoint files are never deleted, only archived.

---

## Support

### Documentation
- **This guide:** `docs/MIGRATION_GUIDE.md`
- **Architecture:** `docs/ARCHITECTURE.md` (coming in Phase 5)
- **claude-mem guide:** `docs/CLAUDE_MEM_GUIDE.md` (coming in Phase 5)
- **Code context guide:** `docs/CODE_CONTEXT_GUIDE.md` (coming in Phase 5)

### Session Protocol
- **Old protocol:** `SESSION_PROTOCOL.md` (being updated in Phase 3D)
- **New protocol:** Will be updated to reflect claude-mem workflow

### Rollback
- **Emergency rollback:** `scripts/rollback-to-pre-migration.sh`
- **Backup location:** `~/.claude-sessions.backup/`
- **Git tag:** `pre-claude-mem-migration`

---

## Next Steps

1. **Use the new workflow:** Commit changes instead of manual checkpoints
2. **Try /mem-search:** Search your session history semantically
3. **Check .claude-code-context.md:** See auto-generated technical context
4. **Wait for Phase 4:** Historical checkpoint migration (upcoming)

---

**Last Updated:** 2025-12-15
**Migration Phase:** 3 of 5
**Next Phase:** Historical data migration (Phase 4)
