import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Card, TabView, TabPanel, addLocale } from '@/assets/js/PrimeReact'
import { PrimeReact_locale } from '@/assets/js/PrimeReact'
import { showNotice, showError } from '@/assets/js/dialogUtils'

// 신규 신설된 5대 핵심 서브 컴포넌트 임포트 레이어
import AssetSummaryCard from '@/components/dashboard/AssetSummaryCard'
import AIRecommendationSection from '@/components/dashboard/AIRecommendationSection'
import AssetDetailTab from '@/components/dashboard/AssetDetailTab'
import TransactionHistoryTab from '@/components/dashboard/TransactionHistoryTab'
import TransactionDialog from '@/components/dashboard/TransactionDialog'

// PrimeReact Calendar 한국어(ko) 로컬라이징 사전 등록
addLocale('ko', PrimeReact_locale.ko.Calendar)

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [selectedAccount, setSelectedAccount] = useState(null) // 선택 계좌의 acc_cd 스트링 홀딩
  const [transactions, setTransactions] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const navigate = useNavigate()
  const { isSignedIn, isInitialized } = useAuth()

  // 거래 등록 및 수정 다이얼로그 상태 및 타겟 거래 객체
  const [displayDialog, setDisplayDialog] = useState(false)
  const [editingTx, setEditingTx] = useState(null) // 수정 모드 시 거래 객체 전체 추적 (신규는 null)
  const [lastSearchedStock, setLastSearchedStock] = useState({
    code: '',
    name: '',
  }) // 신규 연속 등록 시 종목 보존 캐시

  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (isInitialized && !isSignedIn) {
      navigate('/login')
    }
  }, [isInitialized, isSignedIn, navigate])

  // 실시간 자산 및 보유 주식 불러오기 (데이터 일관성 보장 바인딩)
  const fetchAccountData = () => {
    fetch(`${import.meta.env.VITE_API_URL}/api/accounts`)
      .then((res) => res.json())
      .then((resData) => {
        if (resData.status === 'success') {
          // 데이터 로드 시 평가금액(eval_amount) 계산하여 정밀 정렬 지원 바인딩
          const enrichedAccounts = (resData.accounts || []).map((acc) => ({
            ...acc,
            stocks: (acc.stocks || []).map((stock) => ({
              ...stock,
              eval_amount: stock.quantity * stock.current_price,
            })),
          }))
          const enrichedData = {
            ...resData,
            accounts: enrichedAccounts,
          }
          setData(enrichedData)
          // 계좌가 있고, 기존 선택 계좌가 유지되는 경우 찾아서 재매핑하여 무중단 상태 동기화 제공
          if (enrichedAccounts && enrichedAccounts.length > 0) {
            setSelectedAccount((prev) => {
              if (prev && typeof prev === 'string') {
                const found = enrichedAccounts.find((a) => a.acc_cd === prev)
                if (found) return found.acc_cd
              }
              if (prev && typeof prev === 'object' && prev.acc_cd) {
                const found = enrichedAccounts.find(
                  (a) => a.acc_cd === prev.acc_cd,
                )
                if (found) return found.acc_cd
              }
              return enrichedAccounts[0].acc_cd
            })
          }
        }
      })
      .catch((err) => console.error('데이터 로드 실패:', err))
  }

  // SQLite 거래 히스토리 내역 불러오기
  const loadTransactions = () => {
    fetch(`${import.meta.env.VITE_API_URL}/api/transactions`)
      .then((res) => res.json())
      .then((resData) => {
        if (resData.status === 'success') {
          setTransactions(resData.data)
        }
      })
      .catch((err) => console.error('거래 내역 로드 실패:', err))
  }

  useEffect(() => {
    fetchAccountData()
    loadTransactions()

    // 백엔드 API로부터 오늘의 AI 추천 종목 데이터 바인딩
    fetch(`${import.meta.env.VITE_API_URL}/api/recommendations`)
      .then((res) => res.json())
      .then((resData) => {
        if (resData.status === 'success') {
          setRecommendations(resData.data)
        }
      })
      .catch((err) => console.error('추천 데이터 로드 실패:', err))
  }, [])

  if (!data) {
    return (
      <div className="flex align-items-center justify-content-center h-screen">
        <i
          className="pi pi-spin pi-spinner mr-2"
          style={{ fontSize: '2rem' }}
        ></i>
        <span className="text-xl font-bold">
          [sunflower87] 데이터를 불러오는 중...
        </span>
      </div>
    )
  }

  // 종목명 기반 종목코드 검색 연동 API 헬퍼 및 보존 캐시 업데이트
  const handleSearchStock = (keyword) => {
    return fetch(
      `${import.meta.env.VITE_API_URL}/api/stocks/search?keyword=${encodeURIComponent(keyword)}`,
    )
      .then((res) => {
        if (!res.ok) throw new Error('서버 통신 실패')
        return res.json()
      })
      .then((resData) => {
        if (resData.status === 'success' && resData.results.length > 0) {
          const match = resData.results[0]
          // 신규 거래 연속 등록 편의를 위해 마지막 성공 검색 종목 캐싱
          setLastSearchedStock({ code: match.code, name: match.name })
          return match
        } else {
          throw new Error(`'${keyword}'에 매칭되는 종목을 찾지 못했습니다.`)
        }
      })
  }

  // 매수/매도 등록 및 수정 통합 처리 (PUT/POST 분기)
  const handleSaveTransaction = (payload) => {
    setIsSubmitting(true)

    const url = editingTx
      ? `${import.meta.env.VITE_API_URL}/api/transactions/${editingTx.id}`
      : `${import.meta.env.VITE_API_URL}/api/transactions/add`
    const method = editingTx ? 'PUT' : 'POST'

    fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
      .then((res) => {
        if (!res.ok) {
          return res.json().then((errData) => {
            throw new Error(errData.detail || '거래 처리에 실패했습니다.')
          })
        }
        return res.json()
      })
      .then((resData) => {
        if (resData.status === 'success') {
          setDisplayDialog(false)
          setEditingTx(null) // 편집 상태 클리어

          // 성공 알림 및 리액티브 자산 실시간 동기화
          showNotice({
            header: editingTx ? '수정 완료' : '등록 완료',
            icon: 'pi pi-check-circle',
            message:
              resData.message || '매매 내역이 정상적으로 처리되었습니다.',
          })

          fetchAccountData()
          loadTransactions()
        }
      })
      .catch((err) => {
        console.error('거래 추가/수정 중 에러:', err)
        showError(err.message || '서버 통신 실패')
      })
      .finally(() => {
        setIsSubmitting(false)
      })
  }

  // 거래 내역 편집 활성화 핸들러
  const handleEditTransaction = (rowData) => {
    setEditingTx(rowData)
    setDisplayDialog(true)
  }

  // 거래 내역 삭제 및 역산 핸들러
  const handleDeleteTransaction = (rowData) => {
    const confirmMessage = `'${rowData.name}' 매매 거래 기록을 삭제하시겠습니까? 해당 거래에 따른 계좌의 주식 잔고 및 자산이 역산(Rollback)됩니다.`

    // confirmDialog 대신 브라우저 기본 confirm을 활용하여 결합도 최소화
    if (window.confirm(confirmMessage)) {
      fetch(`${import.meta.env.VITE_API_URL}/api/transactions/${rowData.id}`, {
        method: 'DELETE',
      })
        .then((res) => {
          if (!res.ok) {
            return res.json().then((errData) => {
              throw new Error(errData.detail || '삭제 처리에 실패했습니다.')
            })
          }
          return res.json()
        })
        .then((resData) => {
          if (resData.status === 'success') {
            showNotice({
              header: '삭제 완료',
              icon: 'pi pi-check-circle',
              message:
                '매매 거래 내역 삭제 및 자산 역산 처리가 완료되었습니다.',
            })
            fetchAccountData()
            loadTransactions()
          }
        })
        .catch((err) => {
          console.error('거래 삭제 에러:', err)
          showError(err.message || '서버 통신 실패')
        })
    }
  }

  return (
    <div className="p-4 md:p-6 lg:p-8">
      <div className="flex align-items-center justify-content-between mb-6">
        <h1 className="text-4xl font-bold text-900 m-0">
          🌻 sunflower87 Dashboard
        </h1>
        <span className="text-600">Decision Maker: SUN</span>
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
          <TabPanel
            header="보유 자산 상세"
            leftIcon="pi pi-wallet mr-2 text-primary"
          >
            <AssetDetailTab accounts={data.accounts} />
          </TabPanel>

          {/* [탭 2: 매매 내역 히스토리] */}
          <TabPanel
            header="매매 내역 히스토리"
            leftIcon="pi pi-history mr-2 text-primary"
          >
            <TransactionHistoryTab
              transactions={transactions}
              onAddClick={() => {
                setEditingTx(null) // 신규 모드
                setDisplayDialog(true)
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
          setDisplayDialog(false)
          setEditingTx(null)
        }}
        editingTx={editingTx}
        cachedStock={lastSearchedStock}
        accounts={data.accounts}
        isSubmitting={isSubmitting}
        onSearchStock={handleSearchStock}
        onSave={handleSaveTransaction}
      />
    </div>
  )
}
