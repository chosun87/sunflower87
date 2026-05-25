import { Column, DataTable } from '@/assets/ts/PrimeReact'
import CustomPanel from '@components/CustomPanel'
import { transactionsData, type Transaction } from '@/data/LatestTransactionsData'

export default function LatestTransactions() {
  // DataTable Action Type 컬럼 렌더러
  const typeBodyTemplate = (rowData: Transaction) => {
    return (
      <span className={`action-type text-${rowData.type.toLowerCase()}`}>
        {rowData.type === 'Buy' ? '매수' : '매도'}
      </span>
    )
  }

  return (
    <CustomPanel
      maximizable
      header={
        <div className="panel-header-title">
          <i className="panel-header-title-icon fa-solid fa-receipt"></i>
          <span>최근 거래 내역</span>
        </div>
      }
    >
      <DataTable
        className="transactions-table"
        stripedRows
        responsiveLayout="scroll"
        value={transactionsData}
        emptyMessage="최근 거래 기록이 존재하지 않습니다."
      >
        <Column field="asset" header="종목 이름" sortable style={{ fontWeight: 600 }}></Column>
        <Column field="date" header="거래 일자" sortable></Column>
        <Column field="type" header="거래 구분" body={typeBodyTemplate} sortable></Column>
        <Column field="amount" header="수량" sortable></Column>
        <Column field="price" header="체결 단가" sortable></Column>
      </DataTable>
    </CustomPanel>
  )
}
