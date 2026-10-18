# Microsoft Clarity (선택적, 기본 비활성)

`PUBLIC_CLARITY_PROJECT_ID`가 없거나 소문자 영숫자 형식이 아니면 **클라이언트 코드 자체를 HTML에 넣지 않는다**. Clarity 스크립트, 네트워크 요청, 쿠키, 동의 저장소 접근도 없다. ID를 임의 생성하거나 기본값으로 넣지 않는다. 현재 저장소 변수는 미설정이며 실제 수집 연동은 완료되지 않았다.

## 활성화 전 운영자 작업

1. 운영자가 https://clarity.microsoft.com/ 에서 로그인하고 `https://food.mingky.me/` 프로젝트를 생성한다. 계정/프로젝트 생성과 대시보드 변경은 이 코드 작업에 포함되지 않았다.
2. **Settings → Setup → Get tracking code**에서 Project ID 또는 설치 스니펫을 전달한다. 비밀번호·API 키·로그인 쿠키는 필요 없다. Project ID는 공개 식별자다.
3. **Settings → Setup**에서 쿠키 기본 사용을 **OFF**로 설정해 Consent Mode를 켜고, **Settings → Masking → Strict**를 확인한다. 이 사이트 코드도 `<body data-clarity-mask="True">`로 본문 전체와 자식을 마스킹한다. URL, CSS 및 기타 메타데이터까지 마스킹되는 것은 아니므로 주소에 개인정보를 넣지 않는다. `identify`/이메일/사용자 ID 전달은 구현하지 않았다.
4. 사이트가 18세 미만을 대상으로 하지 않는지 등 Microsoft 이용 조건과 운영자의 개인정보 고지 의무를 확인한다.
5. 확인된 ID를 저장소 **Settings → Secrets and variables → Actions → Variables**의 `PUBLIC_CLARITY_PROJECT_ID`에 설정한 후 **Deploy to GitHub Pages**를 다시 실행한다. 워크플로는 이 비밀이 아닌 변수를 Astro 빌드에 전달한다. 로컬은 동일 이름의 빌드 환경 변수를 사용한다.
6. 실제 ID로 배포한 뒤 아래 검증을 다시 한다. 단위 테스트의 `testonly` 값은 VM에서만 사용하며 네트워크로 전송하지 않는다. 이를 배포 변수에 사용해서는 안 된다.

## 동의와 철회

기존 사이트에는 동의 UI/개인정보 페이지가 없고 GA `G-J62KJ0FCZJ`가 항상 로드됐다. 이번 작업은 GA 동작을 바꾸지 않는다. 푸터 **분석 및 개인정보 안내 · Clarity 설정**은 Clarity 전용 opt-in이며 이 범위를 고지한다.

- ID 설정 후에도 방문자의 명시적 허용 전에는 Clarity 요청이 없다. 선택은 localStorage에 저장하고 180일 후 다시 허용해야 한다(방문만으로 기간 연장하지 않음). 저장 실패 시 다음 페이지는 기본 거부다.
- 허용 시에만 스크립트를 한 번 로드하며 `consentv2`를 큐에 먼저 전달한다. 정확한 키는 `analytics_Storage: 'granted'`, `ad_Storage: 'denied'`다. 광고 동의는 항상 거부한다.
- 거부/철회하면 두 범주를 `denied`로 전달하고, 사이트에서 접근 가능한 `_clck`/`_clsk` 쿠키를 지운 후 즉시 새로고침한다. Consent API 거부만으로는 cookieless 수집이 가능하므로 새 문서에서 SDK를 아예 로드하지 않는다. 다른 탭의 철회와 BFCache 복원도 확인한다.
- 이미 전송된 데이터/진행 중 요청을 소급 취소하거나 Microsoft 도메인의 쿠키까지 삭제한다고 보장하지 않는다. 실제 SDK 수집/철회 동작은 실제 프로젝트로 검증해야 한다.
- 비활성화: 저장소 변수를 지우고 재배포한다. 이는 새 문서의 로딩을 막지만 이미 열린 탭의 코드를 원격 종료하지 않는다.

## 검증

```bash
node --experimental-strip-types --test src/lib/*.test.mjs
npm run astro -- check
npm run build
```

VM 테스트는 실제 클라이언트 코드를 실행하되 DOM/스토리지/외부 SDK 경계를 모형으로 제공한다. 미설정·미동의 시 요청 없음, 허용 시 단일 loader와 v2 인자, 철회 시 쿠키 정리/새로고침, 동의 만료 및 탭 간 철회 등을 검증한다. **Microsoft 서버의 수집 성공을 검증한 것은 아니다.**

ID 없는 빌드에서는 모든 `dist/**/*.html`에 `clarity.ms`, `data-clarity-project-id`, `consentv2`가 없고 공통 레이아웃 페이지에는 `data-clarity-disabled`가 있는지 확인한다(검색엔진 소유권 확인용 HTML은 레이아웃 없음). 공개 페이지에서도 개발자 도구 Network의 Clarity 요청, `window.clarity`, `_clck`/`_clsk`가 없는지 확인한다.

활성화 이후에는 새 브라우저 상태에서 미동의→허용→철회를 확인하고, 허용 후 POST `/collect` 및 Clarity 프로젝트의 실시간 데이터가 관측되어야 실제 연동 완료다. 개인정보가 재생에 보이지 않는지 별도로 점검한다.

## 공식 근거

- [설치 및 검증](https://learn.microsoft.com/en-us/clarity/setup-and-installation/clarity-setup)
- [Consent API v2](https://learn.microsoft.com/en-us/clarity/setup-and-installation/clarity-consent-api-v2)
- [Consent Mode 설정](https://learn.microsoft.com/en-us/clarity/setup-and-installation/consent-mode)
- [동의 관리 및 cookieless 동작](https://learn.microsoft.com/en-us/clarity/setup-and-installation/consent-management)
- [마스킹](https://learn.microsoft.com/en-us/clarity/setup-and-installation/clarity-masking)
