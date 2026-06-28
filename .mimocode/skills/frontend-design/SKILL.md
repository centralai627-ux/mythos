---
name: frontend-design
description: Use when building or modifying Mythos desktop app interface, creating new UI components, or improving visual design
---

# Frontend Design for Mythos Desktop

## Philosophy

Approach this as the design lead at a small studio known for giving every client a visual identity that could not be mistaken for anyone else's. Mythos is an AI agent - its interface should reflect intelligence, power, and神秘感 (mystery).

## Ground it in the Subject

Mythos is an AI agent with:
- **Audience**: Power users, developers, AI enthusiasts
- **Single job**: Provide a seamless interface for interacting with an AI agent
- **Visual language**: Technical, powerful, slightly futuristic

## Design Principles

### Typography
- Use monospace fonts for code/technical elements
- Use clean sans-serif for UI text
- Establish clear hierarchy: headers, body, captions

### Color Palette
- **Primary**: Deep dark backgrounds (#1a1a2e, #16213e)
- **Accent**: Vibrant tech colors (#0f3460, #533483)
- **Highlight**: Energetic accents (#e94560, #00d9ff)
- **Text**: High contrast whites/grays on dark

### Layout
- Clean, minimal interface
- Clear visual hierarchy
- Responsive to different window sizes
- Consistent spacing and alignment

### Motion
- Subtle animations for state changes
- Loading indicators for API calls
- Smooth transitions between views

## Mythos Desktop Design System

### Color Variables

```css
:root {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --bg-tertiary: #0f3460;
  --accent-primary: #533483;
  --accent-secondary: #e94560;
  --accent-highlight: #00d9ff;
  --text-primary: #ffffff;
  --text-secondary: #b8b8b8;
  --text-muted: #666666;
}
```

### Typography Scale

```css
:root {
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --font-sans: 'Inter', -apple-system, sans-serif;
  
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
}
```

### Component Patterns

#### Chat Interface
```css
.chat-container {
  background: var(--bg-primary);
  border-radius: 8px;
  padding: 16px;
  font-family: var(--font-sans);
}

.message-user {
  background: var(--bg-tertiary);
  border-left: 3px solid var(--accent-primary);
  padding: 12px 16px;
  margin: 8px 0;
}

.message-agent {
  background: var(--bg-secondary);
  border-left: 3px solid var(--accent-highlight);
  padding: 12px 16px;
  margin: 8px 0;
}
```

#### Input Area
```css
.input-container {
  background: var(--bg-secondary);
  border: 1px solid var(--bg-tertiary);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  gap: 8px;
}

.input-field {
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-family: var(--font-mono);
  flex: 1;
}

.input-field:focus {
  outline: none;
  border-bottom: 2px solid var(--accent-highlight);
}
```

#### Status Indicators
```css
.status-connected {
  color: #00ff88;
  font-family: var(--font-mono);
}

.status-disconnected {
  color: var(--accent-secondary);
  font-family: var(--font-mono);
}

.status-loading {
  color: var(--accent-highlight);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

## Process

### 1. Understand Requirements
- What component/view is being built?
- What is its primary function?
- What data does it display?
- What interactions does it support?

### 2. Design System Check
- Does this component exist in the design system?
- Can it be built from existing patterns?
- What new patterns are needed?

### 3. Implementation
- Follow the design system
- Use CSS variables for consistency
- Ensure responsive behavior
- Add subtle animations where appropriate

### 4. Review
- Check against design principles
- Verify visual hierarchy
- Test with different data states
- Ensure accessibility

## Anti-Patterns to Avoid

- **Generic AI look**: Don't use cream backgrounds with terracotta accents
- **Over-animation**: Don't add animation just because you can
- **Inconsistent spacing**: Don't mix padding/margin values randomly
- **Poor contrast**: Don't use low-contrast text colors
- **Broken hierarchy**: Don't make everything look equally important

## Mythos-Specific Considerations

### Terminal Aesthetic
Mythos has CLI roots - consider incorporating terminal aesthetics:
- Monospace fonts for code blocks
- Green/amber text on dark backgrounds
- Command-line style inputs
- Status bars with technical info

### Power User Features
- Keyboard shortcuts
- Quick actions
- Customizable layouts
- Theme switching

### Performance
- Minimize DOM complexity
- Use CSS transforms for animations
- Lazy load non-critical components
- Optimize for smooth scrolling

## Related Skills

- **web-design-guidelines** - For reviewing UI code
- **skill-creator** - For creating design system skills
