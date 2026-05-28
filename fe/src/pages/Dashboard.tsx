import KpiCards from '@components/Dashboard/KpiCards';
import PortfolioPerformance from '@components/Dashboard/PortfolioPerformance';
import DividendSummary from '@components/Dashboard/DividendSummary';
import LatestTrStockList from '@/components/Dashboard/LatestTrStockList';
import LatestTrCashList from '@/components/Dashboard/LatestTrCashList';
import MyWatchlist from '@components/Dashboard/MyWatchlist';

export default function Dashboard() {
  return (
    <main className="page dashboard">
      <div className="main-inner">
        {/* 1. 상단 핵심 지표(KPI) 카드 영역 */}
        <KpiCards />

        {/* 2. 메인 대시보드 2단 그리드 레이아웃 */}
        <div className="grid">
          {/* 좌측 메인 차트 및 상세 */}
          <div className="col-12 xl:col-8">
            {/* 포트폴리오 수익 추이 Panel */}
            <PortfolioPerformance />
          </div>

          {/* 우측 보조 카드 영역 */}
          <div className="col-12 xl:col-4">
            {/* 나의 관심 종목 Panel */}
            <MyWatchlist />
          </div>
        </div>

        {/* 3. 최근 매매 내역  및 입출금 내역 그리드 레이아웃 */}
        <div className="grid">
          {/* 좌측 메인 차트 및 상세 */}
          <div className="col-12 xl:col-6">
            {/* 최근 매매 내역  Panel */}
            <LatestTrStockList />
          </div>

          {/* 우측 보조 카드 영역 */}
          <div className="col-12 xl:col-6">
            {/* 최근 입출금 내역 Panel */}
            <LatestTrCashList />
          </div>
        </div>
      </div>
    </main>
  );
}
