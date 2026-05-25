import { useNavigate } from 'react-router-dom';
import { Button } from '@/assets/ts/PrimeReact';

// 네비게이션이 필요한 템플릿 로직이 있으므로 커스텀 훅 형태로 제공
export function useDataTableColumns() {
  const navigate = useNavigate();

  const nameBodyTemplate = (rowData: any) => {
    return (
      <Button
        label={rowData.name || rowData.stock_name}
        className="p-button-link p-0 text-left font-bold text-primary hover:underline"
        onClick={() => navigate(`/stock?code=${rowData.code || rowData.stock_code}`)}
        tooltip="클릭 시 60거래일 캔들 차트 분석 페이지로 이동"
        tooltipOptions={{ position: 'top' }}
      />
    );
  };

  const quantityBodyTemplate = (rowData: any) => {
    return <span className="monospace">{rowData.quantity.toLocaleString()}</span>;
  };

  const currentPriceBodyTemplate = (rowData: any) => {
    return <span className="monospace">{(rowData.current_price || 0).toLocaleString()}</span>;
  };

  const avgPriceBodyTemplate = (rowData: any) => {
    const val = Math.floor(rowData.avg_price || 0);
    return <span className="monospace">{val.toLocaleString()}</span>;
  };

  const evalAmountBodyTemplate = (rowData: any) => {
    const val = Math.round(
      rowData.total_eval_amt !== undefined
        ? rowData.total_eval_amt
        : (rowData.quantity || 0) * (rowData.current_price || 0)
    );
    return <span className="monospace">{val.toLocaleString()}</span>;
  };

  const buyAmountBodyTemplate = (rowData: any) => {
    const buy_amount = Math.round(
      rowData.total_purchase_amt !== undefined
        ? rowData.total_purchase_amt
        : rowData.purchase_amount || 0
    );
    return <span className="monospace">{buy_amount.toLocaleString()}</span>;
  };

  const totalTaxFeeBodyTemplate = (rowData: any) => {
    const val = Math.round(rowData.total_tax_fee || 0);
    return <span className="monospace">{val.toLocaleString()}</span>;
  };

  const evalProfitBodyTemplate = (rowData: any) => {
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

  const profitTemplate = (rowData: any) => {
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

  return {
    nameBodyTemplate,
    quantityBodyTemplate,
    currentPriceBodyTemplate,
    avgPriceBodyTemplate,
    evalAmountBodyTemplate,
    buyAmountBodyTemplate,
    totalTaxFeeBodyTemplate,
    evalProfitBodyTemplate,
    profitTemplate,
  };
}
