"""지원금헌터 자동화 공용 유틸리티.

수집기(collect_*.py)는 전부 아래 딕셔너리 모양으로 항목을 반환한다:

    {
        "title": str,             # 공고명 (지역 태그 포함 원문 그대로, 예: "[대구] 2026년 ...")
        "agency": str,            # 소관기관/주관기관
        "region": str | None,     # 제목 앞 대괄호에서 뽑은 지역 (없으면 None = 전국)
        "source": str,            # "기업마당" | "K-Startup"
        "deadline": date | None,  # 마감일 (파싱 실패/상시모집이면 None)
        "deadline_note": str,     # 원문 마감 표기 그대로 (예: "예산 소진시까지")
        "detail_url": str,
    }

날짜 파싱과 D-day 계산, 카테고리 태깅처럼 두 수집기가 공통으로 쓰는 로직만
여기 모은다 — 사이트별 파싱(HTML 구조)은 각 collect_*.py에 둔다.
"""
from __future__ import annotations

import os
import re
import shutil
import traceback
from datetime import date, datetime

REGION_RE = re.compile(r"^\[([^\]]+)\]\s*")

# IndexNow(네이버·Bing이 지원하는 즉시 색인 알림 프로토콜) 검증용 키.
# 비밀값이 아니다 — 이 값을 담은 파일을 docs/{키}.txt로 공개 배포해서
# "이 사이트의 관리자가 보낸 요청이 맞다"는 걸 증명하는 용도일 뿐이다.
# build_digest.py가 이 키로 파일을 쓰고, notify_indexnow.py가 같은 키로
# 핑을 보낸다.
INDEXNOW_KEY = "74df0aedaa5bfc87859187d7d0a03f7b"

# 소진시까지 등 고정 마감일이 없는 상시모집 표현
ONGOING_MARKERS = ("소진", "상시", "예산 소진", "채용시", "선발시")


def extract_region(title: str) -> tuple[str | None, str]:
    """제목 앞의 '[대구]' 같은 지역 태그를 분리한다. 반환: (지역 또는 None, 태그 제거된 제목)."""
    m = REGION_RE.match(title)
    if not m:
        return None, title
    return m.group(1), title[m.end():].strip()


def parse_period(raw: str) -> tuple[date | None, str]:
    """'2026-08-24 ~ 2026-09-10' 또는 '2026.09.10(목) 16:00까지' 형태의 마감 표기를 파싱한다.

    반환: (마감일 date 또는 None, 원문 그대로의 note).
    상시모집·예산소진형 문구는 date=None으로 두고 note에 원문을 남긴다 — 억지로
    임의의 날짜를 채워 넣지 않는다(잘못된 D-day를 만드는 것보다 "모름"이 안전하다).
    """
    note = " ".join(raw.split())
    if any(marker in note for marker in ONGOING_MARKERS):
        return None, note

    # 날짜 패턴 두 개(시작~종료)를 모두 뽑아 마지막 것을 마감일로 쓴다.
    dates = re.findall(r"(\d{4})[.\-](\d{1,2})[.\-](\d{1,2})", note)
    if not dates:
        return None, note

    y, mo, d = dates[-1]
    try:
        return date(int(y), int(mo), int(d)), note
    except ValueError:
        return None, note


def days_left(deadline: date | None, today: date) -> int | None:
    if deadline is None:
        return None
    return (deadline - today).days


HANGUL_RE = re.compile(r"[가-힣]")


def is_english_title(title: str) -> bool:
    """한글이 전혀 없는 제목이면 영문/해외 공고로 본다.

    K-Startup RSS에는 실제로 "Startup Korea Special Visa" 같은 영문 전용
    공고가 섞여 있다(국내 체류 외국인 창업가 대상). 번역 없이도 이런 건
    그대로 골라내는 것만으로 "외국인 창업가를 위한 섹션"을 만들 수 있다.
    """
    return not HANGUL_RE.search(title)


