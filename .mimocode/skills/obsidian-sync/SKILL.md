---
name: obsidian-sync
description: Use when user wants to sync Mythos data (feed, notes, projects) to Obsidian vault for viewing in Obsidian app
---

# Mythos → Obsidian Sync

## Overview

Sync all Mythos data to Obsidian vault so you can view it in Obsidian app.

## Tools

### 1. Full Sync
```
obsidian_sync(vault_path="")
```
Sync everything: feed, daily notes, projects.

### 2. Sync Feed Only
```
obsidian_sync_feed(vault_path="")
```
Sync only feed activities.

## Examples

### Sync everything
```
> Sync semua data ke Obsidian
> Sinkronkan Mythos ke Obsidian
```

### Sync with custom vault path
```
> Sync ke Obsidian di C:\Users\Kamu\Documents\MyVault
```

### Sync feed only
```
> Sync feed saja ke Obsidian
```

## What Gets Synced

| Data | Location in Obsidian |
|------|---------------------|
| Feed activities | Mythos/Feed/ |
| Daily notes | Mythos/Daily Notes/ |
| Projects | Mythos/Projects/ |
| Index | Mythos/Mythos Index.md |

## After Sync

1. Open Obsidian app
2. Open your vault
3. Navigate to "Mythos" folder
4. View all your activities!

## Auto-Sync

You can set up auto-sync by running `obsidian_sync` periodically or after important actions.
