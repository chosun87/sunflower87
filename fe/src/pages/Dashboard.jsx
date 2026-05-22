import { useState, useEffect, useCallback, useRef, lazy, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Card, TabView, TabPanel, addLocale, Button } from '@/assets/js/PrimeReact';
import { PrimeReact_locale } from '@/assets/js/PrimeReact';
import { showNotice, showError } from '@/assets/js/dialogUtils';
import { get, post, put, del, getRecommendations, searchStock, getStockNameByCode } from '@/api';

// 신규 신설된 5대 핵심 서브 컴포넌트 임포트 레이어
const AssetSummaryCard = lazy(() => import('@/components/dashboard/AssetSummaryCard'));
const AIRecommendationSection = lazy(
  () => import('@/components/dashboard/AIRecommendationSection')
);
const AssetDetailTab = lazy(() => import('@/components/dashboard/AssetDetailTab'));
const TransactionHistoryTab = lazy(() => import('@/components/dashboard/TransactionHistoryTab'));
const TransactionDialog = lazy(() => import('@/components/dashboard/TransactionDialog'));

// PrimeReact Calendar 한국어(ko) 로컬라이징 사전 등록
addLocale('ko', PrimeReact_locale.ko.Calendar);

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null); // 선택 계좌의 acc_cd 스트링 홀딩
  const [transactions, setTransactions] = useState([]);
  const [transactionFilters, setTransactionFilters] = useState({});
  const transactionFiltersRef = useRef(transactionFilters);
  const [recommendations, setRecommendations] = useState([]);
  const navigate = useNavigate();
  const { isSignedIn, isInitialized } = useAuth();

  // 거래 등록 및 수정 다이얼로그 상태 및 타겟 거래 객체
  const [displayDialog, setDisplayDialog] = useState(false);
  const [editingTx, setEditingTx] = useState(null); // 수정 모드 시 거래 객체 전체 추적 (신규는 null)
  const [lastSearchedStock, setLastSearchedStock] = useState({
    code: '',
    name: '',
  }); // 신규 연속 등록 시 종목 보존 종목 캐시
  const [stockSearchHistory, setStockSearchHistory] = useState(() => {
    try {
      const stored = localStorage.getItem('stockSearchHistory');
      return stored ? JSON.parse(stored) : [];
    } catch (err) {
      console.warn('Failed to load stock search history', err);
      return [];
    }
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  useEffect(() => {
    transactionFiltersRef.current = transactionFilters;
  }, [transactionFilters]);

  useEffect(() => {
    if (isInitialized && !isSignedIn) {
      navigate('/login');
    }
  }, [isInitialized, isSignedIn, navigate]);

  // 실시간 자산 및 보유 주식 불러오기 (데이터 일관성 보장 바인딩)
  const fetchAccountData = useCallback(async () => {
    try {
      const resData = await get('/api/accounts');
      if (resData?.status !== 'success') {
        throw new Error(resData?.message || '계좌 정보를 불러오지 못했습니다.');
      }

      const enrichedAccounts = (resData.accounts || []).map((acc) => ({
        ...acc,
        stocks: (acc.stocks || []).map((stock) => ({
          ...stock,
          eval_amount: (stock.quantity || 0) * (stock.current_price || 0),
        })),
      }));

      setData({ ...resData, accounts: enrichedAccounts });

      if (enrichedAccounts.length > 0) {
        setSelectedAccount((prev) => {
          if (typeof prev === 'string') {
            const found = enrichedAccounts.find((a) => a.acc_cd === prev);
            if (found) return found.acc_cd;
          }
          if (prev && typeof prev === 'object' && prev.acc_cd) {
            const found = enrichedAccounts.find((a) => a.acc_cd === prev.acc_cd);
            if (found) return found.acc_cd;
          }
          return enrichedAccounts[0].acc_cd;
        });
      }
    } catch (err) {
      console.error('데이터 로드 실패:', err);
      showError(err.message || '계좌 정보를 불러오는 중 오류가 발생했습니다.');
    }
  }, []);

  // SQLite 거래 히스토리 내역 불러오기 (검색 필터 지원)
  const loadTransactions = useCallback(async (filters = null) => {
    const activeFilters = filters ?? transactionFiltersRef.current;
    setTransactionFilters(activeFilters);

    try {
      const resData = await get('/api/transactions', activeFilters);
      if (resData?.status !== 'success') {
        throw new Error(resData?.message || '거래 내역을 불러오지 못했습니다.');
      }
      setTransactions(resData.data || []);
    } catch (err) {
      console.error('거래 내역 로드 실패:', err);
      showError(err.message || '거래 내역 로드 중 오류가 발생했습니다.');
    }
  }, []);

  useEffect(() => {
    const initializePage = async () => {
      await fetchAccountData();
      await loadTransactions();

      // 백엔드 API로부터 오늘의 AI 추천 종목 데이터 바인딩
      try {
        const resData = await getRecommendations();
        if (resData?.status === 'success') {
          setRecommendations(resData.data || []);
        }
      } catch (err) {
        console.error('추천 데이터 로드 실패:', err);
      }
    };

    initializePage();
  }, [fetchAccountData, loadTransactions]);

  if (!data) {
    return (
      <div className="flex align-items-center justify-content-center h-screen">
        <i className="pi pi-spin pi-spinner mr-2" style={{ fontSize: '2rem' }}></i>
        <span className="text-xl font-bold">[sunflower87] 데이터를 불러오는 중...</span>
      </div>
    );
  }

  // 종목명 기반 종목코드 검색 연동 API 헬퍼 및 보존 캐시 업데이트
  const handleSearchStock = async (keyword) => {
    const searchTerm = keyword.trim();
    if (!searchTerm) {
      throw new Error('검색할 종목명을 먼저 입력해주세요.');
    }

    try {
      const resData = await searchStock(searchTerm);
      if (resData.status === 'success' && resData.results.length > 0) {
        const match = resData.results[0];
        setLastSearchedStock({ code: match.code, name: match.name });
        setStockSearchHistory((prev) => {
          const updated = [searchTerm, ...prev.filter((item) => item !== searchTerm)].slice(0, 5);
          try {
            localStorage.setItem('stockSearchHistory', JSON.stringify(updated));
          } catch (err) {
            console.warn('Failed to save stock search history', err);
          }
          return updated;
        });
        return match;
      }

      if (/^\d{6}$/.test(searchTerm)) {
        const fallbackData = await getStockNameByCode(searchTerm);
        if (fallbackData.status === 'success') {
          const match = { code: fallbackData.code, name: fallbackData.name };
          setLastSearchedStock(match);
          return match;
        }
      }

      throw new Error(`'${keyword}'에 매칭되는 종목을 찾지 못했습니다.`);
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : `매칭되는 종목을 찾지 못했습니다.`, {
        cause: err,
      });
    }
  };

  const handleLookupStockCode = async (code) => {
    const stockCode = String(code || '').trim();
    if (!/^\d{6}$/.test(stockCode)) {
      throw new Error('유효한 6자리 종목 코드를 입력해주세요.');
    }

    try {
      const resData = await getStockNameByCode(stockCode);
      if (resData.status === 'success') {
        const match = { code: resData.code, name: resData.name };
        setLastSearchedStock(match);
        return match;
      }
      throw new Error(resData.message || '종목명을 찾을 수 없습니다.');
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '종목명 조회에 실패했습니다.', {
        cause: err,
      });
    }
  };

  // 매수/매도 등록 및 수정 통합 처리 (PUT/POST 분기)
  const handleSaveTransaction = async (payload) => {
    setIsSubmitting(true);

    try {
      const request = editingTx
        ? put(`/api/transactions/${editingTx.id}`, payload)
        : post('/api/transactions/add', payload);

      const resData = await request;
      if (resData.status !== 'success') {
        throw new Error(resData.message || '거래 처리에 실패했습니다.');
      }

      setDisplayDialog(false);
      setEditingTx(null);
      showNotice({
        header: editingTx ? '수정 완료' : '등록 완료',
        icon: 'pi pi-check-circle',
        message: resData.message || '매매 내역이 정상적으로 처리되었습니다.',
      });

      await fetchAccountData();
      await loadTransactions();
    } catch (err) {
      console.error('거래 추가/수정 중 에러:', err);
      showError(err.message || '서버 통신 실패');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 거래 내역 편집 활성화 핸들러
  const handleEditTransaction = (rowData) => {
    setEditingTx(rowData);
    setDisplayDialog(true);
  };

  // 거래 내역 삭제 및 역산 핸들러
  const handleDeleteTransaction = (rowData) => {
    const confirmMessage = `'${rowData.name}' 매매 거래 기록을 삭제하시겠습니까? 해당 거래에 따른 계좌의 주식 잔고 및 자산이 역산(Rollback)됩니다.`;

    // confirmDialog 대신 브라우저 기본 confirm을 활용하여 결합도 최소화
    if (window.confirm(confirmMessage)) {
      const deleteTransaction = async () => {
        try {
          const resData = await del(`/api/transactions/${rowData.id}`);
          if (resData.status !== 'success') {
            throw new Error(resData.message || '삭제 처리에 실패했습니다.');
          }
          showNotice({
            header: '삭제 완료',
            icon: 'pi pi-check-circle',
            message: '매매 거래 내역 삭제 및 자산 역산 처리가 완료되었습니다.',
          });
          await fetchAccountData();
          await loadTransactions();
        } catch (err) {
          console.error('거래 삭제 에러:', err);
          showError(err.message || '서버 통신 실패');
        }
      };
      deleteTransaction();
    }
  };

  // 온디맨드 수동 동기화(On-Demand Sync) 핸들러
  const handleSyncMaster = async () => {
    setIsSyncing(true);
    try {
      const resData = await post('/api/stocks/sync-master');
      if (resData.status !== 'success') {
        throw new Error(resData.message || '동기화 처리에 실패했습니다.');
      }
      showNotice({
        header: '동기화 완료',
        icon: 'pi pi-check-circle',
        message: '종목 마스터 데이터가 최신 상태로 동기화되었습니다.',
      });
    } catch (err) {
      console.error('동기화 중 오류:', err);
      showError(err.message || '마스터 동기화 중 오류가 발생했습니다.');
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <Suspense
      fallback={
        <div className="p-4 text-center">
          <i className="pi pi-spin pi-spinner mr-2" />
          로딩 중...
        </div>
      }
    >
      <div className="p-4 md:p-6 lg:p-8">
        <div className="flex align-items-center justify-content-between mb-6">
          <h1 className="text-4xl font-bold text-900 m-0">🌻 sunflower87 Dashboard</h1>
          <div className="flex align-items-center gap-3">
            <Button
              label="종목 최신화"
              icon="pi pi-refresh"
              className="p-button-outlined p-button-secondary p-button-sm"
              loading={isSyncing}
              onClick={handleSyncMaster}
            />
            <span className="text-600 hidden md:inline">Decision Maker: SUN</span>
          </div>
        </div>

        {/* 상단 총자산 요약 및 계좌 선택 컴포넌트 */}
        <AssetSummaryCard
          totalAsset={data.total_asset}
          accounts={data.accounts}
          selectedAccount={selectedAccount}
          onAccountChange={setSelectedAccount}
        />

        {/* 오늘의 AI 추천 종목 섹션 컴포넌트 */}
        <AIRecommendationSection recommendations={recommendations} />

        {/* 보유 자산 및 매매 거래 내역 탭 구조화 (TabView) */}
        <Card className="shadow-4 border-round mt-6">
          <TabView>
            {/* [탭 1: 보유 자산 상세] */}
            <TabPanel header="보유 자산 상세" leftIcon="pi pi-wallet mr-2 text-primary">
              <AssetDetailTab accounts={data.accounts} />
            </TabPanel>

            {/* [탭 2: 매매 내역 히스토리] */}
            <TabPanel header="매매 내역 히스토리" leftIcon="pi pi-history mr-2 text-primary">
              <TransactionHistoryTab
                transactions={transactions}
                accounts={data.accounts}
                onLoadTransactions={loadTransactions}
                onAddClick={() => {
                  setEditingTx(null); // 신규 모드
                  setDisplayDialog(true);
                }}
                onEditClick={handleEditTransaction}
                onDeleteClick={handleDeleteTransaction}
              />
            </TabPanel>
          </TabView>
        </Card>

        {/* 매매 등록 및 수정 통합 모달 다이얼로그 */}
        <TransactionDialog
          key={editingTx ? `edit-${editingTx.id}` : 'new'}
          visible={displayDialog}
          onHide={() => {
            setDisplayDialog(false);
            setEditingTx(null);
          }}
          editingTx={editingTx}
          cachedStock={lastSearchedStock}
          accounts={data.accounts}
          isSubmitting={isSubmitting}
          onSearchStock={handleSearchStock}
          onLookupCode={handleLookupStockCode}
          searchHistory={stockSearchHistory}
          onSave={handleSaveTransaction}
        />
      </div>
    </Suspense>
  );
}
