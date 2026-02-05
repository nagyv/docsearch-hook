# DocSearch Hook Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Claude Code PreToolUse hook that intercepts WebSearch tool calls and redirects documentation-related queries to local RAG databases via LEANN MCP server.

**Architecture:** A Python 3.12+ script (`docsearch.py`) acts as a PreToolUse hook. It reads configuration from `~/.claude/hooks/docsearch-config.json`, tracks state in session-specific files, and uses exit codes to allow (0) or deny (2) WebSearch calls. When denying, it provides `additionalContext` guiding Claude to use LEANN MCP tools instead. An escape hatch allows retries if RAG results are insufficient.

**Tech Stack:** Python 3.12+ standard library only (json, re, sys, pathlib, os, time)

**Reference:** See `docs/plans/2026-02-04-docsearch-hook-design.md` for full design specification.

---

## Implementation Status: ALL COMPLETE ✅

| Task | Status | Description | Priority | Order |
|------|--------|-------------|----------|-------|
| Task 2 | COMPLETED | Core Hook Script - Skeleton and Input Parsing | P0 - Foundation | 1 |
| Task 3 | COMPLETED | Configuration Loading | P0 - Core | 2 |
| Task 4 | COMPLETED | Keyword Matching with Word Boundaries | P0 - Core | 3 |
| Task 6a | COMPLETED | Session ID Sanitization (Security) | P0 - Security | 4 |
| Task 6 | COMPLETED | Session State Management for Escape Hatch | P0 - Core | 5 |
| Task 12 | COMPLETED | Make Script Executable and Add Shebang | P0 - Core | 6 |
| Task 5 | COMPLETED | Multiple Keyword Matching (Verification Tests) | P1 - Feature | 7 |
| Task 7 | COMPLETED | State Cleanup (Stale State Expiry) | P1 - Enhancement | 8 |
| Task 7a | COMPLETED | Session Start State Cleanup | P1 - Enhancement | 9 |
| Task 3a | COMPLETED | Configuration Schema Validation | P1 - Quality | 10 |
| Task 3b | COMPLETED | Keywords Element Type Validation | P1 - Quality | 11 |
| Task 8 | COMPLETED | Error Logging to stderr | P1 - Enhancement | 12 |
| Task 9 | COMPLETED | Complete Test Coverage and Edge Cases | P1 - Quality | 13 |
| Task 9a | COMPLETED | Permission Error Tests | P1 - Quality | 14 |
| Task 9b | COMPLETED | Session Isolation Tests | P1 - Quality | 15 |
| Task 1 | COMPLETED | Project Structure and Example Config | P2 - Documentation | 16 |
| Task 10 | COMPLETED | README Documentation | P2 - Documentation | 17 |
| Task 11 | COMPLETED | Final Integration Testing | P2 - Validation | 18 |

**Test Results:** 39 tests passing (run time: ~2.2s)

---

## Implementation Progress Log

### 2026-02-05 - Phase 1 (P0 Core)
Tasks 2, 3, and 4 completed with 8 passing tests. Core hook functionality now works:
- Input parsing with fail-open on invalid JSON
- Configuration loading with DOCSEARCH_CONFIG_PATH env var override
- Keyword matching with word boundaries (case-insensitive)
- Denial response generation for single and multiple matches

Tasks 6a, 6, and 12 completed with 15 passing tests total. Security and state management now work:
- Session ID sanitization prevents path traversal attacks
- Escape hatch allows retry with same params
- State files use per-session isolation
- Script is executable with proper shebang

### 2026-02-05 - Phase 2 (P1 Features)
Tasks 5, 7, and 7a completed with 21 passing tests total. Enhanced features now work:
- Multiple keyword matching verified with tests
- State expiry after 5 minutes prevents stale escape hatches
- Stale state file cleanup removes old session files

Tasks 3a, 3b, and 8 completed with 27 passing tests total. Validation and logging now work:
- Config schema validation filters invalid database entries
- Keywords type validation ensures proper array of strings
- Error logging to stderr for JSON parse errors and file access issues

Tasks 9, 9a, and 9b completed with 39 passing tests total. Test coverage now comprehensive:
- Edge case tests for empty queries, missing fields, and special characters in keywords
- Permission error tests verify fail-open behavior for unreadable config and unwritable state dir
- Session isolation tests ensure escape hatch works correctly per-session
- Fixed keyword matching for special characters (c++, c#, .net) using lookahead/lookbehind

### 2026-02-05 - Phase 3 (P2 Documentation)
- Task 1: config.example.json created with GitLab and Kubernetes examples
- Task 10: README.md with comprehensive setup, configuration, and troubleshooting docs
- Task 11: tests/test_integration.py integration testing guide created

---

## Key Learnings & Design Decisions

### Gap Analysis Notes
These gaps were identified during implementation and addressed:

1. **Session Start State Cleanup (Task 7a):** Design spec mentions "Clear state file on session start" - implemented as cleanup during hook execution
2. **Config Schema Validation (Task 3a):** Design spec marks config fields as "required" - added validation with warnings
3. **Type validation for config fields:** Keywords validated as array of strings, not just present
4. **Empty keywords array:** Logs warning and skips entry
5. **Path format validation:** Warns on relative paths (design spec says absolute)
6. **Permission error handling:** Tests verify fail-open behavior for unreadable config and unwritable state dir
7. **Session isolation:** Tests ensure escape hatch works correctly per-session

### Security: Session ID Path Traversal
**CRITICAL - Addressed in Task 6a:** The `get_state_file()` function uses `sanitize_session_id()` to allow only alphanumeric characters, dashes, and underscores. This prevents path traversal attacks from malicious session IDs.

### Special Character Keywords
Keywords with regex special characters (c++, c#, .net) required special handling with lookahead/lookbehind patterns rather than simple `\b` word boundaries, since `\b` doesn't work correctly at word/non-word boundaries for characters like `+` and `#`.

---

## Files Created

| File | Purpose |
|------|---------|
| `docsearch.py` | Main hook script (336 lines, Python 3.12+) |
| `tests/test_hook.py` | 39 unit tests with comprehensive coverage |
| `tests/test_integration.py` | Manual integration testing guide |
| `tests/fixtures/valid_config.json` | Test fixture with GitLab & Kubernetes |
| `config.example.json` | Example configuration for users |
| `README.md` | Setup instructions, usage, troubleshooting |
| `.gitignore` | Standard Python gitignore (prevents cache file pollution) |

---

## Success Criteria Met

From design spec:
- ✅ Hook correctly intercepts WebSearch for configured keywords
- ✅ Multi-keyword queries trigger parallel MCP calls guidance
- ✅ Escape hatch allows retry after MCP failure
- ✅ Per-session state isolation works correctly
- ✅ Hook never breaks Claude's core functionality (fail open)
- ✅ All edge cases handled gracefully
- ✅ Stale state cleanup prevents confusion
- ✅ Clear setup documentation
- ✅ Example config provided
- ✅ Error messages guide users to fixes
- ✅ Clean Python code with type hints (all functions have type annotations)
- ✅ Comprehensive unit tests (39 tests)
- ✅ Well-documented edge case handling

---

## Future Enhancements (Not Required for MVP)

These were identified in the design spec as future work:
- GitHub issue templates (`.github/ISSUE_TEMPLATE/`)
- Database sharing feature (export/import RAG databases)
- CLI setup command for automated database creation
