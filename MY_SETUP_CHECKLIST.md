# 내 정보로 채워야 하는 부분 체크리스트

AUTOMATION.md가 "무엇을 왜 이렇게 만들었나"라면, 이 문서는 **"실제로
돌아가게 하려면 내가 어떤 계정을 만들고 어디에 무엇을 입력해야 하는가"**만
모은 실행 체크리스트다. 계정·비밀정보가 필요한 항목은 내가 대신 만들어줄
수 없다 — 전부 사용자 본인 명의/소유여야 하는 것들이다.

지금 상태: **로컬(D:\Lee\benefit-hunter)에만 존재하고, 아직 어디에도
푸시/공개되지 않았다.** 아래 순서대로 하나씩 처리하면 된다.

---

## 1. GitHub 저장소 만들기 (필수)

- 이 PC에는 이미 `github.com/SmileMaskL` 계정으로 푸시 가능한 Git
  자격증명(Git Credential Manager)이 설정돼 있다 — `salary-calculator`가
  `smilemaskl.github.io`로 실제 배포된 걸 확인했다
- **github.com에서 직접 새 저장소를 만들어야 한다** (예: 저장소 이름
  `benefit-hunter`) — 이건 웹사이트에서 클릭 몇 번이면 되고, 만든 뒤
  알려주면 이 폴더를 `git init` → `git remote add` → `git push`로 올리는
  건 도와줄 수 있다(공개 저장소에 코드를 올리는 행동이라 실행 전 한 번
  더 확인받고 진행하겠다)
- ⚠️ **반드시 Public(공개) 저장소로 만들 것.** GitHub Pages를 무료로
  쓰려면 개인 무료 계정 기준 저장소가 Public이어야 한다(Private는 GitHub
  Pro 유료 계정부터 가능 — 2026-08-27 확인). `automation/subscribers.csv`는
  `.gitignore`로 이미 막아뒀으니 구독자 이메일 같은 개인정보가 실수로
  공개되진 않지만, 커밋하기 전엔 항상 `git status`로 한 번 더 확인하는
  습관을 들일 것

## 2. GitHub Pages 켜기 (필수)

저장소 푸시 후: **Settings → Pages → Source: `Deploy from a branch` →
Branch: `main` / `/docs`** 선택 → 저장. 몇 분 뒤
`https://smilemaskl.github.io/<저장소명>/`으로 오늘의 다이제스트 페이지가
뜬다.

## 3. Actions 변수 등록 — `PAGES_URL` (필수, 위 URL이 확정된 뒤)

**Settings → Secrets and variables → Actions → Variables 탭 → New
repository variable**
- 이름: `PAGES_URL`
- 값: 2번에서 확인한 실제 주소 (예: `https://smilemaskl.github.io/benefit-hunter/`)

이걸 안 채우면: RSS·위젯 링크가 `https://example.github.io/benefit-hunter/`
같은 가짜 주소로 나간다 — 동작은 하지만 링크가 틀린 채로 나가니 꼭 채울 것.

## 4. Brevo 무료 계정 — 이메일 발송용 (필수, 이메일 발송을 원하면)

- [brevo.com](https://www.brevo.com) 가입 (신용카드 불필요로 알려져
  있음 — 가입 화면에서 재확인 권장)
- 발신자 이메일 주소 인증 (본인이 실제로 받을 수 있는 이메일)
- SMTP & API 메뉴에서 API 키 발급

**Settings → Secrets and variables → Actions → Secrets 탭 → New
repository secret**에 등록:
- `BREVO_API_KEY` = 위에서 발급받은 키
- `SENDER_EMAIL` = Brevo에서 인증한 발신 이메일 (이메일 본문 하단 "문의/
  수신거부" 표시에도 이 값이 그대로 쓰인다 — 정보통신망법상 발신자
  연락처 표기 의무를 이걸로 충족한다)

이걸 안 채우면: 이메일 발송은 건너뛰지만, 웹페이지/RSS/캘린더는 정상
생성된다(에러 안 남).

## 5. 구독자 명단 등록 (필요할 때)

