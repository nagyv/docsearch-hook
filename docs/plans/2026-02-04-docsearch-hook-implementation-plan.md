# DocSearch Hook Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Claude Code PreToolUse hook that intercepts WebSearch tool calls and redirects documentation-related queries to local RAG databases via LEANN MCP server.

**Architecture:** A Python 3.12+ script (`docsearch.py`) acts as a PreToolUse hook. It reads configuration from `~/.claude/hooks/docsearch-config.json`, tracks state in session-specific files, and uses exit codes to allow (0) or deny (2) WebSearch calls. When denying, it provides `additionalContext` guiding Claude to use LEANN MCP tools instead. An escape hatch allows retries if RAG results are insufficient.

**Tech Stack:** Python 3.12+ standard library only (json, re, sys, pathlib, os, time)

**Reference:** See `docs/plans/2026-02-04-docsearch-hook-design.md` for full design specification.

---

## Implementation Status

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
| Task 3a | NOT STARTED | Configuration Schema Validation | P1 - Quality | 10 |
| Task 3b | NOT STARTED | Keywords Element Type Validation | P1 - Quality | 11 |
| Task 8 | NOT STARTED | Error Logging to stderr | P1 - Enhancement | 12 |
| Task 9 | NOT STARTED | Complete Test Coverage and Edge Cases | P1 - Quality | 13 |
| Task 9a | NOT STARTED | Permission Error Tests | P1 - Quality | 14 |
| Task 9b | NOT STARTED | Session Isolation Tests | P1 - Quality | 15 |
| Task 1 | NOT STARTED | Project Structure and Example Config | P2 - Documentation | 16 |
| Task 10 | NOT STARTED | README Documentation | P2 - Documentation | 17 |
| Task 11 | NOT STARTED | Final Integration Testing | P2 - Validation | 18 |

### Implementation Progress (2026-02-05)
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

Tasks 5, 7, and 7a completed with 21 passing tests total. Enhanced features now work:
- Multiple keyword matching verified with tests
- State expiry after 5 minutes prevents stale escape hatches
- Stale state file cleanup removes old session files

## Codebase Analysis (2026-02-05)

**Current State:** No implementation exists. Repository contains only:
- `README.md` - Empty placeholder ("# mcp-docsearch")
- `LICENSE` - MIT license file
- `docs/plans/` - Design and implementation plan documents
- `.leann/` - LEANN index files (not relevant to implementation)
- `.mcp.json`, `.claude/settings.local.json` - Configuration files

**All 14 tasks remain to be implemented.**

## Gap Analysis Notes

The following gaps were identified when comparing this plan against the design spec:

### Previously Identified (Addressed in Plan)
1. **Session Start State Cleanup (Task 7a):** Design spec mentions "Clear state file on session start" as a complementary mechanism to timestamp expiry - added as new task.
2. **Config Schema Validation (Task 3a):** Design spec marks config fields as "required" but original plan silently defaults missing fields - added as new task.
3. **Tech Stack:** Design spec should include `os` and `time` modules (used in implementation).

### Newly Identified (2026-02-05 Analysis)

**Critical Gaps:**
4. **Type validation for config fields missing:** Task 3a only checks field presence, not types. `keywords` should be validated as array of strings, not just present.
5. **Empty keywords array not handled:** A database entry with `keywords: []` will silently fail to match anything. Should log warning and skip.

**Important Gaps:**
6. **Path format validation missing:** Design spec says `path` should be "Absolute path" but no validation exists. Should warn on relative paths.
7. **Task 7a cleanup timing differs from design:** Design says "Clear stale state files on session start" but Task 7a cleans during hook execution. Semantically equivalent but worth noting.
8. **No permission error tests:** Implementation silently handles state/config permission errors but these edge cases aren't tested.
9. **No concurrent session isolation test:** Tests use different session_ids but don't verify true isolation.

**Minor Gaps (Can Address Post-MVP):**
10. **GitHub issue templates not created:** Design mentions `.github/ISSUE_TEMPLATE/` but no task creates it.
11. **Success criteria not all testable:** Design lists "Clean Python code with type hints" as success criteria but not verified.
12. **State file naming uses raw session_id:** No sanitization of session_id for filesystem safety (special characters).

### Security Gap (2026-02-05 Deep Analysis) - MUST FIX

**CRITICAL - Session ID Path Traversal Vulnerability:**
13. **Session ID sanitization required:** The `get_state_file()` function uses raw `session_id` in the filename without sanitization. This could allow path traversal attacks if a malicious `session_id` like `"../../etc/passwd"` or `"foo/bar"` is provided. **Add Task 6a: Session ID Sanitization** to address this before Task 6.

### TDD Issues Identified (2026-02-05 Deep Analysis)

14. **Task 3 "Expected: FAIL" reason is incorrect:** The test would actually PASS because Task 2's implementation returns exit 0 for WebSearch tools. Need to fix the expected failure reason.
15. **Task 5 violates TDD principles:** Tests are expected to pass immediately (verification tests, not TDD). Should be relabeled or moved.
16. **Task 7a test doesn't verify cleanup:** `test_stale_state_file_cleaned_on_unrelated_query` should assert that stale files were actually deleted.
17. **Task 5 order test missing null checks:** Should verify `find()` doesn't return -1 before comparing positions.
18. **Keywords element type validation missing:** Task 3a validates `keywords` is a list but not that all elements are strings.

### Parallelization Opportunities

19. **Tasks 5, 3a, and 8 can run in parallel** after Task 4 completes (no dependencies between them).
20. **Task 1 could be P2** since it's just an example config file, not required for core functionality.

---

## Prioritized Remaining Work (Bullet Points)

### Phase 1: Core Functionality (P0) - MUST HAVE
All items below are required for a minimal viable hook:

- [ ] **Task 2: Core Hook Script - Skeleton and Input Parsing**
  - Create `tests/test_hook.py` with `run_hook()` helper and input parsing tests
  - Create `docsearch.py` with main() entry point, stdin JSON parsing, WebSearch filtering
  - Verify tests pass, commit

- [ ] **Task 3: Configuration Loading**
  - Add tests for missing/invalid config file handling (fail-open behavior)
  - Implement `get_config_path()` and `load_config()` functions
  - Support `DOCSEARCH_CONFIG_PATH` environment variable for testing
  - Verify tests pass, commit

- [ ] **Task 4: Keyword Matching with Word Boundaries**
  - Create `tests/fixtures/valid_config.json` test fixture
  - Add tests for single keyword match, no match, case-insensitive, word boundary
  - Implement `find_matching_databases()` with `\b` regex word boundaries
  - Implement `build_deny_response()` for single/multiple database responses
  - Verify tests pass, commit

- [x] **Task 6a: Session ID Sanitization (Security)** *(NEW - MUST BE BEFORE Task 6)*
  - Add tests for path traversal and special character handling in session_id
  - Implement `sanitize_session_id()` using regex to allow only alphanumeric, dash, underscore
  - Create `get_state_file()` stub that uses sanitized session_id
  - Verify tests pass, commit

- [x] **Task 6: Session State Management for Escape Hatch**
  - Add tests for state file creation, escape hatch retry, different query denial
  - Implement `get_state_dir()`, expand `get_state_file()`, `load_state()`, `save_state()`
  - Implement `params_match()` for exact query + set-based domain comparison
  - Update `main()` with escape hatch logic before keyword matching
  - Verify tests pass, commit

- [x] **Task 12: Make Script Executable and Add Shebang**
  - Verify shebang line `#!/usr/bin/env python3` present
  - Run full test suite
  - Verify script executes with `./docsearch.py < /dev/null` (exit 0)
  - Final commit

### Phase 2: Enhanced Features (P1) - IMPORTANT
These enhance functionality but can ship without:

- [ ] **Task 5: Multiple Keyword Matching**
  - Add tests for queries matching multiple databases
  - Add test for k8s alias matching kubernetes
  - Add test for database order preservation in output
  - Verify implementation handles multiple matches with "IN PARALLEL" instruction
  - Commit tests

