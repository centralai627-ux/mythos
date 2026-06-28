---
name: handoff
description: Use when transitioning between tasks or agents in Mythos to ensure smooth handoff
---

# Handoff for Mythos

## Overview

Smooth transitions between tasks, ensuring context is preserved and work continues seamlessly.

## When to Use

- Transitioning between tasks
- Handing off to another agent
- Pausing work for later continuation
- Escalating to user

## Handoff Process

### 1. Document Current State

Before handoff, document:

```markdown
## Current State

**Task**: [Task description]
**Progress**: [What's been done]
**Remaining**: [What's left]
**Blockers**: [Any blockers]
**Context**: [Important context]
```

### 2. Create Continuation Instructions

```markdown
## Continuation Instructions

### Next Steps
1. [First step]
2. [Second step]
3. [Third step]

### Key Files
- `core/agent.py` - Main agent logic
- `core/api_client.py` - API integration
- `tests/test_agent.py` - Agent tests

### Important Notes
- [Note 1]
- [Note 2]
- [Note 3]
```

### 3. Save State

Save state to memory or task system:

```python
# Save to memory
memory.store("task_state", {
    "task_id": "T1",
    "progress": "50%",
    "next_step": "Implement API integration",
    "blockers": [],
    "context": "Working on agent extension"
})

# Or save to task system
task.block(id="T1", event_summary="Waiting for API credentials")
```

### 4. Verify Handoff

Before completing handoff:

- [ ] State documented
- [ ] Instructions clear
- [ ] Context preserved
- [ ] Next steps defined
- [ ] Blockers identified

## Handoff Formats

### Task-to-Task Handoff

```markdown
## Task Handoff

**From**: T1 (Implement API client)
**To**: T2 (Write tests for API client)

### What was done
- Created API client in `core/api_client.py`
- Implemented OpenRouter integration
- Added error handling

### What needs to be done
- Write unit tests for API client
- Test error scenarios
- Test rate limiting

### Key files
- `core/api_client.py` - API client implementation
- `tests/test_api_client.py` - Test file (empty)

### Notes
- API keys are in `config.json`
- Use `pytest` for testing
- Mock external API calls
```

### Agent-to-Agent Handoff

```markdown
## Agent Handoff

**From**: Explore Agent
**To**: General Agent

### Findings
- [Finding 1]
- [Finding 2]
- [Finding 3]

### Recommendations
- [Recommendation 1]
- [Recommendation 2]

### Next Steps
- [Step 1]
- [Step 2]
```

### Pause and Resume

```markdown
## Pause State

**Task**: T1 (Implement new feature)
**Time**: 2024-01-15 14:30:00
**Progress**: 40%

### Completed
- [x] Analyzed requirements
- [x] Designed solution
- [x] Created basic structure

### In Progress
- [ ] Implementing core logic

### Remaining
- [ ] Write tests
- [ ] Update documentation
- [ ] Review and merge

### Context
- Working on agent extension
- Using TDD approach
- Following existing patterns
```

## Mythos-Specific Handoff Patterns

### Memory Handoff

```python
# Save work state to memory
def save_work_state(memory, task_id, state):
    """Save work state for later resumption."""
    memory.store(f"work_state_{task_id}", {
        "timestamp": datetime.now().isoformat(),
        "progress": state["progress"],
        "completed": state["completed"],
        "remaining": state["remaining"],
        "context": state["context"],
        "blockers": state["blockers"]
    })

# Load work state from memory
def load_work_state(memory, task_id):
    """Load work state for resumption."""
    return memory.retrieve(f"work_state_{task_id}")
```

### Task System Handoff

```python
# Block task with handoff notes
def handoff_task(task_id, reason, notes):
    """Handoff task with detailed notes."""
    task.block(
        id=task_id,
        event_summary=reason
    )
    
    # Save detailed notes to memory
    memory.store(f"handoff_{task_id}", {
        "reason": reason,
        "notes": notes,
        "timestamp": datetime.now().isoformat()
    })

# Unblock and resume task
def resume_task(task_id):
    """Resume task with context."""
    handoff = memory.retrieve(f"handoff_{task_id}")
    task.unblock(
        id=task_id,
        event_summary=f"Resuming: {handoff['reason']}"
    )
    return handoff
```

### Agent Communication

```python
# Send handoff message to another agent
def send_handoff(to_agent, task_id, context):
    """Send handoff message to another agent."""
    message = {
        "type": "handoff",
        "task_id": task_id,
        "context": context,
        "timestamp": datetime.now().isoformat()
    }
    
    agent.send(to_agent, json.dumps(message))

# Receive handoff message
def receive_handoff(message):
    """Receive and process handoff message."""
    data = json.loads(message)
    if data["type"] == "handoff":
        return {
            "task_id": data["task_id"],
            "context": data["context"],
            "timestamp": data["timestamp"]
        }
    return None
```

## Handoff Checklist

```markdown
## Handoff Checklist

### Before Handoff
- [ ] Document current state
- [ ] Create continuation instructions
- [ ] Identify blockers
- [ ] Save state to memory/task system

### During Handoff
- [ ] Communicate clearly
- [ ] Preserve context
- [ ] Define next steps
- [ ] Set expectations

### After Handoff
- [ ] Verify handoff received
- [ ] Confirm understanding
- [ ] Start work promptly
- [ ] Update status
```

## Common Handoff Scenarios

### Waiting for User Input

```markdown
## Handoff: Waiting for User

**Task**: T1 (Implement new feature)
**Status**: Blocked

### Blocker
Need user decision on API provider choice.

### Options
1. OpenRouter - More models, higher cost
2. Shannon - Fewer models, lower cost
3. Both - Maximum flexibility

### Recommendation
OpenRouter for flexibility.

### Next Steps
Once user decides:
1. Update config.json
2. Implement provider
3. Write tests
```

### Waiting for External Dependency

```markdown
## Handoff: Waiting for Dependency

**Task**: T2 (Integrate payment system)
**Status**: Blocked

### Blocker
Waiting for payment API credentials from user.

### What's Ready
- Payment client structure created
- Integration patterns defined
- Test framework ready

### What's Needed
- API key
- API secret
- Webhook URL

### Next Steps
Once credentials received:
1. Add to config.json
2. Implement payment flow
3. Test with sandbox
```

### Task Complete

```markdown
## Handoff: Task Complete

**Task**: T3 (Fix agent bug)
**Status**: Done

### What was done
- Identified root cause in `core/agent.py:45`
- Implemented fix
- Added tests
- Verified fix works

### Files changed
- `core/agent.py` - Fixed error handling
- `tests/test_agent.py` - Added test case

### Next steps
- Review and merge
- Update documentation
- Close issue
```

## Related Skills

- **verification-before-completion** - For ensuring quality before handoff
- **systematic-debugging** - For investigating blockers
- **improve-codebase-architecture** - For addressing root causes
