"""오늘의 다이제스트를 만든다: 수집 → 정렬/태깅 → HTML/RSS/ICS/위젯/검색색인 생성.

이 스크립트 하나로 다음을 전부 만든다.
- docs/index.html        : GitHub Pages로 공개되는 오늘의 웹 페이지 (salary-calculator와
  같은 디자인 시스템 — docs/css/style.css, docs/js/common.js 참고)
- docs/feed.xml          : 오늘 다이제스트의 RSS 미러
- docs/deadlines.ics     : 마감일 캘린더 구독 파일
- docs/widget.html       : 다른 사이트에 <iframe>으로 심는 초소형 위젯(TOP3만)
- docs/archive/YYYY-MM-DD.html : 그날 발행분 아카이브
- docs/archive/index.html      : 아카이브 목록 + 클라이언트 사이드 검색
- docs/search-index.json       : 검색용 데이터(날짜별로 계속 누적)
- automation/output/entries.json  : 오늘 항목의 원본 구조화 데이터 — send_email_brevo.py가
  유료 구독자 맞춤 필터링에 재사용한다
- automation/output/email_body.html / subject.txt : 무료 구독자용 기본 발송 본문

⚠️ 이 파일이 만드는 docs/index.html 등은 **매일 자동으로 덮어써진다.** 그래서
구글 애널리틱스 측정 ID·애드센스 클라이언트/슬롯 ID는 생성된 HTML 파일을
직접 손으로 고치면 안 되고(다음 실행에 사라짐), 반드시 아래 환경변수
(GitHub 저장소 Settings → Actions → Variables)로 넣어야 한다. 채워야 할
값과 위치는 MY_SETUP_CHECKLIST.md 참고. docs/privacy.html처럼 이 스크립트가
안 건드리는 정적 파일은 직접 고쳐도 유지된다.

실행 위치는 저장소 루트를 가정한다(`python automation/build_digest.py`).
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date
from html import escape

from collect_bizinfo import collect as collect_bizinfo
from collect_kstartup import collect as collect_kstartup
from common import INDEXNOW_KEY, days_left, guess_categories, today_kst

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
# 이메일보다 카카오톡을 훨씬 많이 쓴다는 피드백에 따라 구독 신청 채널을
# 카카오톡 중심으로 바꿨다. KAKAO_ID는 "카카오톡 ID로 검색"용, KAKAO_OPENCHAT_URL은
# 오픈채팅방을 만들면 그 초대 링크를 넣는 용도(있으면 원클릭 참여가 가능해서 더 낫다).
KAKAO_ID = os.environ.get("KAKAO_ID", "")
KAKAO_OPENCHAT_URL = os.environ.get("KAKAO_OPENCHAT_URL", "")

# 방문자가 많아질수록 수익이 커지는 광고(구글 애드센스) — "무언가를 팔거나
# 대여하는" 모델이 아니라 트래픽에 비례해 자동으로 붙는 수익이라 이 프로젝트의
# "최대한 많이/자주 찾아오게" 전략과 방향이 같다. 승인 전엔 자리만 예약해둔다.
GA_MEASUREMENT_ID = os.environ.get("GA_MEASUREMENT_ID", "")
ADSENSE_CLIENT_ID = os.environ.get("ADSENSE_CLIENT_ID", "")
# 구글/네이버 웹마스터 도구의 "HTML 태그" 소유확인 방식. 파일 업로드 방식 대신
# 이걸 쓰는 이유: docs/는 매일 자동으로 통째로 다시 생성되므로, 검증 파일을
# 手동으로 docs/에 넣어두면 다음 실행에 사라진다 — 환경변수(Variables)로 넣어야
# 영구적으로 유지된다.
GOOGLE_SITE_VERIFICATION = os.environ.get("GOOGLE_SITE_VERIFICATION", "")
NAVER_SITE_VERIFICATION = os.environ.get("NAVER_SITE_VERIFICATION", "")
ADSENSE_SLOTS = {
    "top": os.environ.get("ADSENSE_SLOT_TOP", ""),
    "mid": os.environ.get("ADSENSE_SLOT_MID", ""),
    "bottom": os.environ.get("ADSENSE_SLOT_BOTTOM", ""),
    # 본문 좌우 사이드 레일 광고 — 넓은 화면에서만 보인다(docs/css/style.css의
    # .side-rail 참고). 슬롯을 아직 하나만 만들었다면 같은 값을 양쪽에 등록해도
    # 동작은 하지만(정상), 애드센스 리포트에서 좌/우를 구분해서 보고 싶으면
    # 나중에 슬롯을 하나 더 만들어 등록하면 된다.
    "left": os.environ.get("ADSENSE_SLOT_LEFT", ""),
    "right": os.environ.get("ADSENSE_SLOT_RIGHT", ""),
}

# 제휴 마케팅(쿠팡파트너스, 금융상품 비교 등) 배너 — 애드센스와 같은 철학:
# 실제 제휴 링크가 생기기 전까지는 조용히 숨어있고, 값이 채워지면 자동으로
# 나타난다. MONETIZATION_HOWTO.md 경로 B 참고.
AFFILIATE_BANNER_URL = os.environ.get("AFFILIATE_BANNER_URL", "")
AFFILIATE_BANNER_TEXT = os.environ.get("AFFILIATE_BANNER_TEXT", "")
# 쿠팡 약관 + 공정위 추천보증 심사지침이 요구하는 필수 표시 문구.
# 쿠팡파트너스가 아닌 다른 제휴(금융상품 등)를 걸 땐 AFFILIATE_DISCLOSURE로
# 그 프로그램에 맞는 문구로 바꿔서 등록할 것.
AFFILIATE_DISCLOSURE = os.environ.get(
    "AFFILIATE_DISCLOSURE",
    "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.",
)


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


def _urgency(days_left_val: int | None) -> str:
    """마감 긴급도를 3단계 CSS 클래스로 — None(예산 소진시까지 등)도 언제 끝날지
    모른다는 점에서 사실 가장 긴급할 수 있어 urgent로 취급한다."""
    if days_left_val is None or days_left_val <= 3:
        return "urgent"
    if days_left_val <= 7:
        return "soon"
    return "normal"


def _tag_pills(it: dict) -> str:
    pills = "".join(f'<span class="tag-pill">{escape(t)}</span>' for t in it["tags"])
    if it["region"]:
        pills += f'<span class="tag-pill">📍{escape(it["region"])}</span>'
    return pills


def render_digest_card(it: dict) -> str:
    urgency = _urgency(it["days_left"])
    dday_text = f"D-{it['days_left']}" if it["days_left"] is not None else "⚠️ 상시/소진임박"
    return f"""<a class="digest-card" href="{escape(it['detail_url'])}" target="_blank" rel="noopener">
  <span class="dday-badge {urgency}">{dday_text}</span>
  <h3>{escape(it['title'])}</h3>
  <p class="meta">{escape(it['agency'])} · 마감 {escape(it['deadline_note'] or '정보 없음')} · {escape(it['source'])}</p>
  <div>{_tag_pills(it)}</div>
