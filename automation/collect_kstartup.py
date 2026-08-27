"""K-Startup(k-startup.go.kr) 사업공고(모집중) 수집.

2026-08-27 실제 확인 내역:
- 목록 페이지(bizpbanc-ongoing.do)는 JS로 그려져서 curl로는 항목이 안 보임
- 하지만 K-Startup이 자체 제공하는 **공식 RSS 피드**가 있다:
  https://www.k-startup.go.kr/web/contents/rss/bizpbanc-ongoing.do
  (사이트의 "RSS 피드" 버튼이 만드는 바로 그 URL 그대로, 표준 RSS 2.0)
- RSS에는 제목/링크/등록일만 있고 마감일이 없어서, 각 공고의 상세 페이지
  (`...bizpbanc-ongoing.do?schM=view&id=<id>`)를 한 번씩 더 열어
  `#rcptPeriod`(접수기간) 텍스트를 읽어 마감일을 얻는다. 상세 페이지는
  서버 렌더링이라 curl로도 확인됨.

공식 오픈API(공공데이터포털 15125364)도 있지만 활용신청 승인 후 실제
응답 스키마를 검증하지 못했다 — 필드명을 추측해서 코드를 짜는 대신, 이미
실제로 파싱을 확인한 RSS+상세페이지 방식을 1차로 쓴다. API 키를 발급받아
응답을 직접 확인한 뒤 바꾸고 싶다면 이 파일만 교체하면 된다(다른 스크립트는
공통 dict 모양만 알면 되므로 영향 없음).
"""
from __future__ import annotations

import html
import sys
import time
import xml.etree.ElementTree as ET
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from common import extract_region, parse_period

RSS_URL = "https://www.k-startup.go.kr/web/contents/rss/bizpbanc-ongoing.do"
DETAIL_URL = "https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BenefitHunterBot/1.0)"}
REQUEST_DELAY_SEC = 0.4  # 상세페이지를 연속 요청할 때 서버에 부담 안 주려는 최소한의 대기


def _fetch_rss_items(max_items: int) -> list[dict]:
    resp = requests.get(RSS_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    entries = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        entries.append({"title": title, "link": link, "pubDate": pub_date})

    # 최근 등록순으로 정렬해 상위 N개만 상세페이지를 확인한다(전체를 다 열면
    # 요청 수가 너무 많아진다). RFC822 pubDate 정렬이 번거로우니 리스트
    # 순서(보통 등록일 오름차순으로 내려옴)를 뒤집는 것으로 대체한다.
    entries.reverse()
    return entries[:max_items]


def _extract_id(link: str) -> str | None:
    qs = parse_qs(urlparse(link).query)
    ids = qs.get("id")
    return ids[0] if ids else None


def _fetch_detail(item_id: str) -> dict:
    resp = requests.get(DETAIL_URL, params={"schM": "view", "id": item_id}, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    period_tag = soup.select_one("#rcptPeriod")
    period_raw = period_tag.get_text(" ", strip=True) if period_tag else ""

    agency = ""
    region = None
    for li in soup.select(".dot_list-wrap .dot_list"):
        label = li.select_one(".tit")
        value = li.select_one(".txt")
        if not label or not value:
            continue
        label_text = label.get_text(strip=True)
        value_text = value.get_text(" ", strip=True)
        if label_text == "주관기관명":
            agency = value_text
        elif label_text == "지역":
            region = value_text

    return {"period_raw": period_raw, "agency": agency, "region": region}


def collect(max_items: int = 25) -> list[dict]:
    try:
        entries = _fetch_rss_items(max_items)
    except (requests.RequestException, ET.ParseError) as e:
        print(f"[k-startup] RSS 요청 실패, 이번 회차는 건너뜀: {e}", file=sys.stderr)
        return []

    items: list[dict] = []
    for entry in entries:
        item_id = _extract_id(entry["link"])
        if not item_id:
            continue

        # RSS 원문 자체가 &(40; 처럼 두 번 이스케이프된 채 내려온다
        # (예: "&amp;#40;") — 사람이 읽을 문자로 되돌리려면 두 번 풀어야 한다.
        raw_title = html.unescape(html.unescape(entry["title"]))
        region_from_title, title = extract_region(raw_title)

        try:
            time.sleep(REQUEST_DELAY_SEC)
            detail = _fetch_detail(item_id)
        except requests.RequestException as e:
            print(f"[k-startup] 상세페이지 요청 실패(id={item_id}), 이 항목만 스킵: {e}", file=sys.stderr)
            continue

        deadline, note = parse_period(detail["period_raw"]) if detail["period_raw"] else (None, "정보 없음")

        items.append({
            "title": title,
            "agency": detail["agency"] or "창업진흥원",
            "region": detail["region"] or region_from_title,
            "source": "K-Startup",
            "source_category": "창업지원",
            "deadline": deadline,
            "deadline_note": note,
            "detail_url": entry["link"],
        })

    return items


if __name__ == "__main__":
    for it in collect(5):
        print(it)
