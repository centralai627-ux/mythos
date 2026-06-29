"""
Mythos Feed & Timeline
======================
Social media-like feed showing recent activities, notes, and interactions.
Inspired by Obsidian's timeline and graph view.
"""
from __future__ import annotations
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


class MythosFeed:
    """Activity feed and timeline for Mythos."""
    
    def __init__(self, storage_path: Optional[str] = None) -> None:
        self.storage_path = storage_path or os.path.join(
            os.path.expanduser("~"), ".mythos", "feed.json"
        )
        self.activities: List[Dict[str, Any]] = []
        self._load()
    
    def _load(self) -> None:
        """Load activities from storage."""
        try:
            if os.path.isfile(self.storage_path):
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.activities = json.load(f)
        except Exception:
            self.activities = []
    
    def _save(self) -> None:
        """Save activities to storage."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.activities, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def add_activity(
        self,
        activity_type: str,
        title: str,
        content: str = "",
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Add a new activity to the feed."""
        activity = {
            "id": len(self.activities) + 1,
            "type": activity_type,
            "title": title,
            "content": content,
            "tags": tags or [],
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "likes": 0,
            "comments": [],
        }
        self.activities.append(activity)
        self._save()
        return activity
    
    def get_feed(
        self,
        limit: int = 20,
        activity_type: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get feed of recent activities."""
        filtered = self.activities
        
        if activity_type:
            filtered = [a for a in filtered if a["type"] == activity_type]
        
        if tag:
            filtered = [a for a in filtered if tag in a.get("tags", [])]
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return filtered[:limit]
    
    def get_timeline(self, days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """Get activities grouped by day."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [a for a in self.activities if a["timestamp"] >= cutoff]
        
        timeline = {}
        for activity in recent:
            date = activity["timestamp"][:10]  # YYYY-MM-DD
            if date not in timeline:
                timeline[date] = []
            timeline[date].append(activity)
        
        return timeline
    
    def search_activities(self, query: str) -> List[Dict[str, Any]]:
        """Search activities by title or content."""
        query_lower = query.lower()
        results = []
        
        for activity in self.activities:
            if (query_lower in activity.get("title", "").lower() or
                query_lower in activity.get("content", "").lower()):
                results.append(activity)
        
        return results
    
    def add_comment(self, activity_id: int, comment: str) -> bool:
        """Add a comment to an activity."""
        for activity in self.activities:
            if activity["id"] == activity_id:
                activity["comments"].append({
                    "text": comment,
                    "timestamp": datetime.now().isoformat(),
                })
                self._save()
                return True
        return False
    
    def like_activity(self, activity_id: int) -> bool:
        """Like an activity."""
        for activity in self.activities:
            if activity["id"] == activity_id:
                activity["likes"] += 1
                self._save()
                return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get feed statistics."""
        if not self.activities:
            return {"total": 0, "today": 0, "this_week": 0}
        
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        today_count = sum(1 for a in self.activities if a["timestamp"].startswith(today))
        week_count = sum(1 for a in self.activities if a["timestamp"] >= week_ago)
        
        type_counts = {}
        for activity in self.activities:
            t = activity["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "total": len(self.activities),
            "today": today_count,
            "this_week": week_count,
            "by_type": type_counts,
        }


class MythosGraph:
    """Graph view for connections between notes and concepts."""
    
    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
    
    def add_node(self, node_id: str, node_type: str = "note", label: str = "", metadata: Dict = None) -> None:
        """Add a node to the graph."""
        self.nodes[node_id] = {
            "id": node_id,
            "type": node_type,
            "label": label or node_id,
            "metadata": metadata or {},
        }
    
    def add_edge(self, source: str, target: str, relationship: str = "links_to") -> None:
        """Add an edge between two nodes."""
        self.edges.append({
            "source": source,
            "target": target,
            "relationship": relationship,
        })
    
    def get_connections(self, node_id: str) -> Dict[str, List[str]]:
        """Get all connections for a node."""
        incoming = []
        outgoing = []
        
        for edge in self.edges:
            if edge["target"] == node_id:
                incoming.append(edge["source"])
            if edge["source"] == node_id:
                outgoing.append(edge["target"])
        
        return {"incoming": incoming, "outgoing": outgoing}
    
    def get_related(self, node_id: str, depth: int = 2) -> List[str]:
        """Get related nodes up to specified depth."""
        visited = set()
        queue = [(node_id, 0)]
        related = []
        
        while queue:
            current, current_depth = queue.pop(0)
            
            if current in visited or current_depth > depth:
                continue
            
            visited.add(current)
            if current != node_id:
                related.append(current)
            
            connections = self.get_connections(current)
            for neighbor in connections["incoming"] + connections["outgoing"]:
                if neighbor not in visited:
                    queue.append((neighbor, current_depth + 1))
        
        return related
    
    def to_json(self) -> Dict[str, Any]:
        """Export graph as JSON."""
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
        }


# Global instances
feed = MythosFeed()
graph = MythosGraph()
