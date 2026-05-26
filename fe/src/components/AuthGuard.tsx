import { useEffect, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';
import { ProgressSpinner } from 'primereact/progressspinner';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { post } from '@/api';

export default function AuthGuard() {
  const { isInitialized, isSignedIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!isSignedIn) return;

    const fetchRealtimePrices = (delay: number) => {
      timerRef.current = setTimeout(async () => {
        try {
          const res = await post('/api/stock_ohlcvs/current');
          const nextInterval = res.polling_interval || 60000;

          if (res.updated && res.updated.length > 0) {
            window.dispatchEvent(new Event('market-data-updated'));
          }

          fetchRealtimePrices(nextInterval);
        } catch (error) {
          console.error('Polling failed', error);
          fetchRealtimePrices(60000);
        }
      }, delay);
    };

    fetchRealtimePrices(0);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isSignedIn]);

  useEffect(() => {
    if (isInitialized && !isSignedIn && location.pathname !== '/login') {
      navigate('/login', { replace: true });
    }
  }, [isInitialized, isSignedIn, location.pathname, navigate]);

  // HTML 렌더링 구역 -----------------------------------------------------------------------------------
  if (!isInitialized) {
    return (
      <div className="flex flex-column align-items-center justify-content-center h-full">
        <ProgressSpinner />
        <p className="mt-4">인증 상태 확인 중...</p>
      </div>
    );
  }

  if (!isSignedIn) {
    return (
      <div className="flex flex-column align-items-center justify-center h-full">
        <ProgressSpinner />
        <p className="mt-4">로그인 페이지로 이동 중...</p>
      </div>
    );
  }

  return <Outlet />;
}
