---
name: grill-me
description: Use when reviewing code quality, architecture, or preparing for merge in Mythos
---

# Grill Me: Code Review for Mythos

## Overview

Thorough code review that goes beyond surface-level checks. Focus on architecture, testability, maintainability, and Mythos-specific patterns.

## When to Use

- Before merging significant changes
- When reviewing complex code
- When preparing for release
- When onboarding new contributors

## Review Process

### 1. Understand Context

Before reviewing:
- What problem does this code solve?
- What are the requirements?
- What are the constraints?
- What are the dependencies?

### 2. Architecture Review

Check for:
- **Separation of concerns** - Are modules focused?
- **Dependency direction** - Are dependencies pointing the right way?
- **Interface design** - Are interfaces clean and minimal?
- **Coupling** - Are modules loosely coupled?

### 3. Code Quality Review

Check for:
- **Readability** - Is the code easy to understand?
- **Naming** - Are names clear and consistent?
- **Complexity** - Is the code too complex?
- **Duplication** - Is there unnecessary duplication?

### 4. Mythos-Specific Review

Check for:
- **Agent patterns** - Does it follow agent architecture?
- **API integration** - Is it properly integrated?
- **Memory usage** - Is memory managed correctly?
- **UI consistency** - Does it follow design system?

## Review Checklist

```markdown
## Code Review Checklist

### Architecture
- [ ] Separation of concerns maintained
- [ ] Dependencies pointing correctly
- [ ] Interfaces clean and minimal
- [ ] No circular dependencies

### Code Quality
- [ ] Code is readable
- [ ] Names are clear
- [ ] Complexity is manageable
- [ ] No duplication

### Testing
- [ ] Tests exist and pass
- [ ] Tests cover key behaviors
- [ ] Tests are maintainable
- [ ] Edge cases covered

### Mythos-Specific
- [ ] Follows agent patterns
- [ ] API integration correct
- [ ] Memory managed properly
- [ ] UI follows design system

### Security
- [ ] No secrets in code
- [ ] Input validation present
- [ ] No injection vulnerabilities
- [ ] API keys protected

### Performance
- [ ] No unnecessary operations
- [ ] Efficient algorithms used
- [ ] Memory usage reasonable
- [ ] No blocking operations
```

## Review Formats

### Quick Review

For small changes:

```markdown
## Quick Review

**Files**: [list files]
**Summary**: [one-line summary]
**Issues**: [list issues]
**Verdict**: Approve / Request changes
```

### Detailed Review

For significant changes:

```markdown
## Detailed Review

### Overview
[Description of changes]

### Architecture
[Architecture assessment]

### Code Quality
[Code quality assessment]

### Testing
[Testing assessment]

### Issues Found
[Detailed list of issues]

### Recommendations
[Specific recommendations]

### Verdict
[Approve / Request changes / Needs discussion]
```

## Mythos-Specific Review Patterns

### Agent Code

```python
# Review agent.py changes
def review_agent_code(changes):
    """Review agent code changes."""
    issues = []
    
    # Check for proper error handling
    if not has_error_handling(changes):
        issues.append("Missing error handling in agent")
    
    # Check for proper logging
    if not has_logging(changes):
        issues.append("Missing logging in agent")
    
    # Check for proper state management
    if not has_state_management(changes):
        issues.append("Improper state management")
    
    return issues
```

### API Integration

```python
# Review API client changes
def review_api_client(changes):
    """Review API client changes."""
    issues = []
    
    # Check for proper error handling
    if not has_api_error_handling(changes):
        issues.append("Missing API error handling")
    
    # Check for rate limiting
    if not has_rate_limiting(changes):
        issues.append("Missing rate limiting")
    
    # Check for retry logic
    if not has_retry_logic(changes):
        issues.append("Missing retry logic")
    
    return issues
```

### UI Components

```python
# Review UI changes
def review_ui_code(changes):
    """Review UI code changes."""
    issues = []
    
    # Check for design system compliance
    if not follows_design_system(changes):
        issues.append("Doesn't follow design system")
    
    # Check for responsiveness
    if not is_responsive(changes):
        issues.append("Not responsive")
    
    # Check for accessibility
    if not is_accessible(changes):
        issues.append("Accessibility issues")
    
    return issues
```

## Common Issues to Flag

### Architecture Issues

- **God modules** - Modules doing too much
- **Tight coupling** - Modules depending on internals
- **Circular dependencies** - A depends on B, B depends on A
- **Leaky abstractions** - Implementation details exposed

### Code Quality Issues

- **Magic numbers** - Unexplained constants
- **Deep nesting** - Too many levels of indentation
- **Long functions** - Functions doing too much
- **Poor naming** - Unclear variable/function names

### Mythos-Specific Issues

- **Missing error handling** - API calls without try/except
- **Hardcoded values** - Configuration in code
- **Missing logging** - No debug information
- **No tests** - Changes without tests

## Review Output Format

```markdown
## Review Summary

**Author**: [author]
**Date**: [date]
**Files**: [list of files reviewed]
**Lines changed**: [number]

### Issues Found

| Severity | File | Line | Issue |
|----------|------|------|-------|
| Critical | core/agent.py | 45 | Missing error handling |
| Warning | core/api_client.py | 78 | Hardcoded timeout |
| Info | core/ui.py | 123 | Consider extracting method |

### Recommendations

1. **Add error handling** for API calls
2. **Extract constants** to config
3. **Add logging** for debugging

### Verdict

**Approve** - Changes are good with minor suggestions.
```

## Related Skills

- **verification-before-completion** - For ensuring quality
- **systematic-debugging** - For investigating issues
- **improve-codebase-architecture** - For architectural improvements
