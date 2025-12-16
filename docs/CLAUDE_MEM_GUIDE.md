# claude-mem User Guide

**Plugin:** `claude-mem@anthropic`
**Purpose:** Automatic semantic memory across Claude Code sessions
**Status:** Active (Phase 1+)

---

## What is claude-mem?

`claude-mem` is an official Anthropic plugin for Claude Code that provides **automatic long-term memory** with **semantic search** across all your sessions.

**Key Features:**
- ✅ **Automatic capture:** Observations saved during conversations
- ✅ **Semantic search:** Find things by meaning, not keywords
- ✅ **Persistent:** Memory survives across sessions and restarts
- ✅ **Private:** Stored locally in `~/.claude/mem/`
- ✅ **Cost-effective:** Optimized to ~$11.25/month

---

## Quick Start

### 1. Enable claude-mem

Already enabled in this project! Configuration in `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "claude-mem@anthropic": true
  },
  "env": {
    "CLAUDE_MEM_CONTEXT_OBSERVATIONS": "25"
  }
}
```

### 2. Use /mem-search

```bash
/mem-search authentication implementation
```

### 3. Let it Work Automatically

claude-mem captures observations as you work - no manual intervention needed!

---

## How It Works

### Automatic Observation Capture

During conversations with Claude, important information is automatically captured as "observations":

**What gets captured:**
- 💡 Architectural decisions and rationale
- 🐛 Problems encountered and solutions
- 📚 Code explanations and implementations
- 🎯 Project goals and milestones
- 🔧 Configuration choices
- 💬 Important discussions and context

**What doesn't get captured:**
- Trivial exchanges ("ok", "thanks")
- Repeated information
- Low-value content

### Storage

**Location:** `~/.claude/mem/`

**Format:**
- SQLite database (structured data)
- Chroma vector database (semantic embeddings)

**Privacy:** All data stored locally on your machine

---

## Using /mem-search

### Basic Search

```bash
/mem-search <your query>
```

**Examples:**
```bash
/mem-search authentication implementation
/mem-search database schema design
/mem-search API endpoint structure
/mem-search deployment configuration
```

### Semantic vs Keyword

**Semantic search** (what claude-mem does):
- Understands meaning and context
- Finds related concepts even with different words
- Example: "auth flow" finds results about "login process", "user authentication", "session management"

**Keyword search** (traditional):
- Matches exact words only
- Misses related concepts
- Example: "auth flow" only finds exact phrase "auth flow"

### Search Examples

#### Finding Past Implementations
```bash
# What you type:
/mem-search how did I implement the payment processing?

# What it finds:
- Stripe API integration discussion (2 days ago)
- Payment validation logic explanation (5 days ago)
- Error handling strategy for failed payments (1 week ago)
```

#### Finding Architectural Decisions
```bash
# What you type:
/mem-search why did we choose Redis over in-memory caching?

# What it finds:
- Decision: Redis for distributed caching (3 days ago)
- Rationale: Need persistence across restarts
- Alternative considered: In-memory rejected due to data loss on crash
```

#### Finding Bug Solutions
```bash
# What you type:
/mem-search what was the solution for the CORS error?

# What it finds:
- CORS middleware configuration (1 week ago)
- Allowed origins list setup
- Preflight request handling
```

#### Finding Test Strategies
```bash
# What you type:
/mem-search how should I test the email service?

# What it finds:
- Mock SMTP server strategy (2 weeks ago)
- Email template validation approach
- Integration test patterns used in project
```

---

## Best Practices

### 1. Ask Clear Questions

**Good:**
```bash
/mem-search why did we use JWT instead of session cookies for authentication?
```

**Less effective:**
```bash
/mem-search auth
```

**Why:** More specific queries return more relevant results.

### 2. Use Natural Language

You don't need to guess exact keywords:

```bash
# All these work:
/mem-search login flow
/mem-search how does authentication work
/mem-search user session management
/mem-search sign-in process
```

### 3. Include Context

```bash
# Better:
/mem-search how did I implement error handling in the payment API?

# Less specific:
/mem-search error handling
```

### 4. Search Before Re-implementing

Before implementing a feature, search if you've done something similar:

```bash
/mem-search have I implemented rate limiting before?
/mem-search similar validation logic
/mem-search pattern for handling async operations
```

### 5. Use for Decision Recall

```bash
/mem-search why did we choose this library?
/mem-search what was the rationale for this architecture?
/mem-search alternatives we considered
```

---

## Common Use Cases

### 1. Resuming Work After Break

```bash
# Start of day:
/mem-search what was I working on yesterday with the API?
/mem-search next steps for the authentication feature
```

### 2. Understanding Past Decisions

```bash
/mem-search why is the database structured this way?
/mem-search reasoning behind using microservices?
```

### 3. Finding Implementation Patterns

```bash
/mem-search how did I handle file uploads?
/mem-search pattern for background jobs
/mem-search database migration strategy
```

### 4. Debugging

```bash
/mem-search have I seen this error before?
/mem-search solution for database connection timeout
/mem-search how did I fix the memory leak?
```

### 5. Onboarding New Team Members

