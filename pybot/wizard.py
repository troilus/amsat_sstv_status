# -*- coding: utf-8 -*-
"""Wizard state machine and command/message/callback handlers.

Flow: satellite -> status -> year -> month -> day -> hour -> quarter -> callsign -> grid -> confirm.
Date/time default to the current UTC moment; callsign/grid default to the last used values.
"""

import calendar
import re
import time
from datetime import datetime, timezone

import amsat
import keyboards
from i18n import t
from state import Store

CALLSIGN_RE = re.compile(r"^[A-Za-z0-9]{1,10}(?:/[A-Za-z0-9]{1,6})?$")
GRID_RE = re.compile(r"^[A-Ra-r]{2}[0-9]{2}(?:[A-Xa-x]{2}(?:[0-9]{2})?)?$")

SAT_PAGE_SIZE = 8
YEAR_MIN = 2001
YEAR_PAGE_SIZE = 10
FUTURE_SLACK_S = 60

NEXT = {
    "satellite": "status",
    "status": "date",
    "date": "time",
    "year": "month",
    "month": "day",
    "day": "time",
    "time": "callsign",
    "hour": "quarter",
    "quarter": "callsign",
    "callsign": "grid",
    "grid": "confirm",
    "confirm": "confirm",
}

PREV = {
    "satellite": "satellite",
    "status": "satellite",
    "date": "status",
    "year": "date",
    "month": "year",
    "day": "month",
    "time": "date",
    "hour": "time",
    "quarter": "hour",
    "callsign": "quarter",
    "grid": "callsign",
    "confirm": "grid",
}


def _now_parts():
    n = datetime.now(timezone.utc)
    return {
        "year": n.year,
        "month": n.month,
        "day": n.day,
        "hour": n.hour,
        "quarter": min(3, round(n.minute / 15)),
    }


