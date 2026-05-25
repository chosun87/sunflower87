import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Message, ProgressSpinner } from '@/assets/ts/PrimeReact';
import { useAuth } from '@/context/AuthContext';

export default function Login() {
  const navigate = useNavigate();
  const { login, isSignedIn, isInitialized } = useAuth();

  useEffect(() => {
    if (isInitialized && isSignedIn) {
      navigate('/', { replace: true });
    }
  }, [isInitialized, isSignedIn, navigate]);

  if (!isInitialized) {
    return (
      <div className="full-page flex-column">
        <ProgressSpinner />
        <p>인증 상태 확인 중...</p>
      </div>
    )
  }

  return (
    <div className="full-page flex-column">
      <Message severity="info" text="로그인이 필요합니다." />
      <Button
        size="large"
        raised
        className="btn-login p-button-google"
        icon="fa-brands fa-google"
        label="Google 계정으로 로그인"
        onClick={login}
      />
    </div>
  )
}
