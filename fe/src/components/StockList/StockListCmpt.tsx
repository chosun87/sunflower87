import { useState } from 'react';
import { DataTable, Column, Checkbox } from '@/assets/ts/PrimeReact';
import { useDataTableFoot } from '@/hooks/StockList/DataTableFoot';
import { useDataTableColumns } from '@/components/StockList/DataTableColumns';

export default function StockListCmpt({ accounts }: { accounts: any[] }) {
  // 계좌별 '0주 포함' 상태 관리
  const [showZeroQtyMap, setShowZeroQtyMap] = useState<Record<string, boolean>>({});

  // 비즈니스 로직(총계 계산) 및 템플릿(UI 셀) 훅 호출
  const enrichedAccounts = useDataTableFoot(accounts);
  const columns = useDataTableColumns();

  if (!accounts || accounts.length === 0) {
    return <div className="p-4 text-center text-500">조회 가능한 계좌 정보가 없습니다.</div>;
  }

  return (
    <>
      {enrichedAccounts.map((acc) => {
        const isShowZero = !!showZeroQtyMap[acc.acc_cd];
        const displayStocks = isShowZero
          ? acc.stocks
          : (acc.stocks || []).filter((s: any) => s.quantity > 0);

        return (
          <div className="mb-4" key={acc.acc_cd}>
            {/* 헤더 타이틀 및 옵션 영역 */}
            <div className="flex align-items-center justify-content-between mb-3 border-bottom-1 pb-2 border-100">
              <div className="flex align-items-center w-full">
                <h3 className="text-xl font-bold m-0 text-700">
                  [{acc.acc_company_nm}] {acc.acc_nm} 보유 현황
                </h3>

                <div className="flex align-items-center gap-2 ml-5">
                  <Checkbox
                    inputId={`cb-show-zero-${acc.acc_cd}`}
                    checked={isShowZero}
                    onChange={(e) =>
                      setShowZeroQtyMap((prev) => ({ ...prev, [acc.acc_cd]: e.checked || false }))
                    }
                  />
                  <label
                    htmlFor={`cb-show-zero-${acc.acc_cd}`}
                    className="font-bold text-600 cursor-pointer text-sm"
                  >
                    보유수 0주 포함
                  </label>
                </div>

                <div className="ml-auto flex align-items-center gap-2">
                  <span className="font-semibold text-800">예수금</span>
                  <span className="font-bold text-green-700">
                    {(acc.cash_balance !== undefined
                      ? acc.cash_balance
                      : acc.balance || 0
                    ).toLocaleString()}{' '}
                    원
                  </span>
                </div>
              </div>
            </div>

            {/* 데이터 테이블 영역 */}
            <DataTable
              value={displayStocks}
              responsiveLayout="stack"
              breakpoint="960px"
              sortMode="multiple"
              multiSortMeta={[
                { field: 'quantity', order: -1 },
                { field: 'total_eval_amt', order: -1 }
              ]}
              stripedRows
              paginator
              rows={10}
              rowsPerPageOptions={[5, 10, 25, 50]}
              currentPageReportTemplate="총 {totalRecords} 건"
              paginatorTemplate="CurrentPageReport FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
              rowClassName={(rowData) => (rowData.quantity === 0 ? 'opacity-70' : '')}
              emptyMessage="보유 중인 주식이 없습니다."
            >
              <Column
                field="stock_name"
                header="종목명"
                body={columns.nameBodyTemplate}
                sortable
                footer={<span className="font-bold">합계</span>}
              ></Column>
              <Column
                field="quantity"
                header="총 보유수량"
                align="right"
                body={columns.quantityBodyTemplate}
                sortable
              ></Column>
              <Column
                field="current_price"
                header="현재가"
                align="right"
                body={columns.currentPriceBodyTemplate}
                sortable
              ></Column>
              <Column
                field="avg_price"
                header="매입평단가"
                align="right"
                body={columns.avgPriceBodyTemplate}
                sortable
              ></Column>
              <Column
                field="total_eval_amt"
                header="총 평가금액"
                align="right"
                body={columns.evalAmountBodyTemplate}
                sortable
                footer={
                  <span className="monospace font-bold">
                    {acc.totalEvalAmount.toLocaleString()}
                  </span>
                }
              ></Column>
              <Column
                field="total_purchase_amt"
                header="총 매수금액"
                align="right"
                body={columns.buyAmountBodyTemplate}
                sortable
                footer={
                  <span className="monospace font-bold">
                    {acc.totalPurchaseAmount.toLocaleString()}
                  </span>
                }
              ></Column>
              <Column
                field="total_tax_fee"
                header="총 세금+수수료"
                align="right"
                body={columns.totalTaxFeeBodyTemplate}
                sortable
                footer={
                  <span className="monospace font-bold">{acc.totalTaxFee.toLocaleString()}</span>
                }
              ></Column>
              <Column
                field="total_profit_loss"
                header="총 평가손익"
                align="right"
                body={columns.evalProfitBodyTemplate}
                sortable
                footer={
                  <span className={acc.profitClass}>
                    {acc.isProfitPositive ? '+' : ''}
                    {acc.totalProfit.toLocaleString()}
                  </span>
                }
              ></Column>
              <Column
                field="return_rate"
                header="수익률"
                align="right"
                body={columns.profitTemplate}
                sortable
                footer={
                  <span className={acc.rateClass}>
                    {acc.isRatePositive ? '+' : ''}
                    {acc.totalReturnRate.toFixed(2)}
                  </span>
                }
              ></Column>
            </DataTable>
          </div>
        );
      })}
    </>
  );
}
