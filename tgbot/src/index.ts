import type { Env, TelegramUpdate } from "./types";
import {
  cancelReport,
  handleCallback,
  handleHelp,
  handleLanguageMenu,
  handleStart,
  handleTextMessage,
  startReport,
} from "./wizard";

const WEBHOOK_PATH = "/webhook";

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/") {
      return new Response("AMSAT Status Telegram Bot is running.", {
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }

    if (request.method === "GET" && url.pathname === "/help") {
      return new Response(
        "AMSAT Status Telegram Bot\n\n" +
          "Deploy: wrangler deploy\n" +
          "Webhook: POST /webhook (verify X-Telegram-Bot-Api-Secret-Token == WEBHOOK_SECRET)\n" +
          "Set webhook: node scripts/set-webhook.mjs",
        { headers: { "content-type": "text/plain; charset=utf-8" } }
      );
    }

    if (request.method === "POST" && url.pathname === WEBHOOK_PATH) {
      const secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token");
      if (secret !== env.WEBHOOK_SECRET) {
        return new Response("Forbidden", { status: 403 });
      }
      const update = (await request.json()) as TelegramUpdate;
      ctx.waitUntil(handleUpdate(update, env));
      return new Response("OK");
    }

    return new Response("Not Found", { status: 404 });
  },

  async scheduled(_controller: ScheduledController, env: Env, ctx: ExecutionContext): Promise<void> {
    // No scheduled tasks needed for webhook-driven bot.
    ctx.waitUntil(Promise.resolve());
  },
};

async function handleUpdate(update: TelegramUpdate, env: Env): Promise<void> {
  try {
    if (update.message?.text) {
      const chatId = update.message.chat.id;
      const text = update.message.text.trim();
      await handleCommandOrText(env, chatId, text);
    } else if (update.callback_query) {
      const chatId = update.callback_query.message?.chat.id ?? update.callback_query.from.id;
      const cq = update.callback_query;
      await handleCallback(env, cq.id, chatId, cq.data);
    }
  } catch (e) {
    console.error("handleUpdate error:", e);
  }
}

async function handleCommandOrText(env: Env, chatId: number, text: string): Promise<void> {
  if (text.startsWith("/")) {
    const cmd = text.split(/\s+/)[0].toLowerCase();
    const name = cmd.replace("@", ":").split(":")[0];
    switch (name) {
      case "/start":
        return handleStart(env, chatId);
      case "/report":
        return startReport(env, chatId);
      case "/cancel":
        return cancelReport(env, chatId);
      case "/language":
        return handleLanguageMenu(env, chatId);
      case "/help":
        return handleHelp(env, chatId);
      default:
        return handleHelp(env, chatId);
    }
  }
  return handleTextMessage(env, chatId, text);
}

// (no other exports — the worker module must export only the handler)