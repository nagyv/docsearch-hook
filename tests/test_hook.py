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


class TestSessionIdSanitization:
    """Tests for session ID sanitization to prevent path traversal attacks."""

    def test_path_traversal_session_id_is_sanitized(self, tmp_path):
        """Session IDs with path traversal attempts should be sanitized."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Create a pre-existing state file with sanitized name
        # The session ID "../../etc/passwd" should be sanitized to something safe
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "gitlab ci setup",
                "allowed_domains": [],
                "blocked_domains": [],
            },
            "session_id": "../../etc/passwd",
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

        # Verify no files were created outside the state directory
        # and the state file has a sanitized name (no path separators)
        state_files = list(state_dir.glob("docsearch-state-*.json"))
        assert len(state_files) == 1
        state_filename = state_files[0].name
        assert "/" not in state_filename
        assert ".." not in state_filename

    def test_special_characters_in_session_id_are_sanitized(self, tmp_path):
        """Session IDs with special characters should be sanitized."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "gitlab ci setup",
                "allowed_domains": [],
                "blocked_domains": [],
            },
            "session_id": "test<>|:*?\"session",
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

        # Verify state file was created with sanitized name
        state_files = list(state_dir.glob("docsearch-state-*.json"))
        assert len(state_files) == 1
        state_filename = state_files[0].name
        # Should not contain any special characters
        for char in '<>|:*?"':
            assert char not in state_filename

    def test_alphanumeric_session_id_preserved(self, tmp_path):
        """Normal alphanumeric session IDs should be preserved."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {
                "query": "gitlab ci setup",
                "allowed_domains": [],
                "blocked_domains": [],
            },
            "session_id": "test-session_123",
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

        # Verify state file preserves the session ID
        state_file = state_dir / "docsearch-state-test-session_123.json"
        assert state_file.exists()


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