import { useState, useEffect } from 'react';
import { Panel } from '@/assets/ts/PrimeReact';
import { kpiData, KpiDataItem } from '@/data/kpiData';
import { getDashboardKpi } from '@/api';

const formatCurrency = (num: number) => {
  return '₩' + new Intl.NumberFormat('ko-KR').format(num);
};

const formatPercent = (num: number) => {
  return `${num > 0 ? '+' : ''}${num}%`;
};

export default function KpiCards() {
  const [data, setData] = useState<KpiDataItem[]>(kpiData);

  useEffect(() => {
    getDashboardKpi()
      .then((res: any) => {
        const kpi = res.data;
        const updated = kpiData.map(card => {
          let valueStr = card.value;
          let changeStr = card.change;
          let isValueUp = card.isValueUp;
          let isChangeUp = card.isChangeUp;

          const kpiSection = kpi[card.id];
          if (kpiSection) {
            valueStr = formatCurrency(card.id === 'total' ? kpiSection.total_asset : kpiSection.profit);
            changeStr = formatPercent(kpiSection.return_rate);
            isValueUp = card.id === 'total' ? true : kpiSection.profit >= 0;
            isChangeUp = kpiSection.return_rate >= 0;
          }

          return {
            ...card,
            value: valueStr,
            change: changeStr,
            isValueUp,
            isChangeUp
          };
        });
        setData(updated);
      })
      .catch((err: any) => {
        console.error("Failed to load KPI data", err);
      });
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
              <span>{card.title}</span>
            </div>
          }
        >
          <div className="flex align-items-center justify-content-end gap-3">
            <span
              className={`text-3xl font-bold monospace mb-2 ${card.isValueUp ? 'text-up' : 'text-down'}`}
            >
              {card.value}
            </span>

            <span
              className={`text-sm font-semibold monospace ${card.isChangeUp ? 'text-up' : 'text-down'}`}
            >
              <i
                className={`fa-solid ${card.isChangeUp ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down'} mr-1`}
              ></i>
              {card.change}
            </span>
          </div>
        </Panel>
      ))}
    </div>
  );
}
