---
name: continuous-work
description: Framework for continuous uninterrupted work - handles task chaining, progress tracking, and autonomous completion
---

# Continuous Work Framework

## The Loop

```
1. task list status=open
2. IF no tasks → EXIT with summary
3. task start id=<first>
4. WORK until done or blocked
5. task done id=<id> event_summary="..."
6. GOTO 1
```

## Task Selection Priority

When multiple tasks exist:
1. In-progress tasks first
2. Blocked tasks that can now proceed
3. Highest priority open tasks
4. Smallest tasks (quick wins) if morale matters

## Work Execution

### Before Starting
- Search memory for similar work
- Check project conventions
- Understand the task fully

### During Work
- Focus on one task at a time
- Make progress, not excuses
- Document decisions briefly

### After Completing
- Mark done immediately
- Note any learnings
- Check for next task

## Handling Interruptions

If you must pause (user interaction required):
1. Complete current logical unit of work
2. Save state in task comments
3. Note exactly where you stopped
4. When resuming, read task state first

## Progress Tracking

After every 5 tasks or when switching categories:
```
Completed: [list]
Current: [task]
Blocked: [issues]
Next: [plan]
```

## Anti-Idle Rules

NEVER:
- Ask "what next?" when tasks exist
- Wait for confirmation on routine work
- Retry same failing approach
- Explain obvious actions

ALWAYS:
- Have a next action ready
- Make reasonable assumptions
- Learn from errors
- Keep moving forward