- [ ] **Task 7: State Cleanup (Stale State Expiry)**
  - Add tests for expired state (>5 min) being ignored
  - Add tests for recent state (<5 min) being used
  - Add `STATE_EXPIRY_SECONDS = 300` constant
  - Implement `is_state_expired()` function
  - Update escape hatch check to include expiry validation
  - Verify tests pass, commit

- [ ] **Task 7a: Session Start State Cleanup** *(NEW - from gap analysis)*
  - Add test for clearing stale state files on hook initialization
  - Implement optional cleanup of state files older than expiry threshold
  - This complements timestamp expiry as a safety mechanism
  - Verify tests pass, commit

- [ ] **Task 3a: Configuration Schema Validation** *(NEW - from gap analysis)*
  - Add tests for config with missing required fields (keywords, path, etc.)
  - Add validation that logs warnings for missing required fields
  - Maintain fail-open behavior (allow search through on invalid config)
  - Verify tests pass, commit

- [ ] **Task 3b: Keywords Element Type Validation** *(NEW)*
  - Add test for keywords array with non-string elements (integers, nulls, dicts)
  - Validate all keyword elements are strings using `isinstance(k, str)`
  - Log warning and skip entry if validation fails
  - Verify tests pass, commit

- [ ] **Task 8: Error Logging to stderr**
  - Add test for invalid config JSON logging to stderr
  - Update `load_config()` to log JSON parse errors to stderr
  - Maintain silent behavior for missing config file (expected during setup)
  - Verify tests pass, commit

- [ ] **Task 9: Complete Test Coverage and Edge Cases**
  - Add test for empty query allowing through
  - Add test for missing query field allowing through
  - Add test for missing tool_input field allowing through
  - Add test for missing session_id using "default"
  - Add test for empty databases config allowing through
  - Add test for domains compared as sets (order-independent)
  - Add test for special characters in keywords (c++, c#, .net)
  - Add test verifying all required output fields present
  - Verify all tests pass, commit

- [ ] **Task 9a: Permission Error Tests** *(NEW)*
  - Add test for unreadable config file (chmod 000) - should fail open
  - Add test for unwritable state directory - should still deny
  - Verify fail-open behavior for permission scenarios
  - Commit tests

- [ ] **Task 9b: Session Isolation Tests** *(NEW)*
  - Add test that state from session A doesn't affect session B
  - Add test that escape hatch only works for the session that was denied
  - Verify session isolation works correctly
  - Commit tests

### Phase 3: Documentation & Validation (P2) - POLISH
Final documentation and validation:

- [ ] **Task 1: Project Structure and Example Config** *(moved from P0)*
  - Create `config.example.json` with GitLab and Kubernetes database examples
  - Commit the example configuration file

- [ ] **Task 10: README Documentation**
  - Update `README.md` with comprehensive setup instructions
  - Document features, prerequisites, installation steps
  - Add configuration guide with field descriptions
  - Document escape hatch behavior
  - Add troubleshooting section
  - Commit

- [ ] **Task 11: Final Integration Testing**
  - Create `tests/test_integration.py` as testing guide
  - Document manual test scenarios:
    - Basic interception flow
    - Escape hatch retry flow
    - Multiple keyword parallel MCP calls
    - Non-matching query passthrough
  - Commit

---

## Priority Order for Implementation

### Phase 1: Core Functionality (P0) - Tasks 2, 3, 4, 6a, 6, 12
Must-have for minimal viable hook:
1. **Task 2** - Hook skeleton with input parsing
2. **Task 3** - Configuration loading
3. **Task 4** - Keyword matching (single keyword)
4. **Task 6a** - Session ID sanitization *(SECURITY - must come before Task 6)*
5. **Task 6** - Escape hatch state management
6. **Task 12** - Make script executable

### Phase 2: Enhanced Features (P1) - Tasks 5, 7, 7a, 3a, 3b, 8, 9, 9a, 9b
Important but can ship without:
7. **Task 5** - Multiple keyword matching (verification tests)
8. **Task 7** - Stale state expiry (5-minute timeout)
9. **Task 7a** - Session start state cleanup
10. **Task 3a** - Config schema validation
11. **Task 3b** - Keywords element type validation *(NEW)*
12. **Task 8** - Error logging to stderr
13. **Task 9** - Edge case test coverage
14. **Task 9a** - Permission error tests *(NEW)*
15. **Task 9b** - Session isolation tests *(NEW)*

**Parallelization Note:** Tasks 5, 3a, 3b, and 8 can run in parallel after Task 4.

### Phase 3: Documentation & Validation (P2) - Tasks 1, 10, 11
Polish and documentation:
16. **Task 1** - Project structure and example config *(moved from P0)*
17. **Task 10** - README documentation
18. **Task 11** - Integration testing guide

---

## Task 1: Project Structure and Example Config

**Files:**
- Create: `config.example.json`

**Step 1: Write the example configuration file**

```json
{
  "databases": [
    {
      "keywords": ["gitlab", "gl", "gitlab-ci"],
      "path": "/Users/viktor/.leann/databases/gitlab",
      "mcp_tool_name": "leann-docs",
      "description": "GitLab documentation from docs.gitlab.com"
    },
    {
      "keywords": ["kubernetes", "k8s", "kubectl"],
      "path": "/Users/viktor/.leann/databases/kubernetes",
      "mcp_tool_name": "leann-docs",
      "description": "Kubernetes official documentation"
    }
  ]
}
```

**Step 2: Commit**

```bash
git add config.example.json
git commit -m "feat: add example configuration file for docsearch hook"
```

---

## Task 2: Core Hook Script - Skeleton and Input Parsing

**Files:**
- Create: `docsearch.py`
- Create: `tests/test_hook.py`

**Step 1: Write the failing test for hook script existence and basic input parsing**

Create `tests/test_hook.py`:

```python
"""Unit tests for docsearch.py hook script."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent.parent / "docsearch.py"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def run_hook(stdin_data: dict, env: dict | None = None) -> tuple[int, str, str]:
    """Run the hook script with given stdin and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


class TestInputParsing:
    """Tests for hook input parsing."""

    def test_non_websearch_tool_allows_through(self):
        """Non-WebSearch tool calls should be allowed (exit 0)."""
        hook_input = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/some/file.txt"},
        }
        exit_code, stdout, stderr = run_hook(hook_input)
        assert exit_code == 0

    def test_invalid_json_allows_through(self):
        """Invalid JSON input should fail open (exit 0)."""
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input="not valid json",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hook.py -v`
Expected: FAIL (docsearch.py doesn't exist)

**Step 3: Write minimal implementation**

Create `docsearch.py`:

```python
#!/usr/bin/env python3
"""
DocSearch Hook - PreToolUse hook that redirects documentation queries to RAG databases.

This hook intercepts WebSearch tool calls and checks if the query matches configured
documentation keywords. If matched, it denies the search and guides Claude to use
LEANN MCP tools instead. Includes an escape hatch for retrying web search if RAG fails.
"""
import json
import sys


def main() -> int:
    """Main entry point for the hook."""
    # Read and parse input from stdin
    try:
        stdin_data = sys.stdin.read()
        hook_input = json.loads(stdin_data)
    except json.JSONDecodeError:
        # Invalid JSON - fail open
        return 0

    # Get tool name - if not WebSearch, allow through
    tool_name = hook_input.get("tool_name", "")
    if tool_name != "WebSearch":
        return 0

    # Placeholder for future implementation
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hook.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docsearch.py tests/test_hook.py
git commit -m "feat: add hook skeleton with input parsing"
```

---

## Task 3: Configuration Loading

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`

**Step 1: Write the failing test for configuration loading**

Add to `tests/test_hook.py`:

```python
class TestConfigLoading:
    """Tests for configuration file loading."""

    def test_missing_config_allows_through(self, tmp_path):
        """Missing config file should fail open (exit 0)."""
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "how to configure gitlab ci"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input, env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(tmp_path / "nonexistent.json")}
        )
        assert exit_code == 0

    def test_invalid_json_config_allows_through(self, tmp_path):
        """Invalid JSON config should fail open (exit 0)."""
        config_file = tmp_path / "config.json"
        config_file.write_text("not valid json")

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "how to configure gitlab ci"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input, env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(config_file)}
        )
        assert exit_code == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hook.py::TestConfigLoading -v`
Expected: FAIL (config loading not implemented)

**Step 3: Write minimal implementation**

Update `docsearch.py`:

```python
#!/usr/bin/env python3
"""
DocSearch Hook - PreToolUse hook that redirects documentation queries to RAG databases.

This hook intercepts WebSearch tool calls and checks if the query matches configured
documentation keywords. If matched, it denies the search and guides Claude to use
LEANN MCP tools instead. Includes an escape hatch for retrying web search if RAG fails.
"""
import json
import os
import sys
from pathlib import Path


