import CustomPanel from '@components/CustomPanel'

export default function PortfolioPerformance() {
  return (
    <CustomPanel
      maximizable
      header={
        <div className="panel-header-title">
          <i className="panel-header-title-icon fa-solid fa-chart-line"></i>
          <span>포트폴리오 수익 추이</span>
        </div>
      }
    >
      <div
        className="flex flex-column justify-content-center align-items-center"
        style={{
          height: '350px',
          border: '1px dashed var(--border-color)',
          borderRadius: '8px',
          background: 'var(--surface-100)',
        }}
      >
        <i className="fa-solid fa-chart-area text-4xl text-muted mb-3"></i>
        <span className="font-bold text-lg mb-1">포트폴리오 성과 추이 분석</span>
        <span className="text-sm text-muted">
          기획 요구사항에 의거하여 차트 드로잉 영역을 생략하고 높이를 보존합니다.
        </span>
      </div>
    </CustomPanel>
  )
}