```bash
/mem-search architectural overview
/mem-search key design decisions
/mem-search how does the deployment process work?
```

---

## Cost Management

### Default Configuration
```json
{
  "CLAUDE_MEM_CONTEXT_OBSERVATIONS": "50"
}
```
**Cost:** ~$38.25/month

### Optimized Configuration (Current)
```json
{
  "CLAUDE_MEM_CONTEXT_OBSERVATIONS": "25"
}
```
**Cost:** ~$11.25/month
**Trade-off:** Slightly less context but still very effective

### How to Adjust

Edit `.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_MEM_CONTEXT_OBSERVATIONS": "25"  // Adjust this number
  }
}
```

**Guidelines:**
- `10-15`: Minimal (budget-conscious)
- `25`: Balanced (recommended)
- `50`: Maximum (default, costly)

**Restart Claude Code after changes.**

---

## Troubleshooting

### /mem-search returns no results

**Possible causes:**
1. **New installation** - No observations captured yet
   - Solution: Have a few conversations, then try again

2. **Query too specific** - No matching observations
   - Solution: Try broader query

3. **Database issue** - Corrupted database
   - Solution: Check `~/.claude/mem/` exists and has files

### Observations not being captured

**Check:**
1. Plugin enabled in `.claude/settings.json`
2. Claude Code restarted after enabling
3. Having substantial conversations (not just "ok", "thanks")

### Cost higher than expected

**Solutions:**
1. Reduce `CLAUDE_MEM_CONTEXT_OBSERVATIONS` to `15-20`
2. Monitor usage in Anthropic dashboard
3. Disable plugin temporarily if needed

---

## Limitations

### What claude-mem Does NOT Do

❌ **File search** - Use `/grep` or code search instead
❌ **Code completion** - Built into Claude Code
❌ **Real-time sync** - Observations captured during conversations only
❌ **Cross-machine sync** - Database is local (not cloud-synced)
❌ **Structured queries** - Use natural language, not SQL

### Working Around Limitations

**For file search:**
```bash
# Wrong:
/mem-search find files with "UserModel"

# Right:
Use /grep or /find command instead
```

**For technical details:**
```bash
# For recent commit details:
cat .claude-code-context.md

# For historical technical summaries:
cat ~/.claude/historical-context/index.md
```

---

## Combining with Code Context

claude-mem and Code Context Layer work together:

| Need | Tool |
|------|------|
| "Why did we make this decision?" | `/mem-search` |
| "Which files changed in last commit?" | `.claude-code-context.md` |
| "How does authentication work?" | `/mem-search` |
| "What are the dependencies?" | `.claude-code-context.md` |
| "What was the bug solution?" | `/mem-search` |
| "Which tests should I run?" | `.claude-code-context.md` |

---

## Advanced Tips

### 1. Refresh Memory with Summaries

Periodically reference important context:

```bash
# In conversation:
"Here's a summary of the authentication system:
- JWT-based with refresh tokens
- Redis for token blacklisting
- 15-minute access token expiry
- Role-based permissions"

# claude-mem captures this for future reference
```

### 2. Document Decisions as You Make Them

When making important decisions:

```bash
# Instead of just implementing:
"I'm going to use Redis for caching because:
1. Need distributed cache across instances
2. Data persistence across restarts
3. Built-in expiration support

Alternatives considered:
- In-memory: Too volatile
- Database: Too slow for cache"

# claude-mem captures this rationale
```

### 3. Use as Project Journal

Share end-of-day summaries:

```bash
"Summary of today's work:
- Implemented OAuth2 flow
- Fixed CORS issues with preflight requests
- Next: Add rate limiting to API endpoints"
```

### 4. Cross-Reference with Historical Context

```bash
# First check historical summaries:
cat ~/.claude/historical-context/index.md

# Then use /mem-search for semantic details:
/mem-search [topic from historical summary]
```

---

## FAQ

### Q: Does claude-mem work across different projects?
**A:** Yes! All observations stored in single database, searchable across projects.

### Q: Can I delete or edit observations?
**A:** Not directly through UI. Database is in `~/.claude/mem/` - advanced users can manipulate SQLite directly.

### Q: What happens if I disable claude-mem?
**A:** Observations stop being captured. Existing data preserved in database.

### Q: Can I export my observations?
**A:** SQLite database can be exported using standard SQLite tools.

### Q: Does claude-mem slow down Claude Code?
**A:** Minimal impact. Observations captured asynchronously.

### Q: Is there a limit to how many observations?
**A:** No hard limit. Database grows over time. Can prune old observations if needed.

### Q: Can other people access my observations?
**A:** No. Database is local to your machine (`~/.claude/mem/`).

---

## Resources

- **Architecture:** See `docs/ARCHITECTURE.md` for system design
- **Migration:** See `docs/MIGRATION_GUIDE.md` for old workflow → new workflow
- **Code Context:** See `docs/CODE_CONTEXT_GUIDE.md` for technical details
- **Session Protocol:** See `SESSION_PROTOCOL.md` for complete workflow

---

**Last Updated:** 2025-12-15
**Plugin Version:** claude-mem@anthropic (latest)
**Optimization:** 25 observations per context window (~$11.25/month)
