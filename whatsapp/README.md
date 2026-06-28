# Mythos WhatsApp Bot

WhatsApp bot yang dijalankan di Cloudflare Workers dengan Mythos AI.

## Setup

### 1. Install Wrangler CLI
```bash
npm install -g wrangler
```

### 2. Login Cloudflare
```bash
wrangler login
```

### 3. Set Environment Variables
```bash
wrangler secret put WEBHOOK_VERIFY_TOKEN
wrangler secret put WEBHOOK_SECRET
wrangler secret put PHONE_NUMBER_ID
wrangler secret put WHATSAPP_ACCESS_TOKEN
wrangler secret put OPENROUTER_KEYS
wrangler secret put SHANNON_KEYS
```

### 4. Deploy
```bash
cd whatsapp
npm install
wrangler deploy
```

### 5. Setup WhatsApp Webhook
1. Buka [Meta for Developers](https://developers.facebook.com/)
2. Buat App → Product → WhatsApp
3. Set webhook URL: `https://mythos-whatsapp.<your-subdomain>.workers.dev`
4. Verify token: token yang sama dengan `WEBHOOK_VERIFY_TOKEN`

## Fitur

- Chat dengan Mythos AI via WhatsApp
- Support Shannon dan OpenRouter models
- Auto-detect time/date queries
- Response dalam Bahasa Indonesia/English

## Testing

```bash
wrangler dev
```

Kirim test message ke webhook URL.

## Limitations

- Tidak support gambar/audio di WhatsApp Business API free tier
- Response timeout 30 detik (Cloudflare Workers limit)
- Tidak ada session persistence (setiap pesan independen)
