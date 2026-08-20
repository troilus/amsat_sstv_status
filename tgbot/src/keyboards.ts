import { b64urlEncode, CB } from "./constants";
import { monthName, statusLabel, t } from "./i18n";
import type {
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  Lang,
  Profile,
  ReportStatus,
  Satellite,
  WizardState,
} from "./types";

function btn(text: string, callback_data: string): InlineKeyboardButton {
  return { text, callback_data };
}

export function satelliteKeyboard(
  sats: Satellite[],
  page: number,
  totalPages: number,
  lang: Lang
): InlineKeyboardMarkup {
  const rows: InlineKeyboardButton[][] = [];
  const start = page * 8;
  const slice = sats.slice(start, start + 8);
  for (const s of slice) {
    const label = s.display_name ?? s.name;
    rows.push([btn(label, `${CB.satPick}:${b64urlEncode(s.name)}`)]);
  }
  const nav: InlineKeyboardButton[] = [];
  if (page > 0) nav.push(btn("◀️", `${CB.satPage}:${page - 1}`));
  if (page < totalPages - 1) nav.push(btn("▶️", `${CB.satPage}:${page + 1}`));
  if (nav.length) rows.push(nav);
  rows.push([btn(`${t(lang, "btnSearch")}`, CB.satSearch), btn(t(lang, "btnCancel"), CB.cancel)]);
  return { inline_keyboard: rows };
}

export function statusKeyboard(
  statuses: ReportStatus[],
  lang: Lang,
  selected?: string
): InlineKeyboardMarkup {
  const rows: InlineKeyboardButton[][] = [];
  for (const s of statuses) {
    const label = statusLabel(lang, s.value, s.label) + (s.value === selected ? " ✓" : "");
    rows.push([btn(label, `${CB.statusPick}:${b64urlEncode(s.value)}`)]);
  }
  rows.push([btn(t(lang, "btnBack"), CB.back), btn(t(lang, "btnCancel"), CB.cancel)]);
  return { inline_keyboard: rows };
}

export function yearKeyboard(
  currentYear: number,
  page: number,
  totalPages: number,
  selected: number | undefined,
  lang: Lang
): InlineKeyboardMarkup {
  const years: number[] = [];
  for (let y = currentYear; y >= 2001; y--) years.push(y);
  const rows: InlineKeyboardButton[][] = [];
  const start = page * 10;
  const slice = years.slice(start, start + 10);
  let row: InlineKeyboardButton[] = [];
  for (const y of slice) {
    row.push(btn(`${y}${y === selected ? " ✓" : ""}`, `${CB.yearPick}:${y}`));
    if (row.length === 5) {
      rows.push(row);
      row = [];
    }
  }
  if (row.length) rows.push(row);
  const nav: InlineKeyboardButton[] = [];
  if (page > 0) nav.push(btn("◀️", `${CB.yearPage}:${page - 1}`));
  if (page < totalPages - 1) nav.push(btn("▶️", `${CB.yearPage}:${page + 1}`));
  if (nav.length) rows.push(nav);
  rows.push([
    btn(t(lang, "btnBack"), CB.back),
    btn(t(lang, "btnNext"), CB.next),
    btn(t(lang, "btnCancel"), CB.cancel),
  ]);
  return { inline_keyboard: rows };
}

export function monthKeyboard(selected: number | undefined, lang: Lang): InlineKeyboardMarkup {
  const rows: InlineKeyboardButton[][] = [];
  let row: InlineKeyboardButton[] = [];
  for (let m = 1; m <= 12; m++) {
    row.push(btn(`${monthName(lang, m)}${m === selected ? " ✓" : ""}`, `${CB.monthPick}:${m}`));
    if (row.length === 4) {
      rows.push(row);
      row = [];
    }
  }
  if (row.length) rows.push(row);
  rows.push([
    btn(t(lang, "btnBack"), CB.back),
    btn(t(lang, "btnNext"), CB.next),
    btn(t(lang, "btnCancel"), CB.cancel),
  ]);
  return { inline_keyboard: rows };
}

