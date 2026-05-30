import { DataTable, Column, Button, Checkbox } from '@/assets/ts/PrimeReact';

interface AccountListCmptProps {
  accounts: any[];
  includeDeleted: boolean;
  onIncludeDeletedChange: (val: boolean) => void;
  onAddClick: () => void;
  onEditClick: (account: any) => void;
  onDeleteClick: (account: any) => void;
}

export default function AccountListCmpt({
  accounts,
  includeDeleted,
  onIncludeDeletedChange,
  onAddClick,
  onEditClick,
  onDeleteClick,
}: AccountListCmptProps) {
  


  const actionBodyTemplate = (rowData: any) => {
    const isDeleted = !!rowData.dt_deleted;
    return (
      <div className="flex justify-content-center gap-2">
        <Button
          icon="fa-solid fa-pencil"
          className="p-button-rounded p-button-text p-button-success"
          tooltip="계좌 수정"
          tooltipOptions={{ position: 'top' }}
          onClick={() => onEditClick(rowData)}
          disabled={isDeleted}
        />
        <Button
          icon="fa-solid fa-trash"
          className="p-button-rounded p-button-text p-button-danger"
          tooltip="계좌 삭제"
          tooltipOptions={{ position: 'top' }}
          onClick={() => onDeleteClick(rowData)}
          disabled={isDeleted}
        />
      </div>
    );
  };

  const statusBodyTemplate = (rowData: any) => {
    const isDeleted = !!rowData.dt_deleted;
    if (isDeleted) {
      return <span className="text-red-500 font-bold">비활성</span>;
    }
    return <span className="text-green-500 font-bold">활성</span>;
  };

  return (
    <div className="account-list-cmpt">
      <div className="flex align-items-center w-full mb-4 bg-gray-50 border-round">
        <div className="flex flex-wrap flex-1 gap-2 align-items-center">
          <Checkbox
            inputId="includeDeleted"
            checked={includeDeleted}
            onChange={(e) => onIncludeDeletedChange(e.checked || false)}
          />
          <label htmlFor="includeDeleted" className="ml-2 cursor-pointer">삭제 계좌 포함</label>
        </div>

        <Button
          raised
          icon="fa-solid fa-plus"
          label="새 계좌 등록"
          className="ml-2 p-button-primary"
          onClick={onAddClick}
        />
      </div>
      <DataTable
        value={accounts}
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
        emptyMessage="등록된 계좌가 없습니다."
      >
        <Column field="acc_cd" header="계좌 코드" sortable />
        <Column field="acc_nm" header="계좌명" sortable />
        <Column field="acc_company_nm" header="금융사명" sortable />
        <Column field="dt_opened" header="계좌 개설일" sortable />
        <Column header="상태" body={statusBodyTemplate} sortable align="center" />
        <Column header="수정·삭제" body={actionBodyTemplate} exportable={false} align="center" style={{ minWidth: '6rem' }} />
      </DataTable>
    </div>
  );
}
