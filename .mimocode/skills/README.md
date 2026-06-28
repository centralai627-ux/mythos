# Mythos Skills Directory

This directory contains skills adapted from [skills.sh](https://www.skills.sh/) for the Mythos project.

## Skills Overview

### Testing & Quality

| Skill | Source | Description |
|-------|--------|-------------|
| **tdd** | mattpocock/skills | Test-driven development for Mythos Python agent |
| **verification-before-completion** | obra/superpowers | Force verification before marking tasks done |
| **grill-me** | mattpocock/skills | Deep code review for Mythos |

### Debugging & Architecture

| Skill | Source | Description |
|-------|--------|-------------|
| **systematic-debugging** | obra/superpowers | Find root cause before proposing fixes |
| **improve-codebase-architecture** | mattpocock/skills | Scan codebase for architectural improvements |

### Design & UI

| Skill | Source | Description |
|-------|--------|-------------|
| **frontend-design** | anthropics/skills | Design distinctive UI for Mythos desktop |
| **web-design-guidelines** | vercel-labs/agent-skills | Review UI code for design compliance |

### Skill Creation

| Skill | Source | Description |
|-------|--------|-------------|
| **skill-creator** | anthropics/skills | Create new skills for Mythos |
| **write-a-skill** | mattpocock/skills | Scaffold new agent skills |

### Workflow

| Skill | Source | Description |
|-------|--------|-------------|
| **handoff** | custom | Smooth handoff between tasks or agents |

### Document Processing

| Skill | Source | Description |
|-------|--------|-------------|
| **pdf** | anthropics/skills | PDF processing with text extraction, merging, splitting |
| **docx** | anthropics/skills | Create, read, edit Word documents (.docx) |
| **xlsx** | anthropics/skills | Create, edit, analyze Excel spreadsheets |

## Existing Skills

These skills were already present:

- **autonomous** - Operate autonomously without user interruption
- **autonomous-operation** - Complete autonomous operation framework
- **continuous-work** - Framework for continuous uninterrupted work
- **error-recovery** - Systematic error recovery patterns

## Usage

Skills are automatically available when working on the Mythos project. They provide specialized instructions and workflows for specific tasks.

### Loading a Skill

Skills are loaded automatically when a task matches their description. For example:

- Writing tests → **tdd** skill activates
- Debugging issues → **systematic-debugging** skill activates
- Building UI → **frontend-design** skill activates

### Creating New Skills

Use the **skill-creator** or **write-a-skill** skills to create new Mythos-specific skills.

## Skill Structure

Each skill follows this structure:

```
skill-name/
├── SKILL.md           # Main skill instructions
├── scripts/           # Optional executable scripts
├── references/        # Optional reference documentation
└── assets/            # Optional static assets
```

## Customization

Skills are adapted from skills.sh for Mythos-specific patterns:

- Python-specific testing patterns
- Mythos agent architecture
- Desktop UI design system
- API integration patterns

## Contributing

To add a new skill:

1. Create a new directory in `.mimocode/skills/`
2. Add `SKILL.md` with frontmatter and instructions
3. Update `package.json` with skill metadata
4. Test the skill with relevant tasks

## Resources

- [skills.sh](https://www.skills.sh/) - Open Agent Skills Ecosystem
- [Anthropic Skills](https://github.com/anthropics/skills)
- [Matt Pocock Skills](https://github.com/mattpocock/skills)
- [Obra Superpowers](https://github.com/obra/superpowers)
- [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills)