- 로컬에서 `automation/subscribers.csv` 파일을 만든다 (컬럼:
  `email,name,tier,region,tags` — `subscribers.example.csv` 참고).
  `tier`가 `paid`이고 `region`/`tags`를 채운 사람만 맞춤 필터링된
  다이제스트를 받는다
- 이 파일은 절대 커밋하지 않는다(`.gitignore`에 이미 등록됨)
- GitHub Actions(클라우드)가 발송하려면 이 CSV를 **base64로 인코딩해서
  Secret으로** 넣어야 한다:

  ```powershell
  [Convert]::ToBase64String([IO.File]::ReadAllBytes("automation\subscribers.csv"))
  ```

  출력된 긴 문자열을 **Secrets 탭 → New repository secret →
  `SUBSCRIBERS_CSV_B64`**에 그대로 붙여넣는다. 구독자가 추가/변경될
  때마다 이 과정을 반복해서 시크릿 값을 갱신해야 한다(자동 아님 —
  FEATURES_BACKLOG.md의 "Brevo 연락처 API로 이전"이 이걸 자동화할
  다음 단계).

## 6. (선택) 디스코드/슬랙 커뮤니티 중계

- 디스코드: 채널 설정 → 연동 → 웹훅 → URL 복사 → Secret
  `DISCORD_WEBHOOK_URL`
- 슬랙: 앱 설정 → Incoming Webhooks 활성화 → URL 복사 → Secret
  `SLACK_WEBHOOK_URL`

## 7. (선택) 브라우저 푸시 — OneSignal

- onesignal.com 가입 → 웹푸시 앱 등록(사이트 URL에 3번에서 정한
  `PAGES_URL` 입력) → App ID·REST API Key 확인
- Secrets에 `ONESIGNAL_APP_ID`, `ONESIGNAL_API_KEY` 등록
- FEATURES_BACKLOG.md에 적어둔 대로, 무료 한도를 가입 화면에서 직접
  한 번 재확인할 것

## 8. 브랜드/법적 표기 — 내용을 직접 정해야 하는 부분

- README.md의 브랜드명(지원금헌터)·태그라인은 그대로 써도 되고 바꿔도
  된다 — 바꾸면 `automation/build_digest.py`, `automation/common.py`
  등 코드에는 브랜드명이 하드코딩돼 있지 않아서(제목 문자열 몇 군데
  제외) 큰 수정 없이 바꿀 수 있다
- **개인정보처리방침 페이지가 없다** — 이메일 주소를 수집하는 이상
  정보통신망법/개인정보보호법상 최소한의 처리방침 고지가 필요하다.
  `docs/privacy.html`을 간단히 만들어 "수집 항목(이메일), 이용 목적
  (뉴스레터 발송), 보유 기간, 문의처(본인 연락처)"만 명시하는 정도로
  시작해도 된다 — 원한다면 만들어줄 수 있으니 알려줄 것
- 유료 전환 시 사업자등록 여부·세무 처리는 MONETIZATION_HOWTO.md의
  "공통으로 꼭 지켜야 하는 것" 참고 — 최종 확정은 세무사 상담 권장

---

## 한눈에 보는 필수/선택 표

| 항목 | 필수 여부 | 어디서 |
| --- | --- | --- |
| GitHub 저장소(Public) | 필수 | github.com |
| GitHub Pages 활성화 | 필수 | 저장소 Settings → Pages |
| `PAGES_URL` 변수 | 필수 | 저장소 Settings → Actions → Variables |
| `BREVO_API_KEY`, `SENDER_EMAIL` | 이메일 발송 원하면 필수 | brevo.com 가입 후 Secrets 등록 |
| `SUBSCRIBERS_CSV_B64` | 구독자 있으면 필수 | 로컬 CSV → base64 → Secrets |
| `DISCORD_WEBHOOK_URL`/`SLACK_WEBHOOK_URL` | 선택 | 각 서비스 웹훅 설정 |
| `ONESIGNAL_APP_ID`/`ONESIGNAL_API_KEY` | 선택 | onesignal.com 가입 |
| `docs/privacy.html` | 권장(법적 대비) | 만들어달라고 요청하면 됨 |
