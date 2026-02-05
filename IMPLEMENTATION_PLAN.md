# Implementation Plan: mcp-docsearch

A prioritized implementation plan for the mcp-docsearch Claude Code PreToolUse hook.

**Reference:** [Design Document](docs/plans/2026-02-04-docsearch-hook-design.md)

**Last Updated:** 2026-02-05T06:45Z

**Verification Status:** ✅ Independently verified via codebase analysis:
- No Python source code exists (confirmed: `**/*.py` glob returns 0 files)
- No `.gitignore` file exists (confirmed)
- No `tests/` directory exists (confirmed)
- No `config.example.json` exists (confirmed)
- `.mcp.json` server name is `leann-docs-search` (confirmed - needs rename to `leann`)
- `README.md` contains only `# mcp-docsearch` (confirmed - stub)
- `.leann/indexes/` pre-built with HNSW/contriever backend, 179 passages (confirmed)
- All P0 items remain pending

---

## Status Summary

| Component | Status | Priority | Notes |
|-----------|--------|----------|-------|
| LICENSE | ✅ Complete | - | MIT License |
| Design Document | ✅ Complete | - | 373 lines, comprehensive |
| .leann/ indexes | ✅ Complete | - | Pre-built, HNSW/contriever |
| **.mcp.json** | ⚠️ **Needs fix** | **P0** | **BLOCKING:** Server name `leann-docs-search` → tool name `mcp__leann-docs-search__search` (design expects `mcp__leann__search`). Must resolve before config.example.json |
| **docsearch.py** | ❌ Not started | **P0** | Critical path blocker |
| .gitignore | ❌ Not started | P1 | Quick win |
| config.example.json | ❌ Not started | P1 | Quick win (blocked by .mcp.json decision) |
| tests/ | ❌ Not started | P2 | Blocked by docsearch.py |
| README.md | ⚠️ Stub only | P2 | Currently just `# mcp-docsearch` |
| GitHub templates | ❌ Not started | P3 | Low priority |
| PROMPT_refinement.md | ⚠️ To delete | P3 | Development artifact, not part of deliverables |

---

## Priority-Ordered Task List

Items sorted by implementation priority. Complete in order.

### P0 — Critical Path (Blocks Everything)

- [ ] **Resolve .mcp.json server naming**
  - **DECISION REQUIRED:** Design doc uses `mcp__leann__search`, current config produces `mcp__leann-docs-search__search`
  - **Recommended action:** Rename server from `leann-docs-search` to `leann` in `.mcp.json`
  - This unblocks config.example.json creation (P1)
  - Must be resolved BEFORE any code references tool names

- [ ] **docsearch.py: Create skeleton with constants**
  - Location: `/workspace/repo/docsearch.py`
  - Shebang: `#!/usr/bin/env python3`
  - Imports: `json`, `re`, `sys`, `pathlib`, `time` (stdlib only)
  - Module docstring explaining hook purpose
  - Type hints throughout (Python 3.12+)
  - Constants:
    - `CONFIG_PATH = Path.home() / ".claude/hooks/docsearch-config.json"`
    - `STATE_DIR = Path.home() / ".claude/hooks/"`
    - `STATE_EXPIRY_SECONDS = 300`  # 5 minutes

- [ ] **docsearch.py: Implement configuration loading**
  - Function: `load_config() -> dict | None`
  - Path: `~/.claude/hooks/docsearch-config.json`
  - Validate `databases` array with required fields: `keywords`, `path`, `mcp_tool_name`, `description`
  - Return `None` on any error (fail-open philosophy)
  - No stderr logging on missing file (expected during setup)

- [ ] **docsearch.py: Implement hook input parsing**
  - Function: `parse_hook_input() -> dict | None`
  - Read JSON from stdin
  - Extract: `hook_event_name`, `tool_name`, `tool_input`, `session_id`
  - Return `None` on malformed JSON (triggers fail-open exit 0)

