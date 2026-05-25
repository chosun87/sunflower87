import CustomPanel from '@components/CustomPanel';

export default function DividendSummary() {
  return (
    <CustomPanel
      maximizable
      header={
        <div className="panel-header-title">
          <i className="panel-header-title-icon fa-solid fa-money-bill-trend-up"></i>
          <span>배당금 수령 내역 및 분포</span>
        </div>
      }
    >
      <div
        className="flex flex-column justify-content-center align-items-center p-5"
        style={{
          border: '1px dashed var(--border-color)',
          borderRadius: '8px',
          background: 'var(--surface-100)',
        }}
      >
        <i className="fa-solid fa-chart-pie text-4xl text-muted mb-3"></i>
        <span className="font-bold text-lg mb-1">연간 자산 배당 분포</span>
        <span className="text-sm text-muted">
          기획 요구사항에 의거하여 배당 통계 차트를 생략하고 레이아웃을 보존합니다.
        </span>
      </div>
    </CustomPanel>
  );
}
