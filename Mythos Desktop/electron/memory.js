const initSqlJs = require('sql.js');
const path = require('path');
const os = require('os');
const fs = require('fs');

const DB_DIR = path.join(os.homedir(), '.mythos');
const DB_PATH = path.join(DB_DIR, 'memory.db');

// Ensure directory exists
if (!fs.existsSync(DB_DIR)) {
  fs.mkdirSync(DB_DIR, { recursive: true });
}

let db;
let SQL;

async function getDB() {
  if (!db) {
    SQL = await initSqlJs();
    
    // Load existing database or create new
    if (fs.existsSync(DB_PATH)) {
      const buffer = fs.readFileSync(DB_PATH);
      db = new SQL.Database(buffer);
    } else {
      db = new SQL.Database();
    }
    
    initTables();
  }
  return db;
}

function saveDB() {
  if (db) {
    const data = db.export();
    const buffer = Buffer.from(data);
    fs.writeFileSync(DB_PATH, buffer);
  }
}

function initTables() {
  db.run(`
    CREATE TABLE IF NOT EXISTS conversations (
      id TEXT PRIMARY KEY,
      title TEXT,
      model TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      conversation_id TEXT,
      role TEXT,
      content TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    );

    CREATE TABLE IF NOT EXISTS preferences (
      key TEXT PRIMARY KEY,
      value TEXT,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS facts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      content TEXT,
      source TEXT,
      confidence REAL DEFAULT 1.0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
  `);
  saveDB();
}

// --- Conversation Management ---
async function createConversation(title = 'New Chat', model = 'mythos-auto') {
  const database = await getDB();
  const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  database.run('INSERT INTO conversations (id, title, model) VALUES (?, ?, ?)', [id, title, model]);
  saveDB();
  return id;
}

async function updateConversation(id, updates) {
  const database = await getDB();
  const sets = [];
  const values = [];
  for (const [key, value] of Object.entries(updates)) {
    sets.push(`${key} = ?`);
    values.push(value);
  }
  sets.push('updated_at = CURRENT_TIMESTAMP');
  values.push(id);
  database.run(`UPDATE conversations SET ${sets.join(', ')} WHERE id = ?`, values);
  saveDB();
}

async function getConversations(limit = 50) {
  const database = await getDB();
  const results = database.exec('SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?', [limit]);
  return results.length > 0 ? results[0].values.map(row => {
    const obj = {};
    results[0].columns.forEach((col, i) => obj[col] = row[i]);
    return obj;
  }) : [];
}

async function getConversation(id) {
  const database = await getDB();
  const results = database.exec('SELECT * FROM conversations WHERE id = ?', [id]);
  if (results.length > 0 && results[0].values.length > 0) {
    const obj = {};
    results[0].columns.forEach((col, i) => obj[col] = results[0].values[0][i]);
    return obj;
  }
  return null;
}

async function deleteConversation(id) {
  const database = await getDB();
  database.run('DELETE FROM messages WHERE conversation_id = ?', [id]);
  database.run('DELETE FROM conversations WHERE id = ?', [id]);
  saveDB();
}

// --- Message Management ---
async function addMessage(conversationId, role, content) {
  const database = await getDB();
  database.run('INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)', [conversationId, role, content]);
  database.run('UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', [conversationId]);
  saveDB();
}

async function getMessages(conversationId, limit = 50) {
  const database = await getDB();
  const results = database.exec('SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT ?', [conversationId, limit]);
  if (results.length > 0) {
    return results[0].values.map(row => {
      const obj = {};
      results[0].columns.forEach((col, i) => obj[col] = row[i]);
      return obj;
    }).reverse();
  }
  return [];
}

async function searchMessages(query, limit = 20) {
  const database = await getDB();
  const results = database.exec(
    'SELECT m.*, c.title as conversation_title FROM messages m JOIN conversations c ON m.conversation_id = c.id WHERE m.content LIKE ? ORDER BY m.created_at DESC LIMIT ?',
    [`%${query}%`, limit]
  );
  if (results.length > 0) {
    return results[0].values.map(row => {
      const obj = {};
      results[0].columns.forEach((col, i) => obj[col] = row[i]);
      return obj;
    });
  }
  return [];
}

