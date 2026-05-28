import { useMemo, useState } from 'react';
import dayjs from 'dayjs';
import {
  DataTable,
  Column,
  Badge,
  Button,
  Dropdown,
  InputText,
  Calendar,
} from '@/assets/ts/PrimeReact';
import { TRADE_TYPE } from '@/assets/ts/constants';

export default function TransactionStockCmpt({
  transactions,
  accounts,
  onLoadTransactions,
  onAddClick,
  onEditClick,
  onDeleteClick,
}) {
  const [dates, setDates] = useState(null);
  const [selectedAcc, setSelectedAcc] = useState(null);
  const [searchCode, setSearchCode] = useState(null);

  const stockOptions = useMemo(() => {
    const stockMap = new Map();
    const addStock = (stock) => {
      if (!stock || !stock.stock_code) return;
      const quantity = Number(stock.quantity || 0);
      const existing = stockMap.get(stock.stock_code);
      if (existing) {
        existing.quantity = Math.max(existing.quantity, quantity);
      } else {
        stockMap.set(stock.stock_code, {
          value: stock.stock_code,
          label: stock.stock_name,
          quantity,
        });
      }
    };

    const relevantAccounts = selectedAcc
      ? accounts?.filter((acc) => acc.acc_cd === selectedAcc)
      : accounts;

    (relevantAccounts || []).forEach((account) => {
      (account.stocks || []).forEach(addStock);
    });

    return Array.from(stockMap.values()).sort((a, b) => {
      if (b.quantity !== a.quantity) {
        return b.quantity - a.quantity;
      }
      return a.label.localeCompare(b.label, 'ko');
    });
  }, [accounts, selectedAcc]);

  const stockItemTemplate = (option) => {
    if (!option) return null;
    return (
      <div className="flex align-items-center gap-2">
        <span className="text-500 monospace">{option.value})</span>
        <span>{option.label}</span>
        {option.quantity > 0 && (
          <span className="ml-auto text-500">(보유: {option.quantity.toLocaleString()}주)</span>
        )}
      </div>
    );
  };

  const buildSearchFilters = () => {
    let start_date = null;
    let end_date = null;

    if (dates && dates[0]) {
      start_date = dayjs(dates[0]).format('YYYY-MM-DD');
    }
    if (dates && dates[1]) {
      end_date = dayjs(dates[1]).format('YYYY-MM-DD');
    }

    return {
      acc_cd: selectedAcc,
      stock_code: searchCode,
      start_date,
      end_date,
    };
  };

  const handleSearch = () => {
    if (onLoadTransactions) {
      onLoadTransactions(buildSearchFilters());
    }
  };

  // --- [매매 내역 전용 내부 템플릿 렌더러 정의] ---

  const tradeTypeBodyTemplate = (rowData) => {
    const key = (rowData.trade_type || '').toUpperCase();
    const typeInfo = TRADE_TYPE[key as keyof typeof TRADE_TYPE] || {
      label: rowData.trade_type,
      color: 'text-gray-500',
    };
    const badgeClass = typeInfo.color.replace('text-', 'bg-') + ' text-white';
    return <Badge value={typeInfo.label} className={badgeClass} />;
  };

  const dtTradeBodyTemplate = (rowData) => {
    return rowData.dt_trade ? (
      <span className="monospace">{dayjs(rowData.dt_trade).format('YYYY-MM-DD HH:mm')}</span>
    ) : (
      ''
    );
  };

  const accCdBodyTemplate = (rowData: any) => {
    const company = rowData.acc_company_nm || '';
    const name = rowData.acc_nm || '알 수 없는 계좌';
    if (company) {
      const shortCompany = company.substring(0, 2);
      return `[${shortCompany}] ${name}`;
    }
    return name;
  };

  const stockCodeBodyTemplate = (rowData) => {
    return <span className="monospace">{rowData.stock_code}</span>;
  };

  const quantityBodyTemplate = (rowData) => {
    return <span className="monospace">{rowData.quantity.toLocaleString()} 주</span>;
  };

  const priceBodyTemplate = (rowData) => {
    return <span className="monospace">{rowData.price.toLocaleString()} 원</span>;
  };

  const amountBodyTemplate = (rowData) => {
    return (
      <span className="monospace">{(rowData.quantity * rowData.price).toLocaleString()} 원</span>
    );
  };

  const taxFeeBodyTemplate = (rowData) => {
    const fee = rowData.tax_fee || 0;
    return <span className="monospace">{fee.toLocaleString()} 원</span>;
  };

  const actionsBodyTemplate = (rowData) => {
    return (
      <div className="flex justify-content-end">
        <Button
          icon="fa-solid fa-pencil"
          className="p-button-rounded p-button-text p-button-success"
          tooltip="매매 내역 수정"
          tooltipOptions={{ position: 'top' }}
          onClick={() => onEditClick(rowData)}
        />
        <Button
          icon="fa-solid fa-trash"
          className="p-button-rounded p-button-text p-button-danger"
          tooltip="매매 내역 삭제"
          tooltipOptions={{ position: 'top' }}
          onClick={() => onDeleteClick(rowData)}
        />
      </div>
    );
  };

  const { totalTxAmountSum, totalTxTaxFeeSum, totalQuantitySum } = useMemo(() => {
    let totalBuyAmount = 0;
    let totalSellAmount = 0;

    (transactions || []).forEach((tx) => {
      const amount = (tx.quantity || 0) * (tx.price || 0);
      if (tx.trade_type === TRADE_TYPE.SELL.code || tx.trade_type === 'sell') {
        totalSellAmount += amount;
      } else {
        totalBuyAmount += amount;
      }
    });

    const totalTxAmountSum = totalSellAmount - totalBuyAmount;
    const totalQuantitySum = (transactions || []).reduce((sum, tx) => {
      const quantity = tx.quantity || 0;
      if (tx.trade_type === TRADE_TYPE.SELL.code || tx.trade_type === 'sell') {
        return sum - quantity;
      }
      return sum + quantity;
    }, 0);
    const totalTxTaxFeeSum = (transactions || []).reduce((sum, tx) => sum + (tx.tax_fee || 0), 0);
    return { totalTxAmountSum, totalTxTaxFeeSum, totalQuantitySum };
  }, [transactions]);

  const totalTxAmountClass =
    totalTxAmountSum < 0 ? 'text-sell' : totalTxAmountSum > 0 ? 'text-buy' : '';
  const totalTxAmountText =
    totalTxAmountSum === 0
      ? '0 원'
      : `${totalTxAmountSum > 0 ? '+' : '-'}${Math.abs(totalTxAmountSum).toLocaleString()} 원`;

  return (
    <div className="transaction-stock-cmpt">
      <div className="flex align-items-center w-full mb-4 bg-gray-50 border-round">
        <div className="flex flex-wrap flex-1">
          <div className="p-inputgroup col-12 md:col-6 lg:col-4">
            <span className="p-inputgroup-addon">
              <i className="fa-solid fa-calendar"></i>
            </span>
            <Calendar
              value={dates}
              onChange={(e) => setDates(e.value)}
              selectionMode="range"
              locale="ko"
              dateFormat="yy-mm-dd"
              readOnlyInput
              placeholder="기간 선택"
              className="w-full"
              showButtonBar
            />
          </div>
          <div className="p-inputgroup col-12 md:col-6 lg:col-4">
            <span className="p-inputgroup-addon">
              <i className="fa-solid fa-calendar"></i>
            </span>
            <Dropdown
              value={selectedAcc}
              options={accounts}
              onChange={(e) => {
                setSelectedAcc(e.value);
                setSearchCode(null);
              }}
              optionLabel="acc_nm"
              optionValue="acc_cd"
              placeholder="전체 계좌"
              showClear
            />
          </div>
          <div className="p-inputgroup col-12 md:col-6 lg:col-4">
            <span className="p-inputgroup-addon">
              <i className="fa-solid fa-calendar"></i>
            </span>
            <Dropdown
              value={searchCode}
              options={stockOptions}
              onChange={(e) => setSearchCode(e.value)}
              optionLabel="label"
              optionValue="value"
              itemTemplate={stockItemTemplate}
              placeholder="종목 선택"
              showClear
            />
          </div>
        </div>

        <Button icon="fa-solid fa-search" label="검색" onClick={handleSearch} />

        <Button
          raised
          icon="fa-solid fa-plus"
          label="거래 내역 추가"
          className="ml-2"
          onClick={onAddClick}
        />
      </div>

      <DataTable
        value={transactions}
        responsiveLayout="stack"
        breakpoint="960px"
        sortMode="multiple"
        stripedRows
        paginator
        rows={10}
        rowsPerPageOptions={[5, 10, 25, 50]}
        currentPageReportTemplate="총 {totalRecords} 건"
        paginatorTemplate="CurrentPageReport FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
        scrollable
        className="mt-2"
        emptyMessage="조건에 맞는 매매 거래 히스토리가 존재하지 않습니다."
      >
        <Column
          field="dt_trade"
          header="거래 일시"
          body={dtTradeBodyTemplate}
          sortable
          footer={<span className="font-bold">합계</span>}
        ></Column>
        <Column field="trade_type" header="구분" body={tradeTypeBodyTemplate} sortable></Column>
        <Column field="acc_cd" header="거래 계좌" body={accCdBodyTemplate} sortable></Column>
        <Column field="stock_code" header="종목코드" body={stockCodeBodyTemplate} sortable></Column>
        <Column field="stock_name" header="종목명" sortable></Column>
        <Column
          field="quantity"
          header="거래 수량"
          align="right"
          body={quantityBodyTemplate}
          sortable
          footer={
            <span className="monospace font-bold">{totalQuantitySum.toLocaleString()} 주</span>
          }
        ></Column>
        <Column
          field="price"
          header="거래 단가"
          align="right"
          body={priceBodyTemplate}
          sortable
        ></Column>
        <Column
          header="총 거래금액"
          align="right"
          body={amountBodyTemplate}
          sortable
          footer={
            <span className={`monospace font-bold ${totalTxAmountClass}`}>{totalTxAmountText}</span>
          }
        ></Column>
        <Column
          field="tax_fee"
          header="세금+수수료"
          align="right"
          body={taxFeeBodyTemplate}
          sortable
          footer={
            <span className="monospace font-bold">{totalTxTaxFeeSum.toLocaleString()} 원</span>
          }
        ></Column>
        <Column
          header="수정 &#8226; 삭제"
          body={actionsBodyTemplate}
          exportable={false}
          align="right"
          className="p-0"
          style={{ minWidth: '4rem' }}
        ></Column>
      </DataTable>
    </div>
  );
}
