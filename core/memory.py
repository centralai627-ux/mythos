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


def get_messages(conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        'SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT ?',
        (conversation_id, limit)
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def search_messages(query: str, limit: int = 20) -> List[Dict[str, Any]]:
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


def search_facts(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        'SELECT * FROM facts WHERE content LIKE ? ORDER BY confidence DESC LIMIT ?',
        (f'%{query}%', limit)
    ).fetchall()
    return [dict(r) for r in rows]


def get_facts_context(query: str) -> str:
    facts = search_facts(query, 5)
    if not facts:
        return ''
    return '\n'.join(f'- {f["content"]}' for f in facts)


# --- Context Building ---
def build_context(conversation_id: str, user_message: str) -> Dict[str, Any]:
    messages = get_messages(conversation_id, 20)
    facts = search_facts(user_message, 3)
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


def close():
    global _connection
    if _connection:
        _connection.close()
        _connection = None
