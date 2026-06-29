"""
Mythos Obsidian Integration
============================
Connect Mythos with Obsidian vault as a second brain.
Allows reading, writing, searching, and managing Obsidian notes.
"""
from __future__ import annotations
import os
import re
import json
import glob
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime


class ObsidianVault:
    """Obsidian vault manager for Mythos integration."""
    
    def __init__(self, vault_path: Optional[str] = None) -> None:
        self.vault_path = vault_path or self._detect_vault()
        self._cache: Dict[str, str] = {}
    
    def _detect_vault(self) -> str:
        """Auto-detect Obsidian vault location."""
        # Common Obsidian vault locations
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, "Documents", "Obsidian"),
            os.path.join(home, "Obsidian"),
            os.path.join(home, "vault"),
            os.path.join(home, "notes"),
        ]
        
        for path in candidates:
            if os.path.isdir(path):
                # Check if it's an Obsidian vault (has .obsidian folder)
                obsidian_dir = os.path.join(path, ".obsidian")
                if os.path.isdir(obsidian_dir):
                    return path
                # Check subdirectories for vaults
                for subdir in os.listdir(path):
                    subdir_path = os.path.join(path, subdir)
                    if os.path.isdir(subdir_path):
                        obsidian_dir = os.path.join(subdir_path, ".obsidian")
                        if os.path.isdir(obsidian_dir):
                            return subdir_path
        
        # Default fallback
        return os.path.join(home, "Documents", "Obsidian", "Mythos")
    
    def set_vault(self, path: str) -> bool:
        """Set vault path manually."""
        if os.path.isdir(path):
            self.vault_path = path
            return True
        return False
    
    def get_vault_info(self) -> Dict[str, Any]:
        """Get vault information."""
        if not os.path.isdir(self.vault_path):
            return {"error": "Vault not found", "path": self.vault_path}
        
        notes = self.list_notes()
        folders = self.list_folders()
        
        return {
            "path": self.vault_path,
            "notes_count": len(notes),
            "folders_count": len(folders),
            "folders": folders[:10],  # First 10 folders
            "recent_notes": notes[:10],  # First 10 notes
        }
    
    def list_notes(self, folder: str = "", recursive: bool = True) -> List[Dict[str, Any]]:
        """List all markdown notes in vault."""
        search_path = os.path.join(self.vault_path, folder) if folder else self.vault_path
        
        if not os.path.isdir(search_path):
            return []
        
        notes = []
        pattern = os.path.join(search_path, "**/*.md") if recursive else os.path.join(search_path, "*.md")
        
        for filepath in glob.glob(pattern, recursive=recursive):
            rel_path = os.path.relpath(filepath, self.vault_path)
            stat = os.stat(filepath)
            
            # Read first few lines for preview
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(500)
            except Exception:
                content = ""
            
            notes.append({
                "path": rel_path,
                "name": os.path.basename(filepath),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "preview": content[:200].replace("\n", " "),
            })
        
        # Sort by modification time (newest first)
        notes.sort(key=lambda x: x["modified"], reverse=True)
        return notes
    
    def list_folders(self) -> List[str]:
        """List all folders in vault."""
        folders = []
        
        for root, dirs, files in os.walk(self.vault_path):
            # Skip .obsidian folder
            if ".obsidian" in root:
                continue
            
            rel_path = os.path.relpath(root, self.vault_path)
            if rel_path != ".":
                folders.append(rel_path)
        
        return sorted(folders)
    
    def read_note(self, note_path: str) -> Dict[str, Any]:
        """Read a note from vault."""
        full_path = os.path.join(self.vault_path, note_path)
        
        if not os.path.isfile(full_path):
            # Try adding .md extension
            if not note_path.endswith(".md"):
                full_path = full_path + ".md"
        
        if not os.path.isfile(full_path):
            return {"error": f"Note not found: {note_path}"}
        
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            # Parse frontmatter if exists
            frontmatter = {}
            if content.startswith("---"):
                end_idx = content.find("---", 3)
                if end_idx != -1:
                    fm_text = content[3:end_idx].strip()
                    for line in fm_text.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            frontmatter[key.strip()] = value.strip()
                    content = content[end_idx + 3:].strip()
            
            return {
                "path": note_path,
                "content": content,
                "frontmatter": frontmatter,
                "size": len(content),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def write_note(self, note_path: str, content: str, frontmatter: Optional[Dict] = None) -> Dict[str, Any]:
        """Write a note to vault."""
        full_path = os.path.join(self.vault_path, note_path)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Add .md extension if missing
        if not full_path.endswith(".md"):
            full_path = full_path + ".md"
        
        # Build content with frontmatter
        full_content = ""
        if frontmatter:
            full_content = "---\n"
            for key, value in frontmatter.items():
                full_content += f"{key}: {value}\n"
            full_content += "---\n\n"
        
        full_content += content
        
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(full_content)
            
            return {
                "success": True,
                "path": note_path,
                "size": len(full_content),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def search_notes(self, query: str, folder: str = "") -> List[Dict[str, Any]]:
        """Search notes by content or title."""
        search_path = os.path.join(self.vault_path, folder) if folder else self.vault_path
        
        if not os.path.isdir(search_path):
            return []
        
        results = []
        query_lower = query.lower()
        
        for filepath in glob.glob(os.path.join(search_path, "**/*.md"), recursive=True):
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                
                # Search in content
                if query_lower in content.lower():
                    rel_path = os.path.relpath(filepath, self.vault_path)
                    
                    # Find matching lines
                    matches = []
                    for i, line in enumerate(content.split("\n")):
                        if query_lower in line.lower():
                            matches.append({
                                "line": i + 1,
                                "text": line.strip()[:100],
                            })
                    
                    results.append({
                        "path": rel_path,
                        "name": os.path.basename(filepath),
                        "matches": len(matches),
                        "preview": matches[0]["text"] if matches else "",
                    })
            except Exception:
                continue
        
        # Sort by number of matches
        results.sort(key=lambda x: x["matches"], reverse=True)
        return results[:20]  # Top 20 results
    
    def create_daily_note(self, content: str = "") -> Dict[str, Any]:
        """Create a daily note in Obsidian format."""
        today = datetime.now().strftime("%Y-%m-%d")
        note_path = f"Daily Notes/{today}.md"
        
        frontmatter = {
            "date": today,
            "tags": "daily",
            "created": datetime.now().isoformat(),
        }
        
        if not content:
            content = f"# {today}\n\n## Tasks\n- [ ] \n\n## Notes\n\n\n## Links\n"
        
        return self.write_note(note_path, content, frontmatter)
    
    def create_note_from_template(self, template: str, title: str, variables: Dict[str, str] = {}) -> Dict[str, Any]:
        """Create a note from a template."""
        # Read template if it exists
        template_path = f"Templates/{template}.md"
        template_content = self.read_note(template_path)
        
        if "error" in template_content:
            # Use default template
            content = f"# {title}\n\n## Overview\n\n## Content\n\n## Links\n"
        else:
            content = template_content["content"]
        
        # Replace variables
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", value)
        
        # Replace common variables
        content = content.replace("{{title}}", title)
        content = content.replace("{{date}}", datetime.now().strftime("%Y-%m-%d"))
        content = content.replace("{{time}}", datetime.now().strftime("%H:%M"))
        
        # Create note
        note_path = f"{title}.md"
        frontmatter = {
            "title": title,
            "created": datetime.now().isoformat(),
            "template": template,
        }
        
        return self.write_note(note_path, content, frontmatter)
    
    def link_notes(self, source: str, target: str) -> Dict[str, Any]:
        """Add a link from source note to target note."""
        source_note = self.read_note(source)
        if "error" in source_note:
            return source_note
        
        # Add link at the end
        link = f"\n\n[[{target}]]"
        new_content = source_note["content"] + link
        
        return self.write_note(source, new_content)
    
    def get_backlinks(self, note_name: str) -> List[str]:
        """Find all notes that link to this note."""
        backlinks = []
        search_term = f"[[{note_name}]]"
        
        for filepath in glob.glob(os.path.join(self.vault_path, "**/*.md"), recursive=True):
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                
                if search_term in content:
                    rel_path = os.path.relpath(filepath, self.vault_path)
                    backlinks.append(rel_path)
            except Exception:
                continue
        
        return backlinks
    
    def export_to_json(self, output_path: str) -> Dict[str, Any]:
        """Export vault structure to JSON."""
        notes = self.list_notes()
        
        export = {
            "vault": self.vault_path,
            "exported": datetime.now().isoformat(),
            "notes_count": len(notes),
            "notes": [],
        }
        
        for note in notes[:100]:  # Limit to 100 notes
            note_content = self.read_note(note["path"])
            if "error" not in note_content:
                export["notes"].append({
                    "path": note["path"],
                    "content": note_content["content"][:1000],  # Limit content
                    "frontmatter": note_content.get("frontmatter", {}),
                })
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export, f, indent=2, ensure_ascii=False)
            return {"success": True, "path": output_path, "notes": len(export["notes"])}
        except Exception as e:
            return {"error": str(e)}


# Global instance
obsidian = ObsidianVault()
