import { DataView } from '@/assets/ts/PrimeReact'
import CustomPanel from '@components/CustomPanel'
import { watchlistData, type StockItem } from '@/data/MyWatchlistData'

export default function MyWatchlist() {
  // Watchlist DataView 렌더러
  const watchlistTemplate = (stock: StockItem) => {
    return (
      <div className="watchlist-item w-full">
        <div className="stock-info">
          <div className="stock-meta">
            <span className="stock-name">{stock.name}</span>
            <span className="stock-code text-sm text-muted monospace">{stock.code}</span>
          </div>
        </div>
        <div className="stock-prices">
          <span className={`stock-current monospace ${stock.isUp ? 'text-up' : 'text-down'}`}>
            {stock.price}
          </span>
          <span className={`stock-change monospace ${stock.isUp ? 'text-up' : 'text-down'}`}>
            <i className={`fa-solid ${stock.isUp ? 'fa-caret-up' : 'fa-caret-down'} mr-1`}></i>
            {stock.change}
          </span>
        </div>
      </div>
    )
  }

  return (
    <CustomPanel
      className="my-watchlist-panel"
      maximizable
      header={
        <div className="panel-header-title">
          <i className="panel-header-title-icon fa-solid fa-list-check"></i>
          <span>나의 관심 종목</span>
        </div>
      }
    >
      <DataView value={watchlistData} itemTemplate={watchlistTemplate} layout="list" />
    </CustomPanel>
  )
}
