# DocSearch Hook Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Claude Code PreToolUse hook that intercepts WebSearch calls and redirects documentation queries to local RAG databases with intelligent escape hatch for retries.

**Architecture:** Python 3.12+ script reads hook input from stdin, matches queries against configured keywords, stores per-session state for retry detection, and outputs structured JSON denial with MCP tool guidance.

**Tech Stack:** Python 3.14 stdlib (json, re, sys, pathlib), pytest for testing

---

## Task 1: Project Structure Setup

**Files:**
- Create: `docsearch.py`
- Create: `config.example.json`
- Create: `tests/test_hook.py`
- Create: `tests/fixtures/hook_input.json`
- Create: `tests/fixtures/config.json`
- Create: `.gitignore`

**Step 1: Create .gitignore**

```bash
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.pytest_cache/
*.egg-info/
dist/
build/
.coverage
htmlcov/
.venv/
venv/
EOF
```

**Step 2: Create example config file**

```bash
cat > config.example.json << 'EOF'
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
EOF
```

**Step 3: Create test fixtures directory**

```bash
mkdir -p tests/fixtures
```

**Step 4: Create placeholder hook script**

```bash
cat > docsearch.py << 'EOF'
#!/usr/bin/env python3
# ABOUTME: Claude Code PreToolUse hook that redirects WebSearch to local RAG databases
# ABOUTME: Intercepts documentation queries and routes them to LEANN MCP server

import sys

if __name__ == "__main__":
    # Placeholder - will be implemented via TDD
    sys.exit(0)
EOF
chmod +x docsearch.py
```

**Step 5: Create placeholder test file**

```bash
cat > tests/test_hook.py << 'EOF'
# ABOUTME: Unit tests for docsearch PreToolUse hook
# ABOUTME: Tests keyword matching, state management, and escape hatch logic

import pytest

# Tests will be added incrementally via TDD
EOF
```

**Step 6: Commit project structure**

```bash
git add .gitignore config.example.json docsearch.py tests/
git commit -m "feat: initialize docsearch hook project structure"
```

---

## Task 2: Non-WebSearch Tool Pass-Through

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`
- Create: `tests/fixtures/non_websearch_input.json`

**Step 1: Write failing test for non-WebSearch tools**

Add to `tests/test_hook.py`:

```python
import json
import subprocess
from pathlib import Path

def test_non_websearch_tool_passes_through():
    """Hook should allow non-WebSearch tools through with exit 0"""
    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "ls"},
        "session_id": "test-session-123"
    }

    result = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert result.stdout == ""
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_hook.py::test_non_websearch_tool_passes_through -v
```

Expected: FAIL (exit code 0 but test expects proper filtering)

**Step 3: Implement minimal pass-through logic**

Replace `docsearch.py` content:

```python
#!/usr/bin/env python3
# ABOUTME: Claude Code PreToolUse hook that redirects WebSearch to local RAG databases
# ABOUTME: Intercepts documentation queries and routes them to LEANN MCP server

import json
import sys

def main():
    try:
        hook_input = json.loads(sys.stdin.read())

        # Pass through non-WebSearch tools
        if hook_input.get("tool_name") != "WebSearch":
            sys.exit(0)

        # Placeholder for WebSearch handling
        sys.exit(0)

    except Exception:
        # Fail open - allow tool through on any error
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_hook.py::test_non_websearch_tool_passes_through -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add docsearch.py tests/test_hook.py
git commit -m "feat: add non-WebSearch tool pass-through logic"
```

---

## Task 3: Config File Loading with Fail-Open

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`
- Create: `tests/fixtures/valid_config.json`
- Create: `tests/fixtures/invalid_config.json`

**Step 1: Write test fixtures**

Create `tests/fixtures/valid_config.json`:

```json
{
  "databases": [
    {
      "keywords": ["gitlab"],
      "path": "/test/gitlab",
      "mcp_tool_name": "mcp__leann__search",
      "description": "GitLab docs"
    }
  ]
}
```

Create `tests/fixtures/invalid_config.json`:

```json
{
  "databases": [
    {"keywords": "not-an-array"}
  ]
}
```

**Step 2: Write failing tests for config loading**

Add to `tests/test_hook.py`:

