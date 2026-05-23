# 🌻 Phase-2 (2, 3단계) 통합 구현 계획 (업데이트 됨)

본 문서는 sunflower87 프로젝트 Phase-2의 2단계(매매 검색 API 및 UI) 및 3단계(0주 보유 종목 송출 및 뷰어 필터링) 작업을 위한 구현 계획서입니다. 
**사용자의 피드백을 반영하여 최신화된 버전입니다.**

## ⚠️ User Review Required

변경된 계획이 만족스러우신지 최종 검토 후 승인(Approve)해 주시기 바랍니다.

## 📌 Proposed Changes

---

### [Backend: EARTH-BE]

#### [MODIFY] `be/routers/transactions.py`
- **목표:** 2단계 - 다중 조건 매매 내역 검색 API 확장
- **변경 사항:**
  - `GET /api/transactions` 엔드포인트에 4가지 Optional 쿼리 파라미터(`acc_cd`, `stock_code`, `start_date`, `end_date`)를 추가합니다.
  - SQLAlchemy `db.query(Transaction)`에 파라미터가 하나라도 존재할 경우 해당 조건만 `.filter()`를 동적으로 체이닝(Chaining)합니다. (독립적 검색 지원)
  - `start_date` 및 `end_date`는 날짜 문자열 파싱을 통해 기간 조회가 가능하도록 구현합니다.
  - 결과는 기존과 동일하게 연대기적 역순(`date.desc()`) 정렬을 유지합니다.

#### [MODIFY] `be/portfolio_service.py`
- **목표:** 3단계 - 0주 보유 종목 송출 로직 점검
- **변경 사항:**
  - 현재 로직 점검 결과, `quantity: 0` 종목은 정상적으로 `stocks` 테이블에 남아 프론트엔드로 송출되고 있습니다. 현재 로직을 최대한 유지하되 과거 매도 내역 누락 가능성이 없는지 점검을 마쳤습니다.

---

### [Frontend: EARTH-FE]

#### [MODIFY] `fe/src/components/dashboard/TransactionHistoryTab.jsx`
- **목표:** 2단계 - 거래 내역 검색 UI 구축
- **변경 사항:**
  - 상단에 검색 필터 폼을 구성하며, 컴포넌트 순서를 **[기간(Calendar)] → [계좌(Dropdown)] → [종목(InputText)]** 순서로 배치합니다.
  - 필드 하나만 입력해도 즉각적인 검색이 가능하도록 단일 조건 독립 쿼리를 지원합니다.
  - 검색 필터 상태가 변경될 때마다 부모(`Dashboard.jsx`)로부터 전달받은 `loadTransactions(filters)` 함수를 호출합니다.

#### [MODIFY] `fe/src/pages/Dashboard.jsx`
- **목표:** 2단계 - 동적 쿼리 바인딩
- **변경 사항:**
  - `loadTransactions` 함수가 필터 객체(`acc_cd`, `stock_code`, `start_date`, `end_date`)를 받아 동적으로 API 호출 파라미터를 생성하도록 로직을 갱신합니다. (작업 완료)
  - `TransactionHistoryTab`에 추가된 폼의 이벤트를 처리하도록 함수 참조를 연결합니다.

#### [MODIFY] `fe/src/components/dashboard/AssetDetailTab.jsx`
- **목표:** 3단계 - 계좌별 0주 종목 필터링 및 투명도 처리
- **변경 사항:**
  - 라디오 버튼 대신 **`[ ] 보유수 0주 포함`** 이라는 명시적인 Checkbox를 상단에 배치합니다. (기본값: false - 0주 미표시)
  - 체크박스가 해제된 상태(기본값)에서는 `acc.stocks` 배열을 렌더링할 때 `quantity > 0`인 종목만 보여줍니다.
  - 체크박스가 선택된 상태에서는 `quantity === 0` 종목도 포함하여 표출하되, `rowClassName` 속성을 통해 0주 행(Row)에 `opacity: 0.7` 스타일(또는 클래스)을 부여하여 시각적으로 휴면 종목임을 분명히 합니다.

## 🧪 Verification Plan

### Automated Tests / Manual Verification
1. **검색 필터 테스트:** 대시보드 하단 '매매 내역 히스토리' 탭에서 "기간만", "계좌만", "종목만" 입력했을 때 각각 독립적으로 검색되는지 확인합니다.
2. **0주 표시 테스트:** '보유 자산 상세' 탭에서 [보유수 0주 포함] 체크박스를 클릭 시, 0주 종목이 투명도 0.7 상태로 나타나거나 사라지는지 토글 동작을 확인합니다.
