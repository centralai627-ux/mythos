const https = require('https');
const { MODEL_MAP, SHANNON_BASE_URL, SHANNON_KEYS, MIMO_KEYS, MIMO_BASE_URL, MIMO_MODELS } = require('../config');

let shannonKeyIdx = 0;
let mimoKeyIdx = 0;

function getNextShannonKey() {
  const k = SHANNON_KEYS[shannonKeyIdx % SHANNON_KEYS.length];
  shannonKeyIdx = (shannonKeyIdx + 1) % SHANNON_KEYS.length;
  return k;
}

function getNextMimoKey() {
  const k = MIMO_KEYS[mimoKeyIdx % MIMO_KEYS.length];
  mimoKeyIdx = (mimoKeyIdx + 1) % MIMO_KEYS.length;
  return k;
}

function isShannonModel(modelAlias) {
  return modelAlias === 'mythos-5' || modelAlias === 'mythos-5-pro';
}

function isMimoModel(modelAlias) {
  return modelAlias.startsWith('mythos-mimo') || modelAlias.startsWith('mimo-');
}

function isRetryable(status) {
  return status === 429 || status === 401 || status === 402 || status === 503 || status === 500;
}

function callAPI(messages, apiKey, modelAlias = 'mythos-code') {
  return new Promise((resolve, reject) => {
    const model = MODEL_MAP[modelAlias] || MODEL_MAP['mythos-code'];
    const isShannon = isShannonModel(modelAlias);
    const isMimo = isMimoModel(modelAlias);
    const key = isShannon ? undefined : (isMimo ? undefined : apiKey);

    let hostname, urlPath, authKey;
    if (isShannon) {
      hostname = 'api.shannon-ai.com';
      urlPath = '/v1/chat/completions';
      authKey = getNextShannonKey();
    } else if (isMimo) {
      hostname = 'api.xiaomimimo.com';
      urlPath = '/v1/chat/completions';
      authKey = getNextMimoKey();
    } else {
      hostname = 'openrouter.ai';
      urlPath = '/api/v1/chat/completions';
      authKey = key;
    }

    const body = JSON.stringify({ model, messages, temperature: 0.7, max_tokens: 1024 });

    const req = https.request({
      hostname,
      port: 443,
      path: urlPath,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + (authKey || getNextShannonKey()),
        'HTTP-Referer': 'https://mythos-desktop.app',
        'X-Title': 'Mythos Desktop',
      },
    }, (res) => {
      let data = '';
      res.on('data', (c) => data += c);
      res.on('end', () => {
        try {
          const j = JSON.parse(data);
          if (res.statusCode === 200 && j.choices)
            resolve(j.choices[0]?.message?.content || 'No response');
          else
            reject({ status: res.statusCode, msg: j.error?.message || 'API error' });
        } catch {
          reject({ status: res.statusCode, msg: 'Parse error' });
        }
      });
    });

    req.on('error', (e) => reject({ status: 0, msg: e.message }));
    req.setTimeout(30000, () => { req.destroy(); reject({ status: 0, msg: 'timeout' }); });
    req.write(body);
    req.end();
  });
}

module.exports = { callAPI, getNextShannonKey, getNextMimoKey, isShannonModel, isMimoModel, isRetryable };
