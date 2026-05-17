import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import {
  Card,
  DataTable,
  Column,
  Dropdown,
  Badge,
  Button,
} from "@components/PrimeReact";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const navigate = useNavigate();
  const { isSignedIn, isInitialized } = useAuth();

  const [recommendations] = useState([
    {
      name: "삼성전자",
      code: "005930",
      tag: "가치주",
      reason:
        "외국인 최근 5일 연속 순매수세 유입 및 20일 이동평균선 지지 확인.",
      score: 92,
    },
    {
      name: "현대차",
      code: "005380",
      tag: "저PBR/배당",
      reason:
        "정부 밸류업 프로그램 최대 수혜 예상. PBR 0.6배 수준으로 극심한 저평가 상태.",
      score: 88,
    },
    {
      name: "네이버",
      code: "035420",
      tag: "기술주",
      reason:
        "RSI 지수 30 부근으로 단기 과매도 구간 진입에 따른 기술적 반등 기대.",
      score: 85,
    },
  ]);

  useEffect(() => {
    if (isInitialized && !isSignedIn) {
      navigate("/login");
    }
  }, [isInitialized, isSignedIn, navigate]);

  useEffect(() => {
    // 백엔드 API로부터 계좌 데이터 바인딩
    fetch("http://localhost:8000/api/accounts")
      .then((res) => res.json())
      .then((resData) => {
        if (resData.status === "success") {
          setData(resData);
          // 초기값으로 첫 번째 계좌 선택
          setSelectedAccount(resData.accounts[0]);
        }
      })
      .catch((err) => console.error("데이터 로드 실패:", err));
  }, []);

  if (!data)
    return (
      <div className="flex align-items-center justify-content-center h-screen">
        <i
          className="pi pi-spin pi-spinner mr-2"
          style={{ fontSize: "2rem" }}
        ></i>
        <span className="text-xl font-bold">
          [sunflower87] 데이터를 불러오는 중...
        </span>
      </div>
    );

  // 수익률 컬러 템플릿
  const profitTemplate = (rowData) => {
    const isPositive = rowData.eval_profit_rate >= 0;
    return (
      <Badge
        value={`${rowData.eval_profit_rate}%`}
        severity={isPositive ? "danger" : "info"}
      />
    );
  };

  // 금액 포맷터
  const currencyTemplate = (amount) => {
    return amount.toLocaleString() + " 원";
  };

  return (
    <div className="p-4 md:p-6 lg:p-8">
      <div className="flex align-items-center justify-content-between mb-6">
        <h1 className="text-4xl font-bold text-900 m-0">
          🌻 sunflower87 Dashboard
        </h1>
        <span className="text-600">Decision Maker: SUN</span>
      </div>

      {/* 상단 총자산 요약 카드 */}
      <div className="grid mb-6">
        <div className="col-12 md:col-6">
          <Card title="통합 총자산" className="shadow-2 border-round">
            <h2 className="text-4xl text-primary font-bold m-0">
              {data.total_asset.toLocaleString()} 원
            </h2>
          </Card>
        </div>
        <div className="col-12 md:col-6">
          <Card title="계좌 선택" className="shadow-2 border-round">
            <Dropdown
              value={selectedAccount}
              options={data.accounts}
              onChange={(e) => setSelectedAccount(e.value)}
              optionLabel="alias"
              placeholder="조회할 계좌를 선택하세요"
              className="w-full"
            />
          </Card>
        </div>
      </div>

      {/* 오늘의 AI 추천 종목 섹션 */}
      <div className="mb-6">
        <div className="flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
          <div className="flex align-items-center gap-2">
            <i className="pi pi-sparkles text-amber-500 text-2xl"></i>
            <h2 className="text-2xl font-bold text-900 m-0">
              오늘의 AI 추천 종목
            </h2>
          </div>
          <Badge
            value="정량 지표 분석 기반"
            severity="warning"
            className="p-2 border-round font-semibold"
          />
        </div>

        <div className="grid">
          {recommendations.map((item, idx) => (
            <div key={idx} className="col-12 md:col-4">
              <Card
                className="shadow-2 hover:shadow-4 transition-all transition-duration-200 border-top-3 border-amber-500 h-full flex flex-column"
                style={{ borderRadius: "8px" }}
              >
                <div className="flex justify-content-between align-items-center mb-3">
                  <div>
                    <span className="text-xl font-bold text-900 mr-2">
                      {item.name}
                    </span>
                    <span className="text-500 text-sm font-semibold">
                      {item.code}
                    </span>
                  </div>
                  <Badge
                    value={item.tag}
                    className="bg-amber-100 text-amber-800 font-semibold p-1"
                  />
                </div>

                <p className="text-700 text-sm mb-4 line-height-3 flex-grow-1">
                  {item.reason}
                </p>

                <div className="flex justify-content-between align-items-center pt-3 border-top-1 border-100 mt-auto">
                  <span className="text-sm font-semibold text-600">
                    AI 추천 점수
                  </span>
                  <div className="flex align-items-center gap-2">
                    <span className="text-2xl font-bold text-amber-600">
                      {item.score}점
                    </span>
                    <Button
                      icon="pi pi-chevron-right"
                      className="p-button-rounded p-button-text p-button-sm text-amber-500"
                      aria-label="상세보기"
                    />
                  </div>
                </div>
              </Card>
            </div>
          ))}
        </div>
      </div>

      {/* 선택된 계좌의 보유 종목 상세 테이블 */}
      {selectedAccount && (
        <Card
          title={`${selectedAccount.alias} - 보유 종목 현황`}
          className="shadow-4 border-round"
        >
          <DataTable
            value={selectedAccount.stocks}
            responsiveLayout="stack"
            breakpoint="960px"
            sortMode="multiple"
            stripedRows
            className="mt-2"
          >
            <Column field="name" header="종목명" sortable></Column>
            <Column field="quantity" header="보유수량" sortable></Column>
            <Column
              field="avg_price"
              header="매입평단가"
              body={(rd) => currencyTemplate(rd.avg_price)}
              sortable
            ></Column>
            <Column
              field="current_price"
              header="현재가"
              body={(rd) => currencyTemplate(rd.current_price)}
              sortable
            ></Column>
            <Column
              field="eval_profit_rate"
              header="수익률"
              body={profitTemplate}
              sortable
            ></Column>
          </DataTable>
        </Card>
      )}
    </div>
  );
}
