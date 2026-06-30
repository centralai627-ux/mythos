const os = require('os');
const path = require('path');

// --- Embedded API keys (OpenRouter) ---
const EMBEDDED_KEYS = [
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
  "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",
];

// --- Shannon API Config ---
const SHANNON_KEYS = [
  "sk-dWMQxnPsCB0VGaiS2oq0_m1KM00dP3ev2v_v4dHJ3zk",
  "sk-rBFz0EjOqH0hlSghu63P9bOLaxGSUFziX-8aJ7etzac",
  "sk-kgajDHWx83DPQ8D_Wl1B4HHgy8oDsjiiVWk39mgchC4",
  "sk-DPshiDs5d6v-_X20JccsJpEpPmL6wCyh5y2pkWMA7hA",
  "sk-2UPNW1yIkhMTjZM-dm_AZd0QJ_p9Qmmc2lyGvTJQjSA",
  "sk-ANJZRFqhHMSLlmghJny1jRIcf5BcqTjna_beqqaMoF0",
  "sk-0kIFvmXDzH2vPXVRMcG0j-YryEYGshtLYpLUgInhbto",
  "sk-H9v51mqVkvLjuQaRsLhMLGC6JkiRoqWszkhEHqrP3rs",
  "sk-oNLoyl2G1LHTKlJic4RCBeWOewQGO1hTshVAE2ozZtg"
];

// --- Xiaomi MiMo API Config ---
const MIMO_KEYS = [
  "sk-smweds6l2ldbox0h0aehzdz8uf9g3010kfx33sl6vrjomv53",
  "sk-sd6ux3jfq1hh37rnao9i1jweji8iq4yeyfvkrpbha87j1gq8",
  "sk-s9ps4zagudflqkzubp6vwlww6ckkxbnk24vyi3d5ab6n7muf"
];

const MIMO_BASE_URL = 'https://api.xiaomimimo.com/v1';
const MIMO_MODELS = {
  'mimo-v2.5-pro': 'mimo-v2.5-pro',
  'mimo-v2.5-tts': 'mimo-v2.5-tts',
};

// --- Model Mapping ---
const MODEL_MAP = {
  'mythos-auto': 'mimo-v2.5-pro',
  'mythos-code': 'mimo-v2.5-pro',
  'mythos-code-alt': 'poolside/laguna-m.1:free',
  'mythos-ultra': 'mimo-v2.5-pro',
  'mythos-vision': 'google/gemma-4-31b-it:free',
  'mythos-5': 'shannon-coder-1',
  'mythos-5-pro': 'shannon-pro-2',
  'mythos-mimo': 'mimo-v2.5-pro',
  'mythos-mimo-tts': 'mimo-v2.5-tts',
};

const VISION_MODEL = 'google/gemma-4-31b-it:free';
const SHANNON_BASE_URL = 'https://api.shannon-ai.com/v1';
const SHANNON_MODELS = {
  'mythos-5': 'shannon-coder-1',
  'mythos-5-pro': 'shannon-pro-2',
};

const KNOWLEDGE_DIR = path.join(os.homedir(), '.mythos', 'knowledge');

module.exports = {
  EMBEDDED_KEYS,
  SHANNON_KEYS,
  MIMO_KEYS,
  MIMO_BASE_URL,
  MIMO_MODELS,
  MODEL_MAP,
  VISION_MODEL,
  SHANNON_BASE_URL,
  SHANNON_MODELS,
  KNOWLEDGE_DIR
};
