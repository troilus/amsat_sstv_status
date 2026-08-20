# AMSAT Status — Telegram Bot (Cloudflare Worker)

A Telegram bot that lets users submit satellite status reports to the
[AMSAT Satellite Status](https://www.amsat.org/status/) website through its
public API (`https://www.amsat.org/status/api/v1`).

Users walk through a guided in-chat form:

1. **Satellite** — pick from the live catalog (paginated, with search by name)
2. **Status** — Heard / Telemetry Only / Not Heard / Crew Active
3. **Date** — year → month → day (defaults to today in UTC)
4. **Time** — hour (UTC) → 15-minute period (defaults to the nearest UTC slot)
5. **Callsign** — typed text (defaults to the last one used)
6. **Grid square** — typed Maidenhead locator (required, defaults to the last one used)
7. **Confirm** — review and submit

Re-submitting the same satellite, callsign, hour and 15-minute period
overwrites the earlier report (the API's native correction behavior, matching the
web form).

Languages: **English, Russian, Chinese** (switch anytime with `/language`).

## Stack

- **Runtime:** Cloudflare Workers (webhook mode)
- **Language:** TypeScript
- **State:** Cloudflare KV (wizard session, cached satellite catalog, per-user
  profile with last used callsign / grid square / language)

## Project layout

```
tgbot/
├── wrangler.toml          # Worker config + KV binding
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts           # entry, routing, webhook verification
│   ├── wizard.ts          # flow / state machine / submission
│   ├── keyboards.ts       # inline keyboard builders
│   ├── amsat.ts           # AMSAT API client (catalog, statuses, submit)
│   ├── state.ts           # KV session + profile storage
│   ├── telegram.ts        # Telegram Bot API helper
│   ├── i18n.ts            # en / ru / zh translations
│   ├── constants.ts
│   └── types.ts
└── scripts/
    └── set-webhook.mjs    # registers the Telegram webhook
```

## Prerequisites

- Node.js 18+ and npm
- [wrangler](https://developers.cloudflare.com/workers/wrangler/) (`npm i -g wrangler` or use `npx wrangler`)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Setup

```bash
cd tgbot
npm install
wrangler login
```

Create the KV namespace and paste its id into `wrangler.toml`:

```bash
wrangler kv namespace create SESSIONS
# -> "id" value goes into [[kv_namespaces]] > id
```

Set the secrets:

```bash
wrangler secret put TELEGRAM_BOT_TOKEN
wrangler secret put WEBHOOK_SECRET   # any random string, e.g. openssl rand -hex 32
```

## Deploy

```bash
npm run deploy      # or: wrangler deploy
```

## Register the webhook

Point Telegram's webhook at your worker URL with the same `WEBHOOK_SECRET`:

```bash
$env:TELEGRAM_BOT_TOKEN="<token>"
$env:WORKER_URL="https://<your-worker>.workers.dev"
$env:WEBHOOK_SECRET="<same secret as above>"
node scripts/set-webhook.mjs
```

Or manually:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://<your-worker>.workers.dev/webhook","secret_token":"<secret>","allowed_updates":["message","callback_query"]}'
```

The worker verifies every webhook call against the `X-Telegram-Bot-Api-Secret-Token`
header and rejects mismatches with `403`.

## Local development

```bash
npm run dev    # wrangler dev (KV + secrets from .dev.vars)
```

Create `.dev.vars` for local secrets:

```
TELEGRAM_BOT_TOKEN=...
WEBHOOK_SECRET=...
```

To test locally with Telegram, expose your dev server with a tunnel
(e.g. `cloudflared tunnel --url http://localhost:8787`) and set the webhook to
the tunnel URL plus `/webhook`.

## Verification

```bash
npm run typecheck      # tsc --noEmit
npm run build          # wrangler deploy --dry-run --outdir dist
```

## Notes

- Wizards expire after 30 minutes (KV TTL).
- The satellite catalog is cached in KV for 24 hours to avoid hammering the API.
- `Crew Active` is only meaningful for ISS (matching the API's canonical statuses list).
- All times are UTC; the default date/time reflect the current UTC moment.