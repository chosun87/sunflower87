export interface KpiDataItem {
  id: string;
  title: string;
  icon: string;
  iconColor: string;
  value: string;
  isValueUp: boolean;
  change: string;
  isChangeUp: boolean;
  bgColor: string;
  borderColor: string;
}

// KPI 요약 카드들에 사용되는 전용 고유 Mock 데이터
export const kpiData: KpiDataItem[] = [
  {
    id: 'today',
    title: '오늘 투자수익',
    icon: 'fa-solid fa-calendar-day',
    iconColor: 'var(--orange-500)',
    value: '0',
    isValueUp: false,
    change: '0.00%',
    isChangeUp: true,
    bgColor: 'var(--orange-50)',
    borderColor: 'var(--orange-500)',
  },
  {
    id: 'this_month',
    title: '금월 투자수익',
    icon: 'fa-solid fa-calendar-days',
    iconColor: 'var(--green-500)',
    value: '0',
    isValueUp: true,
    change: '0.00%',
    isChangeUp: true,
    bgColor: 'var(--green-50)',
    borderColor: 'var(--green-500)',
  },
  {
    id: 'this_year',
    title: '금년 투자수익',
    icon: 'fa-solid fa-calendar',
    iconColor: 'var(--indigo-500)',
    value: '0',
    isValueUp: false,
    change: '0.00%',
    isChangeUp: false,
    bgColor: 'var(--indigo-50)',
    borderColor: 'var(--indigo-500)',
  },
  {
    id: 'total',
    title: '총 평가 자산',
    icon: 'fa-solid fa-trophy',
    iconColor: 'var(--purple-500)',
    value: '0',
    isValueUp: true,
    change: '0.00%',
    isChangeUp: true,
    bgColor: 'var(--purple-50)',
    borderColor: 'var(--purple-500)',
  },
];
