# -*- coding: utf-8 -*-
"""Translations for the three bot languages (en / ru / zh)."""

LANGS = ("en", "ru", "zh")

MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "ru": ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"],
    "zh": ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
}

STRINGS = {
    "en": {
        "welcome": (
            "🛰 Welcome to the AMSAT Status Bot.\n\n"
            "Report the current status of amateur satellites you hear, straight to amsat.org.\n\n"
            "Use /report to submit a report, /language to switch language."
        ),
        "help": (
            "🛰 AMSAT Status Bot\n\n"
            "This bot submits satellite status reports to the AMSAT Satellite Status website "
            "(https://www.amsat.org/status/).\n\n"
            "Commands:\n/report — start a new status report\n"
            "/language — choose your language\n"
            "/cancel — cancel the current report\n"
            "/help — show this message\n\n"
            "Note: re-submitting the same satellite, callsign, hour and 15-minute period "
            "overwrites the previous report (useful to correct mistakes)."
        ),
        "langPrompt": "🌐 Select your language / Выберите язык / 选择语言:",
        "langDone": "✅ Language set to English.",
        "reportStart": "Let's submit a report.\n1️⃣ Select the satellite you heard:",
        "noActive": "No active report. Use /report to start.",
        "cancelled": "❌ Report cancelled.",
        "satPrompt": "1️⃣ Select satellite (page {page}/{total}):\nTap 🔍 to search by name.",
        "satSearchHint": "Send the satellite name to search, e.g. \"AO-91\" or \"ISS\".\nSend /cancel to abort.",
        "satNoMatch": "No satellites match \"{q}\". Send another name or tap ⬅️ to go back.",
        "statusPrompt": "2️⃣ What did you observe?",
        "datePrompt": "3️⃣ Report date:\nIs it today ({date})?",
        "dateYes": "✓ Yes, today ({date})",
        "dateNo": "Different date",
        "timePrompt": "4️⃣ Report time (UTC):\nIs it the nearest 15-minute period ({time})?",
        "timeYes": "✓ Yes, {time}",
        "timeNo": "Different time",
        "yearPrompt": "Select year:",
        "monthPrompt": "Select month:",
        "dayPrompt": "Select day:",
        "hourPrompt": "Select hour (UTC):",
        "quarterPrompt": "Select 15-minute period (UTC):",
        "callsignPrompt": "5️⃣ Your callsign:\nSend your callsign as a text message.",
        "callsignUseDefault": "Use {callsign}",
        "callsignEnterNew": "Enter a different callsign",
        "callsignInvalid": "⚠️ Invalid callsign. Use 1–10 letters/digits, optionally followed by /suffix.",
        "gridPrompt": "6️⃣ Your grid square:\nSend a Maidenhead locator as a text message (e.g. OM80 or OM80MA).",
        "gridUseDefault": "Use {grid}",
        "gridEnterNew": "Enter a different grid square",
        "gridInvalid": "⚠️ Invalid grid square. Use a Maidenhead locator like OM80 (4–6 chars, e.g. OM80MA).",
        "confirmTitle": "📋 Confirm your report:",
        "confirmNote": "\n\n⚠️ Re-submitting the same satellite, callsign, hour and 15-minute period will overwrite the previous report (for corrections).",
        "submitOk": "✅ Report submitted successfully!",
        "submitOkBody": "{sat} · {status} · {time}Z · {callsign} · {grid}",
        "submitErr": "❌ Failed to submit report: {err}",
        "submitFuture": "⚠️ The selected time is in the future. Go back and pick an earlier time.",
        "btnNext": "Next ➡️",
        "btnBack": "⬅️ Back",
        "btnCancel": "❌ Cancel",
        "btnSubmit": "✅ Submit",
        "btnPrev": "◀",
        "btnSearch": "🔍 Search",
        "btnMenuReport": "📝 Submit report",
        "btnMenuLang": "🌐 Language",
        "btnMenuHelp": "❓ Help",
        "statusLabels": {
            "Heard": "Heard (active)",
            "Telemetry Only": "TLM/Beacon only",
            "Not Heard": "Not heard",
            "Crew Active": "ISS crew active",
        },
        "labelSat": "Satellite",
        "labelStatus": "Status",
        "labelDate": "Date",
        "labelTime": "Time (UTC)",
        "labelCallsign": "Callsign",
        "labelGrid": "Grid square",
    },
    "ru": {
        "welcome": (
            "🛰 Добро пожаловать в AMSAT Status Bot.\n\n"
            "Сообщайте текущий статус любительских спутников прямо на amsat.org.\n\n"
            "Используйте /report для отчёта, /language для смены языка."
        ),
        "help": (
            "🛰 AMSAT Status Bot\n\n"
            "Этот бот отправляет отчёты о статусе спутников на сайт AMSAT Satellite Status "
            "(https://www.amsat.org/status/).\n\n"
            "Команды:\n/report — новый отчёт о статусе\n"
            "/language — выбрать язык\n"
            "/cancel — отменить текущий отчёт\n"
            "/help — показать справку\n\n"
            "Примечание: повторная отправка того же спутника, позывного, часа и 15-минутного "
            "периода заменяет предыдущий отчёт (для исправления ошибок)."
        ),
        "langPrompt": "🌐 Выберите язык / Select language / 选择语言:",
        "langDone": "✅ Язык установлен: Русский.",
        "reportStart": "Создаём отчёт.\n1️⃣ Выберите спутник, который вы слышали:",
        "noActive": "Нет активного отчёта. Используйте /report.",
        "cancelled": "❌ Отчёт отменён.",
        "satPrompt": "1️⃣ Выберите спутник (стр. {page}/{total}):\nНажмите 🔍 для поиска по имени.",
        "satSearchHint": "Отправьте название спутника для поиска, напр. \"AO-91\" или \"ISS\".\nОтправьте /cancel для отмены.",
        "satNoMatch": "Спутники по запросу \"{q}\" не найдены. Отправьте другое имя или нажмите ⬅️.",
        "statusPrompt": "2️⃣ Что вы наблюдали?",
        "datePrompt": "3️⃣ Дата отчёта:\nСегодня ({date})?",
        "dateYes": "✓ Да, сегодня ({date})",
        "dateNo": "Другая дата",
        "timePrompt": "4️⃣ Время отчёта (UTC):\nЭто ближайший 15-минутный период ({time})?",
        "timeYes": "✓ Да, {time}",
        "timeNo": "Другое время",
        "yearPrompt": "Выберите год:",
        "monthPrompt": "Выберите месяц:",
        "dayPrompt": "Выберите день:",
        "hourPrompt": "Выберите час (UTC):",
        "quarterPrompt": "Выберите 15-минутный период (UTC):",
        "callsignPrompt": "5️⃣ Ваш позывной:\nОтправьте позывной текстом.",
        "callsignUseDefault": "Использовать {callsign}",
        "callsignEnterNew": "Ввести другой позывной",
        "callsignInvalid": "⚠️ Неверный позывной. 1–10 букв/цифр, опционально через /.",
        "gridPrompt": "6️⃣ Ваш квадрат:\nОтправьте локатор Maidenhead текстом (напр. KO85 или KO85XX).",
        "gridUseDefault": "Использовать {grid}",
        "gridEnterNew": "Ввести другой квадрат",
        "gridInvalid": "⚠️ Неверный квадрат. Локатор Maidenhead из 4–6 символов, напр. KO85.",
        "confirmTitle": "📋 Подтвердите отчёт:",
        "confirmNote": "\n\n⚠️ Повторная отправка того же спутника, позывного, часа и 15-минутного периода заменит предыдущий отчёт (для исправления ошибок).",
        "submitOk": "✅ Отчёт успешно отправлен!",
        "submitOkBody": "{sat} · {status} · {time}Z · {callsign} · {grid}",
        "submitErr": "❌ Не удалось отправить отчёт: {err}",
        "submitFuture": "⚠️ Выбранное время в будущем. Вернитесь назад и выберите более раннее время.",
        "btnNext": "Далее ➡️",
        "btnBack": "⬅️ Назад",
        "btnCancel": "❌ Отмена",
        "btnSubmit": "✅ Отправить",
        "btnPrev": "◀",
        "btnSearch": "🔍 Поиск",
        "btnMenuReport": "📝 Отправить отчёт",
        "btnMenuLang": "🌐 Язык",
        "btnMenuHelp": "❓ Справка",
        "statusLabels": {
            "Heard": "Слышал (активен)",
            "Telemetry Only": "Только TLM/маяк",
            "Not Heard": "Не слышал",
            "Crew Active": "Экипаж МКС активен",
        },
        "labelSat": "Спутник",
        "labelStatus": "Статус",
        "labelDate": "Дата",
        "labelTime": "Время (UTC)",
        "labelCallsign": "Позывной",
        "labelGrid": "Квадрат",
    },
    "zh": {
        "welcome": (
            "🛰 欢迎使用 AMSAT 状态上报机器人。\n\n"
            "把你听到的业余卫星当前状态直接上报到 amsat.org。\n\n"
            "使用 /report 上报，使用 /language 切换语言。"
        ),
        "help": (
            "🛰 AMSAT 状态机器人\n\n"
            "该机器人向 AMSAT 卫星状态网站(https://www.amsat.org/status/)提交卫星状态报告。\n\n"
            "命令：\n/report — 开始新的状态上报\n"
            "/language — 选择语言\n"
            "/cancel — 取消当前上报\n"
            "/help — 显示帮助\n\n"
            "注意：对同一卫星、呼号、小时和 15 分钟时段重复上报会覆盖之前的报告(可用于纠正错误)。"
        ),
        "langPrompt": "🌐 选择语言 / Select language / Выберите язык:",
        "langDone": "✅ 语言已设置为中文。",
        "reportStart": "开始上报。\n1️⃣ 请选择你听到的卫星：",
        "noActive": "当前没有进行中的上报，请使用 /report 开始。",
        "cancelled": "❌ 已取消上报。",
        "satPrompt": "1️⃣ 请选择卫星(第 {page}/{total} 页)：\n点击 🔍 可按名称搜索。",
        "satSearchHint": "请发送要搜索的卫星名称，例如 \"AO-91\" 或 \"ISS\"。\n发送 /cancel 可取消。",
        "satNoMatch": "没有找到匹配 \"{q}\" 的卫星。请换一个名称，或点击 ⬅️ 返回。",
        "statusPrompt": "2️⃣ 你观察到了什么？",
        "datePrompt": "3️⃣ 上报日期：\n是今天 {date} 吗？",
        "dateYes": "✓ 是，今天 {date}",
        "dateNo": "改日期",
        "timePrompt": "4️⃣ 上报时间(UTC)：\n是最近的 15 分钟时段 {time} 吗？",
        "timeYes": "✓ 是，{time}",
        "timeNo": "改时间",
        "yearPrompt": "请选择年份：",
        "monthPrompt": "请选择月份：",
        "dayPrompt": "请选择日期：",
        "hourPrompt": "请选择小时(UTC)：",
        "quarterPrompt": "请选择 15 分钟时段(UTC)：",
        "callsignPrompt": "5️⃣ 你的呼号：\n请以文字消息发送你的呼号。",
        "callsignUseDefault": "使用 {callsign}",
        "callsignEnterNew": "输入其他呼号",
        "callsignInvalid": "⚠️ 呼号无效。请使用 1–10 位字母/数字，可带 /后缀。",
        "gridPrompt": "6️⃣ 你的网格坐标：\n请以文字消息发送 Maidenhead 网格(例如 OM80 或 OM80MA)。",
        "gridUseDefault": "使用 {grid}",
        "gridEnterNew": "输入其他网格",
        "gridInvalid": "⚠️ 网格坐标无效。请使用 Maidenhead 网格(4–6 位，例如 OM80)。",
        "confirmTitle": "📋 请确认你的上报：",
        "confirmNote": "\n\n⚠️ 对同一卫星、呼号、小时和 15 分钟时段重复上报将覆盖之前的报告(用于纠正错误)。",
        "submitOk": "✅ 上报成功！",
        "submitOkBody": "{sat} · {status} · {time}Z · {callsign} · {grid}",
        "submitErr": "❌ 上报失败：{err}",
        "submitFuture": "⚠️ 所选时间在未来，请返回并选择更早的时间。",
        "btnNext": "下一步 ➡️",
        "btnBack": "⬅️ 返回",
        "btnCancel": "❌ 取消",
        "btnSubmit": "✅ 提交",
        "btnPrev": "◀",
        "btnSearch": "🔍 搜索",
        "btnMenuReport": "📝 提交上报",
        "btnMenuLang": "🌐 语言",
        "btnMenuHelp": "❓ 帮助",
        "statusLabels": {
            "Heard": "听到(活跃)",
            "Telemetry Only": "仅遥测/信标",
            "Not Heard": "未听到",
            "Crew Active": "ISS 乘员活跃",
        },
        "labelSat": "卫星",
        "labelStatus": "状态",
        "labelDate": "日期",
        "labelTime": "时间(UTC)",
        "labelCallsign": "呼号",
        "labelGrid": "网格坐标",
    },
}


def detect_lang(code):
    """Map a Telegram language_code to one of the supported languages (default en)."""
    if not code:
        return "en"
    c = code.lower()
    if c.startswith("zh"):
        return "zh"
    if c.startswith("ru"):
        return "ru"
    return "en"


def t(lang, key, params=None):
    """Translate key for lang, substituting {name} placeholders."""
    d = STRINGS.get(lang, STRINGS["en"])
    s = d.get(key, "")
    if params:
        for k, v in params.items():
            s = s.replace("{%s}" % k, str(v))
    return s


def month_name(lang, m):
    return MONTHS.get(lang, MONTHS["en"])[m - 1]


def status_label(lang, value, fallback=None):
    d = STRINGS.get(lang, STRINGS["en"])
    return d["statusLabels"].get(value, fallback or value)
