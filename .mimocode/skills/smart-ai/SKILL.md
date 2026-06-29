---
name: smart-ai
description: Use when user wants to improve AI responses, check confidence, validate output, or learn from mistakes
---

# Smart AI System

## Overview

Makes Mythos AI smarter and more reliable with:
- Self-reflection and critique
- Confidence scoring
- Error recovery
- Knowledge validation
- Learning from mistakes

## Tools

### 1. Self-Reflection
```
smart_reflect(question="...", response="...")
```
AI critiques its own response and suggests improvements.

### 2. Confidence Score
```
smart_confidence(question="...", response="...")
```
Calculate confidence score (0-100%) for a response.

### 3. Validate Output
```
smart_validate(output="...", type="text|code|json")
```
Validate AI output before showing to user.

### 4. Stats
```
smart_stats()
```
Get Smart AI statistics.

## Examples

### Check response quality
```
> Cek kualitas jawaban saya tentang quantum computing
```

### Get confidence score
```
> Berapa confidence score jawaban ini?
```

### Validate JSON output
```
> Validasi output JSON ini
```

## How It Works

### Self-Reflection
- Checks for hedging language ("maybe", "perhaps")
- Detects incomplete responses
- Identifies missing actions for do-requests
- Suggests improvements

### Confidence Scoring
- Question clarity (short = lower confidence)
- Response completeness (detailed = higher)
- Tool usage (tools = more reliable)
- Past mistakes (similar errors = lower)

### Learning
- Records mistakes for future reference
- Learns from successful interactions
- Improves over time

## Anti-Fail Features

| Feature | Description |
|---------|-------------|
| Self-critique | AI checks own responses |
| Confidence score | Rate reliability 0-100% |
| Error recovery | Auto-retry with different approach |
| Validation | Check output before showing |
| Learning | Remember past mistakes |
