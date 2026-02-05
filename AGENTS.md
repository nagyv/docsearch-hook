# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project implements a Claude Code PreToolUse hook that intercepts WebSearch tool calls and redirects documentation-related queries to local RAG databases via the LEANN MCP server. The hook provides an intelligent escape hatch allowing Claude to retry web searches if RAG results are insufficient.

**Core Components:**
- `docsearch.py` - Python 3.12+ PreToolUse hook script
- `~/.claude/hooks/docsearch-config.json` - User configuration mapping keywords to RAG databases
- `~/.claude/hooks/docsearch-state-{session_id}.json` - Per-session state files for escape hatch logic
- LEANN MCP Server - External dependency for RAG database access

When implementing features, always consult the design document for the authoritative specification. The implementation plan tracks progress and learnings.

## Development Commands

### Testing
```bash
# Run all tests (once implemented)
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
