# 네이버·구글 검색 노출 설정 (아주 상세 가이드)

## "사이트맵을 많이 등록하면 검색이 잘 되나요?" — 아니다

**개수는 중요하지 않다.** Search Console/서치어드바이저에 사이트맵을
여러 개 제출한다고 순위가 오르지 않는다. 사이트맵은 "검색엔진이 이
페이지들을 알아서 찾아가라"는 안내 지도일 뿐이라, 중요한 건 **그 지도가
내 사이트의 실제 콘텐츠를 빠짐없이·정확한 최신 날짜로 담고 있는가**다.
여러 개로 쪼개봤자 커버리지가 늘지 않으면 의미가 없다.

**실제로 검색 노출을 좌우하는 건 이런 것들이다** (전부 이미 이 프로젝트에
적용/자동화해뒀다):

| 요인 | 이 프로젝트에서 어떻게 했나 |
| --- | --- |
| 콘텐츠 최신성(freshness) | 매일 자동 발행 — 검색엔진이 "계속 살아있는 사이트"로 인식 |
| 사이트맵 완전성 + 정확한 lastmod | `sitemap.xml`을 실제 아카이브 파일 전부 기준으로 매일 자동 재생성 (2026-08-27부터) |
| 중복 콘텐츠 방지(canonical) | 오늘의 index.html과 그날의 아카이브 페이지가 내용이 같아서, 아카이브 쪽을 정식 주소로 지정 |
| 구조화 데이터(JSON-LD) | 각 페이지에 `CollectionPage`/`ItemList` 스키마 삽입 — 검색엔진이 "이게 목록형 콘텐츠"라고 더 잘 이해함 |
| 즉시 색인 알림(IndexNow) | 발행 직후 네이버·Bing에 바로 "이 URL들 바뀌었다"고 핑을 보냄 — 크롤러가 알아서 올 때까지 기다리지 않음 (구글은 이 프로토콜 미지원, 대신 수동 "색인 생성 요청" 사용) |
| 모바일 대응/속도 | 반응형 레이아웃, 정적 사이트라 로딩 매우 빠름 |
| 메타 설명/OG 태그 | 검색결과·SNS 공유 미리보기에 실제 내용이 나오게 함 |
| **백링크(외부에서 이 사이트로 들어오는 링크)** | 자동화로 채울 수 없는 유일한 항목 — GROWTH.md의 커뮤니티/SNS/블로그 공유가 여기 해당. 검색 순위에 가장 크게 기여하는 요소인데 사람이 직접 해야 하는 부분이다 |

