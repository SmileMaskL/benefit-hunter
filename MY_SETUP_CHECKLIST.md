# 내 정보로 채워야 하는 부분 체크리스트

AUTOMATION.md가 "무엇을 왜 이렇게 만들었나"라면, 이 문서는 **"실제로
돌아가게 하려면 내가 어떤 계정을 만들고 어디에 무엇을 입력해야 하는가"**만
모은 실행 체크리스트다. 계정·결제·개인정보가 필요한 항목은 내가 대신
만들어줄 수 없다 — 전부 사용자 본인 명의/소유여야 하는 것들이다.

## 지금 상태 (2026-08-27 기준, 실제 확인함)

| 항목 | 상태 |
| --- | --- |
| GitHub 저장소 | ✅ 생성·푸시 완료 — https://github.com/SmileMaskL/benefit-hunter (Public) |
| GitHub Pages | ✅ 활성화 완료 — https://smilemaskl.github.io/benefit-hunter/ (실제 접속 확인함) |
| `PAGES_URL` 변수 | ✅ 등록 완료 |
| 매일 자동 실행(GitHub Actions) | ✅ 최소 2회 수동 실행으로 성공 확인함(`success`). 다음은 예정된 평일 KST 08:00에 스케줄대로 자동 실행됨 |
| 디자인(헤더/히어로/카드/다크모드/광고 자리) | ✅ salary-calculator와 같은 디자인 시스템으로 교체 완료 |
| **구글 애드센스/애널리틱스** | ⬜ **아직 안 함 — 수익화 1순위, 아래 4번** |
| Brevo(이메일 발송) | ⬜ 아직 안 함 — 아래 5번 |
| 구독자 명단 | ⬜ 아직 없음 — 아래 6번 |
| 결제/정산 계좌(구독료용) | ⬜ 아직 아무 데도 설정 안 함 — 아래 "수익화 관련" 참고, 구독자 500명대까지는 필요 없음 |
| 디스코드/슬랙/OneSignal | ⬜ 선택 사항, 원할 때 |
| 개인정보처리방침(`docs/privacy.html`) | ⬜ 초안은 만들어놨지만 [대괄호] 안에 실제 이름/연락처를 아직 안 채움 |

즉 **"자동으로 매일 돌아가는 것" + "디자인"은 이미 완성**돼 있다.
지금부터 가장 먼저 할 일은 **애드센스 신청**이다 — 구독자 없이도 승인만
나면 바로 수익이 시작되기 때문이다.

---

## 1~3. GitHub 관련 (완료됨 — 참고용)

저장소 생성, Pages 활성화, `PAGES_URL` 변수 등록까지 전부 끝났다. 혹시
저장소를 다시 만들거나 다른 계정으로 옮기고 싶다면 이 문서의 이전 버전
방식(웹사이트에서 Public 저장소 생성 → Settings → Pages → `main`/`docs`)을
그대로 따라하면 된다.

## 4. 구글 애드센스 · 애널리틱스 (최우선 — 수익화의 핵심)

**왜 최우선인가**: 구독자가 0명이어도 승인만 나면 바로 방문자 수에 비례해
수익이 발생한다. "무언가를 팔거나 빌려주는" 게 아니라 트래픽 자체가
돈이 되는 구조라서, 이 프로젝트가 원래 노리는 "최대한 많이·자주 찾아오게"
전략과 정확히 같은 방향이다. 자세한 배경은 MONETIZATION.md의 "①" 항목,
실행 절차는 MONETIZATION_HOWTO.md의 "경로 A" 참고.

