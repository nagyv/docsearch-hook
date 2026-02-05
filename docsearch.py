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
