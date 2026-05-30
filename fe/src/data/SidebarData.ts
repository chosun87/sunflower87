export interface CustomMenuItem {
  key: string;
  label: string;
  icon?: string | null;
  data?: string;
  badge?: number;
  expanded?: boolean;
  children?: CustomMenuItem[];
}

export interface MenuSection {
  title: string;
  items: CustomMenuItem[];
}

export const menuData: MenuSection[] = [
  {
    title: 'MENU',
    items: [
      {
        key: 'dashboard',
        label: 'Dashboard',
        icon: 'fa-solid fa-gauge-high',
        data: '/dashboard',
      },
      {
        key: 'stockList',
        label: '보유 주식 현황',
        icon: 'fa-solid fa-book',
        data: '/stockList',
      },
      {
        key: 'transactionStock',
        label: '주식 매매 내역',
        icon: 'fa-solid fa-handshake',
        // badge: 5,
        data: '/transactionStock',
      },
      {
        key: 'transactionCash',
        label: '계좌 입출금 내역',
        icon: 'fa-solid fa-coins',
        data: '/transactionCash',
      },
      {
        key: 'account',
        label: '계좌 관리',
        icon: 'fa-solid fa-wallet',
        data: '/account',
      },
    ],
  },
  {
    title: 'Sync.',
    items: [
      {
        key: 'sync_data',
        label: '데이터 관리',
        icon: 'fa-solid fa-refresh',
        children: [
          { key: 'recal_stock_cache', label: '종목 최신화', data: '/recal_stock_cache' },
          { key: 'recal_cash_balance', label: '계좌별 예수금 정산', data: '/recal_cash_balance' },
          {
            key: 'sync_daily_balance',
            label: '일일 잔고 동기화',
            data: '/sync_account_daily_balance',
          },
        ],
      },
    ],
  },
  {
    title: 'OTHERS',
    items: [
      {
        key: 'settinngs',
        label: '설정',
        icon: 'fa-solid fa-cog',
        data: '/settings',
      },
    ],
  },
  {
    title: 'TEMPLATES',
    items: [
      {
        key: 'pages',
        label: 'Pages',
        icon: 'fa-solid fa-folder-open',
        children: [
          { key: 'tmp_blank', label: 'Blank', data: '/templates/blank' },
          { key: 'tmp_datatable', label: 'DataTable', data: '/templates/datatable' },
          { key: 'tmp_form', label: 'Form', data: '/templates/form' },
        ],
      },
    ],
  },
];
