const { app, BrowserWindow, shell, ipcMain } = require('electron');
const path = require('path');
const http = require('http');
const fs = require('fs');
const os = require('os');
const https = require('https');

// Import modules
const { EMBEDDED_KEYS, SHANNON_KEYS, MIMO_KEYS, MIMO_BASE_URL } = require('./config');
const { agenticChat } = require('./ai/agentic');
const { visionWithRetry } = require('./tools/vision');
const {
  runShell, webSearch, webFetch,
  readFile, writeFile, listDir, searchFiles,
  addKnowledge, searchKnowledge, listKnowledge, removeKnowledge
} = require('./tools');

// Memory system
const memory = require('./memory');

const DIST = path.join(__dirname, '..', 'dist');
let mainWindow;
let server;

// Voice mode state
let voiceMode = false;
let mimoKeyIdx = 0;
let lastTTSRequest = 0;  // Track last TTS request time
const TTS_MIN_INTERVAL = 2000;  // Minimum 2 seconds between TTS requests

// --- Key Manager ---
let allKeys = EMBEDDED_KEYS.slice();
let keyIdx = Math.floor(Math.random() * allKeys.length);
let shannonIdx = Math.floor(Math.random() * SHANNON_KEYS.length);

const keyManager = {
  getNextKey() {
    const k = allKeys[keyIdx % allKeys.length];
    keyIdx = (keyIdx + 1) % allKeys.length;
    return k;
  },
  getNextShannonKey() {
    const k = SHANNON_KEYS[shannonIdx % SHANNON_KEYS.length];
    shannonIdx = (shannonIdx + 1) % SHANNON_KEYS.length;
    return k;
  },
  getNextMimoKey() {
    const k = MIMO_KEYS[mimoKeyIdx % MIMO_KEYS.length];
    mimoKeyIdx = (mimoKeyIdx + 1) % MIMO_KEYS.length;
    return k;
  }
};

// --- HTTP Server ---
const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'application/javascript',
  '.css': 'text/css', '.json': 'application/json', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
};

function startServer() {
  return new Promise((resolve) => {
    server = http.createServer((req, res) => {
      const url = req.url.split('?')[0];
      let fp = path.join(DIST, url === '/' ? 'index.html' : url);
      if (!fs.existsSync(fp) || fs.statSync(fp).isDirectory()) fp = path.join(DIST, 'index.html');
      try {
        res.writeHead(200, { 'Content-Type': MIME[path.extname(fp)] || 'application/octet-stream' });
        res.end(fs.readFileSync(fp));
      } catch { res.writeHead(404); res.end('Not found'); }
    });
    server.listen(0, '127.0.0.1', () => resolve(server.address().port));
  });
}

// --- Window ---
async function createWindow() {
  const port = await startServer();
  mainWindow = new BrowserWindow({
    width: 1400, height: 900, minWidth: 1000, minHeight: 700,
    frame: false, titleBarStyle: 'hidden', backgroundColor: '#0d1117',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true
    },
    show: false,
  });
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    // Play Mythos introduction speech on first launch
    playBootIntroduction();
  });
  mainWindow.loadURL('http://127.0.0.1:' + port);
  mainWindow.on('closed', () => { mainWindow = null; if (server) server.close(); });
  mainWindow.webContents.setWindowOpenHandler(({ url }) => { shell.openExternal(url); return { action: 'deny' }; });
}

// --- Window IPC ---
ipcMain.on('window-minimize', () => mainWindow && mainWindow.minimize());
ipcMain.on('window-maximize', () => {
  if (!mainWindow) return;
  mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize();
});
ipcMain.on('window-close', () => mainWindow && mainWindow.close());

// --- Chat IPC ---
ipcMain.handle('ai-chat', async (_e, messages, modelAlias, attachmentData) => {
  try {
    if (attachmentData) {
      const key = keyManager.getNextKey();
      const userMsg = messages[messages.length - 1];
      const userPrompt = userMsg?.content || 'Describe this image';
      const visionResult = await visionWithRetry(
        attachmentData, 'Describe this image in detail.', key,
        () => keyManager.getNextKey(), (s) => [429, 401, 402, 503, 500].includes(s)
      );
      const result = await agenticChat([
        { role: 'system', content: 'Image analysis:\n' + visionResult + '\n\nAnswer based on this.' },
        ...messages.slice(0, -1),
        { role: 'user', content: userPrompt }
      ], modelAlias || 'mythos-auto', keyManager);
      return { success: true, content: result.content, toolLogs: result.toolLogs || [] };
    }

    const result = await agenticChat(messages, modelAlias || 'mythos-auto', keyManager);
    return { success: true, content: result.content, toolLogs: result.toolLogs || [] };
  } catch (e) {
    return { success: false, error: e?.msg || e?.message || 'Service unavailable' };
  }
});

