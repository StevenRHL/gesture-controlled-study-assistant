# AGENTS.md

This project uses coding rules adapted from `/Users/steven/Downloads/p10-coding-rules.skill`.

## Core Rules

1. Simple control flow
- Prefer flat, linear logic.
- Avoid unnecessary recursion.
- If nesting exceeds 3 levels, extract a helper.

2. Bounded loops
- Every loop must have a clear termination condition.
- Retries and polling must have explicit limits.
- If a loop is intentionally long-running, document why.

3. Short, focused functions
- Functions should do one thing.
- Keep functions roughly within one screen when practical.
- Split large functions into well-named helpers.

4. Assertions and guards
- Validate inputs at the top of functions.
- Fail loudly on impossible states.
- Prefer guard clauses over nested conditionals.

5. Handle errors and return values
- Do not ignore success or failure signals.
- Catch specific exceptions and re-raise with context when needed.
- Do not silently swallow errors.

6. Minimal variable scope
- Declare variables close to first use.
- Avoid reusing one variable for unrelated values.
- Prefer immutable-style usage when practical.

7. Zero warnings
- Keep the code free of avoidable linter, type, and compiler warnings.
- Fix warnings instead of suppressing them unless there is a documented reason.

## Project-Specific Rules

- Keep Tkinter detail screens inside `detail_container`; do not add new `Toplevel` windows for dashboard detail views.
- Preserve working dashboard-card hitboxes and hand-mouse interactions when adjusting UI behavior.
- Prefer targeted changes over large UI rewrites.
- After Python UI edits, run `python3 -m compileall app`.

## Review Mode

When reviewing code in this project:
- Check each change against the 7 core rules above.
- Prioritize concrete bugs, regressions, and missing guards.
- Give file and line references when possible.
