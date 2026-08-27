"""오늘의 다이제스트를 만든다: 수집 → 정렬/태깅 → HTML/RSS/ICS/위젯/검색색인 생성.

이 스크립트 하나로 다음을 전부 만든다.
- docs/index.html        : GitHub Pages로 공개되는 오늘의 웹 페이지
- docs/feed.xml          : 오늘 다이제스트의 RSS 미러
- docs/deadlines.ics     : 마감일 캘린더 구독 파일
- docs/widget.html       : 다른 사이트에 <iframe>으로 심는 초소형 위젯(TOP3만)
- docs/archive/YYYY-MM-DD.html : 그날 발행분 아카이브
- docs/archive/index.html      : 아카이브 목록 + 클라이언트 사이드 검색
- docs/search-index.json       : 검색용 데이터(날짜별로 계속 누적)
- automation/output/entries.json  : 오늘 항목의 원본 구조화 데이터 — send_email_brevo.py가
  유료 구독자 맞춤 필터링에 재사용한다
- automation/output/email_body.html / subject.txt : 무료 구독자용 기본 발송 본문

실행 위치는 저장소 루트를 가정한다(`python automation/build_digest.py`).
"""
from __future__ import annotations

import json
import os
from datetime import date
from html import escape

from collect_bizinfo import collect as collect_bizinfo
from collect_kstartup import collect as collect_kstartup
from common import days_left, guess_categories, today_kst

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(REPO_ROOT, "docs")
ARCHIVE_DIR = os.path.join(DOCS_DIR, "archive")
OUTPUT_DIR = os.path.join(REPO_ROOT, "automation", "output")

TOP_N = 3
# GitHub Actions에서 `env: PAGES_URL: https://<계정>.github.io/<저장소>/` 로 넘겨주면
# RSS/위젯의 절대경로 링크가 실제 주소로 채워진다. 안 넘기면 상대경로로 대체.
PAGES_URL = os.environ.get("PAGES_URL", "").rstrip("/")
ONESIGNAL_APP_ID = os.environ.get("ONESIGNAL_APP_ID", "")
# 정보통신망법상 이메일에는 발신자 연락처 + 수신거부 방법을 밝혀야 한다.
# 별도 시크릿을 새로 요구하지 않으려고 이미 있는 SENDER_EMAIL을 재사용한다.
CONTACT_EMAIL = os.environ.get("SENDER_EMAIL", "")


def build_entries(today: date) -> list[dict]:
    raw = collect_bizinfo() + collect_kstartup()
    entries = []
    for it in raw:
        dleft = days_left(it["deadline"], today)
        if dleft is not None and dleft < 0:
            continue  # 이미 마감된 건은 제외
        it["days_left"] = dleft
        it["tags"] = guess_categories(it["title"], it["agency"], it["source"])
        entries.append(it)

    # 마감 임박순 정렬. days_left가 None(상시/소진형)인 건 맨 뒤로 보낸다.
    entries.sort(key=lambda x: (x["days_left"] is None, x["days_left"] if x["days_left"] is not None else 0))
    return entries


def render_item_line(it: dict) -> str:
    tag_str = "".join(f"[{t}]" for t in it["tags"])
    region_str = f"[지역:{it['region']}]" if it["region"] else ""
    dday = f"[D-{it['days_left']}] " if it["days_left"] is not None else "⚠️ "
    deadline_str = it["deadline_note"] if it["deadline_note"] else "정보 없음"
    return (
        f"<li><strong>{dday}{escape(tag_str)}{escape(region_str)} "
        f"<a href=\"{escape(it['detail_url'])}\">{escape(it['title'])}</a></strong> "
        f"({escape(it['agency'])}) — 마감: {escape(deadline_str)} · 출처: {escape(it['source'])}</li>"
    )