def guess_categories(title: str, agency: str, source: str) -> list[str]:
    """제목/기관명 키워드로 대략적인 세그먼트 태그를 추정한다.

    완벽한 분류가 목적이 아니라 "3초 스캔"을 돕는 힌트다. 애매하면 태그를
    비워두는 쪽을 택한다(잘못된 태그로 안 맞는 독자를 낚는 것보다 낫다).
    """
    tags: list[str] = []
    text = f"{title} {agency}"
    if source == "K-Startup" or "창업" in text:
        tags.append("예비창업")
    if any(k in text for k in ("소상공인", "자영업", "착한가격업소", "식품", "점포")):
        tags.append("소상공인")
    if any(k in text for k in ("청년", "청소년")):
        tags.append("청년")
    if is_english_title(title):
        tags.append("해외")
    return tags


def matches_subscriber_filters(entry: dict, region_filter: str, tags_filter: list[str]) -> bool:
    """유료 구독자의 맞춤 필터(지역/태그)에 이 공고가 해당하는지 본다.

    필터가 비어 있으면(설정 안 한 값) 그 기준은 무시하고 통과시킨다 —
    "지역만 설정하고 태그는 안 정한" 구독자도 정상적으로 걸러지게 하려는
    의도다. 지역이 없는(=전국 대상) 공고는 어떤 지역 필터에도 항상 매치시킨다.
    """
    if region_filter and entry.get("region") and region_filter not in entry["region"]:
        return False
    if tags_filter and not (set(tags_filter) & set(entry.get("tags", []))):
        return False
    return True


def today_kst() -> date:
    # GitHub Actions 러너는 UTC로 동작하므로, 워크플로에서 이미 KST 기준
    # 스케줄(daily-digest.yml 참고)로 맞춰 실행한다는 전제 하에 실행 시점의
    # 날짜를 그대로 KST 날짜로 취급한다(실행 시각이 KST 08:00대이므로
    # UTC 날짜와 KST 날짜가 어긋나는 자정 근접 구간이 아니다).
    return datetime.utcnow().date()


# ---------- Log/Error, Log/Success 공용 로깅 ----------
# 자동화 스크립트(collect_*.py, build_digest.py, notify_*.py, send_email_brevo.py)가
# 성공/실패를 저장소에 남기는 공용 유틸리티. 저장소 루트의 Log/Error 또는
# Log/Success 아래에 월 폴더(YYYY-MM)를 만들고, 그 안에 날짜별 파일로 이어 붙인다.
# daily-digest.yml이 Log/ 를 커밋하므로 GitHub에 그대로 기록이 남는다.

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_ROOT = os.path.join(_REPO_ROOT, "Log")
LOG_RETENTION_MONTHS = 6


def _write_log(kind: str, script_name: str, message: str) -> None:
    now = datetime.utcnow()
    today = now.strftime("%Y-%m-%d")
    month = today[:7]
    dir_path = os.path.join(LOG_ROOT, kind, month)
    os.makedirs(dir_path, exist_ok=True)
    log_path = os.path.join(dir_path, f"{kind}_log_{today}.txt")
    line = f"[{now:%Y-%m-%d %H:%M} UTC] [{script_name}] {message}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)


def log_success(script_name: str, message: str) -> None:
    _write_log("Success", script_name, message)


def log_error(script_name: str, message: str, exc: BaseException | None = None) -> None:
    if exc is not None:
        message = f"{message}\n" + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    _write_log("Error", script_name, message)


def cleanup_old_logs(retention_months: int = LOG_RETENTION_MONTHS) -> None:
    """Log/Error, Log/Success 안의 월 폴더(YYYY-MM) 중 retention_months보다
    오래된 폴더를 지운다. 스크립트가 돌 때마다 한 번씩 호출하면 된다."""
    now = datetime.utcnow()
    cutoff_year = now.year
    cutoff_month = now.month - retention_months
    while cutoff_month <= 0:
        cutoff_month += 12
        cutoff_year -= 1
    cutoff_label = f"{cutoff_year:04d}-{cutoff_month:02d}"

    for kind in ("Error", "Success"):
        dir_path = os.path.join(LOG_ROOT, kind)
        if not os.path.isdir(dir_path):
            continue
        for entry in os.listdir(dir_path):
            if re.fullmatch(r"\d{4}-\d{2}", entry) and entry < cutoff_label:
                shutil.rmtree(os.path.join(dir_path, entry), ignore_errors=True)