def _page_count(total, size):
    return max(1, -(-total // size))


def _filtered_sats(catalog, q):
    query = (q or "").strip().lower()
    if not query:
        return catalog
    return [s for s in catalog if query in s["name"].lower() or query in (s.get("display_name") or "").lower()]


def _report_time(state):
    y = state.get("year") or YEAR_MIN
    mo, d, h = state.get("month") or 1, state.get("day") or 1, state.get("hour") or 0
    mi = (state.get("quarter") or 0) * 15
    return "{}".format(f"{y:04d}-{mo:02d}-{d:02d}"), "{}".format(f"{h:02d}:{mi:02d}")


def _reported_at(state):
    date, tpart = _report_time(state)
    return f"{date}T{tpart}:00Z"


def _is_future(state):
    y = state.get("year") or YEAR_MIN
    mo, d, h = state.get("month") or 1, state.get("day") or 1, state.get("hour") or 0
    mi = (state.get("quarter") or 0) * 15
    when = datetime(y, mo, d, h, mi, tzinfo=timezone.utc).timestamp()
    return when > time.time() + FUTURE_SLACK_S


def _new_wizard(chat_id):
    p = _now_parts()
    return {
        "step": "satellite",
        "chat_id": chat_id,
        "msg_id": None,
        "sat_page": 0,
        "year_page": 0,
        "search": False,
        "search_query": None,
        "awaiting": None,
        "satellite": None,
        "satellite_display": None,
        "status": None,
        "year": p["year"],
        "month": p["month"],
        "day": p["day"],
        "hour": p["hour"],
        "quarter": p["quarter"],
        "callsign": None,
        "grid": None,
        "created_at": time.time(),
    }


def _step_text(state, ctx):
    lang = ctx["lang"]
    step = state["step"]
    if step == "satellite":
        if state.get("search_query"):
            matches = _filtered_sats(ctx["catalog"], state["search_query"])
            if not matches:
                return "{}\n\n{}".format(t(lang, "satNoMatch", {"q": state["search_query"]}), t(lang, "satSearchHint"))
            return t(lang, "satPrompt", {"page": state["sat_page"] + 1, "total": _page_count(len(matches), SAT_PAGE_SIZE)})
        if state.get("search"):
            return t(lang, "satSearchHint")
        return t(lang, "satPrompt", {"page": state["sat_page"] + 1, "total": _page_count(len(ctx["catalog"]), SAT_PAGE_SIZE)})
    if step == "date":
        date, _ = _report_time(state)
        return t(lang, "datePrompt", {"date": date})
    if step == "time":
        _, tpart = _report_time(state)
        return t(lang, "timePrompt", {"time": tpart})
    if step in ("status", "year", "month", "day", "hour", "quarter", "callsign", "grid"):
        return t(lang, step + "Prompt")
    if step == "confirm":
        date, tpart = _report_time(state)
        return "\n".join(
            [
                t(lang, "confirmTitle"),
                "",
                "{}: {}".format(t(lang, "labelSat"), state.get("satellite_display") or state.get("satellite")),
                "{}: {}".format(t(lang, "labelStatus"), state.get("status")),
                "{}: {}".format(t(lang, "labelDate"), date),
                "{}: {} UTC".format(t(lang, "labelTime"), tpart),
                "{}: {}".format(t(lang, "labelCallsign"), state.get("callsign")),
                "{}: {}".format(t(lang, "labelGrid"), state.get("grid")),
                t(lang, "confirmNote"),
            ]
        )
    return ""


def _step_keyboard(state, ctx):
    lang = ctx["lang"]
    step = state["step"]
    if step == "satellite":
        lst = _filtered_sats(ctx["catalog"], state.get("search_query")) if state.get("search_query") else ctx["catalog"]
        return keyboards.satellite_keyboard(lst, state["sat_page"], _page_count(len(lst), SAT_PAGE_SIZE), lang)
    if step == "status":
        return keyboards.status_keyboard(ctx["statuses"], lang)
    if step == "date":
        date, _ = _report_time(state)
        return keyboards.date_keyboard(date, lang)
    if step == "time":
        _, tpart = _report_time(state)
        return keyboards.time_keyboard(tpart, lang)
    if step == "year":
        cur = state.get("year") or datetime.now(timezone.utc).year
        return keyboards.year_keyboard(cur, state["year_page"], _page_count(cur - YEAR_MIN + 1, YEAR_PAGE_SIZE), state.get("year"), lang)
    if step == "month":
        return keyboards.month_keyboard(state.get("month"), lang)
    if step == "day":
        return keyboards.day_keyboard(state.get("year") or datetime.now(timezone.utc).year, state.get("month") or 1, state.get("day"), lang)
    if step == "hour":
        return keyboards.hour_keyboard(state.get("hour"), lang)
    if step == "quarter":
        return keyboards.quarter_keyboard(state.get("quarter"), lang)
    if step == "callsign":
        return None if state.get("awaiting") else keyboards.callsign_keyboard(ctx["profile"], lang)
    if step == "grid":
        return None if state.get("awaiting") else keyboards.grid_keyboard(ctx["profile"], lang)
    if step == "confirm":
        return keyboards.confirm_keyboard(lang)
    return None


async def _render(update, context, state, ctx):
    text = _step_text(state, ctx)
    kb = _step_keyboard(state, ctx)
    if state.get("msg_id"):
        try:
            await context.bot.edit_message_text(text, chat_id=state["chat_id"], message_id=state["msg_id"], reply_markup=kb)
            return
        except Exception:
            pass
    msg = await update.effective_message.reply_text(text, reply_markup=kb)
    state["msg_id"] = msg.message_id


async def _load_ctx(context, update, chat_id):
    store = context.bot_data["store"]
    api_base = context.bot_data["api_base"]
    catalog_ttl = context.bot_data["catalog_ttl"]
    profile = store.get_profile(chat_id)
    lang = profile.get("lang")
    if not lang:
        from i18n import detect_lang

        u = update.effective_user
        lang = detect_lang(getattr(u, "language_code", None))
    catalog = amsat.get_catalog(store, api_base, catalog_ttl)
    statuses = amsat.get_statuses(api_base)
    return {"store": store, "profile": profile, "lang": lang, "catalog": catalog, "statuses": statuses}


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def cmd_start(update, context):
    chat = update.effective_chat.id
    ctx = await _load_ctx(context, update, chat)
    await update.effective_message.reply_text(t(ctx["lang"], "welcome"), reply_markup=keyboards.main_menu_keyboard(ctx["lang"]))


async def cmd_help(update, context):
    chat = update.effective_chat.id
    ctx = await _load_ctx(context, update, chat)
    await update.effective_message.reply_text(t(ctx["lang"], "help"))


async def cmd_language(update, context):
    ctx = await _load_ctx(context, update, update.effective_chat.id)
    await update.effective_message.reply_text(t(ctx["lang"], "langPrompt"), reply_markup=keyboards.lang_keyboard())


async def cmd_cancel(update, context):
    chat = update.effective_chat.id
    store = context.bot_data["store"]
    profile = store.get_profile(chat)
    lang = profile.get("lang") or "en"
    state = store.get_wizard(chat)
    msg = t(lang, "cancelled")
    if state and state.get("msg_id"):
        try:
            await context.bot.edit_message_text(msg, chat_id=chat, message_id=state["msg_id"])
        except Exception:
            await update.effective_message.reply_text(msg)
    else:
        await update.effective_message.reply_text(msg)
    store.clear_wizard(chat)


async def cmd_report(update, context):
    chat = update.effective_chat.id
    store = context.bot_data["store"]
    state = _new_wizard(chat)
    store.save_wizard(state)
    ctx = await _load_ctx(context, update, chat)
    await _render(update, context, state, ctx)
    store.save_wizard(state)


# ---------------------------------------------------------------------------
# Text message handler (typed input: search term / callsign / grid)
# ---------------------------------------------------------------------------

async def on_message(update, context):
    chat = update.effective_chat.id
    store = context.bot_data["store"]
    text = (update.effective_message.text or "").strip()
    state = store.get_wizard(chat)
    if state is None:
        ctx = await _load_ctx(context, update, chat)
        await update.effective_message.reply_text(t(ctx["lang"], "noActive"), reply_markup=keyboards.main_menu_keyboard(ctx["lang"]))
        return
    ctx = await _load_ctx(context, update, chat)

    if state["step"] == "satellite" and (state.get("search") or state.get("search_query")):
        state["search"] = True
        state["search_query"] = text
        state["sat_page"] = 0
        store.save_wizard(state)
        await _render(update, context, state, ctx)
        store.save_wizard(state)
        return

    if state["step"] == "callsign":
        v = text.upper().replace(" ", "")
        if not CALLSIGN_RE.match(v):
            await _reply_or_edit(update, context, state, t(ctx["lang"], "callsignInvalid"))
            return
        state["callsign"] = v
        _enter_step(state, ctx["profile"], "grid")
        store.save_wizard(state)
        await _render(update, context, state, ctx)
        store.save_wizard(state)
        return

    if state["step"] == "grid":
        v = text.upper()
        if not GRID_RE.match(v):
            await _reply_or_edit(update, context, state, t(ctx["lang"], "gridInvalid"))
            return
        state["grid"] = v
        state["step"] = "confirm"
        state["awaiting"] = None
        store.save_wizard(state)
        await _render(update, context, state, ctx)
        store.save_wizard(state)
        return

    await update.effective_message.reply_text(t(ctx["lang"], "noActive"), reply_markup=keyboards.main_menu_keyboard(ctx["lang"]))


async def _reply_or_edit(update, context, state, text):
    if state.get("msg_id"):
        try:
            await context.bot.edit_message_text(text, chat_id=state["chat_id"], message_id=state["msg_id"])
            return
        except Exception:
            pass
    await update.effective_message.reply_text(text)


def _enter_step(state, profile, step):
    """Move into a step; mark awaiting when no profile default exists for typed steps."""
    state["step"] = step
    state["awaiting"] = None
    if step == "callsign" and not profile.get("callsign"):
        state["awaiting"] = "callsign"
        return True
    if step == "grid" and not profile.get("grid"):
        state["awaiting"] = "grid"
        return True
    return False


# ---------------------------------------------------------------------------
# Callback handler
# ---------------------------------------------------------------------------

async def _on_submit(update, context, ctx, state, chat, store):
    if (
        not state.get("satellite")
        or not state.get("status")
        or not state.get("callsign")
        or not state.get("grid")
        or state.get("year") is None
        or state.get("month") is None
        or state.get("day") is None
    ):
        await _reply_or_edit(update, context, state, t(ctx["lang"], "submitErr", {"err": "incomplete report"}))
        return
    if _is_future(state):
        await _reply_or_edit(update, context, state, t(ctx["lang"], "submitFuture"))
        return
    payload = {
        "name": state["satellite"],
        "report": state["status"],
        "callsign": state["callsign"],
        "grid_square": state["grid"],
        "reported_at": _reported_at(state),
    }
    ok, message = amsat.submit_report(context.bot_data["api_base"], payload)
    if ok:
        profile = store.get_profile(chat)
        profile["callsign"] = state["callsign"]
        profile["grid"] = state["grid"]
        store.save_profile(chat, profile)
        _, tpart = _report_time(state)
        body = t(
            ctx["lang"],
            "submitOkBody",
            {"sat": state.get("satellite_display") or state["satellite"], "status": state["status"], "time": tpart, "callsign": state["callsign"], "grid": state["grid"]},
        )
        await _reply_or_edit(update, context, state, "{}\n\n{}".format(t(ctx["lang"], "submitOk"), body))
        store.clear_wizard(chat)
    else:
        await _reply_or_edit(update, context, state, t(ctx["lang"], "submitErr", {"err": message}))
    return


async def on_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat = update.effective_chat.id
    store = context.bot_data["store"]

    if data.startswith("menu:"):
        action = data.split(":", 1)[1]
        if action == "report":
            await cmd_report(update, context)
        elif action == "lang":
            await cmd_language(update, context)
        elif action == "help":
            await cmd_help(update, context)
        return

    ctx = await _load_ctx(context, update, chat)

    if data.startswith("ln:"):
        lang = data.split(":", 1)[1]
        profile = store.get_profile(chat)
        profile["lang"] = lang
        store.save_profile(chat, profile)
        try:
            await query.edit_message_text(t(lang, "langDone"), reply_markup=keyboards.main_menu_keyboard(lang))
        except Exception:
            await update.effective_message.reply_text(t(lang, "langDone"), reply_markup=keyboards.main_menu_keyboard(lang))
        return

    state = store.get_wizard(chat)
    if data == "cc":
        msg = t(ctx["lang"], "cancelled")
        try:
            await query.edit_message_text(msg)
        except Exception:
            await update.effective_message.reply_text(msg)
        store.clear_wizard(chat)
        return

    if state is None:
        await update.effective_message.reply_text(t(ctx["lang"], "noActive"), reply_markup=keyboards.main_menu_keyboard(ctx["lang"]))
        return

    render = lambda: _render(update, context, state, ctx)

    if data == "cfy":
        await _on_submit(update, context, ctx, state, chat, store)
        return

    if data == "nx":
        n = NEXT[state["step"]]
        if n != state["step"]:
            _enter_step(state, ctx["profile"], n)
            store.save_wizard(state)
            await render()
            store.save_wizard(state)
        return

    if data == "bk":
        if state["step"] == "satellite" and (state.get("search") or state.get("search_query")):
            state["search"] = False
            state["search_query"] = None
            state["sat_page"] = 0
        else:
            prev = PREV[state["step"]]
            state["step"] = prev
            state["awaiting"] = None
            if prev in ("callsign", "grid") and not ctx["profile"].get("callsign" if prev == "callsign" else "grid"):
                state["awaiting"] = prev
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data == "ss":
        if state.get("search_query"):
            state["search"] = False
            state["search_query"] = None
        else:
            state["search"] = True
            state["search_query"] = None
        state["sat_page"] = 0
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data == "csu":
        if ctx["profile"].get("callsign"):
            state["callsign"] = ctx["profile"]["callsign"]
            _enter_step(state, ctx["profile"], "grid")
        else:
            state["awaiting"] = "callsign"
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data == "csn":
        state["awaiting"] = "callsign"
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data == "gru":
        if ctx["profile"].get("grid"):
            state["grid"] = ctx["profile"]["grid"]
            state["step"] = "confirm"
            state["awaiting"] = None
        else:
            state["awaiting"] = "grid"
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data == "grn":
        state["awaiting"] = "grid"
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data.startswith("sp:"):
        state["sat_page"] = int(data.split(":")[1])
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data.startswith("sat:"):
        name = keyboards.b64url_decode(data.split(":", 1)[1])
        sat = next((s for s in ctx["catalog"] if s["name"] == name), None)
        if not sat:
            return
        state["satellite"] = sat["name"]
        state["satellite_display"] = sat.get("display_name") or sat["name"]
        state["search"] = False
        state["search_query"] = None
        _enter_step(state, ctx["profile"], "status")
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data.startswith("st:"):
        state["status"] = keyboards.b64url_decode(data.split(":", 1)[1])
        _enter_step(state, ctx["profile"], "date")
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data == "dty":
        state["step"] = "time"
        state["awaiting"] = None
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data == "dtn":
        state["step"] = "year"
        state["year_page"] = 0
        state["awaiting"] = None
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data == "tmy":
        _enter_step(state, ctx["profile"], "callsign")
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data == "tmn":
        state["step"] = "hour"
        state["awaiting"] = None
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data.startswith("yp:"):
        state["year_page"] = int(data.split(":")[1])
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data.startswith("yr:"):
        state["year"] = int(data.split(":")[1])
        state["step"] = "month"
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data.startswith("mo:"):
        state["month"] = int(data.split(":")[1])
        state["step"] = "day"
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data.startswith("dy:"):
        state["day"] = int(data.split(":")[1])
        state["step"] = "time"
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data.startswith("hr:"):
        state["hour"] = int(data.split(":")[1])
        state["step"] = "quarter"
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return

    if data.startswith("qr:"):
        state["quarter"] = int(data.split(":")[1])
        _enter_step(state, ctx["profile"], "callsign")
        store.save_wizard(state)
        await render()
        store.save_wizard(state)
        return