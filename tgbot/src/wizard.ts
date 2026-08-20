import { getCatalog, getStatuses, submitReport } from "./amsat";
import { b64urlDecode, CB, DEFAULT_STATUSES, pad2, SAT_PAGE_SIZE, YEAR_MIN, YEAR_PAGE_SIZE } from "./constants";
import { t } from "./i18n";
import {
  callsignKeyboard,
  confirmKeyboard,
  dayKeyboard,
  gridKeyboard,
  hourKeyboard,
  langKeyboard,
  mainMenuKeyboard,
  monthKeyboard,
  quarterKeyboard,
  satelliteKeyboard,
  statusKeyboard,
  yearKeyboard,
} from "./keyboards";
import { clearWizard, getProfile, getWizard, saveProfile, saveWizard } from "./state";
import { answerCallbackQuery, editMessageText, sendMessage } from "./telegram";
import type { Env, InlineKeyboardMarkup, Lang, Profile, ReportStatus, Satellite, StepId, WizardState } from "./types";

const CALLSIGN_RE = /^[A-Za-z0-9]{1,10}(?:\/[A-Za-z0-9]{1,6})?$/;
const GRID_RE = /^[A-Ra-r]{2}[0-9]{2}(?:[A-Xa-x]{2}(?:[0-9]{2})?)?$/;

interface Ctx {
  env: Env;
  catalog: Satellite[];
  statuses: ReportStatus[];
  profile: Profile;
  lang: Lang;
}

function nowParts(): { year: number; month: number; day: number; hour: number; quarter: number } {
  const n = new Date();
  return {
    year: n.getUTCFullYear(),
    month: n.getUTCMonth() + 1,
    day: n.getUTCDate(),
    hour: n.getUTCHours(),
    quarter: Math.min(3, Math.round(n.getUTCMinutes() / 15)),
  };
}

async function loadCtx(env: Env, chatId: number): Promise<Ctx> {
  const profile = await getProfile(env, chatId);
  let catalog: Satellite[] = [];
  let statuses: ReportStatus[] = DEFAULT_STATUSES;
  try {
    [catalog, statuses] = await Promise.all([getCatalog(env), getStatuses(env)]);
  } catch (e) {
    console.error("Failed to load catalog/statuses:", e);
  }
  return { env, catalog, statuses, profile, lang: profile.lang || "en" };
}

function pageCount(total: number, size: number): number {
  return Math.max(1, Math.ceil(total / size));
}

function filteredSats(catalog: Satellite[], q: string): Satellite[] {
  const query = q.trim().toLowerCase();
  return catalog.filter(
    (s) => s.name.toLowerCase().includes(query) || (s.display_name ?? "").toLowerCase().includes(query)
  );
}

function reportTime(state: WizardState): { date: string; time: string } {
  const y = state.year ?? 2001;
  const mo = pad2(state.month ?? 1);
  const d = pad2(state.day ?? 1);
  const h = pad2(state.hour ?? 0);
  const mi = pad2((state.quarter ?? 0) * 15);
  return { date: `${y}-${mo}-${d}`, time: `${h}:${mi}` };
}

function reportedAt(state: WizardState): string {
  const r = reportTime(state);
  return `${r.date}T${r.time}:00Z`;
}

function isFuture(state: WizardState): boolean {
  const y = state.year ?? 2001;
  const mo = state.month ?? 1;
  const d = state.day ?? 1;
  const h = state.hour ?? 0;
  const mi = (state.quarter ?? 0) * 15;
  return Date.UTC(y, mo - 1, d, h, mi) > Date.now() + 60_000;
}
const NEXT: Record<StepId, StepId> = {
  satellite: "status",
  status: "year",
  year: "month",
  month: "day",
  day: "hour",
  hour: "quarter",
  quarter: "callsign",
  callsign: "grid",
  grid: "confirm",
  confirm: "confirm",
};

const PREV: Record<StepId, StepId> = {
  satellite: "satellite",
  status: "satellite",
  year: "status",
  month: "year",
  day: "month",
  hour: "day",
  quarter: "hour",
  callsign: "quarter",
  grid: "callsign",
  confirm: "grid",
};

function enterStep(state: WizardState, profile: Profile, step: StepId): boolean {
  state.step = step;
  state.awaiting = undefined;
  if (step === "callsign" && !profile.callsign) {
    state.awaiting = "callsign";
    return true;
  }
  if (step === "grid" && !profile.grid) {
    state.awaiting = "grid";
    return true;
  }
  return false;
}

