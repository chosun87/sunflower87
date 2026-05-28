import { useState } from 'react';
import { Panel } from 'primereact/panel';
import { Button } from 'primereact/button';
import { syncDailyBalance } from '@/api';

export default function DataManagement() {
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSyncDailyBalance = async () => {
    setIsSyncing(true);
    try {
      const res = await syncDailyBalance();
      if (res.status === 'success') {
        alert('모든 계좌의 일일 잔고 동기화가 완료되었습니다.');
        // Trigger market data update event to refresh other components if needed
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
        <h2 className="m-0 text-2xl font-bold text-color">데이터 관리</h2>
      </div>

      <div className="grid">
        <div className="col-12 md:col-6">
          <Panel header="일일 잔고 데이터 동기화">
            <p className="m-0 mb-4 text-color-secondary">
              백엔드 서버에 접속하여 전일까지의 계좌별 일일 잔고 및 수익률을 강제로 다시 계산하고 동기화합니다.
              최근에 과거 날짜로 매매 내역을 추가하거나 수정한 경우, 이 버튼을 눌러 일일 잔고를 갱신해야 대시보드 수익률이 정확하게 반영됩니다.
            </p>
            <Button
              label={isSyncing ? '동기화 중...' : '일일 잔고 강제 동기화'}
              icon={isSyncing ? 'pi pi-spin pi-spinner' : 'pi pi-sync'}
              onClick={handleSyncDailyBalance}
              disabled={isSyncing}
              className="p-button-primary w-full sm:w-auto"
            />
          </Panel>
        </div>
        
        {/* Add more panels here later for other data management tasks like DB Backup, etc. */}
      </div>
    </div>
  );
}