</a>"""


def render_digest_row(it: dict) -> str:
    urgency = _urgency(it["days_left"])
    dday_text = f"D-{it['days_left']}" if it["days_left"] is not None else "⚠️"
    return f"""<li>
  <span class="dday-badge {urgency}">{dday_text}</span>
  {_tag_pills(it)}
  <a href="{escape(it['detail_url'])}" target="_blank" rel="noopener">{escape(it['title'])}</a>
  <div class="meta">{escape(it['agency'])} · 마감 {escape(it['deadline_note'] or '정보 없음')} · 출처: {escape(it['source'])}</div>
</li>"""


def _ga_snippet() -> str:
    if not GA_MEASUREMENT_ID:
        return """
<!--
  구글 애널리틱스(방문자 수 확인, 완전 무료): analytics.google.com 에서 속성을
  만들고 측정 ID(G-로 시작)를 GitHub 저장소 Settings → Actions → Variables의
  GA_MEASUREMENT_ID에 등록하면 다음 자동 발행부터 이 자리에 실제 코드가 들어간다.
  자세한 방법은 MY_SETUP_CHECKLIST.md 참고.
-->"""
    return f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{ dataLayer.push(arguments); }}
  gtag('js', new Date());
  gtag('config', '{GA_MEASUREMENT_ID}');
</script>"""


