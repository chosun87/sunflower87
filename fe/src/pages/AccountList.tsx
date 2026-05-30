import { useEffect, useState } from 'react';
import { BreadCrumb } from '@/assets/ts/PrimeReact';
import { showNotice, showError, showConfirm } from '@/assets/ts/dialogUtils';
import AccountListCmpt from '@/components/AccountList/AccountListCmpt';
import AccountDialog from '@/components/AccountList/AccountDialog';
import { getAccounts, createAccount, updateAccount, deleteAccount } from '@/api/accountApi';

const breadcrumbItems = [{ label: 'Home', url: '/' }, { label: '계좌 관리' }];

export default function AccountList() {
  const [accounts, setAccounts] = useState([]);
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [dialogVisible, setDialogVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchAccounts = async (incDel = includeDeleted) => {
    try {
      const res = await getAccounts(incDel);
      if (res.status === 'success') {
        setAccounts(res.data || []);
      }
    } catch (e: any) {
      console.error('Failed to load accounts:', e);
      showError(e.message || '계좌 목록을 불러오는데 실패했습니다.');
    }
  };

  useEffect(() => {
    fetchAccounts(includeDeleted);
  }, [includeDeleted]);

  const handleAddClick = () => {
    setEditingAccount(null);
    setDialogVisible(true);
  };

  const handleEditClick = (account: any) => {
    setEditingAccount(account);
    setDialogVisible(true);
  };

  const handleDeleteClick = (account: any) => {
    showConfirm({
      message: '정말로 이 계좌를 비활성화(삭제)하시겠습니까?\n계좌가 비활성화되어도 기존 거래 내역은 유지됩니다.',
      header: '계좌 삭제 확인',
      icon: 'fa-solid fa-exclamation-triangle',
      accept: async () => {
        try {
          const res = await deleteAccount(account.acc_cd);
          if (res.status === 'success') {
            showNotice({ header: '삭제 완료', message: '계좌가 비활성 처리되었습니다.' });
            fetchAccounts();
          }
        } catch (e: any) {
          showError(e.message || '삭제에 실패했습니다.');
        }
      },
    });
  };

  const handleSave = async (payload: any) => {
    setIsSubmitting(true);
    try {
      if (editingAccount) {
        await updateAccount(payload.acc_cd, {
          acc_nm: payload.acc_nm,
          acc_company_nm: payload.acc_company_nm,
          dt_opened: payload.dt_opened,
        });
        showNotice({ header: '수정 완료', message: '계좌 정보가 수정되었습니다.' });
      } else {
        await createAccount(payload);
        showNotice({ header: '등록 완료', message: '신규 계좌가 등록되었습니다.' });
      }
      setDialogVisible(false);
      fetchAccounts();
    } catch (e: any) {
      showError(e.message || '저장에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="page account-management">
      <div className="main-inner">
        <div className="page-header">
          <h2 className="page-title">계좌 관리</h2>
          <BreadCrumb className="breadcrumb" model={breadcrumbItems} />
        </div>
        <div className="page-content">
          <AccountListCmpt
            accounts={accounts}
            includeDeleted={includeDeleted}
            onIncludeDeletedChange={setIncludeDeleted}
            onAddClick={handleAddClick}
            onEditClick={handleEditClick}
            onDeleteClick={handleDeleteClick}
          />
        </div>
      </div>

      <AccountDialog
        visible={dialogVisible}
        onHide={() => setDialogVisible(false)}
        editingAccount={editingAccount}
        isSubmitting={isSubmitting}
        onSave={handleSave}
      />
    </main>
  );
}