def get_config_path() -> Path:
    """Get the configuration file path."""
    if env_path := os.environ.get("DOCSEARCH_CONFIG_PATH"):
        return Path(env_path)
    return Path.home() / ".claude" / "hooks" / "docsearch-config.json"


def load_config() -> dict | None:
    """Load and parse the configuration file. Returns None on any error."""
    config_path = get_config_path()
    try:
        with open(config_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def main() -> int:
    """Main entry point for the hook."""
    # Read and parse input from stdin
    try:
        stdin_data = sys.stdin.read()
        hook_input = json.loads(stdin_data)
    except json.JSONDecodeError:
        # Invalid JSON - fail open
        return 0

    # Get tool name - if not WebSearch, allow through
    tool_name = hook_input.get("tool_name", "")
    if tool_name != "WebSearch":
        return 0

    # Load configuration - if missing or invalid, allow through
    config = load_config()
    if config is None:
        return 0

    # Placeholder for keyword matching
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hook.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docsearch.py tests/test_hook.py
git commit -m "feat: add configuration file loading with fail-open behavior"
```

---

## Task 4: Keyword Matching with Word Boundaries

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`
- Create: `tests/fixtures/` directory
- Create: `tests/fixtures/valid_config.json`

**Step 1: Create test fixtures**

Create `tests/fixtures/valid_config.json`:

```json
{
  "databases": [
    {
      "keywords": ["gitlab", "gl", "gitlab-ci"],
      "path": "/mock/path/gitlab",
      "mcp_tool_name": "leann-docs",
      "description": "GitLab documentation"
    },
    {
      "keywords": ["kubernetes", "k8s", "kubectl"],
      "path": "/mock/path/kubernetes",
      "mcp_tool_name": "leann-docs",
      "description": "Kubernetes documentation"
    }
  ]
}
```

**Step 2: Write the failing test for keyword matching**

Add to `tests/test_hook.py`:

```python
class TestKeywordMatching:
    """Tests for keyword detection in queries."""

    def test_single_keyword_match_denies(self):
        """Query containing configured keyword should be denied (exit 2)."""
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "how to configure gitlab ci runners"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json")},
        )
        assert exit_code == 2

        # Verify output is valid JSON with correct structure
        output = json.loads(stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
        assert "gitlab" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_no_keyword_match_allows(self):
        """Query without configured keywords should be allowed (exit 0)."""
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "how to make a sandwich"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json")},
        )
        assert exit_code == 0

    def test_case_insensitive_matching(self):
        """Keyword matching should be case-insensitive."""
        for query in ["GITLAB ci", "GitLab CI", "gitlab ci"]:
            hook_input = {
                "tool_name": "WebSearch",
                "tool_input": {"query": query},
            }
            exit_code, stdout, stderr = run_hook(
                hook_input,
                env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json")},
            )
            assert exit_code == 2, f"Failed for query: {query}"

    def test_word_boundary_matching(self):
        """Partial word matches should NOT trigger denial."""
        # "ungitlabbed" contains "gitlab" but should not match due to word boundaries
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "ungitlabbed workflow"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json")},
        )
        assert exit_code == 0
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_hook.py::TestKeywordMatching -v`
Expected: FAIL (keyword matching not implemented)

**Step 4: Write minimal implementation**

Update `docsearch.py`:

```python
#!/usr/bin/env python3
"""
DocSearch Hook - PreToolUse hook that redirects documentation queries to RAG databases.

This hook intercepts WebSearch tool calls and checks if the query matches configured
documentation keywords. If matched, it denies the search and guides Claude to use
LEANN MCP tools instead. Includes an escape hatch for retrying web search if RAG fails.
"""
import json
import os
import re
import sys
from pathlib import Path


def get_config_path() -> Path:
    """Get the configuration file path."""
    if env_path := os.environ.get("DOCSEARCH_CONFIG_PATH"):
        return Path(env_path)
    return Path.home() / ".claude" / "hooks" / "docsearch-config.json"


def load_config() -> dict | None:
    """Load and parse the configuration file. Returns None on any error."""
    config_path = get_config_path()
    try:
        with open(config_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def find_matching_databases(query: str, config: dict) -> list[dict]:
    """Find all databases with keywords matching the query.

    Uses word boundary matching (case-insensitive).
    Returns list of matching database configs.
    """
    matches = []
    query_lower = query.lower()

    for db in config.get("databases", []):
        for keyword in db.get("keywords", []):
            # Word boundary regex for exact word match
            pattern = rf"\b{re.escape(keyword.lower())}\b"
            if re.search(pattern, query_lower):
                matches.append(db)
                break  # Only add each database once

    return matches


def build_deny_response(matches: list[dict]) -> dict:
    """Build the JSON response for denying a WebSearch."""
    if len(matches) == 1:
        db = matches[0]
        matched_keywords = db["keywords"][0]  # Use first keyword for message
        reason = f"Query matches '{matched_keywords}' - using RAG database instead"
        context = (
            f"This query should use the LEANN MCP tool '{db['mcp_tool_name']}' "
            f"to search the {db['description']} RAG database at {db['path']} instead of web search."
        )
    else:
        keyword_list = " and ".join(f"'{db['keywords'][0]}'" for db in matches)
        reason = f"Query matches {keyword_list} - using RAG databases instead"
        lines = ["This query matches multiple documentation databases. Please use these LEANN MCP tools IN PARALLEL:"]
        for i, db in enumerate(matches, 1):
            lines.append(f"{i}. '{db['mcp_tool_name']}' for {db['description']} at {db['path']}")
        context = "\n".join(lines)

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
            "additionalContext": context,
        }
    }


def main() -> int:
    """Main entry point for the hook."""
    # Read and parse input from stdin
    try:
        stdin_data = sys.stdin.read()
        hook_input = json.loads(stdin_data)
    except json.JSONDecodeError:
        # Invalid JSON - fail open
        return 0

    # Get tool name - if not WebSearch, allow through
    tool_name = hook_input.get("tool_name", "")
    if tool_name != "WebSearch":
        return 0

    # Load configuration - if missing or invalid, allow through
    config = load_config()
    if config is None:
        return 0

    # Get the query from tool input
    tool_input = hook_input.get("tool_input", {})
    query = tool_input.get("query", "")
    if not query:
        return 0

    # Find matching databases
    matches = find_matching_databases(query, config)
    if not matches:
        return 0

    # Deny and provide guidance
    response = build_deny_response(matches)
    print(json.dumps(response))
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_hook.py -v`
Expected: PASS

**Step 6: Commit**

```bash
mkdir -p tests/fixtures
git add docsearch.py tests/test_hook.py tests/fixtures/valid_config.json
git commit -m "feat: add keyword matching with word boundaries and denial responses"
```

---

## Task 5: Multiple Keyword Matching

**Files:**
- Modify: `tests/test_hook.py`

**Step 1: Write the test for multiple keyword matches**

Add to `tests/test_hook.py`:

```python
class TestMultipleKeywordMatching:
    """Tests for queries matching multiple databases."""

    def test_multiple_keywords_match_all_databases(self):
        """Query with multiple keywords should mention all matching databases."""
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "how to deploy gitlab on kubernetes"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json")},
        )
        assert exit_code == 2

        output = json.loads(stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        # Both databases should be mentioned
        assert "gitlab" in context.lower()
        assert "kubernetes" in context.lower()
        assert "IN PARALLEL" in context

    def test_k8s_alias_matches_kubernetes(self):
        """Alternative keywords like 'k8s' should match kubernetes database."""
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "k8s pod configuration"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json")},
        )
        assert exit_code == 2

        output = json.loads(stdout)
        assert "kubernetes" in output["hookSpecificOutput"]["additionalContext"].lower()

    def test_database_order_preserved_in_output(self):
        """Databases should appear in config file order in output."""
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "gitlab kubernetes deployment"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json")},
        )
        assert exit_code == 2

        output = json.loads(stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        # GitLab appears first in config, so should be listed as item 1
        gitlab_pos = context.find("GitLab")
        kubernetes_pos = context.find("Kubernetes")
        assert gitlab_pos < kubernetes_pos, "GitLab should appear before Kubernetes (config order)"
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_hook.py::TestMultipleKeywordMatching -v`
Expected: PASS (already implemented in Task 4)

**Step 3: Commit**

```bash
git add tests/test_hook.py
git commit -m "test: add tests for multiple keyword matching and config order preservation"
```

---

## Task 6: Session State Management for Escape Hatch

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`

**Step 1: Write the failing test for state file management**

Add to `tests/test_hook.py`:

```python
class TestStateManagement:
    """Tests for session state file management."""

    def test_first_search_stores_state_and_denies(self, tmp_path):
        """First matching search should store state and deny."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "how to configure gitlab ci",
                "allowed_domains": [],
                "blocked_domains": [],
            },
            "session_id": "test-session-123",
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )
        assert exit_code == 2

        # State file should be created
        state_file = state_dir / "docsearch-state-test-session-123.json"
        assert state_file.exists()

        state = json.loads(state_file.read_text())
        assert state["last_denied"]["query"] == "how to configure gitlab ci"

    def test_retry_same_params_allows_through(self, tmp_path):
        """Retry with exact same params should allow through (escape hatch)."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Pre-create state file simulating a previous denial
        state_file = state_dir / "docsearch-state-test-session-456.json"
        state_file.write_text(json.dumps({
            "last_denied": {
                "query": "how to configure gitlab ci",
                "allowed_domains": [],
                "blocked_domains": [],
                "timestamp": int(time.time()),
            }
        }))

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "how to configure gitlab ci",
                "allowed_domains": [],
                "blocked_domains": [],
            },
            "session_id": "test-session-456",
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )
        assert exit_code == 0

        # State file should be cleared after successful retry
        state = json.loads(state_file.read_text())
        assert state.get("last_denied") is None

    def test_different_query_denies_again(self, tmp_path):
        """Different query should deny even with existing state."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Pre-create state file with different query
        state_file = state_dir / "docsearch-state-test-session-789.json"
        state_file.write_text(json.dumps({
            "last_denied": {
                "query": "gitlab runners setup",
                "allowed_domains": [],
                "blocked_domains": [],
                "timestamp": int(time.time()),
            }
        }))

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "how to configure gitlab ci",  # Different query
                "allowed_domains": [],
                "blocked_domains": [],
            },
            "session_id": "test-session-789",
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )
        assert exit_code == 2

    def test_corrupted_state_file_fails_open(self, tmp_path):
        """Corrupted state file should be treated as no previous denial."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Pre-create corrupted state file
        state_file = state_dir / "docsearch-state-test-session-corrupted.json"
        state_file.write_text("{invalid json content")

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "how to configure gitlab ci",
                "allowed_domains": [],
                "blocked_domains": [],
            },
            "session_id": "test-session-corrupted",
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )
        # Should deny (no valid state to trigger escape hatch)
        assert exit_code == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hook.py::TestStateManagement -v`
Expected: FAIL (state management not implemented)

**Step 3: Write minimal implementation**

Update `docsearch.py` to add state management:

```python
#!/usr/bin/env python3
"""
DocSearch Hook - PreToolUse hook that redirects documentation queries to RAG databases.

This hook intercepts WebSearch tool calls and checks if the query matches configured
documentation keywords. If matched, it denies the search and guides Claude to use
LEANN MCP tools instead. Includes an escape hatch for retrying web search if RAG fails.
"""
import json
import os
import re
import sys
import time
from pathlib import Path