- [ ] **docsearch.py: Implement keyword matching**
  - Function: `find_matching_databases(query: str, databases: list) -> list`
  - Word boundary regex: `r'\b' + re.escape(keyword) + r'\b'` with `re.IGNORECASE`
  - Return ALL matching database entries (multi-keyword support)
  - Order preserved from config file

- [ ] **docsearch.py: Implement state file operations**
  - Functions:
    - `get_state_path(session_id: str) -> Path`
    - `load_state(session_id: str) -> dict | None`
    - `save_state(session_id: str, tool_input: dict) -> None`
    - `clear_state(session_id: str) -> None`
    - `cleanup_stale_states() -> None`
    - `ensure_hooks_directory() -> None` (create `~/.claude/hooks/` if missing)
  - Path pattern: `~/.claude/hooks/docsearch-state-{session_id}.json`
  - State schema: `{"last_denied": {"query": str, "allowed_domains": list, "blocked_domains": list, "timestamp": int}}`
  - Handle missing/corrupted files gracefully (return None)
  - `load_state` must validate schema structure (has `last_denied` with required subfields: `query`, `allowed_domains`, `blocked_domains`, `timestamp`), not just JSON validity
  - `cleanup_stale_states` removes state files older than 5 minutes (approximates session-start cleanup per design doc line 126)
  - `ensure_hooks_directory` must be called before any file operations to handle first-run scenario

- [ ] **docsearch.py: Implement escape hatch logic**
  - Function: `should_allow_retry(tool_input: dict, state: dict) -> bool`
  - Compare current `tool_input` against `last_denied`:
    - Exact string match on `query`
    - Set comparison (order-independent) for `allowed_domains` and `blocked_domains`
    - Check timestamp < 5 minutes old
  - If match and not expired: return True (caller clears state, exits 0)

- [ ] **docsearch.py: Implement denial output generation**
  - Function: `generate_denial(matched_databases: list) -> dict`
  - Single match format:
    ```json
    {
      "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Query matches '{keyword}' - using RAG database instead",
        "additionalContext": "Use LEANN MCP tool '{mcp_tool_name}' to search {description} at {path}"
      }
    }
    ```
  - Multiple matches: List all databases with explicit "IN PARALLEL" instruction (per design doc line 176)

- [ ] **docsearch.py: Implement main() with error wrapper**
  - Orchestrate full flow:
    1. Parse hook input (exit 0 if None)
    2. Early exit if not PreToolUse or not WebSearch (exit 0)
    3. Load config (exit 0 if None)
    4. Cleanup stale state files (opportunistic, non-blocking)
    5. Check escape hatch (exit 0 if should allow, clears state)
    6. Find matching databases (exit 0 if empty)
    7. Save state for session
    8. Output denial JSON to stdout (exit 2)
  - Wrap entire main in try/except: exit 0 on any unhandled error
  - Log critical errors to stderr only (keep logging minimal per design doc line 196)

### P1 — Quick Wins (No Dependencies)

- [ ] **Create .gitignore**
  - Location: `/workspace/repo/.gitignore`
  - Contents:
    ```
    # Python
    __pycache__/
    *.pyc
    *.pyo
    *.pyd
    .python-version

    # Virtual environments
    venv/
    .venv/
    env/

    # IDE
    .vscode/
    .idea/
    *.swp
    *.swo

    # Testing
    .pytest_cache/
    .coverage
    htmlcov/
    .mypy_cache/
    .tox/

    # State files (session-specific, should not be committed)
    docsearch-state-*.json

    # OS
    .DS_Store
    Thumbs.db
    ```

