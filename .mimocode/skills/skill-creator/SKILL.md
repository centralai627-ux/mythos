---
name: skill-creator
description: Use when creating new skills for Mythos, modifying existing skills, or measuring skill performance
---

# Skill Creator for Mythos

A skill for creating new skills and iteratively improving them.

## Process

1. **Decide** what you want the skill to do and roughly how it should do it
2. **Write** a draft of the skill
3. **Create** a few test prompts and run Mythos with access to the skill on them
4. **Evaluate** the results both qualitatively and quantitatively
5. **Rewrite** the skill based on feedback
6. **Repeat** until satisfied

## Anatomy of a Mythos Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output
```

## SKILL.md Template

```markdown
---
name: skill-name
description: Clear description of when to use this skill. Include trigger keywords.
---

# Skill Title

## Overview

What this skill does and why it exists.

## When to Use

- Use case 1
- Use case 2
- Use case 3

## Workflow

### Step 1: [First Step]
Instructions for step 1.

### Step 2: [Second Step]
Instructions for step 2.

## Examples

### Example 1: [Scenario]
Input: [what user provides]
Output: [what skill produces]

### Example 2: [Another Scenario]
Input: [what user provides]
Output: [what skill produces]

## Anti-Patterns

- Don't do X
- Avoid Y
- Never Z

## Related Skills

- **other-skill** - For related functionality
```

## Writing Guide

### Frontmatter

```yaml
---
name: skill-name
description: >
  Clear, descriptive text about what this skill does.
  Include specific trigger keywords and use cases.
  This is what determines when the skill activates.
---
```

### Description Best Practices

**Good description:**
```
Use when building or modifying the Mythos desktop app interface.
Triggers: UI, desktop app, window, interface, design, theme, layout
```

**Bad description:**
```
A skill for doing things.
```

### Body Structure

1. **Overview** - One paragraph explaining the skill
2. **When to Use** - Specific triggers and use cases
3. **Workflow** - Step-by-step instructions
4. **Examples** - Concrete input/output examples
5. **Anti-Patterns** - What to avoid
6. **Related Skills** - Links to complementary skills

### Progressive Disclosure

- Keep SKILL.md under 500 lines
- Use reference files for large content
- Reference files clearly with guidance on when to read them

## Testing Skills

### Test Prompt Creation

Create 2-3 realistic test prompts:

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

### Running Tests

```bash
# Test the skill
python -m pytest tests/test_skill.py -v

# Test with coverage
python -m pytest tests/test_skill.py --cov=skill_name
```

## Mythos-Specific Skill Patterns

### Agent Integration Skills

```markdown
---
name: agent-integration
description: Integrate external services with Mythos agent
---

# Agent Integration

## When to Use
- Adding new API integrations
- Connecting external tools
- Extending agent capabilities

## Workflow

1. **Identify** the external service
2. **Create** API client in core/api_client.py
3. **Add** commands in core/commands.py
4. **Update** agent.py to expose new functionality
5. **Write** tests for the integration
```

### Memory/Storage Skills

```markdown
---
name: memory-management
description: Manage Mythos memory and storage systems
---

# Memory Management

## When to Use
- Modifying memory storage
- Adding new memory types
- Optimizing memory retrieval

## Workflow

1. **Understand** current memory structure
2. **Design** new memory schema
3. **Implement** in core/memory.py
4. **Add** retrieval methods
5. **Test** storage and retrieval
```

### UI Component Skills

```markdown
---
name: ui-components
description: Create and modify Mythos desktop UI components
---

# UI Components

## When to Use
- Building new UI elements
- Modifying existing components
- Creating themed variations

## Workflow

1. **Check** existing components
2. **Design** following design system
3. **Implement** with CSS variables
4. **Add** animations where appropriate
5. **Test** across different states
```

## Description Optimization

### Trigger Keywords

Include specific keywords that should activate the skill:

```yaml
description: >
  Use when building or modifying the Mythos desktop app interface.
  Triggers: UI, desktop app, window, interface, design, theme, layout,
  component, button, input, display, screen, view
```

### Context Matching

The description should match:
- **What** the skill does
- **When** to use it
- **Why** it's useful

### Anti-Triggers

Also specify when NOT to use the skill:

```yaml
description: >
  Use for Mythos desktop UI work.
  Do NOT use for: CLI interface, API integration, core logic
```

## Related Skills

- **write-a-skill** - For detailed skill writing guidance
- **frontend-design** - For UI design patterns
- **tdd** - For testing skills