def _adsense_head_snippet() -> str:
    if not ADSENSE_CLIENT_ID:
        return """
<!--
  구글 애드센스: 승인 완료 후 발급받은 클라이언트 ID(ca-pub-로 시작)를
  GitHub 저장소 Settings → Actions → Variables의 ADSENSE_CLIENT_ID에 등록하면
  다음 자동 발행부터 이 자리에 실제 코드가 들어간다. 개별 광고 자리(.ad-slot)를
  활성화하려면 ADSENSE_SLOT_TOP / ADSENSE_SLOT_MID / ADSENSE_SLOT_BOTTOM도
  함께 등록할 것. 자세한 방법은 MY_SETUP_CHECKLIST.md 참고.
-->"""
    return f"""
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT_ID}" crossorigin="anonymous"></script>"""


def _ad_slot(position: str) -> str:
    slot = ADSENSE_SLOTS.get(position, "")
    if ADSENSE_CLIENT_ID and slot:
        return f"""<div class="ad-slot">
  <ins class="adsbygoogle" style="display:block;width:100%" data-ad-client="{ADSENSE_CLIENT_ID}" data-ad-slot="{slot}" data-ad-format="auto" data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>"""
    return '<div class="ad-slot">광고 영역 — 애드센스 승인 후 이 자리에 표시됩니다 (MY_SETUP_CHECKLIST.md 참고)</div>'


def _ad_side(position: str) -> str:
    """본문 좌우의 사이드 레일 광고. 넓은 화면에서만 보이고(모바일은
    docs/css/style.css의 미디어 쿼리로 숨김), 슬롯이 없으면 빈 자리만 잡는다."""
    slot = ADSENSE_SLOTS.get(position, "")
    if ADSENSE_CLIENT_ID and slot:
        inner = f"""<ins class="adsbygoogle" style="display:inline-block;width:160px;height:600px" data-ad-client="{ADSENSE_CLIENT_ID}" data-ad-slot="{slot}"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>"""
    else:
        inner = ""
    return f'<aside class="side-rail {position}">{inner}</aside>'


def render_affiliate_banner() -> str:
    """제휴 링크 배너. URL이 없으면 빈 문자열(아무것도 안 뜸) — 애드센스와
    같은 "값 채우기 전엔 조용히 숨김" 패턴. 값이 있으면 법적으로 필요한
    고지 문구(AFFILIATE_DISCLOSURE)를 반드시 같이 표시한다."""
    if not AFFILIATE_BANNER_URL:
        return ""
    text = AFFILIATE_BANNER_TEXT or "추천 상품 보러 가기"
    return f"""<div class="related-site">
  <span class="icon">🛍️</span>
  <div class="txt"><strong>{escape(text)}</strong><span>{escape(AFFILIATE_DISCLOSURE)}</span></div>
  <a class="btn-secondary" href="{escape(AFFILIATE_BANNER_URL)}" target="_blank" rel="noopener sponsored">바로가기</a>
</div>"""


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


def render_subscribe_box() -> str:
    """구독 신청 박스. 카카오톡을 1순위로 보여준다(이메일은 회사 밖에서는
    잘 안 쓴다는 피드백 반영) — 오픈채팅방 링크가 있으면 원클릭 참여 버튼을,
    없으면 카카오톡 ID 검색 안내를 보여준다. 이메일은 보조 수단으로 유지한다.
    """
    if KAKAO_OPENCHAT_URL:
        kakao_block = f"""<a class="btn-primary" href="{escape(KAKAO_OPENCHAT_URL)}" target="_blank" rel="noopener" style="display:inline-block;text-decoration:none;margin-bottom:8px">💬 카카오톡 오픈채팅방 바로 참여하기</a>
    <p style="margin:4px 0 0">참여하면 매일 아침 이 방에 오늘의 다이제스트가 올라옵니다.</p>"""
    elif KAKAO_ID:
        kakao_block = f"""카카오톡에서 <strong>ID로 검색 → {escape(KAKAO_ID)}</strong> 추가 후
    "구독신청"이라고 메시지 보내주시면 등록해드립니다."""
    else:
        kakao_block = "(운영자가 카카오톡 연락처를 아직 설정하지 않았습니다)"

    email_block = (
        f'이메일도 받고 싶다면: <a href="mailto:{escape(CONTACT_EMAIL)}?subject=지원금헌터%20구독신청">{escape(CONTACT_EMAIL)}</a>로 "구독 신청"'
        if CONTACT_EMAIL else "(이메일 구독은 아직 준비 중입니다)"
    )

    return f"""<div class="subscribe-box">
  <strong>💬 카카오톡으로 매일 아침 새 소식 받아보기</strong>
  <p>
    {kakao_block}
  </p>
  <p style="font-size:.78rem;">{email_block}</p>
</div>"""

