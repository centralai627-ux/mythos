const path = require('path');
const os = require('os');
const fs = require('fs');

const DB_DIR = path.join(os.homedir(), '.mythos');
const DB_PATH = path.join(DB_DIR, 'memory.json');

// Ensure directory exists
if (!fs.existsSync(DB_DIR)) {
  fs.mkdirSync(DB_DIR, { recursive: true });
}

// Load or initialize database
function loadDB() {
  if (fs.existsSync(DB_PATH)) {
    try {
      return JSON.parse(fs.readFileSync(DB_PATH, 'utf-8'));
    } catch (e) {
      console.error('Failed to load memory database:', e);
    }
  }
  return {
    conversations: [],
    messages: [],
    preferences: [],
    facts: []
  };
}

function saveDB(db) {
  try {
    fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2));
  } catch (e) {
    console.error('Failed to save memory database:', e);
  }
}

let db = loadDB();

// --- Conversation Management ---
function createConversation(title = 'New Chat', model = 'mythos-auto') {
  const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  const conv = {
    id,
    title,
    model,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
  db.conversations.push(conv);
  saveDB(db);
  return id;
}

function updateConversation(id, updates) {
  const conv = db.conversations.find(c => c.id === id);
  if (conv) {
    Object.assign(conv, updates, { updated_at: new Date().toISOString() });
    saveDB(db);
  }
}

function getConversations(limit = 50) {
  return db.conversations
    .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
    .slice(0, limit);
}

function getConversation(id) {
  return db.conversations.find(c => c.id === id) || null;
}

function deleteConversation(id) {
  db.messages = db.messages.filter(m => m.conversation_id !== id);
  db.conversations = db.conversations.filter(c => c.id !== id);
  saveDB(db);
}

// --- Message Management ---
function addMessage(conversationId, role, content) {
  const msg = {
    id: Date.now(),
    conversation_id: conversationId,
    role,
    content,
    created_at: new Date().toISOString()
  };
  db.messages.push(msg);
  
  const conv = db.conversations.find(c => c.id === conversationId);
  if (conv) {
    conv.updated_at = new Date().toISOString();
  }
  saveDB(db);
}

function getMessages(conversationId, limit = 50) {
  return db.messages
    .filter(m => m.conversation_id === conversationId)
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
    .slice(-limit);
}

function searchMessages(query, limit = 20) {
  const lowerQuery = query.toLowerCase();
  return db.messages
    .filter(m => m.content.toLowerCase().includes(lowerQuery))
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, limit)
    .map(m => {
      const conv = db.conversations.find(c => c.id === m.conversation_id);
      return { ...m, conversation_title: conv ? conv.title : 'Unknown' };
    });
}

// --- Preferences ---
function setPreference(key, value) {
  const pref = db.preferences.find(p => p.key === key);
  if (pref) {
    pref.value = value;
    pref.updated_at = new Date().toISOString();
  } else {
    db.preferences.push({
      key,
      value,
      updated_at: new Date().toISOString()
    });
  }
  saveDB(db);
}

function getPreference(key, defaultValue = null) {
  const pref = db.preferences.find(p => p.key === key);
  return pref ? pref.value : defaultValue;
}

function getAllPreferences() {
  return db.preferences;
}

// --- Facts ---
function addFact(content, source = 'user') {
  db.facts.push({
    id: Date.now(),
    content,
    source,
    confidence: 1.0,
    created_at: new Date().toISOString()
  });
  saveDB(db);
}

function searchFacts(query, limit = 10) {
  const lowerQuery = query.toLowerCase();
  return db.facts
    .filter(f => f.content.toLowerCase().includes(lowerQuery))
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, limit);
}

function getFactsContext(query) {
  const facts = searchFacts(query, 5);
  if (facts.length === 0) return '';
  return facts.map(f => f.content).join('\n');
}

// --- Context Building ---
function buildContext(conversationId, userMessage) {
  const messages = getMessages(conversationId, 20);
  const facts = searchFacts(userMessage, 3);
  const factsContext = facts.length > 0 ? '\n\nKnown facts:\n' + facts.map(f => `- ${f.content}`).join('\n') : '';
  const model = getPreference('preferred_model', 'mythos-auto');
  const language = getPreference('preferred_language', 'id');

  return {
    messages,
    factsContext,
    model,
    language
  };
}

// --- Settings Persistence ---
function saveSettings(settings) {
  for (const [key, value] of Object.entries(settings)) {
    setPreference(`setting_${key}`, JSON.stringify(value));
  }
}

function loadSettings() {
  const settings = {};
  const rows = db.preferences.filter(p => p.key.startsWith('setting_'));
  for (const row of rows) {
    const key = row.key.replace('setting_', '');
    try {
      settings[key] = JSON.parse(row.value);
    } catch {
      settings[key] = row.value;
    }
  }
  return settings;
}

// --- Export/Import ---
function exportConversations(filePath) {
  const conversations = getConversations(1000);
  const data = conversations.map(c => ({
    ...c,
    messages: getMessages(c.id, 1000)
  }));
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
  return { success: true, count: data.length };
}

function importConversations(filePath) {
  const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  let count = 0;
  for (const conv of data) {
    const existing = db.conversations.find(c => c.id === conv.id);
    if (!existing) {
      db.conversations.push(conv);
    }
    for (const msg of conv.messages || []) {
      const existingMsg = db.messages.find(m => m.id === msg.id);
      if (!existingMsg) {
        db.messages.push(msg);
      }
    }
    count++;
  }
  saveDB(db);
  return { success: true, count };
}

// --- Cleanup ---
function close() {
  saveDB(db);
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