export function dayKeyboard(
  year: number,
  month: number,
  selected: number | undefined,
  lang: Lang
): InlineKeyboardMarkup {
  const days = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const rows: InlineKeyboardButton[][] = [];
  let row: InlineKeyboardButton[] = [];
  for (let d = 1; d <= days; d++) {
    row.push(btn(`${d}${d === selected ? " ✓" : ""}`, `${CB.dayPick}:${d}`));
    if (row.length === 7) {
      rows.push(row);
      row = [];
    }
  }
  if (row.length) rows.push(row);
  rows.push([
    btn(t(lang, "btnBack"), CB.back),
    btn(t(lang, "btnNext"), CB.next),
    btn(t(lang, "btnCancel"), CB.cancel),
  ]);
  return { inline_keyboard: rows };
}

export function hourKeyboard(selected: number | undefined, lang: Lang): InlineKeyboardMarkup {
  const rows: InlineKeyboardButton[][] = [];
  let row: InlineKeyboardButton[] = [];
  for (let h = 0; h < 24; h++) {
    row.push(btn(`${String(h).padStart(2, "0")}:00${h === selected ? " ✓" : ""}`, `${CB.hourPick}:${h}`));
    if (row.length === 6) {
      rows.push(row);
      row = [];
    }
  }
  if (row.length) rows.push(row);
  rows.push([
    btn(t(lang, "btnBack"), CB.back),
    btn(t(lang, "btnNext"), CB.next),
    btn(t(lang, "btnCancel"), CB.cancel),
  ]);
  return { inline_keyboard: rows };
}

export function quarterKeyboard(selected: number | undefined, lang: Lang): InlineKeyboardMarkup {
  const ranges = [":00–:15", ":15–:30", ":30–:45", ":45–:00"];
  const rows: InlineKeyboardButton[][] = [];
  let row: InlineKeyboardButton[] = [];
  ranges.forEach((r, i) => {
    row.push(btn(`${r}${i === selected ? " ✓" : ""}`, `${CB.quarterPick}:${i}`));
    if (row.length === 2) {
      rows.push(row);
      row = [];
    }
  });
  if (row.length) rows.push(row);
  rows.push([
    btn(t(lang, "btnBack"), CB.back),
    btn(t(lang, "btnNext"), CB.next),
    btn(t(lang, "btnCancel"), CB.cancel),
  ]);
  return { inline_keyboard: rows };
}

export function callsignKeyboard(
  profile: Profile,
  lang: Lang,
  mode: "start" | "choose"
): InlineKeyboardMarkup | undefined {
  if (mode === "start") return undefined;
  const rows: InlineKeyboardButton[][] = [];
  if (profile.callsign) rows.push([btn(t(lang, "callsignUseDefault", { callsign: profile.callsign }), CB.callsignUse)]);
  rows.push([
    btn(t(lang, "callsignEnterNew"), CB.callsignNew),
    btn(t(lang, "btnCancel"), CB.cancel),
  ]);
  return { inline_keyboard: rows };
}

export function gridKeyboard(
  profile: Profile,
  lang: Lang,
  mode: "start" | "choose"
): InlineKeyboardMarkup | undefined {
  if (mode === "start") return undefined;
  const rows: InlineKeyboardButton[][] = [];
  if (profile.grid) rows.push([btn(t(lang, "gridUseDefault", { grid: profile.grid }), CB.gridUse)]);
  rows.push([
    btn(t(lang, "gridEnterNew"), CB.gridNew),
    btn(t(lang, "btnCancel"), CB.cancel),
  ]);
  return { inline_keyboard: rows };
}

export function confirmKeyboard(lang: Lang): InlineKeyboardMarkup {
  return {
    inline_keyboard: [
      [
        btn(t(lang, "btnSubmit"), CB.submit),
        btn(t(lang, "btnBack"), CB.back),
        btn(t(lang, "btnCancel"), CB.cancel),
      ],
    ],
  };
}

export function langKeyboard(): InlineKeyboardMarkup {
  return {
    inline_keyboard: [
      [btn("🇺🇸 English", `${CB.langPick}:en`), btn("🇷🇺 Русский", `${CB.langPick}:ru`)],
      [btn("🇨🇳 中文", `${CB.langPick}:zh`)],
      [btn("❌", CB.cancel)],
    ],
  };
}

export function mainMenuKeyboard(lang: Lang): InlineKeyboardMarkup {
  return {
    inline_keyboard: [
      [btn(t(lang, "btnMenuReport"), "menu:report")],
      [btn(t(lang, "btnMenuLang"), "menu:lang"), btn(t(lang, "btnMenuHelp"), "menu:help")],
    ],
  };
}