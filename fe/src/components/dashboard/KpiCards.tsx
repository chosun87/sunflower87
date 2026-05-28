import { useState, useEffect } from 'react';
import { Panel } from '@/assets/ts/PrimeReact';
import { kpiData, KpiDataItem } from '@/data/kpiData';
import { getDashboardKpi } from '@/api';

const formatCurrency = (num: number) => {
  return new Intl.NumberFormat('ko-KR').format(num);
};

const formatPercent = (num: number) => {
  return `${num > 0 ? '+' : ''}${num.toFixed(2)}%`;
};

const isZero = (str: string) => {
  const numericString = String(str).replace(/[^0-9.-]+/g, '');
  return Number(numericString) === 0;
};

export default function KpiCards() {
  const [data, setData] = useState<KpiDataItem[]>(kpiData);

  useEffect(() => {
    const fetchData = () => {
      getDashboardKpi()
        .then((res: any) => {
          const kpi = res.data;
          const updated = kpiData.map((card) => {
            let valueStr = card.value;
            let subValueStr = card.subValue;
            let changeStr = card.change;
            const kpiSection = kpi[card.id];
            if (kpiSection) {
              if (card.id === 'total') {
                valueStr = formatCurrency(kpiSection.profit);
                subValueStr = formatCurrency(kpiSection.total_asset);
              } else {
                valueStr = formatCurrency(kpiSection.profit);
              }
              changeStr = formatPercent(kpiSection.return_rate);
            }

            return {
              ...card,
              value: valueStr,
              subValue: subValueStr,
              change: changeStr,
            };
          });
          setData(updated);
        })
        .catch((err: any) => {
          console.error('Failed to load KPI data', err);
        });
    };

    fetchData();

    window.addEventListener('market-data-updated', fetchData);
    return () => {
      window.removeEventListener('market-data-updated', fetchData);
    };
  }, []);

  return (
    <div className="kpi-grid">
      {data.map((card) => (
        <Panel
          key={card.id}
          className="custom-panel"
          style={{ backgroundColor: card.bgColor, borderColor: card.borderColor }}
          header={
            <div className="panel-header-title" style={{ backgroundColor: card.bgColor }}>
              <i className={`${card.icon} mr-2`} style={{ color: card.iconColor }}></i>
              <span className="title-text" dangerouslySetInnerHTML={{ __html: card.title }} />
            </div>
          }
        >
          <div className="flex align-items-center justify-content-end gap-3">
            <div className="value-wrap">
              {card.subValue && <span className="sub-value text-sm font-bold mr-2">({card.subValue})</span>}
              <span
                className={`text-3xl font-bold mb-2 ${isZero(card.value)
                  ? ''
                  : card.id === 'total' || !String(card.value).includes('-')
                    ? 'text-up'
                    : 'text-down'
                  }`}
              >
                {card.value}
              </span>
            </div>

            <span
              className={`font-semibold ${isZero(card.change)
                ? ''
                : String(card.change).includes('-')
                  ? 'text-down'
                  : 'text-up'
                }`}
            >
              <i
                className={`${isZero(card.change)
                  ? ''
                  : String(card.change).includes('-')
                    ? 'fa-solid fa-arrow-trend-down'
                    : 'fa-solid fa-arrow-trend-up'
                  } mr-1`}
              ></i>
              {card.change}
            </span>
          </div>
        </Panel>
      ))}
    </div>
  );
}
