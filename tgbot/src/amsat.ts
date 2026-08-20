import { CATALOG_TTL, DEFAULT_STATUSES, KV_KEYS } from "./constants";
import type { Env, ReportStatus, Satellite } from "./types";

const UA = "amsat-status-tgbot/1.0";

export async function getCatalog(env: Env): Promise<Satellite[]> {
  const cached = await env.SESSIONS.get(KV_KEYS.catalog);
  if (cached) {
    try {
      return JSON.parse(cached) as Satellite[];
    } catch {
      /* fall through to refetch */
    }
  }
  const url = `${env.AMSAT_API_BASE}/catalog.php?include_stats=true`;
  const res = await fetch(url, { headers: { "User-Agent": UA, Accept: "application/json" } });
  if (!res.ok) throw new Error(`catalog fetch failed: HTTP ${res.status}`);
  const json = (await res.json()) as { data?: Satellite[] };
  const sats = json.data ?? [];
  if (sats.length) {
    await env.SESSIONS.put(KV_KEYS.catalog, JSON.stringify(sats), { expirationTtl: CATALOG_TTL });
  }
  return sats;
}

export async function getStatuses(env: Env): Promise<ReportStatus[]> {
  try {
    const url = `${env.AMSAT_API_BASE}/statuses.php`;
    const res = await fetch(url, { headers: { "User-Agent": UA, Accept: "application/json" } });
    if (!res.ok) throw new Error(`statuses fetch failed: HTTP ${res.status}`);
    const json = (await res.json()) as { data?: ReportStatus[] };
    if (json.data && json.data.length) return json.data;
  } catch {
    /* fall through to defaults */
  }
  return DEFAULT_STATUSES;
}

export interface ReportCreate {
  name: string;
  report: string;
  callsign: string;
  grid_square?: string;
  reported_at: string;
}

export interface SubmitResult {
  ok: boolean;
  status?: number;
  message?: string;
}

export async function submitReport(env: Env, body: ReportCreate): Promise<SubmitResult> {
  const url = `${env.AMSAT_API_BASE}/reports.php`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "User-Agent": UA, Accept: "application/json" },
      body: JSON.stringify(body),
    });
    const json = (await res.json().catch(() => ({}))) as {
      error?: { message?: string };
      meta?: { message?: string };
      data?: unknown;
    };
    if (res.ok) {
      return { ok: true, status: res.status };
    }
    return { ok: false, status: res.status, message: json.error?.message ?? `HTTP ${res.status}` };
  } catch (e) {
    return { ok: false, message: e instanceof Error ? e.message : String(e) };
  }
}