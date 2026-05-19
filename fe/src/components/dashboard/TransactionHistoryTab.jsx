import { useMemo } from 'react'
import dayjs from 'dayjs'
import { DataTable, Column, Badge, Button } from '@/assets/js/PrimeReact'

export default function TransactionHistoryTab({
  transactions,
  onAddClick,
  onEditClick,
  onDeleteClick,
}) {
  // --- [매매 내역 전용 내부 템플릿 렌더러 정의] ---

  const txTypeBodyTemplate = (rowData) => {
    const isBuy = rowData.type === 'BUY'
    return isBuy ? (
      <Badge value="매수" className="type-buy" />
    ) : (
      <Badge value="매도" className="type-sell" />
    )
  }

  const dateBodyTemplate = (rowData) => {
    return rowData.date ? (
      <span className="monospace">
        {dayjs(rowData.date).format('YYYY-MM-DD HH:mm')}
      </span>
    ) : (
      ''
    )
  }

  const accountBodyTemplate = (rowData) => {
    const company = rowData.acc_company_nm || ''
    const name = rowData.acc_nm || '알 수 없는 계좌'
    if (company) {
      const shortCompany = company.substring(0, 2)
      return `[${shortCompany}] ${name}`
    }
    return name
  }

  const txCodeBodyTemplate = (rowData) => {
    return <span className="monospace">{rowData.code}</span>
  }

  const txQuantityBodyTemplate = (rowData) => {
    return (
      <span className="monospace">{rowData.quantity.toLocaleString()} 주</span>
    )
  }

  const txPriceBodyTemplate = (rowData) => {
    return (
      <span className="monospace">{rowData.price.toLocaleString()} 원</span>
    )
  }

  const txTotalBodyTemplate = (rowData) => {
    return (
      <span className="monospace">
        {(rowData.quantity * rowData.price).toLocaleString()} 원
      </span>
    )
  }

  const txTaxFeeBodyTemplate = (rowData) => {
    const fee = rowData.tax_fee || 0
    return <span className="monospace">{fee.toLocaleString()} 원</span>
  }

  // 테이블 최우측 [수정/삭제] 액션 컬럼
  const actionsBodyTemplate = (rowData) => {
    return (
      <div className="flex gap-2">
        <Button
          icon="pi pi-pencil"
          className="p-button-rounded p-button-warning p-button-text p-button-sm"
          onClick={() => onEditClick(rowData)}
          tooltip="매매 내역 수정"
        />
        <Button
          icon="pi pi-trash"
          className="p-button-rounded p-button-danger p-button-text p-button-sm"
          onClick={() => onDeleteClick(rowData)}
          tooltip="매매 내역 삭제"
        />
      </div>
    )
  }

  // --- [총 거래금액 및 세금/수수료의 총합 누적 연산] ---
  const { totalTxAmountSum, totalTxTaxFeeSum } = useMemo(() => {
    const totalTxAmountSum = (transactions || []).reduce(
      (sum, tx) => sum + (tx.quantity || 0) * (tx.price || 0),
      0,
    )
    const totalTxTaxFeeSum = (transactions || []).reduce(
      (sum, tx) => sum + (tx.tax_fee || 0),
      0,
    )
    return { totalTxAmountSum, totalTxTaxFeeSum }
  }, [transactions])

  return (
    <div className="mt-3">
      <div className="flex align-items-center justify-content-between mb-4 flex-wrap gap-2">
        <h3 className="text-xl font-bold m-0 text-700">
          SQLite 매매 내역 대장
        </h3>
        <Button
          label="거래 내역 추가"
          icon="pi pi-plus"
          className="p-button-success p-button-sm font-bold shadow-2"
          onClick={onAddClick}
        />
      </div>

      <DataTable
        value={transactions}
        responsiveLayout="stack"
        breakpoint="960px"
        sortMode="multiple"
        stripedRows
        paginator
        rows={10}
        className="mt-2"
        emptyMessage="등록된 매매 거래 히스토리가 존재하지 않습니다."
      >
        <Column
          field="date"
          header="거래 일시"
          body={dateBodyTemplate}
          sortable
          footer={<span className="font-bold">합계</span>}
        ></Column>
        <Column
          field="type"
          header="구분"
          body={txTypeBodyTemplate}
          sortable
        ></Column>
        <Column
          field="acc_cd"
          header="거래 계좌"
          body={accountBodyTemplate}
          sortable
        ></Column>
        <Column
          field="code"
          header="종목코드"
          body={txCodeBodyTemplate}
          sortable
        ></Column>
        <Column field="name" header="종목명" sortable></Column>
        <Column
          field="quantity"
          header="거래 수량"
          align="right"
          body={txQuantityBodyTemplate}
          sortable
        ></Column>
        <Column
          field="price"
          header="거래 단가"
          align="right"
          body={txPriceBodyTemplate}
          sortable
        ></Column>
        <Column
          header="총 거래금액"
          align="right"
          body={txTotalBodyTemplate}
          sortable
          footer={
            <span className="monospace font-bold">
              {totalTxAmountSum.toLocaleString()} 원
            </span>
          }
        ></Column>
        <Column
          field="tax_fee"
          header="세금+수수료"
          align="right"
          body={txTaxFeeBodyTemplate}
          sortable
          footer={
            <span className="monospace font-bold">
              {totalTxTaxFeeSum.toLocaleString()} 원
            </span>
          }
        ></Column>
        <Column
          header="작업"
          body={actionsBodyTemplate}
          exportable={false}
          style={{ minWidth: '8rem' }}
        ></Column>
      </DataTable>
    </div>
  )
}