function stepText(state: WizardState, ctx: Ctx): string {
  const { lang } = ctx;
  switch (state.step) {
    case "satellite": {
      if (state.searchQuery) {
        const list = filteredSats(ctx.catalog, state.searchQuery);
        if (!list.length) return `${t(lang, "satNoMatch", { q: state.searchQuery })}\n\n${t(lang, "satSearchHint")}`;
        return t(lang, "satPrompt", { page: state.satPage + 1, total: pageCount(list.length, SAT_PAGE_SIZE) });
      }
      if (state.search) return t(lang, "satSearchHint");
      return t(lang, "satPrompt", { page: state.satPage + 1, total: pageCount(ctx.catalog.length, SAT_PAGE_SIZE) });
    }
    case "status":
      return t(lang, "statusPrompt");
    case "year":
      return t(lang, "yearPrompt");
    case "month":
      return t(lang, "monthPrompt");
    case "day":
      return t(lang, "dayPrompt");
    case "hour":
      return t(lang, "hourPrompt");
    case "quarter":
      return t(lang, "quarterPrompt");
    case "callsign":
      return t(lang, "callsignPrompt");
    case "grid":
      return t(lang, "gridPrompt");
    case "confirm":
      return [
        t(lang, "confirmTitle"),
        "",
        `${t(lang, "labelSat")}: ${state.satelliteDisplay ?? state.satellite}`,
        `${t(lang, "labelStatus")}: ${state.status}`,
        `${t(lang, "labelDate")}: ${reportTime(state).date}`,
        `${t(lang, "labelTime")}: ${reportTime(state).time} UTC`,
        `${t(lang, "labelCallsign")}: ${state.callsign}`,
        `${t(lang, "labelGrid")}: ${state.grid}`,
        t(lang, "confirmNote"),
      ].join("\n");
    default:
      return "";
  }
}

function stepKeyboard(state: WizardState, ctx: Ctx): InlineKeyboardMarkup | undefined {
  const { lang } = ctx;
  switch (state.step) {
    case "satellite": {
      const list = state.searchQuery ? filteredSats(ctx.catalog, state.searchQuery) : ctx.catalog;
      return satelliteKeyboard(list, state.satPage, pageCount(list.length, SAT_PAGE_SIZE), lang);
    }
    case "status":
      return statusKeyboard(ctx.statuses, lang);
    case "year":
      return yearKeyboard(
        state.year ?? new Date().getUTCFullYear(),
        state.yearPage,
        pageCount((state.year ?? new Date().getUTCFullYear()) - YEAR_MIN + 1, YEAR_PAGE_SIZE),
        state.year,
        lang
      );
    case "month":
      return monthKeyboard(state.month, lang);
    case "day":
      return dayKeyboard(state.year ?? new Date().getUTCFullYear(), state.month ?? 1, state.day, lang);
    case "hour":
      return hourKeyboard(state.hour, lang);
    case "quarter":
      return quarterKeyboard(state.quarter, lang);
    case "callsign":
      return state.awaiting ? undefined : callsignKeyboard(ctx.profile, lang, "choose");
    case "grid":
      return state.awaiting ? undefined : gridKeyboard(ctx.profile, lang, "choose");
    case "confirm":
      return confirmKeyboard(lang);
  }
}

async function renderAndEdit(state: WizardState, ctx: Ctx): Promise<void> {
  const { env } = ctx;
  const text = stepText(state, ctx);
  const kb = stepKeyboard(state, ctx);
  if (state.lastMsgId) {
    await editMessageText(env, state.chatId, state.lastMsgId, text, kb);
  } else {
    const sent = await sendMessage(env, state.chatId, text, kb);
    state.lastMsgId = sent.message_id;
  }
}

async function fullRender(env: Env, state: WizardState): Promise<void> {
  const ctx = await loadCtx(env, state.chatId);
  await renderAndEdit(state, ctx);
  await saveWizard(env, state);
}

function startWizardState(chatId: number): WizardState {
  const p = nowParts();
  return {
    step: "satellite",
    chatId,
    satPage: 0,
    yearPage: 0,
    search: false,
    searchQuery: undefined,
    awaiting: undefined,
    year: p.year,
    month: p.month,
    day: p.day,
    hour: p.hour,
    quarter: p.quarter,
    createdAt: Date.now(),
  };
}
// ---------------------------------------------------------------------------
// Public entry points (commands / menu)
// ---------------------------------------------------------------------------

export async function handleStart(env: Env, chatId: number): Promise<void> {
  const profile = await getProfile(env, chatId);
  const lang = profile.lang || "en";
  await sendMessage(env, chatId, t(lang, "welcome"), mainMenuKeyboard(lang));
}

