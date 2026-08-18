#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AMSAT SSTV 状态监控（GitHub Actions 版）

配合 .github/workflows/amsat-sstv-monitor.yml 每 15 分钟运行一次，
检测 [SSTV] 卫星的新 Heard 报告并通过 ntfy.sh 推送（仅使用 ntfy，不发 Bark）。

跨运行去重状态由 GitHub Actions cache 持久化（workflow 负责恢复/保存 seen.json，
采用「每次运行唯一 key + restore-keys 前缀匹配」模式绕过 cache 不可覆盖的限制）。

首次运行（无状态文件）发送一次启动测试通知并记录基线，不逐条推送历史报告。

环境变量（可选）：
  NTFY_SERVER  ntfy 服务器地址，默认 https://ntfy.sh
  NTFY_TOKEN   ntfy 访问令牌（私有 topic 时设置）
  HOURS        查询窗口小时数，默认 24
"""

import argparse
import logging
import os
import sys

from amsat_sstv_monitor import (
    HEARD,
    build_report_message,
    fetch_reports,
    load_seen,
    save_seen,
    send_ntfy,
)

NTFY_TOPIC = "amsat_status_sstv_heard"


def main():
    parser = argparse.ArgumentParser(description="AMSAT SSTV 状态监控（GitHub Actions）")
    parser.add_argument("--state", default="seen.json", help="去重状态文件路径（默认 seen.json）")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    cfg = {
        "ntfy_topic": NTFY_TOPIC,
        "ntfy_server": os.getenv("NTFY_SERVER", "https://ntfy.sh"),
    }
    token = os.getenv("NTFY_TOKEN", "") or None
    hours = int(os.getenv("HOURS", "24"))
    state_path = args.state

    seen = load_seen(state_path)
    first_run = not os.path.exists(state_path)

    try:
        reports = fetch_reports(hours, status=HEARD)
    except Exception as e:
        logging.error(f"获取报告失败: {e}")
        sys.exit(1)

    if first_run:
        title = "Amsat SSTV 监控已启动（首次运行）"
        lines = [f"已记录基线 {len(reports)} 条现有 Heard 报告", "后续新报告将推送至此。"]
        if reports:
            _, report_body = build_report_message(reports[0])
            lines += ["", "最新报告：", report_body]
        try:
            send_ntfy(cfg, title, "\n".join(lines), token=token)
            logging.info(f"首次运行：已发送启动测试通知，记录基线 {len(reports)} 条")
        except Exception as e:
            logging.error(f"启动测试通知发送失败: {e}")
        for r in reports:
            seen.add(r["id"])
        save_seen(state_path, seen)
        return

    new_reports = [r for r in reports if r.get("id") not in seen]
    if not new_reports:
        logging.info(f"无新增 Heard 报告（共 {len(reports)} 条）")
        return

    sent = 0
    for r in new_reports:
        title, body = build_report_message(r)
        try:
            send_ntfy(cfg, title, body, token=token)
            seen.add(r["id"])
            sent += 1
            logging.info(
                f"已推送 {r.get('satellite_display_name') or r.get('name')} / "
                f"{r.get('callsign') or '?'} @ {r.get('reported_time') or '?'}"
            )
        except Exception as e:
            logging.error(f"推送失败（报告 id={r.get('id')}）: {e}")
    save_seen(state_path, seen)
    logging.info(f"本轮新增 {len(new_reports)} 条，成功推送 {sent} 条")


if __name__ == "__main__":
    main()
