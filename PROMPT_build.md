0a. Study `docs/plans/2026-02-04-docsearch-hook-design.md` with up to 500 parallel Sonnet subagents to learn the application specifications.
0b. Study `docs/plans/2026-02-04-docsearch-hook-implementation-plan.md`.
0c. Study `*` with up to 250 parallel Sonnet subagents to understand the current codebase.

1. Your task is to implement functionality per the plan using parallel subagents. Follow @docs/plans/2026-02-04-docsearch-hook-implementation-plan.md and choose the most important item to address. Before making changes, search the codebase (don't assume not implemented) using Sonnet subagents. You may use up to 500 parallel Sonnet subagents for searches/reads and only 1 Sonnet subagent for build/tests. Use Opus subagents when complex reasoning is needed (debugging, architectural decisions).
2. After implementing functionality or resolving problems, run the tests for that unit of code that was improved. If functionality is missing then it's your job to add it as per the application specifications. Ultrathink.
3. When you discover issues, immediately update @docs/plans/2026-02-04-docsearch-hook-implementation-plan.md with your findings using a subagent. When resolved, update and remove the item.
4. When the tests pass, update @docs/plans/2026-02-04-docsearch-hook-implementation-plan.md, then `git add -A` then `git commit` with a message describing the changes. After the commit, `git push`.

99999. Important: When authoring documentation, capture the why — tests and implementation importance.
999999. Important: Single sources of truth, no migrations/adapters. If tests unrelated to your work fail, resolve them as part of the increment.
9999999. As soon as there are no build or test errors commit and push your code.
99999999. You may add extra logging if required to debug issues.
999999999. Keep @docs/plans/2026-02-04-docsearch-hook-implementation-plan.md current with learnings using a subagent — future work depends on this to avoid duplicating efforts. Update especially after finishing your turn.
9999999999. When you learn something new about how to run the application, update @AGENTS.md using a subagent but keep it brief. For example if you run commands multiple times before learning the correct command then that file should be updated.
99999999999. For any bugs you notice, resolve them or document them in @docs/plans/2026-02-04-docsearch-hook-implementation-plan.md using a subagent even if it is unrelated to the current piece of work.
999999999999. Implement functionality completely. Placeholders and stubs waste efforts and time redoing the same work.
9999999999999. When @docs/plans/2026-02-04-docsearch-hook-implementation-plan.md becomes large periodically clean out the items that are completed from the file using a subagent.
99999999999999. If you find inconsistencies in the specs/* then use an Opus 4.5 subagent with 'ultrathink' requested to update the specs.
999999999999999. IMPORTANT: Keep @AGENTS.md operational only — status updates and progress notes belong in `docs/plans/2026-02-04-docsearch-hook-implementation-plan.md`. A bloated AGENTS.md pollutes every future loop's context.