import { useState } from 'react';
import { Panel } from 'primereact/panel';
import { Button } from 'primereact/button';
import { Calendar } from 'primereact/calendar';
import { syncAccountDailyBalance } from '@/api';

export default function SyncDailyBalance() {
  const [isSyncing, setIsSyncing] = useState(false);

  // Default: start_date is 1 month ago, end_date is yesterday
  const defaultStart = new Date();
  defaultStart.setMonth(defaultStart.getMonth() - 1);
  const [startDate, setStartDate] = useState<Date | null>(defaultStart);

  const defaultEnd = new Date();
  defaultEnd.setDate(defaultEnd.getDate() - 1);
  const [endDate, setEndDate] = useState<Date | null>(defaultEnd);

  const handleSyncDailyBalance = async () => {
    setIsSyncing(true);
    try {
      // Format dates to YYYY-MM-DD
      const start_date = startDate ? startDate.toISOString().split('T')[0] : undefined;
      const end_date = endDate ? endDate.toISOString().split('T')[0] : undefined;

      const payload = { start_date, end_date };

      const res = await syncAccountDailyBalance(payload);
      if (res.status === 'success') {
        alert('모든 계좌의 일일 잔고 동기화가 완료되었습니다.');
        window.dispatchEvent(new Event('market-data-updated'));
      } else {
        alert(`동기화 실패: ${res.message || '알 수 없는 오류가 발생했습니다.'}`);
      }
    } catch (err: any) {
      console.error(err);
      alert(`동기화 실패: ${err.message || '서버와 통신 중 오류가 발생했습니다.'}`);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="page p-4">
      <div className="flex justify-content-between align-items-center mb-4">
        <h2 className="m-0 text-2xl font-bold text-color">일일 잔고 동기화</h2>
      </div>

      <div className="grid">
        <div className="col-12 md:col-6">
          <Panel header="일일 잔고 데이터 동기화">
            <p className="m-0 mb-4 text-color-secondary">
              지정된 기간 동안의 계좌별 일일 잔고 및 수익률을 다시 계산하고 동기화합니다. 최근 과거
              날짜로 매매 내역을 수정했다면 이 기능을 실행하여 대시보드를 갱신하세요.
            </p>

            <div className="flex flex-column gap-3 mb-4">
              <div className="flex flex-column gap-2">
                <label htmlFor="start_date">시작일 (기본: 1개월 전)</label>
                <Calendar
                  id="start_date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.value as Date)}
                  dateFormat="yy-mm-dd"
                  showIcon
                />
              </div>
              <div className="flex flex-column gap-2">
                <label htmlFor="end_date">종료일 (기본: 어제, 최대: 어제)</label>
                <Calendar
                  id="end_date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.value as Date)}
                  dateFormat="yy-mm-dd"
                  showIcon
                  maxDate={defaultEnd}
                />
              </div>
            </div>

            <Button
              label={isSyncing ? '동기화 중...' : '일일 잔고 강제 동기화'}
              icon={isSyncing ? 'pi pi-spin pi-spinner' : 'pi pi-sync'}
              onClick={handleSyncDailyBalance}
              disabled={isSyncing}
              className="p-button-primary w-full sm:w-auto"
            />
          </Panel>
        </div>
      </div>
    </div>
  );
}
