export const KV_KEYS = {
  wizard: "wizard:",
  profile: "profile:",
  catalog: "catalog",
} as const;

export const CATALOG_TTL = 86400;
export const WIZARD_TTL = 1800;

export const SAT_PAGE_SIZE = 8;
export const YEAR_MIN = 2001;
export const YEAR_PAGE_SIZE = 10;

export const CB = {
  satPage: "sp",
  satPick: "sat",
  satSearch: "ss",
  satList: "sl",
  statusPick: "st",
  yearPage: "yp",
  yearPick: "yr",
  monthPick: "mo",
  dayPick: "dy",
  hourPick: "hr",
  quarterPick: "qr",
  callsignUse: "csu",
  callsignNew: "csn",
  gridUse: "gru",
  gridNew: "grn",
  next: "nx",
  back: "bk",
  cancel: "cc",
  submit: "cfy",
  langPick: "ln",
} as const;

export const DEFAULT_STATUSES: { value: string; label: string }[] = [
  { value: "Heard", label: "Satellite active" },
  { value: "Telemetry Only", label: "Telemetry or beacon only" },
  { value: "Not Heard", label: "No signal" },
  { value: "Crew Active", label: "ISS crew voice active" },
];

export function b64urlEncode(s: string): string {
  const bytes = new TextEncoder().encode(s);
  let bin = "";
  bytes.forEach((b) => (bin += String.fromCharCode(b)));
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function b64urlDecode(s: string): string {
  let b = s.replace(/-/g, "+").replace(/_/g, "/");
  while (b.length % 4) b += "=";
  const bin = atob(b);
  const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

export function pad2(n: number): string {
  return String(n).padStart(2, "0");
}