- [ ] **Create config.example.json**
  - Location: `/workspace/repo/config.example.json`
  - Contents:
    ```json
    {
      "databases": [
        {
          "keywords": ["gitlab", "gl", "gitlab-ci"],
          "path": "/path/to/your/.leann/databases/gitlab",
          "mcp_tool_name": "mcp__leann__search",
          "description": "GitLab documentation"
        },
        {
          "keywords": ["kubernetes", "k8s", "kubectl"],
          "path": "/path/to/your/.leann/databases/kubernetes",
          "mcp_tool_name": "mcp__leann__search",
          "description": "Kubernetes official documentation"
        }
      ]
    }
    ```

### P2 — Testing (Blocked by P0)

- [ ] **Create tests/ directory structure**
  - `tests/__init__.py` (empty)
  - `tests/test_hook.py` (main test file)
  - `tests/fixtures/` (directory for test data)

- [ ] **Create test fixtures**
  - `tests/fixtures/valid_config.json`
  - `tests/fixtures/invalid_config.json` (malformed JSON)
  - `tests/fixtures/missing_fields_config.json`
  - `tests/fixtures/websearch_input.json`
  - `tests/fixtures/other_tool_input.json`
  - `tests/fixtures/multi_keyword_input.json`
  - Note: Fixtures should use mock paths (e.g., `/tmp/test-db`) rather than real LEANN paths

- [ ] **Test: Configuration loading**
  - Valid config loads correctly
  - Missing config returns None
  - Invalid JSON returns None
  - Missing required fields returns None

- [ ] **Test: Keyword matching**
  - Single keyword exact match
  - Case-insensitive: "GITLAB", "GitLab", "gitlab" all match
  - Word boundary: "ungitlabbed" does NOT match "gitlab"
  - Multiple databases matching same query
  - No matches returns empty list
  - Special regex characters in keywords are escaped