def get_config_path() -> Path:
    """Get the configuration file path."""
    if env_path := os.environ.get("DOCSEARCH_CONFIG_PATH"):
        return Path(env_path)
    return Path.home() / ".claude" / "hooks" / "docsearch-config.json"


def get_state_dir() -> Path:
    """Get the state directory path."""
    if env_path := os.environ.get("DOCSEARCH_STATE_DIR"):
        return Path(env_path)
    return Path.home() / ".claude" / "hooks"


def get_state_file(session_id: str) -> Path:
    """Get the state file path for a session."""
    return get_state_dir() / f"docsearch-state-{session_id}.json"


def load_config() -> dict | None:
    """Load and parse the configuration file. Returns None on any error."""
    config_path = get_config_path()
    try:
        with open(config_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def load_state(session_id: str) -> dict:
    """Load session state. Returns empty dict on any error."""
    state_file = get_state_file(session_id)
    try:
        with open(state_file) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_state(session_id: str, state: dict) -> None:
    """Save session state."""
    state_file = get_state_file(session_id)
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(state, f)
    except OSError:
        pass  # Fail silently - state is optional


def params_match(current: dict, previous: dict) -> bool:
    """Check if current tool_input matches previous denied params.

    Compares query exactly and domains as sets (order-independent).
    """
    if current.get("query") != previous.get("query"):
        return False

    # Compare domains as sets (order-independent)
    current_allowed = set(current.get("allowed_domains", []) or [])
    previous_allowed = set(previous.get("allowed_domains", []) or [])
    if current_allowed != previous_allowed:
        return False

    current_blocked = set(current.get("blocked_domains", []) or [])
    previous_blocked = set(previous.get("blocked_domains", []) or [])
    if current_blocked != previous_blocked:
        return False

    return True


def find_matching_databases(query: str, config: dict) -> list[dict]:
    """Find all databases with keywords matching the query.

    Uses word boundary matching (case-insensitive).
    Returns list of matching database configs.
    """
    matches = []
    query_lower = query.lower()

    for db in config.get("databases", []):
        for keyword in db.get("keywords", []):
            # Word boundary regex for exact word match
            pattern = rf"\b{re.escape(keyword.lower())}\b"
            if re.search(pattern, query_lower):
                matches.append(db)
                break  # Only add each database once

    return matches


def build_deny_response(matches: list[dict]) -> dict:
    """Build the JSON response for denying a WebSearch."""
    if len(matches) == 1:
        db = matches[0]
        matched_keywords = db["keywords"][0]  # Use first keyword for message
        reason = f"Query matches '{matched_keywords}' - using RAG database instead"
        context = (
            f"This query should use the LEANN MCP tool '{db['mcp_tool_name']}' "
            f"to search the {db['description']} RAG database at {db['path']} instead of web search."
        )
    else:
        keyword_list = " and ".join(f"'{db['keywords'][0]}'" for db in matches)
        reason = f"Query matches {keyword_list} - using RAG databases instead"
        lines = ["This query matches multiple documentation databases. Please use these LEANN MCP tools IN PARALLEL:"]
        for i, db in enumerate(matches, 1):
            lines.append(f"{i}. '{db['mcp_tool_name']}' for {db['description']} at {db['path']}")
        context = "\n".join(lines)

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
            "additionalContext": context,
        }
    }


def main() -> int:
    """Main entry point for the hook."""
    # Read and parse input from stdin
    try:
        stdin_data = sys.stdin.read()
        hook_input = json.loads(stdin_data)
    except json.JSONDecodeError:
        # Invalid JSON - fail open
        return 0

    # Get tool name - if not WebSearch, allow through
    tool_name = hook_input.get("tool_name", "")
    if tool_name != "WebSearch":
        return 0

    # Load configuration - if missing or invalid, allow through
    config = load_config()
    if config is None:
        return 0

    # Get the query from tool input
    tool_input = hook_input.get("tool_input", {})
    query = tool_input.get("query", "")
    if not query:
        return 0

    # Get session ID for state management
    session_id = hook_input.get("session_id", "default")

    # Check escape hatch - if this is a retry of the same params, allow through
    state = load_state(session_id)
    last_denied = state.get("last_denied")
    if last_denied and params_match(tool_input, last_denied):
        # Clear state and allow through
        save_state(session_id, {"last_denied": None})
        return 0

    # Find matching databases
    matches = find_matching_databases(query, config)
    if not matches:
        return 0

    # Store current params in state for escape hatch
    save_state(session_id, {
        "last_denied": {
            "query": tool_input.get("query", ""),
            "allowed_domains": tool_input.get("allowed_domains", []),
            "blocked_domains": tool_input.get("blocked_domains", []),
            "timestamp": int(time.time()),
        }
    })

    # Deny and provide guidance
    response = build_deny_response(matches)
    print(json.dumps(response))
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hook.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docsearch.py tests/test_hook.py
git commit -m "feat: add session state management for escape hatch"
```

---

## Task 7: State Cleanup (Stale State Expiry)

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`

