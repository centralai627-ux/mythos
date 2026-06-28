---
name: write-a-skill
description: Use when creating a new skill for the Mythos project with structured templates
---

# Writing Skills for Mythos

## Process

1. **Gather requirements** - ask user about:
   - What task/domain does the skill cover?
   - What specific use cases should it handle?
   - Does it need executable scripts or just instructions?
   - Any reference materials to include?

2. **Draft the skill** - create:
   - SKILL.md with concise instructions
   - Additional reference files if content exceeds 500 lines
   - Utility scripts if deterministic operations needed

3. **Review with user** - present draft and ask:
   - Does this cover your use cases?
   - Anything missing or unclear?
   - Should any section be more/less detailed?

4. **Finalize** - create the skill directory structure

## Skill Directory Structure

```
.mimocode/skills/
└── skill-name/
    ├── SKILL.md
    ├── scripts/          (optional)
    │   └── helper.py
    ├── references/       (optional)
    │   └── api-docs.md
    └── assets/           (optional)
        └── template.txt
```

## SKILL.md Template for Mythos

```markdown
---
name: skill-name
description: >
  Clear description of when to use this skill.
  Include trigger keywords and use cases.
---

# Skill Title

## Overview

One paragraph explaining what this skill does and why it exists.

## When to Use

- Use case 1: [description]
- Use case 2: [description]
- Use case 3: [description]

## Workflow

### Step 1: [First Step]
Instructions for step 1.

### Step 2: [Second Step]
Instructions for step 2.

### Step 3: [Third Step]
Instructions for step 3.

## Examples

### Example 1: [Scenario]
**Input**: [what user provides]
**Output**: [what skill produces]

### Example 2: [Another Scenario]
**Input**: [what user provides]
**Output**: [what skill produces]

## Anti-Patterns

- Don't do X
- Avoid Y
- Never Z

## Related Skills

- **other-skill** - For related functionality
```

## Mythos-Specific Skill Patterns

### Agent Extension Skills

```markdown
---
name: agent-extension
description: Extend Mythos agent with new capabilities
---

# Agent Extension

## When to Use
- Adding new commands
- Integrating external services
- Creating new tools

## Workflow

1. **Identify** the new capability
2. **Design** the interface
3. **Implement** in appropriate module
4. **Add** to commands.py or tools.py
5. **Write** tests
6. **Update** documentation
```

### Memory Skills

```markdown
---
name: memory-operations
description: Manage Mythos memory and storage
---

# Memory Operations

## When to Use
- Storing data persistently
- Retrieving historical information
- Managing session state

## Workflow

1. **Check** existing memory structure
2. **Design** storage schema
3. **Implement** storage methods
4. **Add** retrieval methods
5. **Test** persistence
```

### UI Skills

```markdown
---
name: ui-development
description: Create Mythos desktop UI components
---

# UI Development

## When to Use
- Building new interface elements
- Modifying existing components
- Creating themed variations

## Workflow

1. **Check** design system
2. **Design** component
3. **Implement** with CSS variables
4. **Add** animations
5. **Test** across states
```

## Writing Style

### Do

- Use clear, concise language
- Provide concrete examples
- Explain the "why" behind instructions
- Use progressive disclosure

### Don't

- Use vague instructions
- Skip examples
- Make assumptions about user knowledge
- Create overly complex structures

## Testing Skills

### Create Test Cases

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "Realistic user prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

### Run Tests

```bash
# Test the skill
python -m pytest tests/test_skill.py -v

# Test with coverage
python -m pytest tests/test_skill.py --cov=skill_name
```

## Skill Description Best Practices

### Good Description

```yaml
description: >
  Use when building or modifying the Mythos desktop app interface.
  Triggers: UI, desktop app, window, interface, design, theme, layout,
  component, button, input, display, screen, view
```

### Bad Description

```yaml
description: >
  A skill for doing things.
```

## Related Skills

- **skill-creator** - For detailed skill creation guidance
- **frontend-design** - For UI design patterns
- **tdd** - For testing skills
