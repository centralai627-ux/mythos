---
name: web-design-guidelines
description: Use when reviewing Mythos UI code for design compliance, accessibility, or auditing design
---

# Web Design Guidelines for Mythos

## Overview

Review files for compliance with Mythos design guidelines and best practices.

## How It Works

1. Read the specified files
2. Check against all design rules
3. Output findings in `file:line` format

## Design Rules

### 1. Color System

**Rule**: Use CSS variables for all colors.

```css
/* CORRECT */
.message { color: var(--text-primary); }

/* WRONG */
.message { color: #ffffff; }
```

**Rule**: Follow the color palette.

```css
:root {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --accent-primary: #533483;
  --accent-secondary: #e94560;
  --accent-highlight: #00d9ff;
}
```

### 2. Typography

**Rule**: Use the type scale.

```css
:root {
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
}
```

**Rule**: Use monospace for code.

```css
code, pre { font-family: var(--font-mono); }
```

### 3. Spacing

**Rule**: Use consistent spacing.

```css
:root {
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
}
```

### 4. Components

**Rule**: Follow component patterns.

```css
/* Chat message pattern */
.message-user {
  background: var(--bg-tertiary);
  border-left: 3px solid var(--accent-primary);
}

.message-agent {
  background: var(--bg-secondary);
  border-left: 3px solid var(--accent-highlight);
}
```

### 5. Accessibility

**Rule**: Ensure sufficient contrast.

```css
/* CORRECT - high contrast */
.text { color: var(--text-primary); background: var(--bg-primary); }

/* WRONG - low contrast */
.text { color: var(--text-muted); background: var(--bg-secondary); }
```

**Rule**: Add focus styles.

```css
:focus {
  outline: 2px solid var(--accent-highlight);
  outline-offset: 2px;
}
```

### 6. Responsive Design

**Rule**: Use flexible layouts.

```css
.container {
  max-width: 100%;
  padding: var(--space-md);
}

@media (min-width: 768px) {
  .container {
    max-width: 800px;
    margin: 0 auto;
  }
}
```

### 7. Animation

**Rule**: Use subtle animations.

```css
/* CORRECT - subtle pulse */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* WRONG - distracting animation */
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
```

## Review Process

### Step 1: Read Files

```python
# Read files to review
files = ["core/ui.py", "assets/styles.css"]
```

### Step 2: Check Rules

For each file, check:
- Color usage
- Typography
- Spacing
- Component patterns
- Accessibility
- Responsive design
- Animation

### Step 3: Output Findings

```markdown
## Design Review

**Files**: core/ui.py, assets/styles.css
**Date**: 2024-01-15

### Findings

| Severity | File | Line | Issue |
|----------|------|------|-------|
| Warning | core/ui.py | 45 | Hardcoded color |
| Error | assets/styles.css | 78 | Missing focus styles |
| Info | core/ui.py | 123 | Consider extracting method |

### Recommendations

1. **Use CSS variables** for colors (core/ui.py:45)
2. **Add focus styles** (assets/styles.css:78)
3. **Extract method** for reusability (core/ui.py:123)
```

## Mythos-Specific Guidelines

### Chat Interface

```css
/* Message container */
.chat-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-md);
}

/* Message bubble */
.message {
  max-width: 80%;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--space-sm);
}

/* User message */
.message-user {
  align-self: flex-end;
  background: var(--bg-tertiary);
  border-left: 3px solid var(--accent-primary);
}

/* Agent message */
.message-agent {
  align-self: flex-start;
  background: var(--bg-secondary);
  border-left: 3px solid var(--accent-highlight);
}
```

### Input Area

```css
/* Input container */
.input-container {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--bg-secondary);
  border-top: 1px solid var(--bg-tertiary);
}

/* Input field */
.input-field {
  flex: 1;
  padding: var(--space-sm);
  background: var(--bg-primary);
  border: 1px solid var(--bg-tertiary);
  border-radius: var(--space-sm);
  color: var(--text-primary);
  font-family: var(--font-mono);
}

/* Submit button */
.input-submit {
  padding: var(--space-sm) var(--space-md);
  background: var(--accent-primary);
  color: var(--text-primary);
  border: none;
  border-radius: var(--space-sm);
  cursor: pointer;
}

.input-submit:hover {
  background: var(--accent-secondary);
}
```

### Status Bar

```css
/* Status container */
.status-bar {
  display: flex;
  justify-content: space-between;
  padding: var(--space-xs) var(--space-md);
  background: var(--bg-tertiary);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}

/* Status indicators */
.status-connected { color: #00ff88; }
.status-disconnected { color: var(--accent-secondary); }
.status-loading { 
  color: var(--accent-highlight);
  animation: pulse 1.5s infinite;
}
```

## Common Issues

### Wrong: Hardcoded Colors

```css
/* WRONG */
.message { color: #ffffff; }
.button { background: #e94560; }

/* CORRECT */
.message { color: var(--text-primary); }
.button { background: var(--accent-secondary); }
```

### Wrong: Inconsistent Spacing

```css
/* WRONG */
.container { padding: 15px; }
.message { margin: 10px; }

/* CORRECT */
.container { padding: var(--space-md); }
.message { margin: var(--space-sm); }
```

### Wrong: Missing Focus Styles

```css
/* WRONG */
button:focus { outline: none; }

/* CORRECT */
button:focus {
  outline: 2px solid var(--accent-highlight);
  outline-offset: 2px;
}
```

## Related Skills

- **frontend-design** - For design system creation
- **skill-creator** - For creating design skills
- **verification-before-completion** - For ensuring quality
