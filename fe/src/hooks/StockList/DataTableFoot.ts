import { useMemo } from 'react';

// 계좌 배열을 받아 총계(Footer)용 합산 데이터를 포함하여 반환하는 훅
export function useDataTableFoot(accounts: any[]) {
  return useMemo(() => {
    return (accounts || []).map((acc) => {
      const activeStocks = (acc.stocks || []).filter((s: any) => s.quantity > 0);

      const totalEvalAmount = activeStocks.reduce((sum, s) => {
        const val =
          s.total_eval_amt !== undefined
            ? s.total_eval_amt
            : (s.quantity || 0) * (s.current_price || 0);
        return sum + val;
      }, 0);

      const totalPurchaseAmount = activeStocks.reduce((sum, s) => {
        const val =
          s.total_purchase_amt !== undefined ? s.total_purchase_amt : s.purchase_amount || 0;
        return sum + val;
      }, 0);

      const totalTaxFee = activeStocks.reduce((sum, s) => {
        return sum + (s.total_tax_fee || 0);
      }, 0);

      const totalProfit = activeStocks.reduce((sum, s) => {
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
}