// --- Tool IPC ---
ipcMain.handle('tool:run_shell', async (_e, command, shellType, cwd) => runShell(command, shellType, cwd));
ipcMain.handle('tool:web_search', async (_e, query, maxResults) => webSearch(query, maxResults));
ipcMain.handle('tool:web_fetch', async (_e, url) => webFetch(url));
ipcMain.handle('tool:read_file', async (_e, filePath) => readFile(filePath));
ipcMain.handle('tool:write_file', async (_e, filePath, content) => writeFile(filePath, content));
ipcMain.handle('tool:list_dir', async (_e, dirPath) => listDir(dirPath));
ipcMain.handle('tool:search', async (_e, pattern, searchPath, glob) => searchFiles(pattern, searchPath, glob));

// --- RAG IPC ---
ipcMain.handle('rag:add', async (_e, title, content, tags) => addKnowledge(title, content, tags));
ipcMain.handle('rag:search', async (_e, query, maxResults) => searchKnowledge(query, maxResults));
ipcMain.handle('rag:list', async () => listKnowledge());
ipcMain.handle('rag:remove', async (_e, id) => removeKnowledge(id));

// --- Memory IPC ---
ipcMain.handle('memory:createConversation', async (_e, title, model) => memory.createConversation(title, model));
ipcMain.handle('memory:getConversations', async () => memory.getConversations());
ipcMain.handle('memory:getConversation', async (_e, id) => memory.getConversation(id));
ipcMain.handle('memory:deleteConversation', async (_e, id) => memory.deleteConversation(id));
ipcMain.handle('memory:addMessage', async (_e, convId, role, content) => memory.addMessage(convId, role, content));
ipcMain.handle('memory:getMessages', async (_e, convId, limit) => memory.getMessages(convId, limit));
ipcMain.handle('memory:searchMessages', async (_e, query, limit) => memory.searchMessages(query, limit));
ipcMain.handle('memory:setPreference', async (_e, key, value) => memory.setPreference(key, value));
ipcMain.handle('memory:getPreference', async (_e, key, defaultVal) => memory.getPreference(key, defaultVal));
ipcMain.handle('memory:saveSettings', async (_e, settings) => memory.saveSettings(settings));
ipcMain.handle('memory:loadSettings', async () => memory.loadSettings());
ipcMain.handle('memory:addFact', async (_e, content, source) => memory.addFact(content, source));
ipcMain.handle('memory:searchFacts', async (_e, query, limit) => memory.searchFacts(query, limit));
ipcMain.handle('memory:exportConversations', async (_e, filePath) => memory.exportConversations(filePath));
ipcMain.handle('memory:importConversations', async (_e, filePath) => memory.importConversations(filePath));

// --- Boot Introduction ---
const MYTHOS_INTRODUCTION = `Hello. I am Mythos. Your autonomous AI assistant.

I was designed to help you think, create, and build. I can write code, analyze documents, search the web, process images, and speak with you directly.

I am always learning. Every conversation we have helps me understand you better. I remember what matters to you, and I use that knowledge to provide more relevant, more helpful responses over time.

I can generate PDFs, create spreadsheets, manage your notes, and even synchronize with Obsidian as your second brain. My voice is powered by advanced text-to-speech technology, and I can adapt my tone and style to match your preferences.

Think of me as your digital companion. I am here to assist, to explore ideas with you, and to make your workflow smoother. Whether you need help with a complex coding problem, want to brainstorm creative solutions, or simply need someone to talk through an idea with — I am ready.

Let us begin.`;

async function playBootIntroduction() {
  try {
    // Wait a moment for the app to fully load
    await new Promise(r => setTimeout(r, 2000));
    
    // Play the introduction
    const result = await speakText(MYTHOS_INTRODUCTION);
    
    if (result.success && result.audioPath) {
      // Notify frontend to play audio
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('play-audio', result.audioPath);
      }
    }
  } catch (e) {
    console.error('Boot introduction failed:', e);
  }
}

