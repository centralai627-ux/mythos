---
name: feed
description: Use when user wants to view, add, or search activities in Mythos feed (like social media timeline)
---

# Mythos Feed - Activity Timeline

## Overview

Social media-like feed showing recent activities, notes, achievements, and ideas.
Like Twitter/Weibo/WeChat Moments but for your Mythos activities.

## Tools

### 1. Add Activity
```
feed_add(type="note", title="My Idea", content="Details...", tags="ai,project")
```
Types: note, task, achievement, idea

### 2. View Feed
```
feed_view(limit=10, type="")
```
Show recent activities.

### 3. Search Feed
```
feed_search(query="quantum")
```
Search activities by title or content.

### 4. Get Stats
```
feed_stats()
```
Get statistics about your activities.

## Examples

### Add a note
```
> Tambahkan catatan: "Ide baru untuk project AI" dengan tag ai,project
```

### View recent activities
```
> Lihat feed terbaru
> Tampilkan 10 aktivitas terakhir
```

### Search
```
> Cari "quantum" di feed
```

### Get stats
```
> Berapa total aktivitas saya?
```

## Activity Types

| Type | Emoji | Use Case |
|------|-------|----------|
| note | 📝 | General notes |
| task | ✅ | Completed tasks |
| achievement | 🏆 | Achievements |
| idea | 💡 | New ideas |

## Integration with Obsidian

Activities can be linked to Obsidian notes:
```
> Buat catatan di feed tentang note Obsidian yang baru dibaca
```