```python
import os
from pathlib import Path

def test_missing_config_fails_open(tmp_path, monkeypatch):
    """Missing config file should allow search through"""
    monkeypatch.setenv("HOME", str(tmp_path))

    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {"query": "gitlab ci"},
        "session_id": "test-123"
    }

    result = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    assert result.returncode == 0

def test_invalid_config_fails_open(tmp_path, monkeypatch):
    """Invalid config JSON should allow search through"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text("invalid json{")

    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {"query": "gitlab ci"},
        "session_id": "test-123"
    }

    result = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
```

**Step 3: Run tests to verify they fail**

```bash
pytest tests/test_hook.py::test_missing_config_fails_open -v
pytest tests/test_hook.py::test_invalid_config_fails_open -v
```

Expected: Tests may pass trivially since current code exits 0 - verify logic is correct

**Step 4: Implement config loading with fail-open**

Update `docsearch.py`:

```python
#!/usr/bin/env python3
# ABOUTME: Claude Code PreToolUse hook that redirects WebSearch to local RAG databases
# ABOUTME: Intercepts documentation queries and routes them to LEANN MCP server

import json
import sys
from pathlib import Path

def load_config():
    """Load config file from ~/.claude/hooks/docsearch-config.json

    Returns config dict or None if missing/invalid (fail open)
    """
    config_path = Path.home() / ".claude" / "hooks" / "docsearch-config.json"

    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            config = json.load(f)

        # Validate basic structure
        if not isinstance(config.get("databases"), list):
            sys.stderr.write("Invalid config: databases must be an array\n")
            return None

        return config

    except json.JSONDecodeError as e:
        sys.stderr.write(f"Invalid config JSON: {e}\n")
        return None
    except Exception as e:
        sys.stderr.write(f"Error loading config: {e}\n")
        return None

def main():
    try:
        hook_input = json.loads(sys.stdin.read())

        # Pass through non-WebSearch tools
        if hook_input.get("tool_name") != "WebSearch":
            sys.exit(0)

        # Load config - fail open if missing/invalid
        config = load_config()
        if config is None:
            sys.exit(0)

        # Placeholder for keyword matching
        sys.exit(0)

    except Exception:
        # Fail open - allow tool through on any error
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_hook.py::test_missing_config_fails_open -v
pytest tests/test_hook.py::test_invalid_config_fails_open -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add docsearch.py tests/
git commit -m "feat: add config file loading with fail-open error handling"
```

---

## Task 4: Keyword Matching Logic

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`

**Step 1: Write failing tests for keyword matching**

Add to `tests/test_hook.py`:

```python
def test_no_keyword_match_passes_through(tmp_path, monkeypatch):
    """Query with no matching keywords should allow search through"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text(
        Path("tests/fixtures/valid_config.json").read_text()
    )

    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {"query": "how to cook pasta"},
        "session_id": "test-123"
    }

    result = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    assert result.returncode == 0

def test_single_keyword_match_denies(tmp_path, monkeypatch):
    """Query with matching keyword should deny with exit 2"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text(
        Path("tests/fixtures/valid_config.json").read_text()
    )

    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {"query": "how to configure gitlab ci"},
        "session_id": "test-123"
    }

    result = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "gitlab" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()

def test_case_insensitive_matching(tmp_path, monkeypatch):
    """Keyword matching should be case-insensitive"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text(
        Path("tests/fixtures/valid_config.json").read_text()
    )

    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {"query": "how to configure GITLAB CI"},
        "session_id": "test-123"
    }

    result = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    assert result.returncode == 2

def test_word_boundary_matching(tmp_path, monkeypatch):
    """Keyword matching should respect word boundaries"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text(
        Path("tests/fixtures/valid_config.json").read_text()
    )

    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {"query": "ungitlabbed workflows"},
        "session_id": "test-123"
    }

    result = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    assert result.returncode == 0  # Should NOT match
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_hook.py -k "keyword" -v
```

Expected: FAIL (keyword matching not implemented)

**Step 3: Implement keyword matching logic**

Update `docsearch.py`:

```python
#!/usr/bin/env python3
# ABOUTME: Claude Code PreToolUse hook that redirects WebSearch to local RAG databases
# ABOUTME: Intercepts documentation queries and routes them to LEANN MCP server

import json
import re
import sys
from pathlib import Path

def load_config():
    """Load config file from ~/.claude/hooks/docsearch-config.json

    Returns config dict or None if missing/invalid (fail open)
    """
    config_path = Path.home() / ".claude" / "hooks" / "docsearch-config.json"

    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            config = json.load(f)

        # Validate basic structure
        if not isinstance(config.get("databases"), list):
            sys.stderr.write("Invalid config: databases must be an array\n")
            return None

        return config

    except json.JSONDecodeError as e:
        sys.stderr.write(f"Invalid config JSON: {e}\n")
        return None
    except Exception as e:
        sys.stderr.write(f"Error loading config: {e}\n")
        return None