즉 "설정 몇 개 더 켜서 검색 잘 되게" 하는 건 이미 거의 다 했고, 남은
가장 큰 레버는 **GROWTH.md에 있는 실제 확산 활동**(커뮤니티 공유, 다른
사이트에서 링크 받기)이다 — 이건 도구 설정이 아니라 콘텐츠/마케팅 활동
영역이라 자동화가 안 된다.

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
2. **네이버 서치어드바이저는 하위 경로를 아예 사이트로 등록받지 않는다.**
   (2026-08-27, 실제로 입력해봐서 확인함 — "URL을 호스트 단위로
   입력해주세요" 오류) 다행히 `smilemaskl.github.io`라는 호스트 자체가
   이미 등록돼 있어서, **새로 등록할 필요 없이 그 기존 사이트 안에서
   sitemap만 추가로 제출**하면 된다 — 아래 B번 참고. 돈 드는 커스텀
   도메인은 필요 없다.

---

## A. 구글 서치 콘솔 (Google Search Console) — 하위 경로도 문제없음

구글은 "URL 접두어(prefix)" 속성 유형을 지원해서 하위 경로도 별도
사이트처럼 등록할 수 있다. 네이버보다 훨씬 간단하다.

1. [search.google.com/search-console](https://search.google.com/search-console/welcome) 접속 → 구글 계정으로 로그인
2. 속성 유형에서 **"URL 접두어"** 선택 → `https://smilemaskl.github.io/benefit-hunter/` 입력
3. **(2026-08-27 실제 확인)** 이 계정으로 `https://smilemaskl.github.io/`
   (salary-calculator)가 이미 검증된 상태라서, 구글이 하위 경로도 자동으로
   같은 소유자로 인식해 **HTML 태그 복사 없이 바로 확인 팝업이 뜨고
   즉시 소유권 확인이 끝났다.** 이 경우 `GOOGLE_SITE_VERIFICATION`
   변수는 필요 없다. (혹시 자동으로 안 되고 HTML 태그 코드가 나오는
   계정이라면, `content="..."` 값만 복사해서 GitHub 저장소 Settings →
   Secrets and variables → Actions → Variables에 `GOOGLE_SITE_VERIFICATION`
   으로 등록하면 된다 — 코드는 이미 준비돼 있다)
4. 소유권 확인이 끝나면 개요(대시보드) 화면으로 이동한다. **여기서부터
   할 일**:
   - 왼쪽 메뉴 **"색인생성" → "Sitemaps"** 클릭 → 입력창에
     `sitemap.xml`만 입력(속성 주소 뒤에 자동으로 붙어
     `https://smilemaskl.github.io/benefit-hunter/sitemap.xml`이 됨) →
     **제출**
   - 왼쪽 메뉴 **"URL 검사"** 클릭 → 상단 검색창에
     `https://smilemaskl.github.io/benefit-hunter/` 붙여넣고 검사 →
     결과가 나오면 **"색인 생성 요청"** 버튼 클릭
   - 개요 화면의 "실적"/"색인생성" 카드에 "데이터를 처리하는 중이므로
     며칠 후에 다시 확인해 보세요"라고 뜨는 건 **정상**이다(오류 아님) —
     처음 등록하면 항상 이렇게 뜨고, 보통 며칠~2주 뒤부터 데이터가 쌓인다

---

## B. 네이버 서치어드바이저 — 확정된 사실 (2026-08-27, 실제 오류 화면으로 확인)

`https://smilemaskl.github.io/benefit-hunter/`를 사이트 등록에 입력하면
**"URL을 호스트 단위로 입력해주세요"**라는 오류가 뜬다. 이건 추측이 아니라
실제로 확인된 사실이다 — **네이버 서치어드바이저는 하위 경로(subpath)를
별도 사이트로 등록하는 기능 자체가 없고, 오직 호스트(도메인/서브도메인)
단위로만 등록받는다.**

그런데 사이트 목록을 보면 **`https://smilemaskl.github.io`가 이미
26.08.26에 등록되어 있다**(salary-calculator 때 등록한 것). 이게 오히려
좋은 소식이다 — 네이버 입장에서 `smilemaskl.github.io`라는 호스트
전체가 이미 소유 확인이 끝난 상태이므로, **`/benefit-hunter/` 경로도
이미 그 호스트에 속한 것으로 취급된다.** 즉 새로 등록할 필요 없이,
**이미 있는 `smilemaskl.github.io` 사이트 항목을 그대로 이용해서
benefit-hunter의 사이트맵/URL만 추가로 제출**하면 된다. 커스텀 도메인을
살 필요가 없다.

### 지금 할 일 (돈 안 드는 방법)

1. [searchadvisor.naver.com](https://searchadvisor.naver.com) 사이트 관리
   화면에서, 새로 입력하지 말고 **사이트 목록에 이미 있는
   `https://smilemaskl.github.io` 링크를 클릭**해서 그 사이트의 관리
   화면으로 들어간다
2. 왼쪽 메뉴 **요청 → 사이트맵 제출**에서
   `https://smilemaskl.github.io/benefit-hunter/sitemap.xml`을 입력해
   제출한다 (등록된 호스트가 `smilemaskl.github.io`이므로 그 밑의
   어떤 경로든 사이트맵으로 제출 가능)
3. 왼쪽 메뉴 **요청 → 웹페이지 수집**(또는 "웹마스터 도구 확인"류 메뉴,
   화면에 따라 이름이 다를 수 있음)에서
   `https://smilemaskl.github.io/benefit-hunter/`를 직접 넣고 수집을
   요청한다 — 이러면 훨씬 빨리 크롤링 우선순위가 올라간다
4. `NAVER_SITE_VERIFICATION` 환경변수는 **필요 없다** — 이미 호스트
   전체가 검증된 상태라 별도 메타태그 인증이 불필요하다(코드에는 만들어
   뒀지만, 나중에 정말 별도 도메인으로 옮기는 경우가 아니면 안 써도 됨)
5. 반영까지는 보통 1~2주 정도 걸린다 — 그 사이 계속 매일 자동 발행이
   쌓이는 것 자체가 네이버가 "살아있는 사이트"로 판단하는 데 도움이 된다

### 그래도 굳이 완전히 독립된 사이트로 분리하고 싶다면 — 커스텀 도메인

위 방법으로 충분하지만, 만약 브랜드를 위해 `smilemaskl.github.io`와
완전히 분리된 주소(예: `jiwonhunter.kr`)를 갖고 싶다면 아래 방법도
있다(비용 발생, 지금 당장 필요한 건 아님).

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
