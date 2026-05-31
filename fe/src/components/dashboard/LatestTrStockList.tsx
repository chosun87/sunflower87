import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { Column, DataTable, Badge, Button } from '@/assets/ts/PrimeReact';
import CustomPanel from '@components/CustomPanel';
import { get } from '@/api/index';
import { TRADE_TYPE } from '@/assets/ts/constants';

export interface Transaction {
  id: number;
  acc_cd: string;
  dt_trade: string;
  trade_type: string;
  stock_code: string;
  stock_name: string;
  quantity: number;
  price: number;
  tax_fee: number;
}

const MAXROW = 4;

export default function LatestTrStockList() {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    const fetchLatestTransactions = async () => {
      try {
        const res = await get('/api/transactions', { limit: MAXROW });
        if (res.status === 'success') {
          const mapped = (res.data || [])
            .map((tx: any) => ({
              ...tx,
              tx_id: tx.id,
            }))
            .slice(0, MAXROW); // 최근 5건만 가져오기
          setTransactions(mapped);
        }
      } catch (e) {
        console.error('Failed to load latest transactions:', e);
      }
    };
    fetchLatestTransactions();
  }, []);

  // --- [템플릿 렌더러 정의] ---
  const tradeTypeBodyTemplate = (rowData: Transaction) => {
    const key = (rowData.trade_type || '').toUpperCase();
    const typeInfo = TRADE_TYPE[key as keyof typeof TRADE_TYPE] || {
      label: rowData.trade_type,
      color: 'text-gray-500',
    };
    const badgeClass = typeInfo.color.replace('text-', 'bg-') + ' text-white';
    return <Badge value={typeInfo.label} className={badgeClass} />;
  };

  const dtTradeBodyTemplate = (rowData: Transaction) => {
    return (
      <span className="monospace">
        {rowData.dt_trade ? dayjs(rowData.dt_trade).format('MM/DD') : ''}
      </span>
    );
  };

  const quantityBodyTemplate = (rowData: Transaction) => {
    return <span className="monospace">{Number(rowData.quantity).toLocaleString()}</span>;
  };

  const priceBodyTemplate = (rowData: Transaction) => {
    return <span className="monospace">{Number(rowData.price).toLocaleString()}</span>;
  };

  const amountBodyTemplate = (rowData: Transaction) => {
    return (
      <span className="monospace">
        {(Number(rowData.quantity) * Number(rowData.price)).toLocaleString()}
      </span>
    );
  };

  // --- [커스텀 패널 헤더 (전체화면 버튼 및 더보기 버튼 제어)] ---
  const headerTemplate = (options: any) => {
    const combinedClassName = `${options.className} align-items-center w-full`;
    return (
      <div className={combinedClassName}>
        <div className="p-panel-title">
          <div className="panel-header-title">
            <i className="panel-header-title-icon fa-solid fa-receipt"></i>
            <span>최근 매매 내역 </span>
          </div>
        </div>
        <div className="panel-header-actions">
          {/* 전체화면 버튼 클릭 시 주식 매매 내역 화면으로 이동 (더보기 버튼은 렌더링하지 않음) */}
          <Button
            icon="fa-solid fa-expand"
            rounded
            text
            severity="secondary"
            onClick={() => navigate('/transactionStock')}
            title="주식매매내역 전체화면으로 이동"
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
        emptyMessage="최근 거래 기록이 존재하지 않습니다."
      >
        <Column field="dt_trade" header="거래일" body={dtTradeBodyTemplate}></Column>
        <Column field="trade_type" header="구분" body={tradeTypeBodyTemplate}></Column>
        <Column field="stock_name" header="거래종목"></Column>
        <Column
          field="quantity"
          header="거래수량"
          align="right"
          body={quantityBodyTemplate}
        ></Column>
        <Column field="price" header="거래단가" align="right" body={priceBodyTemplate}></Column>
        <Column header="거래금액" align="right" body={amountBodyTemplate}></Column>
      </DataTable>
    </CustomPanel>
  );
}
