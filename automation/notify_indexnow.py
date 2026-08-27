"""IndexNow로 네이버·Bing에 "오늘 이 URL들이 바뀌었다"고 즉시 알린다.

2026-08-27 확인: 네이버는 2023년 7월부터 서치어드바이저를 통해 IndexNow
프로토콜을 공식 지원한다(Bing도 지원, 구글은 2025년 10월 기준 미지원 —
구글은 대신 Search Console의 "URL 검사 → 색인 생성 요청"을 수동으로 써야
한다, SEO_SETUP.md 참고). 크롤러가 알아서 방문할 때까지 기다리지 않고
"방금 바뀐 URL 목록"을 직접 알려주는 방식이라 색인 반영이 더 빨라진다.

인증이 따로 필요 없다 — IndexNow는 API 키 발급 대신, 그 키를 담은 텍스트
파일을 사이트에 공개해두는 것만으로 "이 사이트의 관리자가 보낸 요청"임을
증명한다(build_digest.py가 docs/{키}.txt를 매번 새로 써준다).
"""
from __future__ import annotations

import os
import sys
from datetime import date
from urllib.parse import urlparse

import requests

from common import INDEXNOW_KEY, today_kst

INDEXNOW_URL = "https://api.indexnow.org/indexnow"
PAGES_URL = os.environ.get("PAGES_URL", "").rstrip("/")


def main() -> None:
    if not PAGES_URL:
        print("[notify_indexnow] PAGES_URL이 없어 건너뜁니다.")
        return

    host = urlparse(PAGES_URL).netloc
    today = today_kst()
    urls = [
        f"{PAGES_URL}/",
        f"{PAGES_URL}/archive/{today.isoformat()}.html",
        f"{PAGES_URL}/archive/",
        f"{PAGES_URL}/sitemap.xml",
        f"{PAGES_URL}/feed.xml",
    ]

    resp = requests.post(
        INDEXNOW_URL,
        json={
            "host": host,
            "key": INDEXNOW_KEY,
            "keyLocation": f"{PAGES_URL}/{INDEXNOW_KEY}.txt",
            "urlList": urls,
        },
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=15,
    )
    # IndexNow는 200/202를 정상 처리로 본다.
    if resp.status_code not in (200, 202):
        print(f"[notify_indexnow] 실패: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
        return
    print(f"[notify_indexnow] {len(urls)}개 URL 핑 완료 (status {resp.status_code})")


if __name__ == "__main__":
    main()