// --- Preferences ---
async function setPreference(key, value) {
  const database = await getDB();
  database.run('INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)', [key, value]);
  saveDB();
}

async function getPreference(key, defaultValue = null) {
  const database = await getDB();
  const results = database.exec('SELECT value FROM preferences WHERE key = ?', [key]);
  if (results.length > 0 && results[0].values.length > 0) {
    return results[0].values[0][0];
  }
  return defaultValue;
}

async function getAllPreferences() {
  const database = await getDB();
  const results = database.exec('SELECT * FROM preferences');
  if (results.length > 0) {
    return results[0].values.map(row => {
      const obj = {};
      results[0].columns.forEach((col, i) => obj[col] = row[i]);
      return obj;
    });
  }
  return [];
}

// --- Facts ---
async function addFact(content, source = 'user') {
  const database = await getDB();
  database.run('INSERT INTO facts (content, source) VALUES (?, ?)', [content, source]);
  saveDB();
}

async function searchFacts(query, limit = 10) {
  const database = await getDB();
  const results = database.exec('SELECT * FROM facts WHERE content LIKE ? ORDER BY confidence DESC LIMIT ?', [`%${query}%`, limit]);
  if (results.length > 0) {
    return results[0].values.map(row => {
      const obj = {};
      results[0].columns.forEach((col, i) => obj[col] = row[i]);
      return obj;
    });
  }
  return [];
}

async function getFactsContext(query) {
  const facts = await searchFacts(query, 5);
  if (facts.length === 0) return '';
  return facts.map(f => f.content).join('\n');
}

// --- Context Building ---
async function buildContext(conversationId, userMessage) {
  const messages = await getMessages(conversationId, 20);
  const facts = await searchFacts(userMessage, 3);
  const factsContext = facts.length > 0 ? '\n\nKnown facts:\n' + facts.map(f => `- ${f.content}`).join('\n') : '';
  const model = await getPreference('preferred_model', 'mythos-auto');
  const language = await getPreference('preferred_language', 'id');

  return {
    messages,
    factsContext,
    model,
    language
  };
}

// --- Settings Persistence ---
async function saveSettings(settings) {
  for (const [key, value] of Object.entries(settings)) {
    await setPreference(`setting_${key}`, JSON.stringify(value));
  }
}

async function loadSettings() {
  const settings = {};
  const database = await getDB();
  const results = database.exec("SELECT key, value FROM preferences WHERE key LIKE 'setting_%'");
  if (results.length > 0) {
    for (const row of results[0].values) {
      const key = row[0].replace('setting_', '');
      try {
        settings[key] = JSON.parse(row[1]);
      } catch {
        settings[key] = row[1];
      }
    }
  }
  return settings;
}

// --- Export/Import ---
async function exportConversations(filePath) {
  const conversations = await getConversations(1000);
  const data = [];
  for (const conv of conversations) {
    data.push({
      ...conv,
      messages: await getMessages(conv.id, 1000)
    });
  }
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
  return { success: true, count: data.length };
}

async function importConversations(filePath) {
  const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  const database = await getDB();
  let count = 0;
  for (const conv of data) {
    database.run('INSERT OR REPLACE INTO conversations (id, title, model, created_at, updated_at) VALUES (?, ?, ?, ?, ?)', [conv.id, conv.title, conv.model, conv.created_at, conv.updated_at]);
    for (const msg of conv.messages || []) {
      database.run('INSERT OR IGNORE INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)', [msg.id, msg.conversation_id, msg.role, msg.content, msg.created_at]);
    }
    count++;
  }
  saveDB();
  return { success: true, count };
}

// --- Cleanup ---
function close() {
  if (db) {
    saveDB();
    db.close();
    db = null;
  }
}

process.on('exit', close);

module.exports = {
  createConversation,
  updateConversation,
  getConversations,
  getConversation,
  deleteConversation,
  addMessage,
  getMessages,
  searchMessages,
  setPreference,
  getPreference,
  getAllPreferences,
  addFact,
  searchFacts,
  getFactsContext,
  buildContext,
  saveSettings,
  loadSettings,
  exportConversations,
  importConversations,
  close
};