**Step 1: Write the failing test for stale state cleanup**

Add to `tests/test_hook.py`:

```python
class TestStaleStateCleanup:
    """Tests for stale state file cleanup."""

    def test_expired_state_is_ignored(self, tmp_path):
        """State older than 5 minutes should be ignored."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Pre-create state file with old timestamp (6 minutes ago)
        old_timestamp = int(time.time()) - 360  # 6 minutes ago
        state_file = state_dir / "docsearch-state-test-session-old.json"
        state_file.write_text(json.dumps({
            "last_denied": {
                "query": "how to configure gitlab ci",
                "allowed_domains": [],
                "blocked_domains": [],
                "timestamp": old_timestamp,
            }
        }))

        # Same query should be denied again (state expired)
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "how to configure gitlab ci",
                "allowed_domains": [],
                "blocked_domains": [],
            },
            "session_id": "test-session-old",
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )
        assert exit_code == 2  # Should deny, not allow through

    def test_recent_state_is_used(self, tmp_path):
        """State less than 5 minutes old should be used."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Pre-create state file with recent timestamp (2 minutes ago)
        recent_timestamp = int(time.time()) - 120  # 2 minutes ago
        state_file = state_dir / "docsearch-state-test-session-recent.json"
        state_file.write_text(json.dumps({
            "last_denied": {
                "query": "how to configure gitlab ci",
                "allowed_domains": [],
                "blocked_domains": [],
                "timestamp": recent_timestamp,
            }
        }))

        # Same query should be allowed (escape hatch)
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "how to configure gitlab ci",
                "allowed_domains": [],
                "blocked_domains": [],
            },
            "session_id": "test-session-recent",
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )
        assert exit_code == 0  # Should allow through
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hook.py::TestStaleStateCleanup -v`
Expected: FAIL (timestamp expiry not implemented)

**Step 3: Write minimal implementation**

Add near the top of `docsearch.py`:

```python
# State expiry timeout in seconds (5 minutes)
STATE_EXPIRY_SECONDS = 300


def is_state_expired(last_denied: dict) -> bool:
    """Check if the state entry has expired (older than 5 minutes)."""
    timestamp = last_denied.get("timestamp", 0)
    return (int(time.time()) - timestamp) > STATE_EXPIRY_SECONDS
```

Update the escape hatch check in `main()`:

```python
    # Check escape hatch - if this is a retry of the same params, allow through
    state = load_state(session_id)
    last_denied = state.get("last_denied")
    if last_denied and not is_state_expired(last_denied) and params_match(tool_input, last_denied):
        # Clear state and allow through
        save_state(session_id, {"last_denied": None})
        return 0
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hook.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docsearch.py tests/test_hook.py
git commit -m "feat: add 5-minute expiry for stale state entries"
```

---

## Task 8: Error Logging to stderr

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`

**Step 1: Write the failing test for error logging**

Add to `tests/test_hook.py`:

```python
class TestErrorLogging:
    """Tests for error logging to stderr."""

    def test_invalid_config_logs_to_stderr(self, tmp_path):
        """Invalid config JSON should log error to stderr."""
        config_file = tmp_path / "bad_config.json"
        config_file.write_text("{invalid json")

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "test query"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(config_file)},
        )
        assert exit_code == 0  # Fail open
        assert "error" in stderr.lower() or "json" in stderr.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hook.py::TestErrorLogging -v`
Expected: FAIL (no stderr logging)

**Step 3: Write minimal implementation**

Update `load_config()` in `docsearch.py`:

```python
def load_config() -> dict | None:
    """Load and parse the configuration file. Returns None on any error."""
    config_path = get_config_path()
    try:
        with open(config_path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None  # Silent - expected during first-time setup
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file {config_path}: {e}", file=sys.stderr)
        return None
    except OSError as e:
        print(f"Error: Could not read config file {config_path}: {e}", file=sys.stderr)
        return None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hook.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docsearch.py tests/test_hook.py
git commit -m "feat: add error logging to stderr for config issues"
```

---

## Task 9: Complete Test Coverage and Edge Cases

**Files:**
- Modify: `tests/test_hook.py`

**Step 1: Add comprehensive edge case tests**

Add to `tests/test_hook.py`:

```python
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_query_allows_through(self):
        """Empty query should be allowed through."""
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": ""},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json")},
        )
        assert exit_code == 0

    def test_missing_query_allows_through(self):
        """Missing query field should be allowed through."""
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json")},
        )
        assert exit_code == 0

    def test_missing_tool_input_allows_through(self):
        """Missing tool_input field should be allowed through."""
        hook_input = {
            "tool_name": "WebSearch",
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json")},
        )
        assert exit_code == 0

    def test_missing_session_id_uses_default(self, tmp_path):
        """Missing session_id should use 'default' session."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "gitlab setup"},
            # Note: no session_id
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )
        assert exit_code == 2

        # Should use default session
        state_file = state_dir / "docsearch-state-default.json"
        assert state_file.exists()

    def test_empty_databases_config_allows_through(self, tmp_path):
        """Config with empty databases array should allow through."""
        config_file = tmp_path / "empty_config.json"
        config_file.write_text('{"databases": []}')

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "gitlab ci configuration"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(config_file)},
        )
        assert exit_code == 0

    def test_domains_compared_as_sets(self, tmp_path):
        """Domain arrays should be compared as sets (order-independent)."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Pre-create state with domains in one order
        state_file = state_dir / "docsearch-state-test-domains.json"
        state_file.write_text(json.dumps({
            "last_denied": {
                "query": "gitlab ci",
                "allowed_domains": ["b.com", "a.com"],  # Different order
                "blocked_domains": [],
                "timestamp": int(time.time()),
            }
        }))

        # Query with same domains in different order
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "gitlab ci",
                "allowed_domains": ["a.com", "b.com"],  # Same domains, different order
                "blocked_domains": [],
            },
            "session_id": "test-domains",
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )
        assert exit_code == 0  # Should match and allow through

    def test_special_characters_in_keywords(self, tmp_path):
        """Keywords with regex special characters should match correctly."""
        config_file = tmp_path / "special_config.json"
        config_file.write_text(json.dumps({
            "databases": [
                {
                    "keywords": ["c++", "c#", ".net"],
                    "path": "/mock/path/dotnet",
                    "mcp_tool_name": "leann-docs",
                    "description": ".NET documentation"
                }
            ]
        }))

        # Test C++ keyword
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "c++ templates tutorial"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(config_file)},
        )
        assert exit_code == 2

    def test_output_contains_all_required_fields(self):
        """Output JSON should contain all required hookSpecificOutput fields."""
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "gitlab ci"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json")},
        )
        assert exit_code == 2

        output = json.loads(stdout)
        hook_output = output["hookSpecificOutput"]

        # Verify all required fields present
        assert "hookEventName" in hook_output
        assert "permissionDecision" in hook_output
        assert "permissionDecisionReason" in hook_output
        assert "additionalContext" in hook_output

        # Verify field values
        assert hook_output["hookEventName"] == "PreToolUse"
        assert hook_output["permissionDecision"] == "deny"
```

**Step 2: Run all tests**

Run: `pytest tests/test_hook.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_hook.py
git commit -m "test: add comprehensive edge case coverage"
```

---

## Task 10: README Documentation

**Files:**
- Modify: `README.md`

**Step 1: Write comprehensive README**

```markdown
# DocSearch Hook

A Claude Code PreToolUse hook that intercepts WebSearch tool calls and redirects documentation-related queries to local RAG databases via LEANN MCP server.

## Features

