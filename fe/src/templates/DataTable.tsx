import { BreadCrumb, Column, DataTable } from '@/assets/ts/PrimeReact'

const breadcrumbItems = [
  { label: 'Home', url: '/' },
  { label: 'Templates' },
  { label: 'DataTable' },
]

export interface Transaction {
  id: string
  asset: string
  symbol: string
  date: string
  type: 'Buy' | 'Sell'
  amount: number
  price: string
  status: 'Success' | 'Pending' | 'Failed'
}

// 거래 내역 자체 보유 Mock Data
const transactionsData: Transaction[] = [
  {
    id: '1',
    asset: 'Apple Inc.',
    symbol: 'AAPL',
    date: '2026-05-24',
    type: 'Buy',
    amount: 10,
    price: '$175.50',
    status: 'Success',
  },
  {
    id: '2',
    asset: 'Spotify Tech',
    symbol: 'SPOT',
    date: '2026-05-23',
    type: 'Sell',
    amount: 5,
    price: '$240.20',
    status: 'Success',
  },
  {
    id: '3',
    asset: 'Airbnb Inc.',
    symbol: 'ABNB',
    date: '2026-05-22',
    type: 'Buy',
    amount: 15,
    price: '$159.00',
    status: 'Pending',
  },
  {
    id: '4',
    asset: 'Alphabet Inc.',
    symbol: 'GOOGL',
    date: '2026-05-20',
    type: 'Buy',
    amount: 8,
    price: '$151.80',
    status: 'Failed',
  },
]

export default function TemplateDataTable() {
  // DataTable Status 컬럼 렌더러
  const statusBodyTemplate = (rowData: Transaction) => {
    return <span className={`badge-status ${rowData.status.toLowerCase()}`}>{rowData.status}</span>
  }

  // DataTable Action Type 컬럼 렌더러
  const typeBodyTemplate = (rowData: Transaction) => {
    return (
      <span className={`action-type text-${rowData.type.toLowerCase()}`}>
        {rowData.type === 'Buy' ? '매수' : '매도'}
      </span>
    )
  }

  return (
    <main className="page template template-datatable">
      <div className="main-inner">
        <div className="page-header">
          <h2 className="page-title">DataTable</h2>

          <BreadCrumb className="breadcrumb" model={breadcrumbItems} />
        </div>

        <div className="page-content">
          <DataTable
            stripedRows
            responsiveLayout="scroll"
            paginator
            rows={10}
            rowsPerPageOptions={[5, 10, 25, 50]}
            value={transactionsData}
            emptyMessage="데이터가 업습니다."
          >
            <Column field="asset" header="종목 이름" sortable style={{ fontWeight: 600 }}></Column>
            <Column field="date" header="거래 일자" sortable></Column>
            <Column field="type" header="거래 구분" body={typeBodyTemplate} sortable></Column>
            <Column field="amount" header="수량 (Shares)" sortable></Column>
            <Column field="price" header="체결 단가" sortable></Column>
            <Column field="status" header="체결 상태" body={statusBodyTemplate} sortable></Column>
          </DataTable>
        </div>
      </div>
    </main>
  )
}
