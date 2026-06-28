---
name: tdd
description: Use when writing tests, building features test-first, fixing bugs with tests, or improving code quality in Mythos Python agent
---

# Test-Driven Development for Mythos

## Philosophy

**Core principle**: Tests should verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't.

**Good tests** are integration-style: they exercise real code paths through public APIs. They describe _what_ the system does, not _how_ it does it.

**Bad tests** are coupled to implementation. They mock internal collaborators, test private methods, or verify through external means. The warning sign: your test breaks when you refactor, but behavior hasn't changed.

## Anti-Pattern: Horizontal Slices

**DO NOT write all tests first, then all implementation.** This produces brittle tests that test imagined behavior.

**Correct approach**: Vertical slices via tracer bullets. One test → one implementation → repeat.

```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
  ...
```

## Workflow for Mythos

### 1. Planning

Before writing any code:

- [ ] Confirm what interface changes are needed
- [ ] Confirm which behaviors to test (prioritize)
- [ ] List the behaviors to test (not implementation steps)
- [ ] Get user approval on the plan

Ask: "What should the public interface look like? Which behaviors are most important to test?"

### 2. Tracer Bullet

Write ONE test that confirms ONE thing about the system:

```
RED:   Write test for first behavior → test fails
GREEN: Write minimal code to pass → test passes
```

### 3. Incremental Loop

For each remaining behavior:

```
RED:   Write next test → fails
GREEN: Minimal code to pass → passes
```

Rules:
- One test at a time
- Only enough code to pass current test
- Don't anticipate future tests
- Keep tests focused on observable behavior

### 4. Refactor

After all tests pass, look for refactor candidates:

- [ ] Extract duplication
- [ ] Deepen modules (move complexity behind simple interfaces)
- [ ] Apply SOLID principles where natural
- [ ] Run tests after each refactor step

**Never refactor while RED.** Get to GREEN first.

## Mythos-Specific Testing Patterns

### Testing Agent Behavior

```python
def test_agent_processes_request():
    """Test that agent processes a user request and returns response."""
    agent = MythosAgent()
    response = agent._process_request("hello")
    assert response is not None
    assert isinstance(response, str)

def test_agent_handles_api_error():
    """Test that agent handles API errors gracefully."""
    agent = MythosAgent()
    with pytest.raises(APIError):
        agent._process_request("test", simulate_error=True)
```

### Testing Core Modules

```python
def test_memory_stores_and_retrieves():
    """Test memory module stores and retrieves data."""
    memory = Memory()
    memory.store("key", "value")
    assert memory.retrieve("key") == "value"

def test_config_loads_correctly():
    """Test config loads from file."""
    config = Config("config.json")
    assert config.llm.provider == "openrouter"
```

### Testing API Integration

```python
def test_api_client_makes_request():
    """Test API client makes correct request format."""
    client = APIClient()
    request = client.build_request("test prompt")
    assert "model" in request
    assert "messages" in request
```

## Checklist Per Cycle

```
[ ] Test describes behavior, not implementation
[ ] Test uses public interface only
[ ] Test would survive internal refactor
[ ] Code is minimal for this test
[ ] No speculative features added
```

## Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_agent.py

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=core
```

## Related Skills

- **systematic-debugging** - For investigating test failures
- **verification-before-completion** - For ensuring quality before marking tasks done