- [ ] **Test: State file operations**
  - save_state creates correct JSON content
  - load_state reads existing state
  - load_state returns None for missing/corrupted files
  - load_state returns None for valid JSON with invalid schema (missing `last_denied` or subfields)
  - clear_state removes file
  - cleanup_stale_states removes old files but keeps recent ones
  - Session isolation (different session_ids don't interfere)

- [ ] **Test: Escape hatch logic**
  - Exact match allows through (returns True)
  - Query mismatch continues to matching (returns False)
  - Domain arrays compared as sets (order-independent)
  - Timestamp expiry: >5 min = expired (returns False)
  - State cleared after successful escape

- [ ] **Test: Denial output format**
  - Single match structure matches design doc
  - Multiple matches include all databases
  - Multiple matches contain "IN PARALLEL" instruction text
  - Exit code is 2 on denial

- [ ] **Test: Error handling**
  - Unhandled exception results in exit 0
  - Non-WebSearch tool causes exit 0

- [ ] **Test: Integration (optional)**
  - Full flow: WebSearch with keyword → deny
  - Full flow: Same params retry → allow (escape hatch)
  - Full flow: Non-matching query → allow
  - Full flow: Config missing → allow all

### P2 — Documentation (Blocked by P0)

- [ ] **Update README.md: Project overview**
  - What the hook does (1-2 paragraphs)
  - Link to design document
  - Prerequisites: Python 3.12+, LEANN, Claude Code

- [ ] **Update README.md: Installation instructions**
  - Clone repository
  - Copy docsearch.py to `~/.claude/hooks/PreToolUse/`
  - Set executable permission: `chmod +x`
  - Copy and customize config to `~/.claude/hooks/docsearch-config.json`

- [ ] **Update README.md: Configuration guide**
  - Config file location and full schema
  - Keyword matching behavior (case-insensitive, word boundaries)
  - Multiple database example

- [ ] **Update README.md: Usage examples**
  - Query that triggers hook
  - Escape hatch behavior
  - Multi-keyword parallel query

- [ ] **Update README.md: Troubleshooting**
  - Config syntax validation
  - LEANN MCP verification
  - Hook executable check
  - State file inspection

- [ ] **Add docstrings to docsearch.py**
  - Module-level overview
  - Function docstrings with Args and Returns
  - Inline comments for complex logic (escape hatch, keyword matching)

### P3 — Polish (Low Priority)

- [ ] **Create .github/ISSUE_TEMPLATE/bug_report.md**
- [ ] **Create .github/ISSUE_TEMPLATE/feature_request.md**
- [ ] **Create GitHub Issue: Database Sharing Feature**
- [ ] **Create GitHub Issue: CLI Setup Command**
- [ ] **Delete PROMPT_refinement.md**
  - Development artifact, not part of final deliverables
  - Should be deleted, not archived (it's a one-time prompt for refinement)

### P4 — Validation (Final Phase)

- [ ] **Manual testing in Claude Code**
  - Install hook in real environment
  - Test with actual LEANN MCP server
  - Verify keyword interception works
  - Verify escape hatch allows retry
  - Verify multi-keyword triggers parallel guidance
  - Verify fail-open on errors

- [ ] **Design compliance audit**
  - Exit codes match spec (0=allow, 2=deny)
  - Output JSON format matches design doc exactly
  - Config schema matches design doc
  - State schema matches design doc

- [ ] **Verify LEANN MCP server configuration**
  - Confirm `.mcp.json` server naming aligns with LEANN tool expectations
  - Verify `mcp__leann__search` tool name resolves correctly
  - Test MCP tool invocation with actual LEANN server

---

## Implementation Notes

### Design Decisions (from design doc)

1. **Fail Open**: Any error = exit 0 (allow WebSearch through)
2. **Stdlib Only**: No pip dependencies (json, re, sys, pathlib, time)
3. **Session Isolation**: State files keyed by session_id
4. **5-Minute Expiry**: Safety net for stale state

### Key Technical Details

- **Hook Location**: `~/.claude/hooks/PreToolUse/docsearch.py`
- **Config Location**: `~/.claude/hooks/docsearch-config.json`
- **State Location**: `~/.claude/hooks/docsearch-state-{session_id}.json`
- **Exit Codes**: 0 = allow, 2 = deny with guidance

### Hook Input Schema (Verified from Claude Code Official Docs)

PreToolUse hooks receive JSON via stdin with these fields:
```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "WebSearch",
  "tool_input": {
    "query": "search query text",
    "allowed_domains": ["example.com"],
    "blocked_domains": []
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

WebSearch-specific `tool_input` fields:
- `query` (string): The search query
- `allowed_domains` (array, optional): Only include results from these domains
- `blocked_domains` (array, optional): Exclude results from these domains

### Clarifications Resolved

1. **State cleanup**: Design doc mentions "clear stale state files on session start" (line 126) but hooks cannot detect session boundaries. Resolution: opportunistic cleanup of all state files >5 minutes old on each hook invocation approximates this behavior. Combined with 5-minute timestamp expiry check in escape hatch logic, this provides robust stale state handling.
2. **MCP parameters**: Include path in additionalContext, let Claude determine params
3. **Same tool name**: Different databases differentiated by path in additionalContext
4. **Parallel MCP calls**: Multi-keyword denials must include explicit "IN PARALLEL" text per design doc line 176 to ensure Claude calls MCP tools concurrently
5. **MCP tool naming**: The `.mcp.json` server name determines tool name prefix. Current `leann-docs-search` produces `mcp__leann-docs-search__search`. **DECISION: Rename to `leann` for cleaner `mcp__leann__search` as per design doc examples.** (Elevated to P0)
6. **Directory creation**: The hooks directory `~/.claude/hooks/` may not exist on first run. State file operations must create it if missing.

---

## Success Criteria

From design document:

1. **Functional**: Hook intercepts WebSearch for keywords, multi-keyword parallel calls work, escape hatch allows retry
2. **Reliability**: Never breaks Claude (fail open), handles all edge cases
3. **Usability**: Clear docs, example config, helpful error messages
4. **Maintainability**: Type hints, unit tests, documented edge cases