export async function handleHelp(env: Env, chatId: number): Promise<void> {
  const profile = await getProfile(env, chatId);
  await sendMessage(env, chatId, t(profile.lang || "en", "help"));
}

export async function handleLanguageMenu(env: Env, chatId: number): Promise<void> {
  await sendMessage(env, chatId, t("en", "langPrompt"), langKeyboard());
}

export async function startReport(env: Env, chatId: number): Promise<void> {
  const state = startWizardState(chatId);
  await saveWizard(env, state);
  await fullRender(env, state);
}

export async function cancelReport(env: Env, chatId: number): Promise<void> {
  const profile = await getProfile(env, chatId);
  const state = await getWizard(env, chatId);
  const msg = t(profile.lang || "en", "cancelled");
  if (state?.lastMsgId) {
    await editMessageText(env, chatId, state.lastMsgId, msg);
  } else {
    await sendMessage(env, chatId, msg);
  }
  await clearWizard(env, chatId);
}

// ---------------------------------------------------------------------------
// Text message handler (typed input: search term / callsign / grid)
// ---------------------------------------------------------------------------

export async function handleTextMessage(env: Env, chatId: number, text: string): Promise<void> {
  const state = await getWizard(env, chatId);
  if (!state) {
    const profile = await getProfile(env, chatId);
    await sendMessage(env, chatId, t(profile.lang || "en", "noActive"), mainMenuKeyboard(profile.lang || "en"));
    return;
  }
  const ctx = await loadCtx(env, chatId);

  if (state.step === "satellite" && (state.search || state.searchQuery)) {
    state.search = true;
    state.searchQuery = text.trim();
    state.satPage = 0;
    await saveWizard(env, state);
    await renderAndEdit(state, ctx);
    await saveWizard(env, state);
    return;
  }

  if (state.step === "callsign") {
    const v = text.trim().toUpperCase().replace(/\s+/g, "");
    if (!CALLSIGN_RE.test(v)) {
      await editMessageText(env, chatId, state.lastMsgId ?? 0, t(ctx.lang, "callsignInvalid"));
      return;
    }
    state.callsign = v;
    enterStep(state, ctx.profile, "grid");
    await saveWizard(env, state);
    await renderAndEdit(state, ctx);
    await saveWizard(env, state);
    return;
  }

  if (state.step === "grid") {
    const v = text.trim().toUpperCase();
    if (!GRID_RE.test(v)) {
      await editMessageText(env, chatId, state.lastMsgId ?? 0, t(ctx.lang, "gridInvalid"));
      return;
    }
    state.grid = v;
    state.step = "confirm";
    state.awaiting = undefined;
    await saveWizard(env, state);
    await renderAndEdit(state, ctx);
    await saveWizard(env, state);
    return;
  }

  await sendMessage(env, chatId, t(ctx.lang, "noActive"), mainMenuKeyboard(ctx.lang));
}

// ---------------------------------------------------------------------------
// Callback handler
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Callback handler
// ---------------------------------------------------------------------------

