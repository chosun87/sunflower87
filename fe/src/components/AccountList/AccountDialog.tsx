import { Button, Dialog, InputText, Calendar } from '@/assets/ts/PrimeReact';
import { useEffect, useState } from 'react';
import { showConfirm, showError } from '@/assets/ts/dialogUtils';
import dayjs from 'dayjs';

interface AccountDialogProps {
  visible: boolean;
  onHide: () => void;
  editingAccount: any;
  isSubmitting: boolean;
  onSave: (payload: any) => void;
}

export default function AccountDialog({
  visible,
  onHide,
  editingAccount,
  isSubmitting,
  onSave,
}: AccountDialogProps) {
  const isEdit = !!editingAccount;

  const [accCd, setAccCd] = useState('');
  const [accNm, setAccNm] = useState('');
  const [accCompanyNm, setAccCompanyNm] = useState('');
  const [dtOpened, setDtOpened] = useState<Date | null>(null);

  useEffect(() => {
    if (visible) {
      if (isEdit && editingAccount) {
        setAccCd(editingAccount.acc_cd || '');
        setAccNm(editingAccount.acc_nm || '');
        setAccCompanyNm(editingAccount.acc_company_nm || '');
        setDtOpened(editingAccount.dt_opened ? new Date(editingAccount.dt_opened) : null);
      } else {
        setAccCd('');
        setAccNm('');
        setAccCompanyNm('');
        setDtOpened(null);
      }
    }
  }, [visible, isEdit, editingAccount]);

  const handleSubmit = () => {
    if (!accCd || !accNm || !accCompanyNm) {
      showError('모든 필수 항목을 입력해주세요.');
      return;
    }

    const payload = {
      acc_cd: accCd,
      acc_nm: accNm,
      acc_company_nm: accCompanyNm,
      dt_opened: dtOpened ? dayjs(dtOpened).format('YYYY-MM-DD') : undefined,
    };

    // User requirement: showConfirm before save
    showConfirm({
      message: isEdit ? '수정하시겠습니까?' : '등록하시겠습니까?',
      header: isEdit ? '계좌 수정 확인' : '계좌 등록 확인',
      accept: () => {
        onSave(payload);
      },
    });
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
        label={isEdit ? '수정 완료' : '계좌 등록'}
        icon="fa-solid fa-check"
        onClick={handleSubmit}
        className="p-button-primary font-bold"
        disabled={isSubmitting || !accCd || !accNm || !accCompanyNm}
        loading={isSubmitting}
      />
    </div>
  );

  return (
    <Dialog
      header={
        <div className="flex align-items-center gap-2">
          <i
            className={`fa-solid ${isEdit ? 'fa-pen-to-square' : 'fa-plus-circle'} text-primary text-xl`}
          ></i>
          <span className="font-bold text-xl">{isEdit ? '계좌 수정' : '새 계좌 등록'}</span>
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
        <label className="font-bold mb-2 block">
          계좌코드 (고유값) <span className="text-red-500">*</span>
        </label>
        <InputText
          value={accCd}
          onChange={(e) => setAccCd(e.target.value)}
          disabled={isEdit || isSubmitting}
          placeholder="예: NH-01"
        />
      </div>

      <div className="field mb-4">
        <label className="font-bold mb-2 block">
          계좌명 (별칭) <span className="text-red-500">*</span>
        </label>
        <InputText
          value={accNm}
          onChange={(e) => setAccNm(e.target.value)}
          disabled={isSubmitting}
          placeholder="예: NH투자증권 주식계좌"
        />
      </div>

      <div className="field mb-4">
        <label className="font-bold mb-2 block">
          금융사명 <span className="text-red-500">*</span>
        </label>
        <InputText
          value={accCompanyNm}
          onChange={(e) => setAccCompanyNm(e.target.value)}
          disabled={isSubmitting}
          placeholder="예: NH투자증권"
        />
      </div>

      <div className="field mb-2">
        <label className="font-bold mb-2 block">계좌 개설일</label>
        <Calendar
          value={dtOpened}
          onChange={(e) => setDtOpened(e.value as Date)}
          dateFormat="yy-mm-dd"
          mask="9999-99-99"
          locale="ko"
          showIcon
          disabled={isSubmitting}
          placeholder="개설일을 선택하세요"
        />
      </div>
    </Dialog>
  );
}
