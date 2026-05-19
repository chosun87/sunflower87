import { useState, useEffect, useMemo } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import Chart from 'react-apexcharts'
import { Card, Button, ProgressSpinner } from '@/assets/js/PrimeReact'
import { showError } from '@/assets/js/dialogUtils'

// 날짜 데이터 포맷을 정제하는 헬퍼 함수
const formatTradeDate = (tradeDate) => {
  if (!tradeDate || tradeDate.length !== 8) return tradeDate
  const year = tradeDate.substring(0, 4)
  const month = tradeDate.substring(4, 6)
  const day = tradeDate.substring(6, 8)
  return `${year}-${month}-${day}`
}

export default function StockDetail() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const stockCode = searchParams.get('code') || ''

  const [ohlcvData, setOhlcvData] = useState([])
  const [stockName, setStockName] = useState('')
  const [isChartLoading, setIsChartLoading] = useState(true)

  // 주가 API 호출 및 데이터 수신
  useEffect(() => {
    if (!stockCode) {
      showError('종목 코드가 지정되지 않았습니다.')
      navigate('/dashboard')
      return
    }

    setIsChartLoading(true)
    fetch(`${import.meta.env.VITE_API_URL}/api/stocks/ohlcv?code=${stockCode}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error('주가 데이터를 가져오는데 실패했습니다.')
        }
        return res.json()
      })
      .then((resData) => {
        if (resData.status === 'success') {
          setOhlcvData(resData.data || [])
          setStockName(resData.stock_name || '')
        } else {
          showError(resData.message || '데이터 로드 실패')
        }
      })
      .catch((err) => {
        console.error('OHLCV 데이터 로드 에러:', err)
        showError(err.message || '서버 통신 실패')
      })
      .finally(() => {
        setIsChartLoading(false)
      })
  }, [stockCode, navigate])

  // React 성능 최적화: 차트 시리즈 데이터 메모이제이션 (Cascading Render 방지)
  const chartSeries = useMemo(() => {
    return [
      {
        name: 'OHLCV',
        data: ohlcvData.map((item) => ({
          x: formatTradeDate(item.trade_date),
          y: [item.open_price, item.high_price, item.low_price, item.close_price],
        })),
      },
    ]
  }, [ohlcvData])

  // React 성능 최적화: 차트 옵션 메모이제이션 (불필요한 ApexCharts 갱신 방지)
  const chartOptions = useMemo(() => {
    return {
      chart: {
        type: 'candlestick',
        height: 400,
        toolbar: {
          show: true,
        },
      },
      title: {
        text: `${stockName ? `${stockName} ` : ''}[${stockCode}] 60거래일 추세 분석`,
        align: 'left',
        style: {
          fontSize: '18px',
          fontWeight: 'bold',
        },
      },
      xaxis: {
        type: 'category',
        labels: {
          style: {
            cssClass: 'monospace',
          },
        },
      },
      yaxis: {
        tooltip: {
          enabled: true,
        },
        labels: {
          formatter: (val) => Math.round(val).toLocaleString(),
          style: {
            cssClass: 'monospace',
          },
        },
      },
      plotOptions: {
        candlestick: {
          colors: {
            upward: 'var(--blue-600)', // 양봉(상승): 파란색 통제
            downward: 'var(--red-600)', // 음봉(하락): 빨간색 통제
          },
        },
      },
      tooltip: {
        shared: true,
        custom: ({ seriesIndex, dataPointIndex, w }) => {
          const ohlcv = w.config.series[seriesIndex].data[dataPointIndex]
          if (!ohlcv) return ''
          const date = ohlcv.x
          const [open, high, low, close] = ohlcv.y
          return `
            <div class="p-3 monospace" style="font-size: 12px; line-height: 1.5; background: var(--surface-card); color: var(--text-color); border: 1px solid var(--surface-border); border-radius: 4px;">
              <div style="font-weight: bold; margin-bottom: 5px;">${date}</div>
              <div>시가: <span style="font-weight: bold">${open.toLocaleString()}</span></div>
              <div>고가: <span style="color: var(--blue-600); font-weight: bold">${high.toLocaleString()}</span></div>
              <div>저가: <span style="color: var(--red-600); font-weight: bold">${low.toLocaleString()}</span></div>
              <div>종가: <span style="font-weight: bold">${close.toLocaleString()}</span></div>
            </div>
          `
        },
      },
    }
  }, [stockName, stockCode])

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* 뒤로가기 헤더 영역 */}
      <div className="flex align-items-center justify-content-between mb-4">
        <Button
          label="대시보드로 돌아가기"
          icon="pi pi-arrow-left"
          className="p-button-outlined p-button-secondary font-bold"
          onClick={() => navigate('/dashboard')}
        />
        <span className="text-500 font-semibold monospace">CODE: {stockCode}</span>
      </div>

      <Card className="shadow-4 border-round p-3">
        {isChartLoading ? (
          <div
            className="flex flex-column align-items-center justify-content-center"
            style={{ height: '400px' }}
          >
            <ProgressSpinner
              style={{ width: '50px', height: '50px' }}
              strokeWidth="4"
              animationDuration=".5s"
            />
            <span className="text-600 font-semibold mt-3">
              [sunflower87] 주가 데이터를 불러오는 중...
            </span>
          </div>
        ) : ohlcvData.length === 0 ? (
          <div
            className="flex align-items-center justify-content-center text-500 font-semibold"
            style={{ height: '400px' }}
          >
            해당 종목의 주가 데이터를 찾을 수 없습니다.
          </div>
        ) : (
          <div style={{ minHeight: '400px' }}>
            <Chart
              options={chartOptions}
              series={chartSeries}
              type="candlestick"
              height={400}
            />
          </div>
        )}
      </Card>
    </div>
  )
}
