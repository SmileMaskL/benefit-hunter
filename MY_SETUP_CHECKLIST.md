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
| 매일 자동 실행(GitHub Actions) | ✅ 최소 1회 수동 실행으로 성공 확인함(`success`). 다음은 예정된 평일 KST 08:00에 스케줄대로 자동 실행됨 |
| Brevo(이메일 발송) | ⬜ **아직 안 함** — 아래 4번 |
| 구독자 명단 | ⬜ **아직 없음** — 아래 5번 |
| 결제/정산 계좌 | ⬜ **아직 아무 데도 설정 안 함** — 아래 "수익화 관련" 참고, 지금 당장은 필요 없음 |
| 디스코드/슬랙/OneSignal | ⬜ 선택 사항, 원할 때 |
| 개인정보처리방침(`docs/privacy.html`) | ⬜ 초안은 만들어놨지만 [대괄호] 안에 실제 이름/연락처를 아직 안 채움 |

즉 **"자동으로 매일 돌아가는 것" 자체는 이미 완성**돼 있다. 지금부터는
"이메일을 실제로 보내기" "돈을 실제로 받기" 단계이고, 이건 사용자
본인 계정이 필요해서 아래 순서대로 진행해야 한다.

---

## 1~3. GitHub 관련 (완료됨 — 참고용)

저장소 생성, Pages 활성화, `PAGES_URL` 변수 등록까지 전부 끝났다. 혹시
저장소를 다시 만들거나 다른 계정으로 옮기고 싶다면 이 문서의 이전 버전
방식(웹사이트에서 Public 저장소 생성 → Settings → Pages → `main`/`docs`)을
그대로 따라하면 된다.

## 4. Brevo 무료 계정 — 이메일 발송용 (다음 할 일)

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

## 5. 구독자 명단 등록 (구독자가 생기면)

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

## 6. (선택) 디스코드/슬랙 커뮤니티 중계

- 디스코드: 채널 설정 → 연동 → 웹훅 → URL 복사 → Secret `DISCORD_WEBHOOK_URL`
- 슬랙: 앱 설정 → Incoming Webhooks 활성화 → URL 복사 → Secret `SLACK_WEBHOOK_URL`

## 7. (선택) 브라우저 푸시 — OneSignal

- onesignal.com 가입 → 웹푸시 앱 등록(사이트 URL에
  `https://smilemaskl.github.io/benefit-hunter/` 입력) → App ID·REST API
  Key 확인
- Secrets에 `ONESIGNAL_APP_ID`, `ONESIGNAL_API_KEY` 등록
- 무료 한도(가입 화면에서 재확인)를 넘지 않는지 주기적으로 확인

## 8. 개인정보처리방침 내용 채우기 (권장)

`docs/privacy.html`을 열어 `[운영자 이메일 주소]`, `[이름 또는 상호]`,
`[YYYY-MM-DD]` 부분을 실제 정보로 바꾼다. 이 파일은
`automation/build_digest.py`가 자동으로 덮어쓰지 않으니 한 번만 고치면
계속 유지된다.

## 9. 웹페이지 구독 폼 완성하기 (권장)

지금은 `docs/index.html`에 "메일로 구독 신청" 방식의 임시 폼이 있다.
4번(Brevo)까지 끝냈다면, Brevo 대시보드에서 **캠페인 → 폼 → 새 웹 폼
만들기**로 진짜 구독 폼 임베드 코드를 받아서
`automation/build_digest.py`의 `SUBSCRIBE_BOX` 부분을 그 코드로
바꿔달라고 요청하면 된다(코드 수정이 필요한 부분이라 알려주면 처리한다).

---

## 수익화 관련 — "돈은 어디로 들어오나"는 아직 미설정

**지금은 결제도, 정산 계좌 등록도 아무 데도 안 되어 있다.** 이건
정상이다 — 아직 무료 구독자도 없는 단계에서 결제 인프라부터 만드는 건
MONETIZATION.md의 "하지 말아야 할 것"에도 적어둔 안티패턴이다. 실제로
돈을 받을 준비가 필요해지면(구독자 500~1,000명 근처) 아래 중 하나를
고르면 되고, **은행 계좌 등록은 그 플랫폼 화면에서 본인이 직접 해야
한다**(신원 확인이 필요한 금융 절차라 대신 처리 불가):

| 경로 | 계좌를 어디에 등록하나 |
| --- | --- |
| 크몽 | 크몽 판매자센터 → 정산 계좌 등록 |
| Stibee 유료 뉴스레터 | Stibee 유료 구독 설정 화면의 "정산 정보 등록"(계좌 신청서 제출) |
| 토스페이먼츠 등 자체 결제 | 사업자등록 후 PG 가입 심사 과정에서 사업자 명의 계좌 등록 |

자세한 각 경로의 장단점·수수료·전환 시점은 [MONETIZATION_HOWTO.md](MONETIZATION_HOWTO.md) 참고.

---

## 한눈에 보는 필수/선택 표

| 항목 | 필수 여부 | 상태 |
| --- | --- | --- |
| GitHub 저장소·Pages·`PAGES_URL` | 필수 | ✅ 완료 |
| `BREVO_API_KEY`, `SENDER_EMAIL` | 이메일 발송 원하면 필수 | ⬜ 대기 |
| `SUBSCRIBERS_CSV_B64` | 구독자 있으면 필수 | ⬜ 대기 |
| `DISCORD_WEBHOOK_URL`/`SLACK_WEBHOOK_URL` | 선택 | ⬜ 대기 |
| `ONESIGNAL_APP_ID`/`ONESIGNAL_API_KEY` | 선택 | ⬜ 대기 |
| `docs/privacy.html` 내용 채우기 | 권장(법적 대비) | ⬜ 대기 |
| 결제/정산 계좌 | 유료 전환 시점에 필요 | ⬜ 아직 필요 없음 |
