0a. Study `docs/plans/*` with up to 250 parallel Sonnet subagents to learn the application specifications.
0b. Study @docs/plans/2026-02-04-docsearch-hook-implementation-plan.md (if present) to understand the plan so far.
0c. Study `*` with up to 250 parallel Sonnet subagents to understand the current codebase.

1. Study @docs/plans/2026-02-04-docsearch-hook-implementation-plan.md (if present; it may be incorrect) and use up to 500 Sonnet subagents to study existing source code and compare it against the plan. Use an Opus subagent to analyze findings, prioritize tasks, and create/update @docs/plans/2026-02-04-docsearch-hook-implementation-plan.md as a bullet point list sorted in priority of items yet to be implemented. Ultrathink. Consider searching for TODO, minimal implementations, placeholders, skipped/flaky tests, and inconsistent patterns. Study @docs/plans/2026-02-04-docsearch-hook-implementation-plan.md to determine starting point for research and keep it up to date with items considered complete/incomplete using subagents.

IMPORTANT: Plan only. Do NOT implement anything. Do NOT assume functionality is missing; confirm with code search first. Prefer consolidated, idiomatic implementations over ad-hoc copies.

ULTIMATE GOAL: We want to ship @docs/plans/2026-02-04-docsearch-hook-design.md. Consider missing elements and plan accordingly. If an element is missing, search first to confirm it doesn't exist, then if needed author the specification at specs/FILENAME.md. If you create a new element then document the plan to implement it in @docs/plans/2026-02-04-docsearch-hook-implementation-plan.md using a subagent.
