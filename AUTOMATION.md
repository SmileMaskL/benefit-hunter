# 완전 자동화 — PC를 꺼도 계속 발행되게 만들기

## 먼저 정직하게: Stibee만으로는 안 된다

원래 계획(README/CONTENT_CALENDAR)은 "매일 사람이 30분 큐레이션 → Stibee
에디터에 붙여넣고 수동 발송"이었다. 이건 **사람이 매일 PC 앞에 앉아야 한다**는
뜻이라 "PC를 꺼도 평생 무료로 운영"이라는 요구와 정면으로 부딪힌다.

2026-08-27에 Stibee 공식 도움말을 직접 확인한 결과:

> Stibee의 "자동 이메일"(조건 트리거 발송)과 이메일 발송 Open API는
> **Standard/Pro/Enterprise 유료 플랜부터 지원**된다. 무료 플랜은 사람이
> 에디터에서 직접 "발송" 버튼을 눌러야 나간다.

즉 Stibee 무료 플랜으로는 "PC 없이 자동 발송"이 구조적으로 불가능하다.
그래서 **수집·가공은 GitHub Actions(완전 무료 클라우드)로, 실제 이메일
발송은 Brevo(무료 API 발송 지원)로 옮겼다.** Stibee는 필요하면 나중에
유료 전환 시점에 다시 검토해도 된다(그때는 이미 매출이 있으니 유료 플랜
비용을 감당할 수 있다) — MONETIZATION.md 참고.

## 지금 이 폴더에 이미 만들어져 있고, 실제 라이브 데이터로 테스트까지 끝난 것

`automation/` 폴더의 코드는 2026-08-27에 실제로 실행해서 기업마당·K-Startup
에서 진짜 공고 40건을 가져와 `docs/index.html`, `docs/feed.xml`,
`docs/deadlines.ics`를 만드는 것까지 확인했다(가짜 예시가 아니라 리포에
남아있는 `docs/` 파일 자체가 그 실행 결과물이다).

| 파일 | 역할 |
| --- | --- |
| `automation/collect_bizinfo.py` | 기업마당 목록 페이지를 직접 파싱(공식 API·RSS가 없어서 페이지 구조 파싱) |
| `automation/collect_kstartup.py` | K-Startup **공식 RSS**(`/web/contents/rss/bizpbanc-ongoing.do`)로 목록을 받고, 각 공고 상세페이지에서 마감일을 읽음 |
| `automation/build_digest.py` | 두 소스를 합쳐 마감임박순 정렬 + 태깅 → 웹페이지/RSS/캘린더(.ics)/임베드 위젯/검색색인/이메일 본문 생성 |
| `automation/send_email_brevo.py` | Brevo 무료 API로 구독자에게 발송. `tier=paid` 구독자는 지역/태그 맞춤 필터링까지 자동 적용 (키·구독자 없으면 에러 없이 조용히 스킵) |
| `automation/notify_webhooks.py` | 디스코드/슬랙 웹훅으로 발행 요약 자동 중계 (설정 없으면 스킵) |
| `automation/notify_onesignal.py` | OneSignal로 브라우저 푸시 발송 (설정 없으면 스킵) |
| `.github/workflows/daily-digest.yml` | 매일 KST 08:00(평일)에 위 스크립트들을 순서대로 실행하는 GitHub Actions 워크플로 |

`docs/`는 GitHub Pages로 공개하도록 설계된 폴더다 — 이게 활성화되면
**사용자 PC와 완전히 무관하게, GitHub 서버에서 매일 자동으로 갱신되는
"오늘의 지원금" 웹페이지가 생긴다.** `docs/widget.html`(임베드용),
`docs/archive/index.html`(검색), `docs/search-index.json`(검색 데이터),
`docs/deadlines.ics`(캘린더 구독)도 같이 갱신된다. 새로 추가된 기능
전체 목록은 [FEATURES_BACKLOG.md](FEATURES_BACKLOG.md)의 "구현되어
테스트 끝남" 표 참고.