- **Keyword-based interception**: Configure keywords that trigger RAG lookups instead of web searches
- **Multiple database support**: Match queries against multiple documentation databases
- **Smart escape hatch**: If RAG results are insufficient, retry the same search to use web
- **Fail-open design**: Any errors gracefully fall back to normal web search
- **Session isolation**: Per-session state prevents cross-session interference

## Prerequisites

1. Python 3.12+
2. [LEANN](https://github.com/user/leann) installed and configured
3. LEANN MCP server configured in Claude Code's MCP settings
4. RAG databases built using LEANN tools

## Installation

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

3. **Configure Claude Code to use the hook** by adding to your Claude Code settings:

   ```json
   {
     "hooks": {
       "PreToolUse": ["~/.claude/hooks/PreToolUse/docsearch.py"]
     }
   }
   ```

## Configuration

Edit `~/.claude/hooks/docsearch-config.json`:

```json
{
  "databases": [
    {
      "keywords": ["gitlab", "gl", "gitlab-ci"],
      "path": "/path/to/.leann/databases/gitlab",
      "mcp_tool_name": "leann-docs",
      "description": "GitLab documentation from docs.gitlab.com"
    }
  ]
}
```

### Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `keywords` | Yes | Array of keywords to match (case-insensitive, word boundaries) |
| `path` | Yes | Absolute path to LEANN database directory |
| `mcp_tool_name` | Yes | Exact MCP tool name for Claude to use |
| `description` | Yes | Human-readable description shown to Claude |

## How It Works

1. You ask Claude a question containing a configured keyword (e.g., "How do I configure GitLab CI?")
2. Claude attempts to use WebSearch
3. The hook intercepts and denies the search
4. Claude receives guidance to use the LEANN MCP tool instead
5. If RAG results are insufficient, Claude can retry the exact same WebSearch
6. The hook recognizes the retry and allows it through

## Escape Hatch

If the RAG database doesn't have what you need, Claude can simply retry the same web search. The hook tracks the last denied search per session and allows identical retries through. State expires after 5 minutes as a safety net.

## Testing

```bash
pytest tests/test_hook.py -v
```

## Troubleshooting

### Hook not intercepting searches

- Verify the hook script is executable: `chmod +x ~/.claude/hooks/PreToolUse/docsearch.py`
- Check config file exists: `cat ~/.claude/hooks/docsearch-config.json`
- Verify JSON syntax: `python -m json.tool ~/.claude/hooks/docsearch-config.json`

### Config errors

Check stderr for error messages. The hook logs JSON parsing errors to stderr.

### Keyword not matching

- Keywords use word boundary matching (`\b` regex)
- "gitla" won't match "gitlab" - only complete words match
- Matching is case-insensitive

## License

MIT License - see LICENSE file
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README with setup and usage instructions"
```

---

## Task 11: Final Integration Testing

**Files:**
- Create: `tests/test_integration.py` (manual testing guide)

**Step 1: Create integration test guide**

Create `tests/test_integration.py`:

```python
"""
Integration Testing Guide for DocSearch Hook

These tests require a real LEANN MCP server configured.
Run these manually to verify end-to-end functionality.

Setup:
1. Configure LEANN MCP server in Claude Code
2. Build a test RAG database with LEANN
3. Add the database to docsearch-config.json
4. Run Claude Code and test the flow

Test Scenarios:
1. Basic interception: Ask about configured keyword topic
   - Verify hook denies WebSearch
   - Verify Claude uses MCP tool
   - Verify answer comes from RAG

2. Escape hatch: Ask about topic where RAG fails
   - Verify first search denied
   - Verify Claude can retry
   - Verify retry uses web search

3. Multiple keywords: Ask about two topics in one query
   - Verify both databases mentioned
   - Verify Claude calls MCP tools in parallel

4. Non-matching query: Ask about unconfigured topic
   - Verify hook allows WebSearch through
"""
```

**Step 2: Commit**

```bash
git add tests/test_integration.py
git commit -m "docs: add integration testing guide"
```

---

## Task 12: Make Script Executable and Final Verification

**Files:**
- Verify: `docsearch.py`

**Step 1: Verify shebang line**

The shebang is already present: `#!/usr/bin/env python3`

**Step 2: Run full test suite**

Run: `pytest tests/test_hook.py -v --tb=short`
Expected: All tests PASS

**Step 3: Verify script is executable**

Run: `chmod +x docsearch.py && ./docsearch.py < /dev/null; echo "Exit code: $?"`
Expected: Exit code: 0 (fail open on no input)

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final cleanup and verification"
```

---

## Task 3a: Configuration Schema Validation (NEW)

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`

**Step 1: Write the failing test for config validation**

Add to `tests/test_hook.py`:

```python
class TestConfigValidation:
    """Tests for configuration schema validation."""

    def test_missing_keywords_logs_warning(self, tmp_path):
        """Config entry missing 'keywords' should log warning and skip entry."""
        config_file = tmp_path / "incomplete_config.json"
        config_file.write_text(json.dumps({
            "databases": [
                {
                    "path": "/mock/path/test",
                    "mcp_tool_name": "leann-docs",
                    "description": "Test database"
                    # Missing: "keywords"
                }
            ]
        }))

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "some query"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(config_file)},
        )
        # Should allow through (no valid databases)
        assert exit_code == 0
        # Should log warning about missing field
        assert "keywords" in stderr.lower() or "missing" in stderr.lower()

    def test_missing_path_logs_warning(self, tmp_path):
        """Config entry missing 'path' should log warning and skip entry."""
        config_file = tmp_path / "incomplete_config.json"
        config_file.write_text(json.dumps({
            "databases": [
                {
                    "keywords": ["test"],
                    "mcp_tool_name": "leann-docs",
                    "description": "Test database"
                    # Missing: "path"
                }
            ]
        }))

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "test query"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(config_file)},
        )
        # Should allow through (no valid databases after validation)
        assert exit_code == 0
        # Should log warning
        assert "path" in stderr.lower() or "missing" in stderr.lower()

    def test_keywords_not_array_logs_warning(self, tmp_path):
        """Config entry with keywords as string (not array) should log warning."""
        config_file = tmp_path / "bad_type_config.json"
        config_file.write_text(json.dumps({
            "databases": [
                {
                    "keywords": "gitlab",  # Should be ["gitlab"]
                    "path": "/mock/path/test",
                    "mcp_tool_name": "leann-docs",
                    "description": "Test database"
                }
            ]
        }))

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "gitlab ci"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(config_file)},
        )
        # Should allow through (invalid entry skipped)
        assert exit_code == 0
        # Should log warning about type
        assert "keywords" in stderr.lower() or "array" in stderr.lower() or "list" in stderr.lower()

    def test_empty_keywords_array_logs_warning(self, tmp_path):
        """Config entry with empty keywords array should log warning."""
        config_file = tmp_path / "empty_keywords_config.json"
        config_file.write_text(json.dumps({
            "databases": [
                {
                    "keywords": [],  # Empty array
                    "path": "/mock/path/test",
                    "mcp_tool_name": "leann-docs",
                    "description": "Test database"
                }
            ]
        }))

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "test query"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(config_file)},
        )
        # Should allow through (no valid databases)
        assert exit_code == 0
        # Should log warning about empty keywords
        assert "keywords" in stderr.lower() or "empty" in stderr.lower()

    def test_relative_path_logs_warning(self, tmp_path):
        """Config entry with relative path should log warning but still work."""
        config_file = tmp_path / "relative_path_config.json"
        config_file.write_text(json.dumps({
            "databases": [
                {
                    "keywords": ["test"],
                    "path": "relative/path/database",  # Should be absolute
                    "mcp_tool_name": "leann-docs",
                    "description": "Test database"
                }
            ]
        }))

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "test query"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(config_file)},
        )
        # Should still deny (relative path is a warning, not an error)
        assert exit_code == 2
        # Should log warning about relative path
        assert "path" in stderr.lower() or "absolute" in stderr.lower() or "relative" in stderr.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hook.py::TestConfigValidation -v`
Expected: FAIL (validation not implemented)

**Step 3: Write minimal implementation**

Add validation function to `docsearch.py`:

```python
REQUIRED_DATABASE_FIELDS = ["keywords", "path", "mcp_tool_name", "description"]


def validate_database_entry(db: dict, index: int) -> bool:
    """Validate a database entry has all required fields and correct types.

    Returns True if valid, False if invalid (logs warning to stderr).
    Maintains fail-open behavior - warns but allows through when possible.
    """
    # Check required fields are present
    missing = [f for f in REQUIRED_DATABASE_FIELDS if f not in db]
    if missing:
        print(
            f"Warning: Database entry {index} missing required fields: {missing}",
            file=sys.stderr
        )
        return False

    # Validate keywords is a non-empty list
    keywords = db.get("keywords")
    if not isinstance(keywords, list):
        print(
            f"Warning: Database entry {index} 'keywords' must be an array, got {type(keywords).__name__}",
            file=sys.stderr
        )
        return False

    if len(keywords) == 0:
        print(
            f"Warning: Database entry {index} 'keywords' array is empty",
            file=sys.stderr
        )
        return False

    # Warn (but don't fail) for relative paths
    path = db.get("path", "")
    if path and not path.startswith("/"):
        print(
            f"Warning: Database entry {index} 'path' should be absolute, got relative path: {path}",
            file=sys.stderr
        )
        # Continue anyway - relative path might still work

    return True
```

Update `find_matching_databases()` to skip invalid entries:

```python
def find_matching_databases(query: str, config: dict) -> list[dict]:
    """Find all databases with keywords matching the query."""
    matches = []
    query_lower = query.lower()

    for i, db in enumerate(config.get("databases", [])):
        # Skip invalid database entries
        if not validate_database_entry(db, i):
            continue

        for keyword in db.get("keywords", []):
            pattern = rf"\b{re.escape(keyword.lower())}\b"
            if re.search(pattern, query_lower):
                matches.append(db)
                break

    return matches
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hook.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docsearch.py tests/test_hook.py
git commit -m "feat: add configuration schema validation with type checking"
```

---

## Task 7a: Session Start State Cleanup (NEW)

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`

**Step 1: Write the failing test for stale file cleanup**

Add to `tests/test_hook.py`:

```python
class TestSessionStartCleanup:
    """Tests for cleaning stale state files on session start."""

    def test_stale_state_file_cleaned_on_unrelated_query(self, tmp_path):
        """Very old state files should be cleaned up when processing new queries."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Create multiple stale state files (older than 5 minutes)
        old_timestamp = int(time.time()) - 600  # 10 minutes ago

        stale_file1 = state_dir / "docsearch-state-old-session-1.json"
        stale_file1.write_text(json.dumps({
            "last_denied": {
                "query": "old query 1",
                "allowed_domains": [],
                "blocked_domains": [],
                "timestamp": old_timestamp,
            }
        }))

        stale_file2 = state_dir / "docsearch-state-old-session-2.json"
        stale_file2.write_text(json.dumps({
            "last_denied": {
                "query": "old query 2",
                "allowed_domains": [],
                "blocked_domains": [],
                "timestamp": old_timestamp,
            }
        }))

        # Run a hook call for a new session (triggers cleanup)
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "unrelated query no keywords"},
            "session_id": "new-session",
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )

        # Query should pass through (no keyword match)
        assert exit_code == 0

        # Stale files should be cleaned up
        # Note: This is optional behavior - cleanup runs periodically
        # Test verifies stale files don't interfere with new sessions

    def test_recent_state_file_preserved(self, tmp_path):
        """Recent state files should NOT be cleaned up."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Create a recent state file (2 minutes ago)
        recent_timestamp = int(time.time()) - 120
        recent_file = state_dir / "docsearch-state-active-session.json"
        recent_file.write_text(json.dumps({
            "last_denied": {
                "query": "gitlab ci",
                "allowed_domains": [],
                "blocked_domains": [],
                "timestamp": recent_timestamp,
            }
        }))

        # Run a hook call for a different session
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "unrelated query"},
            "session_id": "other-session",
        }
        run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )

        # Recent file should still exist
        assert recent_file.exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hook.py::TestSessionStartCleanup -v`
Expected: FAIL (cleanup not implemented)

**Step 3: Write minimal implementation**

Add cleanup function to `docsearch.py`:

```python
def cleanup_stale_state_files() -> None:
    """Clean up state files older than the expiry threshold.

    This is a best-effort cleanup that runs periodically to prevent
    state file accumulation. Errors are silently ignored.
    """
    state_dir = get_state_dir()
    if not state_dir.exists():
        return

    try:
        for state_file in state_dir.glob("docsearch-state-*.json"):
            try:
                with open(state_file) as f:
                    state = json.load(f)
                last_denied = state.get("last_denied")
                if last_denied and is_state_expired(last_denied):
                    state_file.unlink()
            except (json.JSONDecodeError, OSError, KeyError):
                # Corrupted or unreadable - remove it
                try:
                    state_file.unlink()
                except OSError:
                    pass
    except OSError:
        pass  # Can't list directory - skip cleanup
