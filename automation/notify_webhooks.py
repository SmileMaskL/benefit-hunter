"""오늘의 다이제스트 요약을 디스코드/슬랙 웹훅으로 중계한다 (완전 무료).

GROWTH.md의 "협업/커뮤니티 확산" 채널 중 하나 — 자영업자·창업 커뮤니티
운영자가 자기 디스코드/슬랙 서버에 웹훅을 걸어두면, 우리가 따로 손대지
않아도 그 커뮤니티에 매일 자동으로 요약이 퍼진다.

환경변수(둘 다 선택, 없으면 그냥 건너뜀):
  - DISCORD_WEBHOOK_URL : 디스코드 채널 설정 → 연동 → 웹훅에서 발급
  - SLACK_WEBHOOK_URL   : 슬랙 앱(Incoming Webhooks) 설정에서 발급
"""
from __future__ import annotations

import json
import os
import sys

import requests

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "automation", "output")


def _load_top_lines(max_items: int = 5) -> tuple[str, list[dict]]:
    with open(os.path.join(OUTPUT_DIR, "subject.txt"), encoding="utf-8") as f:
        subject = f.read().strip()
    entries_path = os.path.join(OUTPUT_DIR, "entries.json")
    entries = []
    if os.path.exists(entries_path):
        with open(entries_path, encoding="utf-8") as f:
            entries = json.load(f)[:max_items]
    return subject, entries


def _plain_summary() -> str:
    subject, entries = _load_top_lines()
    lines = [f"**{subject}**", ""]
    for e in entries:
        dday = f"[D-{e['days_left']}] " if e.get("days_left") is not None else "⚠️ "
        lines.append(f"- {dday}{e['title']} ({e['agency']}) — 마감 {e['deadline_note']}")
    return "\n".join(lines)


def notify_discord(webhook_url: str) -> None:
    resp = requests.post(webhook_url, json={"content": _plain_summary()}, timeout=15)
    if resp.status_code >= 300:
        print(f"[notify_webhooks] Discord 전송 실패: {resp.status_code} {resp.text[:200]}", file=sys.stderr)


def notify_slack(webhook_url: str) -> None:
    resp = requests.post(webhook_url, json={"text": _plain_summary()}, timeout=15)
    if resp.status_code >= 300:
        print(f"[notify_webhooks] Slack 전송 실패: {resp.status_code} {resp.text[:200]}", file=sys.stderr)


def main() -> None:
    discord_url = os.environ.get("DISCORD_WEBHOOK_URL")
    slack_url = os.environ.get("SLACK_WEBHOOK_URL")

    if not discord_url and not slack_url:
        print("[notify_webhooks] DISCORD_WEBHOOK_URL / SLACK_WEBHOOK_URL 둘 다 없어 건너뜁니다.")
        return
    if discord_url:
        notify_discord(discord_url)
    if slack_url:
        notify_slack(slack_url)
    print("[notify_webhooks] 완료")


if __name__ == "__main__":
    main()