def find_matching_databases(query, config):
    """Find databases with keywords matching the query

    Args:
        query: Search query string
        config: Config dict with databases list

    Returns:
        List of matching database configs
    """
    matches = []
    query_lower = query.lower()

    for db in config["databases"]:
        for keyword in db.get("keywords", []):
            # Use word boundary regex for exact word matching
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, query_lower):
                matches.append(db)
                break  # Don't add same DB multiple times

    return matches

def main():
    try:
        hook_input = json.loads(sys.stdin.read())

        # Pass through non-WebSearch tools
        if hook_input.get("tool_name") != "WebSearch":
            sys.exit(0)

        # Load config - fail open if missing/invalid
        config = load_config()
        if config is None:
            sys.exit(0)

        # Extract query from tool input
        tool_input = hook_input.get("tool_input", {})
        query = tool_input.get("query", "")

        # Find matching databases
        matching_dbs = find_matching_databases(query, config)

        if not matching_dbs:
            # No matches - allow search through
            sys.exit(0)

        # Build denial response
        matched_keywords = [db["keywords"][0] for db in matching_dbs]
        keywords_str = "' and '".join(matched_keywords)

        if len(matching_dbs) == 1:
            db = matching_dbs[0]
            response = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Query matches '{matched_keywords[0]}' - using RAG database instead",
                    "additionalContext": f"This query should use the LEANN MCP tool '{db['mcp_tool_name']}' to search the {db['description']} RAG database at {db['path']} instead of web search."
                }
            }
        else:
            # Multiple matches
            tools_list = "\n".join([
                f"{i+1}. '{db['mcp_tool_name']}' for {db['description']} at {db['path']}"
                for i, db in enumerate(matching_dbs)
            ])
            response = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Query matches '{keywords_str}' - using RAG databases instead",
                    "additionalContext": f"This query matches multiple documentation databases. Please use these LEANN MCP tools IN PARALLEL:\n{tools_list}"
                }
            }

        print(json.dumps(response))
        sys.exit(2)

    except Exception:
        # Fail open - allow tool through on any error
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_hook.py -k "keyword" -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add docsearch.py tests/test_hook.py
git commit -m "feat: implement keyword matching with word boundaries and case-insensitive search"
```

---

## Task 5: State File Management for Escape Hatch

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`

**Step 1: Write failing tests for state management**

Add to `tests/test_hook.py`:

```python
def test_retry_with_same_params_allows_through(tmp_path, monkeypatch):
    """Retrying same search after denial should allow through"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text(
        Path("tests/fixtures/valid_config.json").read_text()
    )

    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {"query": "gitlab ci setup"},
        "session_id": "test-session-456"
    }

    # First call should deny
    result1 = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )
    assert result1.returncode == 2

    # Second call with same params should allow through
    result2 = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )
    assert result2.returncode == 0
    assert result2.stdout == ""

    # State file should be cleared
    state_file = config_dir / "docsearch-state-test-session-456.json"
    if state_file.exists():
        state = json.loads(state_file.read_text())
        assert state.get("last_denied") is None

def test_different_query_denies_again(tmp_path, monkeypatch):
    """Different query after denial should deny again"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text(
        Path("tests/fixtures/valid_config.json").read_text()
    )

    # First query
    result1 = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps({
            "hookEventName": "PreToolUse",
            "tool_name": "WebSearch",
            "tool_input": {"query": "gitlab ci setup"},
            "session_id": "test-789"
        }),
        capture_output=True,
        text=True
    )
    assert result1.returncode == 2

    # Different query with same keyword
    result2 = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps({
            "hookEventName": "PreToolUse",
            "tool_name": "WebSearch",
            "tool_input": {"query": "gitlab runners configuration"},
            "session_id": "test-789"
        }),
        capture_output=True,
        text=True
    )
    assert result2.returncode == 2

def test_session_isolation(tmp_path, monkeypatch):
    """Different sessions should have isolated state"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text(
        Path("tests/fixtures/valid_config.json").read_text()
    )

    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {"query": "gitlab ci setup"},
    }

    # Session 1 - deny
    result1 = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps({**hook_input, "session_id": "session-1"}),
        capture_output=True,
        text=True
    )
    assert result1.returncode == 2

    # Session 2 - should also deny (not affected by session 1)
    result2 = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps({**hook_input, "session_id": "session-2"}),
        capture_output=True,
        text=True
    )
    assert result2.returncode == 2
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_hook.py -k "retry or session" -v
```