NAV_LINKS = """<a href="./">오늘의 발행</a>
      <a href="archive/">아카이브·검색</a>
      <a href="widget.html">위젯 심기</a>
      <a href="feed.xml">RSS</a>"""

# 이메일 클라이언트는 외부 스타일시트(<link>)를 대부분 무시하거나 잘라낸다.
# docs/css/style.css의 CSS 변수(var(--text) 등)도 구버전 Outlook 등에서
# 지원이 약해서, 이메일 전용으로 값을 하드코딩한 최소 <style> 블록을 따로 둔다.
EMAIL_STYLE = """<style>
  body { font-family: -apple-system, "Malgun Gothic", sans-serif; color:#191d28; }
  .section-title { font-size:1.05rem; font-weight:800; margin:24px 4px 14px; padding-bottom:8px; border-bottom:2px solid #191d28; }
  .digest-grid { display:block; }
  .digest-card { display:block; background:#fff; border:1px solid #e6e8ee; border-radius:14px; padding:16px 18px; margin-bottom:12px; color:#191d28; }
  .dday-badge { display:inline-block; font-size:.72rem; font-weight:800; padding:3px 9px; border-radius:999px; margin-bottom:8px; }
  .dday-badge.urgent { color:#dc2626; background:#fee2e2; }
  .dday-badge.soon { color:#d97706; background:#fef3c7; }
  .dday-badge.normal { color:#2563eb; background:#eef2ff; }
  .digest-card h3 { margin:0 0 6px; font-size:1rem; }
  .meta { margin:0; font-size:.82rem; color:#6b7280; }
  .tag-pill { display:inline-block; font-size:.7rem; font-weight:700; padding:2px 8px; border-radius:999px; background:#eef2ff; color:#2563eb; margin:0 4px 4px 0; }
  .digest-list { list-style:none; margin:0; padding:0; }
  .digest-list li { padding:10px 4px; border-bottom:1px solid #e6e8ee; font-size:.92rem; }
  .digest-list li a { color:#191d28; font-weight:600; }
</style>"""


def render_html(entries: list[dict], today: date, *, embeddable: bool = False, for_email: bool = False) -> str:
    # entries는 이미 "날짜 있는 건 먼저, 마감 임박순"으로 정렬돼 있으므로
    # 앞쪽 TOP_N개를 그대로 잘라 쓰면 된다.
    top = entries[:TOP_N]

    if embeddable:
        # 위젯 페이지는 TOP3만 보여주는 초소형 버전 — 임베드용, 자체 광고는 없음
        top_html = "\n".join(render_digest_row(e) for e in top)
        page_url = f"{PAGES_URL}/" if PAGES_URL else "."
        return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>지원금헌터 위젯</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="css/style.css">
<style>body{{margin:0;padding:.6rem;font-size:.85rem}} main{{padding:0;max-width:none}} h1{{font-size:.95rem;margin:0 0 .6rem}}</style>
</head>
<body>
<h1>🎯 오늘의 마감임박 지원금 (지원금헌터)</h1>
<ul class="digest-list">{top_html or "<li>표시할 항목이 없습니다.</li>"}</ul>
<p style="font-size:.72rem;color:var(--text-sub)">Powered by <a href="{page_url}" target="_blank">지원금헌터</a></p>
</body></html>"""

    rest = entries[TOP_N:]
    domestic = [e for e in rest if "해외" not in e["tags"]]
    intl = [e for e in entries if "해외" in e["tags"]]
    top_html = "\n".join(render_digest_card(e) for e in top)
    rest_html = "\n".join(render_digest_row(e) for e in domestic)
    intl_html = "\n".join(render_digest_row(e) for e in intl)
    intl_section = f"""