export async function handleCallback(
  env: Env,
  callbackQueryId: string,
  chatId: number,
  data: string
): Promise<void> {
  await answerCallbackQuery(env, callbackQueryId);

  if (data.startsWith("menu:")) {
    const action = data.slice(5);
    if (action === "report") return startReport(env, chatId);
    if (action === "lang") return handleLanguageMenu(env, chatId);
    if (action === "help") return handleHelp(env, chatId);
    return;
  }

  if (data.startsWith(`${CB.langPick}:`)) {
    const lang = data.split(":")[1] as Lang;
    const profile = await getProfile(env, chatId);
    profile.lang = lang;
    await saveProfile(env, chatId, profile);
    await sendMessage(env, chatId, t(lang, "langDone"), mainMenuKeyboard(lang));
    return;
  }

  if (data === CB.cancel) {
    return cancelReport(env, chatId);
  }

  const state = await getWizard(env, chatId);
  if (!state) {
    const profile = await getProfile(env, chatId);
    await sendMessage(env, chatId, t(profile.lang || "en", "noActive"), mainMenuKeyboard(profile.lang || "en"));
    return;
  }
  const ctx = await loadCtx(env, chatId);

  const render = async () => {
    await renderAndEdit(state, ctx);
    await saveWizard(env, state);
  };

  if (data === CB.submit) {
    if (
      !state.satellite || !state.status || !state.callsign || !state.grid ||
      state.year == null || state.month == null || state.day == null || state.hour == null || state.quarter == null
    ) {
      await editMessageText(env, chatId, state.lastMsgId ?? 0, t(ctx.lang, "submitErr", { err: "incomplete report" }));
      return;
    }
    if (isFuture(state)) {
      await editMessageText(env, chatId, state.lastMsgId ?? 0, t(ctx.lang, "submitFuture"));
      return;
    }
    const res = await submitReport(ctx.env, {
      name: state.satellite,
      report: state.status,
      callsign: state.callsign,
      grid_square: state.grid,
      reported_at: reportedAt(state),
    });
    if (res.ok) {
      const profile = await getProfile(env, chatId);
      profile.callsign = state.callsign;
      profile.grid = state.grid;
      await saveProfile(env, chatId, profile);
      const body = t(ctx.lang, "submitOkBody", {
        sat: state.satelliteDisplay ?? state.satellite,
        status: state.status,
        time: reportTime(state).time,
        callsign: state.callsign,
        grid: state.grid,
      });
      await editMessageText(env, chatId, state.lastMsgId ?? 0, `${t(ctx.lang, "submitOk")}\n\n${body}`);
      await clearWizard(env, chatId);
    } else {
      await editMessageText(env, chatId, state.lastMsgId ?? 0, t(ctx.lang, "submitErr", { err: res.message ?? "unknown" }));
    }
    return;
  }

  switch (true) {
case data === CB.back: {
      if (state.step === "satellite" && (state.search || state.searchQuery)) {
        state.search = false;
        state.searchQuery = undefined;
        state.satPage = 0;
        return render();
      }
      state.step = PREV[state.step];
      state.awaiting = undefined;
      if ((state.step === "callsign" || state.step === "grid") && !ctx.profile[state.step === "callsign" ? "callsign" : "grid"]) {
        state.awaiting = state.step;
      }
      return render();
    }
    case data === CB.next: {
      const n = NEXT[state.step];
      if (n === state.step) return;
      if (n === "callsign" || n === "grid") {
        enterStep(state, ctx.profile, n);
      } else {
        state.step = n;
      }
      return render();
    }
case data === CB.satSearch: {
      // Toggle: if a search is active, clear back to the full list; otherwise begin search.
      if (state.searchQuery) {
        state.search = false;
        state.searchQuery = undefined;
      } else {
        state.search = true;
        state.searchQuery = undefined;
      }
      state.satPage = 0;
      return render();
    }
    case data === CB.callsignUse: {
      if (ctx.profile.callsign) {
        state.callsign = ctx.profile.callsign;
        enterStep(state, ctx.profile, "grid");
        return render();
      }
      state.awaiting = "callsign";
      return render();
    }
    case data === CB.callsignNew: {
      state.awaiting = "callsign";
      return render();
    }
    case data === CB.gridUse: {
      if (ctx.profile.grid) {
        state.grid = ctx.profile.grid;
        state.step = "confirm";
        state.awaiting = undefined;
        return render();
      }
      state.awaiting = "grid";
      return render();
    }
    case data === CB.gridNew: {
      state.awaiting = "grid";
      return render();
    }
    case data.startsWith(`${CB.satPage}:`):
      state.satPage = Number(data.split(":")[1]);
      return render();
    case data.startsWith(`${CB.satPick}:`): {
      const name = b64urlDecode(data.slice(CB.satPick.length + 1));
      const sat = ctx.catalog.find((s) => s.name === name);
      if (!sat) return;
      state.satellite = sat.name;
      state.satelliteDisplay = sat.display_name ?? sat.name;
      state.search = false;
      state.searchQuery = undefined;
      enterStep(state, ctx.profile, "status");
      return render();
    }
    case data.startsWith(`${CB.statusPick}:`): {
      const value = b64urlDecode(data.slice(CB.statusPick.length + 1));
      state.status = value;
      enterStep(state, ctx.profile, "year");
      return render();
    }
    case data.startsWith(`${CB.yearPage}:`):
      state.yearPage = Number(data.split(":")[1]);
      return render();
    case data.startsWith(`${CB.yearPick}:`):
      state.year = Number(data.split(":")[1]);
      state.step = "month";
      return render();
    case data.startsWith(`${CB.monthPick}:`):
      state.month = Number(data.split(":")[1]);
      state.step = "day";
      return render();
    case data.startsWith(`${CB.dayPick}:`):
      state.day = Number(data.split(":")[1]);
      state.step = "hour";
      return render();
    case data.startsWith(`${CB.hourPick}:`):
      state.hour = Number(data.split(":")[1]);
      state.step = "quarter";
      return render();
    case data.startsWith(`${CB.quarterPick}:`):
      state.quarter = Number(data.split(":")[1]);
      enterStep(state, ctx.profile, "callsign");
      return render();
  }
}