> ⚠️ GitHub Pages를 개인 무료 계정으로 쓰려면 저장소가 **Public**이어야
> 한다(Private는 GitHub Pro 유료부터). 그래서 `automation/subscribers.csv`
> 같은 개인정보 파일은 반드시 `.gitignore`로 막아둬야 하고, 구독자
> 명단을 클라우드에서 쓰려면 CSV를 통째로 GitHub Secret에 암호화하듯
> 넣는 방식(`SUBSCRIBERS_CSV_B64`)을 쓴다 — 자세한 건
> [MY_SETUP_CHECKLIST.md](MY_SETUP_CHECKLIST.md) 5번.

## 아직 자동화하지 않은 부분 (일부러)

- **온통청년(청년정책)**: 공식 오픈API가 있지만 회원가입 후 심사를 거쳐
  인증키를 발급받아야 해서(즉시 발급 아님), 실제 응답 스키마를 이번에
  검증하지 못했다. 확인 안 된 필드명을 추측해서 코드를 짜는 것보다,
  1단계는 기업마당+K-Startup만 자동화하고 온통청년은 계속 수동으로
  다루는 쪽을 택했다. 나중에 키를 발급받으면 `automation/collect_youthcenter.py`를
  같은 패턴(공용 dict 모양 반환)으로 추가하면 된다.
- **기업마당 파싱**은 공식 API가 아니라 페이지 구조 스크레이핑이다.
  bizinfo가 페이지를 개편하면 이 파서도 깨질 수 있다 — 그래서
  `build_digest.py`는 한쪽이 실패해도(빈 리스트 반환) 다른 쪽 결과만으로
  발행이 되도록 만들어져 있다(seller-monitor 프로젝트에서 얻은 것과 같은
  교훈: 죽을 수 있는 외부 의존은 "실패해도 전체가 안 죽게" 설계한다).

## 사용자가 직접 해야 하는 일 (계정·비밀정보라 대신할 수 없는 부분)

계정 생성·시크릿 등록 등 실제 클릭 순서는 전부
**[MY_SETUP_CHECKLIST.md](MY_SETUP_CHECKLIST.md)** 한 곳에 정리해뒀다
(GitHub 저장소·Pages·Brevo·구독자 명단·웹훅·푸시·법적 표기까지). 여기서
중복해서 적지 않는다 — 순서대로 따라가면 된다.

## 로컬에서 미리 테스트하는 법 (Windows)

```
cd automation
pip install -r requirements.txt
set PYTHONUTF8=1
python build_digest.py
python send_email_brevo.py
python notify_webhooks.py
python notify_onesignal.py
```

뒤 세 개는 관련 환경변수(Secrets)가 없으면 전부 "건너뜁니다" 메시지만
찍고 정상 종료한다 — 에러가 아니다.

`PYTHONUTF8=1`을 안 주면 터미널에 한글이 깨져 보일 수 있다(실제 생성된
파일 내용은 UTF-8로 정상이다 — 이건 Windows 콘솔 출력 인코딩 문제일
뿐이다). GitHub Actions는 Ubuntu에서 돌아가서 이 문제가 없다.

## "평생 무료"에 대한 정직한 단서

GitHub Actions·GitHub Pages·Brevo 무료 API는 **현재(2026-08-27) 기준
무료 정책이 유지되는 한** 무료다. 개발비 0원으로 시작할 수 있다는 뜻이지,
어느 회사도 "영원히 무료"를 법적으로 보장하지는 않는다 — 실제로 이번에
조사하면서 MailerLite가 2026년에 무료 플랜 한도를 줄인 사례를 직접
확인했다(SOURCES.md 스타일로 계속 이런 변화는 추적해야 한다). 다만
GitHub Actions·Pages는 수년간 매우 안정적으로 무료를 유지해온 서비스라
리스크가 상대적으로 낮고, Brevo도 무료 발송이 핵심 비즈니스 모델의
일부라 당장 없어질 가능성은 낮다. 구독자가 늘어 하루 300통을 넘기기
시작하면(=이미 MONETIZATION.md의 유료 전환 검토 구간과 맞물림) 그때
유료 전환 매출로 감당하면 된다.
