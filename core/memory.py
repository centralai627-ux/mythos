"""
Mythos Memory System
====================
Persistent memory for CLI using SQLite.
"""
from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

# Database location
DB_DIR = Path.home() / '.mythos'
DB_PATH = DB_DIR / 'memory.db'

# Ensure directory exists
DB_DIR.mkdir(parents=True, exist_ok=True)

_connection: Optional[sqlite3.Connection] = None


def get_db() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(str(DB_PATH))
        _connection.row_factory = sqlite3.Row
        _init_tables()
    return _connection


def _init_tables():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );

        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            source TEXT,
            confidence REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    db.commit()


# --- Conversation Management ---
def create_conversation(title: str = 'New Chat', model: str = 'mythos-code') -> str:
    import time
    import random
    db = get_db()
    conv_id = str(int(time.time() * 1000)) + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    db.execute('INSERT INTO conversations (id, title, model) VALUES (?, ?, ?)', (conv_id, title, model))
    db.commit()
    return conv_id


def get_conversations(limit: int = 50) -> List[Dict[str, Any]]:
    db = get_db()
    rows = db.execute('SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?', (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_conversation(conv_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    row = db.execute('SELECT * FROM conversations WHERE id = ?', (conv_id,)).fetchone()
    return dict(row) if row else None


def delete_conversation(conv_id: str):
    db = get_db()
    db.execute('DELETE FROM messages WHERE conversation_id = ?', (conv_id,))
    db.execute('DELETE FROM conversations WHERE id = ?', (conv_id,))
    db.commit()


# --- Message Management ---
def add_message(conversation_id: str, role: str, content: str):
    db = get_db()
    db.execute('INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)',
               (conversation_id, role, content))
    db.execute('UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (conversation_id,))
    db.commit()


def get_messages(conversation_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get messages from conversation. Default limit increased to 100."""
    db = get_db()
    rows = db.execute(
        'SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT ?',
        (conversation_id, limit)
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def search_messages(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Search messages. Default limit increased to 50."""
    db = get_db()
    rows = db.execute(
        '''SELECT m.*, c.title as conversation_title 
           FROM messages m JOIN conversations c ON m.conversation_id = c.id 
           WHERE m.content LIKE ? ORDER BY m.created_at DESC LIMIT ?''',
        (f'%{query}%', limit)
    ).fetchall()
    return [dict(r) for r in rows]


# --- Preferences ---
def set_preference(key: str, value: str):
    db = get_db()
    db.execute('INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
               (key, value))
    db.commit()


def get_preference(key: str, default: str = '') -> str:
    db = get_db()
    row = db.execute('SELECT value FROM preferences WHERE key = ?', (key,)).fetchone()
    return row['value'] if row else default


def get_all_preferences() -> Dict[str, str]:
    db = get_db()
    rows = db.execute('SELECT key, value FROM preferences').fetchall()
    return {r['key']: r['value'] for r in rows}


# --- Facts ---
def add_fact(content: str, source: str = 'user'):
    db = get_db()
    db.execute('INSERT INTO facts (content, source) VALUES (?, ?)', (content, source))
    db.commit()


def search_facts(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search facts. Default limit increased to 20."""
    db = get_db()
    rows = db.execute(
        'SELECT * FROM facts WHERE content LIKE ? ORDER BY confidence DESC LIMIT ?',
        (f'%{query}%', limit)
    ).fetchall()
    return [dict(r) for r in rows]


def get_facts_context(query: str) -> str:
    """Get facts context for AI. Returns up to 10 most relevant facts."""
    facts = search_facts(query, 10)
    if not facts:
        return ''
    return '\n'.join(f'- {f["content"]}' for f in facts)


def get_all_facts(limit: int = 50) -> List[Dict[str, Any]]:
    """Get all facts from memory."""
    db = get_db()
    rows = db.execute(
        'SELECT * FROM facts ORDER BY created_at DESC LIMIT ?',
        (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


# --- Context Building ---
def build_context(conversation_id: str, user_message: str) -> Dict[str, Any]:
    """Build context for AI with messages, facts, and preferences."""
    messages = get_messages(conversation_id, 50)  # Increased from 20
    facts = search_facts(user_message, 10)  # Increased from 3
    model = get_preference('preferred_model', 'mythos-code')
    language = get_preference('preferred_language', 'id')

    return {
        'messages': messages,
        'facts': facts,
        'facts_context': get_facts_context(user_message),
        'model': model,
        'language': language
    }


# --- Settings ---
def save_settings(settings: Dict[str, Any]):
    for key, value in settings.items():
        set_preference(f'setting_{key}', str(value))


def load_settings() -> Dict[str, Any]:
    settings = {}
    db = get_db()
    rows = db.execute("SELECT key, value FROM preferences WHERE key LIKE 'setting_%'").fetchall()
    for row in rows:
        key = row['key'].replace('setting_', '')
        try:
            settings[key] = json.loads(row['value'])
        except:
            settings[key] = row['value']
    return settings


# --- Export/Import ---
def export_conversations(file_path: str):
    conversations = get_conversations(1000)
    data = []
    for conv in conversations:
        data.append({
            **conv,
            'messages': get_messages(conv['id'], 1000)
        })
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return {'success': True, 'count': len(data)}


def import_conversations(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    db = get_db()
    count = 0
    for conv in data:
        db.execute(
            'INSERT OR REPLACE INTO conversations (id, title, model, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
            (conv['id'], conv['title'], conv['model'], conv['created_at'], conv['updated_at'])
        )
        for msg in conv.get('messages', []):
            db.execute(
                'INSERT OR IGNORE INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)',
                (msg['id'], msg['conversation_id'], msg['role'], msg['content'], msg['created_at'])
            )
        count += 1
    db.commit()
    return {'success': True, 'count': count}


# --- Obsidian Auto-Sync ---
def sync_memory_to_obsidian(vault_path: str = None) -> Dict[str, Any]:
    """Sync memory (conversations, facts, preferences) to Obsidian vault."""
    import os
    from datetime import datetime
    
    # Detect vault path
    if not vault_path:
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, "Documents", "Obsidian Vault"),
            os.path.join(home, "Documents", "Obsidian"),
            os.path.join(home, "Obsidian"),
        ]
        for path in candidates:
            if os.path.isdir(path):
                obsidian_dir = os.path.join(path, ".obsidian")
                if os.path.isdir(obsidian_dir):
                    vault_path = path
                    break
        if not vault_path:
            vault_path = os.path.join(home, "Documents", "Obsidian Vault")
    
    # Create Mythos Memory folder
    memory_folder = os.path.join(vault_path, "Mythos", "Memory")
    os.makedirs(memory_folder, exist_ok=True)
    
    synced = {
        "conversations": 0,
        "facts": 0,
        "preferences": 0,
    }
    
    # Sync conversations
    conversations = get_conversations(20)
    conv_folder = os.path.join(memory_folder, "Conversations")
    os.makedirs(conv_folder, exist_ok=True)
    
    for conv in conversations:
        conv_id = conv["id"]
        title = conv.get("title", "Untitled").replace("/", "-").replace("\\", "-")
        date = conv.get("created_at", "")[:10]
        
        # Get messages
        messages = get_messages(conv_id, 50)
        
        # Write to Obsidian
        note_path = os.path.join(conv_folder, f"{date} - {title}.md")
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"type: conversation\n")
            f.write(f"date: {date}\n")
            f.write(f"model: {conv.get('model', 'unknown')}\n")
            f.write(f"tags: [mythos, conversation]\n")
            f.write(f"---\n\n")
            f.write(f"# {title}\n\n")
            f.write(f"**Date**: {date}\n")
            f.write(f"**Model**: {conv.get('model', 'unknown')}\n\n")
            f.write(f"## Messages\n\n")
            
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                emoji = "👤" if role == "user" else "🤖" if role == "assistant" else "⚙️"
                f.write(f"### {emoji} {role.capitalize()}\n\n")
                f.write(f"{content[:500]}{'...' if len(content) > 500 else ''}\n\n")
        
        synced["conversations"] += 1
    
    # Sync facts
    facts = get_all_facts(50)
    if facts:
        facts_path = os.path.join(memory_folder, "Facts.md")
        with open(facts_path, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"type: facts\n")
            f.write(f"tags: [mythos, facts, memory]\n")
            f.write(f"---\n\n")
            f.write(f"# Mythos Memory - Facts\n\n")
            f.write(f"Last synced: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            
            for fact in facts:
                f.write(f"- {fact.get('content', '')}\n")
                synced["facts"] += 1
    
    # Sync preferences
    preferences = get_all_preferences()
    if preferences:
        prefs_path = os.path.join(memory_folder, "Preferences.md")
        with open(prefs_path, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"type: preferences\n")
            f.write(f"tags: [mythos, preferences, settings]\n")
            f.write(f"---\n\n")
            f.write(f"# Mythos Preferences\n\n")
            f.write(f"Last synced: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            
            for key, value in preferences.items():
                f.write(f"- **{key}**: {value}\n")
                synced["preferences"] += 1
    
    # Create index
    index_path = os.path.join(memory_folder, "Memory Index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(f"---\n")
        f.write(f"type: index\n")
        f.write(f"tags: [mythos, memory, index]\n")
        f.write(f"---\n\n")
        f.write(f"# Mythos Memory Index\n\n")
        f.write(f"Last synced: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"## Statistics\n\n")
        f.write(f"- Conversations: {synced['conversations']}\n")
        f.write(f"- Facts: {synced['facts']}\n")
        f.write(f"- Preferences: {synced['preferences']}\n\n")
        f.write(f"## Folders\n\n")
        f.write(f"- [[Conversations]] - Chat history\n")
        f.write(f"- [[Facts]] - Learned facts\n")
        f.write(f"- [[Preferences]] - User preferences\n")
    
    return {
        "success": True,
        "vault": vault_path,
        "synced": synced,
    }


def close():
    global _connection
    if _connection:
        _connection.close()
        _connection = None