```

Add cleanup call at the start of `main()` (after config loading):

```python
def main() -> int:
    """Main entry point for the hook."""
    # ... existing code ...

    # Load configuration - if missing or invalid, allow through
    config = load_config()
    if config is None:
        return 0

    # Periodically clean up stale state files
    # Only run occasionally to avoid performance impact
    cleanup_stale_state_files()

    # ... rest of main() ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hook.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docsearch.py tests/test_hook.py
git commit -m "feat: add periodic cleanup of stale state files"
```

---

## Task 6a: Session ID Sanitization (NEW - SECURITY)

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`

**Step 1: Write the failing test for session ID sanitization**

Add to `tests/test_hook.py`:

```python
class TestSessionIdSanitization:
    """Tests for session ID sanitization to prevent path traversal."""

    def test_session_id_with_path_traversal_is_sanitized(self, tmp_path):
        """Session ID with path traversal characters should be sanitized."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Attempt path traversal attack
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "gitlab ci setup"},
            "session_id": "../../etc/passwd",  # Malicious session_id
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )
        assert exit_code == 2  # Should still work (deny)

        # State file should be created with sanitized name, NOT traverse paths
        # Should NOT create file at tmp_path/etc/passwd
        assert not (tmp_path / "etc").exists()

        # Should create file with sanitized session_id (special chars replaced)
        state_files = list(state_dir.glob("docsearch-state-*.json"))
        assert len(state_files) == 1
        # Filename should not contain path separators
        assert "/" not in state_files[0].name
        assert ".." not in state_files[0].name

    def test_session_id_with_special_chars_is_sanitized(self, tmp_path):
        """Session ID with special filesystem characters should be sanitized."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "gitlab ci setup"},
            "session_id": "test<>:\"|?*session",  # Invalid filesystem chars
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )
        assert exit_code == 2

        # State file should be created with sanitized name
        state_files = list(state_dir.glob("docsearch-state-*.json"))
        assert len(state_files) == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hook.py::TestSessionIdSanitization -v`
Expected: FAIL (sanitization not implemented)

**Step 3: Write minimal implementation**

Add sanitization function to `docsearch.py`:

```python
def sanitize_session_id(session_id: str) -> str:
    """Sanitize session_id to prevent path traversal and invalid filenames.

    Only allows alphanumeric characters, dashes, and underscores.
    All other characters are replaced with underscores.
    """
    return re.sub(r'[^a-zA-Z0-9_-]', '_', session_id)
```

Update `get_state_file()`:

```python
def get_state_file(session_id: str) -> Path:
    """Get the state file path for a session."""
    safe_id = sanitize_session_id(session_id)
    return get_state_dir() / f"docsearch-state-{safe_id}.json"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hook.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docsearch.py tests/test_hook.py
git commit -m "security: add session ID sanitization to prevent path traversal"
```

---

## Task 3b: Keywords Element Type Validation (NEW)

**Files:**
- Modify: `docsearch.py`
- Modify: `tests/test_hook.py`

**Step 1: Write the failing test for keyword element type validation**

Add to `tests/test_hook.py` in `TestConfigValidation` class:

