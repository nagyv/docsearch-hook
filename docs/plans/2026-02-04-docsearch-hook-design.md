# DocSearch Hook Design

**Date:** 2026-02-04
**Author:** Viktor & Claude
**Status:** Approved

## Overview

A Claude Code PreToolUse hook that intercepts WebSearch tool calls and redirects documentation-related queries to local RAG databases via LEANN MCP server. The hook provides an intelligent escape hatch allowing Claude to retry web searches if RAG results are insufficient.

## Architecture

### Core Components

1. **PreToolUse Hook Script** (`docsearch.py`) - Python 3.12+ script that intercepts WebSearch calls
2. **Configuration File** (`~/.claude/hooks/docsearch-config.json`) - Maps keywords to RAG database metadata
3. **State Files** (`~/.claude/hooks/docsearch-state-{session_id}.json`) - Per-session tracking of denied searches
4. **LEANN MCP Server** - External component, assumed configured in Claude Code MCP settings

### Flow Diagram

```
WebSearch tool call
    ↓
PreToolUse hook fires (docsearch.py)
    ↓
Check state: Is this a retry? (same params as last call)
    ├─ Yes → Allow through (exit 0)
    └─ No → Continue
        ↓
    Parse query for configured keywords (case-insensitive)
        ├─ No match → Allow through (exit 0)
        └─ Match(es) found → Store params, Deny (exit 2) + add context
            ↓
        Claude receives denial + context about RAG database(s)
            ↓
        Claude calls LEANN MCP tool(s) (in parallel if multiple matches)
            ├─ Success → Done
            └─ Fail/Unsatisfied → Claude retries WebSearch
                ↓
            Hook sees same params → Allows through
```

## Configuration Structure

### Config File Location

`~/.claude/hooks/docsearch-config.json`

### Schema

```json
{
  "databases": [
    {
      "keywords": ["gitlab", "gl", "gitlab-ci"],
      "path": "/Users/viktor/.leann/databases/gitlab",
      "mcp_tool_name": "mcp__leann__search",
      "description": "GitLab documentation from docs.gitlab.com"
    },
    {
      "keywords": ["kubernetes", "k8s", "kubectl"],
      "path": "/Users/viktor/.leann/databases/kubernetes",
      "mcp_tool_name": "mcp__leann__search",
      "description": "Kubernetes official documentation"
    }
  ]
}
```

### Fields

- **`keywords`** (required): Array of strings to match in search queries
  - Case-insensitive matching
  - Exact word boundary matching (e.g., "gitla" does NOT match "gitlab")
  - Multiple keywords can map to one database

- **`path`** (required): Absolute path to LEANN database directory

- **`mcp_tool_name`** (required): Exact MCP tool name to suggest to Claude

- **`description`** (required): Human-readable description passed to Claude in `additionalContext`

### Keyword Matching Logic

1. Split query into words
2. Check each word against all configured keywords (case-insensitive, word boundary)
3. Collect ALL matches (multiple databases can match same query)
4. Order in config file determines priority when suggesting tools

## State File & Escape Hatch

### State File Location

`~/.claude/hooks/docsearch-state-{session_id}.json`

Each Claude Code session has isolated state to prevent cross-session interference.

### Schema

```json
{
  "last_denied": {
    "query": "how to configure gitlab ci",
    "allowed_domains": ["docs.gitlab.com"],
    "blocked_domains": [],
    "timestamp": 1738704000
  }
}
```

### Escape Hatch Logic

1. **On WebSearch interception:**
   - Load state file for current session (if exists)
   - Compare current `tool_input` against `last_denied`
   - If exact match (query + domains) → Allow through, clear state, exit 0
   - If no match → Continue to keyword matching

2. **On keyword match (denying search):**
   - Store current `tool_input` in session-specific state file
   - Exit 2 with `permissionDecision: deny` and `additionalContext`

3. **State cleanup:**
   - Clear `last_denied` after successful retry
   - Clear stale state files on session start
   - Optional: Add 5-minute timestamp expiry as safety net

### Parameter Comparison

- Exact string match on `query`
- Arrays compared as sets (order-independent) for `allowed_domains` and `blocked_domains`

## Hook Implementation Details

### Hook Type

Shell-based PreToolUse hook (Python script executed as subprocess)

### Hook Location

`~/.claude/hooks/PreToolUse/docsearch.py`

### Hook Responsibilities

1. **Filter for WebSearch only** - Exit early (code 0) if `tool_name != "WebSearch"`
2. **Load and parse config** - Read `docsearch-config.json`, handle missing/invalid gracefully
3. **Check escape hatch** - Load session state file, compare parameters, allow if match
4. **Keyword detection** - Parse query, match against configured keywords using word boundaries
5. **Multi-keyword handling** - Detect ALL matching databases in a single query
6. **Deny + guide** - If match(es) found, store state and return denial with structured `additionalContext`

### Output Format

#### Single Keyword Match

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Query matches 'gitlab' - using RAG database instead",
    "additionalContext": "This query should use the LEANN MCP tool 'mcp__leann__search' to search the GitLab documentation RAG database at /Users/viktor/.leann/databases/gitlab instead of web search."
  }
}
```

#### Multiple Keyword Matches

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Query matches 'gitlab' and 'kubernetes' - using RAG databases instead",
    "additionalContext": "This query matches multiple documentation databases. Please use these LEANN MCP tools IN PARALLEL:\n1. 'mcp__leann__search' for GitLab documentation at /Users/viktor/.leann/databases/gitlab\n2. 'mcp__leann__search' for Kubernetes official documentation at /Users/viktor/.leann/databases/kubernetes"
  }
}
```

### Error Handling

