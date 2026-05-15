import { useState, useEffect } from "react";
import {
  Card,
  DataTable,
  Column,
  Dropdown,
  Badge,
} from "@components/PrimeReact";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);

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
