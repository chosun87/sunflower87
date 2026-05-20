# TASK-03: SQLite DB 기반 매수/매도 거래 내역 및 종목코드 자동 검색 UI 구현 (_FE_R1)

- **작성일:** 2026. 05. 17
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-FE(어띠페)

---

## 📌 [COMMON] 공통 요구사항
- 거래 내역 수동 등록 시 종목코드를 직접 입력하지 않고, **[종목명 기반 종목코드 자동 검색]** 인터페이스를 구축하여 UX를 개선한다.

## 🌍 [FE_TASK] 프런트엔드 상세 구현 지침
- **UI 구조화:** 메인 대시보드 하단에 PrimeReact의 `TabView` 컴포넌트를 배치하고 [탭 1: 보유 자산 상세], [2탭: 매매 내역 히스토리]로 분리하라.
- **종목 자동 완성 UI 구성:** 
  - `@components/PrimeReact`에서 `InputText`와 `Button`을 임포트하여 사용하라.
  - PrimeFlex의 `p-inputgroup` 클래스를 사용하여 `종목명 입력창`과 `검색 버튼(pi pi-search)`을 가로로 결합하라.
- **인터랙션 흐름:** 종목명 입력 후 검색 버튼 클릭 시 `GET /api/stocks/search?keyword={검색어}`를 호출하고, 반환된 코드를 종목코드 InputBox State에 자동 주입한 뒤 해당 인풋창은 `readOnly` 처리하라.
- **거래 내역 리스트:** `DataTable`을 활용해 내역을 리팅하고 `BUY`는 Red 톤, `SELL`은 Blue 톤 텍스트로 가시성을 확보하라.

## 🏁 완료 조건
1. 종목명 입력 후 검색 버튼을 누르면 종목코드 InputBox가 자동으로 채워지는가?
2. 모든 컴포넌트가 `@components/PrimeReact.js` 통제 규칙을 준수했는가?