**Error Philosophy:** Fail open - when in doubt, allow the WebSearch through.

| Error Scenario | Behavior |
|----------------|----------|
| Config file missing/unreadable | Allow search through (exit 0) |
| Config file invalid JSON | Allow search through (exit 0), log to stderr |
| State file corrupted | Treat as no previous denial, continue |
| Invalid hook input JSON | Allow search through (exit 0) |

### Logging

- **Critical errors only** logged to stderr (e.g., invalid config JSON)
- Users debug by checking config file syntax manually
- Keep logging minimal to avoid noise

## Testing & Edge Cases

### Testing Strategy

1. **Unit Tests** (`tests/test_hook.py`):
   - Mock hook input JSON via stdin
   - Verify correct exit codes (0 for allow, 2 for deny)
   - Test keyword matching (single, multiple, partial, case variations)
   - Verify state file read/write operations with session_id
   - Test escape hatch logic

2. **Integration Tests**:
   - Configure real LEANN MCP server
   - Test full flow: WebSearch → Hook → MCP → Retry
   - Verify parallel MCP calls for multi-keyword queries

### Edge Cases

1. **Multiple keywords in same query:** "How to use GitLab with Kubernetes?"
   - Detect ALL matching databases
   - `additionalContext` mentions all MCP tools with instruction to call in parallel

2. **Partial word matches:** Query "ungitlabbed" contains "gitlab"
   - Use word boundary regex: `\bgitlab\b` (case-insensitive)
   - Should NOT match

3. **Case variations:** "GITLAB", "GitLab", "gitlab"
   - All should match (case-insensitive)

4. **Concurrent hook calls:** Multiple Claude sessions running
   - State file per session: `docsearch-state-{session_id}.json`
   - Each session has isolated state

5. **Stale state files:** User restarts Claude between denial and retry
   - Clear state file on session start
   - Fallback: 5-minute timestamp expiry

## Technology Choices

### Implementation Language

**Python 3.12+**

**Rationale:**
- Native JSON handling (stdlib)
- Excellent regex support for word boundaries
- Easy to test and maintain
- Widely available on development systems
- No external dependencies required

### Dependencies

- Python 3.12+ standard library only:
  - `json` - Config and state file parsing
  - `re` - Keyword matching with word boundaries
  - `sys` - stdin/stdout/stderr/exit codes
  - `pathlib` - File path handling

## User Setup & Usage

### Prerequisites

1. LEANN installed and configured
2. LEANN MCP server configured in Claude Code's MCP settings
3. RAG databases built manually using LEANN tools (see future CLI issue)

### Setup Steps

1. **Install the hook script:**
   ```bash
   mkdir -p ~/.claude/hooks/PreToolUse
   cp docsearch.py ~/.claude/hooks/PreToolUse/docsearch.py
   chmod +x ~/.claude/hooks/PreToolUse/docsearch.py
   ```

2. **Create configuration file:**
   ```bash
   cp config.example.json ~/.claude/hooks/docsearch-config.json
   # Edit with your database paths and keywords
   ```

3. **Verify LEANN MCP is configured** in Claude Code MCP settings

4. **Test the setup:**
   - Start Claude Code
   - Ask: "How do I configure GitLab CI runners?"
   - Verify hook intercepts and Claude uses MCP tool
   - If MCP fails, verify Claude retries with WebSearch

### User Experience Flow

```
User: "How do I configure GitLab CI runners?"
    ↓
Hook detects "gitlab" → Denies WebSearch
    ↓
Claude sees context → Calls mcp__leann__search with GitLab database
    ↓
If MCP succeeds → User gets RAG-based answer
If MCP fails → Claude retries WebSearch → Hook allows through → User gets web results
```

## Project Structure

```
docsearch-hook/
├── README.md                          # Setup instructions, usage guide
├── LICENSE
├── docsearch.py                       # Main hook script (Python 3.12+)
├── config.example.json                # Example configuration
├── tests/
│   ├── test_hook.py                   # Unit tests for hook logic
│   └── fixtures/                      # Test data (mock configs, inputs)
├── docs/
│   └── plans/
│       └── 2026-02-04-docsearch-design.md  # This document
└── .github/
    └── ISSUE_TEMPLATE/
```

## Future Work (GitHub Issues)

### Issue 1: Database Sharing Feature

**Title:** Enable sharing pre-built RAG databases between users

**Description:**
Currently users must build their own LEANN databases. Add functionality to:
- Export database metadata and files in shareable format
- Import shared databases with verification
- Community repository of common documentation databases (GitLab, K8s, etc.)

**Benefits:**
- Reduce setup friction for new users
- Standardize database quality for popular documentation sources
- Community contribution model

### Issue 2: CLI Setup Command

**Title:** Add CLI command for automated database creation

**Description:**
Provide `docsearch-hook setup <keyword> <url>` command that:
- Crawls documentation website using LEANN
- Builds RAG database
- Adds entry to config file automatically
- Validates MCP server configuration

**Benefits:**
- Eliminates manual LEANN tool usage
- Reduces errors in database creation
- Streamlines onboarding experience

## Success Criteria

1. **Functional:**
   - Hook correctly intercepts WebSearch for configured keywords
   - Multi-keyword queries trigger parallel MCP calls
   - Escape hatch allows retry after MCP failure
   - Per-session state isolation works correctly

2. **Reliability:**
   - Hook never breaks Claude's core functionality (fail open)
   - Handle all edge cases gracefully
   - Stale state cleanup prevents confusion

3. **Usability:**
   - Clear setup documentation
   - Example config provided
   - Error messages guide users to fixes

4. **Maintainability:**
   - Clean Python code with type hints
   - Comprehensive unit tests
   - Well-documented edge case handling
