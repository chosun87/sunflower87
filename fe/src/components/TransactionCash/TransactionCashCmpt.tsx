import { useMemo, useState } from 'react';
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

  const txTypeBodyTemplate = (rowData: any) => {
    const typeInfo = CASH_TYPE[rowData.type as keyof typeof CASH_TYPE] || {
      label: rowData.type,
      color: 'text-gray-500',
    };

    // Badge 컴포넌트를 사용하여 라벨과 색상 반영. (색상은 PrimeReact 기본 severity를 쓰거나 className을 사용)
    // 여기서는 기존 스타일 방식을 유지하되, Tailwind 텍스트 색상 클래스를 직접 활용할 수 있도록 span으로 렌더링해도 됩니다.
    // 기존 TransactionStock은 className="type-buy" 등을 썼지만, 상수 객체에 color가 있으므로 이를 활용합니다.
    return <span className={`font-bold ${typeInfo.color}`}>{typeInfo.label}</span>;
  };

  const dateBodyTemplate = (rowData: any) => {
    return rowData.date ? (
      <span className="monospace">{dayjs(rowData.date).format('YYYY-MM-DD')}</span>
    ) : (
      ''
    );
  };

  const accountBodyTemplate = (rowData: any) => {
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

  const descBodyTemplate = (rowData: any) => {
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
          field="date"
          header="거래일"
          body={dateBodyTemplate}
          sortable
          footer={<span className="font-bold">합계</span>}
        ></Column>
        <Column field="type" header="구분" body={txTypeBodyTemplate} sortable></Column>
        <Column field="acc_cd" header="거래 계좌" body={accountBodyTemplate} sortable></Column>
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
        <Column field="description" header="적요" body={descBodyTemplate} sortable></Column>
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
