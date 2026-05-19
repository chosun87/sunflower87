import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import '@/assets/css/earchfe.css'
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

  // 거래 등록 및 수정 모달 상태 관리
  const [displayDialog, setDisplayDialog] = useState(false)
  const [editingTxId, setEditingTxId] = useState(null) // 수정 모드 시 거래 ID 추적
  const [txType, setTxType] = useState('BUY') // BUY 또는 SELL
  const [txAccount, setTxAccount] = useState('미래-종합') // 대상 귀속 계좌
  const [txCode, setTxCode] = useState('')
  const [txName, setTxName] = useState('')
  const [txQuantity, setTxQuantity] = useState(null)
  const [txPrice, setTxPrice] = useState(null)
  const [txTaxFee, setTxTaxFee] = useState(0)
  const [txDate, setTxDate] = useState(new Date())

  const [isSearching, setIsSearching] = useState(false)
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

  // 종목명 기반 종목코드 자동 검색 API 연동
  const handleSearchStock = () => {
    const keyword = txName.trim()
    if (!keyword) {
      showError('검색할 종목명을 먼저 입력해주세요.')
      return
    }

    setIsSearching(true)
    fetch(
      `${import.meta.env.VITE_API_URL}/api/stocks/search?keyword=${encodeURIComponent(keyword)}`,
    )
      .then((res) => res.json())
      .then((resData) => {
        if (resData.status === 'success' && resData.results.length > 0) {
          const match = resData.results[0]
          setTxCode(match.code)
          setTxName(match.name)
          showNotice({
            header: '검색 완료',
            icon: 'pi pi-check-circle',
            message: `종목 '${match.name}' (${match.code})의 정보가 성공적으로 조회되었습니다.`,
            acceptClassName: 'p-button-success',
          })
        } else {
          showError(`'${keyword}'에 매칭되는 종목을 찾지 못했습니다.`)
        }
      })
      .catch((err) => {
        console.error('종목 검색 중 오류 발생:', err)
        showError('서버 통신 실패')
      })
      .finally(() => {
        setIsSearching(false)
      })
  }

  // 매수/매도 등록 및 수정 통합 처리 (PUT/POST 분기)
  const handleSaveTransaction = () => {
    if (!txAccount || !txCode || !txName || !txQuantity || !txPrice) {
      showError('모든 거래 정보를 올바르게 입력해주세요.')
      return
    }

    setIsSubmitting(true)

    // 날짜 포맷 함수 캡슐화
    const targetDateStr = txDate
      ? new Date(txDate.getTime() - txDate.getTimezoneOffset() * 60000)
          .toISOString()
          .replace('T', ' ')
          .substring(0, 19)
      : ''

    const payload = {
      type: txType,
      code: txCode,
      name: txName,
      quantity: txQuantity,
      price: txPrice,
      tax_fee: txTaxFee || 0,
      acc_cd: txAccount, // DB 스키마 표준 규격에 맞추어 acc_cd로 전면 통일
      date: targetDateStr,
    }

    const url = editingTxId
      ? `${import.meta.env.VITE_API_URL}/api/transactions/${editingTxId}`
      : `${import.meta.env.VITE_API_URL}/api/transactions/add`
    const method = editingTxId ? 'PUT' : 'POST'

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
          // 입력 폼 전면 초기화
          setEditingTxId(null)
          setTxType('BUY')
          setTxAccount('미래-종합')
          setTxCode('')
          setTxName('')
          setTxQuantity(null)
          setTxPrice(null)
          setTxTaxFee(0)
          setTxDate(new Date())

          // 성공 알림 및 리액티브 자산 실시간 동기화
          showNotice({
            header: editingTxId ? '수정 완료' : '등록 완료',
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
    setEditingTxId(rowData.id)
    setTxType(rowData.type)
    setTxAccount(rowData.acc_cd)
    setTxCode(rowData.code)
    setTxName(rowData.name)
    setTxQuantity(rowData.quantity)
    setTxPrice(rowData.price)
    setTxTaxFee(rowData.tax_fee || 0)
    setTxDate(new Date(rowData.date))
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
                setEditingTxId(null)
                setTxType('BUY')
                setTxAccount('미래-종합')
                setTxCode('')
                setTxName('')
                setTxQuantity(null)
                setTxPrice(null)
                setTxTaxFee(0)
                setTxDate(new Date())
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
        visible={displayDialog}
        onHide={() => setDisplayDialog(false)}
        editingTxId={editingTxId}
        txType={txType}
        setTxType={setTxType}
        txAccount={txAccount}
        setTxAccount={setTxAccount}
        accounts={data.accounts}
        txCode={txCode}
        setTxCode={setTxCode}
        txName={txName}
        setTxName={setTxName}
        txQuantity={txQuantity}
        setTxQuantity={setTxQuantity}
        txPrice={txPrice}
        setTxPrice={setTxPrice}
        txTaxFee={txTaxFee}
        setTxTaxFee={setTxTaxFee}
        txDate={txDate}
        setTxDate={setTxDate}
        isSearching={isSearching}
        isSubmitting={isSubmitting}
        onSearchStock={handleSearchStock}
        onSave={handleSaveTransaction}
      />
    </div>
  )
}
