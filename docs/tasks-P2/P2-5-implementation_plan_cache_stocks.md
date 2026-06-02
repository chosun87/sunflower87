# 📊 온디맨드 수동 동기화 (On-Demand Sync) 버튼 신설 구현 계획

추가로 지시하신 '온디맨드 수동 동기화' 기능에 대한 구현 방향 및 상세 계획입니다.

- **로직 분리 위치 확정 (사용자 코멘트 수용):** 기존 `database.py`의 `init_db()` 내부에 있던 마스터 수집 로직을 `database.py` 안에 두지 않고, 비즈니스 로직 전용 파일인 **`be/services/cache_stocks.py` 내 `sync_cache_stocks(db)` 함수**로 완전히 분리 추출합니다. 이는 테이블명과 파일명을 일치시켜 관리 편의성을 높이는 훌륭한 아키텍처 개선입니다.

## Proposed Changes

### 백엔드 (어씨베)

#### [NEW] be/services/cache_stocks.py
- `database.py`의 `init_db()` 내부에 하드코딩 되어 있던 KRX 수집 로직(KOSPI, KOSDAQ, ETF 병합 및 Soft Delete 대조)을 뜯어내어 `sync_cache_stocks(db: Session)` 라는 독립 함수로 캡슐화하여 새로 생성합니다.
- 기존 `init_db()`는 단순히 세션을 열어 `sync_cache_stocks(db)`를 호출하고 끝내도록 깔끔하게 리팩토링합니다.

#### [MODIFY] be/routers/stocks.py
- 신규 엔드포인트 **`POST /api/stocks/sync_master`** 를 생성합니다.
- 라우터 내부에서 앞서 분리한 `database.sync_stock_masters(db)` 함수를 호출하여 수동 동기화를 즉시 실행하고 결과를 반환하도록 연결합니다.

### 프런트엔드 (어씨페)

#### [MODIFY] fe/src/pages/Dashboard.jsx
- 대시보드 화면 상단(보통 계좌 요약 카드나 헤더 영역 주변)에 PrimeReact `Button`을 사용해 **'🔄 종목 최신화'** 버튼을 신설합니다.
- 버튼에 `loading` 상태를 바인딩하여, 클릭 직후 API 응답이 올 때까지 버튼을 시각적으로 비활성화(Disabled/Spinner)하고 중복 클릭을 원천 차단합니다.
- 통신이 완료되면 `Toast` 컴포넌트를 호출하여 *"종목 마스터 데이터가 최신 상태로 동기화되었습니다."* 라는 완료 알림을 띄웁니다.

## Verification Plan
1. **백엔드 분리 무결성 검증:** 서버를 껐다 켤 때(`Lifespan` 동작), 이전과 동일하게 마스터 수집 로그(`[sunflower87] Successfully seeded complete KRX stock masters...`)가 정상적으로 콘솔에 출력되는지 확인합니다.
2. **API 수동 트리거 검증:** Swagger UI 또는 프런트엔드 버튼을 통해 `POST /api/stocks/sync_master`를 호출하고, 200 OK와 함께 백엔드 로그 상에 수집 프로세스가 돌아가는지 확인합니다.
3. **UX 록(Lock) 검증:** 프런트엔드 버튼 클릭 시 팽글팽글 도는 로딩 애니메이션이 걸리면서 연속 클릭이 막히는지, 그리고 작업 완료 후 Toast 메시지가 잘 노출되는지 시각적으로 테스트합니다.
