export interface StockItem {
  name: string
  code: string
  price: string
  change: string
  isUp: boolean
}

// 관심 종목 자체 보유 Mock Data
export const watchlistData: StockItem[] = [
  { name: 'Apple Inc.', code: 'AAPL', price: '$175.50', change: '+1.45%', isUp: true },
  { name: 'Spotify Technology', code: 'SPOT', price: '$242.10', change: '+2.35%', isUp: true },
  { name: 'Airbnb Inc.', code: 'ABNB', price: '$158.30', change: '-0.85%', isUp: false },
  { name: 'Alphabet Inc.', code: 'GOOGL', price: '$152.40', change: '+0.95%', isUp: true },
  { name: 'Alphabet Inc.', code: 'GOOGL', price: '$152.40', change: '+0.95%', isUp: true },
]
