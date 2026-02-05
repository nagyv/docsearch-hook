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
