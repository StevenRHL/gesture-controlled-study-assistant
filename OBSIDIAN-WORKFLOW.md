# Obsidian Workflow

## Purpose

This file defines how Codex should keep the project memory in Obsidian synchronized with the real codebase.

## Obsidian location

- Vault root: `/Users/steven/Steven's Things/Personal File/Obsidian`
- Project memory: `/Users/steven/Steven's Things/Personal File/Obsidian/Projects/Hands`

## Required read order

Before making assumptions on any task-related prompt, read:

1. `AI-CONTEXT.md`
2. `Branches/<current-branch>.md` when it exists
3. Any bug or decision note that matches the task
4. The latest dated handoff note if the work appears to continue earlier work

## Required write triggers

Update the Obsidian notes whenever any of the following happens:

- a new task-related user prompt changes project direction or understanding
- files are inspected and new facts are learned
- code is changed
- a command or test is run
- a bug is confirmed, narrowed down, or ruled out
- a design or implementation decision is made
- work stops with unresolved issues or a recommended next step

## Minimum note updates per meaningful task

- Update the current branch note with:
  - what was attempted
  - what was learned
  - what changed
  - what remains risky or unresolved
- Update or create a bug note when behavior is broken, suspected broken, or under active debugging.
- Update or create a decision note when a rule, tradeoff, or architecture choice becomes explicit.
- Create or refresh a dated handoff note for the session.

## Writing standard

- Use concrete file paths, class names, method names, commands, and observed behavior.
- Prefer dated bullet entries over vague summaries.
- Distinguish between:
  - confirmed behavior
  - inferred behavior
  - untested assumptions
- Do not claim runtime verification unless a command or manual run actually happened.

## Current project anchors

- Main entrypoint: `app/main.py`
- Main UI: `app/ui/main_window.py`
- Dashboard detail views must stay inside `detail_container`
- `update_loop` is a high-risk path and should not be changed unless explicitly requested
- Virtual mouse runtime in the main app currently uses `app/core/virtual_mouse.py` with `app/ui/assistive_touch_cursor.py`
- `app/ui/mouse_overlay.py` is a separate standalone Qt overlay path and is not the primary in-app overlay path

## Final-step checklist

Before sending the final reply on a task-related turn:

1. Update Obsidian notes.
2. Make sure the branch note reflects the latest reality.
3. Add a handoff note with the date, goal, files inspected, files changed, commands used, unresolved issues, and next step.
4. In the final reply, mention that the Obsidian memory was updated when relevant.
