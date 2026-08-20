import type { Env, InlineKeyboardMarkup } from "./types";

const TGCALLBACK = "https://api.telegram.org/bot";

async function tg<T>(env: Env, method: string, params: object): Promise<T> {
  const url = `${TGCALLBACK}${env.TELEGRAM_BOT_TOKEN}/${method}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  const data = (await res.json().catch(() => ({}))) as { ok: boolean; result: T; description?: string };
  if (!res.ok || !data.ok) {
    throw new Error(`Telegram ${method} failed: ${data.description ?? res.status}`);
  }
  return data.result;
}

export interface MessageSent {
  message_id: number;
}

export function sendMessage(
  env: Env,
  chatId: number,
  text: string,
  keyboard?: InlineKeyboardMarkup
): Promise<MessageSent> {
  return tg<MessageSent>(env, "sendMessage", {
    chat_id: chatId,
    text,
    ...(keyboard ? { reply_markup: keyboard } : {}),
  });
}

export function editMessageText(
  env: Env,
  chatId: number,
  messageId: number,
  text: string,
  keyboard?: InlineKeyboardMarkup
): Promise<MessageSent> {
  return tg<MessageSent>(env, "editMessageText", {
    chat_id: chatId,
    message_id: messageId,
    text,
    ...(keyboard ? { reply_markup: keyboard } : { reply_markup: { inline_keyboard: [] } }),
  });
}

export function answerCallbackQuery(env: Env, callbackQueryId: string): Promise<boolean> {
  return tg<boolean>(env, "answerCallbackQuery", { callback_query_id: callbackQueryId });
}

export async function setMyCommands(
  env: Env,
  commands: { command: string; description: string }[]
): Promise<boolean> {
  return tg<boolean>(env, "setMyCommands", { commands });
}