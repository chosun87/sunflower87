import { BreadCrumb } from '@/assets/ts/PrimeReact';
import { useEffect, useState } from 'react';
import { get, post, put, del } from '@/api/index';
import TransactionCashCmpt from '@/components/TransactionCash/TransactionCashCmpt';
import TrCashDialog from '@/components/TransactionCash/TrCashDialog';
import { showNotice, showError, showConfirm } from '@/assets/ts/dialogUtils';

const breadcrumbItems = [{ label: 'Home', url: '/' }, { label: '계좌 입출금 내역' }];

export default function TransactionCash() {
  const [transactions, setTransactions] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [currentFilters, setCurrentFilters] = useState({});

  const [dialogVisible, setDialogVisible] = useState(false);
  const [editingTx, setEditingTx] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchTransactions = async (filters?: any) => {
    const activeFilters = filters !== undefined ? filters : currentFilters;
    if (filters !== undefined) {
      setCurrentFilters(filters);
    }

    try {
      const res = await get('/api/transactions_cash', activeFilters);
      if (res.status === 'success') {
        const mapped = (res.data || []).map((tx: any) => ({
          ...tx,
          tx_id: tx.id,
          description: tx.description || '',
        }));
        setTransactions(mapped as never[]);
      }
    } catch (e) {
      console.error('Failed to load cash transactions:', e);
    }
  };

  const fetchAccounts = async () => {
    try {
      const res = await get('/api/stocks/portfolio'); // TransactionStock과 동일한 패턴
      if (res.status === 'success' && res.data) {
        setAccounts(res.data.accounts || []);
      }
    } catch (e) {
      console.error('Failed to load accounts:', e);
    }
  };

  useEffect(() => {
    fetchAccounts();
    fetchTransactions();
  }, []);

  const handleAddClick = () => {
    setEditingTx(null);
    setDialogVisible(true);
  };

  const handleEditClick = (tx: any) => {
    setEditingTx(tx);
    setDialogVisible(true);
  };

  const handleDeleteClick = (tx: any) => {
    showConfirm({
      message: '정말로 이 입출금 내역을 삭제하시겠습니까?\n삭제 시 계좌 예수금이 재정산됩니다.',
      header: '삭제 확인',
      icon: 'fa-solid fa-exclamation-triangle',
      accept: async () => {
        try {
          const res = await del(`/api/transactions_cash/${tx.tx_id}`);
          if (res.status === 'success') {
            showNotice({ header: '삭제 완료', message: '성공적으로 삭제되었습니다.' });
            fetchTransactions();
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
      const apiPayload = {
        acc_cd: payload.acc_cd,
        cash_type: payload.cash_type,
        amount: payload.amount,
        description: payload.description || '',
        dt_cash: payload.dt_cash,
      };

      if (editingTx) {
        await put(`/api/transactions_cash/${(editingTx as any).tx_id}`, apiPayload);
        showNotice({ header: '수정 완료', message: '입출금 내역이 수정되었습니다.' });
      } else {
        await post('/api/transactions_cash', apiPayload); // API 문서에 따라 POST /api/transactions_cash
        showNotice({ header: '등록 완료', message: '신규 입출금 내역이 등록되었습니다.' });
      }
      setDialogVisible(false);
      fetchTransactions();
    } catch (e: any) {
      showError(e.message || '저장에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="page transaction-cash">
      <div className="main-inner">
        <div className="page-header">
          <h2 className="page-title">계좌 입출금 내역</h2>
          <BreadCrumb className="breadcrumb" model={breadcrumbItems} />
        </div>
        <div className="page-content">
          <TransactionCashCmpt
            transactions={transactions}
            accounts={accounts}
            onLoadTransactions={fetchTransactions}
            onAddClick={handleAddClick}
            onEditClick={handleEditClick}
            onDeleteClick={handleDeleteClick}
          />
        </div>
      </div>

      <TrCashDialog
        visible={dialogVisible}
        onHide={() => setDialogVisible(false)}
        editingTx={editingTx}
        accounts={accounts}
        isSubmitting={isSubmitting}
        onSave={handleSave}
      />
    </main>
  );
}