def _onesignal_snippet() -> str:
    if not ONESIGNAL_APP_ID:
        return ""
    return f"""
<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>
<script>
  window.OneSignalDeferred = window.OneSignalDeferred || [];
  OneSignalDeferred.push(function(OneSignal) {{
    OneSignal.init({{ appId: "{ONESIGNAL_APP_ID}" }});
  }});
</script>"""


SUBSCRIBE_BOX = """
<div style="border:2px solid #1a56db;border-radius:8px;padding:1rem;margin:1.5rem 0;">
  <strong>📬 매일 아침, 이 페이지를 이메일로 받아보세요</strong>
  <p style="margin:.5rem 0;font-size:.9rem;">
    <!-- TODO(운영자): Brevo 가입 후 "웹 폼" 임베드 코드로 이 블록을 통째로
         교체할 것 (MY_SETUP_CHECKLIST.md 참고). 그 전까지는 메일로 신청받는
         임시 방식으로 동작한다. -->
    아래 메일로 "구독 신청"이라고 보내주시면 등록해드립니다:
    <a href="mailto:{contact}?subject=지원금헌터%20구독신청">{contact_display}</a>
  </p>
</div>"""


def render_html(entries: list[dict], today: date, *, embeddable: bool = False, for_email: bool = False) -> str:
    # entries는 이미 "날짜 있는 건 먼저, 마감 임박순"으로 정렬돼 있으므로
    # 앞쪽 TOP_N개를 그대로 잘라 쓰면 된다.
    top = entries[:TOP_N]
    top_html = "\n".join(render_item_line(e) for e in top)

    if embeddable:
        # 위젯 페이지는 TOP3만 보여주는 초소형 버전 — 임베드용
        return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>지원금헌터 위젯</title>
