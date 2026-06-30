---
name: obsidian-memory
description: Use when user wants to sync Mythos memory (conversations, facts, preferences) to Obsidian vault automatically
---

# Mythos Memory → Obsidian Sync

## Overview

Automatically sync Mythos memory to Obsidian vault:
- Conversations history
- Learned facts
- User preferences

## Tools

### 1. Sync Memory
```
obsidian_sync_memory(vault_path="")
```
Sync all memory to Obsidian.

## How It Works

### Auto-Sync on Startup
When Mythos starts, it automatically:
1. Loads memory from database
2. Syncs to Obsidian vault
3. Creates organized notes

### Folder Structure
```
📁 Obsidian Vault/
└── 📁 Mythos/
    └── 📁 Memory/
        ├── 📄 Memory Index.md
        ├── 📁 Conversations/
        │   ├── 📄 2026-06-28 - Session.md
        │   └── 📄 2026-06-27 - Project.md
        ├── 📄 Facts.md
        └── 📄 Preferences.md
```

## What Gets Synced

| Data | Location | Format |
|------|----------|--------|
| Conversations | Memory/Conversations/ | Individual notes |
| Facts | Memory/Facts.md | Bullet list |
| Preferences | Memory/Preferences.md | Key-value pairs |
| Index | Memory/Memory Index.md | Statistics |

## Examples

### Manual sync
```
> Sinkronkan memory ke Obsidian
> Sync memory ke vault
```

### Auto-sync
Memory automatically syncs when Mythos starts.

## Benefits

- 📝 All conversations preserved in Obsidian
- 🧠 Facts and preferences accessible
- 🔍 Search across all memory
- 📊 View statistics
