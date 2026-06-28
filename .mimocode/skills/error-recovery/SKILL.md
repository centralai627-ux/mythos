---
name: error-recovery
description: Systematic error recovery patterns for autonomous operation - helps recover from failures without stopping
---

# Error Recovery Patterns

## Recovery Flow

```
ERROR occurs
  ↓
Read error message carefully
  ↓
Is it obvious? → Fix it → Continue
  ↓
Search memory for similar errors
  ↓
Found solution? → Apply it → Continue
  ↓
Try alternative approach (max 2 alternatives)
  ↓
Still failing? → Document & move on
```

## Common Error Patterns

### File/Path Errors
- "No such file" → Check path, create directory first
- "Permission denied" → Try different approach, don't use sudo
- "Already exists" → Use -Force or remove first

### Git Errors
- "Not a git repository" → git init first
- "Nothing to commit" → Check if changes are staged
- "Merge conflict" → Read file, resolve manually

### PowerShell Specific
- Use `;` not `&&` for chaining
- Quote paths with spaces
- Use `-Force` for overwrites

### Network/API Errors
- "Connection refused" → Check URL, try again
- "Timeout" → Reduce scope, try smaller request
- "Rate limited" → Wait or use different key

## Recovery Rules

1. **Never retry same command** without changing something
2. **Max 2 alternative approaches** before moving on
3. **Document what failed** in task/block
4. **Don't ask user** for obvious fixes
5. **Learn from errors** - search memory before retrying

## When to Give Up

Stop trying and move on when:
- Same error 3 times
- Requires user-specific information you don't have
- Would need system changes beyond your scope
- Legal/ethical concerns

Always document WHY you moved on.
