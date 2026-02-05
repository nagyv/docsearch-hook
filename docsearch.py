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


def sanitize_session_id(session_id: str) -> str:
    """Sanitize session ID to prevent path traversal attacks.

    Only allows alphanumeric characters, dashes, and underscores.
    Any other characters are removed.
    """
    # Remove any character that isn't alphanumeric, dash, or underscore
    sanitized = re.sub(r"[^a-zA-Z0-9\-_]", "", session_id)
    # Ensure we have at least some content
    return sanitized if sanitized else "default"


def get_state_file(session_id: str) -> Path:
    """Get the state file path for a session."""
    safe_id = sanitize_session_id(session_id)
    return get_state_dir() / f"docsearch-state-{safe_id}.json"


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