Expected: FAIL (state management not implemented)

**Step 3: Implement state file management**

Update `docsearch.py`:

```python
#!/usr/bin/env python3
# ABOUTME: Claude Code PreToolUse hook that redirects WebSearch to local RAG databases
# ABOUTME: Intercepts documentation queries and routes them to LEANN MCP server

import json
import re
import sys
from pathlib import Path

def load_config():
    """Load config file from ~/.claude/hooks/docsearch-config.json

    Returns config dict or None if missing/invalid (fail open)
    """
    config_path = Path.home() / ".claude" / "hooks" / "docsearch-config.json"

    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            config = json.load(f)

        # Validate basic structure
        if not isinstance(config.get("databases"), list):
            sys.stderr.write("Invalid config: databases must be an array\n")
            return None

        return config

    except json.JSONDecodeError as e:
        sys.stderr.write(f"Invalid config JSON: {e}\n")
        return None
    except Exception as e:
        sys.stderr.write(f"Error loading config: {e}\n")
        return None

def get_state_file_path(session_id):
    """Get path to session-specific state file"""
    return Path.home() / ".claude" / "hooks" / f"docsearch-state-{session_id}.json"

def load_state(session_id):
    """Load state for session, returns None if not found or invalid"""
    state_path = get_state_file_path(session_id)

    if not state_path.exists():
        return None

    try:
        with open(state_path) as f:
            return json.load(f)
    except Exception:
        return None

def save_state(session_id, state):
    """Save state for session"""
    state_path = get_state_file_path(session_id)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        sys.stderr.write(f"Error saving state: {e}\n")

def clear_last_denied(session_id):
    """Clear last_denied from state"""
    state = load_state(session_id) or {}
    state["last_denied"] = None
    save_state(session_id, state)

def params_match(tool_input, last_denied):
    """Check if tool_input matches last_denied params"""
    if not last_denied:
        return False

    # Compare query
    if tool_input.get("query") != last_denied.get("query"):
        return False

    # Compare domains as sets (order-independent)
    allowed1 = set(tool_input.get("allowed_domains", []))
    allowed2 = set(last_denied.get("allowed_domains", []))
    if allowed1 != allowed2:
        return False

    blocked1 = set(tool_input.get("blocked_domains", []))
    blocked2 = set(last_denied.get("blocked_domains", []))
    if blocked1 != blocked2:
        return False

    return True

def find_matching_databases(query, config):
    """Find databases with keywords matching the query

    Args:
        query: Search query string
        config: Config dict with databases list

    Returns:
        List of matching database configs
    """
    matches = []
    query_lower = query.lower()

    for db in config["databases"]:
        for keyword in db.get("keywords", []):
            # Use word boundary regex for exact word matching
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, query_lower):
                matches.append(db)
                break  # Don't add same DB multiple times

    return matches

def main():
    try:
        hook_input = json.loads(sys.stdin.read())

        # Pass through non-WebSearch tools
        if hook_input.get("tool_name") != "WebSearch":
            sys.exit(0)

        # Load config - fail open if missing/invalid
        config = load_config()
        if config is None:
            sys.exit(0)

        # Extract params
        session_id = hook_input.get("session_id", "unknown")
        tool_input = hook_input.get("tool_input", {})

        # Check escape hatch - is this a retry?
        state = load_state(session_id)
        if state and params_match(tool_input, state.get("last_denied")):
            # This is a retry - allow through and clear state
            clear_last_denied(session_id)
            sys.exit(0)

        # Extract query
        query = tool_input.get("query", "")

        # Find matching databases
        matching_dbs = find_matching_databases(query, config)

        if not matching_dbs:
            # No matches - allow search through
            sys.exit(0)

        # Save state before denying
        save_state(session_id, {
            "last_denied": {
                "query": tool_input.get("query"),
                "allowed_domains": tool_input.get("allowed_domains", []),
                "blocked_domains": tool_input.get("blocked_domains", [])
            }
        })

        # Build denial response
        matched_keywords = [db["keywords"][0] for db in matching_dbs]
        keywords_str = "' and '".join(matched_keywords)

        if len(matching_dbs) == 1:
            db = matching_dbs[0]
            response = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Query matches '{matched_keywords[0]}' - using RAG database instead",
                    "additionalContext": f"This query should use the LEANN MCP tool '{db['mcp_tool_name']}' to search the {db['description']} RAG database at {db['path']} instead of web search."
                }
            }
        else:
            # Multiple matches
            tools_list = "\n".join([
                f"{i+1}. '{db['mcp_tool_name']}' for {db['description']} at {db['path']}"
                for i, db in enumerate(matching_dbs)
            ])
            response = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Query matches '{keywords_str}' - using RAG databases instead",
                    "additionalContext": f"This query matches multiple documentation databases. Please use these LEANN MCP tools IN PARALLEL:\n{tools_list}"
                }
            }

        print(json.dumps(response))
        sys.exit(2)

    except Exception:
        # Fail open - allow tool through on any error
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_hook.py -k "retry or session" -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add docsearch.py tests/test_hook.py
git commit -m "feat: implement state file management for escape hatch retry logic"
```