<style>
  body {{ font-family: -apple-system, "Malgun Gothic", sans-serif; margin: 0; padding: .8rem; font-size: .85rem; }}
  h1 {{ font-size: .9rem; margin: 0 0 .5rem; }}
  li {{ margin-bottom: .4rem; }}
  a {{ color: #1a56db; text-decoration: none; }}
</style></head>
<body>
<h1>🎯 오늘의 마감임박 지원금 (지원금헌터)</h1>
<ul>{top_html or "<li>표시할 항목이 없습니다.</li>"}</ul>
<p style="font-size:.75rem;color:#888">Powered by <a href="{PAGES_URL or '.'}" target="_blank">지원금헌터</a></p>
</body></html>"""

    rest = entries[TOP_N:]
    domestic = [e for e in rest if "해외" not in e["tags"]]
    intl = [e for e in entries if "해외" in e["tags"]]
    rest_html = "\n".join(render_item_line(e) for e in domestic)
    intl_html = "\n".join(render_item_line(e) for e in intl)
    intl_section = f"""
<h2>🌐 국내 체류 외국인 창업가를 위한 영문 공고 ({len(intl)}건)</h2>
<ul>
{intl_html}
</ul>""" if intl else ""

    widget_link = f"{PAGES_URL}/widget.html" if PAGES_URL else "widget.html"
    page_url = f"{PAGES_URL}/" if PAGES_URL else ""
    top_title = top[0]["title"] if top else "오늘의 지원사업"
    description = f"마감임박 D-{top[0]['days_left']}: {top_title[:60]}" if top and top[0]["days_left"] is not None else "정부·지자체 지원금·지원사업 마감임박 데일리 큐레이션"
    og_tags = f"""
<meta property="og:title" content="지원금헌터 — {today.isoformat()}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:type" content="website">
{f'<meta property="og:url" content="{escape(page_url)}">' if page_url else ''}
<link rel="alternate" type="application/rss+xml" title="지원금헌터 RSS" href="feed.xml">""" if not for_email else ""
    subscribe_html = "" if (for_email or embeddable) else SUBSCRIBE_BOX.format(
        contact=CONTACT_EMAIL or "미설정",
        contact_display=CONTACT_EMAIL or "(운영자가 SENDER_EMAIL을 아직 설정하지 않았습니다)",
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>지원금헌터 — {today.isoformat()} 마감임박 지원사업</title>
<meta name="description" content="{escape(description)}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ font-family: -apple-system, "Malgun Gothic", sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }}
  h1 {{ font-size: 1.4rem; }}
  h2 {{ font-size: 1.1rem; margin-top: 2rem; border-bottom: 2px solid #333; padding-bottom: .3rem; }}
  li {{ margin-bottom: .6rem; }}
  a {{ color: #1a56db; }}
  .updated {{ color: #666; font-size: .85rem; }}
</style>{og_tags}
{_onesignal_snippet()}
</head>
<body>
<h1>🎯 지원금헌터 — {today.isoformat()}</h1>
<p class="updated">매일 아침 GitHub Actions가 자동으로 갱신합니다 (PC를 꺼도 계속 발행됩니다).
RSS: <a href="feed.xml">feed.xml</a> · 캘린더: <a href="deadlines.ics">deadlines.ics</a> ·
<a href="{widget_link}">내 블로그에 위젯 심기</a> · <a href="archive/">지난 발행 검색</a></p>
{subscribe_html}
<h2>🔥 오늘의 마감임박 TOP {len(top)}</h2>
<ul>
{top_html or "<li>표시할 항목이 없습니다.</li>"}
</ul>

<h2>📂 전체 공고 ({len(domestic)}건)</h2>
<ul>
{rest_html or "<li>추가 공고가 없습니다.</li>"}
</ul>
{intl_section}
<hr>
<p style="font-size:.75rem;color:#888">지원금헌터{f' · 문의/수신거부: {escape(CONTACT_EMAIL)}로 회신' if CONTACT_EMAIL else ''} · <a href="{page_url}privacy.html">개인정보처리방침</a> · 이 메일은 구독 신청하신 분께만 발송됩니다.</p>
</body>
</html>"""


def render_rss(entries: list[dict], today: date) -> str:
    base = PAGES_URL or "https://example.github.io/benefit-hunter"
    items_xml = "\n".join(
        f"""    <item>
      <title>{escape(('[D-' + str(e['days_left']) + '] ') if e['days_left'] is not None else '')}{escape(e['title'])}</title>
      <link>{escape(e['detail_url'])}</link>
      <description>{escape(e['agency'])} · 마감 {escape(e['deadline_note'])}</description>
      <guid isPermaLink="false">{escape(e['detail_url'])}-{today.isoformat()}</guid>
    </item>"""
        for e in entries
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>지원금헌터 — {today.isoformat()}</title>
    <link>{escape(base)}/</link>
    <description>마감임박 정부·지자체 지원금·지원사업 데일리 큐레이션</description>
{items_xml}
  </channel>
</rss>"""


def _ics_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def render_ics(entries: list[dict]) -> str:
    events = []
    for e in entries:
        if not e["deadline"]:
            continue
        dt = e["deadline"].strftime("%Y%m%d")
        uid = f"{abs(hash(e['detail_url']))}@benefit-hunter"
        summary = _ics_escape(f"[마감] {e['title']} ({e['agency']})")
        events.append(
            f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dt}T000000Z
DTSTART;VALUE=DATE:{dt}
SUMMARY:{summary}
URL:{e['detail_url']}
END:VEVENT"""
        )
    body = "\n".join(events)
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//benefit-hunter//deadlines//KO
CALSCALE:GREGORIAN
{body}
END:VCALENDAR"""


def render_email(entries: list[dict], today: date) -> tuple[str, str]:
    top = [e for e in entries if e["days_left"] is not None][:TOP_N]
    count = len(entries)
    subject = (
        f"[지원금헌터] 오늘 마감 D-{top[0]['days_left']}, {top[0]['title'][:20]} 외 {max(count - 1, 0)}건"
        if top else f"[지원금헌터] {today.isoformat()} 소식"
    )
    html = render_html(entries, today, for_email=True)  # 이메일 본문 — 구독 유도 박스는 뺀다(이미 구독자니까)
    return subject, html


def update_search_index(entries: list[dict], today: date) -> None:
    """검색 인덱스(JSON)에 오늘자 항목을 누적한다. 아카이브 검색 페이지가 이 파일을 읽는다."""
    index_path = os.path.join(DOCS_DIR, "search-index.json")
    existing: list[dict] = []
    if os.path.exists(index_path):
        try:
            with open(index_path, encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            existing = []  # 손상됐으면 새로 시작 — 검색 기능이 죽는 것보다 낫다

    existing = [row for row in existing if row.get("date") != today.isoformat()]  # 재실행 시 중복 방지
    for e in entries:
        existing.append({
            "date": today.isoformat(),
            "title": e["title"],
            "agency": e["agency"],
            "url": e["detail_url"],
            "tags": e["tags"],
        })

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False)


ARCHIVE_INDEX_HTML = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>지원금헌터 — 지난 발행 검색</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body { font-family: -apple-system, "Malgun Gothic", sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
  input { width: 100%; padding: .6rem; font-size: 1rem; box-sizing: border-box; margin-bottom: 1rem; }
  li { margin-bottom: .5rem; }
  .date { color: #888; font-size: .8rem; }
</style>
</head>
<body>
<h1>지난 발행 검색</h1>
<p><a href="../">오늘의 다이제스트로 돌아가기</a></p>
<input id="q" type="search" placeholder="예: 청년, 대구, 창업 ...">
<ul id="results"></ul>
<script>
  let data = [];
  fetch('../search-index.json').then(r => r.json()).then(d => { data = d; render(''); });
  function render(query) {
    const q = query.trim().toLowerCase();
    const filtered = q ? data.filter(row =>
      row.title.toLowerCase().includes(q) ||
      row.agency.toLowerCase().includes(q) ||
      (row.tags || []).some(t => t.toLowerCase().includes(q))
    ) : data;
    const ul = document.getElementById('results');
    ul.innerHTML = filtered.slice(0, 200).map(row =>
      `<li><span class="date">${row.date}</span> — <a href="${row.url}">${row.title}</a> (${row.agency})</li>`
    ).join('') || '<li>결과가 없습니다.</li>';
  }
  document.getElementById('q').addEventListener('input', e => render(e.target.value));
</script>
</body>
</html>"""


def main() -> None:
    today = today_kst()
    entries = build_entries(today)

    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    html = render_html(entries, today)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join(ARCHIVE_DIR, f"{today.isoformat()}.html"), "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join(ARCHIVE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(ARCHIVE_INDEX_HTML)

    with open(os.path.join(DOCS_DIR, "widget.html"), "w", encoding="utf-8") as f:
        f.write(render_html(entries, today, embeddable=True))

    with open(os.path.join(DOCS_DIR, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(render_rss(entries, today))

    with open(os.path.join(DOCS_DIR, "deadlines.ics"), "w", encoding="utf-8") as f:
        f.write(render_ics(entries))

    update_search_index(entries, today)

    # 유료 구독자 맞춤 필터링(send_email_brevo.py)이 재사용할 원본 구조화 데이터.
    # date는 JSON으로 못 담으니 문자열로 바꿔서 저장한다.
    serializable = [{**e, "deadline": e["deadline"].isoformat() if e["deadline"] else None} for e in entries]
    with open(os.path.join(OUTPUT_DIR, "entries.json"), "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False)

    subject, email_html = render_email(entries, today)
    with open(os.path.join(OUTPUT_DIR, "subject.txt"), "w", encoding="utf-8") as f:
        f.write(subject)
    with open(os.path.join(OUTPUT_DIR, "email_body.html"), "w", encoding="utf-8") as f:
        f.write(email_html)

    print(f"[build_digest] {len(entries)}건 처리 완료 (기업마당+K-Startup). 제목: {subject}")


if __name__ == "__main__":
    main()
