"""OneSignal로 웹 푸시 알림을 보낸다 (이메일을 잘 안 열어보는 사람용 채널).

2026-08-27 확인: OneSignal은 구독자 3만 명까지 무료 플랜을 제공한다고
여러 리뷰에서 일관되게 확인했지만, 가입 절차·정책은 직접 가입해서
재확인할 것(신용카드 요구 여부까지는 이번에 확정하지 못했다).

필요한 것:
  - docs/index.html에 푸시 구독 위젯을 띄우려면 build_digest.py 실행 시
    환경변수 ONESIGNAL_APP_ID를 넘겨야 한다(그러면 SDK 스니펫이 자동 삽입됨)
  - 실제 발송(이 스크립트)에는 별도로 ONESIGNAL_API_KEY(REST API 키)가 필요

환경변수(둘 다 있어야 발송, 하나라도 없으면 조용히 건너뜀):
  - ONESIGNAL_APP_ID
  - ONESIGNAL_API_KEY
"""
from __future__ import annotations

import os
import sys

import requests

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "automation", "output")
ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"


def main() -> None:
    app_id = os.environ.get("ONESIGNAL_APP_ID")
    api_key = os.environ.get("ONESIGNAL_API_KEY")
    pages_url = os.environ.get("PAGES_URL", "")

    if not app_id or not api_key:
        print("[notify_onesignal] ONESIGNAL_APP_ID / ONESIGNAL_API_KEY가 없어 건너뜁니다.")
        return

    with open(os.path.join(OUTPUT_DIR, "subject.txt"), encoding="utf-8") as f:
        subject = f.read().strip()

    resp = requests.post(
        ONESIGNAL_URL,
        headers={"Authorization": f"Basic {api_key}", "Content-Type": "application/json"},
        json={
            "app_id": app_id,
            "included_segments": ["Subscribed Users"],
            "headings": {"ko": "지원금헌터"},
            "contents": {"ko": subject},
            "url": pages_url or None,
        },
        timeout=15,
    )
    if resp.status_code >= 300:
        print(f"[notify_onesignal] 발송 실패: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
        return
    print("[notify_onesignal] 발송 완료")


if __name__ == "__main__":
    main()
