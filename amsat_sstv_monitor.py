#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AMSAT SSTV 状态监控器

轮询 AMSAT Satellite Status API，当有 SSTV 卫星(名称含 [SSTV])收到
Heard 报告时，通过 Bark App 与/或 ntfy.sh 发送推送通知。

运行期间可输入命令：
  status   - 查看所有 SSTV 卫星最近 Heard 情况
  test     - 发送测试通知
  help / ? - 显示帮助
  quit     - 退出程序

仅使用 Python 标准库，无第三方依赖。
"""

import argparse
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_BASE = "https://www.amsat.org/status/api/v1"
HEARD = "Heard"
SSTV_TAG = "[SSTV]"
GROUP_NAME = "AMSAT-SSTV"
BARK_SUCCESS_CODES = (200, 0)

DEFAULT_CONFIG = {
    "bark_key": "",
    "bark_server": "https://api.day.app",
    "ntfy_server": "https://ntfy.sh",
    "ntfy_topic": "amsat_status_sstv_heard",
    "poll_interval": 900,
    "hours": 24,
    "seen_file": os.path.join(SCRIPT_DIR, "seen.json"),
}


def http_get_json(url, timeout=20):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "amsat-sstv-monitor/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_bark(cfg, title, body, group=GROUP_NAME):
    key = cfg.get("bark_key") or ""
    if not key:
        raise RuntimeError("config.json 中 bark_key 为空")
    server = (cfg.get("bark_server") or "https://api.day.app").rstrip("/")
    payload = urllib.parse.urlencode({"title": title, "body": body, "group": group}).encode("utf-8")
    req = urllib.request.Request(
        f"{server}/{key}",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if result.get("code") not in BARK_SUCCESS_CODES:
        raise RuntimeError(f"Bark 返回异常: {result}")
    return result


def send_ntfy(cfg, title, body, tags=("satellite",), token=None):
    topic = cfg.get("ntfy_topic") or ""
    if not topic:
        raise RuntimeError("config.json 中 ntfy_topic 为空")
    server = (cfg.get("ntfy_server") or "https://ntfy.sh").rstrip("/")
    text = f"{title}\n{body}".encode("utf-8")
    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        f"{server}/{urllib.parse.quote(topic)}",
        data=text,
        method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"ntfy 发送失败: HTTP {e.code}: {e.read().decode('utf-8', 'replace')}"
        )


def fetch_reports(hours, limit=500, name=None, status=None):
    params = {"hours": int(hours), "limit": int(limit)}
    if name:
        params["name"] = name
    if status:
        params["status"] = status
    url = f"{API_BASE}/reports.php?" + urllib.parse.urlencode(params)
    data = http_get_json(url)
    reports = data.get("data", [])
    if not name:
        reports = [r for r in reports if SSTV_TAG in (r.get("name") or "")]
    return reports


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def fmt_relative(dt_utc, now=None):
    if dt_utc is None:
        return "未知"
    now = now or datetime.now(timezone.utc)
    secs = max(0, int((now - dt_utc).total_seconds()))
    if secs < 60:
        return "刚刚"
    if secs < 3600:
        return f"{secs // 60} 分钟前"
    if secs < 86400:
        return f"{secs // 3600} 小时前"
    return f"{secs // 86400} 天前"


def load_seen(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (OSError, ValueError):
        return set()


def save_seen(path, seen):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f)
    os.replace(tmp, path)


def get_notifiers(cfg):
    notifiers = []
    if cfg.get("bark_key"):
        notifiers.append(("Bark", lambda t, b: send_bark(cfg, t, b)))
    if cfg.get("ntfy_topic"):
        notifiers.append(("ntfy", lambda t, b: send_ntfy(cfg, t, b)))
    return notifiers


def notify_all(cfg, title, body):
    notifiers = get_notifiers(cfg)
    if not notifiers:
        logging.info("未配置通知渠道，跳过通知")
        return []
    results = []
    for name, fn in notifiers:
        try:
            fn(title, body)
            results.append(name)
            logging.info(f"已通过 {name} 发送通知")
        except Exception as e:
            logging.error(f"{name} 通知发送失败: {e}")
    return results


def fetch_latest_sstv_heard(hours):
    reports = fetch_reports(hours, status=HEARD)
    return reports[0] if reports else None


REGIONS = [
    ("日本", 30, 46, 128, 146),
    ("韩国", 33, 39, 124, 130),
    ("中国", 18, 54, 73, 135),
    ("东南亚", -12, 24, 92, 145),
    ("印度", 6, 36, 68, 98),
    ("中东", 12, 42, 26, 66),
    ("北欧", 54, 72, 4, 45),
    ("南欧", 35, 47, -10, 30),
    ("中欧", 43, 55, 8, 22),
    ("东欧", 43, 62, 22, 46),
    ("西欧", 36, 61, -12, 12),
    ("北非", 18, 38, -18, 40),
    ("非洲", -36, 18, -20, 52),
    ("美东", 22, 50, -85, -66),
    ("美中", 24, 50, -106, -85),
    ("美西", 30, 50, -126, -106),
    ("阿拉斯加", 51, 72, -172, -129),
    ("加拿大", 42, 75, -141, -52),
    ("墨西哥", 14, 34, -118, -86),
    ("加勒比", 8, 27, -85, -59),
    ("南美北部", -22, 13, -82, -34),
    ("巴西", -35, 6, -75, -34),
    ("南美南部", -56, -21, -76, -53),
    ("澳大利亚", -45, -10, 111, 155),
    ("新西兰", -49, -33, 166, 179),
    ("夏威夷", 18, 24, -161, -153),
    ("太平洋岛屿", -30, 25, 130, 220),
]


def grid_to_latlon(grid):
    """梅登黑德网格定位 -> 网格中心经纬度 (lon, lat)；无效返回 None"""
    if not grid:
        return None
    g = grid.strip().upper()
    if len(g) < 2 or not (g[0].isalpha() and g[1].isalpha()) or g[0] > "R" or g[1] > "R":
        return None
    lon = -180 + (ord(g[0]) - 65) * 20
    lat = -90 + (ord(g[1]) - 65) * 10
    if len(g) >= 4 and g[2].isdigit() and g[3].isdigit():
        lon += int(g[2]) * 2 + 1.0
        lat += int(g[3]) + 0.5
        if len(g) >= 6 and g[4].isalpha() and g[5].isalpha() and g[4] <= "X" and g[5] <= "X":
            lon += (ord(g[4]) - 65) / 12.0 + 1.0 / 24.0 - 1.0
            lat += (ord(g[5]) - 65) / 24.0 + 1.0 / 48.0 - 0.5
    else:
        lon += 10.0
        lat += 5.0
    return lon, lat


def region_name(grid):
    pos = grid_to_latlon(grid)
    if not pos:
        return ""
    lon, lat = pos
    for name, lat0, lat1, lon0, lon1 in REGIONS:
        if lat0 <= lat <= lat1 and lon0 <= lon <= lon1:
            return name
    return ""


def build_report_message(report):
    title = "Amsat SSTV Heard 报告"
    sat = report.get("satellite_display_name") or report.get("name") or "?"
    grid = report.get("grid_square") or "?"
    name = region_name(grid)
    grid_disp = f"{grid}（{name}）" if name else grid
    dt = parse_dt(report.get("reported_time"))
    rel = f"（{fmt_relative(dt)}）" if dt else ""
    body = "\n".join(
        [
            f"卫星: {sat}",
            f"呼号: {report.get('callsign') or '?'}",
            f"网格: {grid_disp}",
            f"时间: {report.get('reported_time') or '?'}{rel}",
        ]
    )
    return title, body


def notify_report(cfg, report):
    return notify_all(cfg, *build_report_message(report))


def run_monitor(cfg, stop_event, once=False):
    seen_path = cfg["seen_file"]
    seen = load_seen(seen_path)
    interval = int(cfg.get("poll_interval") or 300)
    hours = int(cfg.get("hours") or 24)
    first_run = not os.path.exists(seen_path)
    while not stop_event.is_set():
        try:
            reports = fetch_reports(hours, status=HEARD)
            if first_run:
                for r in reports:
                    seen.add(r["id"])
                save_seen(seen_path, seen)
                first_run = False
                logging.info(f"[poll] 首次运行，已记录现有 {len(reports)} 条 Heard 报告，之后的新报告将推送通知")
            else:
                new_reports = [r for r in reports if r.get("id") not in seen]
                for r in new_reports:
                    notify_report(cfg, r)
                    seen.add(r["id"])
                if new_reports:
                    save_seen(seen_path, seen)
                    logging.info(f"[poll] 新增 {len(new_reports)} 条 SSTV Heard 报告并已通知")
                else:
                    logging.info(f"[poll] 检查完成，无新增（共 {len(reports)} 条）")
        except Exception as e:
            logging.error(f"[poll] 检查失败: {e}")
        if once:
            break
        stop_event.wait(interval)


def cmd_status(cfg):
    print("\n正在查询 SSTV 卫星的 Heard 报告...")
    cat = http_get_json(f"{API_BASE}/catalog.php")
    sstv = sorted(
        (s for s in cat.get("data", []) if SSTV_TAG in (s.get("name") or "")),
        key=lambda s: s.get("name", ""),
    )
    print(f"共 {len(sstv)} 颗 SSTV 卫星\n")

    def query_sat(sat):
        try:
            reports = fetch_reports(24, limit=1, name=sat.get("name"), status=HEARD)
            return (sat, reports[0] if reports else None, None)
        except Exception as e:
            return (sat, None, str(e))

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(query_sat, sstv))

    heard_rows = []
    none_rows = []
    for sat, report, err in results:
        display = sat.get("display_name") or sat.get("name")
        if err:
            print(f"  查询 {display} 失败: {err}")
        elif report:
            heard_rows.append((display, report))
        else:
            none_rows.append(display)

    if heard_rows:
        heard_rows.sort(key=lambda t: t[1].get("reported_time") or "", reverse=True)
        print("已收到 Heard：")
        print(f"  {'#':<3}{'卫星':<24}{'最近 Heard(本地)':<22}{'相对':<12}{'呼号':<10}{'网格'}")
        for i, (display, r) in enumerate(heard_rows, 1):
            dt = parse_dt(r.get("reported_time"))
            local = dt.astimezone().strftime("%Y-%m-%d %H:%M") if dt else "?"
            grid = r.get("grid_square") or "?"
            name = region_name(grid)
            grid_disp = f"{grid}（{name}）" if name else grid
            print(
                f"  {i:<3}{display:<24}{local:<22}{fmt_relative(dt):<12}"
                f"{(r.get('callsign') or '?'):<10}{grid_disp}"
            )
        print()
    if none_rows:
        print("最近 24 小时内无 Heard 记录：")
        for display in none_rows:
            print(f"  * {display}")
        print()
    print(f"汇总：已收到 Heard {len(heard_rows)} 颗 / 无 Heard {len(none_rows)} 颗\n")


def cmd_test(cfg):
    notifiers = get_notifiers(cfg)
    if not notifiers:
        print("未配置任何通知渠道（bark_key / ntfy_topic），无法发送测试通知")
        return

    hours = int(cfg.get("hours") or 24)
    report = fetch_latest_sstv_heard(hours)
    if report:
        title, body = build_report_message(report)
        title += "（测试模拟）"
        print(f"模拟最近 Heard: {report.get('satellite_display_name') or report.get('name')} / "
              f"{report.get('callsign') or '?'} @ {report.get('reported_time') or '?'}")
    else:
        report = {
            "satellite_display_name": "ISS [SSTV]",
            "name": "ISS_[SSTV]",
            "callsign": "N0CALL",
            "grid_square": "EM48",
            "reported_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        title, body = build_report_message(report)
        title += "（测试模拟·示例数据）"
        print(f"窗口 {hours} 小时内无 Heard 报告，使用示例数据")

    print(body)
    print("发送模拟通知...")
    for name, fn in notifiers:
        try:
            fn(title, body)
            print(f"  [OK] {name} 已发送")
        except Exception as e:
            print(f"  [失败] {name} 发送失败: {e}")


def print_help():
    print("\n可用命令：")
    print("  status      - 查看所有 SSTV 卫星最近 Heard 情况")
    print("  test        - 发送测试通知")
    print("  help / ?    - 显示此帮助")
    print("  quit / exit - 退出程序")
    print()


def input_loop(cfg, stop_event):
    while not stop_event.is_set():
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        cmd = line.lower()
        try:
            if cmd in ("quit", "exit", "q"):
                print("正在退出...")
                stop_event.set()
                break
            elif cmd in ("help", "?"):
                print_help()
            elif cmd == "status":
                cmd_status(cfg)
            elif cmd == "test":
                cmd_test(cfg)
            else:
                print(f"未知命令: {line}")
                print_help()
        except Exception as e:
            print(f"命令执行失败: {e}")


def load_config(path):
    config_path = path or os.path.join(SCRIPT_DIR, "config.json")
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    else:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        logging.info(f"已生成默认配置文件: {config_path}")
    return cfg, config_path


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="AMSAT SSTV 状态监控器")
    parser.add_argument("--config", default=None, help="配置文件路径（默认: 脚本目录下 config.json）")
    parser.add_argument("--once", action="store_true", help="只检查一轮后退出")
    parser.add_argument("--interval", type=int, default=None, help="覆盖轮询间隔(秒)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%H:%M:%S",
    )

    cfg, config_path = load_config(args.config)
    if args.interval:
        cfg["poll_interval"] = args.interval

    notifier_names = [n for n, _ in get_notifiers(cfg)]
    if notifier_names:
        print(f"通知渠道已启用：{'、'.join(notifier_names)}")
    else:
        print("警告：未配置任何通知渠道（bark_key / ntfy_topic），通知功能不可用，程序正常运行")
    print(f"配置文件: {config_path}")

    stop_event = threading.Event()

    if args.once:
        run_monitor(cfg, stop_event, once=True)
        return

    print(f"AMSAT SSTV 状态监控已启动（配置文件: {config_path}）")
    print(f"轮询间隔: {cfg['poll_interval']} 秒 | 查询窗口: {cfg['hours']} 小时")
    print_help()

    threading.Thread(target=input_loop, args=(cfg, stop_event), daemon=True).start()
    try:
        run_monitor(cfg, stop_event)
    except KeyboardInterrupt:
        print("\n收到中断，正在退出...")
    finally:
        stop_event.set()
        logging.info("已退出")


if __name__ == "__main__":
    main()