<h2 class="section-title">🌐 국내 체류 외국인 창업가를 위한 영문 공고 ({len(intl)}건)</h2>
<ul class="digest-list">
{intl_html}
</ul>""" if intl else ""

    widget_link = f"{PAGES_URL}/widget.html" if PAGES_URL else "widget.html"
    page_url = f"{PAGES_URL}/" if PAGES_URL else ""
    # index.html과 archive/YYYY-MM-DD.html은 발행 당일엔 내용이 완전히 같다
    # (같은 html 문자열을 그대로 두 곳에 저장하기 때문). 검색엔진이 이걸
    # "중복 콘텐츠"로 보지 않도록, 영구적으로 안 바뀌는 아카이브 쪽 주소를
    # 정식 주소(canonical)로 지정한다 — index.html은 매일 내용이 바뀌는
    # "오늘자 미리보기", 아카이브가 그날의 진짜 permalink라는 개념.
    canonical_url = f"{page_url}archive/{today.isoformat()}.html" if page_url else f"archive/{today.isoformat()}.html"
    top_title = top[0]["title"] if top else "오늘의 지원사업"
    description = f"마감임박 D-{top[0]['days_left']}: {top_title[:60]}" if top and top[0]["days_left"] is not None else "정부·지자체 지원금·지원사업 마감임박 데일리 큐레이션"
    site_verification = (
        (f'<meta name="google-site-verification" content="{escape(GOOGLE_SITE_VERIFICATION)}">\n' if GOOGLE_SITE_VERIFICATION else "")
        + (f'<meta name="naver-site-verification" content="{escape(NAVER_SITE_VERIFICATION)}">\n' if NAVER_SITE_VERIFICATION else "")
    )
    json_ld = ""
    if not for_email and not embeddable and page_url:
        item_list = [
            {"@type": "ListItem", "position": i + 1, "url": e["detail_url"], "name": e["title"]}
            for i, e in enumerate(entries[:10])
        ]
        ld = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": f"지원금헌터 — {today.isoformat()}",
            "url": canonical_url,
            "description": description,
            "mainEntity": {"@type": "ItemList", "itemListElement": item_list},
        }
        json_ld = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    og_tags = f"""
{site_verification}<link rel="canonical" href="{escape(canonical_url)}">
<meta property="og:title" content="지원금헌터 — {today.isoformat()}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:type" content="website">
{f'<meta property="og:url" content="{escape(page_url)}">' if page_url else ''}
<link rel="alternate" type="application/rss+xml" title="지원금헌터 RSS" href="feed.xml">
{json_ld}""" if not for_email else ""
    subscribe_html = "" if (for_email or embeddable) else render_subscribe_box()
    css_link = EMAIL_STYLE if for_email else '<link rel="stylesheet" href="css/style.css">'
    head_extra = "" if for_email else f"{_ga_snippet()}{_adsense_head_snippet()}"
    top_ad = "" if (for_email or embeddable) else _ad_slot("top")
    mid_ad = "" if (for_email or embeddable) else _ad_slot("mid")
    bottom_ad = "" if (for_email or embeddable) else _ad_slot("bottom")
    left_side = "" if (for_email or embeddable) else _ad_side("left")
    right_side = "" if (for_email or embeddable) else _ad_side("right")
    affiliate_html = "" if (for_email or embeddable) else render_affiliate_banner()
    header_nav = "" if for_email else f"""<header>
  <div class="header-inner">
    <a class="logo" href="./"><span class="logo-mark">🎯</span>지원금헌터</a>
    <nav>
      {NAV_LINKS}
    </nav>
    <button id="themeToggle" class="theme-toggle" onclick="toggleTheme()" aria-label="다크모드 전환">🌙</button>
  </div>
