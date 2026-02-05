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