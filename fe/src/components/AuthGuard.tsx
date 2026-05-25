import { useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { ProgressSpinner } from 'primereact/progressspinner';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';

export default function AuthGuard() {
  const { isInitialized, isSignedIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

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