</header>"""
    scripts = "" if for_email else '<script src="js/common.js"></script>'

    body_count = f"오늘 마감임박 {len(top)}건 포함, 총 {len(entries)}건"
    soonest = top[0]["days_left"] if top and top[0]["days_left"] is not None else None
    giant = f"D-{soonest}" if soonest is not None else "NEW"
    urgent_count = sum(1 for e in entries if e["days_left"] is not None and e["days_left"] <= 3)
    startup_count = sum(1 for e in entries if "예비창업" in e["tags"])
    biz_count = sum(1 for e in entries if "소상공인" in e["tags"])
    intl_count = len(intl)

    quicknav = """<div class="quicknav">
      <a href="#top3"><span class="qicon">🔥</span>마감임박</a>
      <a href="#all"><span class="qicon">📂</span>전체공고</a>
      <a href="#intl"><span class="qicon">🌐</span>해외</a>
      <a href="archive/"><span class="qicon">🔍</span>아카이브</a>
      <a href="widget.html"><span class="qicon">🧩</span>위젯</a>
    </div>""" if intl_count else """<div class="quicknav">
      <a href="#top3"><span class="qicon">🔥</span>마감임박</a>
      <a href="#all"><span class="qicon">📂</span>전체공고</a>
      <a href="archive/"><span class="qicon">🔍</span>아카이브</a>
      <a href="widget.html"><span class="qicon">🧩</span>위젯</a>
    </div>"""

    hero = "" if for_email else f"""<section class="hero">
  <div class="hero-deco" aria-hidden="true">
    <svg class="blob-1" viewBox="0 0 200 200"><defs><linearGradient id="hg1" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#dc2626"/><stop offset="100%" stop-color="#7c3aed"/></linearGradient></defs><circle cx="100" cy="100" r="90" fill="url(#hg1)"/></svg>
    <svg class="blob-2" viewBox="0 0 200 200"><defs><linearGradient id="hg2" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#7c3aed"/><stop offset="100%" stop-color="#2563eb"/></linearGradient></defs><circle cx="100" cy="100" r="90" fill="url(#hg2)"/></svg>
  </div>
  <div class="hero-inner">
    <span class="hero-kicker">지원금헌터 · {today.isoformat()}</span>
    <div class="hero-giant">{giant}</div>
    <h1>오늘 마감임박 지원사업, 지금 확인하세요</h1>
    <p class="tagline">{escape(body_count)} · 기업마당 + K-Startup 공식 소스 실시간 수집</p>
    <div class="trust-badge on-dark"><span class="pulse-dot"></span> 매일 아침 GitHub Actions가 자동으로 갱신 — PC를 꺼도 계속 발행됩니다</div>
    <div class="hero-actions">
      <button class="btn-primary" onclick="shareCurrentPage('오늘의 마감임박 지원금 확인하세요')">🔗 오늘의 발행 공유하기</button>
      <a class="btn-secondary" href="{widget_link}">내 블로그에 위젯 심기</a>
    </div>
    {quicknav}
  </div>
</section>"""

    stat_bar = f"""<div class="stat-bar">
  <div class="stat-pill"><span class="num">{len(entries)}</span><span class="label">전체 공고</span></div>
  <div class="stat-pill"><span class="num">{urgent_count}</span><span class="label">D-3 이내</span></div>
  <div class="stat-pill"><span class="num">{startup_count}</span><span class="label">예비창업</span></div>
  <div class="stat-pill"><span class="num">{biz_count}</span><span class="label">소상공인</span></div>
  <div class="stat-pill"><span class="num">{intl_count}</span><span class="label">해외/영문</span></div>
</div>"""

    related_site = """<div class="related-site">
  <span class="icon">🧮</span>
  <div class="txt"><strong>같이 보면 좋은 사이트: SmileMaskL의 계산기</strong><span>연봉·퇴직금·육아휴직급여·재산세 계산기 — 지원금 받을 때 세금·수령액도 같이 확인하세요</span></div>
  <a class="btn-secondary" href="https://smilemaskl.github.io/" target="_blank" rel="noopener">바로가기</a>
</div>"""

    body_main = f"""<div class="page-shell">
{left_side}
<main>
{stat_bar}
{subscribe_html}
{top_ad}
<h2 class="section-title" id="top3">🔥 오늘의 마감임박 TOP {len(top)}</h2>
<div class="digest-grid">
{top_html or '<p>표시할 항목이 없습니다.</p>'}
</div>

{mid_ad}

