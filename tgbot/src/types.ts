export type Lang = "en" | "ru" | "zh";

export type StepId =
  | "satellite"
  | "status"
  | "year"
  | "month"
  | "day"
  | "hour"
  | "quarter"
  | "callsign"
  | "grid"
  | "confirm";

export interface Env {
  TELEGRAM_BOT_TOKEN: string;
  WEBHOOK_SECRET: string;
  AMSAT_API_BASE: string;
  SESSIONS: KVNamespace;
}

export interface Profile {
  callsign?: string;
  grid?: string;
  lang: Lang;
}

export interface WizardState {
  step: StepId;
  chatId: number;
  lastMsgId?: number;
  satPage: number;
  yearPage: number;
  search: boolean;
  searchQuery?: string;
  awaiting?: "callsign" | "grid";
  satellite?: string;
  satelliteDisplay?: string;
  status?: string;
  year?: number;
  month?: number;
  day?: number;
  hour?: number;
  quarter?: number;
  callsign?: string;
  grid?: string;
  createdAt: number;
}

export interface Satellite {
  id: number;
  name: string;
  display_name?: string;
  report_count?: number;
  latest_reported_time?: string | null;
}

export interface ReportStatus {
  value: string;
  label: string;
}

export interface InlineKeyboardButton {
  text: string;
  callback_data?: string;
  url?: string;
}

export interface InlineKeyboardMarkup {
  inline_keyboard: InlineKeyboardButton[][];
}

export interface TelegramUpdate {
  update_id: number;
  message?: TelegramMessage;
  callback_query?: {
    id: string;
    from: { id: number; language_code?: string };
    message?: { chat: { id: number }; message_id: number };
    data: string;
  };
}

export interface TelegramMessage {
  message_id: number;
  from?: { id: number; language_code?: string };
  chat: { id: number };
  text?: string;
  entities?: { type: string; offset: number; length: number }[];
}
