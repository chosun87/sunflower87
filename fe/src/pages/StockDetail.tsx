import { useState, useEffect, useMemo, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import Chart from 'react-apexcharts';
import { Card, Button, ProgressSpinner } from '@/assets/js/PrimeReact';
import { showError } from '@/assets/js/dialogUtils';
import { get } from '@/api';

export default function StockDetail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const stockCode = searchParams.get('code') || '';

  const [ohlcvData, setOhlcvData] = useState([]);
  const [stockName, setStockName] = useState('');
  const [isChartLoading, setIsChartLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // 클릭 기반 커스텀 툴팁을 관리하는 상태 (Label 1)
  const [customClickTooltip, setCustomClickTooltip] = useState({
    visible: false,
    item: null,
    prevClose: null,
    ma5Val: null,
    ma20Val: null,
    x: 0,
    y: 0,
    dataPointIndex: -1,
  });

  const chartContainerRef = useRef(null);
  const debounceTimer = useRef(null);

  // 백엔드 API 호출 공통 함수 (Debounce에서 재사용)
  const fetchOhlcvData = async (start_date = null, end_date = null) => {
    try {
      const params = { code: stockCode };
      if (start_date) params.start_date = start_date;
      if (end_date) params.end_date = end_date;
      
      const resData = await get('/api/stocks/ohlcv', params);
      if (resData.status !== 'success') {
        throw new Error(resData.message || '주가 데이터를 가져오는데 실패했습니다.');
      }
      setOhlcvData(resData.data || []);
      setStockName(resData.stock_name || '');
    } catch (err) {
      console.error('OHLCV 데이터 로드 에러:', err);
      showError(err.message || '서버 통신 실패');
    } finally {
      setIsChartLoading(false);
    }
  };

  // 주가 API 비동기 조회 및 상태 매핑 (20ms 마운트 가드 레이어 탑재)
  useEffect(() => {
    if (!stockCode) {
      showError('종목 코드가 지정되지 않았습니다.');
      navigate('/dashboard');
      return;
    }
    setIsChartLoading(true);
    fetchOhlcvData();
  }, [stockCode, navigate]);

  // 전체 화면 토글 버튼 핸들러
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      if (chartContainerRef.current) {
        chartContainerRef.current.requestFullscreen().catch(err => {
          console.error('Fullscreen error:', err);
        });
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(document.fullscreenElement === chartContainerRef.current);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  // 차트 Pan / Zoom 이벤트 핸들러 (300ms Debounce 결계)
  const handleChartPanZoom = (chartContext, { xaxis }) => {
    if (!xaxis || !xaxis.min || !xaxis.max) return;
    
    // category 방식의 X축에서 min, max는 1 기반의 인덱스로 넘어올 가능성이 높습니다.
    const labels = chartContext?.w?.globals?.labels || [];
    if (labels.length === 0) return;

    // 인덱스 범위 보정
    const minIdx = Math.max(0, Math.floor(xaxis.min) - 1);
    const maxIdx = Math.min(labels.length - 1, Math.ceil(xaxis.max) - 1);

    const start_date = labels[minIdx];
    const end_date = labels[maxIdx];

    if (!start_date || !end_date) return;

    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      fetchOhlcvData(start_date, end_date);
    }, 300);
  };

  // 60거래일 데이터를 기반으로 주말/휴장일 공백이 100% 제거된 카테고리 눈금 및 시리즈의 메모이제이션
  const chartData = useMemo(() => {
    if (!ohlcvData || ohlcvData.length === 0) {
      return { categories: [], series: [], rawList: [] };
    }

    const categories = [];
    let lastMonth = null;
    let lastYear = null;

    // 1단계 [A]: 각 영업일의 날짜 변환 및 변곡점(Transition) 여부 1차 판독 (for 루프 활용으로 렌더 사이클 재할당 린트 경고 회피)
    const tempTransitions = [];
    for (let index = 0; index < ohlcvData.length; index++) {
      const item = ohlcvData[index];
      const year = item.trade_date.substring(0, 4);
      const monthStr = item.trade_date.substring(4, 6);
      const dayStr = item.trade_date.substring(6, 8);

      const currentYear = parseInt(year, 10);
      const currentMonth = parseInt(monthStr, 10);

      let label = dayStr; // 기본값: '일(DD)'
      let isTransition = false;

      // 첫 번째 영업일(시작점): YYYY-MM-DD 풀 포맷 및 변곡점 처리
      if (index === 0) {
        label = `${year}-${monthStr}-${dayStr}`;
        lastMonth = currentMonth;
        lastYear = currentYear;
        isTransition = true;
      } else {
        // 연 변곡점 검출
        if (currentYear !== lastYear) {
          label = `${year}-${monthStr}-${dayStr}`;
          lastYear = currentYear;
          lastMonth = currentMonth;
          isTransition = true;
        }
        // 월 변곡점 검출
        else if (currentMonth !== lastMonth) {
          label = `${monthStr}-${dayStr}`;
          lastMonth = currentMonth;
          isTransition = true;
        }
      }

      tempTransitions.push({
        label,
        isTransition,
        year,
        monthStr,
        dayStr,
      });
    }

    // 1단계 [B]: 2차 루프를 돌며 각 영업일의 포맷팅된 날짜 라벨을 100% 매핑 (ApexCharts가 tickAmount 조건에 맞춰 최적으로 자동 솎아냄)
    const rawList = ohlcvData.map((item, index) => {
      const { year, monthStr, dayStr } = tempTransitions[index];

      // 수동 솎아내기(빈 문자열 주입)를 제거하여, tickAmount 솎아내기 기능과 충돌을 파쇄하고 모든 눈금 영역에 올바른 날짜를 노출
      // 중요: ApexCharts의 category 축에서 중복된 문자열(예: '11')이 들어가면
      // 틱 생성 알고리즘이 망가지므로, 무조건 고유값인 trade_date를 카테고리로 씁니다.
      categories.push(item.trade_date);

      return {
        trade_date: item.trade_date,
        open_price: Number(item.open_price || 0),
        high_price: Number(item.high_price || 0),
        low_price: Number(item.low_price || 0),
        close_price: Number(item.close_price || 0),
        rawDate: `${year}-${monthStr}-${dayStr}`,
      };
    });

    // 2단계: 5일 및 20일 이동평균선(MA) 계산 (주말 공백 없는 영업일 밀착형 연산)
    const ma5Data = [];
    const ma20Data = [];

    for (let i = 0; i < rawList.length; i++) {
      // 5일선
      if (i < 4) {
        ma5Data.push(null);
      } else {
        let sum = 0;
        for (let j = 0; j < 5; j++) {
          sum += rawList[i - j].close_price;
        }
        ma5Data.push(Math.round(sum / 5));
      }

      // 20일선
      if (i < 19) {
        ma20Data.push(null);
      } else {
        let sum = 0;
        for (let j = 0; j < 20; j++) {
          sum += rawList[i - j].close_price;
        }
        ma20Data.push(Math.round(sum / 20));
      }
    }

    // 3단계: 고유 문자열(trade_date) 매칭 기반 오버레이 시리즈 빌드
    const series = [
      {
        name: '현재가 (OHLC)',
        type: 'candlestick',
        data: rawList.map((item) => ({
          x: item.trade_date, // 숫자 인덱스가 아닌 고유 날짜 문자열로 완벽 결합
          y: [item.open_price, item.high_price, item.low_price, item.close_price],
        })),
      },
      {
        name: '5일 이동평균선',
        type: 'line',
        data: ma5Data.map((val, idx) => ({
          x: rawList[idx].trade_date,
          y: val,
        })),
      },
      {
        name: '20일 이동평균선',
        type: 'line',
        data: ma20Data.map((val, idx) => ({
          x: rawList[idx].trade_date,
          y: val,
        })),
      },
    ];

    return { categories, series, rawList, tempTransitions };
  }, [ohlcvData]);

  // React 성능 최적화: 차트 옵션 메모이제이션 (카테고리 축 기반의 정밀 레이아웃 정립)
  const chartOptions = useMemo(() => {
    return {
      chart: {
        type: 'line',
        height: 400,
        toolbar: {
          show: true,
        },
        background: 'var(--surface-card)',
        events: {
          zoomed: handleChartPanZoom,
          scrolled: handleChartPanZoom,
          click: function (event, chartContext, config) {
            const idx = config.dataPointIndex;
            // 캔들/데이터 포인트를 클릭했을 때만 툴팁 토글 동작
            if (idx !== undefined && idx !== -1) {
              setCustomClickTooltip((prev) => {
                // 동일한 캔들을 다시 클릭하면 숨김
                if (prev.visible && prev.dataPointIndex === idx) {
                  return { ...prev, visible: false };
                }
                const item = chartData.rawList[idx];
                // 줌/패닝 등 차트 도구 클릭 시 유효하지 않은 인덱스 차단
                if (!item) return prev;

                const prevItem = idx > 0 ? chartData.rawList[idx - 1] : null;
                const prevClose = prevItem ? prevItem.close_price : item.open_price;
                const ma5Val = chartData.series[1].data[idx]?.y;
                const ma20Val = chartData.series[2].data[idx]?.y;
                return {
                  visible: true,
                  item,
                  prevClose,
                  ma5Val,
                  ma20Val,
                  x: event.clientX,
                  y: event.clientY,
                  dataPointIndex: idx,
                };
              });
            } else {
              // 차트의 빈 공간 클릭 시 툴팁 숨김
              setCustomClickTooltip((prev) => ({ ...prev, visible: false }));
            }
          },
        },
      },
      colors: ['#eb3c46', '#ff9436', '#3f72df'], // 미래에셋 기준 색상: 상승 레드, 5일선 오렌지, 20일선 블루
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
        tickPlacement: 'on', // 틱 마크와 라벨을 캔들 중앙에 완벽히 정렬합니다.
        // tickAmount를 제거하여 틱이 캔들과 100% 일치하도록 강제 결합합니다.
        axisBorder: {
          color: 'var(--surface-border)',
        },
        axisTicks: {
          color: 'var(--surface-border)',
        },
        tooltip: {
          enabled: false, // Label 2: 하단 X축 크로스헤어 라벨 영구 숨김
        },
        labels: {
          rotate: 0, // 글자가 45도로 눕지 않고 완벽한 수평 정렬을 유지하도록 통제
          rotateAlways: false,
          hideOverlappingLabels: true, // 겹치는 라벨 자동 숨김 (수동 솎아내기 제거)
          formatter: (val) => {
            if (!val || typeof val !== 'string') return val;
            const idx = chartData.rawList.findIndex((r) => r.trade_date === val);
            if (idx !== -1 && chartData.tempTransitions && chartData.tempTransitions[idx]) {
              // 솎아내지 않고 무조건 정확한 라벨을 반환하여 어긋남(Shift) 착시 방지
              return chartData.tempTransitions[idx].label;
            }
            return val;
          },
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
            upward: '#eb3c46', // 양봉(상승): 미래에셋 레드
            downward: '#2b7eed', // 음봉(하락): 미래에셋 블루
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
        // 기본 툴팁 박스는 렌더링하지 않음 (대신 React 오버레이 컴포넌트로 렌더링)
        // 빈 문자열을 반환하면 십자선(Crosshair)은 유지되면서 내용은 비워집니다.
        custom: () => '<div style="display: none;"></div>',
      },
    };
  }, [stockName, stockCode, chartData]);

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
        <span className="text-500 font-semibold monospace">CODE: {stockCode}</span>
      </div>

      <Card className="shadow-4 border-round p-3 relative">
        {/* 전체 화면 토글 버튼 */}
        <div className="absolute top-0 right-0 p-3 z-5">
            <Button
              icon="pi pi-expand"
              className="p-button-rounded p-button-text p-button-secondary"
              tooltip="전체 화면 토글"
              onClick={toggleFullscreen}
            />
        </div>

        {isChartLoading && ohlcvData.length === 0 ? (
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
          <div
            ref={chartContainerRef}
            className="relative"
            style={{
              minHeight: '400px',
              height: isFullscreen ? '100vh' : 'auto',
              backgroundColor: 'var(--surface-card)',
            }}
          >
            {isChartLoading && (
              <div 
                className="absolute top-0 left-0 w-full h-full flex flex-column align-items-center justify-content-center z-5 border-round"
                style={{ backgroundColor: 'rgba(128, 128, 128, 0.15)', backdropFilter: 'blur(2px)' }}
              >
                <ProgressSpinner style={{ width: '40px', height: '40px' }} strokeWidth="4" animationDuration=".5s" />
                <span className="text-600 font-bold mt-2 text-sm shadow-1">과거 주가 데이터 백필 중...</span>
              </div>
            )}
            <Chart
              options={chartOptions}
              series={chartData.series}
              type="line" // 복합(Mixed) 차트 렌더링 활성화를 위해 메인 타입을 line으로 정의
              height={isFullscreen ? '100%' : 400}
              width="100%"
            />
          </div>
        )}
      </Card>

      {/* 기본 ApexCharts 툴팁 잔여 껍데기를 가리는 글로벌 스타일 */}
      <style>{`
        .apexcharts-tooltip {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
        }
        /* 전체 화면 모드일 때 차트 높이 자동 조절 */
        :fullscreen .apexcharts-canvas {
            height: 100% !important;
        }
      `}</style>

      {/* 클릭 기반 React 커스텀 툴팁 (Label 1) */}
      {customClickTooltip.visible &&
        customClickTooltip.item &&
        (() => {
          const { item, prevClose, ma5Val, ma20Val } = customClickTooltip;

          // 이전 거래일 종가(또는 당일 시가) 대비 등락 색상 계산 (다크 배경용 밝은 컬러)
          const getPriceColor = (price) => {
            if (!prevClose || price === prevClose) return '#f8f9fa';
            return price > prevClose ? '#ff6666' : '#64a0ff';
          };

          // 등락률 문자열 계산 (Prime Icon 적용)
          const getDiffNode = (price) => {
            if (!prevClose || price === prevClose) return <span>0.00%</span>;
            const diff = ((price - prevClose) / prevClose) * 100;
            const isUp = diff > 0;
            return (
              <span
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  gap: '4px',
                }}
              >
                <i
                  className={`pi ${isUp ? 'pi-caret-up' : 'pi-caret-down'}`}
                  style={{ fontSize: '0.75rem' }}
                ></i>
                {Math.abs(diff).toFixed(2)}%
              </span>
            );
          };

          return (
            <div
              className="monospace custom-stock-tooltip"
              style={{
                top: Math.min(customClickTooltip.y + 15, window.innerHeight - 250) + 'px',
                left: Math.min(customClickTooltip.x + 15, window.innerWidth - 250) + 'px',
              }}
            >
              <div className="tooltip-header">
                <i className="pi pi-calendar"></i>
                {item.rawDate}
              </div>
              <div className="price-row">
                시가:{' '}
                <div className="price-group">
                  <span className="price-val" style={{ color: getPriceColor(item.open_price) }}>
                    {item.open_price.toLocaleString()}
                  </span>
                  <span className="price-diff" style={{ color: getPriceColor(item.open_price) }}>
                    {getDiffNode(item.open_price)}
                  </span>
                </div>
              </div>
              <div className="price-row">
                고가:{' '}
                <div className="price-group">
                  <span className="price-val" style={{ color: getPriceColor(item.high_price) }}>
                    {item.high_price.toLocaleString()}
                  </span>
                  <span className="price-diff" style={{ color: getPriceColor(item.high_price) }}>
                    {getDiffNode(item.high_price)}
                  </span>
                </div>
              </div>
              <div className="price-row">
                저가:{' '}
                <div className="price-group">
                  <span className="price-val" style={{ color: getPriceColor(item.low_price) }}>
                    {item.low_price.toLocaleString()}
                  </span>
                  <span className="price-diff" style={{ color: getPriceColor(item.low_price) }}>
                    {getDiffNode(item.low_price)}
                  </span>
                </div>
              </div>
              <div className="price-row stock-divider">
                종가:{' '}
                <div className="price-group">
                  <span className="price-val" style={{ color: getPriceColor(item.close_price) }}>
                    {item.close_price.toLocaleString()}
                  </span>
                  <span className="price-diff" style={{ color: getPriceColor(item.close_price) }}>
                    {getDiffNode(item.close_price)}
                  </span>
                </div>
              </div>
              <div className="ma-row mt-4">
                <span className="ma-label" style={{ color: '#ff9436' }}>
                  5일선:
                </span>
                <span className="ma-val">
                  {ma5Val !== null && ma5Val !== undefined ? `${ma5Val.toLocaleString()} 원` : '-'}
                </span>
              </div>
              <div className="ma-row mt-2">
                <span className="ma-label" style={{ color: '#3f72df' }}>
                  20일선:
                </span>
                <span className="ma-val">
                  {ma20Val !== null && ma20Val !== undefined
                    ? `${ma20Val.toLocaleString()} 원`
                    : '-'}
                </span>
              </div>
            </div>
          );
        })()}
    </div>
  );
}
