import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import dayjs from 'dayjs'
import {
  Card,
  DataTable,
  Column,
  Dropdown,
  Badge,
  Button,
  TabView,
  TabPanel,
  Dialog,
  InputText,
  InputNumber,
  SelectButton,
  Calendar,
  confirmDialog,
  addLocale,
} from '@/assets/js/PrimeReact'
import { showNotice, showError } from '@/assets/js/dialogUtils'

// PrimeReact Calendar 한국어(ko) 로컬라이징 사전 등록
addLocale('ko', {
  firstDayOfWeek: 0,
  dayNames: [
    '일요일',
    '월요일',
    '화요일',
    '수요일',
    '목요일',
    '금요일',
    '토요일',
  ],
  dayNamesShort: ['일', '월', '화', '수', '목', '금', '토'],
  dayNamesMin: ['일', '월', '화', '수', '목', '금', '토'],
  monthNames: [
    '1월',
    '2월',
    '3월',
    '4월',
    '5월',
    '6월',
    '7월',
    '8월',
    '9월',
    '10월',
    '11월',
    '12월',
  ],
  monthNamesShort: [
    '1월',
    '2월',
    '3월',
    '4월',
    '5월',
    '6월',
    '7월',
    '8월',
    '9월',
    '10월',
    '11월',
    '12월',
  ],
  today: '오늘',
  clear: '초기화',
})

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [selectedAccount, setSelectedAccount] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const navigate = useNavigate()
  const { isSignedIn, isInitialized } = useAuth()

  // 거래 등록 및 수정 모달 상태 관리
  const [displayDialog, setDisplayDialog] = useState(false)
  const [editingTxId, setEditingTxId] = useState(null) // 수정 모드 시 거래 ID 추적
  const [txType, setTxType] = useState('BUY') // BUY 또는 SELL
  const [txAccount, setTxAccount] = useState('A001') // 대상 귀속 계좌
  const [txCode, setTxCode] = useState('')
  const [txName, setTxName] = useState('')
  const [txQuantity, setTxQuantity] = useState(null)
  const [txPrice, setTxPrice] = useState(null)
  const [txDate, setTxDate] = useState(new Date())
  const [isSearching, setIsSearching] = useState(false)

  useEffect(() => {
    if (isInitialized && !isSignedIn) {
      navigate('/login')
    }
  }, [isInitialized, isSignedIn, navigate])

  // 실시간 자산 및 보유 주식 불러오기 (데이터 일관성 보장 바인딩)
  const loadAccounts = () => {
    fetch('http://localhost:8000/api/accounts')
      .then((res) => res.json())
      .then((resData) => {
        if (resData.status === 'success') {
          setData(resData)
          // 계좌가 있고, 기존 선택 계좌가 유지되는 경우 찾아서 재매핑하여 무중단 상태 동기화 제공
          if (resData.accounts && resData.accounts.length > 0) {
            setSelectedAccount((prev) => {
              if (prev) {
                const found = resData.accounts.find(
                  (a) => a.acc_cd === prev.acc_cd,
                )
                if (found) return found
              }
              return resData.accounts[0]
            })
          }
        }
      })
      .catch((err) => console.error('데이터 로드 실패:', err))
  }

  // SQLite 거래 히스토리 내역 불러오기
  const loadTransactions = () => {
    fetch('http://localhost:8000/api/transactions')
      .then((res) => res.json())
      .then((resData) => {
        if (resData.status === 'success') {
          setTransactions(resData.data)
        }
      })
      .catch((err) => console.error('거래 내역 로드 실패:', err))
  }

  useEffect(() => {
    loadAccounts()
    loadTransactions()

    // 백엔드 API로부터 오늘의 AI 추천 종목 데이터 바인딩
    fetch('http://localhost:8000/api/recommendations')
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
      `http://localhost:8000/api/stocks/search?keyword=${encodeURIComponent(keyword)}`,
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

  // 커스텀 거래일시 포맷터 함수 (dayjs 활용)
  const formatCustomDate = (dateObj) => {
    return dateObj ? dayjs(dateObj).format('YYYY-MM-DD HH:mm:ss') : ''
  }

  // 매수/매도 등록 및 수정 통합 처리 (PUT/POST 분기)
  const handleSaveTransaction = () => {
    if (!txAccount || !txCode || !txName || !txQuantity || !txPrice) {
      showError('모든 거래 정보를 올바르게 입력해주세요.')
      return
    }

    const payload = {
      type: txType,
      code: txCode,
      name: txName,
      quantity: txQuantity,
      price: txPrice,
      acc_cd: txAccount,
      date: formatCustomDate(txDate),
    }

    const url = editingTxId
      ? `http://localhost:8000/api/transactions/${editingTxId}`
      : 'http://localhost:8000/api/transactions/add'
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
          setTxAccount('A001')
          setTxCode('')
          setTxName('')
          setTxQuantity(null)
          setTxPrice(null)
          setTxDate(new Date())

          // 성공 알림 및 리액티브 자산 실시간 동기화
          showNotice({
            header: editingTxId ? '수정 완료' : '등록 완료',
            icon: 'pi pi-check-circle',
            message:
              resData.message || '매매 내역이 정상적으로 처리되었습니다.',
          })

          loadAccounts()
          loadTransactions()
        }
      })
      .catch((err) => {
        console.error('거래 추가/수정 중 에러:', err)
        showError(err.message || '서버 통신 실패')
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
    setTxDate(new Date(rowData.date))
    setDisplayDialog(true)
  }

  // 거래 내역 삭제 및 역산 핸들러
  const handleDeleteTransaction = (rowData) => {
    confirmDialog({
      message: `'${rowData.name}' 매매 거래 기록을 삭제하시겠습니까? 해당 거래에 따른 계좌의 주식 잔고 및 자산이 역산(Rollback)됩니다.`,
      header: '⚠️ 거래 내역 삭제 확인',
      icon: 'pi pi-exclamation-triangle',
      acceptClassName: 'p-button-danger font-bold',
      rejectClassName: 'p-button-text p-button-secondary',
      acceptLabel: '삭제',
      rejectLabel: '취소',
      accept: () => {
        fetch(`http://localhost:8000/api/transactions/${rowData.id}`, {
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
              loadAccounts()
              loadTransactions()
            }
          })
          .catch((err) => {
            console.error('거래 삭제 에러:', err)
            showError(err.message || '서버 통신 실패')
          })
      },
    })
  }

  // 수익률 컬러 템플릿
  const profitTemplate = (rowData) => {
    const isPositive = rowData.eval_profit_rate >= 0
    return (
      <Badge
        value={`${rowData.eval_profit_rate}%`}
        severity={isPositive ? 'danger' : 'info'}
      />
    )
  }

  // 금액 포맷터
  const currencyTemplate = (amount) => {
    return amount.toLocaleString() + ' 원'
  }

  // 거래 내역 구분 템플릿
  const txTypeBodyTemplate = (rowData) => {
    const isBuy = rowData.type === 'BUY'
    return (
      <span
        className={`font-bold p-1 px-2 border-round text-xs ${
          isBuy
            ? 'bg-red-100 text-red-700 border-red-200'
            : 'bg-blue-100 text-blue-700 border-blue-200'
        }`}
      >
        {isBuy ? '● 매수' : '○ 매도'}
      </span>
    )
  }

  // 거래 내역 일시 템플릿 (dayjs 활용 표준 한국어 포맷 강제 적용)
  const dateBodyTemplate = (rowData) => {
    return rowData.date ? dayjs(rowData.date).format('YYYY-MM-DD HH:mm') : ''
  }

  // 거래 계좌 뱃지 표시 템플릿
  const accountBodyTemplate = (rowData) => {
    const alias = rowData.account_alias || rowData.acc_nm || '알 수 없는 계좌'
    const code = rowData.acc_cd || ''

    // Assign badge colors based on account code for a vibrant and organized aesthetic
    let severity = 'secondary'
    if (code === 'A001') severity = 'success'
    else if (code === 'A002') severity = 'warning'
    else if (code === 'A003') severity = 'info'
    else if (code === 'A004') severity = 'help'

    return <Badge value={alias} severity={severity} />
  }

  // 테이블 최우측 [수정/삭제] 액션 컬럼 정의
  const actionsBodyTemplate = (rowData) => {
    return (
      <div className="flex gap-2">
        <Button
          icon="pi pi-pencil"
          className="p-button-rounded p-button-warning p-button-text p-button-sm"
          onClick={() => handleEditTransaction(rowData)}
          tooltip="매매 내역 수정"
        />
        <Button
          icon="pi pi-trash"
          className="p-button-rounded p-button-danger p-button-text p-button-sm"
          onClick={() => handleDeleteTransaction(rowData)}
          tooltip="매매 내역 삭제"
        />
      </div>
    )
  }

  // 모달 팝업 하단 버튼 정의
  const dialogFooter = (
    <div className="flex justify-content-end gap-2 pt-2">
      <Button
        label="취소"
        icon="pi pi-times"
        onClick={() => setDisplayDialog(false)}
        className="p-button-text p-button-secondary"
      />
      <Button
        label={editingTxId ? '수정 완료' : '거래 등록'}
        icon="pi pi-check"
        onClick={handleSaveTransaction}
        className="p-button-primary font-bold"
        disabled={!txAccount || !txCode || !txName || !txQuantity || !txPrice}
      />
    </div>
  )

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* 매수/매도 커스텀 CSS 컬러 오버라이드 */}
      <style>{`
        .tx-selectbutton.buy-selected .p-button.p-highlight {
          background-color: #ef4444 !important;
          border-color: #ef4444 !important;
          color: #ffffff !important;
        }
        .tx-selectbutton.sell-selected .p-button.p-highlight {
          background-color: #3b82f6 !important;
          border-color: #3b82f6 !important;
          color: #ffffff !important;
        }
      `}</style>

      <div className="flex align-items-center justify-content-between mb-6">
        <h1 className="text-4xl font-bold text-900 m-0">
          🌻 sunflower87 Dashboard
        </h1>
        <span className="text-600">Decision Maker: SUN</span>
      </div>

      {/* 상단 총자산 요약 카드 */}
      <div className="grid mb-6">
        <div className="col-12 md:col-6">
          <Card title="통합 총자산" className="shadow-2 border-round">
            <h2 className="text-4xl text-primary font-bold m-0">
              {data.total_asset.toLocaleString()} 원
            </h2>
          </Card>
        </div>
        <div className="col-12 md:col-6">
          <Card title="계좌 선택" className="shadow-2 border-round">
            <Dropdown
              value={selectedAccount}
              options={data.accounts}
              onChange={(e) => setSelectedAccount(e.value)}
              optionLabel="alias"
              placeholder="조회할 계좌를 선택하세요"
              className="w-full"
            />
          </Card>
        </div>
      </div>

      {/* 오늘의 AI 추천 종목 섹션 */}
      <div className="mb-6">
        <div className="flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
          <div className="flex align-items-center gap-2">
            <i className="pi pi-sparkles text-amber-500 text-2xl"></i>
            <h2 className="text-2xl font-bold text-900 m-0">
              오늘의 AI 추천 종목
            </h2>
          </div>
          <Badge
            value="정량 지표 분석 기반"
            severity="warning"
            className="p-2 border-round font-semibold"
          />
        </div>

        <div className="grid">
          {recommendations.map((item, idx) => (
            <div key={idx} className="col-12 md:col-4">
              <Card
                className="shadow-2 hover:shadow-4 transition-all transition-duration-200 border-top-3 border-amber-500 h-full flex flex-column"
                style={{ borderRadius: '8px' }}
              >
                <div className="flex justify-content-between align-items-center mb-3">
                  <div>
                    <span className="text-xl font-bold text-900 mr-2">
                      {item.name}
                    </span>
                    <span className="text-500 text-sm font-semibold">
                      {item.code}
                    </span>
                  </div>
                  <Badge
                    value={item.tag}
                    className="bg-amber-100 text-amber-800 font-semibold p-1"
                  />
                </div>

                <p className="text-700 text-sm mb-4 line-height-3 flex-grow-1">
                  {item.reason}
                </p>

                <div className="flex justify-content-between align-items-center pt-3 border-top-1 border-100 mt-auto">
                  <span className="text-sm font-semibold text-600">
                    AI 추천 점수
                  </span>
                  <div className="flex align-items-center gap-2">
                    <span className="text-2xl font-bold text-amber-600">
                      {item.score}점
                    </span>
                    <Button
                      icon="pi pi-chevron-right"
                      className="p-button-rounded p-button-text p-button-sm text-amber-500"
                      aria-label="상세보기"
                    />
                  </div>
                </div>
              </Card>
            </div>
          ))}
        </div>
      </div>

      {/* 보유 자산 및 매매 거래 내역 탭 구조화 (TabView) */}
      <Card className="shadow-4 border-round mt-6">
        <TabView>
          {/* [탭 1: 보유 자산 상세] */}
          <TabPanel
            header="보유 자산 상세"
            leftIcon="pi pi-wallet mr-2 text-primary"
          >
            {selectedAccount ? (
              <div className="mt-3">
                <div className="flex align-items-center justify-content-between mb-3">
                  <h3 className="text-xl font-bold m-0 text-700">
                    {selectedAccount.alias} 보유 현황
                  </h3>
                </div>
                <DataTable
                  value={selectedAccount.stocks}
                  responsiveLayout="stack"
                  breakpoint="960px"
                  sortMode="multiple"
                  stripedRows
                >
                  <Column field="name" header="종목명" sortable></Column>
                  <Column field="quantity" header="보유수량" sortable></Column>
                  <Column
                    field="avg_price"
                    header="매입평단가"
                    body={(rd) => currencyTemplate(rd.avg_price)}
                    sortable
                  ></Column>
                  <Column
                    field="current_price"
                    header="현재가"
                    body={(rd) => currencyTemplate(rd.current_price)}
                    sortable
                  ></Column>
                  <Column
                    field="eval_profit_rate"
                    header="수익률"
                    body={profitTemplate}
                    sortable
                  ></Column>
                </DataTable>
              </div>
            ) : (
              <div className="p-4 text-center text-500">
                조회 가능한 계좌 정보가 없습니다.
              </div>
            )}
          </TabPanel>

          {/* [탭 2: 매매 내역 히스토리] */}
          <TabPanel
            header="매매 내역 히스토리"
            leftIcon="pi pi-history mr-2 text-primary"
          >
            <div className="mt-3">
              <div className="flex align-items-center justify-content-between mb-4 flex-wrap gap-2">
                <h3 className="text-xl font-bold m-0 text-700">
                  SQLite 매매 내역 대장
                </h3>
                <Button
                  label="거래 내역 추가"
                  icon="pi pi-plus"
                  className="p-button-success p-button-sm font-bold shadow-2"
                  onClick={() => {
                    setEditingTxId(null)
                    setTxType('BUY')
                    setTxAccount('')
                    setTxCode('')
                    setTxName('')
                    setTxQuantity(null)
                    setTxPrice(null)
                    setTxDate(new Date())
                    setDisplayDialog(true)
                  }}
                />
              </div>

              <DataTable
                value={transactions}
                responsiveLayout="stack"
                breakpoint="960px"
                sortMode="multiple"
                stripedRows
                paginator
                rows={10}
                className="mt-2"
                emptyMessage="등록된 매매 거래 히스토리가 존재하지 않습니다."
              >
                <Column
                  field="date"
                  header="거래 일시"
                  body={dateBodyTemplate}
                  sortable
                ></Column>
                <Column
                  field="type"
                  header="구분"
                  body={txTypeBodyTemplate}
                  sortable
                ></Column>
                <Column
                  field="acc_cd"
                  header="거래 계좌"
                  body={accountBodyTemplate}
                  sortable
                ></Column>
                <Column field="code" header="종목코드" sortable></Column>
                <Column field="name" header="종목명" sortable></Column>
                <Column
                  field="quantity"
                  header="거래 수량"
                  body={(rd) => `${rd.quantity.toLocaleString()} 주`}
                  sortable
                ></Column>
                <Column
                  field="price"
                  header="거래 단가"
                  body={(rd) => currencyTemplate(rd.price)}
                  sortable
                ></Column>
                <Column
                  header="총 거래금액"
                  body={(rd) => currencyTemplate(rd.quantity * rd.price)}
                  sortable
                ></Column>
                <Column
                  header="작업"
                  body={actionsBodyTemplate}
                  exportable={false}
                  style={{ minWidth: '8rem' }}
                ></Column>
              </DataTable>
            </div>
          </TabPanel>
        </TabView>
      </Card>

      {/* 매매 내역 추가 및 수정 다이얼로그 (Form) */}
      <Dialog
        header={
          editingTxId ? '📝 매매 거래 내역 수정' : '📝 신규 매매 거래 등록'
        }
        visible={displayDialog}
        style={{ width: '450px' }}
        footer={dialogFooter}
        onHide={() => setDisplayDialog(false)}
        modal
        className="p-fluid border-round"
      >
        <div className="flex flex-column gap-3 mt-3">
          {/* 매수/매도 직관적 선택 (SelectButton) */}
          <div className="flex flex-column gap-2">
            <span className="font-semibold text-900">매매 구분</span>
            <SelectButton
              value={txType}
              options={[
                { label: '🔴 매수', value: 'BUY' },
                { label: '🔵 매도', value: 'SELL' },
              ]}
              onChange={(e) => setTxType(e.value || 'BUY')}
              className={`tx-selectbutton w-full ${
                txType === 'BUY' ? 'buy-selected' : 'sell-selected'
              }`}
            />
          </div>

          {/* 거래 계좌 선택 Dropdown */}
          <div className="flex flex-column gap-2">
            <label htmlFor="txAccount" className="font-semibold text-900">
              거래 계좌
            </label>
            <Dropdown
              id="txAccount"
              value={txAccount}
              options={data?.accounts || []}
              onChange={(e) => setTxAccount(e.value)}
              optionLabel="acc_nm"
              optionValue="acc_cd"
              placeholder="거래가 발생한 계좌 선택"
              className="w-full"
            />
          </div>

          {/* 종목명 입력창 및 [검색] 버튼 한 그룹화 (p-inputgroup) */}
          <div className="flex flex-column gap-2">
            <label htmlFor="txName" className="font-semibold text-900">
              종목명
            </label>
            <div className="p-inputgroup">
              <InputText
                id="txName"
                value={txName}
                onChange={(e) => setTxName(e.target.value)}
                placeholder="예: 삼성전자"
              />
              <Button
                type="button"
                icon="pi pi-search"
                className="p-button-primary"
                onClick={handleSearchStock}
                tooltip="종목코드 자동 검색"
                loading={isSearching}
              />
            </div>
          </div>

          {/* 종목코드 입력창 (비활성 readOnly 처리) */}
          <div className="flex flex-column gap-2">
            <label htmlFor="txCode" className="font-semibold text-900">
              종목코드
            </label>
            <InputText
              id="txCode"
              value={txCode}
              placeholder="종목명을 검색하면 자동 입력됩니다"
              readOnly
              className="bg-gray-100 cursor-not-allowed"
            />
          </div>

          {/* 거래 일시 입력 (한국어 locale 반영) */}
          <div className="flex flex-column gap-2">
            <label htmlFor="txDate" className="font-semibold text-900">
              거래 일시
            </label>
            <Calendar
              id="txDate"
              value={txDate}
              onChange={(e) => setTxDate(e.value || new Date())}
              showTime
              hourFormat="24"
              locale="ko"
              dateFormat="yy-mm-dd"
              placeholder="거래 날짜와 시간을 선택하세요"
            />
          </div>

          {/* 거래 수량 입력 */}
          <div className="flex flex-column gap-2">
            <label htmlFor="txQuantity" className="font-semibold text-900">
              거래 수량 (주)
            </label>
            <InputNumber
              id="txQuantity"
              value={txQuantity}
              onValueChange={(e) => setTxQuantity(e.value)}
              placeholder="예: 100"
              min={1}
              showButtons
            />
          </div>

          {/* 거래 단가 입력 */}
          <div className="flex flex-column gap-2">
            <label htmlFor="txPrice" className="font-semibold text-900">
              거래 단가 (원)
            </label>
            <InputNumber
              id="txPrice"
              value={txPrice}
              onValueChange={(e) => setTxPrice(e.value)}
              placeholder="예: 72500"
              min={1}
              mode="currency"
              currency="KRW"
              locale="ko-KR"
            />
          </div>
        </div>
      </Dialog>
    </div>
  )
}
