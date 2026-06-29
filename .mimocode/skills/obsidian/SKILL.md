---
name: obsidian
description: Use when user wants to read, write, search, or manage notes in Obsidian vault as a second brain
---

# Obsidian Integration for Mythos

## Overview

Connect Mythos with Obsidian vault as a second brain. Read, write, search, and manage notes.

## Quick Start

```
> Set my Obsidian vault to C:\Users\Me\Documents\MyVault
> List notes in my vault
> Read my note about project ideas
> Create a note about AI research
> Search for "quantum" in my notes
```

## Tools

### 1. Set Vault Path
```
obsidian_set_vault(path="C:\Users\Me\Documents\MyVault")
```
Call this first before using other Obsidian tools.

### 2. List Notes
```
obsidian_list_notes(folder="", recursive=true)
```
List all notes in vault or specific folder.

### 3. Read Note
```
obsidian_read_note(note_path="notes/my-note.md")
```
Read a note from vault.

### 4. Write Note
```
obsidian_write_note(
  note_path="notes/new-note.md",
  content="# My Note\n\nContent here...",
  tags="research,ai"
)
```
Create or update a note.

### 5. Search Notes
```
obsidian_search(query="quantum computing", folder="")
```
Search notes by content.

### 6. Daily Note
```
obsidian_daily_note(content="## Tasks\n- [ ] Task 1")
```
Create today's daily note.

### 7. Link Notes
```
obsidian_link_notes(source="notes/project.md", target="Research")
```
Add a link from one note to another.

## Examples

### Create a research note
```
> Create note "AI Research" with tags "ai,research" about quantum computing
```

### Search and summarize
```
> Search my notes for "machine learning" and summarize findings
```

### Daily journal
```
> Create daily note with tasks: finish report, review code
```

## Workflow

1. **First time**: Set vault path
2. **Read**: Browse or search existing notes
3. **Write**: Create new notes with frontmatter
4. **Link**: Connect related notes with [[]]
5. **Search**: Find information across vault

## Obsidian Features Supported

- Markdown notes
- Frontmatter (YAML)
- Wiki links [[]]
- Tags
- Folders
- Daily notes
- Search
