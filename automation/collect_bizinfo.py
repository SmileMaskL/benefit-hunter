"""기업마당(bizinfo.go.kr) 지원사업 공고 목록 수집.

2026-08-27 실제 접속 확인: 목록 페이지는 서버에서 완성된 HTML로 내려온다
(JS로 나중에 채워지는 방식이 아님) — `curl`만으로도 표(<table>) 안의 실제
공고 데이터를 그대로 받을 수 있었다. 표 컬럼 순서(번호/지원분야/지원사업명/
신청기간/소관부처·지자체/사업수행기관/등록일/조회수)도 그때 확인한 그대로다.
공식 오픈API나 RSS는 없어서(SOURCES.md 참고) 목록 페이지를 직접 파싱한다.

주의: 이건 "공식 API"가 아니라 페이지 구조에 의존하는 스크레이핑이다.
bizinfo가 페이지 구조를 바꾸면 이 파서도 같이 깨질 수 있다 — 그래서
build_digest.py는 이 수집기가 실패해도(빈 리스트를 반환해도) K-Startup 쪽
결과만으로 발행이 가능하게 만들어져 있다.
"""
from __future__ import annotations

import sys

import requests
from bs4 import BeautifulSoup

from common import extract_region, parse_period

LIST_URL = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do"
DETAIL_BASE = "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BenefitHunterBot/1.0)"}


def collect(max_items: int = 30) -> list[dict]:
    try:
        resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[bizinfo] 목록 페이지 요청 실패, 이번 회차는 건너뜀: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("table tbody tr")
    items: list[dict] = []

    for row in rows[:max_items]:
        cells = row.find_all("td")
        if len(cells) < 7:
            continue  # 예상한 8컬럼 구조가 아니면(페이지 개편 등) 조용히 스킵

        category = cells[1].get_text(strip=True)
        title_link = cells[2].find("a")
        if not title_link:
            continue
        raw_title = title_link.get_text(strip=True)
        region, title = extract_region(raw_title)

        href = title_link.get("href", "")
        pblanc_id = ""
        if "pblancId=" in href:
            pblanc_id = href.split("pblancId=", 1)[1].split("&", 1)[0]
        detail_url = f"{DETAIL_BASE}?pblancId={pblanc_id}" if pblanc_id else LIST_URL

        period_raw = cells[3].get_text(strip=True)
        deadline, note = parse_period(period_raw)
        agency = cells[4].get_text(strip=True)

        items.append({
            "title": title,
            "agency": agency,
            "region": region,
            "source": "기업마당",
            "source_category": category,
            "deadline": deadline,
            "deadline_note": note,
            "detail_url": detail_url,
        })

    return items


if __name__ == "__main__":
    for it in collect(10):
        print(it)
