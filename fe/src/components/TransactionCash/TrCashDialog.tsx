import { useState, useEffect } from 'react';
import { Dialog, Button, Dropdown, InputText, InputNumber, Calendar } from '@/assets/ts/PrimeReact';
import dayjs from 'dayjs';
import { showNotice, showError } from '@/assets/ts/dialogUtils';
import { CASH_TYPE_OPTIONS } from '@/assets/ts/constants';

export default function TrCashDialog({
  visible,
  onHide,
  editingTx, // 수정 시 대상 거래 원본 객체 (신규 시 null)
  accounts,
  isSubmitting,
  onSave, // (payload) => Promise<void>
}) {
  // 내부 폼 상태 관리
  // CASH_TYPE_OPTIONS의 기본값은 보통 'DEPOSIT'이므로 이를 디폴트로 설정
  const [txType, setTxType] = useState(editingTx?.cash_type || 'DEPOSIT');
  const [txAccount, setTxAccount] = useState(
    editingTx?.acc_cd || (accounts && accounts.length > 0 ? accounts[0].acc_cd : '')
  );
  const [txAmount, setTxAmount] = useState(editingTx?.amount || null);
  const [txDesc, setTxDesc] = useState(editingTx?.description || '');
  const [txDate, setTxDate] = useState(
    editingTx?.dt_cash ? new Date(editingTx.dt_cash) : new Date()
  );

  useEffect(() => {
    if (visible) {
      setTxType(editingTx?.cash_type || 'DEPOSIT');
      setTxAccount(
        editingTx?.acc_cd || (accounts && accounts.length > 0 ? accounts[0].acc_cd : '')
      );
      setTxAmount(editingTx?.amount || null);
      setTxDesc(editingTx?.description || '');
      setTxDate(editingTx?.dt_cash ? new Date(editingTx.dt_cash) : new Date());
    }
  }, [visible, editingTx, accounts]);

  const dropdownAccounts = (accounts || []).map((acc: any) => ({
    label: `[${acc.acc_company_nm?.substring(0, 2) || ''}] ${acc.acc_nm}`,
    value: acc.acc_cd,
  }));

  const handleSave = () => {
    if (!txAccount || !txType || !txAmount) {
      showError('계좌, 구분, 금액은 필수 입력 항목입니다.');
      return;
    }

    const targetDateStr = txDate ? dayjs(txDate).format('YYYY-MM-DD') : '';

    const payload = {
      cash_type: txType,
      amount: Math.abs(Number(txAmount) || 0), // 금액은 절대값 처리 (API나 서비스에서 부호 처리함)
      description: txDesc,
      acc_cd: txAccount,
      dt_cash: targetDateStr,
    };

    onSave(payload);
  };

  const dialogFooter = (
    <div className="flex justify-content-end gap-2 pt-2">
      <Button
        label="취소"
        icon="fa-solid fa-times"
        onClick={onHide}
        className="p-button-text p-button-secondary"
        disabled={isSubmitting}
      />
      <Button
        label={editingTx ? '수정 완료' : '내역 등록'}
        icon="fa-solid fa-check"
        onClick={handleSave}
        className="p-button-primary font-bold"
        disabled={isSubmitting || !txAccount || !txType || !txAmount}
        loading={isSubmitting}
      />
    </div>
  );

  return (
    <Dialog
      header={
        <div className="flex align-items-center gap-2">
          <i
            className={`fa-solid ${editingTx ? 'fa-pen-to-square' : 'fa-plus-circle'} text-primary text-xl`}
          ></i>
          <span className="font-bold text-xl">
            {editingTx ? '입출금 내역 수정' : '신규 입출금 등록'}
          </span>
        </div>
      }
      visible={visible}
      style={{ width: '400px' }}
      modal
      className="p-fluid"
      footer={dialogFooter}
      onHide={onHide}
    >
      <div className="field mb-4">
        <label className="font-bold mb-2 block">거래 구분 <span className="text-red-500">*</span></label>
        <Dropdown
          value={txType}
          options={CASH_TYPE_OPTIONS}
          onChange={(e) => setTxType(e.value || 'DEPOSIT')}
          placeholder="구분을 선택하세요"
          disabled={isSubmitting}
        />
      </div>

      <div className="field mb-4">
        <label className="font-bold mb-2 block">대상 귀속 계좌 <span className="text-red-500">*</span></label>
        <Dropdown
          value={txAccount}
          options={dropdownAccounts}
          onChange={(e) => setTxAccount(e.value)}
          placeholder="계좌를 선택하세요"
          disabled={isSubmitting}
        />
      </div>

      <div className="field mb-4">
        <label className="font-bold mb-2 block">금액 (원) <span className="text-red-500">*</span></label>
        <InputNumber
          value={txAmount}
          onValueChange={(e) => setTxAmount(e.value)}
          placeholder="금액을 입력하세요"
          min={1}
          disabled={isSubmitting}
        />
      </div>

      <div className="field mb-4">
        <label className="font-bold mb-2 block">적요 (선택)</label>
        <InputText
          value={txDesc}
          onChange={(e) => setTxDesc(e.target.value)}
          placeholder="메모나 적요를 입력하세요 (예: 월급, 배당금 입금)"
          disabled={isSubmitting}
          maxLength={100}
        />
      </div>

      <div className="field mb-2">
        <label className="font-bold mb-2 block">거래일 <span className="text-red-500">*</span></label>
        <Calendar
          value={txDate}
          onChange={(e) => setTxDate(e.value)}
          dateFormat="yy-mm-dd"
          mask="9999-99-99"
          locale="ko"
          showIcon
          disabled={isSubmitting}
        />
      </div>
    </Dialog>
  );
}
