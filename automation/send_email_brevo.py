"""build_digest.py가 만든 오늘의 본문을 Brevo 무료 API로 구독자에게 발송한다.

왜 Stibee가 아니라 Brevo인가 (2026-08-27 확인):
Stibee의 "자동 이메일"과 이메일 발송 Open API는 Standard/Pro/Enterprise
유료 플랜부터 지원된다(무료 플랜은 사람이 에디터에서 직접 눌러야 발송됨).
"PC를 꺼도 평생 무료로 자동 운영"이 목표라 사람의 클릭이 필요 없는
API 발송이 필수인데, 그걸 무료로 제공하는 Brevo(트랜잭션 메일 API,
무료 플랜 기준 일 300통)로 발송 채널을 옮겼다. 자세한 배경은
AUTOMATION.md 참고. (참고로 Stibee는 별도로 "유료 뉴스레터" 결제 기능이
있는데 그건 돈을 받는 기능이지 자동 발송 기능이 아니다 —
MONETIZATION_HOWTO.md 참고.)

구독자 CSV 스키마 (subscribers.example.csv 참고): email,name,tier,region,tags
- tier가 "paid"인 구독자만 region/tags로 맞춤 필터링된 다이제스트를 받는다
  (MONETIZATION.md의 "맞춤 필터"는 유료 전용 기능이라는 설계를 코드로
  그대로 반영한 것). tier가 비어있거나 "free"면 전체 다이제스트를 받는다.
- region은 "대구,경북"처럼 콤마로 여러 개, tags는 "청년,예비창업"처럼 콤마로 여러 개.

이 스크립트는 다음이 준비돼 있어야 실제로 발송한다(하나라도 없으면
에러 없이 조용히 건너뛴다 — 아직 세팅 전이어도 build_digest.py의
웹페이지/RSS/캘린더 생성은 항상 정상 동작해야 하므로):
  - 환경변수 BREVO_API_KEY
  - automation/subscribers.csv
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import date as date_cls

import requests

from build_digest import render_html

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBSCRIBERS_CSV = os.path.join(REPO_ROOT, "automation", "subscribers.csv")
OUTPUT_DIR = os.path.join(REPO_ROOT, "automation", "output")
BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"

# Brevo 무료 플랜 일일 한도(300통)를 절대 넘지 않도록 여유를 두고 캡을 건다.
DAILY_SEND_CAP = int(os.environ.get("DAILY_SEND_CAP", "290"))
SENDER = {
    "email": os.environ.get("SENDER_EMAIL") or "noreply@example.com",
    "name": os.environ.get("SENDER_NAME") or "지원금헌터",
}


def load_subscribers() -> list[dict]:
    if not os.path.exists(SUBSCRIBERS_CSV):
        return []
    with open(SUBSCRIBERS_CSV, newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row.get("email")]


def load_entries() -> list[dict]:
    path = os.path.join(OUTPUT_DIR, "entries.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    for e in raw:
        e["deadline"] = date_cls.fromisoformat(e["deadline"]) if e["deadline"] else None
    return raw


def personalize_html(entries: list[dict], today: date_cls, region_csv: str, tags_csv: str) -> str:
    from common import matches_subscriber_filters

    regions = [r.strip() for r in region_csv.split(",") if r.strip()]
    tags = [t.strip() for t in tags_csv.split(",") if t.strip()]
    if not regions and not tags:
        return render_html(entries, today)

    filtered = [
        e for e in entries
        if any(matches_subscriber_filters(e, r, tags) for r in (regions or [""]))
    ]
    return render_html(filtered or entries, today, for_email=True)  # 0건이면 실망시키지 않게 전체를 대신 보냄


def send_one(api_key: str, to_email: str, to_name: str, subject: str, html: str) -> bool:
    resp = requests.post(
        BREVO_SEND_URL,
        headers={"api-key": api_key, "content-type": "application/json"},
        json={
            "sender": SENDER,
            "to": [{"email": to_email, "name": to_name or to_email}],
            "subject": subject,
            "htmlContent": html,
        },
        timeout=20,
    )
    if resp.status_code >= 300:
        print(f"[send_email_brevo] 발송 실패 {to_email}: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
        return False
    return True


def main() -> None:
    api_key = os.environ.get("BREVO_API_KEY")
    subscribers = load_subscribers()

    if not api_key:
        print("[send_email_brevo] BREVO_API_KEY가 없어 발송을 건너뜁니다 (웹페이지/RSS는 정상 생성됨). "
              "AUTOMATION.md의 Brevo 설정 단계를 참고하세요.")
        return
    if not subscribers:
        print("[send_email_brevo] automation/subscribers.csv에 구독자가 없어 발송을 건너뜁니다.")
        return

    with open(os.path.join(OUTPUT_DIR, "subject.txt"), encoding="utf-8") as f:
        default_subject = f.read().strip()
    with open(os.path.join(OUTPUT_DIR, "email_body.html"), encoding="utf-8") as f:
        default_html = f.read()

    entries = load_entries()
    today = date_cls.today()

    if len(subscribers) > DAILY_SEND_CAP:
        print(f"[send_email_brevo] 구독자 {len(subscribers)}명 > 일일 한도 {DAILY_SEND_CAP}명 — "
              f"무료 플랜 한도 초과 위험. 상위 {DAILY_SEND_CAP}명만 발송하고 나머지는 스킵합니다. "
              "MONETIZATION.md의 유료 전환 조건(500~1,000명)에 근접했다는 신호이기도 합니다.")
        subscribers = subscribers[:DAILY_SEND_CAP]

    sent, failed, personalized = 0, 0, 0
    for row in subscribers:
        html = default_html
        tier = (row.get("tier") or "free").strip().lower()
        if tier == "paid" and entries:
            html = personalize_html(entries, today, row.get("region", ""), row.get("tags", ""))
            personalized += 1

        ok = send_one(api_key, row["email"], row.get("name", ""), default_subject, html)
        sent += ok
        failed += not ok
        time.sleep(0.15)  # Brevo 초당 요청 제한을 여유 있게 피함

    print(f"[send_email_brevo] 발송 완료: 성공 {sent}건(맞춤형 {personalized}건 포함), 실패 {failed}건")


if __name__ == "__main__":
    main()
