---
name: voice
description: Use when user wants Mythos to speak text aloud using voice synthesis or convert text to speech
---

# Mythos Voice - Text-to-Speech

## Overview

Mythos can speak text aloud using Xiaomi MiMo TTS (Text-to-Speech) models.

## Tools

### 1. Speak Text
```
voice_speak(text="Hello, I am Mythos!", voice="default", speed=1.0)
```

## Examples

### Speak a response
```
> Bacakan hasilnya dengan suara
> Speak the answer aloud
```

### Speak with different speed
```
> Bacakan lebih cepat
> Speak faster (speed=1.5)
```

## Voices Available

| Voice | Description |
|-------|-------------|
| default | Standard voice |
| male | Male voice |
| female | Female voice |

## Speed Options

| Speed | Description |
|-------|-------------|
| 0.5 | Very slow |
| 0.75 | Slow |
| 1.0 | Normal (default) |
| 1.25 | Fast |
| 1.5 | Very fast |
| 2.0 | Extremely fast |

## Integration with MiMo

Voice is powered by Xiaomi MiMo TTS:
- Model: mimo-v2.5-tts
- High quality synthesis
- Multiple languages supported
- Natural sounding voice
