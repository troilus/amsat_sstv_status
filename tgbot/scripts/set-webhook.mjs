#!/usr/bin/env node
// Set the Telegram webhook for the AMSAT Status Bot.
//
// Usage:
//   node scripts/set-webhook.mjs
//
// Reads:
//   TELEGRAM_BOT_TOKEN   (required)
//   WORKER_URL           (required, e.g. https://amsat-status-tgbot.example.workers.dev)
//   WEBHOOK_SECRET       (optional, must match the WEBHOOK_SECRET secret set in wrangler)

const token = process.env.TELEGRAM_BOT_TOKEN;
const workerUrl = process.env.WORKER_URL;
const secret = process.env.WEBHOOK_SECRET || "";

if (!token || !workerUrl) {
  console.error("Set TELEGRAM_BOT_TOKEN and WORKER_URL environment variables.");
  process.exit(1);
}

const webhookUrl = `${workerUrl.replace(/\/$/, "")}/webhook`;

const body = {
  url: webhookUrl,
  allowed_updates: ["message", "callback_query"],
  ...(secret ? { secret_token: secret } : {}),
};

const res = await fetch(`https://api.telegram.org/bot${token}/setWebhook`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

const data = await res.json();
if (data.ok) {
  console.log(`Webhook set to ${webhookUrl}`);
  const me = await fetch(`https://api.telegram.org/bot${token}/getMe`).then((r) => r.json());
  console.log(`Bot: @${me.result?.username}`);
} else {
  console.error("setWebhook failed:", JSON.stringify(data));
  process.exit(1);
}

const commands = [
  { command: "start", description: "Start the bot" },
  { command: "report", description: "Submit a new STATUS report" },
  { command: "cancel", description: "Cancel the current report" },
  { command: "language", description: "Change language" },
  { command: "help", description: "Show help" },
];
const cm = await fetch(`https://api.telegram.org/bot${token}/setMyCommands`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ commands }),
}).then((r) => r.json());
console.log("setMyCommands:", cm.ok ? "OK" : JSON.stringify(cm));