<h2 class="section-title" id="all">📂 전체 공고 ({len(domestic)}건)</h2>
<ul class="digest-list">
{rest_html or "<li>추가 공고가 없습니다.</li>"}
</ul>
{f'<div id="intl">{intl_section}</div>' if intl_section else ""}
{related_site}
{affiliate_html}
{bottom_ad}
</main>
{right_side}
</div>""" if not for_email else f"""
{top_ad}
<h2 class="section-title">🔥 오늘의 마감임박 TOP {len(top)}</h2>
<div class="digest-grid">
{top_html or '<p>표시할 항목이 없습니다.</p>'}
</div>
<h2 class="section-title">📂 전체 공고 ({len(domestic)}건)</h2>
<ul class="digest-list">
{rest_html or "<li>추가 공고가 없습니다.</li>"}
</ul>
{intl_section}"""

    footer = "" if for_email else f"""<footer>
  지원금헌터{f' · 문의/수신거부: {escape(CONTACT_EMAIL)}로 회신' if CONTACT_EMAIL else ''} ·
  <a href="{page_url}privacy.html">개인정보처리방침</a>
</footer>"""
    footer_email = f'<p style="font-size:.75rem;color:#888">지원금헌터{f" · 문의/수신거부: {escape(CONTACT_EMAIL)}로 회신" if CONTACT_EMAIL else ""} · <a href="{page_url}privacy.html">개인정보처리방침</a> · 이 메일은 구독 신청하신 분께만 발송됩니다.</p>' if for_email else ""

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>지원금헌터 — {today.isoformat()} 마감임박 지원사업</title>
<meta name="description" content="{escape(description)}">
<meta name="viewport" content="width=device-width, initial-scale=1">
{css_link}{og_tags}{head_extra}
{_onesignal_snippet()}
</head>
<body>
{header_nav}
{hero}
{body_main}
{footer_email}
{footer}
{scripts}
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
        # Python 내장 hash()는 프로세스마다 값이 달라져서(해시 랜덤화) 같은
        # URL인데도 매일 실행마다 UID가 바뀌는 버그가 있었다 — 캘린더 앱은
        # UID로 "같은 일정의 갱신"을 판단하므로, 안 바뀌는 md5로 바꿔서
        # 아직 마감 안 된 같은 공고가 매일 새 일정으로 중복 추가되지 않게 한다.
        uid = f"{hashlib.md5(e['detail_url'].encode('utf-8')).hexdigest()}@benefit-hunter"
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
    html = render_html(entries, today, for_email=True)  # 이메일 본문 — 구독 유도 박스/광고는 뺀다
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


def render_archive_index() -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>지원금헌터 — 지난 발행 검색</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="../css/style.css">
</head>
<body>
{_onesignal_snippet()}
<header>
  <div class="header-inner">
    <a class="logo" href="../"><span class="logo-mark">🎯</span>지원금헌터</a>
    <nav>
      <a href="../">오늘의 발행</a>
      <a href="../widget.html">위젯 심기</a>
      <a href="../feed.xml">RSS</a>
    </nav>
    <button id="themeToggle" class="theme-toggle" onclick="toggleTheme()" aria-label="다크모드 전환">🌙</button>
  </div>
</header>
<main>
<h2 class="section-title">지난 발행 검색</h2>
<input id="q" type="search" placeholder="예: 청년, 대구, 창업 ..." style="width:100%;padding:.7rem;font-size:1rem;border:1.5px solid var(--border);border-radius:10px;margin-bottom:1rem;background:var(--card-bg);color:var(--text)">
<ul class="digest-list" id="results"></ul>
{_ad_slot("bottom")}
</main>
<footer>지원금헌터 · <a href="../privacy.html">개인정보처리방침</a></footer>
<script src="../js/common.js"></script>
<script>
  let data = [];
  fetch('../search-index.json').then(r => r.json()).then(d => {{ data = d; render(''); }});
  function render(query) {{
    const q = query.trim().toLowerCase();
    const filtered = q ? data.filter(row =>
      row.title.toLowerCase().includes(q) ||
      row.agency.toLowerCase().includes(q) ||
      (row.tags || []).some(t => t.toLowerCase().includes(q))
    ) : data;
    const ul = document.getElementById('results');
    ul.innerHTML = filtered.slice(0, 200).map(row =>
      `<li><span class="meta">${{row.date}}</span> — <a href="${{row.url}}" target="_blank" rel="noopener">${{row.title}}</a><div class="meta">${{row.agency}}</div></li>`
    ).join('') || '<li>결과가 없습니다.</li>';
  }}
  document.getElementById('q').addEventListener('input', e => render(e.target.value));
</script>
</body>
</html>"""


