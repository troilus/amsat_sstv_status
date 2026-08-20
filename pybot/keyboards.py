# -*- coding: utf-8 -*-
"""Inline keyboard builders for the wizard steps."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from i18n import month_name, status_label, t

import base64


def b64url_encode(s):
    return base64.urlsafe_b64encode(s.encode("utf-8")).decode("ascii").rstrip("=")


def b64url_decode(s):
    pad = "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("ascii")).decode("utf-8")


def _b(text, data):
    return InlineKeyboardButton(text, callback_data=data)


def back_cancel_row(lang):
    return [_b(t(lang, "btnBack"), "bk"), _b(t(lang, "btnCancel"), "cc")]


def back_next_cancel_row(lang):
    return [_b(t(lang, "btnBack"), "bk"), _b(t(lang, "btnNext"), "nx"), _b(t(lang, "btnCancel"), "cc")]


def satellite_keyboard(sats, page, total_pages, lang):
    rows = []
    start = page * 8
    for s in sats[start : start + 8]:
        label = s.get("display_name") or s["name"]
        rows.append([_b(label, "sat:" + b64url_encode(s["name"]))])
    nav = []
    if page > 0:
        nav.append(_b("◀️", f"sp:{page - 1}"))
    if page < total_pages - 1:
        nav.append(_b("▶️", f"sp:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([_b(t(lang, "btnSearch"), "ss"), _b(t(lang, "btnCancel"), "cc")])
    return InlineKeyboardMarkup(rows)


def status_keyboard(statuses, lang, selected=None):
    rows = []
    for s in statuses:
        label = status_label(lang, s["value"], s.get("label"))
        if s["value"] == selected:
            label += " ✓"
        rows.append([_b(label, "st:" + b64url_encode(s["value"]))])
    rows.append(back_cancel_row(lang))
    return InlineKeyboardMarkup(rows)


def date_keyboard(date_str, lang):
    return InlineKeyboardMarkup(
        [
            [_b(t(lang, "dateYes", {"date": date_str}), "dty"), _b(t(lang, "dateNo"), "dtn")],
            back_cancel_row(lang),
        ]
    )


def time_keyboard(time_str, lang):
    return InlineKeyboardMarkup(
        [
            [_b(t(lang, "timeYes", {"time": time_str}), "tmy"), _b(t(lang, "timeNo"), "tmn")],
            back_cancel_row(lang),
        ]
    )


def year_keyboard(current_year, page, total_pages, selected, lang):
    years = list(range(current_year, 2000, -1))
    rows = []
    start = page * 10
    row = []
    for y in years[start : start + 10]:
        label = f"{y} ✓" if y == selected else str(y)
        row.append(_b(label, f"yr:{y}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    nav = []
    if page > 0:
        nav.append(_b("◀️", f"yp:{page - 1}"))
    if page < total_pages - 1:
        nav.append(_b("▶️", f"yp:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append(back_next_cancel_row(lang))
    return InlineKeyboardMarkup(rows)


def month_keyboard(selected, lang):
    rows = []
    row = []
    for m in range(1, 13):
        label = month_name(lang, m) + (" ✓" if m == selected else "")
        row.append(_b(label, f"mo:{m}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(back_next_cancel_row(lang))
    return InlineKeyboardMarkup(rows)


def day_keyboard(year, month, selected, lang):
    import calendar

    days = calendar.monthrange(year, month)[1]
    rows = []
    row = []
    for d in range(1, days + 1):
        label = f"{d} ✓" if d == selected else str(d)
        row.append(_b(label, f"dy:{d}"))
        if len(row) == 7:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(back_next_cancel_row(lang))
    return InlineKeyboardMarkup(rows)


def hour_keyboard(selected, lang):
    rows = []
    row = []
    for h in range(24):
        label = f"{h:02d}:00 ✓" if h == selected else f"{h:02d}:00"
        row.append(_b(label, f"hr:{h}"))
        if len(row) == 6:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(back_next_cancel_row(lang))
    return InlineKeyboardMarkup(rows)


def quarter_keyboard(selected, lang):
    ranges = [":00–:15", ":15–:30", ":30–:45", ":45–:00"]
    rows = []
    row = []
    for i, r in enumerate(ranges):
        label = r + (" ✓" if i == selected else "")
        row.append(_b(label, f"qr:{i}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(back_next_cancel_row(lang))
    return InlineKeyboardMarkup(rows)


def callsign_keyboard(profile, lang):
    if not profile.get("callsign"):
        return None
    rows = [[_b(t(lang, "callsignUseDefault", {"callsign": profile["callsign"]}), "csu")]]
    rows.append([_b(t(lang, "callsignEnterNew"), "csn"), _b(t(lang, "btnCancel"), "cc")])
    return InlineKeyboardMarkup(rows)


def grid_keyboard(profile, lang):
    if not profile.get("grid"):
        return None
    rows = [[_b(t(lang, "gridUseDefault", {"grid": profile["grid"]}), "gru")]]
    rows.append([_b(t(lang, "gridEnterNew"), "grn"), _b(t(lang, "btnCancel"), "cc")])
    return InlineKeyboardMarkup(rows)


def confirm_keyboard(lang):
    return InlineKeyboardMarkup(
        [
            [_b(t(lang, "btnSubmit"), "cfy"), _b(t(lang, "btnBack"), "bk"), _b(t(lang, "btnCancel"), "cc")],
        ]
    )


def lang_keyboard():
    return InlineKeyboardMarkup(
        [
            [_b("🇺🇸 English", "ln:en"), _b("🇷🇺 Русский", "ln:ru")],
            [_b("🇨🇳 中文", "ln:zh")],
            [_b("❌", "cc")],
        ]
    )


def main_menu_keyboard(lang):
    return InlineKeyboardMarkup(
        [
            [_b(t(lang, "btnMenuReport"), "menu:report")],
            [_b(t(lang, "btnMenuLang"), "menu:lang"), _b(t(lang, "btnMenuHelp"), "menu:help")],
        ]
    )