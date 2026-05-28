export interface KpiDataItem {
  id: string;
  title: string;
  icon: string;
  iconColor: string;
  value: string;
  subValue?: string;
  change: string;
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
    change: '0.00%',
    bgColor: 'var(--orange-50)',
    borderColor: 'var(--orange-500)',
  },
  {
    id: 'this_month',
    title: '금월 투자수익',
    icon: 'fa-solid fa-calendar-days',
    iconColor: 'var(--green-500)',
    value: '0',
    change: '0.00%',
    bgColor: 'var(--green-50)',
    borderColor: 'var(--green-500)',
  },
  {
    id: 'this_year',
    title: '금년 투자수익',
    icon: 'fa-solid fa-calendar',
    iconColor: 'var(--indigo-500)',
    value: '0',
    change: '0.00%',
    bgColor: 'var(--indigo-50)',
    borderColor: 'var(--indigo-500)',
  },
  {
    id: 'total',
    title: '총 평가 수익 <span class="title-sub text-sm ml-1">(총 평가 자산)</span>',
    icon: 'fa-solid fa-trophy',
    iconColor: 'var(--purple-500)',
    value: '0',
    subValue: '0',
    change: '0.00%',
    bgColor: 'var(--purple-50)',
    borderColor: 'var(--purple-500)',
  },
];
