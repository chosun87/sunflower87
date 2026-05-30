import { useState, useEffect } from 'react';
import {
  Dialog,
  Button,
  SelectButton,
  Dropdown,
  AutoComplete,
  InputText,
  InputNumber,
  Calendar,
} from '@/assets/ts/PrimeReact';
import { showNotice, showError } from '@/assets/ts/dialogUtils';

export default function TrStockDialog({
  visible,
  onHide,
  editingTx, // 수정 시 대상 거래 원본 객체 (신규 시 null)
  cachedStock, // 신규 등록 시 마지막 검색 보존 종목 (검색 데이터 뷰 보존)
  accounts,
  isSubmitting,
  onSearchStock, // (keyword) => Promise<{code, name}>
  onLookupCode, // (code) => Promise<{code, name}>
  searchHistory = [],
  onSave, // (payload) => Promise<void>
}) {
  // 내부 폼 상태 관리 레이어 (Resetting state with a key 패턴 적용으로 초기값 바로 바인딩)
  const [txType, setTxType] = useState(editingTx?.trade_type || 'BUY');
  const [txAccount, setTxAccount] = useState(
    editingTx?.acc_cd || (accounts && accounts.length > 0 ? accounts[0].acc_cd : '')
  );
  const [txCode, setTxCode] = useState(editingTx?.stock_code || cachedStock?.code || '');
  const [txName, setTxName] = useState(editingTx?.stock_name || cachedStock?.name || '');
  const [txQuantity, setTxQuantity] = useState(editingTx?.quantity || null);
  const [txPrice, setTxPrice] = useState(editingTx?.price || null);
  const [txTaxFee, setTxTaxFee] = useState(editingTx?.tax_fee || 0);
  const [txDate, setTxDate] = useState(
    editingTx?.dt_trade ? new Date(editingTx.dt_trade) : new Date()
  );

  useEffect(() => {
    if (visible) {
      setTxType(editingTx?.trade_type || 'BUY');
      setTxAccount(
        editingTx?.acc_cd || (accounts && accounts.length > 0 ? accounts[0].acc_cd : '')
      );
      setTxCode(editingTx?.stock_code || cachedStock?.code || '');
      setTxName(editingTx?.stock_name || cachedStock?.name || '');
      setTxQuantity(editingTx?.quantity || null);
      setTxPrice(editingTx?.price || null);
      setTxTaxFee(editingTx?.tax_fee || 0);
      setTxDate(editingTx?.dt_trade ? new Date(editingTx.dt_trade) : new Date());
    }
  }, [visible, editingTx, cachedStock, accounts]);

  const [isSearching, setIsSearching] = useState(false);
  const [historySuggestions, setHistorySuggestions] = useState([]);

  const typeOptions = [
    { label: '매수 (BUY)', value: 'BUY' },
    { label: '매도 (SELL)', value: 'SELL' },
  ];

  const dropdownAccounts = (accounts || []).map((acc) => ({
    label: `[${acc.acc_company_nm.substring(0, 2)}] ${acc.acc_nm}`,
    value: acc.acc_cd,
  }));

  // 보유 중인 주식 목록 추출 (보유 수량이 0보다 큰 종목만, 중복 제거)
  const heldStocks = Array.from(
    new Set(
      (accounts || [])
        .flatMap((acc) => (acc.stocks || []).filter((s) => s.quantity > 0).map((s) => s.stock_name))
        .filter(Boolean)
    )
  );

  const filterHistorySuggestions = (query) => {
    const combinedSuggestions = Array.from(new Set([...heldStocks, ...searchHistory]));
    const normalized = query.trim().toLowerCase();
    const filtered = combinedSuggestions.filter((item) => item.toLowerCase().includes(normalized));
    setHistorySuggestions(filtered.length > 0 ? filtered : combinedSuggestions);
  };

  // 내부 종목 검색 처리 핸들러
  const handleSearch = () => {
    const keyword = txName.trim();
    if (!keyword) {
      showError('검색할 종목명을 먼저 입력해주세요.');
      return;
    }

    setIsSearching(true);
    onSearchStock(keyword)
      .then((match) => {
        setTxCode(match.code);
        setTxName(match.name);
        showNotice({
          header: '검색 완료',
          icon: 'fa-solid fa-check-circle',
          message: `종목 '${match.name}' (${match.code})의 정보가 성공적으로 조회되었습니다.`,
          acceptClassName: 'p-button-success',
        });
      })
      .catch((err) => {
        showError(err.message || '매칭되는 종목을 찾지 못했습니다.');
      })
      .finally(() => {
        setIsSearching(false);
      });
  };

  const handleLookupCode = () => {
    const code = txCode.trim();
    if (!/^\d{6}$/.test(code)) {
      showError('유효한 6자리 종목 코드를 입력해주세요.');
      return;
    }

    setIsSearching(true);
    onLookupCode(code)
      .then((match) => {
        setTxName(match.name);
        showNotice({
          header: '코드 조회 성공',
          icon: 'fa-solid fa-check-circle',
          message: `종목 코드 '${match.code}'에 대한 종목명 '${match.name}' 조회가 완료되었습니다.`,
          acceptClassName: 'p-button-success',
        });
      })
      .catch((err) => {
        showError(err.message || '종목명 조회에 실패했습니다.');
      })
      .finally(() => {
        setIsSearching(false);
      });
  };

  // 내부 저장 핸들러 호출 및 페이로드 빌드
  const handleSave = () => {
    if (!txAccount || !txCode || !txName || !txQuantity || !txPrice) {
      showError('모든 거래 정보를 올바르게 입력해주세요.');
      return;
    }

    // 날짜 표준 ISO 포맷 변환 필터링 가동
    const targetDateStr = txDate
      ? new Date(txDate.getTime() - txDate.getTimezoneOffset() * 60000).toISOString().split('T')[0]
      : '';

    const payload = {
      trade_type: txType,
      stock_code: txCode,
      stock_name: txName,
      quantity: Math.abs(Number(txQuantity) || 0), // 부호 정합성 검증 추가
      price: Math.abs(Number(txPrice) || 0),
      tax_fee: Math.abs(Number(txTaxFee) || 0), // 부호 정합성 검증 추가
      acc_cd: txAccount,
      dt_trade: targetDateStr,
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
        label={editingTx ? '수정 완료' : '거래 등록'}
        icon="fa-solid fa-check"
        onClick={handleSave}
        className="p-button-primary font-bold"
        disabled={isSubmitting || !txAccount || !txCode || !txName || !txQuantity || !txPrice}
        loading={isSubmitting}
      />
    </div>
  );

  return (
    <Dialog
      header={
        <div className="flex align-items-center gap-2">
          <i
            className={`pi ${editingTx ? 'pi-file-edit' : 'pi-plus-circle'} text-primary text-xl`}
          ></i>
          <span className="font-bold text-xl">
            {editingTx ? '매매 기록 수정' : '신규 매매 등록'}
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
        <label className="font-bold mb-2 block">거래 구분 <span className="text-red-500">*</span></label>
        <SelectButton
          value={txType}
          options={typeOptions}
          onChange={(e) => setTxType(e.value || 'BUY')}
          disabled={isSubmitting}
        />
      </div>

      <div className="field mb-4">
        <label className="font-bold mb-2 block">대상 귀속 계좌 <span className="text-red-500">*</span></label>
        <Dropdown
          value={txAccount}
          options={dropdownAccounts}
          onChange={(e) => setTxAccount(e.value)}
          placeholder="거래를 반영할 계좌를 선택하세요"
          disabled={isSubmitting}
        />
      </div>

      <div className="stock-nm field mb-4">
        <label className="font-bold mb-2 block">종목명 검색 <span className="text-red-500">*</span></label>
        <div className="p-inputgroup">
          <AutoComplete
            value={txName}
            suggestions={historySuggestions}
            completeMethod={(e) => filterHistorySuggestions(e.query)}
            dropdown
            placeholder="예: 삼성전자 (입력 후 검색 클릭)"
            onChange={(e) => setTxName(e.value)}
            disabled={isSubmitting}
            forceSelection={false}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleSearch();
              }
            }}
          />
          <Button
            icon="fa-solid fa-search"
            onClick={handleSearch}
            loading={isSearching}
            disabled={isSubmitting}
          />
        </div>
        {searchHistory && searchHistory.length > 0 && (
          <small className="block text-500 mt-2">이전 검색: {searchHistory.join(', ')}</small>
        )}
      </div>

      <div className="field mb-4">
        <label className="font-bold mb-2 block">확정 종목코드 <span className="text-red-500">*</span></label>
        <div className="p-inputgroup">
          <InputText
            value={txCode}
            onChange={(e) => setTxCode(e.target.value)}
            placeholder="검색 시 자동 입력 (수동 입력 가능)"
            disabled={isSubmitting}
          />
          <Button
            icon="fa-solid fa-search"
            onClick={handleLookupCode}
            disabled={isSubmitting || !/^\d{6}$/.test(txCode.trim())}
            loading={isSearching}
          />
        </div>
      </div>

      <div className="grid">
        <div className="col-6 field mb-4">
          <label className="font-bold mb-2 block">거래 수량 (주) <span className="text-red-500">*</span></label>
          <InputNumber
            value={txQuantity}
            onValueChange={(e) => setTxQuantity(e.value)}
            placeholder="수량"
            min={1}
            disabled={isSubmitting}
          />
        </div>
        <div className="col-6 field mb-4">
          <label className="font-bold mb-2 block">거래 단가 (원) <span className="text-red-500">*</span></label>
          <InputNumber
            value={txPrice}
            onValueChange={(e) => setTxPrice(e.value)}
            placeholder="단가"
            min={1}
            disabled={isSubmitting}
          />
        </div>
      </div>

      <div className="grid">
        <div className="col-6 field mb-4">
          <label className="font-bold mb-2 block">세금 및 수수료 (원)</label>
          <InputNumber
            value={txTaxFee}
            onValueChange={(e) => setTxTaxFee(e.value || 0)}
            placeholder="미입력 시 0원"
            min={0}
            disabled={isSubmitting}
          />
        </div>

        <div className="col-6 field mb-4">
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
      </div>
    </Dialog>
  );
}
