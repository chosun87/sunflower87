# 03_FE-01-review.md: 프론트엔드 실시간 주가 Polling 동기화 설계안

본 문서는 프론트엔드(React)에서 사용자 로그인 상태일 때 백엔드 API를 통해 실시간 주가를 수집하고 전역 상태를 동기화하는 메커니즘을 설계한 문서입니다.

## 1. 요구 사항 및 핵심 아이디어
- **위치**: 로그인 상태를 판별하는 `App.tsx` 내의 `<AuthGuard />` 컴포넌트 (또는 전용 Custom Hook)
- **동적 Polling 주기**: 초기 접속 시에는 즉시(0ms) 요청을 보내고, 백엔드로부터 응답받은 네이버 금융의 `pollingInterval` 값을 사용하여 다음 요청의 타이머 간격을 동적으로 조절합니다.

---

## 2. 시간외 거래가(overMarketPriceInfo) 실시간 반영 전략
네이버 실시간 API는 정규장 마감(15:30) 이후 시간외 단일가 등 거래가 발생하면 `overMarketPriceInfo` 필드를 반환합니다.

- **전략**: 시간외 가격을 현재가로 덮어쓰기 (Overwrite)
- **설명**: 장 마감 후 시간외 단일가 거래가 발생했을 경우, 백엔드 API에서 기존 정규장 종가(`closePrice`)를 버리고 시간외 거래가(`overPrice`)를 `Stock.current_price`로 덮어씌웁니다. 
- **효과**: 프론트엔드는 UI의 별도 수정 없이, 각 종목별로 수신한 `stockExchangeType`의 `endTime`(정규장 마감)과 `startTime` 정보를 기준으로 시간외 거래가(overPrice)를 반영하므로, 사용자의 자산과 수익률이 장 마감 이후에도 실제 최신 거래 가격에 맞춰서 역동적으로 갱신됩니다.

---

## 2. 전문가 의견 및 아키텍처 제안 (Best Practices)

의사결정권자님의 의견은 정확하게 실무 Best Practice와 일치합니다! 이를 좀 더 안정적으로 리액트 환경에서 구현하기 위해 아래 3가지 추가 제안을 드립니다.

### 💡 제안 1: 백엔드 응답에 `polling_interval` 추가
현재 백엔드의 `POST /api/stock_ohlcvs/current` API는 단순히 업데이트된 주식 목록만을 반환하고 있습니다. 프론트엔드가 동적 주기를 알기 위해서는 백엔드가 네이버에서 받은 `pollingInterval` 값을 프론트엔드로 전달해 주어야 합니다.
- **백엔드 수정 사항**: 네이버 API 응답의 `data.get("pollingInterval", 60000)` 값을 추출하여 JSON 응답 최상단에 함께 리턴하도록 수정합니다.

### 💡 제안 2: `setInterval` 대신 재귀적 `setTimeout` 활용
리액트에서 주기가 계속 변하는(Dynamic Interval) 타이머를 구현할 때 일반적인 `setInterval`을 사용하면 클리어(Clear)하고 다시 등록하는 과정이 매우 번거롭고 버그가 발생하기 쉽습니다. 
대신, 1회용 타이머인 **`setTimeout`을 API 응답이 끝난 직후에 재귀적으로 호출**하는 방식을 사용하면 훨씬 안전하게 동적 타이머를 구현할 수 있습니다.

### 💡 제안 3: `<AuthGuard>` 내부의 데이터 흐름 설계
`<AuthGuard />` 컴포넌트는 모든 보호된 라우트를 감싸고 있으므로(Mount 유지), 이 안에서 전역적으로 주가 갱신을 트리거하기에 최적의 장소입니다.
- `<AuthGuard>` 마운트 시 최초 1회 즉시 호출 (또는 60초 대기 후 호출)
- 백엔드 통신 완료 후 응답받은 `polling_interval`(예: 70000ms)을 추출
- `setTimeout`으로 70000ms 뒤에 다시 스스로를 호출하도록 예약
- 주가 갱신 성공 시 전역 상태(예: Zustand 스토어 갱신 또는 React Query의 `invalidateQueries`)를 갱신하여 전체 화면 리렌더링

---

## 3. 구현 예정 의사 코드 (Pseudo Code)

### 백엔드 (Python FastAPI)
```python
@router.post("/current")
def refresh_current_ohlcv(db: Session = Depends(get_db)):
    # ... 기존 로직 ...
    dynamic_interval = 60000 # 기본값
    
    for code in unique_codes:
        # 네이버 API 호출 ...
        data = response.json()
        dynamic_interval = data.get("pollingInterval", dynamic_interval)
        # ... 파싱 및 DB 적재 ...
        
    return {
        "status": "success", 
        "polling_interval": dynamic_interval, # 프론트엔드에 전달!
        "updated": updated
    }
```

### 프론트엔드 (React / AuthGuard.tsx)
```tsx
import { useEffect, useRef } from 'react';
import { api } from '../api'; // axios 또는 fetch 래퍼

export const AuthGuard = () => {
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // 재귀적으로 호출될 Polling 함수
    const fetchRealtimePrices = async (delay: number) => {
      timerRef.current = setTimeout(async () => {
        try {
          // 1. 백엔드 실시간 업데이트 트리거
          const res = await api.post('/api/stock_ohlcvs/current');
          const nextInterval = res.data.polling_interval || 60000;
          
          // 2. 만약 주가가 갱신되었다면 잔고 등 전역 데이터 Refetch
          if (res.data.updated.length > 0) {
              await fetchGlobalAccountsData(); // 계좌 상태 갱신 함수
          }

          // 3. 서버가 알려준 새로운 주기로 다음 타이머 예약!
          fetchRealtimePrices(nextInterval);
        } catch (error) {
          console.error("Polling failed", error);
          // 실패 시 기본 1분 후 재시도 (안전망)
          fetchRealtimePrices(60000); 
        }
      }, delay);
    };

    // 마운트 시 최초 60초(기본값) 타이머 개시
    fetchRealtimePrices(60000);

    // 컴포넌트 언마운트 (로그아웃 등) 시 타이머 정리
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  // ... 기존 렌더링 로직 (Outlet 등) ...
  return <Outlet />;
};
```

위 설계안을 통해 서버에는 부하를 주지 않으면서 프론트엔드는 완벽하게 장중/장마감 시간에 맞춰 스마트하게 실시간 데이터를 동기화할 수 있습니다.
