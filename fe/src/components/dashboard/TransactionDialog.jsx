import {
  Dialog,
  Button,
  SelectButton,
  Dropdown,
  InputText,
  InputNumber,
  Calendar,
} from '@/assets/js/PrimeReact'

export default function TransactionDialog({
  visible,
  onHide,
  editingTxId,
  txType,
  setTxType,
  txAccount,
  setTxAccount,
  accounts,
  txCode,
  setTxCode,
  txName,
  setTxName,
  txQuantity,
  setTxQuantity,
  txPrice,
  setTxPrice,
  txTaxFee,
  setTxTaxFee,
  txDate,
  setTxDate,
  isSearching,
  isSubmitting,
  onSearchStock,
  onSave,
}) {
  const typeOptions = [
    { label: '매수 (BUY)', value: 'BUY' },
    { label: '매도 (SELL)', value: 'SELL' },
  ]

  const dropdownAccounts = (accounts || []).map((acc) => ({
    label: `[${acc.acc_company_nm.substring(0, 2)}] ${acc.acc_nm}`,
    value: acc.acc_cd,
  }))

  const dialogFooter = (
    <div className="flex justify-content-end gap-2 pt-2">
      <Button
        label="취소"
        icon="pi pi-times"
        onClick={onHide}
        className="p-button-text p-button-secondary"
        disabled={isSubmitting}
      />
      <Button
        label={editingTxId ? '수정 완료' : '거래 등록'}
        icon="pi pi-check"
        onClick={onSave}
        className="p-button-primary font-bold"
        disabled={
          isSubmitting ||
          !txAccount ||
          !txCode ||
          !txName ||
          !txQuantity ||
          !txPrice
        }
        loading={isSubmitting}
      />
    </div>
  )

  return (
    <Dialog
      header={
        <div className="flex align-items-center gap-2">
          <i className="pi pi-file-edit text-primary text-xl"></i>
          <span className="font-bold text-xl">
            {editingTxId ? '📝 매매 거래 기록 수정' : '➕ 신규 매매 거래 등록'}
          </span>
        </div>
      }
      visible={visible}
      style={{ width: '450px' }}
      modal
      className="p-fluid"
      footer={dialogFooter}
      onHide={onHide}
    >
      <div className="field mb-4">
        <label className="font-bold mb-2 block">거래 구분</label>
        <SelectButton
          value={txType}
          options={typeOptions}
          onChange={(e) => setTxType(e.value || 'BUY')}
          disabled={isSubmitting}
        />
      </div>

      <div className="field mb-4">
        <label className="font-bold mb-2 block">대상 귀속 계좌</label>
        <Dropdown
          value={txAccount}
          options={dropdownAccounts}
          onChange={(e) => setTxAccount(e.value)}
          placeholder="거래를 반영할 계좌를 선택하세요"
          disabled={isSubmitting}
        />
      </div>

      <div className="field mb-4">
        <label className="font-bold mb-2 block">종목명 검색</label>
        <div className="p-inputgroup">
          <InputText
            value={txName}
            onChange={(e) => setTxName(e.target.value)}
            placeholder="예: 삼성전자 (입력 후 검색 클릭)"
            disabled={isSubmitting}
          />
          <Button
            icon="pi pi-search"
            className="p-button-primary font-bold"
            label="검색"
            onClick={onSearchStock}
            loading={isSearching}
            disabled={isSubmitting}
          />
        </div>
      </div>

      <div className="field mb-4">
        <label className="font-bold mb-2 block">확정 종목코드</label>
        <InputText
          value={txCode}
          onChange={(e) => setTxCode(e.target.value)}
          placeholder="검색 시 자동 입력 (수동 입력 가능)"
          disabled={isSubmitting}
        />
      </div>

      <div className="grid">
        <div className="col-6 field mb-4">
          <label className="font-bold mb-2 block">거래 수량 (주)</label>
          <InputNumber
            value={txQuantity}
            onValueChange={(e) => setTxQuantity(e.value)}
            placeholder="수량"
            min={1}
            disabled={isSubmitting}
          />
        </div>
        <div className="col-6 field mb-4">
          <label className="font-bold mb-2 block">거래 단가 (원)</label>
          <InputNumber
            value={txPrice}
            onValueChange={(e) => setTxPrice(e.value)}
            placeholder="단가"
            min={1}
            disabled={isSubmitting}
          />
        </div>
      </div>

      <div className="field mb-4">
        <label className="font-bold mb-2 block">세금 및 수수료 (원)</label>
        <InputNumber
          value={txTaxFee}
          onValueChange={(e) => setTxTaxFee(e.value || 0)}
          placeholder="미입력 시 0원"
          min={0}
          disabled={isSubmitting}
        />
      </div>

      <div className="field mb-2">
        <label className="font-bold mb-2 block">거래 일시</label>
        <Calendar
          value={txDate}
          onChange={(e) => setTxDate(e.value)}
          showTime
          hourFormat="24"
          dateFormat="yy-mm-dd"
          locale="ko"
          showIcon
          disabled={isSubmitting}
        />
      </div>
    </Dialog>
  )
}
