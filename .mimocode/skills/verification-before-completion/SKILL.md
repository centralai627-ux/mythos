---
name: verification-before-completion
description: Use when completing features, fixing bugs, or making changes to force verification before marking tasks done
---

# Verification Before Completion for Mythos

## Overview

Every task must be verified before marking it complete. This prevents accepting incorrect output and debugging it afterward.

## The Verification Protocol

### Before Marking Done

1. **Run Tests**
   ```bash
   python -m pytest
   ```

2. **Check Linting**
   ```bash
   python -m flake8 core/
   ```

3. **Verify Type Hints**
   ```bash
   python -m mypy core/
   ```

4. **Manual Testing**
   - Test the specific change
   - Test related functionality
   - Test edge cases

5. **Review Changes**
   - Read the diff
   - Check for unintended changes
   - Verify no secrets/keys exposed

### Verification Checklist

```markdown
## Verification Checklist

### Functional
- [ ] Feature works as intended
- [ ] Edge cases handled
- [ ] Error handling implemented
- [ ] No regression in existing functionality

### Code Quality
- [ ] Tests pass
- [ ] No lint errors
- [ ] Type hints correct
- [ ] Code follows project style

### Security
- [ ] No secrets in code
- [ ] Input validation added
- [ ] No SQL injection/XSS vectors
- [ ] API keys not exposed

### Documentation
- [ ] README updated if needed
- [ ] Code comments added for complex logic
- [ ] API documentation updated
```

## Mythos-Specific Verification

### Agent Behavior

```python
def verify_agent_behavior():
    """Verify agent processes requests correctly."""
    agent = MythosAgent()
    
    # Test basic request
    response = agent._process_request("hello")
    assert response is not None
    assert len(response) > 0
    
    # Test error handling
    try:
        agent._process_request("invalid_api_key", simulate_error=True)
    except APIError:
        pass  # Expected
    
    # Test memory integration
    agent.memory.store("test_key", "test_value")
    assert agent.memory.retrieve("test_key") == "test_value"
```

### API Integration

```python
def verify_api_integration():
    """Verify API client works correctly."""
    client = APIClient()
    
    # Test request building
    request = client.build_request("test")
    assert "model" in request
    assert "messages" in request
    
    # Test response parsing
    response = client.parse_response(mock_response)
    assert "content" in response
    
    # Test error handling
    with pytest.raises(APIError):
        client.handle_error(invalid_response)
```

### UI Components

```python
def verify_ui_components():
    """Verify UI components render correctly."""
    # Test component rendering
    component = ChatMessage("user", "test message")
    assert component.render() is not None
    
    # Test styling
    assert component.get_style("color") == "#ffffff"
    
    # Test interactions
    component.on_click()
    assert component.clicked is True
```

## Verification Tools

### Automated Verification

```bash
# Full verification suite
python -m pytest --tb=short
python -m flake8 core/ --max-line-length=100
python -m mypy core/ --ignore-missing-imports

# Security scan
python -m bandit -r core/

# Dependency check
python -m safety check
```

### Manual Verification

```python
# Verify API keys not in code
import subprocess
result = subprocess.run(
    ["grep", "-r", "sk-", "core/"],
    capture_output=True,
    text=True
)
if result.stdout:
    print("WARNING: API keys found in code!")
    print(result.stdout)
```

## Verification Report Format

```markdown
## Verification Report

**Task**: [Task description]
**Date**: [Date]
**Verified by**: [Agent/Tool]

### Results

| Check | Status | Notes |
|-------|--------|-------|
| Tests pass | ✅ | All 45 tests passed |
| Lint clean | ✅ | No errors |
| Type hints | ⚠️ | 2 warnings (non-critical) |
| Manual test | ✅ | Feature works as expected |
| Security scan | ✅ | No issues found |

### Issues Found

None

### Conclusion

Task is verified and ready for completion.
```

## When Verification Fails

### Immediate Actions

1. **Don't mark done** - Keep task in progress
2. **Document failure** - What failed and why
3. **Fix root cause** - Use systematic-debugging skill
4. **Re-verify** - Run verification again
5. **Mark done only when all checks pass**

### Escalation

If verification fails 3+ times:
1. Question the approach
2. Consider architectural issues
3. Discuss with user
4. Document lessons learned

## Related Skills

- **tdd** - For writing proper tests
- **systematic-debugging** - For investigating failures
- **improve-codebase-architecture** - For addressing root causes
