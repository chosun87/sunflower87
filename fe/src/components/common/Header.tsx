import { useNavigate } from 'react-router-dom';
import { Button } from '@/assets/ts/PrimeReact';
import { useAuth, useAuthTimer } from '@/context/AuthContext';
import { GOOGLE_AUTH_PARAMS } from '@/assets/ts/googleAuthParams';

export default function Header() {
  const navigate = useNavigate();
  const { isSignedIn, logout, extendLogin } = useAuth();
  const { authRemainingTime } = useAuthTimer();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="app-header">
      <div className="flex align-items-center justify-content-between p-3 bg-primary text-white shadow-2">
        <div className="flex align-items-center gap-2">
          <i className="pi pi-sun text-2xl"></i>
          <span className="text-xl font-bold">sunflower87</span>
        </div>

        <div className="flex align-items-center gap-3">
          {isSignedIn && (
            <div className="flex flex-column align-items-center relative">
              {/* 인증만료까지 남은 시간 표시 (클릭 시 연장) */}
              {!GOOGLE_AUTH_PARAMS.DISABLED_RELOGIN && (
                <span
                  className="auth-remaining-time text-xs monospace text-white-alpha-80 mb-1"
                  style={{ cursor: 'pointer' }}
                  onClick={extendLogin}
                  title="인증 연장하기"
                >
                  {authRemainingTime}
                </span>
              )}
              <Button
                label="Logout"
                icon="pi pi-sign-out"
                className="p-button-text text-white p-0"
                onClick={handleLogout}
              />
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
