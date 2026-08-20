import { KV_KEYS, WIZARD_TTL } from "./constants";
import type { Env, Profile, WizardState } from "./types";

export async function getWizard(env: Env, chatId: number): Promise<WizardState | null> {
  const raw = await env.SESSIONS.get(`${KV_KEYS.wizard}${chatId}`);
  return raw ? (JSON.parse(raw) as WizardState) : null;
}

export async function saveWizard(env: Env, state: WizardState): Promise<void> {
  await env.SESSIONS.put(`${KV_KEYS.wizard}${state.chatId}`, JSON.stringify(state), {
    expirationTtl: WIZARD_TTL,
  });
}

export async function clearWizard(env: Env, chatId: number): Promise<void> {
  await env.SESSIONS.delete(`${KV_KEYS.wizard}${chatId}`);
}

export async function getProfile(env: Env, chatId: number): Promise<Profile> {
  const raw = await env.SESSIONS.get(`${KV_KEYS.profile}${chatId}`);
  if (raw) {
    try {
      return JSON.parse(raw) as Profile;
    } catch {
      /* fall through */
    }
  }
  return { lang: "en" };
}

export async function saveProfile(env: Env, chatId: number, profile: Profile): Promise<void> {
  await env.SESSIONS.put(`${KV_KEYS.profile}${chatId}`, JSON.stringify(profile));
}