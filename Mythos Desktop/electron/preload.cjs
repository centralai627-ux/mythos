const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Window controls
  minimize: () => ipcRenderer.send('window-minimize'),
  maximize: () => ipcRenderer.send('window-maximize'),
  close: () => ipcRenderer.send('window-close'),
  isElectron: true,
  
  // Generic invoke for any IPC
  invoke: (channel, ...args) => ipcRenderer.invoke(channel, ...args),
  
  // Chat
  chat: (messages, modelAlias, attachmentData) => ipcRenderer.invoke('ai-chat', messages, modelAlias, attachmentData),
  
  // Voice
  voice: {
    toggle: (enabled) => ipcRenderer.invoke('voice:toggle', enabled),
    status: () => ipcRenderer.invoke('voice:status'),
    speak: (text, speed) => ipcRenderer.invoke('voice:speak', text, speed),
  },
  
  // Tools
  tools: {
    runShell: (command, shellType) => ipcRenderer.invoke('tool:run_shell', command, shellType),
    webSearch: (query, maxResults) => ipcRenderer.invoke('tool:web_search', query, maxResults),
    webFetch: (url) => ipcRenderer.invoke('tool:web_fetch', url),
    readFile: (filePath) => ipcRenderer.invoke('tool:read_file', filePath),
    writeFile: (filePath, content) => ipcRenderer.invoke('tool:write_file', filePath, content),
    listDir: (dirPath) => ipcRenderer.invoke('tool:list_dir', dirPath),
    search: (pattern, searchPath, glob) => ipcRenderer.invoke('tool:search', pattern, searchPath, glob),
  },
  
  // RAG Knowledge Base
  rag: {
    add: (title, content, tags) => ipcRenderer.invoke('rag:add', title, content, tags),
    search: (query, maxResults) => ipcRenderer.invoke('rag:search', query, maxResults),
    list: () => ipcRenderer.invoke('rag:list'),
    remove: (id) => ipcRenderer.invoke('rag:remove', id),
  },

  // Memory System
  memory: {
    createConversation: (title, model) => ipcRenderer.invoke('memory:createConversation', title, model),
    getConversations: () => ipcRenderer.invoke('memory:getConversations'),
    getConversation: (id) => ipcRenderer.invoke('memory:getConversation', id),
    deleteConversation: (id) => ipcRenderer.invoke('memory:deleteConversation', id),
    addMessage: (convId, role, content) => ipcRenderer.invoke('memory:addMessage', convId, role, content),
    getMessages: (convId, limit) => ipcRenderer.invoke('memory:getMessages', convId, limit),
    searchMessages: (query, limit) => ipcRenderer.invoke('memory:searchMessages', query, limit),
    setPreference: (key, value) => ipcRenderer.invoke('memory:setPreference', key, value),
    getPreference: (key, defaultVal) => ipcRenderer.invoke('memory:getPreference', key, defaultVal),
    saveSettings: (settings) => ipcRenderer.invoke('memory:saveSettings', settings),
    loadSettings: () => ipcRenderer.invoke('memory:loadSettings'),
    addFact: (content, source) => ipcRenderer.invoke('memory:addFact', content, source),
    searchFacts: (query, limit) => ipcRenderer.invoke('memory:searchFacts', query, limit),
    exportConversations: (filePath) => ipcRenderer.invoke('memory:exportConversations', filePath),
    importConversations: (filePath) => ipcRenderer.invoke('memory:importConversations', filePath),
  }
});