def render_sitemap(today: date) -> str:
    """sitemap.xml을 실제 아카이브 파일 목록 기준으로 매번 새로 만든다.

    이전엔 손으로 쓴 정적 sitemap.xml(URL 3개, lastmod 없음)이었다 — 검색
    엔진에 "이 사이트에 매일 새 페이지가 쌓인다"는 신호를 정확히 주려면
    실제로 존재하는 아카이브 페이지 전부와 정확한 최종수정일(lastmod)이
    있어야 한다. sitemap 자체를 여러 개 등록한다고 검색 순위가 오르는 게
    아니라, **이렇게 실제 콘텐츠를 빠짐없이·정확하게 담은 사이트맵 하나**가
    중요하다(SEO_SETUP.md 참고).
    """
    base = f"{PAGES_URL}/" if PAGES_URL else "https://smilemaskl.github.io/benefit-hunter/"
    urls = [(base, today, "daily", "1.0")]

    archive_files = sorted(
        f for f in os.listdir(ARCHIVE_DIR)
        if f.endswith(".html") and f != "index.html"
    ) if os.path.isdir(ARCHIVE_DIR) else []
    for fname in archive_files:
        try:
            d = date.fromisoformat(fname[:-len(".html")])
        except ValueError:
            continue  # 예상 못한 파일명은 조용히 건너뜀
        urls.append((f"{base}archive/{fname}", d, "never", "0.5"))

    urls.append((f"{base}archive/", today, "daily", "0.6"))
    urls.append((f"{base}privacy.html", today, "yearly", "0.2"))

    entries_xml = "\n".join(
        f"""  <url>
    <loc>{escape(loc)}</loc>
    <lastmod>{d.isoformat()}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{prio}</priority>
  </url>"""
        for loc, d, freq, prio in urls
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries_xml}
</urlset>"""


def render_kakao_text(entries: list[dict], today: date, subject: str) -> str:
    """카카오톡 오픈채팅방에 매일 복사·붙여넣기용 평문 요약.

    카카오톡 알림톡/브랜드메시지 자동 발송은 건당 비용이 드는 유료
    서비스라(FEATURES_BACKLOG.md 참고) 무료 자동화에는 못 넣었다. 대신
    이 파일을 매일 자동으로 만들어 `docs/kakao-message.txt`로 공개해두면,
    운영자가 매일 아침 이 주소를 열어 복사한 뒤 오픈채팅방에 붙여넣기만
    하면 된다(완전 자동은 아니지만 10초 이내로 끝나는 반자동).
    """
    lines = [f"🎯 지원금헌터 — {subject}", ""]
    page_url = f"{PAGES_URL}/" if PAGES_URL else ""
    for e in entries[:TOP_N]:
        dday = f"D-{e['days_left']}" if e["days_left"] is not None else "⚠️"
        lines.append(f"[{dday}] {e['title']} ({e['agency']})")
        lines.append(f"  마감: {e['deadline_note']} · {e['detail_url']}")
    lines.append("")
    lines.append(f"전체 목록 보기: {page_url or './'}")
    return "\n".join(lines)


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
        f.write(render_archive_index())

    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(render_sitemap(today))

    # IndexNow(네이버·Bing) 소유 검증용 키 파일 — notify_indexnow.py가 핑을
    # 보낼 때 이 파일이 실제로 공개돼 있어야 검색엔진이 신뢰한다.
    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)

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

    # 카카오톡 오픈채팅방 반자동 공유용 — automation/output/은 커밋 안 되니
    # (gitignore) 사람이 매일 열어볼 수 있게 docs/에도 공개해둔다.
    with open(os.path.join(DOCS_DIR, "kakao-message.txt"), "w", encoding="utf-8") as f:
        f.write(render_kakao_text(entries, today, subject))

    print(f"[build_digest] {len(entries)}건 처리 완료 (기업마당+K-Startup). 제목: {subject}")


if __name__ == "__main__":
    main()
