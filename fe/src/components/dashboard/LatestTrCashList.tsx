import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { Column, DataTable, Badge, Button } from '@/assets/ts/PrimeReact';
import CustomPanel from '@components/CustomPanel';
import { get } from '@/api/index';
import { CASH_TYPE } from '@/assets/ts/constants';

export interface TransactionCash {
  id: number;
  acc_cd: string;
  acc_nm: string;
  acc_company_nm: string;
  dt_cash: string;
  cash_type: string;
  amount: number;
  description: string;
}

const MAXROW = 4;

export default function LatestTrCashList() {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState<TransactionCash[]>([]);

  useEffect(() => {
    const fetchLatestCash = async () => {
      try {
        const res = await get('/api/transactions_cash', { limit: MAXROW });
        if (res.status === 'success') {
          const mapped = (res.data || [])
            .map((tx: any) => ({
              ...tx,
              tx_id: tx.id,
              description: tx.description || '',
            }))
            .slice(0, MAXROW);
          setTransactions(mapped);
        }
      } catch (e) {
        console.error('Failed to load latest cash transactions:', e);
      }
    };
    fetchLatestCash();
  }, []);

  // --- [템플릿 렌더러 정의] ---
  const cashTypeBodyTemplate = (rowData: TransactionCash) => {
    // 소문자로 들어올 경우를 대비한 안전 장치 및 기본값 폴백
    const key = (rowData.cash_type || '').toUpperCase();
    const typeInfo = CASH_TYPE[key as keyof typeof CASH_TYPE] || {
      label: rowData.cash_type,
      color: 'text-gray-500',
    };
    const badgeClass = typeInfo.color.replace('text-', 'bg-') + ' text-white';
    return <Badge value={typeInfo.label} className={badgeClass} />;
  };

  const dtCashBodyTemplate = (rowData: TransactionCash) => {
    return (
      <span className="monospace">
        {rowData.dt_cash ? dayjs(rowData.dt_cash).format('MM/DD') : ''}
      </span>
    );
  };

  const accCdBodyTemplate = (rowData: TransactionCash) => {
    const company = rowData.acc_company_nm || '';
    const name = rowData.acc_nm || rowData.acc_cd;
    if (company) {
      const shortCompany = company.substring(0, 2);
      return `[${shortCompany}] ${name}`;
    }
    return name;
  };

  const amountBodyTemplate = (rowData: TransactionCash) => {
    return <span className="monospace">{Number(rowData.amount).toLocaleString()}</span>;
  };

  // --- [커스텀 패널 헤더 (전체화면 버튼 및 더보기 버튼 제어)] ---
  const headerTemplate = (options: any) => {
    const combinedClassName = `${options.className} align-items-center w-full`;
    return (
      <div className={combinedClassName}>
        <div className="p-panel-title">
          <div className="panel-header-title">
            <i className="panel-header-title-icon fa-solid fa-money-bill-transfer"></i>
            <span>최근 입출금 내역</span>
          </div>
        </div>
        <div className="panel-header-actions">
          <Button
            icon="fa-solid fa-expand"
            rounded
            text
            severity="secondary"
            onClick={() => navigate('/transactionCash')}
            title="입출금 내역 전체화면으로 이동"
          />
        </div>
      </div>
    );
  };

  return (
    <CustomPanel headerTemplate={headerTemplate}>
      <DataTable
        className="transactions-table"
        stripedRows
        responsiveLayout="scroll"
        value={transactions}
        emptyMessage="최근 입출금 기록이 존재하지 않습니다."
      >
        <Column field="dt_cash" header="거래일" body={dtCashBodyTemplate}></Column>
        <Column field="cash_type" header="구분" body={cashTypeBodyTemplate}></Column>
        <Column field="acc_cd" header="거래 계좌" body={accCdBodyTemplate}></Column>
        <Column field="description" header="적요"></Column>
        <Column field="amount" header="금액" align="right" body={amountBodyTemplate}></Column>
      </DataTable>
    </CustomPanel>
  );
}
