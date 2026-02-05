# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project implements a Claude Code PreToolUse hook that intercepts WebSearch tool calls and redirects documentation-related queries to local RAG databases via the LEANN MCP server. The hook provides an intelligent escape hatch allowing Claude to retry web searches if RAG results are insufficient.

**Core Components:**
- `docsearch.py` - Python 3.12+ PreToolUse hook script (39 passing tests)
- `~/.claude/hooks/docsearch-config.json` - User configuration mapping keywords to RAG databases
- `~/.claude/hooks/docsearch-state-{session_id}.json` - Per-session state files for escape hatch logic
- LEANN MCP Server - External dependency for RAG database access

**Implementation Status:** Complete. All 18 tasks from the implementation plan finished with:
- Core hook functionality (input parsing, config loading, keyword matching, escape hatch)
- Security features (session ID sanitization, path traversal prevention)
- Enhanced features (state expiry, stale file cleanup, config validation, error logging)
- Comprehensive test coverage (39 tests including edge cases, permissions, session isolation)
- Documentation (README, example config, integration testing guide)

When implementing features, always consult the design document for the authoritative specification. The implementation plan tracks progress and learnings.

## Development Commands

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_hook.py

# Run with verbose output
python -m pytest -v tests/
```

### Hook Installation (for testing)
```bash
# Install hook to Claude Code hooks directory
mkdir -p ~/.claude/hooks/PreToolUse
cp docsearch.py ~/.claude/hooks/PreToolUse/docsearch.py
chmod +x ~/.claude/hooks/PreToolUse/docsearch.py

# Install example config
cp config.example.json ~/.claude/hooks/docsearch-config.json
```

## Key Implementation Details

### Keyword Matching
- Uses word boundary regex for exact word matching (case-insensitive)
- Special characters in keywords (c++, .net, c#) handled with lookahead/lookbehind
- Multiple keywords can match multiple databases in a single query

### Escape Hatch
- First matching search is denied and params stored in session state
- Identical retry from same session is allowed through
- State expires after 5 minutes to prevent stale escape hatches
- Stale state files cleaned up on each hook run

### Fail-Open Design
- Invalid JSON input: allow through
- Missing/unreadable config: allow through
- Config parse errors: allow through
- State write failures: silent (still denies matching searches)
