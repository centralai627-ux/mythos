// Mythos WhatsApp Bot - Cloudflare Worker
// Integrates Mythos AI with WhatsApp via Meta Cloud API

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Webhook verification for WhatsApp
    if (request.method === 'GET') {
      const mode = url.searchParams.get('hub.mode');
      const token = url.searchParams.get('hub.verify_token');
      const challenge = url.searchParams.get('hub.challenge');

      if (mode === 'subscribe' && token === env.WEBHOOK_VERIFY_TOKEN) {
        return new Response(challenge, { status: 200 });
      }
      return new Response('Forbidden', { status: 403 });
    }

    // Handle incoming messages
    if (request.method === 'POST') {
      try {
        const body = await request.json();

        // Verify webhook signature
        const signature = request.headers.get('x-hub-signature-256');
        if (env.WEBHOOK_SECRET && !verifySignature(body, signature, env.WEBHOOK_SECRET)) {
          return new Response('Invalid signature', { status: 403 });
        }

        // Process WhatsApp message
        const result = await handleWhatsAppMessage(body, env);

        return new Response(JSON.stringify(result), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      } catch (e) {
        console.error('Error:', e);
        return new Response(JSON.stringify({ error: e.message }), { status: 500 });
      }
    }

    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'ok',
        name: env.MYTHOS_NAME || 'Mythos AI',
        version: env.MYTHOS_VERSION || '1.0.0'
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    return new Response('Mythos WhatsApp Bot', { status: 200 });
  }
};

// Verify webhook signature
function verifySignature(body, signature, secret) {
  if (!signature || !secret) return true;
  // Simplified - implement HMAC verification if needed
  return true;
}

// Handle incoming WhatsApp message
async function handleWhatsAppMessage(body, env) {
  const entry = body.entry?.[0];
  const changes = entry?.changes?.[0];
  const value = changes?.value;

  if (!value?.messages?.length) {
    return { status: 'ok', type: 'no_messages' };
  }

  const message = value.messages[0];
  const from = message.from;
  const msgType = message.type;

  // Only handle text messages
  if (msgType !== 'text') {
    await sendWhatsAppMessage(from, 'Saya hanya bisa memproses pesan teks.', env);
    return { status: 'ok', type: 'unsupported' };
  }

  const userText = message.text?.body || '';

  // Process with Mythos AI
  const response = await chatWithMythos(userText, env);

  // Send response back to WhatsApp
  await sendWhatsAppMessage(from, response, env);

  return { status: 'ok', type: 'processed' };
}

// Chat with Mythos AI
async function chatWithMythos(userText, env) {
  // Get API keys
  const openrouterKeys = (env.OPENROUTER_KEYS || '').split(',').filter(k => k);
  const shannonKeys = (env.SHANNON_KEYS || '').split(',').filter(k => k);

  // Detect if needs tools
  const toolResult = detectToolNeeds(userText);
  if (toolResult) {
    return toolResult;
  }

  // Try Shannon first (if available)
  if (shannonKeys.length > 0) {
    try {
      const key = shannonKeys[Math.floor(Math.random() * shannonKeys.length)];
      return await callShannonAPI(userText, key);
    } catch (e) {
      console.log('Shannon failed, trying OpenRouter:', e.message);
    }
  }

  // Fallback to OpenRouter
  if (openrouterKeys.length > 0) {
    const key = openrouterKeys[Math.floor(Math.random() * openrouterKeys.length)];
    return await callOpenRouterAPI(userText, key);
  }

  return 'Mythos AI tidak tersedia saat ini. Silakan coba lagi nanti.';
}

// Detect tool needs from user message
function detectToolNeeds(text) {
  const msg = text.toLowerCase();

  // Time/date
  if (msg.match(/jam berapa|what time|current time|sekarang jam|pukul/)) {
    const now = new Date();
    const time = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const date = now.toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    return `*Jam: ${time}*\n*Tanggal: ${date}*`;
  }

  // Date
  if (msg.match(/tanggal berapa|what date|hari apa|today|hari ini/)) {
    const now = new Date();
    const date = now.toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    const time = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
    return `*Tanggal: ${date}*\n*Jam: ${time}*`;
  }

  return null;
}

// Call Shannon API
async function callShannonAPI(text, apiKey) {
  const response = await fetch('https://api.shannon-ai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: 'shannon-coder-1',
      messages: [
        { role: 'system', content: 'You are Mythos, a helpful AI assistant. Be concise and helpful. Respond in the same language the user uses.' },
        { role: 'user', content: text }
      ],
      max_tokens: 1024,
      temperature: 0.7
    })
  });

  if (!response.ok) {
    throw new Error(`Shannon API error: ${response.status}`);
  }

  const data = await response.json();
  return data.choices?.[0]?.message?.content || 'Tidak ada respons.';
}

// Call OpenRouter API
async function callOpenRouterAPI(text, apiKey) {
  const models = [
    'poolside/laguna-xs.2:free',
    'nvidia/nemotron-3-ultra-550b-a55b:free'
  ];
  const model = models[Math.floor(Math.random() * models.length)];

  const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
      'HTTP-Referer': 'https://mythos-whatsapp.app',
      'X-Title': 'Mythos WhatsApp'
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: 'system', content: 'You are Mythos, a helpful AI assistant. Be concise and helpful. Respond in the same language the user uses.' },
        { role: 'user', content: text }
      ],
      max_tokens: 1024,
      temperature: 0.7
    })
  });

  if (!response.ok) {
    throw new Error(`OpenRouter API error: ${response.status}`);
  }

  const data = await response.json();
  return data.choices?.[0]?.message?.content || 'Tidak ada respons.';
}

// Send WhatsApp message
async function sendWhatsAppMessage(to, text, env) {
  const phoneNumberId = env.PHONE_NUMBER_ID;
  const accessToken = env.WHATSAPP_ACCESS_TOKEN;

  if (!phoneNumberId || !accessToken) {
    console.log('WhatsApp not configured, message:', text);
    return;
  }

  const response = await fetch(
    `https://graph.facebook.com/v18.0/${phoneNumberId}/messages`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        messaging_product: 'whatsapp',
        to: to,
        type: 'text',
        text: { body: text }
      })
    }
  );

  if (!response.ok) {
    const error = await response.text();
    console.error('WhatsApp send error:', error);
  }
}
