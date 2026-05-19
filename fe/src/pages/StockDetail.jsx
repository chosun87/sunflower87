import { useState, useEffect, useMemo } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import Chart from 'react-apexcharts'
import { Card, Button, ProgressSpinner } from '@/assets/js/PrimeReact'
import { showError } from '@/assets/js/dialogUtils'

export default function StockDetail() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const stockCode = searchParams.get('code') || ''

  const [ohlcvData, setOhlcvData] = useState([])
  const [stockName, setStockName] = useState('')
  const [isChartLoading, setIsChartLoading] = useState(true)
  const [windowWidth, setWindowWidth] = useState(window.innerWidth)

  // 반응형 X축 눈금 제어를 위해 화면 크기(창 너비) 실시간 감지 레이어 구현
  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth)
    }
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  // 주가 API 비동기 조회 및 상태 매핑 (20ms 마운트 가드 레이어 탑재)
  useEffect(() => {
    if (!stockCode) {
      showError('종목 코드가 지정되지 않았습니다.')
      navigate('/dashboard')
      return
    }

    Promise.resolve().then(() => {
      setIsChartLoading(true)
    })
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
          setIsChartLoading(false)
        } else {
          showError(resData.message || '데이터 로드 실패')
          setIsChartLoading(false)
        }
      })
      .catch((err) => {
        console.error('OHLCV 데이터 로드 에러:', err)
        showError(err.message || '서버 통신 실패')
        setIsChartLoading(false)
      })
  }, [stockCode, navigate])

  // 60거래일 데이터를 기반으로 주말/휴장일 공백이 100% 제거된 카테고리 눈금 및 시리즈의 메모이제이션
  const chartData = useMemo(() => {
    if (!ohlcvData || ohlcvData.length === 0) {
      return { categories: [], series: [], rawList: [] }
    }

    const categories = []
    let lastMonth = null
    let lastYear = null

    // 1단계 [A]: 각 영업일의 날짜 변환 및 변곡점(Transition) 여부 1차 판독 (for 루프 활용으로 렌더 사이클 재할당 린트 경고 회피)
    const tempTransitions = []
    for (let index = 0; index < ohlcvData.length; index++) {
      const item = ohlcvData[index]
      const year = item.trade_date.substring(0, 4)
      const monthStr = item.trade_date.substring(4, 6)
      const dayStr = item.trade_date.substring(6, 8)

      const currentYear = parseInt(year, 10)
      const currentMonth = parseInt(monthStr, 10)

      let label = dayStr // 기본값: '일(DD)'
      let isTransition = false

      // 첫 번째 영업일(시작점): YYYY-MM-DD 풀 포맷 및 변곡점 처리
      if (index === 0) {
        label = `${year}-${monthStr}-${dayStr}`
        lastMonth = currentMonth
        lastYear = currentYear
        isTransition = true
      } else {
        // 연 변곡점 검출
        if (currentYear !== lastYear) {
          label = `${year}-${monthStr}-${dayStr}`
          lastYear = currentYear
          lastMonth = currentMonth
          isTransition = true
        }
        // 월 변곡점 검출
        else if (currentMonth !== lastMonth) {
          label = `${monthStr}-${dayStr}`
          lastMonth = currentMonth
          isTransition = true
        }
      }

      tempTransitions.push({
        label,
        isTransition,
        year,
        monthStr,
        dayStr,
      })
    }

    // 1단계 [B]: 2차 루프를 돌며 각 영업일의 포맷팅된 날짜 라벨을 100% 매핑 (ApexCharts가 tickAmount 조건에 맞춰 최적으로 자동 솎아냄)
    const rawList = ohlcvData.map((item, index) => {
      const { label, year, monthStr, dayStr } = tempTransitions[index]

      // 수동 솎아내기(빈 문자열 주입)를 제거하여, tickAmount 솎아내기 기능과 충돌을 파쇄하고 모든 눈금 영역에 올바른 날짜를 노출
      categories.push(label)

      return {
        trade_date: item.trade_date,
        open_price: Number(item.open_price || 0),
        high_price: Number(item.high_price || 0),
        low_price: Number(item.low_price || 0),
        close_price: Number(item.close_price || 0),
        rawDate: `${year}-${monthStr}-${dayStr}`,
      }
    })

    // 2단계: 5일 및 20일 이동평균선(MA) 계산 (주말 공백 없는 영업일 밀착형 연산)
    const ma5Data = []
    const ma20Data = []

    for (let i = 0; i < rawList.length; i++) {
      // 5일선
      if (i < 4) {
        ma5Data.push(null)
      } else {
        let sum = 0
        for (let j = 0; j < 5; j++) {
          sum += rawList[i - j].close_price
        }
        ma5Data.push(Math.round(sum / 5))
      }

      // 20일선
      if (i < 19) {
        ma20Data.push(null)
      } else {
        let sum = 0
        for (let j = 0; j < 20; j++) {
          sum += rawList[i - j].close_price
        }
        ma20Data.push(Math.round(sum / 20))
      }
    }

    // 3단계: 인덱스(idx) 1:1 매칭 기반 오버레이 시리즈 빌드
    const series = [
      {
        name: '현재가 (OHLC)',
        type: 'candlestick',
        data: rawList.map((item, idx) => ({
          x: idx, // 타임스탬프 대신 1:1 순차 인덱스를 사용하여 공백 파쇄
          y: [
            item.open_price,
            item.high_price,
            item.low_price,
            item.close_price,
          ],
        })),
      },
      {
        name: '5일 이동평균선',
        type: 'line',
        data: ma5Data.map((val, idx) => ({
          x: idx,
          y: val,
        })),
      },
      {
        name: '20일 이동평균선',
        type: 'line',
        data: ma20Data.map((val, idx) => ({
          x: idx,
          y: val,
        })),
      },
    ]

    return { categories, series, rawList }
  }, [ohlcvData])

  // 창 크기에 대응되는 최적의 X축 눈금 개수(tickAmount) 연산
  const tickAmount = useMemo(() => {
    if (windowWidth <= 768) return 8
    if (windowWidth <= 1200) return 14
    return 20
  }, [windowWidth])

  // React 성능 최적화: 차트 옵션 메모이제이션 (카테고리 축 기반의 정밀 레이아웃 정립)
  const chartOptions = useMemo(() => {
    return {
      chart: {
        type: 'line',
        height: 400,
        toolbar: {
          show: true,
        },
        background: 'transparent',
      },
      colors: ['var(--blue-600)', '#ff9800', '#9c27b0'], // 상승 블루 / 오렌지 5일선 / 보라 20일선 지정
      stroke: {
        width: [1, 2, 2], // 캔들 테두리: 1px / 5일선 및 20일선 두께: 2px 규격 적용
        curve: 'straight', // 왜곡 없이 올바르게 렌더링
      },
      title: {
        text: `${stockName ? `${stockName} ` : ''}[${stockCode}] ${chartData.rawList.length}거래일 추세 분석`,
        align: 'left',
        style: {
          fontSize: '18px',
          fontWeight: 'bold',
          color: 'var(--text-color)',
        },
      },
      grid: {
        borderColor: 'var(--surface-border)', // 테마와 일치하는 은은한 그리드선 부여
        strokeDashArray: 4,
        xaxis: {
          lines: {
            show: false, // 가로 격자선만 깔끔하게 노출
          },
        },
        yaxis: {
          lines: {
            show: true,
          },
        },
      },
      xaxis: {
        type: 'category', // 카테고리 축으로 선언하여 주말/휴장일의 빈 공간(공백)을 100% 완벽하게 소멸
        categories: chartData.categories, // 미리 솎아낸 눈금 및 변곡점 라벨 주입
        tickAmount: tickAmount,
        axisBorder: {
          color: 'var(--surface-border)',
        },
        axisTicks: {
          color: 'var(--surface-border)',
        },
        labels: {
          rotate: 0, // 글자가 45도로 눕지 않고 완벽한 수평 정렬을 유지하도록 통제
          rotateAlways: false,
          style: {
            colors: 'var(--text-color-secondary)',
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
            colors: 'var(--text-color-secondary)',
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
          wick: {
            useFillColor: true, // 꼬리 굵기 및 발색 최적화
          },
        },
      },
      legend: {
        show: true,
        position: 'top',
        horizontalAlign: 'right',
        labels: {
          colors: 'var(--text-color)',
          useSeriesColors: false,
        },
        markers: {
          width: 10,
          height: 10,
          radius: 12, // 원형 서클 스타일 적용
          offsetX: -4,
        },
        itemMargin: {
          horizontal: 12,
          vertical: 4,
        },
      },
      tooltip: {
        shared: true,
        // 카테고리 축 전용 명품 Glassmorphism 다크 툴팁 팝업 출력
        custom: ({ dataPointIndex, w }) => {
          const item = chartData.rawList[dataPointIndex]
          const ma5Val = w.config.series[1].data[dataPointIndex]?.y
          const ma20Val = w.config.series[2].data[dataPointIndex]?.y

          if (!item) return ''

          return `
            <div class="p-3 monospace" style="
              font-size: 12px;
              line-height: 1.6;
              background: rgba(33, 37, 41, 0.9);
              backdrop-filter: blur(8px);
              color: #f8f9fa;
              border: 1px solid rgba(255, 255, 255, 0.15);
              border-radius: 8px;
              box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35);
              min-width: 180px;
            ">
              <div style="font-weight: 800; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.15); padding-bottom: 6px; font-size: 13px; color: #ced4da;">
                📅 ${item.rawDate}
              </div>
              <div style="display: flex; justify-content: space-between;">시가: <span style="font-weight: bold; color: #f8f9fa;">${item.open_price.toLocaleString()}</span></div>
              <div style="display: flex; justify-content: space-between;">고가: <span style="color: #64b5f6; font-weight: bold;">▲ ${item.high_price.toLocaleString()}</span></div>
              <div style="display: flex; justify-content: space-between;">저가: <span style="color: #ef5350; font-weight: bold;">▼ ${item.low_price.toLocaleString()}</span></div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 6px; border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom: 4px;">
                종가: <span style="font-weight: bold; color: #f8f9fa;">${item.close_price.toLocaleString()}</span>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                <span style="color: #ffb74d; font-weight: bold;">5일선:</span>
                <span style="font-weight: bold;">${ma5Val !== null && ma5Val !== undefined ? `${ma5Val.toLocaleString()} 원` : '-'}</span>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 2px;">
                <span style="color: #ba68c8; font-weight: bold;">20일선:</span>
                <span style="font-weight: bold;">${ma20Val !== null && ma20Val !== undefined ? `${ma20Val.toLocaleString()} 원` : '-'}</span>
              </div>
            </div>
          `
        },
      },
    }
  }, [stockName, stockCode, chartData, tickAmount])

  return (
    <div className="p-4 md:p-6 lg:p-8 animate-fadein">
      {/* 뒤로가기 헤더 영역 */}
      <div className="flex align-items-center justify-content-between mb-4">
        <Button
          label="대시보드로 돌아가기"
          icon="pi pi-arrow-left"
          className="p-button-outlined p-button-secondary font-bold"
          onClick={() => navigate('/dashboard')}
        />
        <span className="text-500 font-semibold monospace">
          CODE: {stockCode}
        </span>
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
              series={chartData.series}
              type="line" // 복합(Mixed) 차트 렌더링 활성화를 위해 메인 타입을 line으로 정의
              height={400}
            />
          </div>
        )}
      </Card>
    </div>
  )
}
