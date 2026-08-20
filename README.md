# AMSAT SSTV Status

业余无线电卫星工具的集合——围绕 [AMSAT Satellite Status](https://www.amsat.org/status/) 网站及其公共 API（`https://www.amsat.org/status/api/v1`）构建的一组工具集。

A collection of amateur-radio satellite tools built around the [AMSAT Satellite Status](https://www.amsat.org/status/) website and its public API (`https://www.amsat.org/status/api/v1`).

## Overview / 概览

| 工具 | 说明 | 位置 |
| --- | --- | --- |
| Telegram 状态上报机器人 | 在 Telegram 聊天内引导用户提交卫星状态报告到 amsat.org（含三语言） | [`tgbot/`](tgbot/README.md)（Cloudflare Workers）· [`pybot/`](pybot/README.md)（自托管 Python） |
| SSTV 状态监控器 | 轮询 API，当 SSTV 卫星收到 Heard 报告时推送通知（Bark / ntfy） | `amsat_sstv_monitor.py`（本地）· `amsat_sstv_monitor_action.py`（GitHub Actions） |

## Features / 特性

- **Telegram 机器人**（两种后端，回调数据兼容一致，向导步骤略有差异）：
  - 引导式向导：卫星 → 状态 → 日期/时间 → 呼号 → 网格 → 确认提交。
  - 默认值带 ✓：日期=今天（UTC），时间=最近的 15 分钟时段（UTC），呼号/网格=该对话上次使用的值。
  - 三语言：**English / Русский / 中文**，可按会话切换（`/language`），默认跟随 Telegram 账户语言。
  - 重复提交同一卫星 + 呼号 + 小时 + 15 分钟时段会覆盖之前的报告（与官方网页表单行为一致，用于修正错误）。
- **SSTV 监控器**：仅用 Python 标准库，无第三方依赖；支持 Bark 与 ntfy.sh 两种推送渠道；可交互查看各 SSTV 卫星最近 Heard 情况。

## Directory layout / 目录结构

```
amsat_sstv_status/
├── .github/workflows/
│   ├── amsat-sstv-monitor.yml        # SSTV 监控（GitHub Actions 版，目前仅手动触发）
│   ├── amsat-sstv-monitor-test.yml   # 监控器手动测试
│   └── build-pybot.yml               # 用 PyInstaller 构建 pybot Linux 单文件二进制
├── tgbot/                            # Telegram 机器人 · Cloudflare Workers + TypeScript 版
├── pybot/                            # Telegram 机器人 · Python 长轮询版（功能对等移植）
├── amsat_sstv_monitor.py             # SSTV 监控器（本地运行版）
├── amsat_sstv_monitor_action.py      # SSTV 监控器（GitHub Actions 版，复用监控器核心）
├── config.json                       # 监控器配置（不入库，见 .gitignore）
└── seen.json                         # 监控器去重状态（自动生成）
```

## Telegram 状态上报机器人 / Telegram Status Bot

用户通过机器人与 AMSAT 网站交互，提交卫星状态报告。报告默认使用当前 UTC 时刻（最近 15 分钟时段），呼号和网格默认使用该对话上次使用的值（✓ 表示已选中默认值），可直接接受默认值。

上报向导：

```
卫星 → 状态 → 日期 → 时间 → 呼号 → 网格 → 确认
```

- **日期确认（pybot）**：显示今天日期（UTC）。选「是」直接进入时间；选「不是」再进入 年→月→日 逐项选择。
- **时间确认（pybot）**：显示最近的 15 分钟时段（UTC）。选「是」进入呼号；选「不是」再进入 小时→时段 逐项选择。
- **tgbot**：日期/时间直接走 年→月→日→小时→时段 逐项选择（默认值已预选带 ✓，可直接翻页接受）。
- 呼号用文字输入，格式如 `BG7WZJ` 或 `ZL3AHW/M`；网格用 Maidenhead 定位器文字输入，格式如 `OM80` 或 `OM80MA`。

### 双后端对比 / Two backends

| | `tgbot/` | `pybot/` |
| --- | --- | --- |
| 运行时 | Cloudflare Workers（webhook） | 自托管 Python 长轮询 |
| 语言/依赖 | TypeScript | Python 3.12+，`python-telegram-bot>=21` |
| 存储 | Cloudflare KV（会话/目录缓存/用户档案） | JSON 文件（`state.json`，原子写入 + 线程锁） |
| 日期/时间步 | 年→月→日→小时→时段（默认值预选 ✓） | 日期确认→时间确认，「不是」才展开 年/月/日 与 小时/时段 |
| 部署 | `wrangler deploy` | `python bot.py` 或编译 Linux 单文件二进制 |
| 适用场景 | 无需服务器，走 Cloudflare 免费层 | 自建服务器 / 离线内网 / 需要二进制分发 |

- `tgbot/` 详细部署见 [`tgbot/README.md`](tgbot/README.md)（含 KV 绑定、secret、webhook 注册）。
- `pybot/` 详细部署见 [`pybot/README.md`](pybot/README.md)；可用 GitHub Actions 一键编译 Linux 单文件二进制（`build-pybot.yml`），或本地 `bash build_linux.sh`。

## SSTV 状态监控器 / SSTV Monitor

轮询 AMSAT API，当名称含 `[SSTV]` 的卫星收到 Heard（活跃）报告时，通过 Bark App 和/或 ntfy.sh 推送通知。两版共享同一核心逻辑（`fetch_reports` / 去重 / 消息构造）。

### 本地版（`amsat_sstv_monitor.py`）

```bash
python amsat_sstv_monitor.py [--once] [--interval 300] [--config config.json]
```

运行期间可输入命令：`status`（查看所有 SSTV 卫星最近 Heard）、`test`（发送测试通知）、`help`/`?`、`quit`。

配置（`config.json`，首次运行自动生成模板）：

| Key | 默认 | 说明 |
| --- | --- | --- |
| `bark_key` | `""` | Bark App 推送 key（留空则不启用） |
| `bark_server` | `https://api.day.app` | Bark 服务地址 |
| `ntfy_topic` | `amsat_status_sstv_heard` | ntfy.sh 话题（留空则不启用） |
| `ntfy_server` | `https://ntfy.sh` | 自建 ntfy 服务地址也可 |
| `ntfy_token` | `""` | ntfy 访问令牌（可选，留空为匿名） |
| `poll_interval` | `900` | 轮询间隔（秒） |
| `hours` | `24` | 查询窗口（小时） |
| `seen_file` | `seen.json` | 去重状态文件 |

### GitHub Actions 版（`amsat_sstv_monitor_action.py`）

配合 `.github/workflows/amsat-sstv-monitor.yml` 运行（定时 cron 已停用，目前仅手动触发 `workflow_dispatch`）。跨运行去重由 workflow 的 cache（`seen.json`）持久化。环境变量：`NTFY_TOKEN`（必填）、`HOURS`（可选，默认 24）。

## GitHub Actions / 工作流

| Workflow | 触发 | 说明 |
| --- | --- | --- |
| `amsat-sstv-monitor.yml` | 手动（原 `*/15 * * * *` cron 已停用） | 轮询 SSTV Heard 报告并推送 ntfy |
| `amsat-sstv-monitor-test.yml` | 手动 | 监控器首次运行/测试（发送启动通知） |
| `build-pybot.yml` | 手动 | 用 PyInstaller 在 ubuntu-latest 构建 `amsat_sstv_bot` 单文件二进制，上传 artifact |

## AMSAT 公共 API / Public API

基址 `https://www.amsat.org/status/api/v1`：

- `GET /catalog.php?include_stats=true` — 卫星目录（约 88 颗卫星）。
- `GET /statuses.php` — 规范的报告状态值（Heard / Telemetry Only / Not Heard / Crew Active）。
- `GET /reports.php?hours=&limit=[&name=&status=]` — 查询报告（监控器使用）。
- `POST /reports.php` — 提交/覆盖报告，请求体如：

  ```json
  {
    "name": "ISS_[SSTV]",
    "report": "Heard",
    "callsign": "BG7WZJ",
    "grid_square": "OM80MA",
    "reported_at": "2026-08-20T04:15:00Z"
  }
  ```

所有时间均为 UTC。同一卫星 + 呼号 + 小时 + 15 分钟时段的重复提交会覆盖之前的报告。

## Security & configuration / 安全与配置

- `config.json`、`state.json`、`seen.json` 均在 `.gitignore` 中，不入库。
- 机器人令牌通过 `wrangler secret`（tgbot）或环境变量 `TELEGRAM_BOT_TOKEN` / `NTFY_TOKEN`（pybot / Actions）注入。
- 监控器需要的推送凭据放在本地 `config.json`。

## Development / 开发

```bash
# tgbot（Cloudflare Worker）
cd tgbot && npm run typecheck && npm run deploy

# pybot
cd pybot && python -m py_compile *.py

# 构建 Linux 单文件二进制
# 本地: cd pybot && bash build_linux.sh   （或走 CI: Actions → Build pybot Linux binary）
```