import { Card, Dropdown } from '@/assets/js/PrimeReact'

export default function AssetSummaryCard({
  totalAsset,
  accounts,
  selectedAccount,
  onAccountChange,
}) {
  return (
    <div className="grid mb-6">
      <div className="col-12 md:col-6">
        <Card title="통합 총자산" className="shadow-2 border-round">
          <h2 className="text-4xl text-primary font-bold m-0">
            {totalAsset.toLocaleString()} 원
          </h2>
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