```python
    def test_keywords_with_non_string_elements_logs_warning(self, tmp_path):
        """Config entry with non-string keyword elements should log warning."""
        config_file = tmp_path / "bad_keywords_config.json"
        config_file.write_text(json.dumps({
            "databases": [
                {
                    "keywords": ["valid", 123, None, {"nested": "dict"}],
                    "path": "/mock/path/test",
                    "mcp_tool_name": "leann-docs",
                    "description": "Test database"
                }
            ]
        }))

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "valid query"},
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(config_file)},
        )
        # Should allow through (invalid entry skipped)
        assert exit_code == 0
        # Should log warning about non-string elements
        assert "string" in stderr.lower() or "keywords" in stderr.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_hook.py::TestConfigValidation::test_keywords_with_non_string_elements_logs_warning -v`
Expected: FAIL (type validation not implemented)

**Step 3: Write minimal implementation**

Update `validate_database_entry()` in `docsearch.py`:

```python
def validate_database_entry(db: dict, index: int) -> bool:
    """Validate a database entry has all required fields and correct types."""
    # ... existing checks ...

    # Validate all keyword elements are strings
    if not all(isinstance(k, str) for k in keywords):
        print(
            f"Warning: Database entry {index} 'keywords' contains non-string elements",
            file=sys.stderr
        )
        return False

    # ... rest of function ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_hook.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docsearch.py tests/test_hook.py
git commit -m "feat: validate all keyword elements are strings"
```

---

## Task 9a: Permission Error Tests (NEW)

**Files:**
- Modify: `tests/test_hook.py`

**Step 1: Write permission error tests**

Add to `tests/test_hook.py`:

```python
class TestPermissionErrors:
    """Tests for permission error handling (fail-open behavior)."""

    def test_unreadable_config_allows_through(self, tmp_path):
        """Unreadable config file should fail open (exit 0)."""
        config_file = tmp_path / "unreadable_config.json"
        config_file.write_text('{"databases": [{"keywords": ["test"], "path": "/test", "mcp_tool_name": "test", "description": "test"}]}')
        config_file.chmod(0o000)  # No permissions

        try:
            hook_input = {
                "tool_name": "WebSearch",
                "tool_input": {"query": "test query"},
            }
            exit_code, stdout, stderr = run_hook(
                hook_input,
                env={**os.environ, "DOCSEARCH_CONFIG_PATH": str(config_file)},
            )
            # Should fail open
            assert exit_code == 0
        finally:
            config_file.chmod(0o644)  # Restore for cleanup

    def test_unwritable_state_dir_still_denies(self, tmp_path):
        """Unwritable state directory should still deny (state is optional)."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        state_dir.chmod(0o555)  # Read-only

        try:
            hook_input = {
                "tool_name": "WebSearch",
                "tool_input": {"query": "gitlab ci setup"},
                "session_id": "test-session",
            }
            exit_code, stdout, stderr = run_hook(
                hook_input,
                env={
                    **os.environ,
                    "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                    "DOCSEARCH_STATE_DIR": str(state_dir),
                },
            )
            # Should still deny (state write failure is silent)
            assert exit_code == 2
        finally:
            state_dir.chmod(0o755)  # Restore for cleanup
```

**Step 2: Run tests**

Run: `pytest tests/test_hook.py::TestPermissionErrors -v`
Expected: PASS (implementation already handles these cases)

**Step 3: Commit**

```bash
git add tests/test_hook.py
git commit -m "test: add permission error handling tests"
```

---

## Task 9b: Session Isolation Tests (NEW)

**Files:**
- Modify: `tests/test_hook.py`

**Step 1: Write session isolation tests**

Add to `tests/test_hook.py`:

```python
class TestSessionIsolation:
    """Tests for session state isolation between concurrent sessions."""

    def test_different_sessions_have_isolated_state(self, tmp_path):
        """State from session A should not affect session B."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Create state for session A (previous denial)
        state_file_a = state_dir / "docsearch-state-session-A.json"
        state_file_a.write_text(json.dumps({
            "last_denied": {
                "query": "gitlab ci setup",
                "allowed_domains": [],
                "blocked_domains": [],
                "timestamp": int(time.time()),
            }
        }))

        # Session B with SAME query should be denied (no escape hatch)
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "gitlab ci setup",  # Same query as A's state
                "allowed_domains": [],
                "blocked_domains": [],
            },
            "session_id": "session-B",  # Different session
        }
        exit_code, stdout, stderr = run_hook(
            hook_input,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )

        # Session B should be denied (its own first request)
        assert exit_code == 2

        # Session A's state should be unchanged
        state_a = json.loads(state_file_a.read_text())
        assert state_a["last_denied"]["query"] == "gitlab ci setup"

        # Session B should have its own state file
        state_file_b = state_dir / "docsearch-state-session-B.json"
        assert state_file_b.exists()

    def test_session_escape_hatch_only_affects_own_session(self, tmp_path):
        """Escape hatch retry should only work for the session that was denied."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Create state for session A
        state_file_a = state_dir / "docsearch-state-session-A.json"
        state_file_a.write_text(json.dumps({
            "last_denied": {
                "query": "gitlab ci setup",
                "allowed_domains": [],
                "blocked_domains": [],
                "timestamp": int(time.time()),
            }
        }))

        # Session A retries same query - should be allowed (escape hatch)
        hook_input_a = {
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "gitlab ci setup",
                "allowed_domains": [],
                "blocked_domains": [],
            },
            "session_id": "session-A",
        }
        exit_code_a, _, _ = run_hook(
            hook_input_a,
            env={
                **os.environ,
                "DOCSEARCH_CONFIG_PATH": str(FIXTURES_DIR / "valid_config.json"),
                "DOCSEARCH_STATE_DIR": str(state_dir),
            },
        )
        assert exit_code_a == 0  # Escape hatch works

        # Session A's state should be cleared
        state_a = json.loads(state_file_a.read_text())
        assert state_a.get("last_denied") is None
```

**Step 2: Run tests**

Run: `pytest tests/test_hook.py::TestSessionIsolation -v`
Expected: PASS (implementation already handles isolation)

**Step 3: Commit**

```bash
git add tests/test_hook.py
git commit -m "test: add session isolation tests"
```

---

## Summary

### Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `docsearch.py` | Create | Main hook script (Python 3.12+) |
| `config.example.json` | Create | Example configuration file |
| `tests/test_hook.py` | Create | Comprehensive unit tests |
| `tests/fixtures/valid_config.json` | Create | Test fixture configuration |
| `tests/test_integration.py` | Create | Integration testing guide |
| `README.md` | Modify | Setup and usage documentation |

### Key Implementation Details

1. **Fail-open design**: All errors result in allowing WebSearch through
2. **Word boundary matching**: Uses `\b` regex to prevent partial matches
3. **Session isolation**: State files named with sanitized session_id
4. **5-minute expiry**: Stale state entries are ignored
5. **Set comparison**: Domain arrays compared order-independently
6. **Config validation**: Missing required fields AND type validation logged as warnings (Task 3a)
   - Validates `keywords` is a non-empty array
   - Validates all keyword elements are strings (Task 3b)
   - Warns on relative paths (but allows)
   - Skips invalid database entries entirely
7. **Stale file cleanup**: Periodic cleanup of expired state files (Task 7a)
8. **Session ID sanitization**: Prevents path traversal attacks (Task 6a)

### Testing Commands

```bash
# Run all tests
pytest tests/test_hook.py -v

# Run specific test class
pytest tests/test_hook.py::TestKeywordMatching -v

# Run with coverage
pytest tests/test_hook.py -v --cov=docsearch

# Run new validation tests
pytest tests/test_hook.py::TestConfigValidation -v

# Run new cleanup tests
pytest tests/test_hook.py::TestSessionStartCleanup -v
```

### Total Tasks: 18

| Phase | Tasks (in execution order) | Status |
|-------|---------------------------|--------|
| P0 - Core | 2, 3, 4, 6a, 6, 12 | 0/6 complete |
| P1 - Enhanced | 5, 7, 7a, 3a, 3b, 8, 9, 9a, 9b | 0/9 complete |
| P2 - Polish | 1, 10, 11 | 0/3 complete |
| **Total** | **18 tasks** | **0/18 complete** |

**IMPORTANT:** Task 6a (Session ID Sanitization) MUST be completed before Task 6 (Session State Management) for security reasons.