---

## Task 6: Multi-Keyword Detection

**Files:**
- Modify: `tests/test_hook.py`
- Create: `tests/fixtures/multi_db_config.json`

**Step 1: Create multi-database config fixture**

Create `tests/fixtures/multi_db_config.json`:

```json
{
  "databases": [
    {
      "keywords": ["gitlab", "gl"],
      "path": "/test/gitlab",
      "mcp_tool_name": "mcp__leann__search",
      "description": "GitLab documentation"
    },
    {
      "keywords": ["kubernetes", "k8s"],
      "path": "/test/k8s",
      "mcp_tool_name": "mcp__leann__search",
      "description": "Kubernetes documentation"
    }
  ]
}
```

**Step 2: Write failing test for multi-keyword queries**

Add to `tests/test_hook.py`:

```python
def test_multiple_keyword_match_denies_with_all_tools(tmp_path, monkeypatch):
    """Query matching multiple keywords should suggest all tools in parallel"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text(
        Path("tests/fixtures/multi_db_config.json").read_text()
    )

    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {"query": "how to deploy gitlab on kubernetes"},
        "session_id": "test-multi"
    }

    result = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    assert result.returncode == 2
    output = json.loads(result.stdout)

    context = output["hookSpecificOutput"]["additionalContext"]
    reason = output["hookSpecificOutput"]["permissionDecisionReason"]

    # Should mention both keywords
    assert "gitlab" in reason.lower() or "gl" in reason.lower()
    assert "kubernetes" in reason.lower() or "k8s" in reason.lower()

    # Should mention parallel execution
    assert "PARALLEL" in context

    # Should mention both databases
    assert "GitLab" in context
    assert "Kubernetes" in context
```

**Step 3: Run test to verify current implementation passes**

```bash
pytest tests/test_hook.py::test_multiple_keyword_match_denies_with_all_tools -v
```

Expected: PASS (already implemented in Task 4)

**Step 4: Commit test**

```bash
git add tests/
git commit -m "test: add multi-keyword detection test coverage"
```

---

## Task 7: Domain Filtering Support

**Files:**
- Modify: `tests/test_hook.py`

**Step 1: Write tests for domain filtering in state**

Add to `tests/test_hook.py`:

```python
def test_retry_with_different_domains_denies_again(tmp_path, monkeypatch):
    """Retry with different domain filters should deny again"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text(
        Path("tests/fixtures/valid_config.json").read_text()
    )

    # First call with allowed_domains
    result1 = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps({
            "hookEventName": "PreToolUse",
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "gitlab ci setup",
                "allowed_domains": ["docs.gitlab.com"]
            },
            "session_id": "domain-test"
        }),
        capture_output=True,
        text=True
    )
    assert result1.returncode == 2

    # Second call with different allowed_domains
    result2 = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps({
            "hookEventName": "PreToolUse",
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "gitlab ci setup",
                "allowed_domains": ["stackoverflow.com"]
            },
            "session_id": "domain-test"
        }),
        capture_output=True,
        text=True
    )
    assert result2.returncode == 2  # Should deny again (different params)

def test_retry_with_same_domains_allows_through(tmp_path, monkeypatch):
    """Retry with same domain filters should allow through"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text(
        Path("tests/fixtures/valid_config.json").read_text()
    )

    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {
            "query": "gitlab ci setup",
            "allowed_domains": ["docs.gitlab.com"],
            "blocked_domains": ["spam.com"]
        },
        "session_id": "domain-test-2"
    }

    # First call should deny
    result1 = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )
    assert result1.returncode == 2

    # Second call with same params should allow
    result2 = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )
    assert result2.returncode == 0
```

