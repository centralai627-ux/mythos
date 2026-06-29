"""
Mythos → Obsidian Sync
=======================
Sync Mythos activities, notes, and feed to Obsidian vault.
Creates markdown files that can be viewed in Obsidian app.
"""
from __future__ import annotations
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class ObsidianSync:
    """Sync Mythos data to Obsidian vault."""
    
    def __init__(self, vault_path: Optional[str] = None) -> None:
        self.vault_path = vault_path or self._detect_vault()
        self.sync_folder = "Mythos"
    
    def _detect_vault(self) -> str:
        """Auto-detect Obsidian vault location."""
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, "Documents", "Obsidian"),
            os.path.join(home, "Obsidian"),
            os.path.join(home, "vault"),
        ]
        
        for path in candidates:
            if os.path.isdir(path):
                obsidian_dir = os.path.join(path, ".obsidian")
                if os.path.isdir(obsidian_dir):
                    return path
                for subdir in os.listdir(path):
                    subdir_path = os.path.join(path, subdir)
                    if os.path.isdir(subdir_path):
                        obsidian_dir = os.path.join(subdir_path, ".obsidian")
                        if os.path.isdir(obsidian_dir):
                            return subdir_path
        
        return os.path.join(home, "Documents", "Obsidian", "Mythos")
    
    def set_vault(self, path: str) -> bool:
        """Set vault path manually."""
        if os.path.isdir(path):
            self.vault_path = path
            return True
        return False
    
    def _ensure_folder(self, folder: str) -> str:
        """Ensure folder exists and return full path."""
        full_path = os.path.join(self.vault_path, self.sync_folder, folder)
        os.makedirs(full_path, exist_ok=True)
        return full_path
    
    def sync_feed(self, feed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync Mythos feed to Obsidian."""
        folder = self._ensure_folder("Feed")
        
        # Create index note
        index_path = os.path.join(folder, "Feed Index.md")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("# Mythos Feed\n\n")
            f.write(f"Last synced: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write("## Recent Activities\n\n")
            
            for activity in feed_data[:20]:
                emoji = {"note": "📝", "task": "✅", "achievement": "🏆", "idea": "💡"}.get(activity.get("type", ""), "📌")
                date = activity.get("timestamp", "")[:10]
                f.write(f"- {emoji} **{activity.get('title', 'Untitled')}** ({date})\n")
                if activity.get("content"):
                    f.write(f"  - {activity['content'][:100]}...\n")
            
            f.write(f"\n---\n\n")
            f.write(f"Total: {len(feed_data)} activities\n")
        
        # Create individual notes for each activity
        for activity in feed_data:
            date = activity.get("timestamp", "")[:10]
            title = activity.get("title", "Untitled").replace("/", "-").replace("\\", "-")
            note_path = os.path.join(folder, f"{date} - {title}.md")
            
            with open(note_path, "w", encoding="utf-8") as f:
                f.write(f"---\n")
                f.write(f"type: {activity.get('type', 'note')}\n")
                f.write(f"date: {date}\n")
                f.write(f"tags: [{', '.join(activity.get('tags', []))}]\n")
                f.write(f"---\n\n")
                f.write(f"# {activity.get('title', 'Untitled')}\n\n")
                f.write(f"{activity.get('content', '')}\n\n")
                f.write(f"---\n")
                f.write(f"*Likes: {activity.get('likes', 0)} | Comments: {len(activity.get('comments', []))}*\n")
        
        return {"success": True, "synced": len(feed_data), "folder": folder}
    
    def sync_daily_notes(self, days: int = 7) -> Dict[str, Any]:
        """Sync daily notes to Obsidian."""
        folder = self._ensure_folder("Daily Notes")
        
        synced = 0
        for i in range(days):
            date = (datetime.now() - __import__('datetime').timedelta(days=i)).strftime("%Y-%m-%d")
            note_path = os.path.join(folder, f"{date}.md")
            
            if not os.path.exists(note_path):
                with open(note_path, "w", encoding="utf-8") as f:
                    f.write(f"---\n")
                    f.write(f"date: {date}\n")
                    f.write(f"tags: [daily]\n")
                    f.write(f"---\n\n")
                    f.write(f"# {date}\n\n")
                    f.write(f"## Tasks\n- [ ] \n\n")
                    f.write(f"## Notes\n\n\n")
                    f.write(f"## Links\n")
                synced += 1
        
        return {"success": True, "created": synced, "folder": folder}
    
    def sync_projects(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync projects to Obsidian."""
        folder = self._ensure_folder("Projects")
        
        for project in projects:
            name = project.get("name", "Untitled").replace("/", "-")
            note_path = os.path.join(folder, f"{name}.md")
            
            with open(note_path, "w", encoding="utf-8") as f:
                f.write(f"---\n")
                f.write(f"type: project\n")
                f.write(f"status: {project.get('status', 'active')}\n")
                f.write(f"tags: [{', '.join(project.get('tags', []))}]\n")
                f.write(f"---\n\n")
                f.write(f"# {project.get('name', 'Untitled')}\n\n")
                f.write(f"## Overview\n{project.get('description', '')}\n\n")
                f.write(f"## Tasks\n")
                for task in project.get("tasks", []):
                    status = "x" if task.get("done") else " "
                    f.write(f"- [{status}] {task.get('title', '')}\n")
                f.write(f"\n## Notes\n{project.get('notes', '')}\n")
        
        return {"success": True, "synced": len(projects), "folder": folder}
    
    def create_index(self) -> Dict[str, Any]:
        """Create main index note for Mythos in Obsidian."""
        index_path = os.path.join(self.vault_path, self.sync_folder, "Mythos Index.md")
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"type: index\n")
            f.write(f"tags: [mythos, index]\n")
            f.write(f"---\n\n")
            f.write(f"# Mythos - AI Assistant\n\n")
            f.write(f"Last synced: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(f"## Sections\n\n")
            f.write(f"- [[Feed Index]] - Activity timeline\n")
            f.write(f"- [[Daily Notes]] - Daily journal\n")
            f.write(f"- [[Projects]] - Active projects\n\n")
            f.write(f"## Quick Links\n\n")
            f.write(f"- Open Mythos CLI: `mythos`\n")
            f.write(f"- View feed: `feed_view`\n")
            f.write(f"- Add note: `feed_add`\n")
        
        return {"success": True, "path": index_path}
    
    def full_sync(self, feed_data: List[Dict] = None, projects: List[Dict] = None) -> Dict[str, Any]:
        """Perform full sync to Obsidian."""
        results = {
            "index": self.create_index(),
            "daily_notes": self.sync_daily_notes(),
        }
        
        if feed_data:
            results["feed"] = self.sync_feed(feed_data)
        
        if projects:
            results["projects"] = self.sync_projects(projects)
        
        return results


# Global instance
obsidian_sync = ObsidianSync()
