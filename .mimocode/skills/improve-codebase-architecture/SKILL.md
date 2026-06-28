---
name: improve-codebase-architecture
description: Use when refactoring, organizing code, or improving Mythos module design and architecture
---

# Improve Mythos Codebase Architecture

## Overview

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is testability and maintainability.

## Mythos Architecture Overview

```
mythos/
├── mythos.py          # Entry point
├── core/
│   ├── agent.py       # Main agent logic
│   ├── api_client.py  # API integration
│   ├── memory.py      # Memory system
│   ├── tools.py       # Tool implementations
│   ├── commands.py    # Command handling
│   ├── ui.py          # UI components
│   └── config.py      # Configuration
├── assets/            # Static assets
└── config.json        # Configuration file
```

## Process

### 1. Explore

Walk the codebase and note where you experience friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test?

Apply the **deletion test**: would deleting it concentrate complexity, or just move it?

### 2. Identify Candidates

Look for these patterns:

#### Shallow Modules
```python
# SHALLOW: Interface nearly as complex as implementation
class MemoryManager:
    def __init__(self, config):
        self.config = config
        self.db = Database(config.db_path)
        self.cache = Cache(config.cache_size)
    
    def store(self, key, value):
        self.db.set(key, value)
        self.cache.set(key, value)
    
    def retrieve(self, key):
        if key in self.cache:
            return self.cache.get(key)
        return self.db.get(key)
```

#### Deep Modules
```python
# DEEP: Simple interface, deep implementation
class Memory:
    def __init__(self, config):
        self._implementation = self._create_implementation(config)
    
    def store(self, key, value):
        """Store a value in memory."""
        self._implementation.store(key, value)
    
    def retrieve(self, key):
        """Retrieve a value from memory."""
        return self._implementation.retrieve(key)
    
    def _create_implementation(self, config):
        """Create the appropriate memory implementation."""
        if config.memory_type == "redis":
            return RedisMemory(config)
        elif config.memory_type == "sqlite":
            return SQLiteMemory(config)
        else:
            return InMemoryStorage()
```

### 3. Propose Improvements

For each candidate, describe:

- **Files** — which files/modules are involved
- **Problem** — why the current architecture is causing friction
- **Solution** — plain English description of what would change
- **Benefits** — how tests would improve
- **Recommendation strength** — Strong, Worth exploring, or Speculative

## Mythos-Specific Architecture Patterns

### Agent Module

**Current Issues:**
- `agent.py` does too much (REPL, request processing, UI coordination)
- Tight coupling between agent and UI

**Proposed Solution:**
```python
# Split into focused modules
core/
├── agent/
│   ├── __init__.py
│   ├── core.py        # Core agent logic
│   ├── repl.py        # REPL interface
│   └── processor.py   # Request processing
├── ui/
│   ├── __init__.py
│   ├── chat.py        # Chat UI
│   └── display.py     # Display components
```

### API Client

**Current Issues:**
- Multiple API providers in one file
- No abstraction for different providers
- Hard to add new providers

**Proposed Solution:**
```python
# Abstract API provider interface
core/
├── api/
│   ├── __init__.py
│   ├── base.py        # Abstract base class
│   ├── openrouter.py  # OpenRouter implementation
│   ├── shannon.py     # Shannon implementation
│   └── factory.py     # Provider factory
```

### Memory System

**Current Issues:**
- Flat memory structure
- No separation of concerns
- Hard to extend

**Proposed Solution:**
```python
# Layered memory architecture
core/
├── memory/
│   ├── __init__.py
│   ├── base.py        # Abstract memory interface
│   ├── short_term.py  # Session memory
│   ├── long_term.py   # Persistent memory
│   └── cache.py       # Cache layer
```

## Implementation Guidelines

### Step 1: Create Failing Tests

Before refactoring, ensure existing tests pass:

```bash
python -m pytest
```

### Step 2: Make Small Changes

Refactor in small, testable increments:

1. Extract one module
2. Run tests
3. Fix any issues
4. Commit
5. Repeat

### Step 3: Update Imports

Update all imports to use new module structure:

```python
# Before
from core.agent import MythosAgent

# After
from core.agent.core import MythosAgent
```

### Step 4: Verify

After each change:

```bash
python -m pytest
python -m flake8 core/
python -m mypy core/
```

## Benefits of Better Architecture

### Testability
- Smaller, focused modules are easier to test
- Clear interfaces make mocking easier
- Isolated concerns reduce test complexity

### Maintainability
- Changes are localized to specific modules
- Easier to understand code flow
- Clear responsibility boundaries

### Extensibility
- New features can be added without modifying existing code
- Plugin architecture for new providers
- Easy to add new memory types

## Related Skills

- **tdd** - For writing tests during refactoring
- **systematic-debugging** - For investigating issues
- **verification-before-completion** - For ensuring quality
