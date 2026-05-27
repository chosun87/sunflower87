import { BreadCrumb } from '@/assets/ts/PrimeReact';
import { useEffect, useState } from 'react';
import { get, post, put, del, searchStock, getStockNameByCode } from '@/api/index';
import TransactionStockCmpt from '@/components/TransactionStock/TransactionStockCmpt';
import TrStockDialog from '@/components/TransactionStock/TrStockDialog';
import { showNotice, showError, showConfirm } from '@/assets/ts/dialogUtils';

const breadcrumbItems = [{ label: 'Home', url: '/' }, { label: '주식 매매 내역' }];

export default function TransactionStock() {
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
      const res = await get('/api/transactions', activeFilters);
      if (res.status === 'success') {
        const mapped = (res.data || []).map((tx: any) => ({
          ...tx,
          tx_id: tx.id,
        }));
        setTransactions(mapped as never[]);
      }
    } catch (e) {
      console.error('Failed to load transactions:', e);
    }
  };

  const fetchAccounts = async () => {
    try {
      const res = await get('/api/stocks/portfolio');
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
      message: '정말로 이 매매 내역을 삭제하시겠습니까?',
      header: '삭제 확인',
      icon: 'fa-solid fa-exclamation-triangle',
      accept: async () => {
        try {
          const res = await del(`/api/transactions/${tx.tx_id}`);
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
        trade_type: payload.trade_type,
        stock_code: payload.stock_code,
        quantity: payload.quantity,
        price: payload.price,
        tax_fee: payload.tax_fee,
        dt_trade: payload.dt_trade,
      };

      if (editingTx) {
        await put(`/api/transactions/${(editingTx as any).tx_id}`, apiPayload);
        showNotice({ header: '수정 완료', message: '매매 내역이 수정되었습니다.' });
      } else {
        await post('/api/transactions/add', apiPayload);
        showNotice({ header: '등록 완료', message: '신규 매매 내역이 등록되었습니다.' });
      }
      setDialogVisible(false);
      fetchTransactions();
    } catch (e: any) {
      showError(e.message || '저장에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 모달 팝업의 검색 API 연결
  const handleSearchStock = async (keyword: string) => {
    const res = await searchStock(keyword);
    if (res.status === 'success' && res.data && res.data.length > 0) {
      return res.data[0]; // 첫 번째 매칭 결과 반환
    }
    throw new Error('검색 결과가 없습니다.');
  };

  const handleLookupCode = async (code: string) => {
    const res = await getStockNameByCode(code);
    if (res.status === 'success' && res.data) {
      return res.data;
    }
    throw new Error('조회 결과가 없습니다.');
  };

  return (
    <main className="page transaction-stock">
      <div className="main-inner">
        <div className="page-header">
          <h2 className="page-title">주식 매매 내역</h2>
          <BreadCrumb className="breadcrumb" model={breadcrumbItems} />
        </div>
        <div className="page-content">
          <TransactionStockCmpt
            transactions={transactions}
            accounts={accounts}
            onLoadTransactions={fetchTransactions}
            onAddClick={handleAddClick}
            onEditClick={handleEditClick}
            onDeleteClick={handleDeleteClick}
          />
        </div>
      </div>

      <TrStockDialog
        visible={dialogVisible}
        onHide={() => setDialogVisible(false)}
        editingTx={editingTx}
        cachedStock={null}
        accounts={accounts}
        isSubmitting={isSubmitting}
        onSearchStock={handleSearchStock}
        onLookupCode={handleLookupCode}
        onSave={handleSave}
      />
    </main>
  );
}
