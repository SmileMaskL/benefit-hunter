# 네이버·구글 검색 노출 설정 (아주 상세 가이드)

## 먼저 알아야 할 것 — 지금 사이트 주소의 한계

`https://smilemaskl.github.io/benefit-hunter/`는 **`smilemaskl.github.io`라는
같은 도메인의 하위 경로(subpath)**다. 이게 검색엔진 등록에 두 가지 실무적
문제를 만든다.

1. **robots.txt는 무조건 도메인 루트(`smilemaskl.github.io/robots.txt`)만
   읽힌다.** `docs/robots.txt`(이 저장소의 파일)는 실제로는
   `smilemaskl.github.io/benefit-hunter/robots.txt`에 놓이는데, 크롤러는
   이 위치를 절대 보지 않는다. 다행히 루트의 `salary-calculator` 쪽
   robots.txt가 `Allow: /`(전체 허용)라서 크롤링 자체는 막혀 있지
   않지만, 거기 적힌 `Sitemap:` 줄은 salary-calculator 것만 가리키고
   있어서 이 사이트의 sitemap.xml은 자동으로 발견되지 않는다 → **아래처럼
   Search Console/서치어드바이저에 수동 제출이 필수다.**
2. **네이버 서치어드바이저가 하위 경로 등록을 거부할 수 있다.** 검색해봐도
   "루트 도메인이 이미 등록돼 있으면 하위 경로는 등록이 안 된다"는 사례가
   있다는 것만 확인했고, 100% 공식 문서로 못 박아 확인은 못 했다(정직하게
   밝힘). 그래서 아래에 **① 지금 주소로 먼저 시도하는 법**과 **② 막혔을
   때의 확실한 해결책(커스텀 도메인)**을 둘 다 정리했다.

---

## A. 구글 서치 콘솔 (Google Search Console) — 하위 경로도 문제없음

구글은 "URL 접두어(prefix)" 속성 유형을 지원해서 하위 경로도 별도
사이트처럼 등록할 수 있다. 네이버보다 훨씬 간단하다.

1. [search.google.com/search-console](https://search.google.com/search-console/welcome) 접속 → 구글 계정으로 로그인
2. 속성 유형에서 **"URL 접두어"** 선택 → `https://smilemaskl.github.io/benefit-hunter/` 입력
3. 소유권 확인 방법 중 **"HTML 태그"** 선택 → `<meta name="google-site-verification" content="....">` 형태의 코드가 나온다 → `content="..."` 안의 값만 복사
4. GitHub 저장소 **Settings → Secrets and variables → Actions → Variables
   탭 → New repository variable**:
   - 이름: `GOOGLE_SITE_VERIFICATION`
   - 값: 방금 복사한 값
5. 다음 자동 발행(또는 Actions 탭에서 수동 실행) 후, Search Console
   화면에서 **"확인"** 버튼 클릭 → 성공하면 소유권 확인 완료
6. 왼쪽 메뉴 **"Sitemaps"** → `sitemap.xml` 입력 → 제출
   (`https://smilemaskl.github.io/benefit-hunter/sitemap.xml`이 실제로
   제출되는 주소)
7. **"URL 검사"** 메뉴에 메인 페이지 주소를 넣고 **"색인 생성 요청"**을
   누르면 훨씬 빨리(보통 며칠 내) 색인이 시작된다

---

## B. 네이버 서치어드바이저 — 두 가지 경로

### B-1. 지금 주소로 먼저 시도 (하위 경로 등록)

1. [searchadvisor.naver.com](https://searchadvisor.naver.com) 접속 → 네이버
   계정 로그인 → **웹마스터 도구**
2. **사이트 관리 → 사이트 등록** → `https://smilemaskl.github.io/benefit-hunter/` 입력
3. 여기서 **"이미 등록된 사이트의 하위 경로입니다"** 같은 오류가 뜨면
   → B-2(커스텀 도메인)로 넘어갈 것. 오류 없이 등록이 되면 계속:
4. 소유확인 방법 중 **"HTML 태그"** 선택 → 메타태그의 `content="..."` 값
   복사
5. GitHub 저장소 Variables에 `NAVER_SITE_VERIFICATION` = 그 값으로 등록
   (구글과 동일한 방식, A번 4단계 참고)
6. 자동 발행 후 서치어드바이저에서 **"확인"** 클릭
7. **요청 → 사이트맵 제출**에서 `sitemap.xml` 제출
8. **요청 → 웹페이지 수집** 메뉴에서 메인 페이지 주소를 직접 넣고 수집
   요청하면 더 빨리 반영된다 (네이버는 보통 반영까지 1~2주 정도 걸림)

### B-2. 하위 경로 등록이 막힐 때 — 커스텀 도메인으로 해결 (확실한 방법)

이 방법을 쓰면 네이버 등록 문제 자체가 사라지고, 브랜드도 더 좋아진다
(README.md의 브랜드명 전략과도 맞음 — `지원금헌터`라는 이름을 도메인에도
쓸 수 있음).

1. 도메인 등록업체(가비아, 후이즈, Cloudflare Registrar, Namecheap 등)에서
   원하는 도메인 구매 — 예: `jiwonhunter.kr`, `jiwonhunter.com` 등
   (연 1만~2만원대가 일반적)
2. 구매한 도메인의 DNS 설정에서 **A 레코드** 4개를 GitHub Pages IP로 추가:
   ```
   185.199.108.153
   185.199.109.153
   185.199.110.153
   185.199.111.153
   ```
   (서브도메인을 쓰고 싶다면 `www` 같은 이름으로 GitHub Pages 기본
   주소(`smilemaskl.github.io`)를 가리키는 **CNAME 레코드** 하나만 추가해도 됨)
3. 도메인이 정해지면 알려주면, `docs/CNAME` 파일(도메인 이름 한 줄)을
   만들고 GitHub 저장소 **Settings → Pages → Custom domain**에 등록하는
   것까지 도와줄 수 있다 (도메인 구매 자체는 결제가 필요해서 본인이
   해야 함)
4. 커스텀 도메인이 붙으면 그게 **도메인 루트**가 되므로, robots.txt와
   sitemap.xml이 진짜로 그 위치에서 정상 작동하고, 네이버 등록도
   "하위 경로" 문제 없이 깨끗하게 된다

---

## 색인이 잘 안 될 때 체크리스트

- [ ] `GOOGLE_SITE_VERIFICATION`/`NAVER_SITE_VERIFICATION` 변수가 등록돼
      있고, 그 이후 자동 발행이 최소 1번 돌았는가 (Actions 탭에서 확인)
- [ ] 실제 페이지 소스보기(Ctrl+U)에서 `<meta name="google-site-verification"...`
      태그가 보이는가
- [ ] sitemap.xml을 브라우저로 직접 열어봤을 때 정상적으로 XML이 보이는가
      (`https://smilemaskl.github.io/benefit-hunter/sitemap.xml`)
- [ ] 색인 요청 후 최소 며칠~2주는 기다렸는가 (즉시 반영되지 않음)
- [ ] 콘텐츠가 매일 갱신되고 있는가 — 검색엔진은 "최근에도 계속 갱신되는
      사이트"를 더 자주, 더 우호적으로 재방문한다(이 프로젝트는 이미
      매일 자동 갱신되므로 이 조건은 충족됨)