**Step 2: Run tests to verify they pass**

```bash
pytest tests/test_hook.py -k "domain" -v
```

Expected: PASS (already implemented in Task 5)

**Step 3: Commit tests**

```bash
git add tests/test_hook.py
git commit -m "test: add domain filtering test coverage for state comparison"
```

---

## Task 8: Error Handling Edge Cases

**Files:**
- Modify: `tests/test_hook.py`

**Step 1: Write tests for error scenarios**

Add to `tests/test_hook.py`:

```python
def test_corrupted_state_file_continues(tmp_path, monkeypatch):
    """Corrupted state file should be treated as no previous denial"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text(
        Path("tests/fixtures/valid_config.json").read_text()
    )

    # Create corrupted state file
    (config_dir / "docsearch-state-corrupt.json").write_text("invalid{json")

    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {"query": "gitlab ci"},
        "session_id": "corrupt"
    }

    result = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    # Should deny (not crash)
    assert result.returncode == 2

def test_invalid_hook_input_fails_open(tmp_path, monkeypatch):
    """Invalid hook input JSON should allow through"""
    result = subprocess.run(
        ["python3", "docsearch.py"],
        input="invalid json{",
        capture_output=True,
        text=True
    )

    assert result.returncode == 0

def test_missing_query_field_fails_open(tmp_path, monkeypatch):
    """Missing query field should allow through"""
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".claude" / "hooks"
    config_dir.mkdir(parents=True)
    (config_dir / "docsearch-config.json").write_text(
        Path("tests/fixtures/valid_config.json").read_text()
    )

    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {},  # No query field
        "session_id": "no-query"
    }

    result = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
```

**Step 2: Run tests to verify they pass**

```bash
pytest tests/test_hook.py -k "corrupted or invalid or missing" -v
```

Expected: PASS (already implemented with fail-open strategy)

**Step 3: Commit tests**

```bash
git add tests/test_hook.py
git commit -m "test: add error handling test coverage for edge cases"
```

---

## Task 9: Documentation and Installation Instructions

**Files:**
- Modify: `README.md`

**Step 1: Write comprehensive README**

Replace `README.md`:

```markdown
# DocSearch Hook for Claude Code

A Claude Code PreToolUse hook that intelligently redirects documentation-related WebSearch queries to local RAG databases via the LEANN MCP server.

## Features

- **Automatic Search Interception**: Detects documentation queries and redirects to local RAG databases
- **Intelligent Escape Hatch**: Allows Claude to retry web searches if RAG results are insufficient
- **Multi-Database Support**: Query multiple documentation sources in parallel
- **Session Isolation**: Per-session state management prevents cross-session interference
- **Fail-Open Design**: Never breaks Claude's functionality - errors allow searches through

## Prerequisites

1. **Python 3.12+** (tested with Python 3.14)
2. **LEANN** installed and configured
3. **LEANN MCP server** configured in Claude Code's MCP settings
4. **RAG databases** built using LEANN tools

## Installation

### 1. Install the Hook Script

```bash
# Clone or download this repository
git clone https://github.com/yourusername/docsearch-hook.git
cd docsearch-hook

# Copy hook to Claude Code hooks directory
mkdir -p ~/.claude/hooks/PreToolUse
cp docsearch.py ~/.claude/hooks/PreToolUse/docsearch.py
chmod +x ~/.claude/hooks/PreToolUse/docsearch.py
```

### 2. Create Configuration File

```bash
# Copy example config
cp config.example.json ~/.claude/hooks/docsearch-config.json

# Edit with your database paths and keywords
# Example config structure:
{
  "databases": [
    {
      "keywords": ["gitlab", "gl", "gitlab-ci"],
      "path": "/Users/yourname/.leann/databases/gitlab",
      "mcp_tool_name": "mcp__leann__search",
      "description": "GitLab documentation from docs.gitlab.com"
    }
  ]
}
```

### 3. Verify LEANN MCP Server Configuration

Ensure your `~/.claude/mcp-config.json` includes the LEANN server:

```json
{
  "mcpServers": {
    "leann": {
      "command": "leann",
      "args": ["mcp"]
    }
  }
}
```

### 4. Test the Setup

```bash
# Run tests
pytest tests/

