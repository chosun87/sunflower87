import { Card, Badge, Button } from '@/assets/js/PrimeReact'

export default function AIRecommendationSection({ recommendations }) {
  return (
    <div className="mb-6 hidden">
      <div className="flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
        <div className="flex align-items-center gap-2">
          <i className="pi pi-sparkles text-amber-500 text-2xl"></i>
          <h2 className="text-2xl font-bold text-900 m-0">
            오늘의 AI 추천 종목
          </h2>
        </div>
        <Badge
          value="정량 지표 분석 기반"
          severity="warning"
          className="p-2 border-round font-semibold"
        />
      </div>

      <div className="grid">
        {recommendations.map((item, idx) => (
          <div key={idx} className="col-12 md:col-4">
            <Card
              className="shadow-2 hover:shadow-4 transition-all transition-duration-200 border-top-3 border-amber-500 h-full flex flex-column"
              style={{ borderRadius: '8px' }}
            >
              <div className="flex justify-content-between align-items-center mb-3">
                <div>
                  <span className="text-xl font-bold text-900 mr-2">
                    {item.name}
                  </span>
                  <span className="text-500 text-sm font-semibold">
                    {item.code}
                  </span>
                </div>
                <Badge
                  value={item.tag}
                  className="bg-amber-100 text-amber-800 font-semibold p-1"
                />
              </div>

              <p className="text-700 text-sm mb-4 line-height-3 flex-grow-1">
                {item.reason}
              </p>

              <div className="flex justify-content-between align-items-center pt-3 border-top-1 border-100 mt-auto">
                <span className="text-sm font-semibold text-600">
                  AI 추천 점수
                </span>
                <div className="flex align-items-center gap-2">
                  <span className="text-2xl font-bold text-amber-600">
                    {item.score}점
                  </span>
                  <Button
                    icon="pi pi-chevron-right"
                    className="p-button-rounded p-button-text p-button-sm text-amber-500"
                    aria-label="상세보기"
                  />
                </div>
              </div>
            </Card>
          </div>
        ))}
      </div>
    </div>
  )
}
