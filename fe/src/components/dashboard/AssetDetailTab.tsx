import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DataTable, Column, Badge, Button, Checkbox } from '@/assets/js/PrimeReact';

export default function AssetDetailTab({ accounts }) {
  const navigate = useNavigate();
  const [showZeroQty, setShowZeroQty] = useState(false);

  // --- [보유 자산 전용 내부 템플릿 렌더러 정의] ---

  const nameBodyTemplate = (rowData) => {
    return (
      <Button
        label={rowData.name}
        className="p-button-link p-0 text-left font-bold text-primary hover:underline"
        onClick={() => navigate(`/stock?code=${rowData.code}`)}
        tooltip="클릭 시 60거래일 캔들 차트 분석 페이지로 이동"
        tooltipOptions={{ position: 'top' }}
      />
    );
  };

  const quantityBodyTemplate = (rowData) => {
    return <span className="monospace">{rowData.quantity.toLocaleString()}</span>;
  };

  const currentPriceBodyTemplate = (rowData) => {
    return <span className="monospace">{rowData.current_price.toLocaleString()}</span>;
  };

  const avgPriceBodyTemplate = (rowData) => {
    const val = Math.floor(rowData.avg_price || 0);
    return <span className="monospace">{val.toLocaleString()}</span>;
  };

  const evalAmountBodyTemplate = (rowData) => {
    const val = Math.round(
      rowData.total_eval_amt !== undefined
        ? rowData.total_eval_amt
        : (rowData.quantity || 0) * (rowData.current_price || 0)
    );
    return <span className="monospace">{val.toLocaleString()}</span>;
  };

  const buyAmountBodyTemplate = (rowData) => {
    const buy_amount = Math.round(
      rowData.total_purchase_amt !== undefined
        ? rowData.total_purchase_amt
        : rowData.purchase_amount || 0
    );
    return <span className="monospace">{buy_amount.toLocaleString()}</span>;
  };

  const totalTaxFeeBodyTemplate = (rowData) => {
    const val = Math.round(rowData.total_tax_fee || 0);
    return <span className="monospace">{val.toLocaleString()}</span>;
  };

  const evalProfitBodyTemplate = (rowData) => {
    const buy_amount = Math.round(
      rowData.total_purchase_amt !== undefined
        ? rowData.total_purchase_amt
        : rowData.purchase_amount || 0
    );
    const profit = Math.round(
      rowData.total_profit_loss !== undefined
        ? rowData.total_profit_loss
        : (rowData.total_eval_amt !== undefined
            ? rowData.total_eval_amt
            : (rowData.quantity || 0) * (rowData.current_price || 0)) - buy_amount
    );

    if (buy_amount === 0 || profit === 0) {
      return <span className="monospace">0</span>;
    }

    const isPositive = profit > 0;
    const className = `monospace font-bold ${isPositive ? 'text-buy' : 'text-sell'}`;
    return (
      <span className={className}>
        {isPositive ? '+' : ''}
        {profit.toLocaleString()}
      </span>
    );
  };

  const profitTemplate = (rowData) => {
    const buy_amount =
      rowData.total_purchase_amt !== undefined
        ? rowData.total_purchase_amt
        : rowData.purchase_amount || 0;

    if (buy_amount === 0) {
      return <span className="monospace">0.00</span>;
    }

    const rate =
      rowData.return_rate !== undefined
        ? rowData.return_rate
        : buy_amount > 0
          ? (((rowData.quantity || 0) * (rowData.current_price || 0) - buy_amount) / buy_amount) *
            100
          : 0;

    if (rate === 0) {
      return <span className="monospace">0.00</span>;
    }

    const isPositive = rate > 0;
    const className = `monospace font-bold ${isPositive ? 'text-buy' : 'text-sell'}`;
    return (
      <span className={className}>
        {isPositive ? '+' : ''}
        {rate.toFixed(2)}
      </span>
    );
  };

  // --- [계좌 목록 렌더링 루프] ---

  const enrichedAccounts = useMemo(() => {
    return (accounts || []).map((acc) => {
      const totalEvalAmount = (acc.stocks || []).reduce((sum, s) => {
        const val =
          s.total_eval_amt !== undefined
            ? s.total_eval_amt
            : (s.quantity || 0) * (s.current_price || 0);
        return sum + val;
      }, 0);

      const totalPurchaseAmount = (acc.stocks || []).reduce((sum, s) => {
        const val =
          s.total_purchase_amt !== undefined ? s.total_purchase_amt : s.purchase_amount || 0;
        return sum + val;
      }, 0);

      const totalTaxFee = (acc.stocks || []).reduce((sum, s) => {
        return sum + (s.total_tax_fee || 0);
      }, 0);

      const totalProfit = (acc.stocks || []).reduce((sum, s) => {
        const buy_amount =
          s.total_purchase_amt !== undefined ? s.total_purchase_amt : s.purchase_amount || 0;
        const eval_amount =
          s.total_eval_amt !== undefined
            ? s.total_eval_amt
            : (s.quantity || 0) * (s.current_price || 0);
        const profit =
          s.total_profit_loss !== undefined ? s.total_profit_loss : eval_amount - buy_amount;
        return sum + profit;
      }, 0);

      const totalReturnRate =
        totalPurchaseAmount > 0 ? (totalProfit / totalPurchaseAmount) * 100 : 0;

      const isProfitPositive = totalProfit > 0;
      const profitClass = `monospace font-bold ${isProfitPositive ? 'text-buy' : totalProfit < 0 ? 'text-sell' : ''}`;

      const isRatePositive = totalReturnRate > 0;
      const rateClass = `monospace font-bold ${isRatePositive ? 'text-buy' : totalReturnRate < 0 ? 'text-sell' : ''}`;

      return {
        ...acc,
        totalEvalAmount,
        totalPurchaseAmount,
        totalTaxFee,
        totalProfit,
        totalReturnRate,
        isProfitPositive,
        profitClass,
        isRatePositive,
        rateClass,
      };
    });
  }, [accounts]);

  if (!accounts || accounts.length === 0) {
    return <div className="p-4 text-center text-500">조회 가능한 계좌 정보가 없습니다.</div>;
  }

  return (
    <>
      <div className="flex align-items-center mb-4 gap-2">
        <Checkbox
          inputId="cb-show-zero"
          checked={showZeroQty}
          onChange={(e) => setShowZeroQty(e.checked)}
        />
        <label htmlFor="cb-show-zero" className="font-bold text-700 cursor-pointer">
          보유수 0주 포함
        </label>
      </div>

      {enrichedAccounts.map((acc) => {
        const displayStocks = showZeroQty
          ? acc.stocks
          : (acc.stocks || []).filter((s) => s.quantity > 0);

        return (
          <div className="mt-3 mb-6" key={acc.acc_cd}>
            <div className="flex align-items-center justify-content-between mb-3 border-bottom-1 pb-2 border-100">
              <div className="flex align-items-center gap-3 w-full">
                <h3 className="text-xl font-bold m-0 text-700">{acc.alias} 보유 현황</h3>

                <div className="ml-auto flex align-items-center gap-2">
                  <span className="font-semibold text-800">예수금</span>
                  <span className="font-bold text-green-700">
                    {(acc.cash_balance !== undefined
                      ? acc.cash_balance
                      : acc.balance
                    ).toLocaleString()}{' '}
                    원
                  </span>
                </div>
              </div>
            </div>

            <DataTable
              value={displayStocks}
              responsiveLayout="stack"
              breakpoint="960px"
              sortMode="multiple"
              stripedRows
              rowClassName={(rowData) => (rowData.quantity === 0 ? 'opacity-70' : '')}
              emptyMessage="보유 중인 주식이 없습니다."
            >
              <Column
                field="name"
                header="종목명"
                body={nameBodyTemplate}
                sortable
                footer={<span className="font-bold">합계</span>}
              ></Column>
              <Column
                field="quantity"
                header="총 보유수량"
                align="right"
                body={quantityBodyTemplate}
                sortable
              ></Column>
              <Column
                field="current_price"
                header="현재가"
                align="right"
                body={currentPriceBodyTemplate}
                sortable
              ></Column>
              <Column
                field="avg_price"
                header="매입평단가"
                align="right"
                body={avgPriceBodyTemplate}
                sortable
              ></Column>
              <Column
                field="total_eval_amt"
                header="총 평가금액"
                align="right"
                body={evalAmountBodyTemplate}
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
                body={buyAmountBodyTemplate}
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
                body={totalTaxFeeBodyTemplate}
                sortable
                footer={
                  <span className="monospace font-bold">{acc.totalTaxFee.toLocaleString()}</span>
                }
              ></Column>
              <Column
                field="total_profit_loss"
                header="총 평가손익"
                align="right"
                body={evalProfitBodyTemplate}
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
                body={profitTemplate}
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
