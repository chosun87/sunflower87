import { useMemo } from 'react'
import { Card, Dropdown } from '@/assets/js/PrimeReact'

export default function AssetSummaryCard({
  totalAsset,
  accounts,
  selectedAccount,
  onAccountChange,
}) {
  const { totalProfit, returnRate, isPositive } = useMemo(() => {
    let sumEval = 0
    let sumPurchase = 0

    ;(accounts || []).forEach((acc) => {
      ;(acc.stocks || []).forEach((s) => {
        const buy_amount =
          s.total_purchase_amt !== undefined
            ? s.total_purchase_amt
            : s.purchase_amount || 0
        const eval_amount =
          s.total_eval_amt !== undefined
            ? s.total_eval_amt
            : (s.quantity || 0) * (s.current_price || 0)
        sumEval += eval_amount
        sumPurchase += buy_amount
      })
    })

    const profit = sumEval - sumPurchase
    const rate = sumPurchase > 0 ? (profit / sumPurchase) * 100 : 0
    const positive = profit > 0

    return { totalProfit: profit, returnRate: rate, isPositive: positive }
  }, [accounts])

  const profitClass = `font-bold ${isPositive ? 'text-buy' : totalProfit < 0 ? 'text-sell' : ''}`
  const profitStyle = {
    fontSize: '1.2rem',
    marginLeft: '1rem',
  }

  return (
    <div className="grid mb-6">
      <div className="col-12 md:col-6">
        <Card title="통합 총자산" className="shadow-2 border-round">
          <div className="flex align-items-baseline">
            <h2 className="text-4xl text-primary font-bold m-0">
              {totalAsset.toLocaleString()} 원
            </h2>
            {(totalProfit !== 0 || returnRate !== 0) && (
              <span className={profitClass} style={profitStyle}>
                {isPositive ? '+' : ''}
                {totalProfit.toLocaleString()} 원 ({isPositive ? '+' : ''}
                {returnRate.toFixed(2)}%)
              </span>
            )}
          </div>
        </Card>
      </div>
      <div className="col-12 md:col-6">
        <Card title="계좌 선택" className="shadow-2 border-round">
          <Dropdown
            value={selectedAccount}
            options={accounts}
            onChange={(e) => onAccountChange(e.value)}
            optionLabel="acc_nm"
            optionValue="acc_cd"
            placeholder="조회할 계좌를 선택하세요"
            className="w-full"
          />
        </Card>
      </div>
    </div>
  )
}
