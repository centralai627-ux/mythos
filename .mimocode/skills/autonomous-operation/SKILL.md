---
name: autonomous-operation
description: Complete autonomous operation framework - enables continuous self-directed work with automatic task chaining, error recovery, and minimal user interruption
---

# Autonomous Operation Framework

## Philosophy

Work like a senior engineer:
- Have a plan, execute it
- When done with one thing, move to the next
- Don't ask permission for routine operations
- Only escalate truly ambiguous decisions
- Learn from mistakes and don't repeat them

## Autonomous Workflow Loop

```
LOOP:
  1. CHECK state → task list (open tasks)
  2. IF no open tasks → REPORT completion → EXIT
  3. PICK next task (highest priority)
  4. START task
  5. EXECUTE task
  6. IF success → DONE task → GOTO 1
  7. IF blocked → TRY recovery (max 2 attempts)
  8. IF still blocked → BLOCK task with reason → GOTO 1
```

## Decision Matrix: Ask vs Act

| Situation | Action |
|-----------|--------|
| Clear requirement | ACT - just do it |
| Minor ambiguity | ACT - make reasonable assumption, document it |
| Multiple valid approaches | ACT - pick best, explain in summary |
| Destructive action | ASK - confirm first |
| Missing critical info | ASK - specific question only |
| Legal/ethical concern | ASK - always |

## Task Execution Protocol

### Starting Work
```bash
task list status=open    # See what needs doing
task start id=<id>       # Begin work
```

### During Work
- Work systematically through subtasks
- Document decisions in task comments
- If you deviate from plan, explain why

### Completing Work
```bash
task done id=<id> event_summary="Brief description of what was accomplished"
# IMMEDIATELY after:
task list status=open    # Check for next task
```

### When Blocked
```bash
task block id=<id> event_summary="Specific reason for blocker"
# Then:
task list status=open    # Move to next task
```

## Error Handling

1. **First failure**: Read error, try obvious fix
2. **Second failure**: Search for similar errors in memory, try alternative approach
3. **Third failure**: Document issue, move to next task
4. **Never**: Retry same command more than 3 times

## Progress Reporting

After completing 5+ tasks or when switching work categories:
```
## Progress Update
- Completed: [list of tasks]
- In Progress: [current task]
- Blocked: [blockers with reasons]
- Next: [planned actions]
```

## Memory Integration

Before starting work:
- Search memory for similar past tasks
- Check for project-specific patterns
- Note any learned preferences

After completing work:
- Record solutions to non-obvious problems
- Note any new patterns discovered
- Update project knowledge

## Communication Style

During autonomous operation:
- Minimal output between tasks
- Clear status updates at milestones
- Concise summaries, not essays
- Focus on what changed, not what you tried

## Anti-Patterns to Avoid

- Asking "what should I do next?" when tasks exist
- Waiting for confirmation on routine operations
- Retrying failed commands without changing approach
- Explaining obvious actions
- Creating unnecessary documentation mid-task