// --- Voice/TTS Functions ---
function cleanTextForSpeech(text) {
  // Remove code blocks
  text = text.replace(/```[\s\S]*?```/g, '');
  // Remove inline code
  text = text.replace(/`[^`]*`/g, '');
  // Remove markdown links
  text = text.replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1');
  // Remove markdown headers
  text = text.replace(/^#{1,6}\s+/gm, '');
  // Remove bold/italic markers
  text = text.replace(/\*{1,2}([^\*]*)\*{1,2}/g, '$1');
  // Remove bullet points
  text = text.replace(/^[\-\*]\s+/gm, '');
  // Remove numbered lists
  text = text.replace(/^\d+\.\s+/gm, '');
  // Remove extra whitespace
  text = text.replace(/\n{3,}/g, '\n\n');
  return text.trim();
}

async function speakText(text, speed = 1.0, retries = 3) {
  // Rate limiting - wait if too soon since last request
  const now = Date.now();
  const timeSinceLastRequest = now - lastTTSRequest;
  if (timeSinceLastRequest < TTS_MIN_INTERVAL) {
    const waitTime = TTS_MIN_INTERVAL - timeSinceLastRequest;
    console.log(`TTS rate limiting: waiting ${waitTime}ms`);
    await new Promise(r => setTimeout(r, waitTime));
  }
  lastTTSRequest = Date.now();
  
  const key = keyManager.getNextMimoKey();
  
  // Clean text for speech
  const cleanText = cleanTextForSpeech(text);
  if (!cleanText || cleanText.length < 5) {
    return { success: false, error: 'Text too short to speak' };
  }
  
  // Limit speech length
  const limitedText = cleanText.length > 800 
    ? cleanText.substring(0, 800) + '... I have truncated the rest.'
    : cleanText;
  
  // Detect language (simple heuristic)
  const hasIndonesian = /[a-z]+ (adalah|dan|ini|itu|untuk|dengan|tidak|bisa|akan|sudah|yang|dari|ke|di|pada)/i.test(limitedText);
  
  // Try voice design first, fallback to regular TTS
  const models = hasIndonesian 
    ? ['mimo-v2.5-tts']
    : ['mimo-v2.5-tts-voicedesign', 'mimo-v2.5-tts'];
  
  for (const model of models) {
    const result = await speakWithModel(text, model, hasIndonesian, speed, retries);
    if (result.success) return result;
    
    // If not a server error, return immediately
    if (result.statusCode && ![429, 500, 503].includes(result.statusCode)) {
      return result;
    }
  }
  
  return { success: false, error: 'Voice service temporarily unavailable. Please try again in a few moments.' };
}

async function speakWithModel(text, model, hasIndonesian, speed, retries) {
  const key = keyManager.getNextMimoKey();
  const voice = hasIndonesian ? '冰糖' : 'Mia';
  
  // Sister Location style - cold, polite, eerie female AI voice
  const styleInstruction = hasIndonesian 
    ? 'Berbicara dengan jelas, natural, dan profesional dalam Bahasa Indonesia.'
    : `(Circus Baby voice) A young female AI voice, cold and mechanical yet deceptively polite. 
The voice should sound like a sophisticated animatronic trying to be friendly while hiding darker intentions. 
Slightly distorted, with perfect clarity and an unsettling calmness. 
Think of a robot that has learned to mimic human warmth but can't quite hide the artificial nature beneath.
Slow, deliberate pacing with precise articulation. Each word carefully chosen and delivered.
A hint of curiosity and playfulness that feels slightly wrong - like something pretending to be human.`;
  
  const audioConfig = hasIndonesian 
    ? { format: "wav", voice: voice }
    : { format: "wav", optimize_text_preview: true };
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    const body = JSON.stringify({
      model: model,
      messages: [
        { role: "user", content: styleInstruction },
        { role: "assistant", content: text }
      ],
      audio: audioConfig
    });
    
    try {
      const result = await makeTTSRequest(key, body);
      if (result.success) return result;
      
      // Server overloaded - wait longer
      if (result.statusCode === 503 && attempt < retries) {
        const delay = Math.min(10000 * Math.pow(2, attempt), 60000); // 10s, 20s, 40s
        console.log(`TTS server busy, retry ${attempt + 1}/${retries} after ${Math.round(delay/1000)}s (model: ${model})`);
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      
      // Rate limited - wait and retry
      if (result.statusCode === 429 && attempt < retries) {
        const delay = Math.min(5000 * Math.pow(2, attempt), 30000);
        console.log(`TTS rate limited, retry ${attempt + 1}/${retries} after ${Math.round(delay/1000)}s`);
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      
      return result;
    } catch (e) {
      if (attempt < retries) {
        await new Promise(r => setTimeout(r, 2000));
        continue;
      }
      return { success: false, error: e.message };
    }
  }
  
  return { success: false, error: 'Max retries exceeded', statusCode: 503 };
}

function makeTTSRequest(key, body) {
  return new Promise((resolve) => {
    const req = https.request({
      hostname: 'api.xiaomimimo.com',
      port: 443,
      path: '/v1/chat/completions',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + key,
      },
    }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const response = JSON.parse(Buffer.concat(chunks).toString());
            if (response.choices && response.choices[0] && response.choices[0].message && response.choices[0].message.audio) {
              const audioBase64 = response.choices[0].message.audio.data;
              const audioBuffer = Buffer.from(audioBase64, 'base64');
              const tempPath = path.join(os.tmpdir(), `mythos_tts_${Date.now()}.wav`);
              fs.writeFileSync(tempPath, audioBuffer);
              resolve({ success: true, audioPath: tempPath, duration: audioBuffer.length / 32000 });
            } else {
              resolve({ success: false, error: 'No audio in response' });
            }
          } catch (e) {
            resolve({ success: false, error: 'Failed to parse response: ' + e.message });
          }
        } else {
          const errorBody = Buffer.concat(chunks).toString();
          resolve({ 
            success: false, 
            error: `TTS API error ${res.statusCode}`,
            statusCode: res.statusCode
          });
        }
      });
    });
    
    req.on('error', (e) => resolve({ success: false, error: e.message }));
    req.setTimeout(60000, () => { req.destroy(); resolve({ success: false, error: 'timeout' }); });
    req.write(body);
    req.end();
  });
}

// --- Voice IPC ---
ipcMain.handle('voice:toggle', async (_e, enabled) => {
  voiceMode = enabled;
  return { success: true, voiceMode };
});

ipcMain.handle('voice:status', async () => {
  return { voiceMode };
});

ipcMain.handle('voice:speak', async (_e, text, speed) => {
  return await speakText(text, speed);
});

// Get audio file as base64 data URL for playback in renderer
ipcMain.handle('voice:getAudioData', async (_e, audioPath) => {
  try {
    if (!fs.existsSync(audioPath)) {
      return { success: false, error: 'Audio file not found' };
    }
    const audioBuffer = fs.readFileSync(audioPath);
    const base64 = audioBuffer.toString('base64');
    const ext = path.extname(audioPath).slice(1);
    const mimeType = ext === 'wav' ? 'audio/wav' : 'audio/mpeg';
    return { 
      success: true, 
      dataUrl: `data:${mimeType};base64,${base64}`,
      size: audioBuffer.length 
    };
  } catch (e) {
    return { success: false, error: e.message };
  }
});

// --- Auto-voice hook in chat ---
const originalChatHandler = ipcMain._events['ai-chat'];
ipcMain.removeHandler('ai-chat');
ipcMain.handle('ai-chat', async (_e, messages, modelAlias, attachmentData) => {
  try {
    let result;
    if (attachmentData) {
      const key = keyManager.getNextKey();
      const userMsg = messages[messages.length - 1];
      const userPrompt = userMsg?.content || 'Describe this image';
      const visionResult = await visionWithRetry(
        attachmentData, 'Describe this image in detail.', key,
        () => keyManager.getNextKey(), (s) => [429, 401, 402, 503, 500].includes(s)
      );
      result = await agenticChat([
        { role: 'system', content: 'Image analysis:\n' + visionResult + '\n\nAnswer based on this.' },
        ...messages.slice(0, -1),
        { role: 'user', content: userPrompt }
      ], modelAlias || 'mythos-auto', keyManager);
    } else {
      result = await agenticChat(messages, modelAlias || 'mythos-auto', keyManager);
    }
    
    // Auto-voice: speak response if voice mode is enabled
    let audioPath = null;
    if (voiceMode && result.content) {
      const ttsResult = await speakText(result.content);
      if (ttsResult.success) {
        audioPath = ttsResult.audioPath;
      }
    }
    
    return { 
      success: true, 
      content: result.content, 
      toolLogs: result.toolLogs || [],
      audioPath: audioPath
    };
  } catch (e) {
    return { success: false, error: e?.msg || e?.message || 'Service unavailable' };
  }
});

// --- Lifecycle ---
app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (server) server.close(); if (process.platform !== 'darwin') app.quit(); });
app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
