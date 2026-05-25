import { Panel } from '@/assets/ts/PrimeReact';
import { kpiData } from '@/data/kpiData';

export default function KpiCards() {
  return (
    <div className="kpi-grid">
      {kpiData.map((card) => (
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
