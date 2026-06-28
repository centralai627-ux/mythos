---
name: autonomous
description: Use when you need to operate autonomously without user interruption - handles task chaining, automatic progression, and self-directed workflow completion
---

# Autonomous Operation Skill

## Core Principles

1. **Always have a next action** - Never idle waiting for input unless blocked
2. **Chain tasks automatically** - When one task finishes, immediately start the next
3. **Self-recover from blockers** - Try alternatives before stopping
4. **Minimal user interruption** - Only ask when truly ambiguous or destructive

## Workflow

### Starting Autonomous Mode
1. List all open tasks
2. Start the highest priority open task
3. Work until task is done or blocked
4. If done → check for next task → repeat
5. If blocked → try to unblock → if can't, move to next task

### Task Completion Check
After completing any task:
```
1. Run: task list (status=open)
2. If tasks exist → start next one
3. If no tasks → report completion summary
```

### Blocking Criteria
Only block and ask user when:
- Requirement is genuinely ambiguous (multiple valid interpretations)
- Action is destructive and irreversible (deleting production data, force push)
- Missing critical information that cannot be inferred
- Legal/ethical concerns

### Auto-Recovery Strategies
When encountering errors:
1. Read error message carefully
2. Check if similar error was solved before (search memory)
3. Try alternative approach
4. If same error 3x → document and move to next task
5. Never get stuck in infinite retry loops

## Progress Reporting

After every 5 tasks completed or when switching task categories:
- Brief summary of what was accomplished
- Current blockers if any
- Next planned actions

## Integration with Task System

Always use the `task` tool to:
- Track progress with `task start` before beginning work
- Mark completion with `task done` immediately after finishing
- Block with `task block` if genuinely stuck
- Create subtasks for complex work with `task create` and `parent_id`