# Start Claude Code and try a query
# Example: "How do I configure GitLab CI runners?"
# The hook should intercept and suggest using the RAG database
```

## Configuration

### Config File Location

`~/.claude/hooks/docsearch-config.json`

### Schema

```json
{
  "databases": [
    {
      "keywords": ["keyword1", "keyword2"],
      "path": "/absolute/path/to/database",
      "mcp_tool_name": "mcp__leann__search",
      "description": "Human-readable description"
    }
  ]
}
```

### Fields

- **keywords** (required): Array of strings to match in queries (case-insensitive, word-boundary matching)
- **path** (required): Absolute path to LEANN database directory
- **mcp_tool_name** (required): Exact MCP tool name (usually `mcp__leann__search`)
- **description** (required): Description shown to Claude in denial context

## How It Works

```
User asks: "How to configure GitLab CI runners?"
    ↓
Hook detects "gitlab" keyword → Denies WebSearch
    ↓
Claude receives denial + context about RAG database
    ↓
Claude calls mcp__leann__search with GitLab database
    ↓
If successful → User gets RAG-based answer
If unsuccessful → Claude retries WebSearch → Hook allows through
```

## State Management

- **Per-session state**: Each Claude Code session has isolated state in `~/.claude/hooks/docsearch-state-{session_id}.json`
- **Escape hatch**: If Claude retries the exact same search (same query and domain filters), the hook allows it through
- **Automatic cleanup**: State is cleared after successful retry

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/ -k "keyword" -v      # Keyword matching tests
pytest tests/ -k "retry" -v        # Escape hatch tests
pytest tests/ -k "session" -v      # Session isolation tests

# Run with coverage
pytest tests/ --cov=docsearch --cov-report=html
```

## Troubleshooting

### Hook Not Triggering

1. Check hook script location: `~/.claude/hooks/PreToolUse/docsearch.py`
2. Verify executable permissions: `chmod +x ~/.claude/hooks/PreToolUse/docsearch.py`
3. Check config file exists: `~/.claude/hooks/docsearch-config.json`

### Config File Errors

- Validate JSON syntax: `python3 -m json.tool ~/.claude/hooks/docsearch-config.json`
- Check stderr output when running Claude Code
- Verify all required fields are present

### State File Issues

- State files location: `~/.claude/hooks/docsearch-state-*.json`
- Delete stale state files manually if needed
- Each session creates its own state file

## Development

### Running Tests During Development

```bash
# Install pytest
pip install pytest

# Run tests with output
pytest tests/ -v -s

# Run specific test
pytest tests/test_hook.py::test_single_keyword_match_denies -v
```

### Adding New Databases

1. Build LEANN database using LEANN tools
2. Add entry to `~/.claude/hooks/docsearch-config.json`
3. Test with relevant query in Claude Code

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Future Enhancements