**구글 애널리틱스(선택이지만 강력 추천, 완전 무료)**:
1. [analytics.google.com](https://analytics.google.com)에서 속성 생성
2. 측정 ID(`G-`로 시작) 확인
3. 저장소 **Settings → Secrets and variables → Actions → Variables 탭 →
   New repository variable** → `GA_MEASUREMENT_ID` = 그 값

**구글 애드센스(승인 필요)**:
1. [adsense.google.com](https://adsense.google.com)에서 사이트
   (`https://smilemaskl.github.io/benefit-hunter/`) 등록·심사 신청
   (콘텐츠가 2~4주 정도 쌓인 뒤 신청하는 게 유리함)
2. 승인 후 클라이언트 ID(`ca-pub-`로 시작)와 광고 단위별 슬롯 ID 확인
3. Variables 탭에 등록:
   - `ADSENSE_CLIENT_ID` = 클라이언트 ID
   - `ADSENSE_SLOT_TOP` / `ADSENSE_SLOT_MID` / `ADSENSE_SLOT_BOTTOM` =
     각 광고 단위 슬롯 ID (페이지 상단/중단/하단 3자리에 대응)
4. 애드센스 계정의 "지급" 메뉴에서 본인 은행 계좌·세금 정보 등록 —
   여기서부터는 구글이 매달 자동으로 입금해준다

이걸 안 채우면: 사이트에는 "광고 영역 — 애드센스 승인 후 표시됩니다"라는
빈 자리만 보이고(레이아웃은 이미 잡혀 있음), 값을 채우는 순간 다음
자동 발행부터 실제 광고로 바뀐다. **생성된 HTML 파일을 직접 손으로
고치면 안 된다** — 매일 자동으로 덮어써져서 사라진다. 반드시 위 Variables로
등록할 것.

## 5. Brevo 무료 계정 — 이메일 발송용

- [brevo.com](https://www.brevo.com) 가입 (신용카드 불필요로 알려져
  있음 — 가입 화면에서 재확인 권장)
- 발신자 이메일 주소 인증 (본인이 실제로 받을 수 있는 이메일)
- SMTP & API 메뉴에서 API 키 발급

등록 위치: `https://github.com/SmileMaskL/benefit-hunter` → **Settings →
Secrets and variables → Actions → Secrets 탭 → New repository secret**
- `BREVO_API_KEY` = 위에서 발급받은 키
- `SENDER_EMAIL` = Brevo에서 인증한 발신 이메일 (사이트 하단 "문의/수신거부"
  표시와 `docs/index.html`의 구독 신청 안내 메일 주소로도 그대로 쓰인다)

이걸 안 채우면: 이메일 발송은 계속 건너뛰지만, 웹페이지/RSS/캘린더/위젯은
지금처럼 정상 갱신된다.

## 6. 구독자 명단 등록 (구독자가 생기면)

- 로컬에서 `automation/subscribers.csv` 파일을 만든다 (컬럼:
  `email,name,tier,region,tags` — `subscribers.example.csv` 참고)
- 이 파일은 `.gitignore`에 이미 등록돼 있어 저장소(Public!)에 절대
  올라가지 않는다
- GitHub Actions(클라우드)가 발송하려면 이 CSV를 base64로 인코딩해서
  Secret으로 등록해야 한다:

  ```powershell
  [Convert]::ToBase64String([IO.File]::ReadAllBytes("automation\subscribers.csv"))
  ```

  출력된 문자열을 **Secrets 탭 → New repository secret →
  `SUBSCRIBERS_CSV_B64`**에 붙여넣는다. 구독자가 바뀔 때마다 반복 필요
  (자동화는 FEATURES_BACKLOG.md의 "Brevo 연락처 API 이전" 참고).

## 7. (선택) 디스코드/슬랙 커뮤니티 중계

- 디스코드: 채널 설정 → 연동 → 웹훅 → URL 복사 → Secret `DISCORD_WEBHOOK_URL`
- 슬랙: 앱 설정 → Incoming Webhooks 활성화 → URL 복사 → Secret `SLACK_WEBHOOK_URL`

## 8. (선택) 브라우저 푸시 — OneSignal

- onesignal.com 가입 → 웹푸시 앱 등록(사이트 URL에
  `https://smilemaskl.github.io/benefit-hunter/` 입력) → App ID·REST API
  Key 확인
- Secrets에 `ONESIGNAL_APP_ID`, `ONESIGNAL_API_KEY` 등록
- 무료 한도(가입 화면에서 재확인)를 넘지 않는지 주기적으로 확인

## 9. 개인정보처리방침 내용 채우기 (권장)

`docs/privacy.html`을 열어 `[운영자 이메일 주소]`, `[이름 또는 상호]`,
`[YYYY-MM-DD]` 부분을 실제 정보로 바꾼다. 이 파일은
`automation/build_digest.py`가 자동으로 덮어쓰지 않으니 한 번만 고치면
계속 유지된다.

## 10. 웹페이지 구독 폼 완성하기 (권장)

지금은 `docs/index.html`에 "메일로 구독 신청" 방식의 임시 폼이 있다.
5번(Brevo)까지 끝냈다면, Brevo 대시보드에서 **캠페인 → 폼 → 새 웹 폼
만들기**로 진짜 구독 폼 임베드 코드를 받아서
`automation/build_digest.py`의 `SUBSCRIBE_BOX` 부분을 그 코드로
바꿔달라고 요청하면 된다(코드 수정이 필요한 부분이라 알려주면 처리한다).

---

## 수익화 관련 — "돈은 어디로 들어오나"

| 경로 | 지금 상태 | 계좌를 어디에 등록하나 |
| --- | --- | --- |
| **구글 애드센스** (1순위) | ⬜ 4번 완료 후 시작 가능 | 애드센스 계정 → "지급" 메뉴 → 은행 계좌·세금 정보 등록. 구글이 매달 자동 입금 |
| 제휴 마케팅 | ⬜ 아직 미착수 (MONETIZATION_HOWTO.md 경로 B) | 가입하는 제휴 프로그램마다 각자의 정산 계좌 등록 화면에서 |
| Stibee 유료 뉴스레터 (구독자 500~1,000명 이후) | ⬜ 아직 필요 없음 | Stibee 유료 구독 설정 화면의 "정산 정보 등록"(계좌 신청서 제출) |
| 토스페이먼츠 등 자체 결제 (규모가 더 커진 뒤) | ⬜ 아직 필요 없음 | 사업자등록 후 PG 가입 심사 과정에서 사업자 명의 계좌 등록 |

**은행 계좌 등록은 각 플랫폼 화면에서 본인이 직접 해야 한다**(신원 확인이
필요한 금융 절차라 대신 처리 불가). 각 경로의 장단점·수수료·전환 시점은
[MONETIZATION_HOWTO.md](MONETIZATION_HOWTO.md) 참고.

---

## 한눈에 보는 필수/선택 표

| 항목 | 필수 여부 | 상태 |
| --- | --- | --- |
| GitHub 저장소·Pages·`PAGES_URL` | 필수 | ✅ 완료 |
| `ADSENSE_CLIENT_ID`, `ADSENSE_SLOT_TOP/MID/BOTTOM` | **수익화 1순위** | ⬜ 대기 |
| `GA_MEASUREMENT_ID` | 권장(트래픽 확인용) | ⬜ 대기 |
| `BREVO_API_KEY`, `SENDER_EMAIL` | 이메일 발송 원하면 필수 | ⬜ 대기 |
| `SUBSCRIBERS_CSV_B64` | 구독자 있으면 필수 | ⬜ 대기 |
| `DISCORD_WEBHOOK_URL`/`SLACK_WEBHOOK_URL` | 선택 | ⬜ 대기 |
| `ONESIGNAL_APP_ID`/`ONESIGNAL_API_KEY` | 선택 | ⬜ 대기 |
| `docs/privacy.html` 내용 채우기 | 권장(법적 대비) | ⬜ 대기 |
| 결제/정산 계좌(구독료용) | 유료 전환 시점에 필요 | ⬜ 아직 필요 없음 |
