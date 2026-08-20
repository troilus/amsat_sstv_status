# AMSAT Status Bot — Python backend (pybot)

Long-polling Telegram bot that submits AMSAT satellite status reports to
`https://www.amsat.org/status/api/v1` (web form at `https://www.amsat.org/status/`).
Feature-parity port of the Cloudflare Worker backend in `../tgbot`.

## Setup

1. `pip install -r requirements.txt`
2. Edit `config.json` and set `telegram_token` (or export `TELEGRAM_BOT_TOKEN`).
3. Run the bot:

   ```
   python bot.py
   ```

## Build a standalone Linux binary

The repo ships a GitHub Actions workflow (`.github/workflows/build-pybot.yml`)
that compiles the bot into a single self-contained Linux binary with PyInstaller:

1. GitHub → **Actions** → **Build pybot Linux binary** → **Run workflow**.
2. Download the `amsat-sstv-bot-linux` artifact.
3. Place `amsat_sstv_bot` and `config.json` (with `telegram_token` set) in the
   same directory on the target machine and run `./amsat_sstv_bot`. `state.json`
   is auto-created next to the binary.

A systemd unit example is provided in `amsat-sstv-bot.service`.
To build locally instead, run `bash build_linux.sh` from this directory
(creates a temporary venv and outputs `dist/amsat_sstv_bot`).

## Configuration (`config.json`)

| Key               | Default                            | Description                          |
| ----------------- | ---------------------------------- | ------------------------------------ |
| `telegram_token`  | *(empty)*                          | Bot token from @BotFather           |
| `amsat_api_base`  | `https://www.amsat.org/status/api/v1` | AMSAT Status API base           |
| `state_file`      | `state.json`                       | JSON file holding profiles/wizards/catalog cache |
| `catalog_ttl`     | `86400`                            | Satellite catalog cache TTL (seconds) |

## Flow

`/report` → satellite (paged, searchable) → status → year → month → day → hour →
15-minute period → callsign → grid → confirm → submit.

Defaults are preselected and shown with ✓: date/time = current UTC (nearest 15-min
slot); callsign/grid = last used per chat (stored in the profile). When no default
exists the bot asks for the value as a text message.

Re-submitting the same satellite + callsign + hour + 15-minute period overwrites
the previous report (useful for corrections).

Commands: `/report`, `/cancel`, `/language`, `/help`. Language defaults from the
Telegram account's `language_code` (zh/ru/en) and can be switched per chat.

## Design notes

- Pure dependency on [`python-telegram-bot`](https://python-telegram-bot.org/) ≥21
  (long polling); the AMSAT API is called with the stdlib `urllib`.
- State is a plain JSON file (`state.json`); writes are atomic (tmp + `os.replace`)
  and guarded by a `threading.Lock`. Run with `concurrent_updates=False` so wizard
  steps are handled in order.
- Callback payloads and flow are identical to `tgbot` (see `../tgbot`).