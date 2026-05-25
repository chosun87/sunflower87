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
export const transactionsData: Transaction[] = [
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