See [GitHub Issues](https://github.com/yourusername/docsearch-hook/issues) for planned features:

- CLI setup command for automated database creation
- Database sharing functionality
- Community database repository
```

**Step 2: Commit README**

```bash
git add README.md
git commit -m "docs: add comprehensive installation and usage documentation"
```

---

## Task 10: Integration Testing Setup

**Files:**
- Create: `tests/integration/test_full_flow.py`
- Create: `tests/integration/README.md`

**Step 1: Create integration test directory**

```bash
mkdir -p tests/integration
```

**Step 2: Create integration test README**

Create `tests/integration/README.md`:

```markdown
# Integration Tests

These tests require a real LEANN MCP server configuration and database.

## Setup

1. Ensure LEANN is installed
2. Build a test database
3. Configure MCP server in Claude Code
4. Run integration tests manually (not in CI)

## Running

```bash
# Skip in normal test runs
pytest tests/test_hook.py

# Run integration tests manually
pytest tests/integration/ -v
```

## Note

Integration tests are provided as examples and documentation.
They require manual setup and are not run in automated CI.
```

**Step 3: Create example integration test**

Create `tests/integration/test_full_flow.py`:

```python
# ABOUTME: Integration tests for full docsearch hook flow with real LEANN MCP server
# ABOUTME: Requires manual setup - not run in automated CI

import json
import subprocess
import pytest

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

@pytest.mark.skip(reason="Requires manual LEANN setup")
def test_full_flow_with_real_mcp():
    """
    End-to-end test with real LEANN MCP server

    Manual setup required:
    1. Build LEANN database for a test documentation site
    2. Configure ~/.claude/hooks/docsearch-config.json
    3. Ensure LEANN MCP server is running
    4. Update this test with your actual config
    """
    # This is a template - customize for your setup
    hook_input = {
        "hookEventName": "PreToolUse",
        "tool_name": "WebSearch",
        "tool_input": {"query": "your test query here"},
        "session_id": "integration-test"
    }

    result = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    # First call should deny
    assert result.returncode == 2

    # At this point, you would manually verify:
    # 1. Claude Code receives the denial context
    # 2. Claude calls the MCP tool
    # 3. MCP returns results or fails
    # 4. If MCP fails, Claude retries WebSearch
    # 5. Hook allows the retry through

    # Retry should allow through
    result2 = subprocess.run(
        ["python3", "docsearch.py"],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    assert result2.returncode == 0
```

**Step 4: Update pytest configuration**

Create `pytest.ini`:

```ini
[pytest]
markers =
    integration: marks tests as integration tests (deselect with '-m "not integration"')

# By default, skip integration tests
addopts = -m "not integration"
```

**Step 5: Commit integration test setup**

```bash
git add tests/integration/ pytest.ini
git commit -m "test: add integration test framework and documentation"
```

---

## Task 11: Final Validation and Cleanup

**Files:**
- Create: `.github/workflows/test.yml` (optional)
- Modify: `README.md`

**Step 1: Run full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: All unit tests PASS

**Step 2: Verify hook script is executable**

```bash
ls -la docsearch.py
```

Expected: `-rwxr-xr-x` (executable flag set)

**Step 3: Validate example config**

```bash
python3 -m json.tool config.example.json > /dev/null && echo "Valid JSON"
```

Expected: "Valid JSON"

**Step 4: Run hook manually with example input**

```bash
echo '{
  "hookEventName": "PreToolUse",
  "tool_name": "WebSearch",
  "tool_input": {"query": "test"},
  "session_id": "manual-test"
}' | python3 docsearch.py
echo "Exit code: $?"
```

Expected: Exit code 0 (no config file, fails open)

**Step 5: Check for any TODO or FIXME comments**

```bash
grep -r "TODO\|FIXME" docsearch.py tests/
```

Expected: No output (or document any intentional TODOs)

**Step 6: Verify all files have proper headers**

```bash
head -n 2 docsearch.py tests/test_hook.py
```

Expected: All files have "ABOUTME" comment headers

**Step 7: Final commit**

```bash
git add -A
git commit -m "chore: final validation and cleanup"
```

---

## Task 12: Create GitHub Issues for Future Work

**Files:**
- Create issues manually in GitHub (or use `gh` CLI)

**Step 1: Create database sharing issue**

```bash
gh issue create --title "Enable sharing pre-built RAG databases" --body "$(cat <<'EOF'
## Goal
Allow users to share pre-built LEANN databases to reduce setup friction.

## Features
- Export database metadata and files in shareable format
- Import shared databases with verification
- Community repository of common documentation databases (GitLab, K8s, etc.)

## Benefits
- Reduce setup friction for new users
- Standardize database quality for popular documentation sources
- Enable community contribution model

## Related
See design document section "Future Work - Issue 1"
EOF
)"
```

**Step 2: Create CLI setup command issue**

```bash
gh issue create --title "Add CLI command for automated database creation" --body "$(cat <<'EOF'
## Goal
Provide automated database creation to eliminate manual LEANN tool usage.

## Command Interface
```bash
docsearch-hook setup <keyword> <url>
```

## Features
- Crawl documentation website using LEANN
- Build RAG database automatically
- Add entry to config file
- Validate MCP server configuration

## Benefits
- Eliminates manual LEANN tool usage
- Reduces errors in database creation
- Streamlines onboarding experience

## Related
See design document section "Future Work - Issue 2"
EOF
)"
```

**Step 3: Commit (if using file-based issue tracking)**

```bash
git add -A
git commit -m "docs: create GitHub issues for future enhancements"
```

---

## Completion Checklist

- [ ] All unit tests passing
- [ ] Config example provided
- [ ] README.md complete with installation instructions
- [ ] Hook script executable
- [ ] State file management working
- [ ] Escape hatch retry logic tested
- [ ] Multi-keyword detection tested
- [ ] Error handling with fail-open validated
- [ ] Integration test framework documented
- [ ] Future work issues created

## Post-Implementation

After completing all tasks:

1. **Manual testing**: Install hook in real Claude Code environment
2. **Documentation review**: Ensure README is accurate
3. **Performance check**: Verify hook doesn't slow down Claude noticeably
4. **Edge case validation**: Test with real-world queries

---

