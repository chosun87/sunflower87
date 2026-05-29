import { useMemo, useState, useRef } from 'react';
import dayjs from 'dayjs';
import { DataTable, Column, Badge, Button, Dropdown, Calendar } from '@/assets/ts/PrimeReact';
import { CASH_TYPE } from '@/assets/ts/constants';

export default function TransactionCashCmpt({
  transactions,
  accounts,
  onLoadTransactions,
  onAddClick,
  onEditClick,
  onDeleteClick,
}) {
  const [dates, setDates] = useState(null);
  const calendarRef = useRef<any>(null);

  const handleDateChange = (e: any) => {
    const selectedDates = e.value;
    setDates(selectedDates);
    if (selectedDates && selectedDates.length === 2 && selectedDates[1] !== null) {
      calendarRef.current?.hide();
    }
  };
  const [selectedAcc, setSelectedAcc] = useState(null);

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

  const cashTypeBodyTemplate = (rowData: any) => {
    const key = (rowData.cash_type || '').toUpperCase();
    const typeInfo = CASH_TYPE[key as keyof typeof CASH_TYPE] || {
      label: rowData.cash_type,
      color: 'text-gray-500',
    };
    const badgeClass = typeInfo.color.replace('text-', 'bg-') + ' text-white';
    return <Badge value={typeInfo.label} className={badgeClass} />;
  };

  const dtCashBodyTemplate = (rowData: any) => {
    return rowData.dt_cash ? (
      <span className="monospace">{dayjs(rowData.dt_cash).format('YYYY-MM-DD')}</span>
    ) : (
      ''
    );
  };

  const accCdBodyTemplate = (rowData: any) => {
    const matchedAcc = accounts?.find((a: any) => a.acc_cd === rowData.acc_cd);
    const company = rowData.acc_company_nm || matchedAcc?.acc_company_nm || '';
    const name = rowData.acc_nm || matchedAcc?.acc_nm || rowData.acc_cd;
    if (company) {
      const shortCompany = company.substring(0, 2);
      return `[${shortCompany}] ${name}`;
    }
    return name;
  };

  const amountBodyTemplate = (rowData: any) => {
    return <span className="monospace font-bold">{(rowData.amount || 0).toLocaleString()} 원</span>;
  };

  const descriptionBodyTemplate = (rowData: any) => {
    return <span>{rowData.description}</span>;
  };

  const actionsBodyTemplate = (rowData: any) => {
    return (
      <div className="flex justify-content-end gap-2">
        <Button
          icon="fa-solid fa-pencil"
          className="p-button-rounded p-button-text p-button-success"
          tooltip="내역 수정"
          tooltipOptions={{ position: 'top' }}
          onClick={() => onEditClick(rowData)}
        />
        <Button
          icon="fa-solid fa-trash"
          className="p-button-rounded p-button-text p-button-danger"
          tooltip="내역 삭제"
          tooltipOptions={{ position: 'top' }}
          onClick={() => onDeleteClick(rowData)}
        />
      </div>
    );
  };

  const totalAmountSum = useMemo(() => {
    return (transactions || []).reduce((sum: number, tx: any) => sum + (tx.amount || 0), 0);
  }, [transactions]);

  return (
    <div className="transaction-cash-cmpt">
      <div className="flex align-items-center w-full mb-4 bg-gray-50 border-round">
        <div className="flex flex-wrap flex-1 gap-2">
          <div className="p-inputgroup max-w-20rem">
            <span className="p-inputgroup-addon">
              <i className="fa-solid fa-calendar"></i>
            </span>
            <Calendar
              ref={calendarRef}
              value={dates}
              onChange={handleDateChange}
              selectionMode="range"
              locale="ko"
              dateFormat="yy-mm-dd"
              readOnlyInput
              placeholder="기간 선택"
              className="w-full"
              showButtonBar
            />
          </div>
          <div className="p-inputgroup max-w-20rem">
            <span className="p-inputgroup-addon">
              <i className="fa-solid fa-wallet"></i>
            </span>
            <Dropdown
              value={selectedAcc}
              options={accounts}
              onChange={(e) => setSelectedAcc(e.value)}
              optionLabel="acc_nm"
              optionValue="acc_cd"
              placeholder="전체 계좌"
              showClear
            />
          </div>
          <Button icon="fa-solid fa-search" label="검색" onClick={handleSearch} />
        </div>

        <Button
          raised
          icon="fa-solid fa-plus"
          label="내역 추가"
          className="ml-2 p-button-primary"
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
        emptyMessage="조건에 맞는 입출금 내역이 존재하지 않습니다."
      >
        <Column
          field="dt_cash"
          header="거래일"
          body={dtCashBodyTemplate}
          sortable
          footer={<span className="font-bold">합계</span>}
        ></Column>
        <Column field="cash_type" header="구분" body={cashTypeBodyTemplate} sortable></Column>
        <Column field="acc_cd" header="거래 계좌" body={accCdBodyTemplate} sortable></Column>
        <Column field="description" header="적요" body={descriptionBodyTemplate} sortable></Column>
        <Column
          field="amount"
          header="금액 (원)"
          align="right"
          body={amountBodyTemplate}
          sortable
          footer={
            <span className="monospace font-bold text-primary">
              {totalAmountSum.toLocaleString()} 원
            </span>
          }
        ></Column>
        <Column
          header="수정 &#8226; 삭제"
          body={actionsBodyTemplate}
          exportable={false}
          align="right"
          className="p-0"
          style={{ minWidth: '6rem' }}
        ></Column>
      </DataTable>
    </div>
  );
}
