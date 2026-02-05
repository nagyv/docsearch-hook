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
