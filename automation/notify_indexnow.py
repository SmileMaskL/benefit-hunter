"""IndexNow로 네이버·Bing에 "오늘 이 URL들이 바뀌었다"고 즉시 알린다.

2026-08-27 확인: 네이버는 2023년 7월부터 서치어드바이저를 통해 IndexNow
프로토콜을 공식 지원한다(Bing도 지원, 구글은 2025년 10월 기준 미지원 —
구글은 IndexNow에 참여하지 않는다).

구글의 "사이트맵 핑"(google.com/ping?sitemap=...)도 2023년 6월에 이미
공식 폐지되어 지금은 404만 돌려준다(직접 호출해서 확인함) — 자동화
후보에서 제외했다. 구글 쪽은 대신 render_sitemap()이 각 URL마다 정확한
<lastmod>을 채워주는 것으로 신선도를 알린다(구글이 공식 권장하는 방식,
https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping).
사람이 서치콘솔에 로그인해서 눌러야 하는 "URL 검사 → 색인 생성 요청"은
계정 자동화가 필요해 이용약관 위반 소지가 있고, 반복한다고 색인이 더
빨라지지도 않아서 자동화하지 않는다(SEO_SETUP.md 참고).

IndexNow는 인증이 따로 필요 없다 — API 키 발급 대신, 그 키를 담은 텍스트
파일을 사이트에 공개해두는 것만으로 "이 사이트의 관리자가 보낸 요청"임을
증명한다(build_digest.py가 docs/{키}.txt를 매번 새로 써준다).
"""
from __future__ import annotations

import os
import sys
from datetime import date
from urllib.parse import urlparse

import requests

from common import INDEXNOW_KEY, cleanup_old_logs, log_error, log_success, today_kst

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
        msg = f"실패: {resp.status_code} {resp.text[:200]}"
        print(f"[notify_indexnow] {msg}", file=sys.stderr)
        log_error("notify_indexnow", msg)
        return
    msg = f"{len(urls)}개 URL 핑 완료 (status {resp.status_code})"
    print(f"[notify_indexnow] {msg}")
    log_success("notify_indexnow", msg)


if __name__ == "__main__":
    cleanup_old_logs()
    try:
        main()
    except Exception as e:
        log_error("notify_indexnow", "실행 중 예외 발생", exc=e)
        raise
